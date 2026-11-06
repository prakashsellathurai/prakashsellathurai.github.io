#!/usr/bin/env python3
"""Fetch and cache book covers and metadata into books.json."""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path

SHELVES = ["currently-reading", "read", "curated"]
IMAGE_DIR = "./data/public/static/images/bookshelf"
BOOKS_PATH = Path("./data/non-public/books.json")
OPENLIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"
OPENLIBRARY_COVER_URL = "https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"

# LibraryThing public widget API — no authentication required.
_LT_USERNAME = "prakashsellathurai"
_LT_API_URL = (
    "https://www.librarything.com/api_getdata.php"
    f"?userid={_LT_USERNAME}&key=0&type=json&max=1000"
    "&showCollections=1&showTags=1&showRatings=1"
)
# LT collection IDs for this account (confirmed from live data).
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


def _fetch_json(url: str, timeout: int = 30) -> dict | None:
    """Fetch a JSON document over HTTP.

    Args:
        url: Absolute URL of the JSON document.

    Returns:
        Parsed JSON object, or None when the fetch fails.
    """
    raw = _fetch_raw(url, timeout=timeout)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing JSON from {url}: {e}")
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


def _fetch_lt_books() -> dict[str, list[dict[str, str]]] | None:
    """Fetch all books from the LibraryThing public widget API.

    Calls api_getdata.php, extracts the JSON payload from the JS wrapper,
    and maps each book to the correct internal shelf.

    Returns:
        Shelf mapping, or None when the fetch or parse fails.
    """
    raw = _fetch_raw(_LT_API_URL)
    if raw is None:
        return None
    m = _LT_JSON_RE.search(raw)
    if not m:
        print("LT API: unexpected response format.")
        return None
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        print(f"LT API: JSON parse error: {exc}")
        return None
    lt_books: dict[str, dict] = data.get("books") or {}
    isbns = [str(book.get("ISBN_cleaned") or book.get("ISBN") or "") for book in lt_books.values()]
    work_links = _lt_work_links(isbns)
    result = _map_lt_to_shelves(lt_books, work_links)
    total = sum(len(v) for v in result.values())
    print(f"LT API: fetched {len(lt_books)} books, mapped {total} to shelves.")
    return result


def _map_lt_to_shelves(
    lt_books: dict[str, dict],
    work_links: Mapping[str, str],
) -> dict[str, list[dict[str, str]]]:
    """Map LibraryThing book records to internal shelf names.

    Shelf priority: currently-reading > curated (by tag) > read.
    Books in the to-read collection are skipped.

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
        book_id = book.get("book_id", "")
        isbn = book.get("ISBN_cleaned") or book.get("ISBN") or ""
        link = work_links.get(isbn, "") or f"https://www.librarything.com/work/{book_id}"
        entry: dict[str, str] = {
            "title": book.get("title", ""),
            "link": link,
            "imageUrl": book.get("cover", ""),
            "author": book.get("author_fl") or book.get("author_lf", ""),
            "rating": str(book.get("rating") or "0"),
            "description": "",
        }
        if _LT_COLLECTION_CURRENTLY_READING in collections:
            shelves["currently-reading"].append(entry)
        elif _LT_TAG_CURATED in tags:
            shelves["curated"].append(entry)
        elif _LT_COLLECTION_READ in collections:
            shelves["read"].append(entry)
    return shelves


def _search_openlibrary(title: str, author: str) -> dict | None:
    """Search Open Library for a book by title and author.

    Args:
        title: Book title.
        author: Book author name.

    Returns:
        First matching Open Library work, or None when nothing matches.
    """
    query = " ".join(part for part in (title, author) if part).strip()
    if not query:
        return None
    url = f"{OPENLIBRARY_SEARCH_URL}?q={urllib.parse.quote_plus(query)}&limit=3"
    data = _fetch_json(url)
    if not data:
        return None
    docs = data.get("docs") or []
    if not docs:
        return None
    return docs[0]


def _cover_url(cover_id: int) -> str:
    """Build an Open Library cover image URL.

    Args:
        cover_id: Open Library cover id.

    Returns:
        Open Library cover image URL.
    """
    return OPENLIBRARY_COVER_URL.format(cover_id=cover_id)


def _download_image(url: str) -> str | None:
    """Download a book cover image to the local cache. Returns the local URL path or None."""
    ext = os.path.splitext(url.split("/")[-1].split("?")[0])[1]
    if not ext or len(ext) > 6:
        ext = ".jpg"
    filename = hashlib.md5(url.encode()).hexdigest() + ext
    filepath = os.path.join(IMAGE_DIR, filename)

    if os.path.exists(filepath):
        return f"/static/images/bookshelf/{filename}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        with open(filepath, "wb") as f:
            f.write(data)
        return f"/static/images/bookshelf/{filename}"
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        print(f"  Failed to download {url}: {e}")
        return None


def _enrich_book(book: dict[str, str]) -> dict[str, str]:
    """Enrich a book entry with an Open Library cover image.

    Args:
        book: Book entry from the bookshelf data.

    Returns:
        Book entry with an Open Library cover image.
    """
    enriched = dict(book)
    doc = _search_openlibrary(book.get("title", ""), book.get("author", ""))
    if doc is None:
        return enriched
    cover_id = doc.get("cover_i")
    if not cover_id:
        return enriched
    remote_url = _cover_url(int(cover_id))
    enriched["imageUrlRemote"] = remote_url
    enriched["imageUrl"] = _download_image(remote_url) or remote_url
    return enriched


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

    Fetches live data from the LibraryThing public widget API, then
    enriches each book with an Open Library cover image.

    Falls back to the existing books.json when the LT API is unreachable.
    Writes the new data only when content loss stays under 50 percent.
    """
    os.makedirs(IMAGE_DIR, exist_ok=True)
    books_data = _fetch_lt_books()
    if books_data is None:
        print("LT API unavailable, falling back to books.json.")
        books_data = _load_books()
    previous_count = _total_books(books_data)
    for shelf in SHELVES:
        books = books_data.get(shelf) or []
        books_data[shelf] = [_enrich_book(book) for book in books]
    new_count = _total_books(books_data)
    if _exceeds_loss(previous_count, new_count):
        print("Aborting books write: content would drop by more than 50 percent.")
        return
    BOOKS_PATH.write_text(json.dumps(books_data, indent=2) + "\n")
    print(f"Books data saved to {BOOKS_PATH}")


if __name__ == "__main__":
    fetch_books()
