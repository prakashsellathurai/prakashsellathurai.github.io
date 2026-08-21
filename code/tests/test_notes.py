import re

from playwright.sync_api import expect


class TestNotesSidebar:
    def test_notes_page_has_wikipedia_style_search_box(self, page):
        page.goto("/notes/")
        search = page.locator("#site-search input[data-search]")
        expect(search).to_be_visible()

    def test_search_box_submits_to_google_with_site_operator(self, page):
        page.goto("/notes/")
        form = page.locator("#site-search form[data-site-domain]")
        expect(form).to_have_attribute("action", "https://www.google.com/search")
        expect(form).to_have_attribute("data-site-domain", "prakashsellathurai.com")
        expect(form.locator('input[name="q"]')).to_be_visible()

    def test_notes_sidebar_is_grouped_tree(self, page):
        page.goto("/notes/")
        group = page.locator("#site-sidebar details.nav-tree-dir")
        expect(group.first).to_be_visible()
        expect(page.locator("#site-notes a.nav-tree-file")).not_to_have_count(0)

    def test_essays_not_in_sidebar(self, page):
        page.goto("/notes/")
        expect(page.locator("#site-essays")).to_have_count(0)

    def test_notes_detail_highlights_active_note(self, page):
        page.goto("/notes/agentic-systems/notes.html")
        active = page.locator("#site-sidebar a.nav-tree-file.active")
        expect(active).to_have_count(1)
        expect(active).to_have_text(re.compile("Notes", re.I))

    def test_notes_files_are_separate_pages(self, page):
        page.goto("/notes/")
        notes_list = page.locator("#site-sidebar a.nav-tree-file")
        expect(notes_list).not_to_have_count(0)
        expect(page.locator('/notes/cpython/development.html'))
        expect(page.locator('/notes/unix-commands/tail.html'))

    def test_notes_index_has_topic_cards(self, page):
        page.goto("/notes/")
        cards = page.locator(".article-content .content-index-section")
        expect(cards).not_to_have_count(0)
        expect(cards.first).to_be_visible()

    def test_note_topic_page_lists_files(self, page):
        page.goto("/notes/cpython/")
        file_links = page.locator(".article-content .content-file-link")
        expect(file_links).not_to_have_count(0)
        expect(file_links.first).to_be_visible()

    def test_file_links_are_in_a_simple_list(self, page):
        page.goto("/notes/")
        list_items = page.locator(".article-content .content-file-list li")
        expect(list_items.first).to_be_visible()
        expect(list_items.first.locator("a.content-file-link")).to_be_visible()



class TestExperimentsSidebar:
    def test_experiments_page_has_search_box(self, page):
        page.goto("/experiments/")
        search = page.locator("#site-search input[data-search]")
        expect(search).to_be_visible()