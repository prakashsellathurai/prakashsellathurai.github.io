import re

from playwright.sync_api import expect


class TestNotesSidebar:
    def test_notes_page_has_wikipedia_style_search_box(self, page):
        page.goto("/notes/")
        search = page.locator("#p-search input[data-gb-search]")
        expect(search).to_be_visible()

    def test_search_box_submits_to_google_with_site_operator(self, page):
        page.goto("/notes/")
        form = page.locator("#p-search form[data-site-domain]")
        expect(form).to_have_attribute("action", "https://www.google.com/search")
        expect(form).to_have_attribute("data-site-domain", "prakashsellathurai.com")
        expect(form.locator('input[name="q"]')).to_be_visible()

    def test_notes_sidebar_is_grouped_tree(self, page):
        page.goto("/notes/")
        group = page.locator("#mw-panel details.gb-tree-dir")
        expect(group.first).to_be_visible()
        expect(page.locator("#p-notes a.gb-tree-file")).to_have_count(5)

    def test_essays_are_in_sidebar_and_searchable(self, page):
        page.goto("/notes/")
        essays = page.locator("#p-essays a.gb-tree-file")
        expect(essays.first).to_be_visible()
        search = page.locator("#p-search input[data-gb-search]")
        search.fill("bottom")
        visible = page.locator("#p-essays a.gb-tree-file:visible")
        expect(visible).to_have_count(1)
        expect(visible).to_have_text(re.compile("bottom", re.I))

    def test_notes_detail_highlights_active_note(self, page):
        page.goto("/notes/agentic-systems/notes.html")
        active = page.locator("#mw-panel a.gb-tree-file.active")
        expect(active).to_have_count(1)
        expect(active).to_have_text(re.compile("Notes", re.I))

    def test_notes_files_are_separate_pages(self, page):
        page.goto("/notes/")
        notes_list = page.locator("#mw-panel a.gb-tree-file")
        expect(notes_list).not_to_have_count(0)
        expect(page.locator('/notes/cpython/development.html'))
        expect(page.locator('/notes/unix-commands/tail.html'))

    def test_notes_index_has_topic_cards(self, page):
        page.goto("/notes/")
        cards = page.locator(".mw-parser-output .gb-index-section")
        expect(cards).not_to_have_count(0)
        expect(cards.first).to_be_visible()

    def test_note_topic_page_lists_files(self, page):
        page.goto("/notes/cpython/")
        file_links = page.locator(".mw-parser-output .gb-file-link")
        expect(file_links).not_to_have_count(0)
        expect(file_links.first).to_be_visible()

    def test_file_links_are_in_a_simple_list(self, page):
        page.goto("/notes/")
        list_items = page.locator(".mw-parser-output .gb-file-list li")
        expect(list_items.first).to_be_visible()
        expect(list_items.first.locator("a.gb-file-link")).to_be_visible()



class TestExperimentsSidebar:
    def test_experiments_page_has_search_box(self, page):
        page.goto("/experiments/")
        search = page.locator("#p-search input[data-gb-search]")
        expect(search).to_be_visible()

    def test_search_filters_experiment_files(self, page):
        page.goto("/experiments/")
        search = page.locator("#p-search input[data-gb-search]")
        search.fill("epoll")
        visible = page.locator("#mw-panel a.gb-tree-file:visible")
        expect(visible).to_have_count(1)
        expect(visible).to_have_text(re.compile("epoll_server", re.I))