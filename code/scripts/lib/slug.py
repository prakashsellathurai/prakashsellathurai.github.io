"""URL-safe slug generation."""

from __future__ import annotations

import re


def slug(text: str | int | float) -> str:
    """Convert text to a URL-friendly slug.

    Strips non-alphanumeric characters, lowercases, and replaces
    whitespace/underscores with hyphens.

    Args:
        text: Input to slugify. Converted to string before processing.

    Returns:
        Lowercase slug with only letters, digits, and hyphens.
    """
    s = str(text).lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    s = s.strip("-")
    return s
