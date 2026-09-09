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
        data = _load_json_ld(page)
        assert data

    def test_should_have_website_schema(self, page):
        page.goto("/")
        data = _load_json_ld(page)
        website = _get_schema(data, "WebSite")
        assert website
        assert website["name"]
        assert website["url"] == "https://prakashsellathurai.com/"
        assert website["potentialAction"]["@type"] == "SearchAction"
        assert "search_term_string" in website["potentialAction"]["query-input"]

    def test_should_have_person_schema(self, page):
        page.goto("/")
        data = _load_json_ld(page)
        person = _get_schema(data, "Person")
        assert person
        assert person["name"]
        assert "prakashsellathurai.com" in person["url"]
        assert person.get("image")
        assert person.get("email")

    def test_should_have_robots_txt(self, out_dir):
        text = (out_dir / "robots.txt").read_text()
        assert "User-agent:" in text
        assert "Sitemap:" in text

    def test_should_have_sitemap_xml(self, out_dir):
        text = (out_dir / "sitemap.xml").read_text()
        assert "<urlset" in text
        assert "<loc>" in text

    def test_sitemap_should_not_have_duplicate_urls(self, out_dir):
        locs = re.findall(r"<loc>([^<]+)</loc>", (out_dir / "sitemap.xml").read_text())
        assert len(locs) == len(set(locs)), f"duplicate URLs: {set(x for x in locs if locs.count(x) > 1)}"

    def test_should_have_rss_feed(self, out_dir):
        text = (out_dir / "feed.xml").read_text()
        assert "<rss" in text
        assert "<channel>" in text


class TestSitemapSEO:
    def test_sitemap_should_not_contain_raw_source_files(self, out_dir):
        """Sitemap should not contain .py, .c, .cpp, .txt URLs."""
        text = (out_dir / "sitemap.xml").read_text()
        locs = re.findall(r"<loc>([^<]+)</loc>", text)
        raw_exts = ('.py', '.c', '.cpp', '.txt')
        for loc in locs:
            for ext in raw_exts:
                assert not loc.endswith(ext), f"Sitemap contains raw source file: {loc}"

    def test_sitemap_should_not_contain_dryrun_urls(self, out_dir):
        """Sitemap should not contain dryrun URLs."""
        text = (out_dir / "sitemap.xml").read_text()
        assert "/dryrun/" not in text, "Sitemap contains dryrun URL"

    def test_sitemap_should_use_trailing_slash_for_leetcode(self, out_dir):
        """LeetCode solution URLs should use trailing slash, not index.html."""
        text = (out_dir / "sitemap.xml").read_text()
        locs = re.findall(r"<loc>([^<]+)</loc>", text)
        leetcode_locs = [loc for loc in locs if "/leetcode-solutions/" in loc]
        for loc in leetcode_locs:
            if loc != "https://prakashsellathurai.com/leetcode-solutions/":
                assert loc.endswith("/"), f"LeetCode URL should end with trailing slash: {loc}"
                assert not loc.endswith("/index.html"), f"LeetCode URL should not end with index.html: {loc}"

    def test_robots_txt_should_disallow_raw_source_files(self, out_dir):
        """robots.txt should disallow raw source file extensions."""
        text = (out_dir / "robots.txt").read_text()
        assert "Disallow: /*.py$" in text
        assert "Disallow: /*.c$" in text
        assert "Disallow: /*.cpp$" in text
        assert "Disallow: /*.txt$" in text


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

    def test_should_have_blog_posting_schema(self, page):
        page.goto("/essays/")
        first_essay = page.locator("article h2 a").first
        href = first_essay.get_attribute("href")
        page.goto(href)
        data = _load_json_ld(page)
        blog = _get_schema(data, "BlogPosting")
        assert blog
        assert blog["headline"]
        assert blog["datePublished"]
        assert blog["author"]["@type"] == "Person"
        assert blog["author"]["name"]
        assert "prakashsellathurai.com" in blog["url"]

    def test_should_have_essay_breadcrumbs(self, page):
        page.goto("/essays/")
        first_essay = page.locator("article h2 a").first
        href = first_essay.get_attribute("href")
        page.goto(href)
        data = _load_json_ld(page)
        breadcrumbs = _get_schema(data, "BreadcrumbList")
        assert breadcrumbs
        assert len(breadcrumbs["itemListElement"]) >= 3
        assert breadcrumbs["itemListElement"][0]["item"]["name"] == "Home"
        assert breadcrumbs["itemListElement"][1]["item"]["name"] == "Essays"


class TestAboutPageSEO:
    def test_should_have_about_page_schema(self, page):
        page.goto("/about.html")
        data = _load_json_ld(page)
        about = _get_schema(data, "ProfilePage")
        assert about
        assert "About" in about["name"]
        assert about["mainEntity"]["@type"] == "Person"
        assert "prakashsellathurai.com" in about["url"]

    def test_should_have_profile_rich_result(self, page):
        page.goto("/about.html")
        data = _load_json_ld(page)
        about = _get_schema(data, "ProfilePage")
        person = about["mainEntity"]
        assert person["name"] == "Prakash Sellathurai"
        assert person["description"]
        assert person["sameAs"]
        assert person["jobTitle"]
        assert person["image"]
        assert person["email"]
        assert person["knowsAbout"]

    def test_should_have_about_breadcrumbs(self, page):
        page.goto("/about.html")
        data = _load_json_ld(page)
        breadcrumbs = _get_schema(data, "BreadcrumbList")
        assert breadcrumbs
        assert len(breadcrumbs["itemListElement"]) == 2
        assert breadcrumbs["itemListElement"][1]["item"]["name"] == "About"


class TestProjectsPageSEO:
    def test_should_have_collection_page_schema(self, page):
        page.goto("/projects.html")
        data = _load_json_ld(page)
        collection = _get_schema(data, "CollectionPage")
        assert collection
        assert collection["mainEntity"]["@type"] == "ItemList"
        items = collection["mainEntity"]["itemListElement"]
        assert len(items) > 0
        first = items[0]
        assert first["@type"] == "ListItem"
        assert first["item"]["@type"] == "SoftwareApplication"
        assert first["item"]["name"]
        assert first["item"]["codeRepository"]
        assert first["item"]["applicationCategory"] == "DeveloperApplication"

    def test_should_have_projects_breadcrumbs(self, page):
        page.goto("/projects.html")
        data = _load_json_ld(page)
        breadcrumbs = _get_schema(data, "BreadcrumbList")
        assert breadcrumbs
        assert len(breadcrumbs["itemListElement"]) == 2
        assert breadcrumbs["itemListElement"][1]["item"]["name"] == "Projects"
