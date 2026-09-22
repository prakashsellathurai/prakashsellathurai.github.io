"""Parse YAML frontmatter from markdown files."""

from __future__ import annotations

import re
from typing import Any

import yaml


def parse_frontmatter(content: str) -> dict[str, Any]:
    """Parse YAML frontmatter from a string.

    Extracts YAML data between ``---`` delimiters at the start of the
    content and returns it alongside the remaining body.

    Args:
        content: Raw file content that may contain YAML frontmatter.

    Returns:
        Dictionary with ``data`` (parsed YAML dict) and ``content``
        (body text after the frontmatter block).
    """
    match = re.match(r"^---\r?\n([\s\S]*?)\r?\n(?:---|\.\.\.)\r?\n?", content)
    if not match:
        return {"data": {}, "content": content}

    raw = match.group(1)
    body = content[match.end() :]
    data = yaml.safe_load(raw) or {}

    return {"data": data, "content": body}
