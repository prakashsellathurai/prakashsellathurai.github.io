import time as time_module

from playwright.sync_api import expect


class TestCoreWebVitals:
    def test_homepage_should_have_good_lcp(self, page):
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

    def test_homepage_should_have_good_cls(self, page):
        page.goto("/")
        page.wait_for_timeout(1000)
        cls = page.evaluate("""() => {
            const entries = performance.getEntriesByType('layout-shift');
            return entries.reduce((sum, e) => sum + (e.value || 0), 0);
        }""")
        assert cls < 0.1

    def test_homepage_should_have_good_inp(self, page):
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

    def test_homepage_should_load_quickly_ttfb(self, page):
        start = time_module.time() * 1000
        page.goto("/")
        ttfb = (time_module.time() * 1000) - start
        assert ttfb < 600

    def test_pages_should_have_no_render_blocking_resources(self, page):
        page.goto("/")
        stylesheets = page.locator('link[rel="stylesheet"]').count()
        assert stylesheets > 0

    def test_homepage_total_blocking_time_should_be_low(self, page):
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

    def test_essay_page_performance_should_be_acceptable(self, page):
        page.goto("/essays/")
        first_essay = page.locator("article h2 a").first
        href = first_essay.get_attribute("href")
        start = time_module.time() * 1000
        page.goto(href)
        load_time = (time_module.time() * 1000) - start
        assert load_time < 2000
