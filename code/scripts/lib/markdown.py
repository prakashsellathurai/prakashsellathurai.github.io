"""Markdown rendering with sidenote-style footnotes."""

from __future__ import annotations

import re

import mistune

_ESCAPE_TABLE = str.maketrans({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
})


def escape_html(text: str | None) -> str:
    """Escape special HTML characters in text.

    Args:
        text: String to escape. Returns empty string if None or falsy.

    Returns:
        Escaped string safe for HTML embedding.
    """
    if not text:
        return ""
    return str(text).translate(_ESCAPE_TABLE)


_PAT_FN_DEF = re.compile(r"^\[\^([\w-]+)\]:\s*(.*)")
_PAT_FN_REF = re.compile(r"\[\^([\w-]+)\]")

_PLACEHOLDER = "\x00FN:{}\x00"

_md = mistune.create_markdown(escape=False)
_md_gfm = mistune.create_markdown(
    escape=False,
    plugins=["table", "strikethrough", "task_lists", "url"],
)


class MarkdownRenderer:
    """Render Markdown to HTML with optional GitHub-Flavored extensions.

    Supports sidenote-style footnotes: definitions at the bottom of the
    content are rendered as inline sidenote elements.

    Args:
        gfm: Enable GitHub-Flavored Markdown extensions (tables,
            strikethrough, task lists, autolinks).
    """

    def __init__(self, gfm: bool = False) -> None:
        self._md = _md_gfm if gfm else _md

    def render(self, content: str) -> str:
        """Render Markdown content to HTML.

        Extracts footnotes, renders the body, then replaces footnote
        placeholders with sidenote HTML elements.

        Args:
            content: Markdown source text with optional footnote definitions.

        Returns:
            Rendered HTML string.
        """
        defs, body = self._extract_footnotes(content)
        body = _PAT_FN_REF.sub(lambda m: _PLACEHOLDER.format(m.group(1)), body)
        html = self._md(body)
        for fn_id, fn_content in defs.items():
            rendered = _md(fn_content).strip()
            if rendered.startswith("<p>") and rendered.endswith("</p>"):
                rendered = rendered[3:-4]
            sidenote = (
                f'<a class="sidenote-number" href="#sn-{fn_id}">{fn_id}</a>'
                f'<span class="sidenote" id="sn-{fn_id}"> {rendered}</span>'
            )
            html = html.replace(_PLACEHOLDER.format(fn_id), sidenote)
        return html

    def _extract_footnotes(self, text: str) -> tuple[dict[str, str], str]:
        defs: dict[str, str] = {}
        lines = text.split("\n")
        result: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            m = _PAT_FN_DEF.match(line)
            if m:
                fn_id = m.group(1)
                parts = [m.group(2)]
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    if next_line == "" or next_line[0] in (" ", "\t"):
                        parts.append("\n\n" if next_line == "" else " " + next_line.strip())
                        i += 1
                    else:
                        break
                defs[fn_id] = "".join(parts).strip()
            else:
                result.append(line)
                i += 1
        return defs, "\n".join(result)
