import { test, expect } from '@playwright/test';

test.describe('Stability Check', () => {
  test('should load the main page and NOT reload (checking for infinite loop)', async ({
    page,
  }) => {
    // Catch-all mock for API v1
    await page.route('**/v1/**', async route => {
      const url = route.request().url();

      if (url.includes('/profile/')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            first_name: 'Test',
            last_name: 'User',
            short_description: 'Sky Hunter',
          }),
        });
      }

      if (url.includes('/background/')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            url: 'https://via.placeholder.com/1920x1080',
          }),
        });
      }

      if (url.includes('/settings/')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            travelHighlights: true,
            gallery: true,
            contactForm: true,
            lastimages: true,
          }),
        });
      }

      if (url.includes('/image/')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([]),
        });
      }

      // Default fallback
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    // 1. Navigate to the home page
    await page.goto('/');

    // 2. Wait for the Hero title to ensure initial load is complete
    const heroTitle = page.locator('h1').first();
    await expect(heroTitle).toBeVisible();

    // 3. Set a marker in the window object.
    // If the page reloads, this property will be lost (undefined).
    const markerValue = Date.now();
    await page.evaluate(val => {
      (window as any).__stability_marker = val;
    }, markerValue);

    // 4. Wait for 5 seconds.
    // This is long enough for most refresh loops (which usually trigger immediately or within 1-2s) to happen.
    // eslint-disable-next-line
    await page.waitForTimeout(5000);

    // 5. Check if the marker still exists and has the same value
    const retrievedValue = await page.evaluate(() => {
      return (window as any).__stability_marker;
    });

    // If retrievedValue is undefined or different, the page reloaded!
    expect(
      retrievedValue,
      'Page reloaded unexpectedly! The window variable was lost.'
    ).toBe(markerValue);

    // 6. Final assertion: Helper elements should still be visible
    await expect(heroTitle).toBeVisible();
  });
});
