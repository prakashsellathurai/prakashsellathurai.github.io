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

    def test_should_have_some_topic_links(self, page):
        page.goto("/experiments/")
        hrefs = page.locator('a[href^="/experiments/"]').all()
        topic_hrefs = [
            h.get_attribute("href")
            for h in hrefs
            if h.get_attribute("href").count("/") == 2
        ]
        assert len(topic_hrefs) >= 1

    def test_should_have_file_links(self, page):
        page.goto("/experiments/")
        file_links = page.locator('a[href$=".html"]')
        assert file_links.count() >= 1


class TestExperimentsTopicPage:
    def test_should_load_and_list_content(self, page):
        page.goto("/experiments/")
        topic_links = page.locator('section a[href^="/experiments/"][href*="/"][href$="/"]')
        topic_count = topic_links.count()
        assert topic_count >= 1
        href = topic_links.first.get_attribute("href")
        page.goto(href)
        expect(page).to_have_title(re.compile("Experiments"))
        assert page.locator("section a").count() >= 1


class TestExperimentsIntegration:
    def test_header_has_experiments_link(self, page):
        page.goto("/")
        expect(page.locator('header a[href="/experiments/"]')).to_be_visible()

    def test_sitemap_contains_experiments(self, page):
        response = page.request.get("/sitemap.xml")
        assert response.ok
        text = response.text()
        assert "/experiments/" in text

    def test_sitemap_has_experiment_file_entries(self, page):
        response = page.request.get("/sitemap.xml")
        text = response.text()
        assert ".html" in text
        entries = re.findall(r"<loc>[^<]+</loc>", text)
        exp_entries = [e for e in entries if "/experiments/" in e]
        assert len(exp_entries) >= 1
