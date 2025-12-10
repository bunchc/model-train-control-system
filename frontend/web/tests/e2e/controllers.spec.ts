import { test, expect } from '@playwright/test';
import { getControllerIds } from './testDataHelper';

/**
 * E2E tests for Controller Management UI
 *
 * Prerequisites:
 * - Backend running at localhost:8000 (docker-compose up)
 * - At least one controller configured in config.yaml
 * - Frontend dev server (auto-started by Playwright)
 *
 * Test data assumption: "Test Controller" controller exists with trains
 */

/**
 * Wait for controllers to finish loading on the page
 */
async function waitForControllersLoaded(page: import('@playwright/test').Page) {
  // Wait for page title to appear
  await page.waitForSelector('h1:has-text("Edge Controllers")', { timeout: 10000 });

  // Then wait for loading to complete (either cards or empty state)
  await Promise.race([
    page.waitForSelector('[data-testid^="controller-card-"]', { timeout: 10000 }).catch(() => null),
    page.waitForSelector('text="No controllers configured"', { timeout: 10000 }).catch(() => null),
  ]);
}

test.describe('Controllers List Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/controllers');
    await waitForControllersLoaded(page);
  });

  test('displays controller cards when controllers exist', async ({ page, request }) => {
    await expect(page.locator('h1')).toHaveText('Edge Controllers');
    const controllerIds = await getControllerIds(request);
    if (!controllerIds.length) {
      await expect(page.locator('text="No controllers configured"')).toBeVisible();
    } else {
      for (const controllerId of controllerIds) {
        await expect(page.locator(`[data-testid="controller-card-${controllerId}"]`)).toBeVisible();
      }
    }
  });

  test('controller card shows status badge', async ({ page, request }) => {
    const controllerIds = await getControllerIds(request);
    if (!controllerIds.length) test.skip();
    const statusBadge = page.locator('[data-testid^="controller-status-"]');
    await expect(statusBadge.first()).toBeVisible();
  });

  test('clicking controller card navigates to detail page', async ({ page, request }) => {
    const controllerIds = await getControllerIds(request);
    if (!controllerIds.length) test.skip();
    const controllerId = controllerIds[0];
    await page.locator(`[data-testid="controller-card-${controllerId}"]`).click();
    await page.waitForURL(new RegExp(`/controllers/${controllerId}`), { timeout: 5000 });
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('text="Back to Dashboard"')).toBeVisible();
  });
});

test.describe('Controllers Navigation', () => {
  test('can navigate to controllers page from header', async ({ page }) => {
    // Start at dashboard
    await page.goto('/');

    // Wait for page to load
    await page.waitForSelector('h1', { timeout: 5000 });

    // Click Controllers link in header navigation
    await page.locator('a[href="/controllers"]').click();

    // Wait for navigation
    await page.waitForURL('/controllers');

    // Verify we're on controllers page
    await expect(page.locator('h1')).toHaveText('Edge Controllers');
  });
});

test.describe('Controller Detail Page', () => {
  let controllerId;
  let controllerName;
  let controllerAddress;
  test.beforeEach(async ({ page, request }) => {
    // Fetch controllers from API
    const response = await request.get('/api/controllers');
    expect(response.ok()).toBeTruthy();
    const controllers = await response.json();
    if (controllers.length === 0) {
      test.skip();
    }
    controllerId = controllers[0].id;
    controllerName = controllers[0].name;
    controllerAddress = controllers[0].address;
    // Navigate to controller detail page via controllers list
    await page.goto('/controllers');
    await waitForControllersLoaded(page);
    await page.locator(`[data-testid="controller-card-${controllerId}"]`).click();
    await page.waitForSelector(`h1:has-text("${controllerName}")`, { timeout: 5000 });
  });

  test('controller detail page shows controller name and status', async ({ page }) => {
    // Verify controller name in heading
    await expect(page.locator('h1')).toContainText(controllerName);
    // Verify status badge is visible (Online, Offline, or Unknown)
    const statusBadge = page.locator(`[data-testid="controller-status-${controllerId}"]`);
    await expect(statusBadge).toBeVisible();
  });

  test('Controller Info card displays ID and address', async ({ page }) => {
    // Verify Controller Info section exists
    await expect(page.locator('h3:has-text("Controller Info")')).toBeVisible();
    // Verify ID field label exists
    await expect(page.locator('text="ID"')).toBeVisible();
    // Verify Address field shows configured IP
    await expect(page.locator('text="Address"')).toBeVisible();
    await expect(page.locator(`[data-testid="controller-address-${controllerId}"]`)).toHaveText(controllerAddress);
  });

  test('System Info card displays platform and Python version', async ({ page }) => {
    // Verify System Info section exists
    await expect(page.locator('h3:has-text("System Info")')).toBeVisible();

    // Verify Platform field label exists
    await expect(page.locator('text="Platform"')).toBeVisible();

    // Verify Python field label exists
    await expect(page.locator('text="Python"')).toBeVisible();
  });

  test('back link returns to dashboard', async ({ page }) => {
    // Click back link
    await page.locator('text="Back to Dashboard"').click();

    // Verify navigation to dashboard (root)
    await page.waitForURL('/');

    // Verify dashboard content is visible
    await expect(page.locator('h1')).toBeVisible();
  });
});

