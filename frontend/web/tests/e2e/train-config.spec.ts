import { test, expect } from '@playwright/test';

/**
 * E2E tests for Train Configuration Modal
 * Tests the complete user workflow from opening the modal to saving changes
 *
 * Flow: Dashboard → Click Train Card → Train Detail Page → Click Configure (Cog) → Modal
 */

// Helper function to wait for modal to be fully visible (after HeadlessUI animation)
// HeadlessUI's Dialog wrapper may report as "hidden" due to CSS positioning,
// so we target the Dialog.Panel content (the rounded white box) instead
async function waitForModalOpen(page: import('@playwright/test').Page) {
  // Wait for the input field inside the modal - this is definitely visible when modal is open
  await page.waitForSelector('input[id="train-name"]', {
    state: 'visible',
    timeout: 5000
  });
  // Small wait for animation to complete
  await page.waitForTimeout(100);
}

async function waitForModalClose(page: import('@playwright/test').Page) {
  // Modal is closed when the train-name input is no longer visible
  await expect(page.locator('input[id="train-name"]')).not.toBeVisible({ timeout: 5000 });
}

test.describe('Train Configuration Modal', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the dashboard
    await page.goto('http://localhost:3001');

    // Wait for trains to load - look for a train card link
    await page.waitForSelector('a[href^="/trains/"]', { timeout: 10000 });

    // Click the first train card to go to detail page
    await page.locator('a[href^="/trains/"]').first().click();

    // Wait for detail page to load
    await page.waitForSelector('text=Back to Dashboard', { timeout: 5000 });
  });

  test('should update train configuration successfully', async ({ page }) => {
    // Click the configure button (cog icon)
    await page.locator('button[aria-label="Configure train"]').click();

    // Wait for modal to fully open
    await waitForModalOpen(page);

    // Get current name input
    const nameInput = page.locator('input[id="train-name"]');
    await expect(nameInput).toBeVisible();

    // Clear and enter new name
    await nameInput.clear();
    await nameInput.fill('Express Line Engine');

    // Update description
    const descriptionTextarea = page.locator('textarea');
    await descriptionTextarea.clear();
    await descriptionTextarea.fill('Fast passenger train for the main line');

    // Toggle invert directions if it exists
    const invertCheckbox = page.locator('input[id="invert_directions"]');
    if (await invertCheckbox.isVisible()) {
      await invertCheckbox.check();
    }

    // Click Save Changes
    await page.locator('button:has-text("Save Changes")').click();

    // Wait for success toast
    await expect(page.locator('text=/updated/i')).toBeVisible({ timeout: 5000 });

    // Modal should close
    await waitForModalClose(page);

    // Verify the page header shows the new name
    await expect(page.locator('h1:has-text("Express Line Engine")')).toBeVisible();
  });

  test('should prevent saving with empty name', async ({ page }) => {
    // Click the configure button
    await page.locator('button[aria-label="Configure train"]').click();

    // Wait for modal to fully open
    await waitForModalOpen(page);

    // Clear the name field
    const nameInput = page.locator('input[id="train-name"]');
    await nameInput.clear();

    // Click Save Changes
    const saveButton = page.locator('button:has-text("Save Changes")');
    await saveButton.click();

    // Modal should stay open (validation prevents submission)
    // Wait a moment for any potential close animation
    await page.waitForTimeout(300);
    // Verify modal is still open by checking the input is visible
    await expect(nameInput).toBeVisible();

    // The browser's HTML5 validation should prevent submission
    const hasValidationMessage = await nameInput.evaluate((el: HTMLInputElement) => {
      return el.validationMessage !== '';
    });

    // Either HTML5 validation kicks in OR we see an error in the UI
    const errorVisible = await page.locator('text=/required/i').isVisible().catch(() => false);

    expect(hasValidationMessage || errorVisible).toBeTruthy();
  });

  test('should discard changes when cancelled', async ({ page }) => {
    // Click the configure button
    await page.locator('button[aria-label="Configure train"]').click();

    // Wait for modal to fully open
    await waitForModalOpen(page);

    // Get original values
    const nameInput = page.locator('input[id="train-name"]');
    const originalName = await nameInput.inputValue();

    // Make changes
    await nameInput.clear();
    await nameInput.fill('Changed Name');

    const descriptionTextarea = page.locator('textarea');
    await descriptionTextarea.clear();
    await descriptionTextarea.fill('Changed description');

    // Click Cancel
    await page.locator('button:has-text("Cancel")').click();

    // Modal should close
    await waitForModalClose(page);

    // Re-open the modal
    await page.locator('button[aria-label="Configure train"]').click();
    await waitForModalOpen(page);

    // Verify original values are restored
    await expect(nameInput).toHaveValue(originalName);
    await expect(descriptionTextarea).not.toHaveValue('Changed description');

    // Close modal
    await page.locator('button:has-text("Cancel")').click();
  });

  test('should show warning when no changes are made', async ({ page }) => {
    // Click the configure button
    await page.locator('button[aria-label="Configure train"]').click();

    // Wait for modal to fully open
    await waitForModalOpen(page);

    // Don't make any changes, just click Save
    await page.locator('button:has-text("Save Changes")').click();

    // Should see a warning toast
    await expect(page.locator('text=/no changes/i')).toBeVisible({ timeout: 5000 });

    // Modal should stay open - verify by checking input is still visible
    await page.waitForTimeout(300);
    await expect(page.locator('input[id="train-name"]')).toBeVisible();

    // Close modal
    await page.locator('button:has-text("Cancel")').click();
  });
});
