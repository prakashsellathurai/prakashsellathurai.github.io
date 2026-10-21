"""Asset detection and conditional script injection for templates."""

from __future__ import annotations

from dataclasses import dataclass
import re

_RE_MERMAID = re.compile(r'class=["\'][^"\']*\b(language-mermaid|mermaid)\b')
_RE_KATEX = re.compile(r"\$\$|\\\[|\\\(|(?<![\$\\])\$([^\$\s\n](?:[^\$\n]*?[^\$\s\n])?)\$(?!\$)")
_RE_HIGHLIGHT = re.compile(r'<pre><code(?![^>]*\blanguage-mermaid\b)|class=["\'](?:code_cell|notebook-cell)')

_HIGHLIGHT_HTML = """<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script>hljs.highlightAll();</script>"""

_MERMAID_HTML = """<script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/11.12.0/mermaid.min.js"></script>
<script>
  document.querySelectorAll("pre > code.language-mermaid").forEach(function (code) {
    var pre = code.parentElement;
     pre.textContent = code.textContent; // preserve the diagram text
     pre.classList.add("mermaid");
  });
  mermaid.initialize({ startOnLoad: true });
</script>"""

_KATEX_HTML = """<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/katex.min.css" crossorigin="anonymous">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/katex.min.js" crossorigin="anonymous"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/contrib/auto-render.min.js" crossorigin="anonymous" onload="renderMath()"></script>
<script>
  function renderMath() {
    if (typeof renderMathInElement === "function") {
      renderMathInElement(document.body, {
        delimiters: [
          {left: '$$', right: '$$', display: true},
          {left: '$', right: '$', display: false},
          {left: '\\\\(', right: '\\\\)', display: false},
          {left: '\\\\[', right: '\\\\]', display: true}
        ],
        throwOnError: false
      });
    }
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderMath);
  } else {
    renderMath();
  }
</script>"""


@dataclass(slots=True)
class PageAssets:
    """Tracks required client-side assets for a rendered page."""

    needs_mermaid: bool = False
    needs_katex: bool = False
    needs_highlight: bool = False

    @classmethod
    def from_content(cls, content: str) -> PageAssets:
        """Inspect HTML content and determine required assets.

        Args:
            content: Rendered HTML page content.

        Returns:
            PageAssets instance with detected requirements.
        """
        return cls(
            needs_mermaid=bool(_RE_MERMAID.search(content)),
            needs_katex=bool(_RE_KATEX.search(content)),
            needs_highlight=bool(_RE_HIGHLIGHT.search(content)),
        )

    def render_html(self) -> str:
        """Render required script and link elements.

        Returns:
            HTML string with script and link tags. Returns empty string when no assets are needed.
        """
        parts: list[str] = []
        if self.needs_highlight:
            parts.append(_HIGHLIGHT_HTML)
        if self.needs_mermaid:
            parts.append(_MERMAID_HTML)
        if self.needs_katex:
            parts.append(_KATEX_HTML)
        return "\n".join(parts)
