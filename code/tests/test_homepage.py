import re

from playwright.sync_api import expect


def test_should_load_homepage_successfully(page):
    page.goto("/")
    expect(page).to_have_title(re.compile("Prakash"))


def test_should_display_author_logo(page):
    page.goto("/")
    logo = page.locator("#mw-head #p-logo a")
    expect(logo).to_be_visible()
    expect(logo).to_have_attribute("href", "/")
    expect(logo).to_contain_text("PS")


def test_should_display_site_description(page):
    page.goto("/")
    expect(page.get_by_text(re.compile("Software Engineer"))).to_be_visible()


def test_about_page_displays_full_name(page):
    page.goto("/about.html")
    expect(page.locator("h1")).to_contain_text("Prakash Sellathurai")


class TestRecentNotes:
    def test_homepage_sidebar_lists_essays(self, page):
        page.goto("/")
        essays = page.locator("#p-essays a.gb-tree-file")
        expect(essays.first).to_be_visible()

    def test_homepage_has_recent_notes_box(self, page):
        page.goto("/")
        box = page.locator(".mp-box", has_text="Recent notes")
        expect(box).to_be_visible()

    def test_recent_notes_box_lists_note_links(self, page):
        page.goto("/")
        box = page.locator(".mp-box", has_text="Recent notes")
        links = box.locator('a[href^="/notes/"]')
        expect(links.first).to_be_visible()
        expect(links.first).to_have_attribute("href", re.compile(r"/notes/.*\.html"))

    def test_recent_notes_box_has_all_notes_link(self, page):
        page.goto("/")
        box = page.locator(".mp-box", has_text="Recent notes")
        expect(box.locator('a[href="/notes/"]')).to_be_visible()
