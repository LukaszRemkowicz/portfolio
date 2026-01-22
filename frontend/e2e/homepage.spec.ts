import { test, expect } from "@playwright/test";

test.describe("Landing Page", () => {
  test.beforeEach(async ({ page }) => {
    // Catch-all mock for API v1
    await page.route("**/api/v1/**", async (route) => {
      const url = route.request().url();

      if (url.includes("/profile/")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            first_name: "Test",
            last_name: "User",
            short_description: "Sky Hunter",
          }),
        });
      }

      if (url.includes("/background/")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            url: "https://via.placeholder.com/1920x1080",
          }),
        });
      }

      if (url.includes("/whats-enabled/")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            contactForm: true,
            programming: true,
            gallery: true,
            lastimages: true,
          }),
        });
      }

      if (url.includes("/image/")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            {
              pk: 1,
              name: "Test Galaxy",
              url: "https://via.placeholder.com/800x600",
              thumbnail_url: "https://via.placeholder.com/200x150",
              description: "A test galaxy far away",
              capture_date: "2023-01-01",
              location: "Backyard",
              tags: ["Galaxy", "Deep Sky"],
            },
            {
              pk: 2,
              name: "Test Nebula",
              url: "https://via.placeholder.com/800x600",
              thumbnail_url: "https://via.placeholder.com/200x150",
              description: "A test nebula",
              capture_date: "2023-01-02",
              location: "Mountain",
              tags: ["Nebula"],
            },
          ]),
        });
      }

      // Default fallback for other API calls (like /contact/ which might be handled in the test itself)
      if (route.request().method() === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([]),
        });
      }

      return route.continue();
    });

    await page.goto("/");
  });

  test("should display the hero section with correct title", async ({
    page,
  }) => {
    // Check for the main title
    const title = page.locator("h1").first();
    await expect(title).toContainText("The Beauty of");
    await expect(title).toContainText("Ancient Light.");
  });

  test("should navigate to gallery and back", async ({ page }) => {
    // Click on "View Portfolio"
    await page.click("text=View Portfolio");

    // Should be on the astrophotography page
    await expect(page).toHaveURL(/\/astrophotography/);

    // Check for gallery title
    await expect(page.locator("h1").first()).toContainText("Gallery");

    // Go back to home - click the logo
    await page.click('nav a:has-text("Łukasz Remkowicz")');
    await expect(page).toHaveURL("http://localhost:3000/");
  });

  test("should open image modal in gallery", async ({ page }) => {
    // Wait for images to load
    const firstImage = page
      .getByRole("button", { name: /View details for/ })
      .first();
    await expect(firstImage).toBeVisible({ timeout: 20000 });

    // Click on the first image - use force to skip pointer-events issues
    await firstImage.click({ force: true });

    // Modal should be visible
    const modal = page.getByTestId("image-modal");
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Close modal
    await page.keyboard.press("Escape");
    await expect(modal).not.toBeVisible();
  });

  test("should submit contact form", async ({ page }) => {
    // Mock the contact endpoint
    await page.route("**/api/v1/contact/", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ success: true }),
      });
    });

    // Scroll to contact
    const contactHeading = page.locator('h2:has-text("Direct Inquiry")');
    await expect(contactHeading).toBeVisible();
    await contactHeading.scrollIntoViewIfNeeded();

    // Fill form
    await page.fill('#contact input[name="name"]', "Test User", {
      force: true,
    });
    await page.fill('#contact input[name="email"]', "test@example.com", {
      force: true,
    });
    await page.fill('#contact input[name="subject"]', "Test Subject", {
      force: true,
    });
    await page.fill(
      '#contact textarea[name="message"]',
      "This is a test message longer than 10 chars.",
      { force: true },
    );

    // Submit
    await page.click('#contact button[type="submit"]');

    // Check for success message
    await expect(
      page.locator("text=Thank you! Your message has been sent successfully."),
    ).toBeVisible();
  });
});
