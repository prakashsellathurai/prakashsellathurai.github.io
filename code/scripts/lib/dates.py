"""Date parsing and formatting utilities."""

from datetime import datetime


def parse_date(date_str: str) -> datetime:
    """Parse an ISO date string (with optional trailing 'Z') to datetime."""
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))


def format_date_iso(date_str: str) -> str:
    """Format a date string as ISO 8601 for structured data."""
    return parse_date(date_str).isoformat()


def format_date(date_str: str) -> str:
    """Format a date string for human display (e.g. 'Aug 07, 2026')."""
    return parse_date(date_str).strftime("%b %d, %Y")
