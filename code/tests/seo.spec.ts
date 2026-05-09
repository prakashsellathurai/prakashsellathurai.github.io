import { test, expect } from '@playwright/test';

test.describe('SEO Tests', () => {
  test.describe('Homepage SEO', () => {
    test('should have title tag', async ({ page }) => {
      await page.goto('/');
      const title = await page.title();
      expect(title).toBeTruthy();
    });

    test('should have meta description', async ({ page }) => {
      await page.goto('/');
      const desc = await page.locator('meta[name="description"]').getAttribute('content');
      expect(desc).toBeTruthy();
      expect(desc.length).toBeGreaterThan(50);
    });

    test('should have keywords meta', async ({ page }) => {
      await page.goto('/');
      const keywords = await page.locator('meta[name="keywords"]').getAttribute('content');
      expect(keywords).toBeTruthy();
    });

    test('should have canonical URL', async ({ page }) => {
      await page.goto('/');
      const canonical = await page.locator('link[rel="canonical"]').getAttribute('href');
      expect(canonical).toContain('prakashsellathurai.com');
    });

    test('should have Open Graph tags', async ({ page }) => {
      await page.goto('/');
      await expect(page.locator('meta[property="og:title"]')).toHaveAttribute('content', /.+/);
      await expect(page.locator('meta[property="og:description"]')).toHaveAttribute('content', /.+/);
      await expect(page.locator('meta[property="og:url"]')).toHaveAttribute('content', /.+/);
      await expect(page.locator('meta[property="og:image"]')).toHaveAttribute('content', /.+/);
    });

    test('should have Twitter Card meta', async ({ page }) => {
      await page.goto('/');
      await expect(page.locator('meta[name="twitter:card"]')).toHaveAttribute('content', 'summary_large_image');
      await expect(page.locator('meta[name="twitter:title"]')).toHaveAttribute('content', /.+/);
      await expect(page.locator('meta[name="twitter:image"]')).toHaveAttribute('content', /.+/);
    });

    test('should have JSON-LD structured data', async ({ page }) => {
      await page.goto('/');
      const jsonLd = await page.locator('script[type="application/ld+json"]').textContent();
      expect(jsonLd).toBeTruthy();
      const data = JSON.parse(jsonLd!);
      expect(data['@type']).toBe('Person');
      expect(data.name).toBeTruthy();
      expect(data.url).toContain('prakashsellathurai.com');
    });

    test('should have robots.txt', async ({ request }) => {
      const response = await request.get('/robots.txt');
      expect(response.ok()).toBeTruthy();
      const text = await response.text();
      expect(text).toContain('User-agent:');
      expect(text).toContain('Sitemap:');
    });

    test('should have sitemap.xml', async ({ request }) => {
      const response = await request.get('/sitemap.xml');
      expect(response.ok()).toBeTruthy();
      const text = await response.text();
      expect(text).toContain('<urlset');
      expect(text).toContain('<loc>');
    });

    test('should have RSS feed', async ({ request }) => {
      const response = await request.get('/feed.xml');
      expect(response.ok()).toBeTruthy();
      const text = await response.text();
      expect(text).toContain('<rss');
      expect(text).toContain('<channel>');
    });
  });

  test.describe('Essay Page SEO', () => {
    test('should have unique title per essay', async ({ page }) => {
      await page.goto('/essays/');
      const firstEssay = page.locator('article h2 a').first();
      const href = await firstEssay.getAttribute('href');
      await page.goto(href!);
      const title = await page.title();
      expect(title).toContain('- Prakash');
    });

    test('should have essay-specific meta description', async ({ page }) => {
      await page.goto('/essays/');
      const firstEssay = page.locator('article h2 a').first();
      const href = await firstEssay.getAttribute('href');
      await page.goto(href!);
      const desc = await page.locator('meta[name="description"]').getAttribute('content');
      expect(desc).toBeTruthy();
    });

    test('should have essay-specific canonical URL', async ({ page }) => {
      await page.goto('/essays/');
      const firstEssay = page.locator('article h2 a').first();
      const href = await firstEssay.getAttribute('href');
      await page.goto(href!);
      const canonical = await page.locator('link[rel="canonical"]').getAttribute('href');
      expect(canonical).toContain('/essays/');
    });
  });
});