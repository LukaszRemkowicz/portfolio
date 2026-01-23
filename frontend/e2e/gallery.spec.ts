import { test, expect } from '@playwright/test';

test.describe('Gallery Page', () => {
  test.beforeEach(async ({ page }) => {
    // Catch-all mock for API v1
    await page.route('**/api/v1/**', async route => {
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

      if (url.includes('/whats-enabled/')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            travelHighlights: true,
            gallery: true,
            contactForm: true,
          }),
        });
      }

      if (url.includes('/image/')) {
        const images = [
          {
            pk: 1,
            name: 'Milky Way Arch',
            url: 'https://via.placeholder.com/800x600',
            thumbnail_url: 'https://via.placeholder.com/200x150',
            description: 'Milky Way over mountains',
            tags: ['Milky Way', 'mountains'],
            celestial_object: 'Milky Way',
            created_at: '2023-01-01',
          },
          {
            pk: 2,
            name: 'Orion Nebula',
            url: 'https://via.placeholder.com/800x600',
            thumbnail_url: 'https://via.placeholder.com/200x150',
            description: 'M42 Orion Nebula',
            tags: ['Deep Sky', 'nebula'],
            celestial_object: 'Deep Sky',
            created_at: '2023-01-02',
          },
        ];

        // Check for detail view (e.g., /api/v1/image/1/)
        const match = url.match(/\/image\/(\d+)\//);
        if (match) {
          const id = parseInt(match[1]);
          const img = images.find(i => i.pk === id);
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(img || {}),
          });
        }

        // Image list view with simple mock filtering
        let filteredImages = [...images];
        const searchParams = new URL(url).searchParams;
        const tagFilter = searchParams.get('tag');
        const catFilter = searchParams.get('filter');

        if (tagFilter) {
          filteredImages = filteredImages.filter(img =>
            img.tags.some(t => t.toLowerCase() === tagFilter.toLowerCase())
          );
        }
        if (catFilter) {
          filteredImages = filteredImages.filter(
            img =>
              img.celestial_object?.toLowerCase() === catFilter.toLowerCase() ||
              img.tags.some(t => t.toLowerCase() === catFilter.toLowerCase())
          );
        }

        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(filteredImages),
        });
      }

      // Default fallback for other API calls
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.goto('/astrophotography');
  });

  test('should display all images by default', async ({ page }) => {
    await expect(
      page
        .getByRole('button', { name: /View details for Milky Way Arch/ })
        .first()
    ).toBeVisible();
    await expect(
      page
        .getByRole('button', { name: /View details for Orion Nebula/ })
        .first()
    ).toBeVisible();
  });

  test('should filter images by selecting a category', async ({ page }) => {
    // Direct navigation to filter state
    await page.goto('/astrophotography?filter=Deep+Sky');

    const filterBtn = page
      .getByRole('button', { name: 'Deep Sky', exact: true })
      .first();

    // Verify filter is active - check the button has the aria-pressed attribute
    await expect(filterBtn).toHaveAttribute('aria-pressed', 'true', {
      timeout: 10000,
    });
  });

  test('should open modal and display tags', async ({ page }) => {
    const card = page
      .getByRole('button', { name: /View details for Milky Way Arch/ })
      .first();
    await card.click({ force: true });

    await page.waitForURL(/\?img=/, { timeout: 10000 });

    const modal = page.getByTestId('image-modal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Check tags exist - they have # prefix in the UI
    const tag = modal.getByRole('button', { name: '#Milky Way' }).first();
    await expect(tag).toBeVisible({ timeout: 10000 });
  });

  test('should navigate to tag view when clicking a tag in modal', async ({
    page,
  }) => {
    // Direct navigation to image state
    await page.goto('/astrophotography?img=2');

    const modal = page.getByTestId('image-modal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    const tag = modal.getByRole('button', { name: '#Deep Sky' }).first();
    await tag.click({ force: true });

    await page.waitForURL(/\?tag=deep-sky/, { timeout: 10000 });

    // Should close modal and filter gallery
    await expect(modal).not.toBeVisible({ timeout: 10000 });

    // Check URL
    await expect(page).toHaveURL(/tag=deep-sky/);
  });
});
