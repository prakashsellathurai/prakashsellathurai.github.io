import re

from playwright.sync_api import expect


class TestNotesSidebar:
    def test_notes_page_has_gitbook_style_search_box(self, page):
        page.goto("/notes/")
        search = page.locator('.gb-sidebar input[data-gb-search]')
        expect(search).to_be_visible()

    def test_notes_sidebar_is_grouped_tree(self, page):
        page.goto("/notes/")
        group = page.locator(".gb-sidebar details.gb-tree-dir")
        expect(group.first).to_be_visible()
        expect(page.locator(".gb-sidebar a.gb-tree-file")).to_have_count(3)

    def test_notes_detail_highlights_active_note(self, page):
        page.goto("/notes/agentic-systems.html")
        active = page.locator(".gb-sidebar a.gb-tree-file.active")
        expect(active).to_have_count(1)
        expect(active).to_have_text(re.compile("Agentic Systems", re.I))

    def test_search_filters_note_links(self, page):
        page.goto("/notes/")
        search = page.locator('.gb-sidebar input[data-gb-search]')
        search.fill("cpython")
        visible = page.locator(".gb-sidebar a.gb-tree-file:visible")
        expect(visible).to_have_count(1)
        expect(visible).to_have_text(re.compile("Cpython", re.I))


class TestExperimentsSidebar:
    def test_experiments_page_has_search_box(self, page):
        page.goto("/experiments/")
        search = page.locator('.gb-sidebar input[data-gb-search]')
        expect(search).to_be_visible()

    def test_search_filters_experiment_files(self, page):
        page.goto("/experiments/")
        search = page.locator('.gb-sidebar input[data-gb-search]')
        search.fill("epoll")
        visible = page.locator(".gb-sidebar a.gb-tree-file:visible")
        expect(visible).to_have_count(1)
        expect(visible).to_have_text(re.compile("epoll_server", re.I))
