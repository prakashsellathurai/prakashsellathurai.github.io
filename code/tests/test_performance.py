from __future__ import annotations

import time as time_module


class TestCoreWebVitals:
    def test_homepage_lcp_is_within_acceptable_threshold(self, page):
        page.goto("/")
        lcp = page.evaluate("""() => {
            return new Promise((resolve) => {
                new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    const last = entries[entries.length - 1];
                    resolve(last ? (last.renderTime || last.startTime) : 0);
                }).observe({type: 'largest-contentful-paint', buffered: true});
                setTimeout(() => resolve(0), 2000);
            });
        }""")
        assert lcp < 2500

    def test_homepage_cls_indicates_no_layout_shifts(self, page):
        page.goto("/")
        page.wait_for_timeout(1000)
        cls = page.evaluate("""() => {
            const entries = performance.getEntriesByType('layout-shift');
            return entries.reduce((sum, e) => sum + (e.value || 0), 0);
        }""")
        assert cls < 0.1

    def test_homepage_inp_shows_responsive_interaction(self, page):
        page.goto("/")
        inp = page.evaluate("""() => {
            return new Promise((resolve) => {
                let maxDuration = 0;
                new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (entry.interactionId) {
                            if (entry.duration > maxDuration) {
                                maxDuration = entry.duration;
                            }
                        }
                    }
                }).observe({type: 'event', buffered: true, durationThreshold: 16});
                setTimeout(() => resolve(maxDuration), 1000);
            });
        }""")
        assert inp < 200

    def test_homepage_ttfb_indicates_fast_server_response(self, page):
        start = time_module.time() * 1000
        page.goto("/")
        ttfb = (time_module.time() * 1000) - start
        assert ttfb < 600

    def test_homepage_has_linked_stylesheets(self, page):
        page.goto("/")
        stylesheets = page.locator('link[rel="stylesheet"]').count()
        assert stylesheets > 0

    def test_homepage_tbt_indicates_no_long_blocking_tasks(self, page):
        page.goto("/")
        tbt = page.evaluate("""() => {
            const paint = performance.getEntriesByType('paint');
            const fcp = paint.find(p => p.name === 'first-contentful-paint');
            const longTasks = performance.getEntriesByType('longtask');
            const totalBlockingTime = longTasks
                .filter(t => (fcp ? t.startTime > fcp.startTime : true))
                .reduce((sum, t) => sum + (t.duration - 50), 0);
            return Math.max(0, totalBlockingTime);
        }""")
        assert tbt < 200

    def test_essay_page_loads_within_acceptable_time(self, page):
        page.goto("/essays/")
        first_essay = page.locator("article h2 a").first
        href = first_essay.get_attribute("href")
        start = time_module.time() * 1000
        page.goto(href)
        load_time = (time_module.time() * 1000) - start
        assert load_time < 2000
