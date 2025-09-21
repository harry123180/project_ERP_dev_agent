# Critical Requisition Status Bug Fix Report

## 🚨 Bug Summary

**Issue**: Both "保存草稿" (Save as Draft) and "提交審核" (Submit for Review) buttons in the New Requisition page were creating requisitions with the same "draft" status, preventing proper workflow progression.

**Impact**: Critical business logic failure - approval workflow could not function correctly as submitted requisitions appeared as drafts.

**Status**: ✅ **RESOLVED**

## 🔍 Root Cause Analysis

### Frontend Issues (Form.vue)
1. **Missing Status Parameter**: The `CreateRequisitionRequest` interface didn't include a `status` field
2. **Incorrect Button Logic**: Both buttons used the same underlying `handleSaveDraft` method
3. **Workflow Bug**: "Submit for Review" called `handleSaveDraft` first, then tried to submit a non-existent requisition ID

### Backend Issues (requisitions.py)
1. **Missing Status Handling**: The `create_requisition` endpoint ignored any status parameter from frontend
2. **Default Status Only**: All new requisitions defaulted to 'draft' regardless of button clicked
3. **Inconsistent Item Status**: Items weren't set to correct status based on order status

## 🛠️ Fixes Implemented

### 1. Frontend Fixes (Form.vue)

#### API Type Definition Update
```typescript
export interface CreateRequisitionRequest {
  usage_type: 'daily' | 'project'
  project_id?: string
  status?: 'draft' | 'submitted'  // ✅ ADDED: Status field
  items: { ... }[]
}
```

#### Button Logic Separation
- **"保存草稿" (Save Draft)**: Sets `status: 'draft'` explicitly
- **"提交審核" (Submit for Review)**: 
  - For new requisitions: Sets `status: 'submitted'` directly
  - For existing requisitions: Updates then submits separately

### 2. Backend Fixes (requisitions.py)

#### Status Parameter Handling
```python
# CRITICAL FIX: Handle status from frontend
initial_status = data.get('status', 'draft')  # Default to draft if not specified

# Create request order with specified status
order = RequestOrder(
    request_order_no=request_order_no,
    requester_id=current_user.user_id,
    requester_name=current_user.chinese_name,
    usage_type=data['usage_type'],
    project_id=data.get('project_id'),
    order_status=initial_status  # ✅ CRITICAL FIX: Set initial status
)

# CRITICAL FIX: Set submit_date if creating directly in submitted status
if initial_status == 'submitted':
    order.submit_date = date.today()
```

#### Item Status Consistency
```python
# CRITICAL FIX: Set item status based on order status
item_status = 'pending_review' if initial_status == 'submitted' else 'draft'

item = RequestOrderItem(
    # ... other fields ...
    item_status=item_status,  # ✅ CRITICAL FIX: Set correct item status
    # ... other fields ...
)
```

## ✅ Test Results

All tests passed successfully:

| Test Case | Expected Result | Actual Result | Status |
|-----------|----------------|---------------|---------|
| Save Draft Button | `order_status: 'draft'`, `item_status: 'draft'` | ✅ Correct | PASS |
| Submit for Review Button | `order_status: 'submitted'`, `item_status: 'pending_review'` | ✅ Correct | PASS |
| Draft Verification | Status remains 'draft' | ✅ Correct | PASS |
| Submit Verification | Status is 'submitted' | ✅ Correct | PASS |

### Test Evidence
```
🎉 ALL TESTS PASSED! Bug fix successful!

The requisition status bug has been resolved:
• 'Save Draft' button creates requisitions with 'draft' status
• 'Submit for Review' button creates requisitions with 'submitted' status
```

## 📋 Status Values Confirmed

The system uses consistent status values across frontend and backend:

| Status | Chinese Display | English Value | Item Status |
|--------|----------------|---------------|-------------|
| 草稿 | Draft | `draft` | `draft` |
| 已提交 | Submitted | `submitted` | `pending_review` |
| 已審核 | Reviewed | `reviewed` | `approved`/`rejected`/`questioned` |

## 🔄 Workflow Impact

**Before Fix**:
- Both buttons → `draft` status
- Approval workflow broken
- All requisitions appeared as drafts

**After Fix**:
- "保存草稿" → `draft` status (can edit)
- "提交審核" → `submitted` status (enters approval workflow)
- Proper workflow progression enabled

## 📁 Files Modified

### Frontend Changes
- `frontend/src/views/requisitions/Form.vue` - Button logic separation
- `frontend/src/api/requisition.ts` - Added status field to interface

### Backend Changes  
- `backend/app/routes/requisitions.py` - Status parameter handling and item status consistency

## 🧪 Verification

A comprehensive test suite was created (`test_requisition_status_fix.py`) that:
1. Tests both draft and submit functionality
2. Verifies order status correctness
3. Confirms item status consistency
4. Validates end-to-end workflow

## 🚀 Business Impact

✅ **Procurement workflow now functions correctly**
✅ **Users can distinguish between drafts and submitted requests**
✅ **Approval process can proceed as designed**
✅ **Status tracking works properly throughout system**

## 📝 Recommendations

1. **Deploy immediately** - This is a critical business logic fix
2. **Monitor status transitions** in production
3. **Train users** on correct button usage (though it's now intuitive)
4. **Consider additional status validation** in future enhancements

---

**Fix Completed**: September 10, 2025  
**Test Status**: All tests passing  
**Ready for Production**: ✅ Yes  
**Risk Level**: Low (isolated fix with comprehensive testing)