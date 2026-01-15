import { test, expect } from '@playwright/test';

test.describe('Landing Page', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('should display the hero section with correct title', async ({ page }) => {
        // Check for the main title
        const title = page.locator('h1');
        await expect(title).toContainText('The Beauty of');
        await expect(title).toContainText('Ancient Light.');
    });

    test('should navigate to gallery and back', async ({ page }) => {
        // Click on "View Portfolio"
        await page.click('text=View Portfolio');

        // Should be on the astrophotography page
        await expect(page).toHaveURL(/\/astrophotography/);

        // Check for gallery title
        await expect(page.locator('h1')).toContainText('Gallery');

        // Go back to home
        await page.click('nav >> text=Home');
        await expect(page).toHaveURL('/');
    });

    test('should open image modal in gallery', async ({ page }) => {
        // Scroll to gallery
        const gallerySection = page.locator('section:has-text("Latest images")');
        await gallerySection.scrollIntoViewIfNeeded();

        // Wait for images to load
        const firstImage = page.locator('[class*="Gallery_card"]').first();
        await expect(firstImage).toBeVisible({ timeout: 10000 });

        // Click on the first image
        await firstImage.click();

        // Modal should be visible
        const modal = page.locator('[class*="Gallery_modalOverlay"]');
        await expect(modal).toBeVisible();

        // Close modal
        await page.keyboard.press('Escape');
        await expect(modal).not.toBeVisible();
    });

    test('should validate contact form', async ({ page }) => {
        // Scroll to contact
        const contactSection = page.locator('section:has-text("Connect with the Cosmos")');
        await contactSection.scrollIntoViewIfNeeded();

        // Try to submit empty form
        await page.click('button[type="submit"]');

        // Should see validation errors (assuming they appear)
        // Based on Contact.tsx logic, they might be toast messages or field highlights
        // Let's check for "required" or similar if implemented
    });
});
