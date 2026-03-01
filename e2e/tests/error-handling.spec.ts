import { test, expect } from '@playwright/test';

test.describe('Error handling', () => {
  test('/setup shows setup content', async ({ page }) => {
    await page.goto('/setup');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Setup page should render without crashing
    const bodyText = await page.textContent('body');
    expect(bodyText!.length).toBeGreaterThan(0);
  });

  test('/nonexistent redirects to /', async ({ page }) => {
    await page.goto('/nonexistent');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // React Router catch-all should redirect to /
    const url = new URL(page.url());
    expect(url.pathname).toBe('/');
  });
});
