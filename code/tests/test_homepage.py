from __future__ import annotations

import re

from playwright.sync_api import expect


def test_homepage_loads_with_author_name_in_title(page):
    page.goto("/")
    expect(page).to_have_title(re.compile("Prakash"))


def test_homepage_displays_site_logo_and_branding(page):
    page.goto("/")
    logo = page.locator("#site-header #site-logo a")
    expect(logo).to_be_visible()
    expect(logo).to_have_attribute("href", "/")
    expect(logo).to_contain_text("PS")


def test_homepage_displays_professional_description(page):
    page.goto("/")
    expect(page.get_by_text(re.compile("Software Engineer"))).to_be_visible()


def test_about_page_displays_full_name(page):
    page.goto("/about.html")
    expect(page.locator("h1")).to_contain_text("Prakash Sellathurai")


class TestRecentNotes:
    def test_sidebar_lists_essays(self, page):
        page.goto("/")
        essays = page.locator("#site-essays a.nav-tree-file")
        expect(essays.first).to_be_visible()

    def test_recent_notes_box_is_visible(self, page):
        page.goto("/")
        box = page.locator(".home-box", has_text="Recent notes")
        expect(box).to_be_visible()

    def test_recent_notes_box_lists_links_to_note_pages(self, page):
        page.goto("/")
        box = page.locator(".home-box", has_text="Recent notes")
        links = box.locator('a[href^="/notes/"]')
        expect(links.first).to_be_visible()
        expect(links.first).to_have_attribute("href", re.compile(r"/notes/.*\.html"))

    def test_recent_notes_box_has_view_all_link(self, page):
        page.goto("/")
        box = page.locator(".home-box", has_text="Recent notes")
        expect(box.locator('a[href="/notes/"]')).to_be_visible()
