import { test, expect } from './fixtures';

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should navigate to main sections via navbar', async ({ page }) => {
    const nav = page.locator('nav');

    // Navigate to About
    await nav
      .getByRole('link', { name: 'About', exact: true })
      .first()
      .click({ force: true });
    // The About link is a hash link, it shouldn't change URL except for the hash
    await expect(
      page.getByRole('heading', { name: 'Beyond the Atmosphere.' }).first()
    ).toBeVisible({ timeout: 15000 });

    // Navigate to Portfolio (Astrophotography)
    await nav
      .getByRole('link', { name: 'Astrophotography', exact: true })
      .first()
      .click();
    await page.waitForURL('**/astrophotography', { timeout: 10000 });
    await expect(page).toHaveURL(/\/astrophotography/);

    // Navigate Home
    await nav.getByRole('link', { name: 'Home', exact: true }).first().click();
    await page.waitForURL('**/', { timeout: 10000 });
    await expect(page).toHaveURL('http://localhost:3000/');
  });

  test('should highlight active link', async ({ page }) => {
    // Go to Astrophotography
    await page.goto('/astrophotography');

    // Check active state via aria-current (scope to nav to avoid logo)
    const link = page
      .locator('nav')
      .getByRole('link', { name: 'Astrophotography', exact: true })
      .first();
    await expect(link).toHaveAttribute('aria-current', 'page');
  });

  test('should toggle mobile menu', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    const menuTrigger = page.getByLabel('Open menu');
    await expect(menuTrigger).toBeVisible();
    await menuTrigger.click();

    const closeTrigger = page.getByLabel('Close menu');
    await expect(closeTrigger).toBeVisible();

    await closeTrigger.click();
    await expect(closeTrigger).not.toBeVisible();
  });
});
