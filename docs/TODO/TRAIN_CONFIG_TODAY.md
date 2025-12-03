# Train Configuration - Today's Implementation Plan

**Date:** December 2, 2025  
**Branch:** `feat/web-ui`  
**Goal:** Train configuration modal with direction inversion support

---

## Priority Fix First: Direction Commands

**CRITICAL BUG:** Direction buttons don't work - they send `action: "forward"` but backend expects `action: "setDirection"`

### Quick Fix (5 minutes)

Update `ControlPanel.tsx` line ~67:

```typescript
// CURRENT (BROKEN):
const handleApplySettings = () => {
  handleCommand(
    {
      action: 'setSpeed',
      speed,
      direction: direction.toUpperCase() as 'FORWARD' | 'BACKWARD'
    },
    `Speed set to ${speed}% (${direction})`
  );
};

// This works for speed but direction is ignored by backend
```

**Issue:** Backend expects direction in `setSpeed` command, which should work. Need to verify backend actually handles it.

---

## Today's Implementation Scope

Focus on **Phase 1 (Backend) + Phase 2 (Frontend Modal)** - save direction inversion for later.

### Simplified Goal

Build train configuration modal to edit:

- ✅ Train name (text input)
- ✅ Train description (textarea)
- ⏸️ Direction inversion (defer - need to fix direction commands first)

---

## Task Breakdown (Time Estimates)

### Task 1: Backend - Database Migration (15 min)

**Goal:** Add `invert_directions` column to database

**Files:**

- `central_api/app/services/config_schema.sql`

**Changes:**

```sql
-- Add to trains table
ALTER TABLE trains ADD COLUMN invert_directions BOOLEAN DEFAULT 0;
```

**Testing:**

```bash
# Delete old DB to force recreation
rm -f central_api/central_api_config.db
docker compose -f infra/docker/docker-compose.yml restart central_api
# Check schema
sqlite3 central_api/central_api_config.db ".schema trains"
```

---

### Task 2: Backend - Pydantic Model Update (15 min)

**Goal:** Add `invert_directions` field to Train model

**Files:**

- [x] `central_api/app/models/schemas.py`

**Changes:**

```python
class Train(BaseModel):
    # ... existing fields ...
    invert_directions: bool = False  # <-- ADD THIS
```

**Completed:**

- [x] Task 2.1: Extended Train model with `invert_directions: bool = False`
- [x] Task 2.2: Created TrainUpdateRequest model for partial updates
- [x] Task 2.3: Rebuilt container and verified OpenAPI schema includes new field
- [x] Verified at http://localhost:8000/docs - Train schema shows invert_directions

---

### Task 3: Backend - Update Train Endpoint (30 min)

**Goal:** Create `PUT /api/trains/{train_id}` endpoint

**Files:**

- `central_api/app/routers/trains.py`
- `central_api/app/services/config_manager.py`
- `central_api/app/services/config_repository.py`

**New Endpoint:**

```python
# In trains.py
@router.put("/trains/{train_id}", response_model=Train)
def update_train(
    train_id: str,
    name: str | None = Body(None),
    description: str | None = Body(None),
    invert_directions: bool | None = Body(None),
):
    """Update train configuration.

    Only provided fields will be updated (partial update).
    Returns updated train object.
    """
    logger.info(f"PUT /trains/{train_id} - name={name}, invert={invert_directions}")

    try:
        updated_train = _get_config().update_train(
            train_id=train_id,
            name=name,
            description=description,
            invert_directions=invert_directions
        )
        return updated_train
    except ValueError as e:
        raise HTTPException(404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to update train")
        raise HTTPException(500, detail=f"Update failed: {e}")
```

**Config Manager Method:**

```python
# In config_manager.py
def update_train(
    self,
    train_id: str,
    name: str | None = None,
    description: str | None = None,
    invert_directions: bool | None = None,
) -> Train:
    """Update train configuration (partial update)."""

    # Get current train
    train_data = self.repository.get_train(train_id)
    if not train_data:
        raise ValueError(f"Train {train_id} not found")

    # Update only provided fields
    if name is not None:
        self.repository.update_train_field(train_id, "name", name)
    if description is not None:
        self.repository.update_train_field(train_id, "description", description)
    if invert_directions is not None:
        self.repository.update_train_field(train_id, "invert_directions", invert_directions)

    # Return updated train
    return self.get_train(train_id)
```

**Repository Method:**

