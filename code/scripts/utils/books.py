#!/usr/bin/env python3
"""Fetch and cache book covers and metadata into books.json."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SHELVES = ["currently-reading", "read", "curated"]
IMAGE_DIR = "./data/public/static/images/bookshelf"
BOOKS_PATH = Path("./data/non-public/books.json")
OPENLIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"
OPENLIBRARY_COVER_URL = "https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"


def _fetch_json(url: str, timeout: int = 30) -> dict | None:
    """Fetch a JSON document over HTTP.

    Args:
        url: Absolute URL of the JSON document.

    Returns:
        Parsed JSON object, or None when the fetch fails.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
        print(f"Error fetching {url}: {e}")
        return None


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


def fetch_books() -> None:
    """Fetch book covers from Open Library and write books.json.

    Books live in books.json. This step keeps cover images fresh via Open Library.
    """
    os.makedirs(IMAGE_DIR, exist_ok=True)
    books_data = _load_books()
    for shelf in SHELVES:
        books = books_data.get(shelf) or []
        books_data[shelf] = [_enrich_book(book) for book in books]
    BOOKS_PATH.write_text(json.dumps(books_data, indent=2) + "\n")
    print(f"Books data saved to {BOOKS_PATH}")


if __name__ == "__main__":
    fetch_books()
