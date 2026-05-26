import re

from playwright.sync_api import expect


class TestFootnotes:
    def test_sidenote_links_match_sidenote_ids(self, page):
        page.goto("/essays/bottom-up.html")
        refs = page.locator("a.sidenote-number")
        note_count = refs.count()
        assert note_count > 0
        for i in range(note_count):
            ref = refs.nth(i)
            href = ref.get_attribute("href")
            assert re.match(r"^#sn-\d+$", href)
            note_id = href[1:]
            sidenote = page.locator(f"span.sidenote#{note_id}")
            expect(sidenote).to_be_visible()
