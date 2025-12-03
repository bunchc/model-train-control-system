# Train Configuration Implementation Plan

**Feature**: Train-specific configuration page with gear icon and direction inversion

## Research Summary

From exploration, found:

1. **Frontend Structure**: React/TypeScript with existing Modal component, using Heroicons for icons
2. **API Endpoints**:
   - No existing train update endpoints - need to create new ones
   - Train assignment via `POST /api/controllers/{controller_uuid}/trains`
   - Train retrieval via `GET /api/trains` and individual controller endpoints
3. **Train Schema**: Has `name`, `description`, `plugin` fields - needs extension for inversion config
4. **Hardware**: `adafruit_dcmotor_hat` plugin supports direction control (1=forward, 0=reverse)
5. **Current Page**: `TrainDetail.tsx` displays train info with name in header - perfect location for gear icon

## Implementation Plan

### Phase 1: Backend API Extensions

1. **Extend Train Schema** (`central_api/app/models/schemas.py`)
   - Add optional `invert_directions: bool = False` field to `Train` model
   - Add `TrainUpdateRequest` model for configuration updates

2. **Create Train Update Endpoints** (`central_api/app/routers/trains.py`)
   - `PUT /api/trains/{train_id}` - Update train name, description, and invert flag
   - Return updated train object, invalidate cache

3. **Update Config Manager** (`central_api/app/services/config_manager.py`)
   - Add `update_train()` method to handle train configuration updates
   - Update database schema to store invert_directions flag

4. **Database Migration**
   - Add `invert_directions` column to trains table (default: false)

### Phase 2: Frontend Configuration Modal

1. **Create TrainConfigModal Component** (`frontend/web/src/components/trains/TrainConfigModal.tsx`)
   - Modal with train name/description text inputs
   - Conditional "Invert Directions" toggle (only for `adafruit_dcmotor_hat` plugin)
   - Read-only fields showing plugin details, train ID, etc.
   - Save/Cancel buttons

2. **Add API Client Functions** (`frontend/web/src/api/endpoints/trains.ts`)
   - `updateTrain(trainId, updateData)` function
   - Add `UseUpdateTrain` hook in `queries.ts`

3. **Update TrainDetail Page** (`frontend/web/src/pages/TrainDetail.tsx`)
   - Add gear icon (CogIcon from Heroicons) next to train name
   - Add modal state management
   - Wire up gear icon click to open modal

4. **Update TypeScript Types** (`frontend/web/src/api/types.ts`)
   - Add `invert_directions?: boolean` to `Train` interface
   - Add `TrainUpdateRequest` interface

### Phase 3: Direction Logic Implementation

1. **Frontend Direction Inversion**
   - Update `ControlPanel` component to check train's `invert_directions` flag
   - When sending commands:
     - If `invert_directions = true`: "Forward" UI button → "BACKWARD" API command
     - If `invert_directions = false`: "Forward" UI button → "FORWARD" API command

2. **API Command Translation** (if needed)
   - Verify current command structure in train command endpoints
   - Ensure direction inversion happens at UI level, not API level

### Phase 4: Controller Restart Logic

1. **Train Config Change Detection**
   - When train config is updated, determine if edge controller restart is needed
   - Changes requiring restart: `invert_directions`, `plugin.config` changes
   - Changes NOT requiring restart: `name`, `description`

2. **Controller Restart Endpoint**
   - Add endpoint to trigger container restart for specific controller/train
   - Use existing Ansible/Docker management to restart edge controller containers

### Phase 5: UI Polish & Error Handling

1. **Form Validation**
   - Required field validation for name
   - Character limits and sanitization
   - Real-time validation feedback

2. **Loading States**
   - Show loading spinner during save operations
   - Disable form during API calls

3. **Error Handling**
   - Display API error messages
   - Retry mechanisms for failed saves
   - Rollback UI state on errors

## Key Implementation Details

- **Icon Placement**: Gear icon positioned to the far right of train name in page header
- **Conditional Toggle**: "Invert Directions" only shown for `adafruit_dcmotor_hat` plugin
- **Direction Logic**: Inversion happens at UI level - when toggle is ON, Forward button sends BACKWARD command
- **Database Changes**: New `invert_directions` boolean column with default false
- **Restart Logic**: Only restart controller when hardware-related configs change

## File Structure Preview

```
frontend/web/src/components/trains/TrainConfigModal.tsx          # New modal component
central_api/app/models/schemas.py                                # Extended Train model  
central_api/app/routers/trains.py                               # New PUT endpoint
central_api/app/services/config_manager.py                      # Update train method
frontend/web/src/api/endpoints/trains.ts                        # Update API client
frontend/web/src/pages/TrainDetail.tsx                          # Add gear icon
```

## Current Direction Button Investigation

**ISSUE IDENTIFIED**: Direction buttons in control panel do NOT send actual direction commands.

**Analysis**:

1. **Frontend Direction Flow**:
   - ControlPanel has Forward/Reverse buttons that set local `direction` state ('forward'/'reverse')
   - When "Apply Configuration" is clicked, it sends: `{ action: direction, direction }`
   - This means: `{ action: "forward", direction: "forward" }` or `{ action: "reverse", direction: "reverse" }`

2. **Backend Command Processing**:
   - Edge controller in `main.py` does NOT handle `action: "forward"` or `action: "reverse"`
   - Supported actions: "start", "stop", "emergencyStop", "setSpeed", "setDirection"
   - Unknown actions (like "forward"/"reverse") are logged as warnings and ignored

3. **Correct Direction Commands**:
   - Use `action: "setDirection"` with `direction: "FORWARD"/"BACKWARD"`
   - Or include direction with other commands like `action: "setSpeed", speed: 50, direction: "FORWARD"`

**ROOT CAUSE**: Frontend is sending `action: "forward"` but backend expects `action: "setDirection"`

**IMMEDIATE FIX NEEDED**: Update ControlPanel.tsx to send proper direction commands:

```typescript
// WRONG (current):
{ action: direction, direction }  // sends { action: "forward", direction: "forward" }

// CORRECT (should be):
{ action: "setDirection", direction: direction.toUpperCase() }  // sends { action: "setDirection", direction: "FORWARD" }
```

This provides a complete train configuration system with proper direction inversion for the Adafruit DC Motor HAT while maintaining clean separation between UI logic and hardware control.
