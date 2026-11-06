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
