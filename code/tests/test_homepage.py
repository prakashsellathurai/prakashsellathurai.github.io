import re

from playwright.sync_api import expect


def test_should_load_homepage_successfully(page):
    page.goto("/")
    expect(page).to_have_title(re.compile("Prakash"))


def test_should_display_author_name(page):
    page.goto("/")
    expect(page.locator(".sidebar")).to_contain_text("Prakash")


def test_should_display_site_description(page):
    page.goto("/")
    expect(page.get_by_text(re.compile("Software Engineer"))).to_be_visible()


def test_about_page_displays_full_name(page):
    page.goto("/about.html")
    expect(page.locator("h1")).to_contain_text("Prakash Sellathurai")
