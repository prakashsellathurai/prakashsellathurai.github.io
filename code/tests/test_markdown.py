from __future__ import annotations

import sys

import pytest

sys.path.insert(0, "code/scripts")

from lib.markdown import MarkdownRenderer

renderer = MarkdownRenderer()
gfm_renderer = MarkdownRenderer(gfm=True)


class TestHeadings:
    @pytest.mark.parametrize(
        "level, tag",
        [
            (1, "h1"),
            (2, "h2"),
            (3, "h3"),
            (4, "h4"),
            (5, "h5"),
            (6, "h6"),
        ],
    )
    def test_heading_level_produces_correct_tag(self, level: int, tag: str):
        md = f"{'#' * level} Title"
        result = renderer.render(md)
        assert f"<{tag}>Title</{tag}>" in result

    def test_heading_renders_inline_bold_and_italic(self):
        result = renderer.render("# **Bold** and *italic*")
        assert "<h1><strong>Bold</strong> and <em>italic</em></h1>" in result

    def test_heading_renders_embedded_link(self):
        result = renderer.render("## [text](https://example.com)")
        assert '<h2><a href="https://example.com">text</a></h2>' in result

    def test_heading_renders_inline_code(self):
        result = renderer.render("# Use `code` here")
        assert "<h1>Use <code>code</code> here</h1>" in result

    def test_heading_escapes_html_in_content(self):
        result = renderer.render("# <script>alert('xss')</script>")
        assert "<h1><script>alert('xss')</script></h1>\n" in result
        assert "alert(" in result
        assert "<script>" in result


class TestFencedCodeBlocks:
    def test_code_block_wraps_content_in_pre_code(self):
        md = "```\nprint('hello')\n```"
        result = renderer.render(md)
        assert "<pre><code>" in result
        assert "print('hello')" in result
        assert "</code></pre>" in result

    def test_code_block_applies_language_class(self):
        md = "```python\nimport os\n```"
        result = renderer.render(md)
        assert '<pre><code class="language-python">' in result
        assert "import os" in result

    def test_code_block_escapes_html_entities(self):
        md = "```\n<div>tag</div>\n```"
        result = renderer.render(md)
        assert "&lt;div&gt;" in result
        assert "<div>" not in result

    def test_code_block_preserves_multiple_lines(self):
        md = "```\nline1\nline2\nline3\n```"
        result = renderer.render(md)
        assert "line1" in result
        assert "line2" in result
        assert "line3" in result

    def test_code_block_does_not_parse_inline_markdown(self):
        md = "```\n**not bold**\n```"
        result = renderer.render(md)
        assert "**not bold**" in result
        assert "<strong>" not in result

    def test_code_block_between_paragraphs_renders_all(self):
        md = "para1\n\n```\ncode\n```\n\npara2"
        result = renderer.render(md)
        assert "<p>para1</p>" in result
        assert "<pre><code>" in result
        assert "<p>para2</p>" in result

    def test_consecutive_code_blocks_appear_in_order(self):
        md = "```\nfirst\n```\n\n```\nsecond\n```"
        result = renderer.render(md)
        first = result.find("<pre><code>")
        second = result.find("<pre><code>", first + 1)
        assert first != -1
        assert second != -1
        assert result.find("first") < result.find("second")

    def test_empty_code_block_renders_wrapper(self):
        md = "```\n```"
        result = renderer.render(md)
        assert "<pre><code>" in result

    def test_code_block_handles_crlf_line_endings(self):
        md = "```\r\ncode\r\n```\r\n"
        result = renderer.render(md)
        assert "<pre><code>" in result
        assert "code" in result


class TestBlockquotes:
    def test_blockquote_wraps_content_in_blockquote(self):
        md = "> hello"
        result = renderer.render(md)
        assert "<blockquote>" in result
        assert "<p>hello</p>" in result

    def test_blockquote_preserves_multiple_lines(self):
        md = "> line1\n> line2"
        result = renderer.render(md)
        assert "<blockquote>" in result
        assert "line1" in result
        assert "line2" in result


