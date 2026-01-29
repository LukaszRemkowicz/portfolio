import { test, expect } from './fixtures';

test.describe('Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    // Override specific routes needed for Homepage tests

    // 1. Mock specific image data for the homepage "Latest Images" section
    await page.route('**/v1/image/**', async route => {
      // Logic from original test: return 2 specific images
      // We only care about the list view here
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            pk: 1,
            name: 'Test Galaxy',
            url: 'https://via.placeholder.com/800x600',
            thumbnail_url: 'https://via.placeholder.com/200x150',
            description: 'A test galaxy far away',
            capture_date: '2023-01-01',
            location: 'Backyard',
            tags: ['Galaxy', 'Deep Sky'],
          },
          {
            pk: 2,
            name: 'Test Nebula',
            url: 'https://via.placeholder.com/800x600',
            thumbnail_url: 'https://via.placeholder.com/200x150',
            description: 'A test nebula',
            capture_date: '2023-01-02',
            location: 'Mountain',
            tags: ['Nebula'],
          },
        ]),
      });
    });

    // 2. Mock Contact Form endpoint
    await page.route('**/v1/contact/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true }),
      });
    });

    // 3. Mock Feature Flags explicitly to ensure Contact Form is enabled
    await page.route('**/v1/settings/', async route => {
      await route.fulfill({
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
    });

    await page.goto('/');
  });

  test('should display the hero section with correct title', async ({
    page,
  }) => {
    const title = page.locator('h1').first();
    await expect(title).toContainText('The Beauty of');
    await expect(title).toContainText('Ancient Light.');
  });

  test('should navigate to gallery and back', async ({ page }) => {
    await page.click('text=View Portfolio');
    await expect(page).toHaveURL(/\/astrophotography/);
    await expect(page.locator('h1').first()).toContainText('Gallery');

    await page.click('nav a:has-text("Łukasz Remkowicz")');
    await expect(page).toHaveURL('http://localhost:3000/');
  });

  test('should open image modal in gallery', async ({ page }) => {
    // Wait for the container to ensure data is loaded
    // Wait for the heading to ensure data is loaded and section is rendered
    // Broader search for the heading
    const heading = page.getByRole('heading', { name: /Latest images/i });

    await expect(heading).toBeVisible({ timeout: 20000 });

    const firstImage = page
      .getByRole('button', { name: /View details for/ })
      .first();

    await expect(firstImage).toBeVisible({ timeout: 10000 });
    await firstImage.click();

    const modal = page.getByTestId('image-modal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    await page.keyboard.press('Escape');
    await expect(modal).not.toBeVisible();
  });

  test('should submit contact form', async ({ page }) => {
    // Use more robust selector and longer timeout for lazy loaded component
    const contactHeading = page.getByRole('heading', {
      name: /Direct Inquiry/i,
    });
    await expect(contactHeading).toBeVisible({ timeout: 15000 });
    await contactHeading.scrollIntoViewIfNeeded();

    await page.fill('#contact input[name="name"]', 'Test User', {
      force: true,
    });
    await page.fill('#contact input[name="email"]', 'test@example.com', {
      force: true,
    });
    await page.fill('#contact input[name="subject"]', 'Test Subject', {
      force: true,
    });
    await page.fill(
      '#contact textarea[name="message"]',
      'This is a test message longer than 10 chars.',
      { force: true }
    );

    await page.click('#contact button[type="submit"]');

    await expect(
      page.locator('text=Thank you! Your message has been sent successfully.')
    ).toBeVisible();
  });
});
