# 🚨 CRITICAL BUG FIX PROJECT PLAN - ERP REQUISITION STATUS UPDATE

## Executive Summary

**CRITICAL BUG**: Requisition status NOT updating from "已提交" (submitted) to "已審核" (reviewed) after all items are approved through the UI.

**SEVERITY**: CRITICAL - CEO is watching, CANNOT FAIL
**TIMELINE**: IMMEDIATE - Must be resolved within 24 hours
**IMPACT**: Business process broken, approvals not reflecting in system

---

## Root Cause Analysis Framework

### Primary Issue Identified
Based on comprehensive codebase analysis, I've identified the core problem:

**The frontend UI emits an 'updated' event after item approval, but this event only triggers a local UI refresh without fetching the latest requisition status from the backend API.**

### Technical Root Causes

1. **Frontend State Synchronization Issue**:
   - In `frontend/src/views/requisitions/Review.vue`, lines 288-291 and 462-465 emit 'updated' events after item approvals
   - However, the parent component (`List.vue`) only closes the dialog and refetches the list without ensuring the status has been updated on the backend
   - The UI shows old cached status data

2. **Backend Transaction Timing**:
   - Backend properly updates status in `backend/app/models/request_order.py` lines 97-108 in `update_status_after_review()`
   - API endpoints flush and commit correctly (lines 332-346 in requisitions.py)
   - BUT there may be a timing issue where the frontend requests status before backend commit is complete

3. **Store State Management Gap**:
   - `frontend/src/stores/requisition.ts` lines 154-171 refresh requisition after approval
   - But `fetchRequisitionDetail()` might be called before database transaction completes

---

## Development Tasks with Specific Code Areas

### Task 1: Fix Frontend State Synchronization (DEV TEAM)
**Priority: CRITICAL**
**Estimated Time: 2-3 hours**

#### 1.1 Fix Review Component Event Handling
- **File**: `frontend/src/views/requisitions/Review.vue`
- **Lines**: 288-291, 462-465
- **Action**: Ensure 'updated' event includes forced refresh flag
- **Verification**: Status updates immediately after approval

#### 1.2 Fix Store State Management
- **File**: `frontend/src/stores/requisition.ts`
- **Lines**: 154-171
- **Action**: Add retry mechanism and polling for status changes
- **Verification**: Store correctly reflects backend status

#### 1.3 Fix List Component Refresh Logic
- **File**: `frontend/src/views/requisitions/List.vue`
- **Lines**: 271-275
- **Action**: Add status validation after update
- **Verification**: List shows correct status immediately

### Task 2: Backend Robustness Enhancement (DEV TEAM)
**Priority: HIGH**
**Estimated Time: 1-2 hours**

#### 2.1 Add Status Update Logging
- **File**: `backend/app/models/request_order.py`
- **Lines**: 78-108
- **Action**: Enhanced logging for status transitions
- **Verification**: Clear audit trail of status changes

#### 2.2 API Response Enhancement
- **File**: `backend/app/routes/requisitions.py`
- **Lines**: 327-357
- **Action**: Return updated requisition status in approval response
- **Verification**: Frontend gets latest status in API response

---

## Testing Strategy with Playwright MCP Validation

### Phase 1: Automated UI Testing (QA ASSISTANT)
**Priority: CRITICAL**
**Estimated Time: 2-3 hours**

#### Test Scenario 1: Single Item Approval
1. Navigate to requisitions list
2. Find requisition with status "已提交"
3. Open requisition for review
4. Approve single item with supplier and price
5. Verify status changes to "已審核" in UI
6. Close review dialog
7. Verify status shows "已審核" in list
8. Refresh page and verify status persists

#### Test Scenario 2: Multi-Item Batch Approval
1. Open requisition with multiple items
2. Select all items
3. Use batch approval functionality
4. Verify all items show "approved" status
5. Verify requisition status changes to "已審核"
6. Navigate back to list and verify status

#### Test Scenario 3: Mixed Actions Status Update
1. Open requisition with 3+ items
2. Approve 2 items
3. Reject 1 item
4. Question remaining items
5. Verify status updates to "已審核" when all items processed

### Phase 2: API Integration Testing (QA TEAM)
**Priority: HIGH**
**Estimated Time: 1-2 hours**

#### API Test Cases:
1. Direct API calls to approve items
2. Verify database status updates
3. Test concurrent approval scenarios
4. Validate status consistency across API endpoints

---

## Success Criteria and Acceptance Testing

### Primary Success Metrics

1. **Functional Requirement**: 
   - ✅ Status MUST change from "已提交" to "已審核" when last item approved
   - ✅ Change must be visible immediately in UI (no refresh required)
   - ✅ Change must persist after page refresh
   - ✅ Must work through UI interaction (no API cheating)

