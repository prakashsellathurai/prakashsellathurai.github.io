from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, "code/scripts")

from lib.assets import PageAssets


class TestPageAssetsDetection:
    def test_plain_content_requires_no_assets(self) -> None:
        content = "<p>This is a plain paragraph without any special elements.</p>"
        assets = PageAssets.from_content(content)
        assert not assets.needs_mermaid
        assert not assets.needs_katex
        assert not assets.needs_highlight
        assert assets.render_html() == ""

    def test_mermaid_diagram_enables_mermaid_only(self) -> None:
        content = '<pre><code class="language-mermaid">graph TD;\nA-->B;</code></pre>'
        assets = PageAssets.from_content(content)
        assert assets.needs_mermaid
        assert not assets.needs_katex
        assert not assets.needs_highlight
        rendered = assets.render_html()
        assert "mermaid.min.js" in rendered
        assert "highlight.min.js" not in rendered
        assert "katex.min.js" not in rendered

    def test_code_block_enables_highlight_only(self) -> None:
        content = '<pre><code class="language-python">print("hello world")</code></pre>'
        assets = PageAssets.from_content(content)
        assert assets.needs_highlight
        assert not assets.needs_mermaid
        assert not assets.needs_katex
        rendered = assets.render_html()
        assert "highlight.min.js" in rendered
        assert "mermaid.min.js" not in rendered
        assert "katex.min.js" not in rendered

    def test_notebook_cell_enables_highlight(self) -> None:
        content = '<div class="code_cell"><div class="highlight"><pre>x = 1</pre></div></div>'
        assets = PageAssets.from_content(content)
        assert assets.needs_highlight
        assert "highlight.min.js" in assets.render_html()

    @pytest.mark.parametrize(
        "math_snippet",
        [
            "<p>Display math $$E = mc^2$$ in text</p>",
            "<p>Bracket display \\[a^2 + b^2 = c^2\\] here</p>",
            "<p>Parenthesis inline \\(x + y\\) here</p>",
            "<p>Inline math $x^2 + y^2 = z^2$ here</p>",
        ],
    )
    def test_math_delimiters_enable_katex_only(self, math_snippet: str) -> None:
        assets = PageAssets.from_content(math_snippet)
        assert assets.needs_katex
        assert not assets.needs_mermaid
        assert not assets.needs_highlight
        rendered = assets.render_html()
        assert "katex.min.js" in rendered
        assert "renderMath()" in rendered

    def test_currency_or_shell_dollar_does_not_trigger_katex(self) -> None:
        content = "<p>The cost is $100 and value is $200.</p>"
        assets = PageAssets.from_content(content)
        assert not assets.needs_katex

    def test_multiple_assets_combined_in_output(self) -> None:
        content = (
            '<pre><code class="language-python">x = 1</code></pre>'
            '<pre><code class="language-mermaid">graph TD; A-->B;</code></pre>'
            "<p>$$y = mx + b$$</p>"
        )
        assets = PageAssets.from_content(content)
        assert assets.needs_highlight
        assert assets.needs_mermaid
        assert assets.needs_katex
        rendered = assets.render_html()
        assert "highlight.min.js" in rendered
        assert "mermaid.min.js" in rendered
        assert "katex.min.js" in rendered


class TestConditionalAssetIntegration:
    def test_mermaid_page_loads_mermaid_script(self, out_dir: pathlib.Path) -> None:
        target = out_dir / "experiments" / "biology" / "dna-sequencing" / "readme.html"
        assert target.exists()
        html = target.read_text(encoding="utf-8")
        assert "mermaid.min.js" in html

    def test_notebook_page_loads_highlight_script(self, out_dir: pathlib.Path) -> None:
        target = (
            out_dir
            / "experiments"
            / "python"
            / "numba"
            / "np.mean"
            / "scratchbook.html"
        )
        assert target.exists()
        html = target.read_text(encoding="utf-8")
        assert "highlight.min.js" in html

    def test_clean_note_page_omits_unused_scripts(self, out_dir: pathlib.Path) -> None:
        # Find a note without diagrams or code
        notes_dir = out_dir / "notes"
        assert notes_dir.exists()
        all_notes = list(notes_dir.rglob("*.html"))
        # Exclude index pages
        detail_notes = [n for n in all_notes if n.name != "index.html"]
        assert len(detail_notes) > 0

        # Verify at least one clean note exists and omits all three libraries
        found_clean = False
        for note_file in detail_notes:
            html = note_file.read_text(encoding="utf-8")
            if (
                "mermaid.min.js" not in html
                and "katex.min.js" not in html
                and "highlight.min.js" not in html
            ):
                found_clean = True
                break
        assert found_clean, "Expected at least one note without injected scripts"
