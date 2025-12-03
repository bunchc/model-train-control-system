# Web UI Testing Strategy - Comprehensive Plan

**Status**: 📋 Planning Document  
**Created**: 2025-12-03  
**Purpose**: Apply RTL + Playwright testing to all frontend features  
**Context**: Proven strategy from Train Config Modal implementation

---

## Executive Summary

This document provides a complete, copy-paste-ready plan to add comprehensive test coverage to the Model Train Control System web UI. The strategy uses two complementary layers:

1. **React Testing Library (RTL)** - Fast component/integration tests
2. **Playwright** - Real browser end-to-end tests

**Time Investment**: ~2-3 hours per major feature  
**ROI**: Catch bugs before production, safe refactoring, living documentation

---

## Testing Philosophy

### The Pyramid (What We're Building)

```
        /\
       /E2E\          ← Playwright (5-10 critical paths)
      /----\
     /Integ \         ← RTL + API mocks (20-30 tests)
    /--------\
   /   Unit   \       ← Jest (50+ tests for utilities/hooks)
  /------------\
```

### Coverage Goals by Layer

| Layer | Tool | What to Test | Coverage Target |
|-------|------|--------------|-----------------|
| Unit | Jest | Pure functions, utilities, custom hooks | 80-90% |
| Integration | RTL | Components with user interactions | 70-80% |
| E2E | Playwright | Critical user workflows | Happy path + 1-2 error cases |

---

## Current Web UI Feature Inventory

Based on `frontend/web/src/` structure:

### High Priority (User-Facing Core Features)

1. **Train List (`pages/TrainList.tsx`)**
   - Display all trains
   - Real-time status updates
   - Navigation to detail

2. **Train Detail (`pages/TrainDetail.tsx`)**
   - Show train info + telemetry
   - Control panel (speed/direction)
   - Config modal trigger

3. **Train Config Modal (`components/trains/TrainConfigModal.tsx`)** ✅ DONE
   - Edit name/description
   - Toggle invert directions
   - Validation + toasts

4. **Controller List (`pages/ControllerList.tsx`)**
   - Display edge controllers
   - Status indicators
   - Health checks

5. **Dashboard (`pages/Dashboard.tsx`)**
   - System overview
   - Quick stats
   - Recent activity

### Medium Priority (Supporting Features)

6. **Train Control Panel (`components/trains/TrainControlPanel.tsx`)**
   - Speed slider
   - Direction buttons
   - Emergency stop

7. **Telemetry Display (`components/trains/TelemetryCard.tsx`)**
   - Voltage/current/speed
   - Real-time updates
   - Alerts/warnings

8. **Navigation (`components/layout/Navigation.tsx`)**
   - Menu routing
   - Active state
   - Mobile responsive

### Low Priority (Nice to Have)

9. **Theme Toggle** (Dark mode)
10. **Error Boundaries**
11. **Loading States**

---

## Testing Template: RTL + Playwright

### For Each Feature, Create

```
frontend/web/
├── src/
│   ├── components/trains/TrainControlPanel.tsx
│   └── pages/TrainList.tsx
├── tests/
│   ├── components/
│   │   └── TrainControlPanel.test.tsx      ← RTL tests
│   ├── e2e/
│   │   ├── train-control.spec.ts           ← Playwright E2E
│   │   └── train-list.spec.ts
│   └── utils/
│       └── test-utils.tsx                   ← Shared helpers
```

---

## Step-by-Step Implementation Guide

### Phase 1: Setup (One-time, 15-20 min)

#### 1.1 Install Dependencies

```bash
cd frontend/web

# RTL (likely already installed)
npm install -D @testing-library/react @testing-library/jest-dom @testing-library/user-event

# Playwright
npm install -D @playwright/test

# Initialize Playwright
npx playwright install
```

#### 1.2 Create Test Utilities

**File**: `frontend/web/tests/utils/test-utils.tsx`

```typescript
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { ReactElement } from 'react';

// Create a custom render that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </BrowserRouter>
  );
};

export const renderWithProviders = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything
export * from '@testing-library/react';
export { renderWithProviders as render };
```

#### 1.3 Configure Playwright

**File**: `frontend/web/playwright.config.ts`

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:3001',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3001',
    reuseExistingServer: !process.env.CI,
  },
});
```

#### 1.4 Update package.json Scripts

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:all": "npm test && npm run test:e2e"
  }
}
```

---

### Phase 2: Per-Feature Test Implementation

For each feature, follow this 4-step process:

#### Step 1: RTL Component Tests (20-30 min per feature)

