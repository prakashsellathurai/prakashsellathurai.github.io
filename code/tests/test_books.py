"""Tests for the books utility module."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

BOOKS_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "code" / "scripts" / "utils" / "books.py"
)


@pytest.fixture(scope="module")
def books_module() -> ModuleType:
    """Load the books utility module under test."""
    spec = importlib.util.spec_from_file_location("books_under_test", BOOKS_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_total_books_counts_all_shelves(books_module: ModuleType) -> None:
    """Test that total book count sums every shelf."""
    data = {"read": [{"title": "Book One"}], "curated": [{"title": "Book Two"}]}
    assert books_module._total_books(data) == 2


def test_exceeds_loss_true_when_drop_over_half(books_module: ModuleType) -> None:
    """Test that loss over 50 percent is detected."""
    assert books_module._exceeds_loss(10, 4) is True


def test_exceeds_loss_false_when_drop_at_half(books_module: ModuleType) -> None:
    """Test that loss at exactly 50 percent is allowed."""
    assert books_module._exceeds_loss(10, 5) is False


def test_exceeds_loss_false_when_content_grows(books_module: ModuleType) -> None:
    """Test that growth is not treated as loss."""
    assert books_module._exceeds_loss(10, 12) is False


def test_exceeds_loss_false_when_previous_empty(books_module: ModuleType) -> None:
    """Test that empty previous content is not treated as loss."""
    assert books_module._exceeds_loss(0, 0) is False


def test_map_lt_to_shelves_prefers_resolved_work_link(books_module: ModuleType) -> None:
    """Test that mapped books use the resolved LibraryThing work link."""
    lt_books = {
        "327134007": {
            "book_id": "327134007",
            "title": "The Idea Factory: Bell Labs and the Great Age of American Innovation",
            "author_fl": "Jon Gertner",
            "author_lf": "Gertner, Jon",
            "ISBN": "9780738801234",
            "ISBN_cleaned": "0738801234",
            "rating": 0,
            "cover": "",
            "tags": ["currently-reading"],
            "collections": {"1": "Your library", "7": "Currently reading"},
        }
    }
    work_links = {"0738801234": "https://www.librarything.com/work/9338746"}
    result = books_module._map_lt_to_shelves(lt_books, work_links)
    assert result["currently-reading"][0]["link"] == "https://www.librarything.com/work/9338746"


def test_map_lt_to_shelves_falls_back_to_book_link_without_work_link(
    books_module: ModuleType,
) -> None:
    """Test that mapped books fall back to the book link when no work link exists."""
    lt_books = {
        "327134007": {
            "book_id": "327134007",
            "title": "The Idea Factory: Bell Labs and the Great Age of American Innovation",
            "author_fl": "Jon Gertner",
            "author_lf": "Gertner, Jon",
            "ISBN": "9780738801234",
            "ISBN_cleaned": "0738801234",
            "rating": 0,
            "cover": "",
            "tags": ["currently-reading"],
            "collections": {"1": "Your library", "7": "Currently reading"},
        }
    }
    result = books_module._map_lt_to_shelves(lt_books, {})
    assert result["currently-reading"][0]["link"] == "https://www.librarything.com/work/327134007"
