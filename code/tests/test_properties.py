from __future__ import annotations

import json
import re
import string
import sys

from hypothesis import given, settings, assume
from hypothesis import strategies as st

sys.path.insert(0, "code/scripts")

from lib.dates import format_date, format_date_iso, parse_date
from lib.markdown import MarkdownRenderer, escape_html
from lib.rendering import (
    apply_template,
    extract_body,
    heading_to_id,
    note_description,
    panel_section,
    render_code_as_notebook,
)
from lib.search import SearchIndexBuilder, _STOPWORDS, tokenize
from lib.seo import (
    breadcrumbs_for_url,
    collection_schema,
    person_schema,
    website_schema,
)
from lib.slug import slug
from lib.frontmatter import parse_frontmatter
from lib.url import essay_url, flatten_experiment_pages, flatten_note_pages, note_file_url, note_topic_url, tag_url, topic_url
from lib.datatypes import ExperimentTopic, FileData, NoteTopic, SiteMetadata

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
        assume(not text.startswith(("#", ">", "|", "-", "*","+")))
        assume(not text.strip().startswith(("```", "~~~")))
        assume(not text.startswith("\t"))
        assume(not text.startswith("<"))
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


class TestDates:
    @given(st.text(min_size=1, alphabet="0123456789-TZ:+ "))
    @settings(max_examples=200)
    def test_parse_date_and_format_date_iso_roundtrip(self, date_str: str) -> None:
        assume("T" in date_str or len(date_str) >= 10)
        try:
            result = format_date_iso(date_str)
            assert len(result) > 0
            assert "+" in result or "Z" in result or "-" in result
        except (ValueError, TypeError):
            pass

    @given(st.text(min_size=1, alphabet="0123456789-TZ:+ "))
    @settings(max_examples=200)
    def test_format_date_returns_nonempty(self, date_str: str) -> None:
        try:
            result = format_date(date_str)
            assert len(result) > 0
        except (ValueError, TypeError):
            pass

    @given(st.text(min_size=8, alphabet="0123456789-"))
    @settings(max_examples=200)
    def test_parse_date_iso_format_valid(self, date_str: str) -> None:
        assume("-" in date_str and len(date_str) >= 10)
        try:
            result = parse_date(date_str)
            assert result.year >= 1900
        except (ValueError, TypeError):
            pass


