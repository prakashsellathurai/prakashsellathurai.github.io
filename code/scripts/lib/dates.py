"""Date parsing and formatting utilities."""
from __future__ import annotations

from datetime import datetime


def parse_date(date_str: str) -> datetime:
    """Parse an ISO date string to a datetime object.

    Handles the trailing 'Z' UTC suffix by converting it to '+00:00'.

    Args:
        date_str: ISO 8601 date string, optionally ending with 'Z'.

    Returns:
        Timezone-aware datetime object.

    Raises:
        ValueError: If date_str is not a valid ISO format string.
    """
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))


def format_date_iso(date_str: str) -> str:
    """Reformat a date string as ISO 8601 for structured data.

    Args:
        date_str: ISO 8601 date string (may contain 'Z' suffix).

    Returns:
        Normalized ISO 8601 string with timezone offset.
    """
    return parse_date(date_str).isoformat()


def format_date(date_str: str) -> str:
    """Format a date string for human-readable display.

    Args:
        date_str: ISO 8601 date string.

    Returns:
        Formatted string like 'Aug 07, 2026'.
    """
    return parse_date(date_str).strftime("%b %d, %Y")