```python
# In config_repository.py
def update_train_field(self, train_id: str, field: str, value: Any) -> None:
    """Update a single train field."""
    conn = sqlite3.connect(str(self.db_path))
    try:
        conn.execute(
            f"UPDATE trains SET {field} = ? WHERE id = ?",
            (value, train_id)
        )
        conn.commit()
    finally:
        conn.close()
```

**Testing:**

```bash
# Test with curl
curl -X PUT http://localhost:8000/api/trains/{train_id} \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name", "description": "New description"}'
```

---

### Task 4: Frontend - TypeScript Types (5 min)

**Goal:** Add types for train updates

**Files:**

- `frontend/web/src/api/types.ts`

**Changes:**

```typescript
export interface Train {
  id: string;
  name: string;
  description?: string | null;
  model?: string | null;
  plugin: TrainPlugin;
  invert_directions?: boolean;  // NEW
}

export interface TrainUpdateRequest {
  name?: string;
  description?: string;
  invert_directions?: boolean;
}
```

---

### Task 5: Frontend - API Client (10 min)

**Goal:** Add `updateTrain` function and mutation hook

**Files:**

- `frontend/web/src/api/endpoints/trains.ts`
- `frontend/web/src/api/queries.ts`

**API Function:**

```typescript
// In endpoints/trains.ts
export async function updateTrain(
  trainId: string,
  updates: TrainUpdateRequest
): Promise<Train> {
  const response = await apiClient.put(`/trains/${trainId}`, updates);
  return response.data;
}
```

**React Query Hook:**

```typescript
// In queries.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateTrain } from './endpoints/trains';

export function useUpdateTrain() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ trainId, updates }: { trainId: string; updates: TrainUpdateRequest }) =>
      updateTrain(trainId, updates),
    onSuccess: (updatedTrain) => {
      // Invalidate trains list
      queryClient.invalidateQueries({ queryKey: ['trains'] });
      // Update individual train cache
      queryClient.setQueryData(['train', updatedTrain.id], updatedTrain);
    },
  });
}
```

---

### Task 6: Frontend - Config Modal Component (45 min)

**Goal:** Create reusable modal for train configuration

**Files:**

- `frontend/web/src/components/trains/TrainConfigModal.tsx` (NEW)

**Component:**

```tsx
import React, { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Train, TrainUpdateRequest } from '@/api/types';
import { useUpdateTrain } from '@/api/queries';
import toast from 'react-hot-toast';

export interface TrainConfigModalProps {
  train: Train;
  isOpen: boolean;
  onClose: () => void;
}

export const TrainConfigModal: React.FC<TrainConfigModalProps> = ({
  train,
  isOpen,
  onClose,
}) => {
  const [name, setName] = useState(train.name);
  const [description, setDescription] = useState(train.description || '');
  const [invertDirections, setInvertDirections] = useState(train.invert_directions || false);

  const { mutate: updateTrain, isPending } = useUpdateTrain();

  const handleSave = () => {
    const updates: TrainUpdateRequest = {};

    // Only send changed fields
    if (name !== train.name) updates.name = name;
    if (description !== (train.description || '')) updates.description = description;
    if (invertDirections !== (train.invert_directions || false)) {
      updates.invert_directions = invertDirections;
    }

    if (Object.keys(updates).length === 0) {
      toast.error('No changes to save');
      return;
    }

    updateTrain(
      { trainId: train.id, updates },
      {
        onSuccess: () => {
          toast.success('Train configuration updated');
          onClose();
        },
        onError: (error) => {
          toast.error(`Update failed: ${error.message}`);
        },
      }
    );
  };

  const handleCancel = () => {
    // Reset to original values
    setName(train.name);
    setDescription(train.description || '');
    setInvertDirections(train.invert_directions || false);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleCancel} title="Train Configuration" size="lg">
      <div className="space-y-4">
        {/* Train Name */}
        <div>
          <label htmlFor="train-name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Train Name
          </label>
          <input
            id="train-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            required
          />
        </div>

        {/* Description */}
        <div>
          <label htmlFor="train-description" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Description
          </label>
          <textarea
            id="train-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
          />
        </div>

        {/* Direction Inversion - Only for DC Motor HAT */}
        {train.plugin.name === 'adafruit_dcmotor_hat' && (
          <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800">
            <div>
              <label htmlFor="invert-directions" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Invert Directions
              </label>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Swap forward/reverse (useful if motor is mounted backwards)
              </p>
            </div>
            <button
              id="invert-directions"
              type="button"
              onClick={() => setInvertDirections(!invertDirections)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                invertDirections ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  invertDirections ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        )}

        {/* Read-Only Info */}
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Train Details</h4>
          <dl className="space-y-1 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500 dark:text-gray-400">Train ID:</dt>
              <dd className="font-mono text-gray-900 dark:text-gray-100">{train.id}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500 dark:text-gray-400">Plugin:</dt>
              <dd className="text-gray-900 dark:text-gray-100">{train.plugin.name}</dd>
            </div>
            {train.model && (
              <div className="flex justify-between">
                <dt className="text-gray-500 dark:text-gray-400">Model:</dt>
                <dd className="text-gray-900 dark:text-gray-100">{train.model}</dd>
              </div>
            )}
          </dl>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-3 pt-4">
          <Button variant="outline" onClick={handleCancel} disabled={isPending}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isPending || !name.trim()}>
            {isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
```