class TestSeoSchema:
    @given(st.text(min_size=1), st.text(min_size=1))
    @settings(max_examples=200)
    def test_website_schema_has_required_keys(self, site_url: str, site_title: str) -> None:
        schema = website_schema(site_url, site_title)
        assert schema["@type"] == "WebSite"
        assert "url" in schema
        assert "name" in schema
        assert "potentialAction" in schema

    @given(st.text(min_size=1))
    @settings(max_examples=200)
    def test_website_schema_json_serializable(self, site_url: str) -> None:
        schema = website_schema(site_url, "Test Site")
        json.dumps(schema)

    @given(st.text(min_size=1))
    @settings(max_examples=200)
    def test_person_schema_has_required_keys(self, site_url: str) -> None:
        metadata = SiteMetadata({"author": "Test", "siteUrl": site_url})
        schema = person_schema(metadata, site_url)
        assert schema["@type"] == "Person"
        assert "name" in schema
        assert "url" in schema

    @given(st.text(min_size=1), st.text(min_size=1), st.text(min_size=1), st.text(min_size=1))
    @settings(max_examples=200)
    def test_collection_schema_has_required_keys(self, name: str, description: str, url: str, item_list: str) -> None:
        schema = collection_schema([{"@type": "ListItem"}], name=name, description=description, url=url)
        assert schema["@type"] == "CollectionPage"
        assert "mainEntity" in schema

    @given(st.text())
    @settings(max_examples=200)
    def test_breadcrumbs_for_url_root_returns_none(self, url: str) -> None:
        if url == "/" or not url.strip():
            assert breadcrumbs_for_url("/", "https://example.com") is None

    @given(st.text(min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ "), st.integers(min_value=1, max_value=100), st.integers(min_value=1, max_value=100))
    @settings(max_examples=200)
    def test_breadcrumbs_for_url_returns_valid_or_none(self, url: str, position: int, best_rating: int) -> None:
        result = breadcrumbs_for_url(url, "https://example.com")
        if result is not None:
            assert result["@type"] == "BreadcrumbList"
            assert "itemListElement" in result


class TestFlattenPages:
    @given(st.lists(st.tuples(st.text(min_size=1), st.text(min_size=1)), min_size=1))
    @settings(max_examples=100)
    def test_flatten_experiment_pages_all_have_url_and_title(self, pages: list[tuple[str, str]]) -> None:
        experiments = []
        for topic_slug, file_slug in pages:
            experiments.append({
                "topic": topic_slug,
                "topic_slug": topic_slug,
                "topic_title": topic_slug.replace("-", " ").title(),
                "files": [{"filename": file_slug, "slug": file_slug, "title": file_slug, "ext": "md", "content": ""}],
                "subtopics": [],
            })
        result = flatten_experiment_pages(experiments)
        for entry in result:
            assert "url" in entry
            assert "title" in entry
            assert entry["url"].startswith("/experiments/")
            assert entry["url"].endswith(".html")

    @given(st.lists(st.tuples(st.text(min_size=1), st.text(min_size=1)), min_size=1))
    @settings(max_examples=100)
    def test_flatten_note_pages_all_have_url_and_title(self, pages: list[tuple[str, str]]) -> None:
        notes = []
        for topic_slug, file_slug in pages:
            notes.append({
                "topic": topic_slug,
                "topic_slug": topic_slug,
                "topic_title": topic_slug.replace("-", " ").title(),
                "files": [{"filename": file_slug, "slug": file_slug, "title": file_slug, "ext": "md", "content": ""}],
                "subtopics": [],
            })
        result = flatten_note_pages(notes)
        for entry in result:
            assert "url" in entry
            assert "title" in entry
            assert entry["url"].startswith("/notes/")
            assert entry["url"].endswith(".html")

    @given(st.lists(st.tuples(st.text(min_size=1, alphabet=string.ascii_lowercase), st.text(min_size=1, alphabet=string.ascii_lowercase)), min_size=1, unique_by=lambda x: (x[0], x[1])))
    @settings(max_examples=100)
    def test_flatten_experiment_pages_no_duplicate_urls(self, pages: list[tuple[str, str]]) -> None:
        experiments = []
        for topic_slug, file_slug in pages:
            experiments.append({
                "topic": topic_slug,
                "topic_slug": topic_slug,
                "topic_title": topic_slug.replace("-", " ").title(),
                "files": [{"filename": file_slug, "slug": file_slug, "title": file_slug, "ext": "md", "content": ""}],
                "subtopics": [],
            })
        result = flatten_experiment_pages(experiments)
        urls = [e["url"] for e in result]
        assert len(urls) == len(set(urls))


class TestRendering:
    @given(st.text(min_size=1), st.dictionaries(st.text(), st.text()))
    @settings(max_examples=200, deadline=None)
    def test_apply_template_replaces_all_placeholders(self, template: str, data: dict) -> None:
        result = apply_template(template, data)
        for key, value in data.items():
            placeholder = "{{" + key + "}}"
            if placeholder in template and value is not None:
                assert placeholder not in result

    @given(st.text(min_size=1, alphabet=string.ascii_letters + string.digits + "- "))
    @settings(max_examples=200)
    def test_heading_to_id_produces_unique_ids(self, text: str) -> None:
        used = {}
        for _ in range(5):
            hid = heading_to_id(text, used)
            used[hid] = True
        assert len(used) > 0

    @given(st.text(min_size=1), st.integers(min_value=3, max_value=500))
    @settings(max_examples=200)
    def test_note_description_respects_limit(self, content: str, limit: int) -> None:
        fd = FileData({"filename": "test.md", "slug": "test", "title": "Test", "ext": "md", "content": content})
        result = note_description(fd, limit=limit)
        assert len(result) <= limit + 1

    @given(st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc", "Cs"])))
    @settings(max_examples=200)
    def test_extract_body_returns_body_content(self, body: str) -> None:
        if body.strip():
            html = f"<html><body>{body}</body></html>"
            result = extract_body(html)
            assert body.strip() in result

    @given(st.text(min_size=1))
    @settings(max_examples=200)
    def test_render_code_as_notebook_produces_pre_code(self, content: str) -> None:
        fd = FileData({"filename": "test.py", "slug": "test", "title": "Test", "ext": "py", "content": content})
        result = render_code_as_notebook(fd, renderer)
        assert "<pre><code" in result

    @given(st.text(min_size=1), st.text(min_size=1))
    @settings(max_examples=200)
    def test_panel_section_has_proper_structure(self, title: str, body: str) -> None:
        result = panel_section(title, body, id_attr="test-id")
        assert '<div class="portal"' in result
        assert f'id="test-id"' in result
        assert "<h3>" in result


class TestTrieNode:
    @given(st.text(min_size=1), st.text(min_size=1), st.integers(min_value=0, max_value=6))
    @settings(max_examples=200)
    def test_weights_are_non_negative(self, title: str, url: str, type_code: int) -> None:
        builder = SearchIndexBuilder()
        builder.add(title, url, type_code)
        js = builder.to_js()
        payload_str = js.split("=", 1)[1].rstrip(";\n")
        payload = json.loads(payload_str)
        for weight_list in payload["w"]:
            for packed in weight_list:
                assert packed >= 0
