# 🚨 CRITICAL BUG REPORT: Requisition Submission Failure

**Date:** 2025-09-09  
**Reporter:** Claude QA Automation  
**Severity:** HIGH  
**Priority:** CRITICAL  

## 🔍 Executive Summary

A critical bug has been identified in the ERP system's requisition workflow. When users attempt to submit a requisition for review, the system appears to confirm successful submission but **fails to change the requisition status from 'draft' to 'submitted'**. This prevents the entire approval workflow from functioning.

## 🧪 Test Scenario Executed

### Test Steps:
1. ✅ Login as system administrator (admin/admin123)
2. ✅ Navigate to requisition management 
3. ✅ Create new requisition with test data:
   - Item: "測試商品A"
   - Specification: "測試規格說明"  
   - Quantity: 2
   - Usage: "測試用途說明"
4. ✅ Click "提交審核" (Submit for Review)
5. ✅ Confirm submission in dialog with "確定提交"
6. ❌ **FAILED:** Status remains "草稿" (Draft) instead of changing to "已提交" (Submitted)

## 🐛 Bug Details

### Primary Issue:
**Requisition REQ20250909059 remains in 'draft' status after confirmed submission**

### Expected Behavior:
- After clicking "提交審核" and confirming with "確定提交"
- Requisition status should change from "草稿" (Draft) to "已提交" (Submitted) or "待審核" (Pending Review)
- Requisition should appear in review queue for administrators

### Actual Behavior:  
- System displays success confirmation messages
- Requisition REQ20250909059 created successfully in database
- **Status remains "草稿" (Draft)**
- No status transition occurs
- Review workflow cannot proceed

### Evidence:
- **Frontend UI:** Requisition list shows REQ20250909059 with "草稿" status
- **Backend Logs:** Shows successful INSERT but no status UPDATE operations
- **Database State:** Requisition exists with order_status='draft'

## 🔧 Technical Analysis

### Backend Investigation:
From backend logs, the system successfully:
```sql
INSERT INTO request_orders (request_order_no, requester_id, requester_name, usage_type, project_id, submit_date, order_status, created_at, updated_at) 
VALUES ('REQ20250909059', 1, '系統管理員', 'daily', None, '2025-09-09', 'draft', ...)
```

### Missing Operation:
No evidence of status update API call after submission confirmation:
```sql
-- EXPECTED BUT MISSING:
UPDATE request_orders SET order_status='submitted' WHERE request_order_no='REQ20250909059'
```

### Root Cause Hypothesis:
1. **Frontend Issue:** Submit confirmation dialog may not trigger proper API call for status update
2. **Backend Issue:** Submit API endpoint may be missing or not updating status field
3. **API Integration:** Frontend may be calling wrong endpoint or passing incorrect parameters

## 🚨 Console Errors Captured

### Element Plus Validation Errors (Secondary Issues):
- **56+ instances** of `Invalid prop: validation failed for prop "type"` on ElTag components
- **6+ instances** of `Invalid prop: validation failed for prop "size"` on ElTimelineItem components  
- **1 instance** of `Property "Truck" was accessed during render but is not defined`
- **1 instance** of `onUnmounted lifecycle warning`

### Impact of Console Errors:
- UI rendering warnings (non-blocking)
- Component prop validation failures
- Potential performance impact from repeated warnings

## 📊 Impact Assessment

### Business Impact:
- **CRITICAL:** Complete requisition approval workflow is broken
- **BLOCKING:** No requisitions can be submitted for review
- **WORKFLOW:** Approval process cannot function
- **USER EXPERIENCE:** Confusing behavior - appears to work but doesn't

### Affected Components:
- ✅ Requisition Creation: WORKING
- ❌ Requisition Submission: BROKEN  
- ❌ Requisition Review: CANNOT TEST (blocked by submission)
- ❌ Requisition Approval: CANNOT TEST (blocked by submission)

## 🔨 Recommended Development Actions

### Priority 1 (CRITICAL):
1. **Investigate Submit API Endpoint**
   - Verify `/api/v1/requisitions/{id}/submit` or similar endpoint exists
   - Ensure it updates `order_status` from 'draft' to 'submitted'
   - Check if frontend is calling correct API after confirmation dialog

2. **Frontend Review**
   - Examine submission confirmation dialog handler
   - Verify API call is made after "確定提交" click
   - Check for error handling in submission process

3. **Database Schema Validation** 
   - Confirm `order_status` field accepts 'submitted' value
   - Verify any constraints or triggers on status updates

### Priority 2 (HIGH):
4. **Fix Element Plus Prop Validation**
   - StatusTag component: Fix empty string type prop on ElTag
   - Timeline components: Fix "small" size prop (should be "normal" or "large")
   - Dashboard: Define missing "Truck" property

### Priority 3 (MEDIUM):
5. **Add Comprehensive Testing**
   - Unit tests for submission API endpoints
   - Integration tests for complete workflow
   - UI tests for status transitions

## 🧑‍💻 Developer Investigation Guide

### Files to Investigate:
1. **Frontend Submission Logic:**
   - Look for requisition form submission handlers
   - Search for "提交審核" button click handlers
   - Examine API service calls for requisition operations

2. **Backend API Endpoints:**
   - Check Flask routes for requisition submission
   - Verify status update logic in requisition models
   - Review any validation or business rules

3. **Database Model:**
   - Examine request_orders table schema
   - Check for status field constraints
   - Verify any triggers or stored procedures

### Debugging Steps:
1. Add logging to submission confirmation handler
2. Monitor network requests during submission process
3. Add debug logging to backend status update operations
4. Test with direct API calls to isolate issue

## ⏰ Timeline Expectations

- **Immediate:** Acknowledge and assign to development team
- **Within 2 hours:** Initial investigation and root cause identification  
- **Within 4 hours:** Fix implementation and testing
- **Within 6 hours:** Deployment to staging for validation
- **Within 8 hours:** Production deployment after QA sign-off

## 📞 Contact Information

**QA Reporter:** Claude Automation System  
**Test Environment:** Local Development (localhost:5174)  
**Test Data:** REQ20250909059  
**Timestamp:** 2025-09-09 10:59 AM  

---
*This report was generated by automated QA testing using Playwright MCP browser automation.*