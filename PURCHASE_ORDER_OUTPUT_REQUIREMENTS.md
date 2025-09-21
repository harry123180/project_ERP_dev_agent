# Purchase Order Output Requirements Analysis

## Current System Status Analysis

### Purchase Order Status Enum Values (from backend/app/models/purchase_order.py)
The current system has the following purchase order statuses:
- `pending` - Initial state
- `order_created` - Purchase order has been created but not confirmed (已製單)
- `confirmed` - Purchase order has been confirmed by procurement personnel
- `purchased` - Purchase order has been sent to supplier and confirmed (已採購)

### Current Data Model Fields
The PurchaseOrder model includes all necessary fields for document generation:
- **Header Information**: purchase_order_no, supplier details, order_date, quotation_no
- **Contact Information**: supplier_name, supplier_address, contact_phone, contact_person, supplier_tax_id
- **Financial Calculations**: subtotal_int, tax_decimal1, grand_total_int
- **Logistics**: delivery_address, notes
- **Tracking**: creator_id, output_person_id, confirm_purchaser_id
- **Line Items**: via PurchaseOrderItem relationship with item details, quantities, prices

## New Requirements Analysis

### 1. Purchase Order Output Functionality

#### 1.1 "輸出採購單" (Output Purchase Order) Button
**Location**: Purchase Order List Page
**Functionality**: 
- Add "輸出採購單" button to each purchase order row in the list
- Only available for purchase orders with status `order_created` or `confirmed`
- Clicking opens a preview modal/dialog

#### 1.2 Purchase Order Preview
**Purpose**: Allow users to review the purchase order before outputting
**Content**: 
- Complete purchase order document matching the PDF template format
- Real-time calculation display
- All supplier and item information populated

#### 1.3 Output Format Options
**Two Options Required**:
1. **Excel Output**: Generate .xlsx file using the template structure
2. **PDF Output**: Generate .pdf file matching the provided template design

#### 1.4 Status Change After Output
**Behavior**: 
- After successful output (Excel or PDF), change purchase order status to `order_created` (已製單)
- Record the `output_person_id` as the current user
- Update timestamp for tracking

### 2. Purchase Order Status Confirmation Feature

#### 2.1 New Navigation Menu Item
**Menu Item**: "確認採購狀態" (Confirm Purchase Status)
**Purpose**: Dedicated page for confirming purchase orders that have been output

#### 2.2 Purchase Order Status List
**Display Criteria**: Show all purchase orders with status `order_created` (已製單)
**Columns**:
- Purchase Order Number
- Supplier Name
- Creation Date
- Output Date
- Output Person
- Total Amount
- Status
- Action (Confirm Button)

#### 2.3 Purchase Status Confirmation
**Action**: "確認採購" (Confirm Purchase) button
**Functionality**:
- Change status from `order_created` to `purchased` (已採購)
- Record `confirm_purchaser_id` as current user
- Record confirmation timestamp
- Update all related PurchaseOrderItem statuses to `purchased`

### 3. Purchase Order Template Structure

Based on the PDF template analysis, the purchase order should include:

#### 3.1 Header Section
- Company Logo (百兆豐國際有限公司)
- Document Title: "採購單"
- Supplier Information Block:
  - 廠商名稱 (Supplier Name)
  - 廠商編號 (Supplier ID)  
  - 廠商地址 (Supplier Address)
  - 連絡電話 (Contact Phone)
  - 聯絡人 (Contact Person)
- Order Information Block:
  - 訂購日期 (Order Date)
  - 報價單號 (Quotation Number)
  - 採購單號 (Purchase Order Number)

#### 3.2 Items Table
- 項目 (Item Number)
- 產品型號 (Product Model)
- 名稱 (Name)
- 規格 (Specification)
- 數量 (Quantity)
- 單位 (Unit)
- 單價 (Unit Price)
- 金額 (Amount)

#### 3.3 Financial Summary
- 未稅金額(NTD) (Subtotal before tax)
- 稅金5% (5% Tax)
- 合計 (Total with tax)

#### 3.4 Terms and Conditions
- Standard procurement terms
- Delivery address
- Invoice requirements
- Signature area with date

### 4. Financial Calculation Rules

Based on the procurement workflow document:
- **Quantity**: Must be positive integer
- **Unit Price**: Must be positive, allows decimals
- **Line Subtotal** = Quantity × Unit Price (rounded to integer)
- **Total (Pre-tax)** = Sum of line subtotals (positive integer)
- **Tax Amount** = Total × Tax Rate (5%) (1 decimal place)
- **Grand Total** = Total + Tax Amount (rounded to positive integer)

