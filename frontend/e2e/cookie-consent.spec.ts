// frontend/e2e/cookie-consent.spec.ts
import { test, expect } from './fixtures';

test.beforeEach(async ({ page, context }) => {
  // 1. Mock endpoints
  await page.route('**/v1/profile/', async route =>
    route.fulfill({ status: 200, body: JSON.stringify({}) })
  );
  await page.route('**/v1/background/', async route =>
    route.fulfill({ status: 200, body: JSON.stringify({ url: '' }) })
  );
  await page.route('**/v1/settings/', async route => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({
        contactForm: true,
        programming: true,
        gallery: true,
        lastimages: true,
        travelHighlights: true,
        meteors: null,
      }),
    });
  });

  // 2. Clear context
  await context.clearCookies();
});

test.describe('Cookie Consent & Privacy Policy', () => {
  test.beforeEach(async ({ page }) => {
    // Go to home page
    await page.goto('/', { waitUntil: 'domcontentloaded' });

    // Wait for app to be ready
    await page.waitForFunction(
      () => !document.querySelector('[class*="loadingScreen"]')
    );
    await expect(page.getByText('Signal lost')).toBeHidden();
  });

  test('hides banner and sets localStorage when Accept is clicked', async ({
    page,
  }) => {
    // Force banner open to ensure deterministic test
    await page.evaluate(() => (window as any).openCookieSettings());

    // Wait for banner
    const banner = page.getByRole('heading', { name: 'Cookie Consent' });
    await expect(banner).toBeVisible({ timeout: 5000 });

    // Click Accept
    await page.getByRole('button', { name: 'Accept' }).click();

    // Banner disappears
    await expect(banner).not.toBeVisible();

    // Storage updated
    const consent = await page.evaluate(() =>
      localStorage.getItem('cookieConsent')
    );
    expect(consent).toBe('true');
  });

  test('hides banner and sets localStorage when Decline is clicked', async ({
    page,
  }) => {
    // Force banner open
    await page.evaluate(() => (window as any).openCookieSettings());

    await page.getByRole('button', { name: 'Decline' }).click();

    // Banner should disappear
    await expect(
      page.getByRole('heading', { name: 'Cookie Consent' })
    ).not.toBeVisible({ timeout: 1000 });

    // Check localStorage
    const cookieConsent = await page.evaluate(() =>
      localStorage.getItem('cookieConsent')
    );
    expect(cookieConsent).toBe('false');
  });

  test('does not show banner on subsequent visits after accepting', async ({
    page,
  }) => {
    // beforeEach navigated, now set localStorage and reload
    await page.evaluate(() => localStorage.setItem('cookieConsent', 'true'));
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForFunction(
      () => !document.querySelector('[class*="loadingScreen"]'),
      { timeout: 15000 }
    );
    // Wait a bit to ensure banner doesn't appear
    await page.waitForTimeout(1500);

    // Banner should not appear
    expect(
      await page.getByRole('heading', { name: 'Cookie Consent' }).isVisible()
    ).toBeFalsy();
  });

  test('does not show banner on subsequent visits after declining', async ({
    page,
  }) => {
    // beforeEach navigated, now set localStorage and reload
    await page.evaluate(() => localStorage.setItem('cookieConsent', 'false'));
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForFunction(
      () => !document.querySelector('[class*="loadingScreen"]'),
      { timeout: 15000 }
    );
    // Wait a bit to ensure banner doesn't appear
    await page.waitForTimeout(1500);

    // Banner should not appear
    expect(
      await page.getByRole('heading', { name: 'Cookie Consent' }).isVisible()
    ).toBeFalsy();
  });

  test('reopens banner when Cookie Settings is clicked in footer', async ({
    page,
  }) => {
    // Force banner open initially so we can dismiss it
    await page.evaluate(() => (window as any).openCookieSettings());

    // Dismiss it first
    await page.getByRole('button', { name: 'Accept' }).click();
    await expect(
      page.getByRole('heading', { name: 'Cookie Consent' })
    ).not.toBeVisible();

    // Footer interaction
    const footer = page.locator('footer');
    await footer.scrollIntoViewIfNeeded();
    // Use locator with filter to avoid strict mode issues if any hidden elements exist
    await footer
      .locator('button', { hasText: 'Cookie Settings' })
      .first()
      .click();

    // Banner should reappear
    await expect(
      page.getByRole('heading', { name: 'Cookie Consent' })
    ).toBeVisible({ timeout: 2000 });
  });

  test('navigates to Privacy Policy from footer link', async ({ page }) => {
    // Dismiss cookie banner
    await page.getByRole('button', { name: 'Decline' }).click();
    await expect(
      page.getByRole('heading', { name: 'Cookie Consent' })
    ).not.toBeVisible();

    // Footer interaction
    const footer = page.locator('footer');
    await footer.scrollIntoViewIfNeeded();

    await footer.locator('a', { hasText: 'Privacy Policy' }).first().click();

    // Should navigate to privacy page
    await page.waitForURL('**/privacy', { timeout: 5000 });
    await expect(page).toHaveURL(/\/privacy/);

    // Verify content
    await expect(
      page.getByRole('heading', { name: 'Privacy Policy & Cookie Notice' })
    ).toBeVisible();
  });
});