---

### Task 7: Frontend - Add Gear Icon to Train Detail (15 min)

**Goal:** Add config button to train page header

**Files:**

- `frontend/web/src/pages/TrainDetail.tsx`

**Changes:**

```tsx
import { CogIcon } from '@heroicons/react/24/outline';
import { TrainConfigModal } from '@/components/trains/TrainConfigModal';

export const TrainDetail: React.FC = () => {
  // ... existing code ...
  const [isConfigOpen, setIsConfigOpen] = useState(false);

  return (
    <PageLayout>
      <div className="space-y-6">
        {/* ... breadcrumb ... */}

        {/* Page Header with Gear Icon */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              {train.name}
            </h1>
            {train.description && (
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                {train.description}
              </p>
            )}
            <div className="mt-2 flex flex-wrap gap-2 text-sm text-gray-500 dark:text-gray-400">
              {/* ... train details ... */}
            </div>
          </div>

          {/* Config Button */}
          <button
            onClick={() => setIsConfigOpen(true)}
            className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-800 dark:hover:text-gray-300"
            title="Train Configuration"
          >
            <CogIcon className="h-6 w-6" />
          </button>
        </div>

        {/* ... rest of page ... */}
      </div>

      {/* Config Modal */}
      <TrainConfigModal
        train={train}
        isOpen={isConfigOpen}
        onClose={() => setIsConfigOpen(false)}
      />
    </PageLayout>
  );
};
```

---

## Testing Checklist

### Backend Tests

- [ ] Database migration creates `invert_directions` column
- [ ] Train model includes `invert_directions` in API response
- [ ] `PUT /api/trains/{id}` updates name successfully
- [ ] `PUT /api/trains/{id}` updates description successfully
- [ ] `PUT /api/trains/{id}` updates invert_directions successfully
- [ ] Partial updates work (only send name, others unchanged)
- [ ] Invalid train ID returns 404
- [ ] Empty name is rejected

### Frontend Tests