## User Stories and Acceptance Criteria

### User Story 1: Output Purchase Order
**As a** procurement personnel
**I want to** output purchase orders in Excel or PDF format
**So that** I can send them to suppliers

**Acceptance Criteria**:
- [ ] "輸出採購單" button appears on purchase order list for eligible orders
- [ ] Clicking opens preview modal showing complete purchase order
- [ ] User can choose between Excel and PDF output formats
- [ ] Generated documents match template format exactly
- [ ] After output, purchase order status changes to "已製單"
- [ ] System records who performed the output and when

### User Story 2: Confirm Purchase Status
**As a** procurement manager  
**I want to** review and confirm purchase orders that have been output
**So that** I can track which orders have been officially sent to suppliers

**Acceptance Criteria**:
- [ ] New menu item "確認採購狀態" appears in navigation
- [ ] Page shows all purchase orders with "已製單" status
- [ ] Each order has a "確認採購" button
- [ ] Clicking confirmation changes status to "已採購"
- [ ] System records who confirmed and when
- [ ] All related line items also update to "已採購" status

### User Story 3: Purchase Order Template Compliance
**As a** business user
**I want** generated purchase orders to match our standard template
**So that** suppliers receive consistent, professional documentation

**Acceptance Criteria**:
- [ ] Excel output matches template structure in docs/最終修正版採購單.xlsx
- [ ] PDF output matches template design in docs/採購單_模板1_測試.pdf
- [ ] All required fields are populated correctly
- [ ] Financial calculations follow business rules exactly
- [ ] Company branding and legal terms are included

## Technical Considerations

### Backend Changes Required
1. **New API Endpoints**:
   - `GET /api/v1/po/<po_no>/preview` - Get formatted data for preview
   - `POST /api/v1/po/<po_no>/output` - Generate and download file
   - `GET /api/v1/po/pending-confirmation` - Get orders awaiting confirmation
   - `POST /api/v1/po/<po_no>/confirm-purchase` - Confirm purchase status

2. **File Generation Libraries**:
   - Excel: openpyxl or xlsxwriter for .xlsx generation
   - PDF: reportlab or weasyprint for .pdf generation

3. **Template Storage**:
   - Store template files in backend/templates/ directory
   - Implement template rendering with dynamic data

### Frontend Changes Required
1. **Purchase Order List Enhancements**:
   - Add "輸出採購單" button with proper permissions
   - Implement preview modal/dialog component

2. **New Page: Purchase Status Confirmation**:
   - Create new Vue component for confirmation list
   - Add routing and navigation menu item
   - Implement confirmation workflow

3. **File Download Handling**:
   - Handle file download responses from API
   - Provide user feedback for generation progress

### Database Schema Updates
- No schema changes required - existing fields support all functionality
- `output_person_id` already exists for tracking
- Status enum already includes required values

### Security and Permissions
- Maintain existing procurement_required decorator
- Add audit trail for all status changes
- Validate user permissions before allowing confirmations

## Implementation Priority
1. **Phase 1**: Backend API endpoints for preview and output
2. **Phase 2**: File generation functionality (Excel and PDF)
3. **Phase 3**: Frontend preview modal and output buttons
4. **Phase 4**: Purchase confirmation page and workflow
5. **Phase 5**: Testing and template refinement

## Handoff Summary for UI/UX Designer and Developer

### Design Requirements
1. **Purchase Order Preview Modal**: Design a modal that displays the purchase order in a format similar to the final output, allowing users to review before generating
2. **Output Format Selection**: Design interface for users to choose between Excel and PDF output options
3. **Confirmation Page Layout**: Create a clean list view for purchase orders awaiting confirmation with clear action buttons
4. **Status Indicators**: Design visual indicators for different purchase order statuses throughout the system

### Development Requirements
1. **File Generation Backend**: Implement Excel and PDF generation using templates
2. **Preview API**: Create endpoint to format purchase order data for preview display
3. **Confirmation Workflow**: Build the purchase status confirmation feature with proper state management
4. **Template Integration**: Integrate the provided Excel and PDF templates into the generation process
5. **Status Management**: Ensure proper status transitions and user tracking throughout the workflow

This requirements analysis provides a complete foundation for implementing the purchase order output functionality while maintaining consistency with the existing ERP system architecture.