2. **Performance Requirement**:
   - ✅ Status update must complete within 2 seconds of approval
   - ✅ UI must reflect change within 1 second

3. **Reliability Requirement**:
   - ✅ Must work 100% of the time across different browsers
   - ✅ Must work with concurrent users
   - ✅ Must handle network delays gracefully

### Acceptance Testing Framework

#### Browser Compatibility Testing:
- Chrome (latest)
- Firefox (latest) 
- Edge (latest)
- Mobile browsers (Chrome Mobile, Safari Mobile)

#### User Scenario Testing:
- Single approver workflow
- Multiple approvers working simultaneously
- Network interruption scenarios
- Large requisitions (50+ items)

---

## Team Task Assignments

### Dev Team (dev-agent-bmad) - LEAD DEVELOPER
**Timeline: 4-6 hours**
**Responsibilities:**

1. **Frontend State Fix** (2-3 hours)
   - Fix Review.vue event emission
   - Update requisition store refresh logic
   - Implement status polling mechanism
   - Add loading states for status transitions

2. **Backend Logging Enhancement** (1-2 hours)
   - Add comprehensive status update logging
   - Enhance API responses with status data
   - Add status validation endpoints

3. **Integration Testing Support** (1 hour)
   - Create test requisitions with known states
   - Provide debug endpoints for testing
   - Support QA team with technical issues

### QA Team (qa-test-architect) - TEST STRATEGY LEAD
**Timeline: 3-4 hours**
**Responsibilities:**

1. **Test Case Design** (1-2 hours)
   - Create comprehensive test scenarios
   - Define edge cases and error conditions
   - Design performance benchmarks
   - Create acceptance criteria checklist

2. **Test Environment Setup** (1 hour)
   - Configure test data
   - Set up monitoring and logging
   - Prepare test user accounts

3. **Manual Validation** (1-2 hours)
   - Execute critical path testing
   - Validate business process flow
   - Document any issues found
   - Sign-off on acceptance criteria

### QA Assistant (qa-mcp-assistant) - AUTOMATED TEST EXECUTION
**Timeline: 4-5 hours**
**Responsibilities:**

1. **Playwright MCP Test Development** (2-3 hours)
   - Implement automated UI test scenarios
   - Create browser interaction scripts
   - Add screenshot capture for evidence
   - Implement retry logic for flaky tests

2. **Test Execution** (1-2 hours)
   - Run comprehensive test suites
   - Document all test results
   - Capture evidence of success/failure
   - Generate detailed test reports

3. **Regression Testing** (1 hour)
   - Verify existing functionality not broken
   - Test related workflows (creation, submission)
   - Validate permission controls still work

---

## Risk Mitigation Plan

### High-Risk Areas
1. **Concurrent User Conflicts**: Multiple users approving same requisition
2. **Database Transaction Issues**: Partial commits or rollbacks
3. **Network Latency**: Slow API responses affecting UI state
4. **Browser Caching**: Old status data cached in browser

### Mitigation Strategies
1. **Database-level locking** for status updates
2. **Optimistic concurrency control** with version checking  
3. **Retry mechanisms** for failed API calls
4. **Cache invalidation** strategies in frontend

---

## Escalation Protocol

### Level 1: Technical Issues (0-2 hours)
- Dev team self-resolves
- QA provides immediate feedback
- PM monitors progress

### Level 2: Cross-team Dependencies (2-4 hours)
- PM coordinates between teams
- Technical lead provides guidance
- Emergency debugging session

### Level 3: Critical Blocker (4+ hours)
- Executive escalation
- All-hands debugging
- External consultant if needed

---

## Verification Checklist

Before marking this bug as RESOLVED, ALL items must be checked:

- [ ] Single item approval updates status to "已審核" immediately
- [ ] Batch approval updates status to "已審核" immediately
- [ ] Mixed approval/rejection/question updates status correctly
- [ ] Status persists after page refresh
- [ ] Status shows correctly in list view
- [ ] Works across all supported browsers
- [ ] Performance meets 2-second requirement
- [ ] Automated tests pass 100% of runs (minimum 10 runs)
- [ ] Manual testing confirms business process works
- [ ] No regression in existing functionality
- [ ] CEO demo-ready functionality verified

---

## Communication Plan

### Hourly Updates Required:
- Dev team progress updates
- QA test execution status
- Any blockers or issues encountered

### Final Deliverables:
1. Working bug fix deployed
2. Automated test suite covering bug scenario
3. Documentation of root cause and fix
4. CEO demo readiness confirmation

---

**Remember: This is CRITICAL. The CEO is watching. We CANNOT FAIL.**

**Next Steps**: 
1. Dev team immediately starts on frontend state fixes
2. QA Assistant begins test scenario development
3. QA Team prepares test environment and criteria
4. PM monitors hourly progress and removes blockers

**Expected Resolution**: Within 24 hours with full validation complete.