import { test, expect } from '@playwright/test';

test.describe('Homepage', () => {
  test('should load homepage successfully', async ({ page }) => {
    await page.goto('/');
    
    await expect(page).toHaveTitle(/Prakash/);
  });

  test('should display author name', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.locator('.sidebar').getByText('Prakash')).toBeVisible();
  });

  test('should display site description', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.getByText(/Software Engineer/)).toBeVisible();
  });


  test('should display author name in about page', async ({ page }) => {
    await page.goto('/about.html');
    
    await expect(page.locator('h1')).toContainText('Prakash Sellathurai');
  });
});