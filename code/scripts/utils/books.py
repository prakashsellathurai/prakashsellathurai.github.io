#!/usr/bin/env python3
"""Fetch book metadata from LibraryThing and write books.json."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path

SHELVES = ["currently-reading", "read", "curated"]
BOOKS_PATH = Path("./data/non-public/books.json")

# LibraryThing public JSON API — no authentication required.
_LT_USERNAME = "prakashsellathurai"
_LT_API_URL = (
    "https://www.librarything.com/api_getdata.php"
    "?userid={username}&key=0&type=json&max=250&page={page}"
    "&showCollections=1&showTags=1&showRatings=1"
)
# LT collection IDs and tags for this account.
_LT_COLLECTION_CURRENTLY_READING = "7"
_LT_COLLECTION_READ = "1096112"
_LT_TAG_CURATED = "curated"

# Regex to extract the JSON payload from the JS wrapper LT returns.
_LT_JSON_RE = re.compile(r"var widgetResults = (.+?);\s*LibraryThing", re.DOTALL)
# LibraryThing work info JSON API endpoint. Accepts comma-separated ISBNs.
_LT_WORK_INFO_URL = "https://www.librarything.com/api/json/workinfo.js?ids={isbns}"


def _fetch_raw(url: str, timeout: int = 30) -> str | None:
    """Fetch a URL and return raw response text.

    Args:
        url: Absolute URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        Decoded response body, or None when the fetch fails.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        print(f"Error fetching {url}: {e}")
        return None


def _lt_work_links(isbns: Sequence[str]) -> dict[str, str]:
    """Resolve LibraryThing work links from ISBNs.

    Args:
        isbns: ISBN strings to resolve. Blank values are ignored.

    Returns:
        Mapping of ISBN to LibraryThing work link. Empty mapping on failure.
    """
    result: dict[str, str] = {}
    clean_isbns = [isbn for isbn in isbns if isbn]
    if not clean_isbns:
        return result
    raw = _fetch_raw(_LT_WORK_INFO_URL.format(isbns=",".join(clean_isbns)), timeout=30)
    if raw is None:
        return result
    start_marker = "LT_addLibraryThinglinks("
    start = raw.rfind(start_marker)
    if start == -1:
        print("LT work info: unexpected response format.")
        return result
    start_json = raw.find("{", start + len(start_marker))
    end = raw.find(");", start_json)
    if start_json == -1 or end == -1:
        print("LT work info: unexpected response format.")
        return result
    payload_str = raw[start_json:end]
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError as exc:
        print(f"LT work info: JSON parse error: {exc}")
        return result
    books_info = payload if isinstance(payload, dict) else {}
    for isbn, info in books_info.items():
        if isinstance(info, dict) and info.get("link"):
            result[str(isbn)] = str(info["link"])
    return result


def _make_book_entry(
    book: dict,
    work_links: Mapping[str, str],
) -> dict[str, str]:
    """Build a book entry dict from a LibraryThing record.

    Args:
        book: Raw LT book record.
        work_links: Mapping of ISBN to LibraryThing work link.

    Returns:
        Book entry with title, link, imageUrl, author, rating, description.
    """
    book_id = book.get("book_id", "")
    isbn = book.get("ISBN_cleaned") or book.get("ISBN") or ""
    link = work_links.get(isbn, "") or f"https://www.librarything.com/work/{book_id}"
    return {
        "title": book.get("title", ""),
        "link": link,
        "imageUrl": book.get("cover", ""),
        "author": book.get("author_fl") or book.get("author_lf", ""),
        "rating": str(book.get("rating") or "0"),
        "description": "",
    }


def _map_lt_to_shelves(
    lt_books: dict[str, dict],
    work_links: Mapping[str, str],
) -> dict[str, list[dict[str, str]]]:
    """Map LibraryThing book records to internal shelf names.

    A book belongs to every shelf whose criteria it matches:
    - currently-reading: collection 7
    - curated: tag 'curated'
    - read: collection 1096112

    Args:
        lt_books: Mapping of book_id to LT book record.
        work_links: Mapping of ISBN to LibraryThing work link.

    Returns:
        Mapping of shelf name to book entries.
    """
    shelves: dict[str, list[dict[str, str]]] = {s: [] for s in SHELVES}
    for book in lt_books.values():
        collections: dict[str, str] = book.get("collections") or {}
        tags: list[str] = book.get("tags") or []
        entry = _make_book_entry(book, work_links)
        if _LT_COLLECTION_CURRENTLY_READING in collections:
            shelves["currently-reading"].append(entry)
        if _LT_TAG_CURATED in tags:
            shelves["curated"].append(entry)
        if _LT_COLLECTION_READ in collections:
            shelves["read"].append(entry)
    return shelves