**Template**: `tests/components/[ComponentName].test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from '../utils/test-utils';
import { ComponentName } from '@/components/path/ComponentName';

describe('ComponentName', () => {
  // Test 1: Rendering
  it('renders with initial state', () => {
    render(<ComponentName />);
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
  });

  // Test 2: User interaction
  it('handles user input correctly', async () => {
    const user = userEvent.setup();
    render(<ComponentName />);

    const input = screen.getByLabelText(/name/i);
    await user.type(input, 'Test Value');

    expect(input).toHaveValue('Test Value');
  });

  // Test 3: Validation
  it('shows validation errors', async () => {
    const user = userEvent.setup();
    render(<ComponentName />);

    await user.click(screen.getByRole('button', { name: /submit/i }));

    expect(await screen.findByText(/required/i)).toBeInTheDocument();
  });

  // Test 4: API success
  it('handles successful submission', async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();
    render(<ComponentName onSuccess={onSuccess} />);

    await user.type(screen.getByLabelText(/name/i), 'Valid Input');
    await user.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  // Test 5: API error
  it('displays error message on failure', async () => {
    // Mock API to return error
    vi.mock('@/api/endpoints/trains', () => ({
      updateTrain: vi.fn().mockRejectedValue(new Error('API Error'))
    }));

    const user = userEvent.setup();
    render(<ComponentName />);

    await user.click(screen.getByRole('button', { name: /submit/i }));

    expect(await screen.findByText(/error/i)).toBeInTheDocument();
  });
});
```

**What to Test:**

- ✅ Component renders without crashing
- ✅ Props control rendering correctly
- ✅ User interactions trigger expected behavior
- ✅ Validation works (show/hide errors)
- ✅ API calls succeed (mocked)
- ✅ API calls fail gracefully (mocked errors)
- ✅ Loading states display
- ✅ Conditional rendering (if/else logic)

**What NOT to Test:**

- ❌ CSS styling (use visual regression instead)
- ❌ Third-party library internals
- ❌ Implementation details (state variable names)

#### Step 2: Playwright E2E Tests (20-30 min per feature)

**Template**: `tests/e2e/[feature-name].spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to feature page
    await page.goto('/trains');

    // Wait for data to load
    await page.waitForSelector('[data-testid="train-list"]');
  });

  test('happy path: user completes main workflow', async ({ page }) => {
    // Step 1: Find and click action button
    await page.click('[aria-label="Configure train"]');

    // Step 2: Interact with modal
    await expect(page.locator('dialog')).toBeVisible();
    await page.fill('input[name="name"]', 'Updated Name');

    // Step 3: Submit
    await page.click('button:has-text("Save Changes")');

    // Step 4: Verify success
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page.locator('text=Updated Name')).toBeVisible();
  });

  test('validation: prevents invalid input', async ({ page }) => {
    await page.click('[aria-label="Configure train"]');

    // Try to submit empty form
    await page.fill('input[name="name"]', '');
    await page.click('button:has-text("Save Changes")');

    // Should show error, not close modal
    await expect(page.locator('text=/required/i')).toBeVisible();
    await expect(page.locator('dialog')).toBeVisible();
  });

  test('cancel: discards changes', async ({ page }) => {
    const originalName = await page.locator('[data-testid="train-name"]').textContent();

    await page.click('[aria-label="Configure train"]');
    await page.fill('input[name="name"]', 'Temporary');
    await page.click('button:has-text("Cancel")');

    // Should close modal without saving
    await expect(page.locator('dialog')).not.toBeVisible();
    await expect(page.locator(`text=${originalName}`)).toBeVisible();
  });
});
```

**What to Test:**

- ✅ Critical user path (happy path)
- ✅ Form validation prevents bad data
- ✅ Error states display correctly
- ✅ Navigation works
- ✅ Real API integration (uses localhost:8000)

**What NOT to Test:**

- ❌ Every possible edge case (RTL covers that)
- ❌ Internal state management
- ❌ Multiple browser types (unless specifically needed)

#### Step 3: Run Tests (5 min)

```bash
# Run RTL tests
npm test

# Run Playwright tests (headless)
npm run test:e2e

# Run Playwright tests (UI mode for debugging)
npm run test:e2e:ui

# Run everything
npm run test:all
```

#### Step 4: Verify Coverage (5 min)

```bash
# Generate coverage report
npm test -- --coverage

# Check coverage/index.html
open coverage/index.html
```

**Coverage Goals:**

- Components: 70-80%
- Utils/Hooks: 80-90%
- Overall: 70%+

---

## Feature-by-Feature Checklist

Copy this for each feature you test:

### Feature: [Name]

**Files:**

- [ ] Component: `src/components/[path]/[Name].tsx`
- [ ] RTL Tests: `tests/components/[Name].test.tsx`
- [ ] E2E Tests: `tests/e2e/[feature].spec.ts`

**RTL Tests Written:**