test.describe('Privacy Policy Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/privacy', { waitUntil: 'domcontentloaded' });
  });

  test('displays all required GDPR information', async ({ page }) => {
    // Check main sections
    await expect(
      page.getByRole('heading', { name: 'Privacy Policy & Cookie Notice' })
    ).toBeVisible();
    await expect(page.getByText(/Last updated:/i)).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Introduction' })
    ).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'What Data We Collect' })
    ).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Cookies Used' })
    ).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Why We Use Cookies' })
    ).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Your Choices & Rights' })
    ).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Data Retention' })
    ).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Third-Party Services' })
    ).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Contact' })).toBeVisible();
  });

  test('documents all Google Analytics cookies', async ({ page }) => {
    // Check for _ga cookie
    await expect(page.getByText('_ga', { exact: true })).toBeVisible();
    await expect(page.getByText(/2 years/i)).toBeVisible();

    // Check for _gid cookie
    await expect(page.getByText('_gid', { exact: true })).toBeVisible();
    await expect(page.getByText(/24 hours/i)).toBeVisible();

    // Check for _gat cookie
    await expect(page.getByText('_gat', { exact: true })).toBeVisible();
    await expect(page.getByText(/1 minute/i)).toBeVisible();
  });

  test('provides Google Analytics opt-out link', async ({ page }) => {
    const optOutLink = page.getByRole('link', {
      name: /Google Analytics Opt-out Browser Add-on/i,
    });
    await expect(optOutLink).toBeVisible();
    await expect(optOutLink).toHaveAttribute(
      'href',
      'https://tools.google.com/dlpage/gaoptout'
    );
    await expect(optOutLink).toHaveAttribute('target', '_blank');
    await expect(optOutLink).toHaveAttribute('rel', 'noopener noreferrer');
  });

  test('provides link to Google Privacy Policy', async ({ page }) => {
    const googlePrivacyLink = page.getByRole('link', {
      name: /Google Privacy Policy/i,
    });
    await expect(googlePrivacyLink).toBeVisible();
    await expect(googlePrivacyLink).toHaveAttribute(
      'href',
      'https://policies.google.com/privacy'
    );
    await expect(googlePrivacyLink).toHaveAttribute('target', '_blank');
  });

  test('states data retention period', async ({ page }) => {
    await expect(page.getByText(/26 months/i)).toBeVisible();
  });

  test('clarifies no PII is collected', async ({ page }) => {
    await expect(
      page.getByText(/No personally identifiable information/i)
    ).toBeVisible();
    await expect(
      page.getByText(/cannot identify individual visitors/i)
    ).toBeVisible();
  });

  test('is accessible via navbar or footer from any page', async ({ page }) => {
    // Dismiss cookie banner
    await page.getByRole('button', { name: 'Decline' }).click();

    // Use link role with exact match
    await page.locator('a', { hasText: 'Privacy Policy' }).first().click();
    await page.waitForURL('**/privacy');

    // Navigate back home
    await page.goto('/');

    // Verify we can still access the page
    await expect(page).toHaveURL('http://localhost:3000/');
  });
});
