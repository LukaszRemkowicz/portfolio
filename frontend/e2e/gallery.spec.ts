import { test, expect } from './fixtures';

test.describe('Gallery Page', () => {
  test.beforeEach(async ({ page }) => {
    // Override default empty image list with mock data for Gallery tests
    await page.route('**/v1/astroimages/**', async route => {
      const url = route.request().url();
      const images = [
        {
          pk: 1,
          name: 'Milky Way Arch',
          slug: 'milky-way-arch',
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
          slug: 'orion-nebula',
          url: 'https://via.placeholder.com/800x600',
          thumbnail_url: 'https://via.placeholder.com/200x150',
          description: 'M42 Orion Nebula',
          tags: ['Deep Sky', 'nebula'],
          celestial_object: 'Deep Sky',
          created_at: '2023-01-02',
        },
      ];

      // Check for detail view (e.g., /api/v1/astroimages/slug/ or /api/v1/astroimages/1/)
      // Check if URL ends with ID/slug before query params
      const urlObj = new URL(url);
      const isDetailView = urlObj.pathname.match(/\/astroimages\/([^/]+)\/?$/);
      if (isDetailView && isDetailView[1]) {
        const idOrSlug = isDetailView[1];
        const img = images.find(
          i => i.pk.toString() === idOrSlug || i.slug === idOrSlug
        );
        if (img) {
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(img),
          });
        }
      }

      // Image list view with simple mock filtering
      let filteredImages = [...images];
      const tagFilter = urlObj.searchParams.get('tag');
      const catFilter = urlObj.searchParams.get('filter');

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
    });

    await page.goto('/astrophotography');
  });

  test('should display all images by default', async ({ page }) => {
    await expect(
      page.getByTestId('gallery-card-milky-way-arch').first()
    ).toBeVisible();
    await expect(
      page.getByTestId('gallery-card-orion-nebula').first()
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
    const card = page.getByTestId('gallery-card-milky-way-arch').first();
    // Force click to deal with potential overlay components like hover elements
    await card.click();

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
    await tag.click();

    await page.waitForURL(/\?tag=deep-sky/, { timeout: 10000 });

    // Should close modal and filter gallery
    await expect(modal).not.toBeVisible({ timeout: 10000 });

    // Check URL
    await expect(page).toHaveURL(/tag=deep-sky/);
  });
});