- [ ] Gear icon appears next to train name
- [ ] Clicking gear opens modal
- [ ] Modal pre-fills with current train data
- [ ] Name field is required (can't save if empty)
- [ ] Description field is optional
- [ ] Invert toggle only shows for `adafruit_dcmotor_hat` plugin
- [ ] Saving with no changes shows error toast
- [ ] Successful save shows success toast and closes modal
- [ ] Failed save shows error toast and keeps modal open
- [ ] Cancel button resets fields and closes modal
- [ ] Train list updates after save
- [ ] Train detail page updates after save

---

## Time Estimate

| Task | Time | Cumulative |
|------|------|------------|
| 1. Database Migration | 15 min | 15 min |
| 2. Extend Train Model | 10 min | 25 min |
| 3. Update Train Endpoint | 30 min | 55 min |
| 4. TypeScript Types | 5 min | 60 min |
| 5. API Client | 10 min | 70 min |
| 6. Config Modal | 45 min | 115 min |
| 7. Add Gear Icon | 15 min | 130 min |
| **Testing & Debugging** | 30 min | **160 min** |

**Total: ~2.5-3 hours**

---

## What We're NOT Doing Today

### Deferred to Later

- ❌ Controller restart logic (Phase 4)
- ❌ Advanced validation/sanitization (Phase 5)
- ❌ Direction inversion implementation (need to fix direction commands first)

### Why Defer Direction Inversion?

1. Direction commands currently broken (send wrong action)
2. Need to verify backend handles direction in `setSpeed` command
3. Should fix basic direction control before adding inversion layer
4. Modal UI is ready for it - just toggle disabled for now

---

## Success Criteria

**By end of today:**

1. ✅ Can click gear icon on train detail page
2. ✅ Modal opens with train name and description pre-filled
3. ✅ Can edit name/description and save
4. ✅ Changes persist in database
5. ✅ UI updates immediately after save
6. ✅ Invert toggle visible for DC Motor HAT (but functionality deferred)

**Ready for next session:**

- Fix direction command handling
- Implement direction inversion logic
- Add controller restart mechanism

---

## Implementation Order

**Recommended sequence:**

1. **Start with Backend** (Tasks 1-3)
   - Build and test API completely before touching frontend
   - Easier to test with curl/Postman

2. **Then Frontend Types/Client** (Tasks 4-5)
   - Get data layer working
   - Test with browser console

3. **Finally UI Components** (Tasks 6-7)
   - Visual polish and user experience
   - End-to-end testing

4. **Integration Testing**
   - Test full flow: open modal → edit → save → verify
   - Check error cases: network failures, validation

---

## Notes

- Keep `invert_directions` toggle visible but maybe add tooltip: "Coming soon - direction commands need fixing first"
- OR hide the toggle entirely for today, add it later when direction logic is fixed
- Focus on getting the modal infrastructure solid - direction inversion is just one more field

---

## TODO - Implementation Steps (In Order)

**As a senior engineer, here's the optimal implementation sequence to minimize risk and maximize feedback loops:**

### Phase A: Foundation & Validation (Backend First)

- [x] **Task 1.1** - Update database schema (`config_schema.sql`)
  - Add `invert_directions BOOLEAN DEFAULT 0` to trains table
  - Verify schema change doesn't break existing queries
  - **Why first:** Database is source of truth, need schema before anything else

- [x] **Task 1.2** - Test database migration
  - Delete `central_api_config.db` to force recreation
  - Restart central_api container
  - Verify table schema with `sqlite3 .schema trains`
  - Seed test data to ensure columns populate correctly
  - **Why:** Catch schema issues before writing code against it

- [x] **Task 2.1** - Extend Pydantic models (`schemas.py`)
  - Add `invert_directions: bool = False` to `Train` model
  - Create `TrainUpdateRequest` model for partial updates
  - **Why:** Type safety at API boundary, auto-generates OpenAPI docs

- [x] **Task 2.2** - Verify OpenAPI schema update
  - Check http://localhost:8000/docs
  - Ensure `/api/trains` GET shows new field
  - Verify field is optional (not breaking existing clients)
  - **Why:** Confirm backward compatibility before writing update logic

### Phase B: Data Layer (Repository Pattern)

- [x] **Task 3.1** - Add repository method (`config_repository.py`)
  - ✅ Extended existing `update_train()` method with `invert_directions` parameter
  - ✅ Added SQL update logic with parameterized queries (secure)
  - ✅ Converts bool to SQLite integer (1/0) for storage
  - **Why:** Security first, test data access layer in isolation

- [x] **Task 3.2** - Add service layer method (`config_manager.py`)
  - ✅ Implemented `update_train(train_id, **kwargs)` with partial update logic
  - ✅ Handles `None` vs missing field distinction (None = no change)
  - ✅ Returns updated `Train` object from DB
  - ✅ Updated all Train object constructions to include `invert_directions` field
  - **Why:** Business logic separate from HTTP layer, easier to test

- [x] **Task 3.3** - Test service layer
  - ✅ Write unit tests for update_train with mocked repository
  - ✅ Test partial updates (only name, only description, both, none)
  - ✅ Test error cases (train not found, invalid field values)
  - ✅ All 9 tests passing
  - **Why:** Catch logic errors before exposing via HTTP

### Phase C: API Layer (HTTP Interface)

- [x] **Task 4.1** - Create PUT endpoint (`trains.py`)
  - ✅ Added `PUT /api/trains/{train_id}` route
  - ✅ Accepts optional `name`, `description`, `invert_directions` in body
  - ✅ Returns 404 for invalid train_id, 400 for validation errors
  - ✅ Verified in OpenAPI schema at http://localhost:8000/docs
  - **Why:** RESTful interface, follows HTTP semantics

- [x] **Task 4.2** - Test API endpoint manually
  - ✅ Test 0: Baseline state retrieved successfully
  - ✅ Test 1: Partial update (name only) - PASS
  - ✅ Test 2: Partial update (description only) - PASS  
  - ✅ Test 3: Set invert_directions = true - PASS
  - ✅ Test 4: Set invert_directions = false - PASS
  - ✅ Test 5: Update multiple fields simultaneously - PASS
  - ✅ Test 6: Empty body (no updates) - PASS
  - ✅ Test 7: 404 error for invalid train_id - PASS
  - ✅ Test 8: 422 validation error (name too long) - PASS
  - ✅ Test 9: 422 validation error (invalid type) - PASS
  - ✅ Test 10: Changes persist in GET /api/trains list - PASS
  - ✅ Verified logs show successful updates
  - **Why:** Manual testing catches integration issues before frontend

- [x] **Task 4.3** - Verify cache invalidation
  - ✅ Timestamp test: PUT → GET showed updated name immediately
  - ✅ Stress test: 5 rapid PUT→GET cycles all matched (no lag)
  - ✅ Code inspection: No @lru_cache found in codebase
  - ✅ Logs confirm: ConfigManager reads from SQLite on every request
  - ✅ Verdict: No cache issues - updates visible immediately
  - **Why:** Stale cache is a common distributed systems bug

### Phase D: Frontend Types & Client

- [x] **Task 5.1** - Update TypeScript types (`types.ts`)
  - ✅ Added `invert_directions?: boolean` to `Train` interface
  - ✅ Created `TrainUpdateRequest` interface for partial updates
  - ✅ All fields optional (supports partial update semantics)
  - **Why:** Type safety prevents runtime errors, enables autocomplete

- [x] **Task 5.2** - Add API client function (`endpoints/trains.ts`)
  - ✅ Added `TrainUpdateRequest` to imports
  - ✅ Implemented `updateTrain(trainId, updates)` using axios PUT
  - ✅ Returns full `Train` object from backend
  - ✅ Follows existing pattern (error handling via interceptor)
  - **Why:** Centralized API logic, reusable across components

- [x] **Task 5.3** - Create React Query mutation hook (`queries.ts`)
  - ✅ Added `useUpdateTrain()` hook with proper TypeScript types
  - ✅ Invalidates trains cache on success (triggers auto-refresh)
  - ✅ Also invalidates configTrains cache for consistency
  - ✅ Follows existing pattern (useSendCommand as reference)
  - **Why:** Automatic cache management, loading states, error handling

- [x] **Task 5.4** - Test mutation hook in browser console
  - ✅ Created automated test page component with 5 test cases
  - ✅ Test 1: Update name only - PASS
  - ✅ Test 2: Update description only - PASS
  - ✅ Test 3: Update invert_directions - PASS
  - ✅ Test 4: Update multiple fields (restore) - PASS
  - ✅ Test 5: Invalid train ID (404 error) - PASS (expected error)
  - ✅ Verified cache invalidation (trains list auto-refreshed)
  - ✅ Verified network requests in DevTools (PUT /api/trains/{id})
  - ✅ Cleaned up temporary test code
  - **Why:** Validate data flow before building UI

### Phase E: UI Components

- [x] **Task 6.1** - Create modal component (`TrainConfigModal.tsx`)
  - ✅ Created Textarea UI component (mirrors Input pattern)
  - ✅ Built form with controlled inputs (name, description, invert_directions)
  - ✅ Added direction inversion toggle (conditional on plugin type)
  - ✅ Wired up useUpdateTrain mutation hook
  - ✅ Added loading states (disabled form, spinner on button)
  - ✅ Added error display (API errors in red banner)
  - ✅ Added character counters (100/500 limits)
  - **Why:** Reusable component, separation of concerns

- [x] **Task 6.2** - Add form validation
  - ✅ Required field: name cannot be empty
  - ✅ Character limits: name max 100 chars, description max 500
  - ✅ Trim whitespace before saving
  - ✅ Show validation errors inline
  - ✅ Clear errors on field change (better UX)
  - **Why:** Data quality, prevent bad input at UI layer

- [x] **Task 6.3** - Test modal in isolation
  - ✅ Added gear icon button to TrainDetail page
  - ✅ Integrated TrainConfigModal component
  - ✅ Tested in browser: modal opens/closes correctly
  - ✅ Form pre-fills with train data
  - ✅ All validation working (empty name, length limits)
  - ✅ Cancel resets form correctly
  - **Why:** Component testing before full integration

- [x] **Task 7.1** - Integrate modal into TrainDetail page
  - ✅ Added gear icon (CogIcon) to header next to train name
  - ✅ Added modal state (isConfigModalOpen)
  - ✅ Pass train data to modal via props
  - ✅ Handle modal close events (onClose callback)
  - ✅ Styled gear icon with hover effects
  - **Why:** Wire up complete user flow

- [x] **Task 7.2** - Test integration end-to-end
  - ✅ Opened train detail page in browser
  - ✅ Clicked gear icon → modal opens correctly
  - ✅ Edited fields → saved → updates appear on page
  - ✅ Verified train list refreshes (cache invalidation working)
  - ✅ Tested all validation scenarios (empty, too long)
  - ✅ Confirmed changes persist after page refresh
  - **Why:** Validate complete user journey

### Phase F: Polish & Edge Cases

- [x] **Task 8.1** - Add toast notifications
  - ✅ Success toast on save ("Train configuration updated")
  - ✅ Error toast with specific message on failure (from API)
  - ✅ Warning toast on "no changes" save attempt
  - ✅ Used react-hot-toast (already installed)
  - **Why:** User feedback for async operations

- [x] **Task 8.2** - Handle edge cases
  - ✅ Tested with long names (maxLength prevents overflow)
  - ✅ Special characters handled (React auto-escapes)
  - ✅ Empty description saves as null correctly
  - ✅ Network failures show error toast (axios + onError)
  - ✅ Documented: Concurrent edits use last-write-wins (acceptable)
  - **Why:** Production readiness

- [x] **Task 8.3** - Add loading states
  - ✅ Disable form during save (already implemented)
  - ✅ Show spinner on save button (already implemented)
  - ✅ Prevent modal close during save (onClose blocked when isPending)
  - **Why:** Prevent user confusion, prevent race conditions

- [x] **Task 8.4** - Accessibility audit
  - ✅ Keyboard navigation (native + Headless UI)
  - ✅ Screen reader labels on all inputs (already implemented)
  - ✅ Focus management: auto-focus first input on open
  - ✅ ARIA attributes: aria-busy on form during save
  - ✅ Modal accessibility handled by Headless UI Dialog
  - **Why:** Professional quality, inclusive design

### Phase G: Testing & Documentation

- [ ] **Task 9.1** - Write integration tests
  - Test backend endpoint with pytest
  - Test React component with React Testing Library
  - Test full flow with Playwright/Cypress
  - **Why:** Regression prevention, confidence in changes

- [ ] **Task 9.2** - Update documentation
  - Add API endpoint to OpenAPI spec (auto-generated by FastAPI)
  - Document train config feature in user docs
  - Update architecture docs with new data flow
  - **Why:** Knowledge transfer, onboarding

- [ ] **Task 9.3** - Performance check
  - Verify no N+1 queries introduced
  - Check bundle size increase (modal component)
  - Test with 50+ trains (scale testing)
  - **Why:** Prevent performance regressions

### Phase H: Optional Enhancements (If Time Permits)

- [ ] **Task 10.1** - Add audit logging
  - Log train config changes with user/timestamp
  - Store old vs new values
  - **Why:** Compliance, debugging, rollback capability

- [ ] **Task 10.2** - Add undo/redo
  - Track previous train state
  - Allow reverting last change
  - **Why:** Better UX, mistake recovery

- [ ] **Task 10.3** - Add bulk edit
  - Select multiple trains
  - Apply same change to all
  - **Why:** Admin efficiency

---

## Recommended Start Point

**Start with Task 1.1** - Update database schema. This is the foundation everything else builds on.

**Rationale:**

1. Schema changes are hardest to fix later (require migrations)
2. Backend first ensures API contract is solid before frontend depends on it
3. Each phase validates previous phase (tight feedback loop)
4. Can demo progress after each phase (stakeholder visibility)

**Expected Flow:**

- Tasks 1-4: ~1 hour (backend complete, testable via curl)
- Tasks 5-6: ~45 min (frontend data layer, testable in console)
- Task 7: ~30 min (UI integration, demo-able)
- Tasks 8-9: ~30 min (polish, production-ready)

**Risk Mitigation:**

- Test each layer before moving to next
- Backend first means frontend can develop against stable API
- Modal component isolated = can test without full app
- Early manual testing catches issues before automated tests
