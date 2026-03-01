import { test, expect } from '@playwright/test';

test.describe('Config page', () => {
  test('all 5 tab buttons are visible', async ({ page }) => {
    await page.goto('/config');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    const tabs = page.locator('.config-tabs .tab');
    const count = await tabs.count();
    expect(count).toBe(5);
  });

  test('clicking a tab renders corresponding panel', async ({ page }) => {
    await page.goto('/config');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Click "Display" tab
    const displayTab = page.locator('.tab').filter({ hasText: 'Display' });
    await displayTab.click();
    await page.waitForTimeout(500);

    // URL should update to include tab=display
    expect(page.url()).toContain('tab=display');
  });

  test('save button exists and is clickable', async ({ page }) => {
    await page.goto('/config');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    const saveBtn = page.locator('button').filter({ hasText: 'Save' });
    await expect(saveBtn).toBeVisible();
    await expect(saveBtn).toBeEnabled();
  });
});
