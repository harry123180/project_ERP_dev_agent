# Story: Purchase Order User Tracking Enhancement
**Story ID**: ERP-E03-S07  
**Title**: Enhanced User Tracking and Purchase Confirmation Workflow  
**Priority**: P0  
**Story Points**: 8  
**Status**: ✅ COMPLETED (2025-09-10)

## User Story
**As a** Procurement Manager  
**I want to** see who created, outputted, and confirmed each purchase order with timestamps  
**So that** I can track accountability and audit the complete lifecycle of purchase orders  

## Background & Context
The purchase order system needed enhanced visibility into user actions throughout the PO lifecycle. This includes tracking who creates POs, who outputs them for supplier communication, and who confirms the actual purchase execution. This information needs to be readily visible in the PO list with interactive details.

## Completed Features

### 1. Confirm Purchase Functionality (確認採購)
- **Status Transition**: Added ability to confirm purchase when PO status is "outputted" (已製單)
- **Button Visibility**: "確認採購" button only appears for POs with status "outputted"
- **State Changes**: 
  - PO status changes from "outputted" to "purchased"
  - All line items automatically update to "purchased" status
- **User Tracking**: Records which user confirmed the purchase with timestamp

### 2. User Information Display Columns
Added two new columns to the purchase order list:

#### 製單人 (Output Person)
- Displays the Chinese name of the user who outputted/exported the PO
- Interactive popover on hover showing:
  - Full name (chinese_name)
  - Username (username)
  - Output timestamp (output_timestamp)

#### 採購人 (Purchase Confirmer)
- Displays the Chinese name of the user who confirmed the purchase
- Interactive popover on hover showing:
  - Full name (chinese_name)
  - Username (username)
  - Confirmation timestamp (confirm_timestamp)

## Acceptance Criteria - Completed ✅

**AC1**: ✅ Purchase order list displays output person and purchase confirmer columns

**AC2**: ✅ User names are clickable/hoverable with detailed information popover

**AC3**: ✅ Popover shows username and operation timestamp

**AC4**: ✅ "Confirm Purchase" button appears only when status is "outputted"

**AC5**: ✅ Clicking "Confirm Purchase" updates PO status to "purchased"

**AC6**: ✅ All PO items synchronize status to "purchased" when PO is confirmed

**AC7**: ✅ System tracks and displays the confirming user with timestamp

## Technical Implementation

### Backend Changes
```python
# User Model Enhancement (backend/app/models/user.py)
outputted_purchase_orders = db.relationship(
    'PurchaseOrder', 
    foreign_keys='PurchaseOrder.output_person_id', 
    backref='output_person', 
    lazy='dynamic'
)

# New Endpoint (backend/app/routes/purchase_orders.py)
@bp.route('/<po_no>/confirm-purchase', methods=['POST'])
@procurement_required
def confirm_purchase_status(current_user, po_no):
    # Updates PO status to 'purchased'
    # Updates all items to 'purchased'
    # Records confirm_purchaser_id
```

### Frontend Changes
```vue
# List.vue Enhancement
- Added output_person_name column with ElPopover
- Added confirm_purchaser_name column with ElPopover
- Added confirmPurchase() method with ElMessageBox confirmation
- Added canConfirmPurchase() validation
```

### Database Schema
- Fixed SQLAlchemy relationship conflicts
- Added proper foreign key relationships for user tracking
- Ensured cascade updates for item status changes

## Test Coverage
- `test_user_columns.py` - Basic user column display validation
- `test_user_info_display.py` - Comprehensive user information display test
- `test_complete_functionality.py` - End-to-end integration test

## Business Impact
- **Accountability**: Complete audit trail of who performed each action
- **Transparency**: Clear visibility of PO lifecycle progression
- **Compliance**: Meets audit requirements for purchase authorization tracking
- **Efficiency**: Quick identification of responsible parties for follow-up

## Deployment Notes
- No database migration required (uses existing columns)
- Backward compatible with existing PO data
- CORS configuration updated to support idempotency headers

## Future Enhancements
1. Add role-based permissions for confirm purchase action
2. Implement bulk confirmation for multiple POs
3. Add email notifications on status changes
4. Create audit log for all PO state transitions
5. Add export functionality for audit reports

## Related Documentation
- [Progress Update 2025-09-10](../PROGRESS_UPDATE_20250910.md)
- [EPIC-3: Purchase Order Management](./EPIC-3-PURCHASE-ORDER-MANAGEMENT.md)

## Definition of Done ✅
- [x] Code implemented and tested
- [x] Unit tests passing
- [x] Integration tests passing
- [x] User acceptance criteria met
- [x] Documentation updated
- [x] Code reviewed and merged
- [x] Deployed to development environment