def _fetch_lt_books() -> dict[str, list[dict[str, str]]] | None:
    """Fetch all books from the LibraryThing JSON API across all pages.

    Paginates through api_getdata.php until all books in the account are
    retrieved, resolves work links, and maps books to shelves.

    Returns:
        Mapping of shelf name to book entries, or None when the initial fetch fails.
    """
    all_books: dict[str, dict] = {}
    page = 1
    max_pages = 50
    while page <= max_pages:
        url = _LT_API_URL.format(username=_LT_USERNAME, page=page)
        raw = _fetch_raw(url)
        if raw is None:
            if page == 1:
                return None
            print(f"LT API: warning: page {page} fetch failed, using {len(all_books)} books.")
            break
        m = _LT_JSON_RE.search(raw)
        if not m:
            if page == 1:
                print("LT API: unexpected response format.")
                return None
            break
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError as exc:
            if page == 1:
                print(f"LT API: JSON parse error: {exc}")
                return None
            break
        page_books = data.get("books") or {}
        if not page_books:
            break
        new_books = 0
        for bid, book in page_books.items():
            if bid not in all_books:
                all_books[bid] = book
                new_books += 1
        if new_books == 0:
            break
        page += 1

    isbns = [str(book.get("ISBN_cleaned") or book.get("ISBN") or "") for book in all_books.values()]
    work_links = _lt_work_links(isbns)
    result = _map_lt_to_shelves(all_books, work_links)
    total = sum(len(v) for v in result.values())
    print(f"LT API: fetched {len(all_books)} books across {page} pages, mapped {total} shelf entries.")
    return result


def _load_books() -> dict[str, list[dict[str, str]]]:
    """Load bookshelf entries from books.json.

    Used as a fallback when the LibraryThing API is unreachable.

    Returns:
        Mapping of shelf name to book entries.
    """
    books_data: dict[str, list[dict[str, str]]] = {shelf: [] for shelf in SHELVES}
    if not BOOKS_PATH.exists():
        return books_data
    data = json.loads(BOOKS_PATH.read_text(encoding="utf-8"))
    for shelf in SHELVES:
        books_data[shelf] = list(data.get(shelf) or [])
    return books_data


def _total_books(books_data: dict[str, list[dict[str, str]]]) -> int:
    """Count the total number of books across all shelves.

    Args:
        books_data: Mapping of shelf name to book entries.

    Returns:
        Total number of book entries.
    """
    return sum(len(books or []) for books in books_data.values())


def _exceeds_loss(previous_count: int, new_count: int, limit: float = 0.5) -> bool:
    """Return True when content loss is over the limit.

    Args:
        previous_count: Total book entries before the update.
        new_count: Total book entries after the update.
        limit: Allowed loss ratio. Loss over this ratio counts as removal.

    Returns:
        True when the new content drops by more than the limit.
    """
    if previous_count <= 0:
        return False
    return new_count < previous_count * limit


def fetch_books() -> None:
    """Fetch books from LibraryThing and write books.json.

    Fetches live data from the LibraryThing JSON API.

    Falls back to the existing books.json when the LT API is unreachable.
    Writes the new data only when content loss stays under 50 percent.
    """
    previous_count = _total_books(_load_books())
    books_data = _fetch_lt_books()
    if books_data is None:
        print("LT API unavailable, falling back to books.json.")
        return
    new_count = _total_books(books_data)
    if _exceeds_loss(previous_count, new_count):
        print("Aborting books write: content would drop by more than 50 percent.")
        return
    BOOKS_PATH.write_text(json.dumps(books_data, indent=2) + "\n")
    print(f"Books data saved to {BOOKS_PATH}")


if __name__ == "__main__":
    fetch_books()
