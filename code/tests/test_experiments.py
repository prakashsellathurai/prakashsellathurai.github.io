import json
import re

from playwright.sync_api import expect


def _get_schema(data, schema_type):
    if data.get("@type") == schema_type:
        return data
    if "@graph" in data:
        for item in data["@graph"]:
            if item.get("@type") == schema_type:
                return item
    return None


def _load_json_ld(page):
    text = page.locator('script[type="application/ld+json"]').text_content()
    return json.loads(text) if text else None


class TestExperimentsListPage:
    def test_should_load_successfully(self, page):
        page.goto("/experiments/")
        expect(page).to_have_title(re.compile("Experiments"))
        desc = page.locator('meta[name="description"]').get_attribute("content")
        assert "experiment" in desc.lower()

    def test_should_have_canonical_url(self, page):
        page.goto("/experiments/")
        canonical = page.locator('link[rel="canonical"]').get_attribute("href")
        assert "/experiments/" in canonical

    def test_should_have_experiments_breadcrumb(self, page):
        page.goto("/experiments/")
        data = _load_json_ld(page)
        bc = _get_schema(data, "BreadcrumbList")
        assert bc
        assert bc["itemListElement"][1]["item"]["name"] == "Experiments"

    def test_should_have_file_links(self, page):
        page.goto("/experiments/")
        file_links = page.locator('a[href$=".html"]')
        assert file_links.count() >= 1

    def test_directory_pages_list_their_files(self, page):
        page.goto("/experiments/biology/dna-sequencing/")
        file_links = page.locator(".mw-parser-output .gb-file-link")
        expect(file_links).not_to_have_count(0)
        expect(file_links.first).to_be_visible()

    def test_topic_page_groups_subtopic_files(self, page):
        page.goto("/experiments/python/")
        sections = page.locator(".mw-parser-output .gb-index-section")
        expect(sections).not_to_have_count(0)
        expect(sections.first).to_be_visible()



class TestExperimentsIntegration:
    def test_header_has_experiments_link(self, page):
        page.goto("/")
        expect(page.locator('#mw-panel a[href="/experiments/"]')).to_be_visible()

    def test_sitemap_contains_experiments(self, out_dir):
        text = (out_dir / "sitemap.xml").read_text()
        assert "/experiments/" in text

    def test_sitemap_has_experiment_file_entries(self, out_dir):
        text = (out_dir / "sitemap.xml").read_text()
        assert ".html" in text
        entries = re.findall(r"<loc>[^<]+</loc>", text)
        exp_entries = [e for e in entries if "/experiments/" in e]
        assert len(exp_entries) >= 1


class TestMermaidRendering:
    def test_mermaid_diagram_renders_as_svg(self, page):
        page.goto("/experiments/biology/dna-sequencing/readme.html")
        svg = page.locator(".gitbook-markdown-body svg[id^='mermaid']")
        expect(svg.first).to_be_visible(timeout=15000)


class TestNotebookCollapsible:
    URL = "/experiments/python/numba/np.mean/scratchbook.html"

    def test_code_cells_are_collapsed_by_default(self, page):
        page.goto(self.URL)
        blocks = page.locator(".gb-code-block")
        assert blocks.count() >= 1
        expect(blocks.first).not_to_have_attribute("open", "")

    def test_expand_label_visible_while_collapsed(self, page):
        page.goto(self.URL)
        first = page.locator(".gb-code-block").first
        expect(first.locator(".gb-code-expand")).to_be_visible()
        expect(first.locator(".gb-code-collapse")).to_be_hidden()

    def test_outputs_visible_while_collapsed(self, page):
        page.goto(self.URL)
        cell = page.locator("div.code_cell:has(.gb-code-block):has(.output_wrapper)").first
        expect(cell.locator(".output_wrapper").first).to_be_visible()

    def test_prompt_visible_while_collapsed(self, page):
        page.goto(self.URL)
        first = page.locator(".gb-code-block").first
        prompt = first.locator("xpath=preceding-sibling::div[contains(@class,'input_prompt')]")
        expect(prompt).to_be_visible()

    def test_clicking_summary_expands_and_collapses(self, page):
        page.goto(self.URL)
        first = page.locator(".gb-code-block").first
        summary = first.locator("summary")
        summary.click()
        expect(first).to_have_attribute("open", "")
        expect(first.locator(".gb-code-collapse")).to_be_visible()
        expect(first.locator(".gb-code-expand")).to_be_hidden()
        summary.click()
        expect(first).not_to_have_attribute("open", "")

    def test_code_is_syntax_highlighted(self, page):
        page.goto(self.URL)
        page.locator(".gb-code-block").first.locator("summary").click()
        code = page.locator(".gb-code-block pre code.language-python").first
        expect(code).to_be_visible()
        expect(code).to_contain_text("import numpy as np")
        page.locator(".gb-code-block pre code.language-python.hljs").first.wait_for(
            state="visible"
        )
        highlighted = page.locator(".gb-code-block code.hljs span.hljs-keyword")
        assert highlighted.count() >= 1
