import { test, expect } from './fixtures';

test.describe('Travel Highlights Page', () => {
  test.beforeEach(async ({ page }) => {
    // Override specific endpoint for travel detail
    await page.route('**/v1/travel/iceland/**', async route => {
      return route.fulfill({
        status: 200,
        headers: {
          'Access-Control-Allow-Origin': '*',
        },
        contentType: 'application/json',
        body: JSON.stringify({
          country: 'Iceland',
          place: null,
          story: '<p>A land of fire and ice...</p>',
          adventure_date: 'Jan 2026',
          created_at: '2026-01-01T00:00:00Z',
          highlight_name: 'Iceland Expedition',
          background_image: 'https://via.placeholder.com/1920x1080',
          images: [
            {
              pk: 101,
              name: 'Northern Lights',
              url: 'https://via.placeholder.com/800x600',
              thumbnail_url: 'https://via.placeholder.com/200x150',
              description: 'Dancing lights.',
              location: 'Reykjavik',
              camera: [{ model: 'Canon R6' }],
              lens: [{ model: '14mm F1.8' }],
              telescope: [],
            },
          ],
        }),
      });
    });

    // Navigate to the travel page
    await page.goto('/travel-highlights/iceland');
  });

  test('should display the travel highlights content', async ({ page }) => {
    // Check main title (Country)
    await expect(
      page.getByRole('heading', { name: 'Iceland' }).first()
    ).toBeVisible();

    // Check subtitle
    await expect(
      page.getByText(/Exploring the cosmic wonders/i).first()
    ).toBeVisible();

    // Check story title
    await expect(page.getByText('Iceland Expedition').first()).toBeVisible();

    // Check story content
    await expect(
      page.getByText('A land of fire and ice...').first()
    ).toBeVisible();
  });

  test('should display image cards with correct specifications', async ({
    page,
  }) => {
    // Check if the title exists as a heading
    await expect(
      page.getByRole('heading', { name: 'Northern Lights' }).first()
    ).toBeVisible();

    // Check description
    await expect(page.getByText('Dancing lights.').first()).toBeVisible();
  });

  test('should open modal when clicking an image', async ({ page }) => {
    const image = page.getByRole('img', { name: 'Northern Lights' }).first();
    await image.click();

    // Check modal
    const modal = page.getByTestId('image-modal');
    await expect(modal).toBeVisible();
    await expect(
      modal.getByRole('heading', { name: 'Northern Lights' })
    ).toBeVisible();
  });
});
