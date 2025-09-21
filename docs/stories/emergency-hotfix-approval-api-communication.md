# Emergency Hotfix: Procurement Approval API Communication - Brownfield Addition

## Story Title

Procurement Approval API Communication Failure - Emergency P0 Hotfix

## User Story

As a **Procurement Manager**,
I want **my approval actions to properly save to the backend system**,
So that **requisition status transitions from "submitted" to "reviewed" are completed and the procurement workflow functions correctly**.

## Story Context

**Existing System Integration:**

- Integrates with: Vue.js frontend Review component and Flask backend requisitions API
- Technology: Vue.js 3 frontend with Element Plus UI, Flask backend with SQLAlchemy ORM
- Follows pattern: Existing API communication pattern used by approve/reject/question functions
- Touch points: Frontend Review.vue `saveChanges` function and backend `/api/requisitions/{id}/items/{item_id}/approve` endpoint

**Current Issue:**
- Frontend `saveChanges` function shows success message without making backend API call
- Backend endpoint exists and functions correctly when called directly
- Status transition logic is implemented but never triggered
- No approval_debug.log created indicating backend API never receives requests

## Acceptance Criteria

**Functional Requirements:**

1. `saveChanges` function in Review.vue must make actual API calls to backend endpoints
2. Supplier selection and unit price changes must be persisted to database via API
3. Status transition from "submitted" to "reviewed" must trigger when all items are processed

**Integration Requirements:**

4. Existing approve/reject/question functionality continues to work unchanged
5. New saveChanges functionality follows existing API communication pattern used by other review actions
6. Integration with backend requisitions API maintains current behavior for existing endpoints

**Quality Requirements:**

7. Change is covered by integration tests verifying API communication
8. Frontend error handling follows existing pattern for API failures
9. No regression in existing approval workflow functionality verified

## Technical Notes

- **Integration Approach:** Implement API calls in `saveChanges` function similar to existing `approveItem`, `rejectItem`, `questionItem` functions
- **Existing Pattern Reference:** Follow the pattern used in `approveItem` function which makes POST requests to `/api/requisitions/{id}/items/{item_id}/approve`
- **Key Constraints:** Must maintain backward compatibility with existing approval actions and not affect other workflow components

## Definition of Done

- [ ] `saveChanges` function makes appropriate API calls to persist changes
- [ ] Supplier selection changes are saved to backend database
- [ ] Unit price changes are saved to backend database  
- [ ] Status transition to "reviewed" occurs when all items are processed
- [ ] approval_debug.log file is created when backend receives API calls
- [ ] Existing approval/reject/question functionality remains unchanged
- [ ] Integration tests verify API communication works correctly
- [ ] No regression in procurement workflow verified through testing

## Risk and Compatibility Check

**Minimal Risk Assessment:**

- **Primary Risk:** Breaking existing approval workflow during API integration fix
- **Mitigation:** Follow exact same pattern as existing approve/reject functions, maintain all existing function signatures
- **Rollback:** Revert saveChanges function to current implementation (frontend-only success message)

**Compatibility Verification:**

- [ ] No breaking changes to existing APIs (using same endpoints)
- [ ] Database changes are additive only (no schema modifications required)
- [ ] UI changes follow existing design patterns (no visual changes)
- [ ] Performance impact is negligible (same API pattern as existing functions)

## Validation Checklist

**Scope Validation:**

- [ ] Story can be completed in one development session (estimated 2-3 hours)
- [ ] Integration approach is straightforward (copy existing API pattern)
- [ ] Follows existing patterns exactly (approve/reject function structure)
- [ ] No design or architecture work required (using existing APIs)

**Clarity Check:**

- [ ] Story requirements are unambiguous (fix missing API calls)
- [ ] Integration points are clearly specified (Review.vue saveChanges function)
- [ ] Success criteria are testable (API calls logged, status transitions occur)
- [ ] Rollback approach is simple (revert function implementation)

## Emergency Classification

**Priority:** P0 - Critical Production Blocking Issue
**Impact:** Complete procurement approval workflow failure
**Urgency:** Immediate - Blocking all procurement operations
**Estimated Fix Time:** 2-3 hours focused development work

This emergency hotfix addresses a critical production issue where the frontend approval workflow appears successful but fails to communicate with the backend, preventing any procurement approvals from being processed.