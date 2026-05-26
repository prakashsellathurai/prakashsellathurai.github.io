import json
import re

from playwright.sync_api import expect


class TestHomepageSEO:
    def test_should_have_title_tag(self, page):
        page.goto("/")
        title = page.title()
        assert title

    def test_should_have_meta_description(self, page):
        page.goto("/")
        desc = page.locator('meta[name="description"]').get_attribute("content")
        assert desc
        assert len(desc) > 50

    def test_should_have_keywords_meta(self, page):
        page.goto("/")
        keywords = page.locator('meta[name="keywords"]').get_attribute("content")
        assert keywords

    def test_should_have_canonical_url(self, page):
        page.goto("/")
        canonical = page.locator('link[rel="canonical"]').get_attribute("href")
        assert "prakashsellathurai.com" in canonical

    def test_should_have_open_graph_tags(self, page):
        page.goto("/")
        expect(page.locator('meta[property="og:title"]')).to_have_attribute("content", re.compile(".+"))
        expect(page.locator('meta[property="og:description"]')).to_have_attribute("content", re.compile(".+"))
        expect(page.locator('meta[property="og:url"]')).to_have_attribute("content", re.compile(".+"))
        expect(page.locator('meta[property="og:image"]')).to_have_attribute("content", re.compile(".+"))

    def test_should_have_twitter_card_meta(self, page):
        page.goto("/")
        expect(page.locator('meta[name="twitter:card"]')).to_have_attribute("content", "summary_large_image")
        expect(page.locator('meta[name="twitter:title"]')).to_have_attribute("content", re.compile(".+"))
        expect(page.locator('meta[name="twitter:image"]')).to_have_attribute("content", re.compile(".+"))

    def test_should_have_json_ld_structured_data(self, page):
        page.goto("/")
        json_ld = page.locator('script[type="application/ld+json"]').text_content()
        assert json_ld
        data = json.loads(json_ld)
        assert data["@type"] == "Person"
        assert data["name"]
        assert "prakashsellathurai.com" in data["url"]

    def test_should_have_robots_txt(self, page):
        response = page.request.get("/robots.txt")
        assert response.ok
        text = response.text()
        assert "User-agent:" in text
        assert "Sitemap:" in text

    def test_should_have_sitemap_xml(self, page):
        response = page.request.get("/sitemap.xml")
        assert response.ok
        text = response.text()
        assert "<urlset" in text
        assert "<loc>" in text

    def test_should_have_rss_feed(self, page):
        response = page.request.get("/feed.xml")
        assert response.ok
        text = response.text()
        assert "<rss" in text
        assert "<channel>" in text


class TestEssaySEO:
    def test_should_have_unique_title_per_essay(self, page):
        page.goto("/essays/")
        first_essay = page.locator("article h2 a").first
        href = first_essay.get_attribute("href")
        page.goto(href)
        title = page.title()
        assert "- Prakash" in title

    def test_should_have_essay_specific_meta_description(self, page):
        page.goto("/essays/")
        first_essay = page.locator("article h2 a").first
        href = first_essay.get_attribute("href")
        page.goto(href)
        desc = page.locator('meta[name="description"]').get_attribute("content")
        assert desc

    def test_should_have_essay_specific_canonical_url(self, page):
        page.goto("/essays/")
        first_essay = page.locator("article h2 a").first
        href = first_essay.get_attribute("href")
        page.goto(href)
        canonical = page.locator('link[rel="canonical"]').get_attribute("href")
        assert "/essays/" in canonical
