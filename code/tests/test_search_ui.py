import re

from playwright.sync_api import expect


class TestSearchDropdown:
    def test_dropdown_shows_suggestions_while_typing(self, page):
        page.goto("/notes/")
        search = page.locator("#p-search input[data-gb-search]")
        search.fill("cpython")
        dropdown = page.locator("#p-search .sb-dropdown.open")
        expect(dropdown).to_be_visible()
        expect(dropdown.locator(".sb-item").first).to_be_visible()

    def test_suggestion_navigates_to_matching_page(self, page):
        page.goto("/notes/")
        page.locator("#p-search input[data-gb-search]").fill("cpython")
        page.locator(".sb-dropdown.open .sb-item").first.click()
        page.wait_for_load_state("load")
        expect(page).to_have_url(re.compile(r"/notes/", re.I))

    def test_dropdown_includes_google_fallback_row(self, page):
        page.goto("/notes/")
        page.locator("#p-search input[data-gb-search]").fill("cpython")
        row = page.locator(".sb-dropdown.open .sb-google")
        expect(row).to_be_visible()
        expect(row).to_contain_text("on prakashsellathurai.com")

    def test_google_row_link_targets_google_site_search(self, page):
        page.goto("/notes/")
        page.locator("#p-search input[data-gb-search]").fill("cpython")
        with page.expect_navigation(wait_until="domcontentloaded") as nav:
            page.locator(".sb-dropdown.open .sb-google").click()
        url = nav.value.url
        assert url.startswith("https://www.google.com/search?q=")
        assert "site%3Aprakashsellathurai.com" in url

    def test_escape_closes_dropdown(self, page):
        page.goto("/notes/")
        search = page.locator("#p-search input[data-gb-search]")
        search.fill("cpython")
        expect(page.locator(".sb-dropdown.open")).to_be_visible()
        page.keyboard.press("Escape")
        expect(page.locator(".sb-dropdown.open")).to_have_count(0)

    def test_no_match_closes_dropdown(self, page):
        page.goto("/notes/")
        page.locator("#p-search input[data-gb-search]").fill("zzzzznomatch")
        page.wait_for_timeout(400)
        expect(page.locator(".sb-dropdown.open")).to_have_count(0)