import sys
sys.path.insert(0, "code/scripts")

from lib.markdown import MarkdownRenderer

renderer = MarkdownRenderer()


class TestHeadings:
    def test_h1(self):
        assert renderer.render("# Title") == "<h1>Title</h1>"

    def test_h2(self):
        assert renderer.render("## Section") == "<h2>Section</h2>"

    def test_h3(self):
        assert renderer.render("### Subsection") == "<h3>Subsection</h3>"

    def test_h4(self):
        assert renderer.render("#### Sub-subsection") == "<h4>Sub-subsection</h4>"

    def test_h5(self):
        assert renderer.render("##### Level 5") == "<h5>Level 5</h5>"

    def test_h6(self):
        assert renderer.render("###### Level 6") == "<h6>Level 6</h6>"

    def test_heading_with_inline_formatting(self):
        result = renderer.render("# **Bold** and *italic*")
        assert "<h1><strong>Bold</strong> and <em>italic</em></h1>" in result

    def test_heading_with_link(self):
        result = renderer.render("## [text](https://example.com)")
        assert '<h2><a href="https://example.com">text</a></h2>' in result

    def test_heading_with_inline_code(self):
        result = renderer.render("# Use `code` here")
        assert "<h1>Use <code>code</code> here</h1>" in result

    def test_heading_escapes_html(self):
        result = renderer.render("# <script>alert('xss')</script>")
        assert "&#039;xss&#039;" in result
        assert "<script>" not in result


class TestFencedCodeBlocks:
    def test_basic_code_block(self):
        md = "```\nprint('hello')\n```"
        result = renderer.render(md)
        assert "<pre><code>" in result
        assert "print(&#039;hello&#039;)" in result
        assert "</code></pre>" in result

    def test_code_block_with_language(self):
        md = "```python\nimport os\n```"
        result = renderer.render(md)
        assert '<pre><code class="language-python">' in result
        assert "import os" in result

    def test_code_block_escapes_html(self):
        md = "```\n<div>tag</div>\n```"
        result = renderer.render(md)
        assert "&lt;div&gt;" in result
        assert "<div>" not in result

    def test_multi_line_code_block(self):
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

    def test_code_block_between_paragraphs(self):
        md = "para1\n\n```\ncode\n```\n\npara2"
        result = renderer.render(md)
        assert "<p>para1</p>" in result
        assert "<pre><code>" in result
        assert "<p>para2</p>" in result

    def test_consecutive_code_blocks(self):
        md = "```\nfirst\n```\n\n```\nsecond\n```"
        result = renderer.render(md)
        first = result.find("<pre><code>")
        second = result.find("<pre><code>", first + 1)
        assert first != -1
        assert second != -1
        assert result.find("first") < result.find("second")

    def test_empty_code_block(self):
        md = "```\n```"
        result = renderer.render(md)
        assert "<pre><code>" in result

    def test_code_block_with_crlf(self):
        md = "```\r\ncode\r\n```\r\n"
        result = renderer.render(md)
        assert "<pre><code>" in result
        assert "code" in result


class TestBlockquotes:
    def test_basic_blockquote(self):
        md = "> hello"
        result = renderer.render(md)
        assert "<blockquote>" in result
        assert "<p>hello</p>" in result

    def test_multi_line_blockquote(self):
        md = "> line1\n> line2"
        result = renderer.render(md)
        assert "<p>line1 line2</p>" in result


class TestHeadingsWithCodeBlocks:
    def test_heading_between_code_blocks(self):
        md = "```\ncode1\n```\n\n## Heading\n\n```\ncode2\n```"
        result = renderer.render(md)
        code1 = result.find("<pre><code>")
        heading = result.find("<h2>")
        code2 = result.find("<pre><code>", heading)
        assert code1 < heading < code2

    def test_notes_content(self):
        md = """## Pipelining & Instruction level parallelism
conventional thinking tells Instructions are excuted one afer another"""

        result = renderer.render(md)
        assert "<h2>Pipelining &amp; Instruction level parallelism</h2>" in result
        assert "<p>conventional thinking" in result

    def test_code_block_with_tabular_data(self):
        md = "```\nSPECint95\tSPECfp95\n195 MHz\tMIPS R10000\n```"
        result = renderer.render(md)
        assert "SPECint95" in result
        assert "SPECfp95" in result


class TestParagraphs:
    def test_basic_paragraph(self):
        assert renderer.render("hello world") == "<p>hello world</p>"

    def test_multi_line_paragraph(self):
        md = "line1\nline2\nline3"
        result = renderer.render(md)
        assert "<p>line1 line2 line3</p>" in result

    def test_multiple_paragraphs(self):
        md = "para1\n\npara2"
        result = renderer.render(md)
        assert result == "<p>para1</p>\n<p>para2</p>"


class TestInlineFormatting:
    def test_bold(self):
        assert renderer.render("**bold**") == "<p><strong>bold</strong></p>"

    def test_italic(self):
        assert renderer.render("*italic*") == "<p><em>italic</em></p>"

    def test_inline_code(self):
        assert renderer.render("`code`") == "<p><code>code</code></p>"

    def test_link(self):
        result = renderer.render("[text](https://example.com)")
        assert '<a href="https://example.com">text</a>' in result


class TestEdgeCases:
    def test_empty_string(self):
        assert renderer.render("") == ""

    def test_only_whitespace(self):
        assert renderer.render("   \n\n  ") == ""

    def test_special_chars_escaped(self):
        result = renderer.render("a & b < c > d")
        assert "a &amp; b &lt; c &gt; d" in result
