# Invoice Management Search Enhancement

## Issue Fixed
Users searching for September invoices for "本土供應商" (local supplier) in the accounting invoice management page were not getting results despite having valid purchase orders.

## Root Cause
The `/api/v1/accounting/invoice-management/search` endpoint only accepted `supplier_id` parameter but users were searching with supplier names like "本土供應商" (partial name).

## Solution Implemented
Enhanced the search endpoint to support both `supplier_id` and `supplier_name` parameters with backward compatibility:

### API Changes

#### Before
```
GET /api/v1/accounting/invoice-management/search?supplier_id=S001&invoice_month=2025-09
```

#### After (Backward Compatible)
```
# Original method still works
GET /api/v1/accounting/invoice-management/search?supplier_id=S001&invoice_month=2025-09

# New method with exact supplier name
GET /api/v1/accounting/invoice-management/search?supplier_name=台灣本土供應商&invoice_month=2025-09

# New method with partial supplier name (user's case)
GET /api/v1/accounting/invoice-management/search?supplier_name=本土供應商&invoice_month=2025-09
```

### Technical Implementation
1. **Enhanced Parameter Handling**: Accepts both `supplier_id` and `supplier_name` parameters
2. **Partial Matching**: Uses `ILIKE` pattern matching for both Chinese (`supplier_name_zh`) and English (`supplier_name_en`) supplier names
3. **Backward Compatibility**: Existing code using `supplier_id` continues to work unchanged
4. **Error Handling**: Returns appropriate 404 error for suppliers not found

### Code Changes
- **File**: `backend/app/routes/accounting.py`
- **Function**: `authenticate_and_process()`
- **Changes**:
  - Added `supplier_name` parameter support
  - Added supplier name lookup with partial matching
  - Updated validation logic for flexible parameter requirements

### Test Results
✅ Search by supplier_id (existing functionality)
✅ Search by full supplier name (台灣本土供應商)
✅ Search by partial supplier name (本土供應商)
✅ Error handling for invalid supplier names

### Example Response
For search with `supplier_name=本土供應商&invoice_month=2025-09`:

```json
{
  "supplier": {
    "supplier_id": "S001",
    "supplier_name_zh": "台灣本土供應商",
    "supplier_name_en": "Taiwan Local Supplier"
  },
  "purchase_orders": [
    {
      "purchase_order_no": "PO20250914001",
      "grand_total_int": 1296,
      "purchase_status": "purchased",
      "created_at": "2025-09-13T16:29:57.348808"
    },
    {
      "purchase_order_no": "PO20250911001",
      "grand_total_int": 55000,
      "purchase_status": "purchased",
      "created_at": "2025-09-10T17:23:58"
    }
  ],
  "summary": {
    "total_orders": 3,
    "total_amount": 61546
  },
  "date_range": {
    "start_date": "2025-08-27",
    "end_date": "2025-09-25",
    "due_date": "2025-10-30",
    "payment_days": 30
  }
}
```

## Impact
- ✅ Fixed user search issue - can now search by partial supplier names
- ✅ Maintains backward compatibility - existing integrations unaffected
- ✅ Improved user experience - more flexible search options
- ✅ Proper Unicode handling for Chinese supplier names

## Files Modified
- `backend/app/routes/accounting.py` - Enhanced search logic
- `test_invoice_search_fix.py` - Comprehensive test suite (new file)

## Deployment Notes
- No database migrations required
- No breaking changes to existing API contracts
- Ready for immediate deployment