- [ ] Renders correctly
- [ ] User interactions work
- [ ] Validation logic
- [ ] API success case (mocked)
- [ ] API error case (mocked)
- [ ] Loading states
- [ ] Edge cases

**Playwright Tests Written:**

- [ ] Happy path workflow
- [ ] Validation prevents bad input
- [ ] Cancel/close behavior
- [ ] Error handling

**Execution:**

- [ ] RTL tests pass: `npm test`
- [ ] Playwright tests pass: `npm run test:e2e`
- [ ] Coverage ≥ 70%

**Time Spent**: _____ min

---

## Priority Order for Rollout

Apply testing in this order:

### Week 1: Critical Features

1. ✅ Train Config Modal (DONE - reference implementation)
2. Train Control Panel (speed/direction control)
3. Train Detail page (main user interface)

### Week 2: Core Features

4. Train List page (primary navigation)
5. Controller List page (system health)
6. Dashboard (overview)

### Week 3: Supporting Features

7. Telemetry display components
8. Navigation/layout components
9. Shared UI components (Button, Input, Modal)

### Week 4: Utilities & Hooks

10. Custom hooks (useTrains, useControllers, etc.)
11. API client functions
12. Utility functions

---

## CI/CD Integration (Future)

Once tests are written, add to GitHub Actions:

```yaml
# .github/workflows/frontend-tests.yml
name: Frontend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: cd frontend/web && npm ci

      - name: Run RTL tests
        run: cd frontend/web && npm test

      - name: Run Playwright tests
        run: cd frontend/web && npm run test:e2e

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: frontend/web/playwright-report/
```

---

## Maintenance Guidelines

### When to Update Tests

**Always update when:**

- ✅ Adding new feature
- ✅ Changing user-facing behavior
- ✅ Fixing a bug (add test to prevent regression)

**Consider updating when:**

- Refactoring component structure
- Updating dependencies
- Changing API contracts

### Red Flags (Tests Smell Bad)

❌ **Test tests implementation, not behavior:**

```typescript
// BAD
expect(component.state.isOpen).toBe(true);

// GOOD
expect(screen.getByRole('dialog')).toBeVisible();
```

❌ **Test is flaky (passes/fails randomly):**

- Add explicit waits: `await waitFor(() => ...)`
- Use `findBy` instead of `getBy` for async elements

❌ **Test takes >5 seconds:**

- Mock slow dependencies
- Reduce test scope

---

## Troubleshooting Guide

### Common RTL Issues

**Problem**: "Unable to find element"

```typescript
// Solution: Use correct query
screen.getByRole('button', { name: /submit/i })  // Accessible
screen.getByTestId('submit-btn')  // Last resort
```

**Problem**: "Test passes locally, fails in CI"

```typescript
// Solution: Add waitFor
await waitFor(() => {
  expect(screen.getByText('Success')).toBeInTheDocument();
});
```

### Common Playwright Issues

**Problem**: "Timeout waiting for element"

```typescript
// Solution: Increase timeout or add explicit wait
await page.waitForSelector('[data-testid="train-list"]', { timeout: 10000 });
```

**Problem**: "Element is not clickable"

```typescript
// Solution: Wait for element to be ready
await page.click('button:has-text("Submit")', { force: false });
```

---

## Quick Reference Commands

```bash
# RTL (fast, run often)
npm test                          # All tests
npm test TrainConfig             # Specific file
npm test -- --coverage           # With coverage
npm test -- --watch              # Watch mode

# Playwright (slower, run before commit)
npm run test:e2e                 # All E2E tests
npm run test:e2e train-config    # Specific test
npm run test:e2e:ui              # Visual debugging mode
npx playwright show-report       # View last results

# Combined
npm run test:all                 # Everything
```

---

## Success Metrics

After implementing this strategy, you should have:

- ✅ **70%+ code coverage** on frontend
- ✅ **All critical paths tested** in E2E
- ✅ **Tests run in <2 min** (RTL) + <5 min (E2E)
- ✅ **No flaky tests** (pass consistently)
- ✅ **Living documentation** (tests explain behavior)

---

## References

- **Train Config Modal Tests**: Reference implementation (completed 2025-12-03)
- **RTL Docs**: https://testing-library.com/react
- **Playwright Docs**: https://playwright.dev
- **Testing Best Practices**: https://kentcdodds.com/blog/common-mistakes-with-react-testing-library

---

## Next Steps

1. **Pick a feature** from the priority list
2. **Copy the templates** from this doc
3. **Write RTL tests** (~30 min)
4. **Write Playwright tests** (~30 min)
5. **Run and verify** (~5 min)
6. **Repeat** for next feature

**Estimated time to test entire UI**: 10-15 hours over 2-3 weeks

**Start now**: Use this doc as your guide, reference Train Config Modal implementation for examples.
