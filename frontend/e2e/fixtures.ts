import { test as base } from '@playwright/test';

// Define the type for our fixtures (we don't export specific values yet, just the auto-worker)
type PortfolioFixtures = {
  mockApi: void;
};

export const test = base.extend<PortfolioFixtures>({
  mockApi: [
    async ({ page }, use) => {
      // Catch-all mock for API v1
      await page.route('**/v1/**', async route => {
        const url = route.request().url();

        // 1. User Profile
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

        // 2. Background Image
        if (url.includes('/background/')) {
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              url: 'https://via.placeholder.com/1920x1080',
            }),
          });
        }

        // 3. Feature Flags (Enable ALL for max coverage by default)
        if (url.includes('/settings/')) {
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              contactForm: true,
              programming: true,
              gallery: true,
              lastimages: true,
              travelHighlights: true,
            }),
          });
        }

        // 5. Categories
        if (url.includes('/categories/')) {
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify([
              'Deep Sky',
              'Solar System',
              'Landscape',
              'Nature',
            ]),
          });
        }

        // 6. Default Image List (Empty by default, override in specific tests if needed)
        // Note: gallery.spec.ts needs complex logic, so we let it fall through or it overrides this.
        // But for "navigation" and "stability", empty is fine.
        // We'll return "continue" for image endpoints if not handled here to allow overrides?
        // No, Playwright routes are "first match wins" if defined later? Actually LATEST defined route handler executes FIRST.
        // So if we define this here, test-specific 'page.route' calls inside the test will take precedence.

        // 6. Default Image List (Empty by default, override in specific tests if needed)
        // Note: gallery.spec.ts needs complex logic, so we let it fall through or it overrides this.
        // But for "navigation" and "stability", empty is fine.
        // We'll return "continue" for image endpoints if not handled here to allow overrides?
        // No, Playwright routes are "first match wins" if defined later? Actually LATEST defined route handler executes FIRST.
        // So if we define this here, test-specific 'page.route' calls inside the test will take precedence.

        // Let's provide a safe default for images to avoid network errors
        if (url.includes('/image/')) {
          // If the test didn't override this path, return empty list to prevent 404s
          // But wait, allow the `continue()` call? No, we are mocking everything.
          // We will fulfill with empty list as a safe default.
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify([]),
          });
        }

        // Default: 200 OK empty list for anything else to prevent frontend crashing on uncaught fetch errors
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([]),
        });
      });

      await use();
    },
    { auto: true },
  ],
});

export { expect } from '@playwright/test';
