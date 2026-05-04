import { test, expect } from '@playwright/test';

test.describe('Homepage', () => {
  test('should load homepage successfully', async ({ page }) => {
    await page.goto('/');
    
    await expect(page).toHaveTitle(/Prakash/);
  });

  test('should display author name', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.locator('.sidebar').getByText('Prakash Sellathurai')).toBeVisible();
  });

  test('should display site description', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.getByText(/Software Engineer/)).toBeVisible();
  });

  test('should display author name in quick about section', async ({ page }) => {
    await page.goto('/');
    
    const sidebar = page.locator('.sidebar').first();
    await expect(sidebar.locator('h3', { hasText: /^About/ })).toBeVisible();
    await expect(sidebar.locator('h3', { hasText: /^About/ })).toContainText('Prakash Sellathurai');
  });

  test('should display author name in about page', async ({ page }) => {
    await page.goto('/about.html');
    
    await expect(page.locator('h1')).toContainText('Prakash Sellathurai');
  });
});