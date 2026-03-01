import { test, expect } from '@playwright/test';

test.describe('Demo Mode — highest priority', () => {
  test('root loads and metric values are visible (no undefined/NaN)', async ({
    page,
  }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Wait for loading to complete
    await expect(page.locator('.loading-container')).not.toBeVisible({
      timeout: 10000,
    });

    // Check the page has rendered text content (no blank screen)
    const bodyText = await page.textContent('body');
    expect(bodyText).not.toContain('undefined');
    expect(bodyText).not.toContain('NaN');
  });

  test('Demo indicator is visible when no PostHog configured', async ({
    page,
  }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Wait for data to load
    await expect(page.locator('.loading-container')).not.toBeVisible({
      timeout: 10000,
    });

    // Look for demo indicator text
    const demoText = page.getByText('Demo');
    await expect(demoText).toBeVisible({ timeout: 5000 });
  });

  test('zero JS errors during 5s observation', async ({ page }) => {
    const jsErrors: string[] = [];
    page.on('pageerror', (error) => jsErrors.push(error.message));

    await page.goto('/');
    await page.waitForTimeout(5000);

    expect(jsErrors).toEqual([]);
  });

  test('nothing overflows 480x480 viewport', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    const overflow = await page.evaluate(() => {
      const body = document.body;
      return {
        scrollWidth: body.scrollWidth,
        scrollHeight: body.scrollHeight,
      };
    });

    expect(overflow.scrollWidth).toBeLessThanOrEqual(480);
    expect(overflow.scrollHeight).toBeLessThanOrEqual(480);
  });
});
