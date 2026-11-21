#!/usr/bin/env python3
"""Fetch and cache book metadata into books.json."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path

SHELVES = ["currently-reading", "read", "curated"]
IMAGE_DIR = "./data/public/static/images/bookshelf"
BOOKS_PATH = Path("./data/non-public/books.json")

# LibraryThing public JSON API — no authentication required.
_LT_USERNAME = "prakashsellathurai"
_LT_API_BASE = (
    "https://www.librarything.com/api_getdata.php"
    f"?userid={_LT_USERNAME}&key=0&type=json&max=1000"
    "&showCollections=1&showTags=1&showRatings=1"
)
# LT collection IDs for this account (confirmed from live data).
_LT_COLLECTION_CURRENTLY_READING = "7"
_LT_COLLECTION_READ = "1096112"
_LT_TAG_CURATED = "curated"
_LT_API_URL_CURATED = f"{_LT_API_BASE}&tag={_LT_TAG_CURATED}"
_LT_API_URL_CURRENTLY_READING = (
    f"{_LT_API_BASE}&collection={_LT_COLLECTION_CURRENTLY_READING}"
)
_LT_API_URL_READ = f"{_LT_API_BASE}&collection={_LT_COLLECTION_READ}"
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


def _lt_api_url(shelf: str) -> str:
    """Build the LibraryThing JSON API URL for one shelf.

    Args:
        shelf: Internal shelf name.

    Returns:
        JSON API URL filtered to the shelf.
    """
    if shelf == "curated":
        return _LT_API_URL_CURATED
    if shelf == "currently-reading":
        return _LT_API_URL_CURRENTLY_READING
    return _LT_API_URL_READ


def _fetch_lt_shelf(shelf: str) -> list[dict[str, str]] | None:
    """Fetch books for one shelf from the LibraryThing JSON API.

    Args:
        shelf: Internal shelf name.

    Returns:
        Book entries for the shelf, or None when the fetch or parse fails.
    """
    raw = _fetch_raw(_lt_api_url(shelf))
    if raw is None:
        return None
    m = _LT_JSON_RE.search(raw)
    if not m:
        print(f"LT API: unexpected response format for shelf {shelf}.")
        return None
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        print(f"LT API: JSON parse error for shelf {shelf}: {exc}")
        return None
    lt_books: dict[str, dict] = data.get("books") or {}
    isbns = [str(book.get("ISBN_cleaned") or book.get("ISBN") or "") for book in lt_books.values()]
    work_links = _lt_work_links(isbns)
    shelves = _map_lt_to_shelves(lt_books, work_links)
    return shelves.get(shelf) or []


def _fetch_lt_books() -> dict[str, list[dict[str, str]]] | None:
    """Fetch books for each shelf from the LibraryThing JSON API.

    Returns:
        Mapping of shelf name to book entries, or None when any fetch fails.
    """
    books_data: dict[str, list[dict[str, str]]] = {}
    for shelf in SHELVES:
        books = _fetch_lt_shelf(shelf)
        if books is None:
            return None
        books_data[shelf] = books
    return books_data


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
    os.makedirs(IMAGE_DIR, exist_ok=True)
    books_data = _fetch_lt_books()
    if books_data is None:
        print("LT API unavailable, falling back to books.json.")
        books_data = _load_books()
    previous_count = _total_books(books_data)
    new_count = _total_books(books_data)
    if _exceeds_loss(previous_count, new_count):
        print("Aborting books write: content would drop by more than 50 percent.")
        return
    BOOKS_PATH.write_text(json.dumps(books_data, indent=2) + "\n")
    print(f"Books data saved to {BOOKS_PATH}")


if __name__ == "__main__":
    fetch_books()
