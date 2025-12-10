# Playwright E2E Failures Report

**Test Run Summary:**  

- Date: 2025-12-09T12:22:21Z  
- Total tests: [see Playwright report]  
- Passed: [see Playwright report]  
- Failed: 3  
- Artifacts: `20251209_122221/`, `frontend/web/playwright-report/`

---

## Next Steps Overview

- **Missing data:** 2
- **Timing/wait issues:** 2
- **Selector mismatch:** 1

---

## Failing Test Entries

### Title: frontend/web/tests/e2e/controllers.spec.ts::Controllers List Page > displays controller cards when controllers exist

- **Status:** failing (2025-12-09T12:22:21Z)
- **Test file:** frontend/web/tests/e2e/controllers.spec.ts:24
- **Test name:** "displays controller cards when controllers exist"
- **Failure summary:** Controller card element not found; test expected at least one controller card to be visible.
- **Full error message:**  

  ```
  Error: locator('[data-testid="controller-card-ctrl-123"]') did not match any elements
  ```

- **Stack trace:**  

  ```
  at frontend/web/tests/e2e/controllers.spec.ts:41:9
  ```

- **Selector(s) involved:** `[data-testid="controller-card-ctrl-123"]`
- **Screenshot(s):**  
  - 20251209_122221/controllers-list-page-displays-controller-cards-when-controllers-exist.png  
    - Observation: Screenshot shows empty controller list; no cards rendered.
- **Trace(s):**  
  - 20251209_122221/controllers-list-page-displays-controller-cards-when-controllers-exist.zip
- **HTTP/network notes:**  
  - `/api/controllers` returned `[]` (empty array) during test.
- **Relevant logs:**  
  - No server-side errors in logs; frontend logs show "No controllers configured".
- **Likely cause hypotheses:**  
  1. Test data not seeded; backend returned no controllers.
  2. Timing issue: UI rendered before data loaded.
  3. Selector mismatch if controller IDs changed.
- **Next-investigation steps:**  
  - [x] Inspect `/api/controllers` response during test run.
    - **Result:**
      - `/api/controllers` returned 2 controllers:
        - `b7e6a2e2-8c3a-4e2a-9c1a-2f8e4b7e6a2e` (Test Controller)
        - `13b2c43b-5323-4d58-9ffb-e1bf2b68762f` (625eb0275a8b)
      - **No controller with ID `ctrl-123` present.**
    - `/api/trains` returned 1 train:
      - `7e2b1c2a-8f3e-4b1a-9c2d-1a2b3c4d5e6f` (Test Train)
    - **Conclusion:** Test is looking for `[data-testid="controller-card-ctrl-123"]`, but backend only has UUIDs, not legacy IDs. Test data and selectors are out of sync.
  - [x] Check backend seed script execution in test orchestration.
    - **Result:** Ansible and compose provisioning completed successfully; controllers and trains registered with UUIDs.
  - [x] Confirm controller-card-* elements are rendered with correct IDs.
    - **Result:**
      - Test uses `getControllerIds(request)` to fetch controller IDs from `/api/controllers`.
      - The selector `[data-testid="controller-card-${controllerId}"]` is dynamically built from live backend data (UUIDs).
      - Test logic is correct, but failure may be due to frontend not rendering cards for the returned UUIDs.
      - Screenshot confirms no cards rendered, despite backend returning controllers.
    - **Conclusion:** Frontend is not rendering controller cards for valid UUIDs from backend. Issue is in frontend data binding or rendering logic, not test code or selectors.
  - [ ] Open screenshot and trace for UI state.
- **Priority:** high
- **Repro commands:**  

  ```
  PLAYWRIGHT_API_BASE=http://localhost:8100/api npx playwright test frontend/web/tests/e2e/controllers.spec.ts -g "displays controller cards when controllers exist" --headed --debug
  ```

- **Timestamp:** 2025-12-09T12:22:21Z

---

### Title: frontend/web/tests/e2e/train-config.spec.ts::Train Configuration Modal > should update train configuration successfully

**Status:** passing (2025-12-09T21:10:00Z)
**Test file:** frontend/web/tests/e2e/train-config.spec.ts:35
**Test name:** "should update train configuration successfully"
**Resolution:** Backend patch applied to allow `invert_directions` field; test now passes. Success toast and modal close as expected.

---
**Status:** still failing (2025-12-09T21:10:00Z)

### Title: frontend/web/tests/e2e/controllers.spec.ts::Controller Detail Page > controller detail page shows controller name and status

- **Status:** passing (2025-12-09T22:26:00Z)
- **Resolution:** Test now uses dynamic controller ID, name, and address variables set in beforeEach. Status badge and info card are correctly rendered and asserted. No selector or data mismatch remains.  
- **Notes:** Confirmed by latest E2E run; all Controller Detail Page tests pass.  

---

## Remaining Failing Test Entries (as of 2025-12-09T22:26:00Z)

### Title: frontend/web/tests/e2e/controllers.spec.ts::Breadcrumb Navigation Flow

- **Status:** failing
- **Tests affected:**
  - assigned trains table shows clickable train links with context
  - clicking train link navigates to detail page with breadcrumb showing controller name
  - clicking breadcrumb navigates back to controller detail page
  - train detail page shows default breadcrumb when accessed directly without context
- **Failure summary:** Assigned trains table is empty or not rendered; navigation and link assertions time out or fail due to missing rows/links.
- **Next-investigation steps:**
  1. Confirm test data seeding for assigned trains (ensure at least one train is assigned to the test controller).
  2. Check `/api/controllers` and `/api/trains` responses during test run for correct assignments.
  3. Review frontend logic for rendering assigned trains table on the controller detail page.
  4. Open Playwright screenshots and traces for UI state and selector issues.
- **Priority:** high
- **Repro commands:**

  ```
  PLAYWRIGHT_API_BASE=http://localhost:8100/api npx playwright test frontend/web/tests/e2e/controllers.spec.ts -g "Breadcrumb Navigation Flow" --headed --debug
  ```

---

## Next Steps Overview (updated)

- [x] Fix Controller Detail Page tests to use dynamic controller data (ID, name, address)
- [x] Validate Controller Info card and status badge rendering
- [ ] Debug and resolve Breadcrumb Navigation Flow failures (assigned trains table, navigation, and breadcrumbs)
- [ ] Confirm test data seeding for assigned trains and controller-train relationships
- [ ] Review Playwright artifacts for remaining failures

## Footer

**Command used to generate this TODO:**  
Manual artifact review, Playwright HTML report, and screenshot/trace inspection from `20251209_122221/`

**Report directory:** `20251209_122221/`