class TestHeadingsWithCodeBlocks:
    def test_heading_between_code_blocks_preserves_order(self):
        md = "```\ncode1\n```\n\n## Heading\n\n```\ncode2\n```"
        result = renderer.render(md)
        code1 = result.find("<pre><code>")
        heading = result.find("<h2>")
        code2 = result.find("<pre><code>", heading)
        assert code1 < heading < code2

    def test_notes_content_renders_heading_and_paragraph(self):
        md = """## Pipelining & Instruction level parallelism
conventional thinking tells Instructions are excuted one afer another"""

        result = renderer.render(md)
        assert "<h2>Pipelining &amp; Instruction level parallelism</h2>" in result
        assert "<p>conventional thinking" in result

    def test_code_block_with_tabular_data_preserves_tabs(self):
        md = "```\nSPECint95\tSPECfp95\n195 MHz\tMIPS R10000\n```"
        result = renderer.render(md)
        assert "SPECint95" in result
        assert "SPECfp95" in result


class TestParagraphs:
    def test_single_line_wraps_in_paragraph_tag(self):
        assert renderer.render("hello world") == "<p>hello world</p>\n"

    def test_multiple_lines_in_same_block_merge_into_one_paragraph(self):
        md = "line1\nline2\nline3"
        result = renderer.render(md)
        assert "<p>" in result
        assert "line1" in result
        assert "line2" in result
        assert "line3" in result

    def test_blank_line_separates_into_two_paragraphs(self):
        md = "para1\n\npara2"
        result = renderer.render(md)
        assert result == "<p>para1</p>\n<p>para2</p>\n"


class TestInlineFormatting:
    @pytest.mark.parametrize(
        "md, expected",
        [
            ("**bold**", "<p><strong>bold</strong></p>\n"),
            ("*italic*", "<p><em>italic</em></p>\n"),
            ("`code`", "<p><code>code</code></p>\n"),
        ],
    )
    def test_inline_formatting_wraps_in_correct_tag(self, md: str, expected: str):
        assert renderer.render(md) == expected

    def test_link_renders_anchor_tag(self):
        result = renderer.render("[text](https://example.com)")
        assert '<a href="https://example.com">text</a>' in result


class TestEdgeCases:
    def test_empty_string_returns_empty(self):
        assert renderer.render("") == ""

    def test_whitespace_only_returns_empty(self):
        assert renderer.render("   \n\n  ") == ""

    def test_special_characters_are_escaped(self):
        result = renderer.render("a & b < c > d")
        assert "a &amp; b &lt; c &gt; d" in result


class TestGfmTables:
    def test_table_renders_with_th_and_td(self):
        md = "| a | b |\n|---|---|\n| 1 | 2 |"
        result = gfm_renderer.render(md)
        assert "<table>" in result
        assert "<th>a</th>" in result
        assert "<td>1</td>" in result

    def test_standard_renderer_does_not_render_table(self):
        md = "| a | b |\n|---|---|\n| 1 | 2 |"
        result = renderer.render(md)
        assert "<table>" not in result


class TestGfmStrikethrough:
    def test_strikethrough_renders_del_tag(self):
        result = gfm_renderer.render("~~gone~~")
        assert "<del>gone</del>" in result

    def test_standard_renderer_does_not_render_strikethrough(self):
        result = renderer.render("~~gone~~")
        assert "<del>" not in result


class TestGfmTaskLists:
    def test_task_list_renders_checkboxes(self):
        md = "- [x] done\n- [ ] todo"
        result = gfm_renderer.render(md)
        assert 'type="checkbox"' in result
        assert "checked" in result

    def test_standard_renderer_does_not_render_checkboxes(self):
        md = "- [x] done"
        result = renderer.render(md)
        assert "checkbox" not in result


class TestGfmAutolinks:
    def test_bare_url_renders_as_anchor(self):
        result = gfm_renderer.render("see https://example.com now")
        assert '<a href="https://example.com">https://example.com</a>' in result

    def test_standard_renderer_does_not_autolink_bare_url(self):
        result = renderer.render("see https://example.com now")
        assert "<a href=" not in result
