"""Tests for the quotes utility module."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

QUOTES_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "code" / "scripts" / "utils" / "quotes.py"
)


@pytest.fixture(scope="module")
def quotes_module() -> ModuleType:
    """Load the quotes utility module under test."""
    spec = importlib.util.spec_from_file_location("quotes_under_test", QUOTES_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_exceeds_loss_true_when_drop_over_half(quotes_module: ModuleType) -> None:
    """Test that loss over 50 percent is detected."""
    assert quotes_module._exceeds_loss(10, 4) is True


def test_exceeds_loss_false_when_drop_at_half(quotes_module: ModuleType) -> None:
    """Test that loss at exactly 50 percent is allowed."""
    assert quotes_module._exceeds_loss(10, 5) is False


def test_exceeds_loss_false_when_content_grows(quotes_module: ModuleType) -> None:
    """Test that growth is not treated as loss."""
    assert quotes_module._exceeds_loss(10, 12) is False


def test_exceeds_loss_false_when_previous_empty(quotes_module: ModuleType) -> None:
    """Test that empty previous content is not treated as loss."""
    assert quotes_module._exceeds_loss(0, 0) is False
