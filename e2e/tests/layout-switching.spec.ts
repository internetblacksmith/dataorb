import { test, expect } from '@playwright/test';

test.describe('Layout switching via keyboard shortcuts', () => {
  test('Ctrl+Alt+2 navigates to /modern', async ({ page }) => {
    await page.goto('/classic');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    await page.keyboard.down('Control');
    await page.keyboard.down('Alt');
    await page.keyboard.press('2');
    await page.keyboard.up('Alt');
    await page.keyboard.up('Control');

    await page.waitForTimeout(1000);
    expect(page.url()).toContain('/modern');
  });

  test('Ctrl+Shift+C navigates to /config', async ({ page }) => {
    await page.goto('/classic');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    await page.keyboard.down('Control');
    await page.keyboard.down('Shift');
    await page.keyboard.press('KeyC');
    await page.keyboard.up('Shift');
    await page.keyboard.up('Control');

    await page.waitForTimeout(1000);
    expect(page.url()).toContain('/config');
  });
});
