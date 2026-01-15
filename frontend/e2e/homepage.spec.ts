import { test, expect } from "@playwright/test";

test.describe("Landing Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("should display the hero section with correct title", async ({
    page,
  }) => {
    // Check for the main title
    const title = page.locator("h1");
    await expect(title).toContainText("The Beauty of");
    await expect(title).toContainText("Ancient Light.");
  });

  test("should navigate to gallery and back", async ({ page }) => {
    // Click on "View Portfolio"
    await page.click("text=View Portfolio");

    // Should be on the astrophotography page
    await expect(page).toHaveURL(/\/astrophotography/);

    // Check for gallery title
    await expect(page.locator("h1")).toContainText("Gallery");

    // Go back to home - click the logo
    await page.click('nav a:has-text("Łukasz Remkowicz")');
    await expect(page).toHaveURL("https://portfolio.local/");
  });

  test("should open image modal in gallery", async ({ page }) => {
    // Wait for images to load - use images inside the gallery
    const firstImage = page.locator("section#gallery img").first();
    await expect(firstImage).toBeVisible({ timeout: 20000 });

    // Click on the first image - use force to skip pointer-events issues
    await firstImage.click({ force: true });

    // Modal should be visible - check for any overlay or modal class
    const modal = page.locator('[class*="modalOverlay"], [class*="modal"]');
    await expect(modal.first()).toBeVisible({ timeout: 10000 });

    // Close modal
    await page.keyboard.press("Escape");
    await expect(modal.first()).not.toBeVisible();
  });

  test("should validate contact form", async ({ page }) => {
    // Scroll to contact - using the actual title
    const contactHeading = page.locator('h2:has-text("Direct Inquiry")');
    await expect(contactHeading).toBeVisible();
    await contactHeading.scrollIntoViewIfNeeded();

    // Check if the form is there
    const emailInput = page.locator('input[type="email"]');
    await expect(emailInput).toBeVisible();

    // Try to submit empty form
    await page.click('button[type="submit"]');

    // Check for some feedback (required attribute or error message)
    const nameInput = page.locator('input[name="name"]');
    const validationMessage = await nameInput.evaluate(
      (node: HTMLInputElement) => node.validationMessage,
    );
    expect(validationMessage).not.toBe("");
  });
});
