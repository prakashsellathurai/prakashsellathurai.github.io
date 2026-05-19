import { test, expect } from '@playwright/test';

test.describe('Footnotes', () => {
  test('sidenote-number links to matching sidenote', async ({ page }) => {
    await page.goto('/essays/bottom-up.html');

    const refs = page.locator('a.sidenote-number');
    const noteCount = await refs.count();
    expect(noteCount).toBeGreaterThan(0);

    for (let i = 0; i < noteCount; i++) {
      const ref = refs.nth(i);
      const href = await ref.getAttribute('href');
      expect(href).toMatch(/^#sn-\d+$/);

      const id = href!.slice(1);
      const sidenote = page.locator(`span.sidenote#${id}`);
      await expect(sidenote).toBeVisible();
    }
  });
});
