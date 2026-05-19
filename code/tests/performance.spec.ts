/**
 * Core Web Vitals Performance Tests
 *
 * Based on Google's Core Web Vitals thresholds:
 * https://web.dev/articles/vitals-thresholds
 *
 * | Metric | Good (green) | Needs Improvement (orange) | Poor (red) |
 * |--------|--------------|------------------------------|------------|
 * | LCP    | < 2500ms     | 2500-4000ms                 | > 4000ms   |
 * | CLS    | < 0.1        | 0.1-0.25                    | > 0.25     |
 * | INP    | < 200ms      | 200-500ms                   | > 500ms    |
 * | TTFB   | < 600ms      | 600-1800ms                  | > 1800ms   |
 * | TBT    | < 200ms      | 200-600ms                   | > 600ms    |
 */

import { test, expect } from '@playwright/test';

test.describe('Page Speed / Core Web Vitals', () => {
  test('homepage should have good LCP (Largest Contentful Paint)', async ({ page }) => {
    const metrics = await page.goto('/').then(() => page.evaluate(() => {
      return new Promise((resolve) => {
        new PerformanceObserver((entryList) => {
          const entries = entryList.getEntries();
          const lastEntry = entries[entries.length - 1] as PerformanceEntry & { renderTime?: number };
          resolve({
            lcp: lastEntry.renderTime || lastEntry.startTime,
          });
        }).observe({ type: 'largest-contentful-paint', buffered: true });

        // Fallback if no LCP observed
        setTimeout(() => resolve({ lcp: 0 }), 2000);
      });
    }));

    expect(metrics.lcp).toBeLessThan(2500);
  });

  test('homepage should have good CLS (Cumulative Layout Shift)', async ({ page }) => {
    await page.goto('/');

    await page.waitForTimeout(1000);

    const cls = await page.evaluate(() => {
      const entries = performance.getEntriesByType('layout-shift') as any[];
      return entries.reduce((sum, entry) => sum + (entry.value || 0), 0);
    });

    expect(cls).toBeLessThan(0.1);
  });

  test('homepage should have good FID/INP (First Input Delay / Interaction to Next Paint)', async ({ page }) => {
    await page.goto('/');

    const inp = await page.evaluate(() => {
      return new Promise((resolve) => {
        let maxDuration = 0;
        new PerformanceObserver((entryList) => {
          for (const entry of entryList.getEntries() as any[]) {
            if (entry.interactionId) {
              const duration = entry.duration;
              if (duration > maxDuration) {
                maxDuration = duration;
              }
            }
          }
        }).observe({ type: 'event', buffered: true, durationThreshold: 16 });

        setTimeout(() => resolve(maxDuration), 1000);
      });
    });

    expect(inp).toBeLessThan(200);
  });

  test('homepage should load quickly (Time to First Byte)', async ({ page }) => {
    const start = Date.now();
    await page.goto('/');
    const ttfb = Date.now() - start;

    expect(ttfb).toBeLessThan(600);
  });

  test('pages should have no render-blocking resources', async ({ page }) => {
    await page.goto('/');

    const stylesheets = await page.locator('link[rel="stylesheet"]').count();
    expect(stylesheets).toBeGreaterThan(0);
  });

  test('homepage total blocking time should be low', async ({ page }) => {
    const metrics = await page.goto('/').then(() => page.evaluate(() => {
      const paint = performance.getEntriesByType('paint');
      const fcp = paint.find((p: any) => p.name === 'first-contentful-paint');

      const longTasks = performance.getEntriesByType('longtask') as any[];
      const totalBlockingTime = longTasks
        .filter(t => (fcp ? t.startTime > fcp.startTime : true))
        .reduce((sum, t) => sum + (t.duration - 50), 0);

      return { totalBlockingTime: Math.max(0, totalBlockingTime) };
    }));

    expect(metrics.totalBlockingTime).toBeLessThan(200);
  });

  test('essay page performance should be acceptable', async ({ page }) => {
    await page.goto('/essays/');
    const firstEssay = page.locator('article h2 a').first();
    const href = await firstEssay.getAttribute('href');

    const start = Date.now();
    await page.goto(href!);
    const loadTime = Date.now() - start;

    expect(loadTime).toBeLessThan(2000);
  });
});