test.describe('Breadcrumb Navigation Flow', () => {
  let controller;
  test.beforeEach(async ({ page, request }) => {
    // Fetch controllers from API
    const response = await request.get('/api/controllers');
    expect(response.ok()).toBeTruthy();
    const controllers = await response.json();
    // Find a controller with at least one assigned train
    controller = controllers.find(c => Array.isArray(c.trains) && c.trains.length > 0);
    if (!controller) {
      test.skip();
    }
    // Navigate to controller detail page via controllers list
    await page.goto('/controllers');
    await waitForControllersLoaded(page);
    await page.locator(`[data-testid="controller-card-${controller.id}"]`).click();
    await page.waitForSelector(`h1:has-text("${controller.name}")`, { timeout: 5000 });
  });

  test('assigned trains table shows clickable train links with context', async ({ page }) => {
    // Scroll to Assigned Trains section (may be below fold)
    await page.locator('h2:has-text("Assigned Trains")').scrollIntoViewIfNeeded();

    // Verify section heading is visible
    await expect(page.locator('h2:has-text("Assigned Trains")')).toBeVisible();
    // Verify table exists and has at least one train row
    const tableRows = page.locator('tbody tr');
    await expect(tableRows.first()).toBeVisible();
    // Verify first row shows train name
    const firstTrainName = await tableRows.first().locator('td').first().textContent();
    expect(firstTrainName).toBeTruthy();
    expect(firstTrainName?.trim().length).toBeGreaterThan(0);
    // Verify "View" link exists in Actions column
    const firstViewLink = tableRows.first().locator('a:has-text("View")');
    await expect(firstViewLink).toBeVisible();
    // Verify link has proper href with query parameters for breadcrumb context
    const href = await firstViewLink.getAttribute('href');
    expect(href).toMatch(/^\/trains\/[a-z0-9-]+\?/);
    expect(href).toContain('from=');
    expect(href).toContain('fromName=');
  });

  test('clicking train link navigates to detail page with breadcrumb showing controller name', async ({ page }) => {
    // Scroll to Assigned Trains section
    await page.locator('h2:has-text("Assigned Trains")').scrollIntoViewIfNeeded();

    // Click the first "View" link in the table
    const firstViewLink = page.locator('tbody tr').first().locator('a:has-text("View")');
    await firstViewLink.click();

    // Wait for train detail page to load
    await page.waitForSelector('h1', { timeout: 5000 });

    // Verify URL contains breadcrumb query parameters
    const currentUrl = page.url();
    expect(currentUrl).toContain('from=%2Fcontrollers%2F'); // URL-encoded /controllers/
    expect(currentUrl).toContain(`fromName=${encodeURIComponent(controller.name)}`);
    // Verify breadcrumb link shows "Back to <Controller Name>"
    const breadcrumb = page.locator(`a:has-text("Back to ${controller.name}")`);
    await expect(breadcrumb).toBeVisible();
    // Verify breadcrumb has arrow icon (accessible via ArrowLeftIcon)
    const breadcrumbIcon = breadcrumb.locator('svg');
    await expect(breadcrumbIcon).toBeVisible();
    // Verify breadcrumb href points to controller detail page
    const breadcrumbHref = await breadcrumb.getAttribute('href');
    expect(breadcrumbHref).toMatch(new RegExp(`^/controllers/${controller.id}$`));
  });

  test('clicking breadcrumb navigates back to controller detail page', async ({ page }) => {
    // Navigate to train via controller (establish breadcrumb context)
    await page.locator('h2:has-text("Assigned Trains")').scrollIntoViewIfNeeded();
    const firstViewLink = page.locator('tbody tr').first().locator('a:has-text("View")');
    await firstViewLink.click();

    // Wait for train detail page to load
    await page.waitForSelector('h1', { timeout: 5000 });

    // Verify we're on train detail page
    const trainUrl = page.url();
    expect(trainUrl).toContain('/trains/');

    // Click the breadcrumb to navigate back
    const breadcrumb = page.locator(`a:has-text("Back to ${controller.name}")`);
    await breadcrumb.click();
    // Wait for navigation back to controller detail page
    await expect(page.locator('h2:has-text("Assigned Trains")')).toBeVisible();
    // Verify URL is clean controller detail URL (no query params from train page)
    const finalUrl = page.url();
    expect(finalUrl).toMatch(new RegExp(`/controllers/${controller.id}$`));
    expect(finalUrl).not.toContain('from=');
    expect(finalUrl).not.toContain('fromName=');
    // Verify we can see the trains table we started from
    const tableRows = page.locator('tbody tr');
    await expect(tableRows.first()).toBeVisible();
  });

  test('train detail page shows default breadcrumb when accessed directly without context', async ({ page }) => {
    // Get a train ID from the assigned trains table first
    await page.locator('h2:has-text("Assigned Trains")').scrollIntoViewIfNeeded();
    const firstViewLink = page.locator('tbody tr').first().locator('a:has-text("View")');
    const href = await firstViewLink.getAttribute('href');

    // Extract train ID from href (format: /trains/{trainId}?...)
    const trainId = href?.match(/\/trains\/([a-z0-9-]+)/)?.[1];
    expect(trainId).toBeTruthy();

    // Navigate directly to train detail page WITHOUT query parameters
    await page.goto(`/trains/${trainId}`);

    // Wait for train detail page to load
    await page.waitForSelector('h1', { timeout: 5000 });

    // Verify default breadcrumb is shown (fallback behavior)
    const breadcrumb = page.locator('a:has-text("Back to Dashboard")');
    await expect(breadcrumb).toBeVisible();

    // Verify breadcrumb href points to root
    const breadcrumbHref = await breadcrumb.getAttribute('href');
    expect(breadcrumbHref).toBe('/');

    // Click breadcrumb to verify it works
    await breadcrumb.click();

    // Should navigate to dashboard (root)
    await page.waitForURL('/');
    await expect(page.locator('h1')).toBeVisible();
  });
});
