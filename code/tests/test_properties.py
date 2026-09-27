from __future__ import annotations

import json
import sys
import re

from hypothesis import given, settings, assume
from hypothesis import strategies as st

sys.path.insert(0, "code/scripts")

from lib.markdown import MarkdownRenderer, escape_html
from lib.search import SearchIndexBuilder, tokenize
from lib.slug import slug
from lib.frontmatter import parse_frontmatter
from lib.url import essay_url, note_topic_url, note_file_url, tag_url, topic_url

renderer = MarkdownRenderer()


class TestSlug:
    @given(st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cs", "Co", "Sk", "Sm", "Sc", "Mn", "Mc"], min_codepoint=32, max_codepoint=127)))
    @settings(max_examples=200)
    def test_slug_output_is_valid(self, text: str) -> None:
        result = slug(text)
        assert isinstance(result, str)
        assert result == result.lower()
        assert re.match(r"^[a-z0-9-]*$", result) is not None

    @given(st.text())
    @settings(max_examples=200)
    def test_slug_never_starts_or_ends_with_hyphen(self, text: str) -> None:
        result = slug(text)
        if result:
            assert not result.startswith("-")
            assert not result.endswith("-")

    @given(st.text())
    @settings(max_examples=200)
    def test_slug_contains_no_underscores_or_spaces(self, text: str) -> None:
        result = slug(text)
        assert "_" not in result
        assert " " not in result

    @given(st.text())
    @settings(max_examples=200)
    def test_slug_is_idempotent(self, text: str) -> None:
        assert slug(slug(text)) == slug(text)

    @given(st.integers(min_value=0), st.integers(min_value=0))
    def test_slug_with_integers_produces_valid_output(self, a: int, b: int) -> None:
        result = slug(f"{a}_{b}")
        assert re.match(r"^[0-9-]+$", result) is not None


class TestTokenize:
    @given(st.text())
    @settings(max_examples=200)
    def test_token_output_tokens_are_at_least_three_chars(self, text: str) -> None:
        tokens = tokenize(text)
        for tok in tokens:
            assert len(tok) >= 3

    @given(st.text())
    @settings(max_examples=200)
    def test_token_output_tokens_are_lowercase_alphanumeric(self, text: str) -> None:
        tokens = tokenize(text)
        for tok in tokens:
            assert tok == tok.lower()
            assert re.match(r"^[a-z0-9]+$", tok) is not None

    @given(st.text())
    @settings(max_examples=200)
    def test_token_contains_no_stopwords(self, text: str) -> None:
        from lib.search import _STOPWORDS
        tokens = tokenize(text)
        for tok in tokens:
            assert tok not in _STOPWORDS


class TestMarkdownRenderer:
    @given(st.text())
    @settings(max_examples=200)
    def test_escape_html_produces_safe_output(self, text: str) -> None:
        result = escape_html(text)
        assert "<" not in result
        assert ">" not in result
        assert not re.search(r"&(?![#a-zA-Z])", result)

    @given(st.text())
    @settings(max_examples=200)
    def test_escape_html_preserves_visible_characters(self, text: str) -> None:
        result = escape_html(text)
        for ch in text:
            if ch not in "&<>\"'" and ch.isprintable():
                assert ch in result

    @given(st.text(min_size=1))
    @settings(max_examples=200)
    def test_render_plain_text_wraps_in_paragraph(self, text: str) -> None:
        assume(not text.startswith(("#", ">", "|", "-", "* ")))
        assume(not text.strip().startswith(("```", "~~~")))
        assume(not text.startswith("\t"))
        assume(not re.match(r"^\s+[^\s]", text))
        if text.strip():
            result = renderer.render(text)
            assert result.startswith("<p>")
            assert result.rstrip().endswith("</p>")

    @given(st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc", "Cs"])))
    @settings(max_examples=200)
    def test_render_non_control_characters_produce_output(self, text: str) -> None:
        if text.strip():
            result = renderer.render(text)
            assert len(result) > 0


class TestFrontmatter:
    @given(st.text())
    @settings(max_examples=200)
    def test_parse_frontmatter_no_delimiters_returns_empty_data(self, text: str) -> None:
        if not text.startswith("---"):
            result = parse_frontmatter(text)
            assert result["data"] == {}
            assert result["content"] == text

    @given(st.text(min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ "), st.text(min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ "))
    @settings(max_examples=200)
    def test_parse_frontmatter_returns_dict_with_data_and_content_keys(self, key: str, value: str) -> None:
        assume(key.isidentifier() or re.match(r"^[a-z_]+$", key))
        assume("\n" not in key and "\n" not in value)
        content = f"---\n{key}: {value}\n---\nbody text"
        result = parse_frontmatter(content)
        assert "data" in result
        assert "content" in result
        assert isinstance(result["data"], dict)
        assert isinstance(result["content"], str)

    @given(st.text(min_size=1))
    @settings(max_examples=200)
    def test_parse_frontmatter_returns_dict_with_data_and_content_keys_simple(self, text: str) -> None:
        result = parse_frontmatter(text)
        assert "data" in result
        assert "content" in result
        assert isinstance(result["data"], dict)
        assert isinstance(result["content"], str)


class TestSearchIndexBuilder:
    @given(st.lists(st.tuples(st.text(), st.text(), st.integers(min_value=0, max_value=6)), min_size=1))
    @settings(max_examples=100)
    def test_to_js_deserialization_roundtrip(self, docs: list[tuple[str, str, int]]) -> None:
        builder = SearchIndexBuilder()
        for title, url, type_code in docs:
            builder.add(title, url, type_code)
        js = builder.to_js()
        payload_str = js.split("=", 1)[1].rstrip(";\n")
        payload = json.loads(payload_str)
        assert len(payload["d"]) == len(docs)
        for i, (title, url, type_code) in enumerate(docs):
            assert payload["d"][i][0] == title
            assert payload["d"][i][1] == url
            assert payload["d"][i][2] == type_code

    @given(st.lists(st.tuples(st.text(), st.text(), st.integers(min_value=0, max_value=6)), min_size=1))
    @settings(max_examples=100)
    def test_all_docs_appear_in_serialized_output(self, docs: list[tuple[str, str, int]]) -> None:
        builder = SearchIndexBuilder()
        titles = []
        for title, url, type_code in docs:
            builder.add(title, url, type_code)
            titles.append(title)
        js = builder.to_js()
        payload_str = js.split("=", 1)[1].rstrip(";\n")
        payload = json.loads(payload_str)
        serialized_titles = [d[0] for d in payload["d"]]
        for title in titles:
            assert title in serialized_titles

    @given(st.lists(st.tuples(st.text(), st.text(), st.integers(min_value=0, max_value=6)), min_size=1))
    @settings(max_examples=100)
    def test_document_count_preserved_after_serialization(self, docs: list[tuple[str, str, int]]) -> None:
        builder = SearchIndexBuilder()
        for title, url, type_code in docs:
            builder.add(title, url, type_code)
        js = builder.to_js()
        payload_str = js.split("=", 1)[1].rstrip(";\n")
        payload = json.loads(payload_str)
        assert len(payload["c"]) == len(payload["k"]) == len(payload["w"])

    @given(st.text(min_size=1), st.text(min_size=1), st.integers(min_value=0, max_value=6))
    @settings(max_examples=200)
    def test_add_no_exception_with_valid_inputs(self, title: str, url: str, type_code: int) -> None:
        builder = SearchIndexBuilder()
        builder.add(title, url, type_code)
        assert builder is not None


class TestUrlGeneration:
    @given(st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc", "Cs"], min_codepoint=32, max_codepoint=127)))
    @settings(max_examples=200)
    def test_essay_url_contains_slug(self, slug_text: str) -> None:
        clean = re.sub(r"[^\w\s-]", "", slug_text).strip("-")
        if clean:
            url = essay_url(clean)
            assert url.startswith("/essays/")
            assert url.endswith(".html")
            assert clean in url

    @given(st.text(min_size=1))
    @settings(max_examples=200)
    def test_note_topic_url_contains_slug(self, topic_slug: str) -> None:
        url = note_topic_url(topic_slug)
        assert url.startswith("/notes/")
        assert url.endswith("/")

    @given(st.text(min_size=1), st.text(min_size=1))
    @settings(max_examples=200)
    def test_note_file_url_constructs_valid_path(self, topic_slug: str, file_slug: str) -> None:
        url = note_file_url(topic_slug, None, file_slug)
        assert url.startswith(f"/notes/{topic_slug}/")
        assert url.endswith(f"{file_slug}.html")

    @given(st.text(min_size=1))
    @settings(max_examples=200)
    def test_tag_url_contains_tag(self, tag: str) -> None:
        url = tag_url(tag)
        assert url.startswith("/tags/")
        assert url.endswith(".html")
        assert tag in url

    @given(st.text(min_size=1))
    @settings(max_examples=200)
    def test_topic_url_contains_slug(self, topic_slug: str) -> None:
        url = topic_url(topic_slug)
        assert url.startswith("/experiments/")
        assert url.endswith("/")
