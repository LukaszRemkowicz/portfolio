// frontend/e2e/cookie-consent.spec.ts
import { test, expect } from './fixtures';

test.describe('Cookie Consent & Privacy Policy', () => {
  test.beforeEach(async ({ page, context }) => {
    // Clear localStorage before each test
    await context.clearCookies();

    // HomePage has a loading screen that shows until loadInitialData() completes
    // The tests will fail if we try to interact before the page is ready
    // Wait for navigation to complete and the loading screen to disappear
    await page.goto('/', { waitUntil: 'networkidle' });

    // Wait for the page to not be in loading state
    // The LoadingScreen component should not be visible when page is ready
    await page.waitForFunction(
      () => !document.querySelector('[class*="loadingScreen"]'),
      { timeout: 15000 }
    );

    // Ensure we didn't land on an error page (which also hides loading screen)
    await expect(page.getByText('Signal lost')).not.toBeVisible();
  });

  test('displays cookie banner on first visit', async ({ page }) => {
    // Wait for banner to appear (has 1s delay)
    await expect(
      page.getByRole('heading', { name: 'Cookie Consent' })
    ).toBeVisible({ timeout: 2000 });

    expect(
      await page
        .getByText(/We use cookies to enhance your experience/i)
        .isVisible()
    ).toBeTruthy();

    // Verify buttons are present
    await expect(page.getByRole('button', { name: 'Accept' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Decline' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Learn more' })).toBeVisible();
  });

  test('hides banner and sets localStorage when Accept is clicked', async ({
    page,
  }) => {
    await page.getByRole('button', { name: 'Accept' }).click();

    // Banner should disappear
    await expect(
      page.getByRole('heading', { name: 'Cookie Consent' })
    ).not.toBeVisible({ timeout: 1000 });

    // Check localStorage
    const cookieConsent = await page.evaluate(() =>
      localStorage.getItem('cookieConsent')
    );
    expect(cookieConsent).toBe('true');
  });

  test('hides banner and sets localStorage when Decline is clicked', async ({
    page,
  }) => {
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
    // Banner is visible initially (from beforeEach)
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

  test('navigates to Privacy Policy from Learn more link', async ({ page }) => {
    // Click Learn more link in cookie banner (first Privacy Policy link)
    await page.getByRole('link', { name: 'Learn more' }).click();

    // Should navigate to privacy page
    await page.waitForURL('**/privacy', { timeout: 5000 });
    await expect(page).toHaveURL(/\/privacy/);

    // Verify Privacy Policy content is loaded
    await expect(
      page.getByRole('heading', { name: 'Privacy Policy & Cookie Notice' })
    ).toBeVisible();
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
    await page.goto('/privacy');
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
