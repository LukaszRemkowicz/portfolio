import { test, expect } from './fixtures';
import type { Route } from '@playwright/test';

const thumbnailPayload = (name: string) => ({
  fallback_image: {
    url: `https://example.test/images/${name}/thumbnail-560.webp`,
    width: 560,
    height: 373,
    mime_type: 'image/webp',
  },
  variants: {
    thumbnail: [
      {
        url: `https://example.test/images/${name}/thumbnail-320.webp`,
        width: 320,
        height: 213,
        mime_type: 'image/webp',
      },
      {
        url: `https://example.test/images/${name}/thumbnail-560.webp`,
        width: 560,
        height: 373,
        mime_type: 'image/webp',
      },
    ],
  },
});

test.describe('Gallery Page', () => {
  test.beforeEach(async ({ page }) => {
    // Override default empty image list with mock data for Gallery tests
    const fulfillAstroImages = async (route: Route) => {
      const url = route.request().url();
      const images = [
        {
          pk: 1,
          name: 'The Milky Way and Red Sprites over Geroldsee (Wagenbrüchsee)',
          slug: 'milky-way-arch',
          description: 'Milky Way over mountains',
          tags: [
            { name: 'Red Sprites', slug: 'red-sprites', count: 1 },
            { name: 'Milky Way', slug: 'milky-way', count: 1 },
            {
              name: 'Astrolandscape',
              slug: 'astrolandscape',
              count: 1,
            },
            { name: 'Airglow', slug: 'airglow', count: 1 },
          ],
          celestial_object: 'Milky Way',
          created_at: '2023-01-01',
          place: { id: 1, name: 'Mountain Pass', country: 'Poland' },
          process: true,
          ...thumbnailPayload('milky-way-arch'),
        },
        {
          pk: 2,
          name: 'Orion Nebula',
          slug: 'orion-nebula',
          description: 'M42 Orion Nebula',
          tags: [
            { name: 'Deep Sky', slug: 'deep-sky', count: 1 },
            { name: 'Nebula', slug: 'nebula', count: 1 },
          ],
          celestial_object: 'Deep Sky',
          created_at: '2023-01-02',
          place: { id: 2, name: 'Backyard', country: 'Poland' },
          process: true,
          ...thumbnailPayload('orion-nebula'),
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
          img.tags.some(t => t.slug.toLowerCase() === tagFilter.toLowerCase())
        );
      }
      if (catFilter) {
        filteredImages = filteredImages.filter(
          img =>
            img.celestial_object?.toLowerCase() === catFilter.toLowerCase() ||
            img.tags.some(t => t.name.toLowerCase() === catFilter.toLowerCase())
        );
      }

      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(filteredImages),
      });
    };

    await page.route('**/v1/astroimages/**', fulfillAstroImages);
    await page.route('**/app/astroimages/**', fulfillAstroImages);

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

  test('should render gallery cards with responsive image candidates', async ({
    page,
  }) => {
    const cardImage = page
      .getByTestId('gallery-card-milky-way-arch')
      .locator('img')
      .first();

    await expect(cardImage).toBeVisible();
    await expect(cardImage).toHaveAttribute(
      'srcset',
      /thumbnail-320\.webp 320w/
    );
    await expect(cardImage).toHaveAttribute(
      'srcset',
      /thumbnail-560\.webp 560w/
    );
    await expect(cardImage).toHaveAttribute('sizes', /100vw/);
    await expect(cardImage).toHaveAttribute('width', '560');
    await expect(cardImage).toHaveAttribute('height', '373');
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

    await page.waitForURL(/\/astrophotography\/milky-way-arch/, {
      timeout: 10000,
    });

    const modal = page.getByTestId('image-modal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Check tags exist - they have # prefix in the UI
    const tag = modal.getByRole('button', { name: '#Milky Way' }).first();
    await expect(tag).toBeVisible({ timeout: 10000 });
  });

  test('should wrap tags below a long modal title', async ({ page }) => {
    await page.goto('/astrophotography/milky-way-arch');

    const modal = page.getByTestId('image-modal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    const title = modal.getByRole('heading', {
      name: 'The Milky Way and Red Sprites over Geroldsee (Wagenbrüchsee)',
    });
    const firstTag = modal.getByRole('button', { name: '#Red Sprites' });
    const titleBox = await title.boundingBox();
    const firstTagBox = await firstTag.boundingBox();

    expect(titleBox).not.toBeNull();
    expect(firstTagBox).not.toBeNull();
    expect(firstTagBox!.y).toBeGreaterThanOrEqual(
      titleBox!.y + titleBox!.height
    );
  });

  test('should navigate to tag view when clicking a tag in modal', async ({
    page,
  }) => {
    // Direct navigation to image state
    await page.goto('/astrophotography/orion-nebula');

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
