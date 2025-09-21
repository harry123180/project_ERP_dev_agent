# Purchase Order Export Feature - Product Requirements Document

## Document Information
- **Version**: 1.0
- **Created**: 2025-09-10
- **Last Updated**: 2025-09-10
- **Status**: Draft
- **Author**: Product Management Team
- **Reviewers**: Development Team, UX Team, QA Team

---

## 1. Executive Summary

The Purchase Order Export Feature is a critical component of our ERP system that enables procurement staff to generate properly formatted purchase orders for supplier delivery. The current implementation has significant usability and technical issues that prevent users from successfully printing purchase orders to A4 paper format and managing order status transitions correctly.

This PRD defines the requirements to fix critical print layout issues, implement proper status transition logic, and establish a foundation for comprehensive export capabilities that will improve procurement workflow efficiency and compliance.

### Key Business Value
- Enables proper purchase order delivery to suppliers via print format
- Ensures accurate status tracking throughout the procurement lifecycle  
- Reduces manual intervention and errors in PO management
- Provides audit trail for exported purchase orders

---

## 2. Problem Statement

### Current Pain Points

#### 2.1 Print Layout Issues (Critical)
- **Layout Distortion**: Print preview differs significantly from actual A4 paper output
- **Content Scaling**: Text sizes and proportions are inconsistent when printing
- **Layout Misalignment**: Elements don't fit properly on A4 paper dimensions
- **Unusable Output**: Printed purchase orders are not suitable for supplier delivery

#### 2.2 Status Transition Logic Issues (Critical)
- **Inconsistent Rules**: Current logic only updates status from 'pending' to 'order_created'
- **Missing Workflow**: POs with status '已建立' (order_created) cannot be exported again
- **Status Gap**: No proper transition from 'order_created' to '已製單' (outputted) 
- **Data Persistence**: Status changes are not properly tracked or auditable

#### 2.3 Export Operation Issues (Medium Priority)
- **Mock Implementation**: PDF and Excel exports are placeholder functionality
- **Limited Formats**: No customization options for different export needs
- **No Validation**: No checks for export eligibility or data completeness

---

## 3. User Stories

### 3.1 Primary User: Procurement Staff

**As a procurement staff member, I want to:**

#### Story 1: Print Purchase Orders Successfully
- **I want to** print purchase orders that display correctly on A4 paper
- **So that** I can deliver professional, readable purchase orders to suppliers
- **Acceptance Criteria:**
  - Print output matches the on-screen preview
  - All content fits properly within A4 paper margins
  - Text is readable and properly sized
  - Layout maintains professional appearance

#### Story 2: Export Purchase Orders with Correct Status
- **I want to** export POs with status "已建立" or "已製單" without errors
- **So that** I can re-export orders when needed for supplier delivery
- **Acceptance Criteria:**
  - Can export POs with status "order_created" (已建立)
  - Can export POs with status "outputted" (已製單)
  - Export operation updates status appropriately
  - Status history is maintained for audit purposes

#### Story 3: Automatic Status Transition
- **I want** POs to automatically transition from "已建立" to "已製單" when exported
- **So that** I can track which orders have been sent to suppliers
- **Acceptance Criteria:**
  - Export operation updates "order_created" status to "outputted"
  - Status change is persisted in the database
  - Export person ID is recorded for audit trail
  - Timestamp of export is recorded

### 3.2 Secondary User: Finance/Audit Team

**As a finance/audit staff member, I want to:**

#### Story 4: Track Export History
- **I want to** see who exported each purchase order and when
- **So that** I can maintain proper audit trails for procurement activities
- **Acceptance Criteria:**
  - Export actions are logged with user ID and timestamp
  - Status change history is available
  - Export format and destination are tracked

---

## 4. Functional Requirements

### 4.1 Status Transition Rules

#### 4.1.1 Export Eligibility
- **REQ-001**: System SHALL allow export for POs with status "order_created" (已建立)
- **REQ-002**: System SHALL allow export for POs with status "outputted" (已製單)  
- **REQ-003**: System SHALL prevent export for POs with other statuses
- **REQ-004**: System SHALL validate PO completeness before allowing export

#### 4.1.2 Status Updates
- **REQ-005**: System SHALL update status from "order_created" to "outputted" on first export
- **REQ-006**: System SHALL maintain "outputted" status on subsequent exports
- **REQ-007**: System SHALL record export_person_id and export_timestamp
- **REQ-008**: System SHALL preserve all existing status transition rules

### 4.2 Print Layout Specifications

#### 4.2.1 A4 Paper Layout Requirements
- **REQ-009**: Print output SHALL fit within A4 paper dimensions (210mm x 297mm)
- **REQ-010**: System SHALL apply proper margins (top: 25mm, bottom: 25mm, left: 20mm, right: 20mm)
- **REQ-011**: Print layout SHALL match on-screen preview exactly
- **REQ-012**: Text SHALL be readable with minimum 10pt font size

#### 4.2.2 Content Layout Specifications
- **REQ-013**: Company header SHALL occupy maximum 80mm height
- **REQ-014**: Supplier information table SHALL use responsive column widths
- **REQ-015**: Items table SHALL handle page breaks properly
- **REQ-016**: Totals section SHALL align consistently on the right
- **REQ-017**: Signature section SHALL provide adequate space for signatures

#### 4.2.3 CSS Print Media Requirements
- **REQ-018**: System SHALL implement CSS @media print rules
- **REQ-019**: Non-printable sections SHALL be hidden in print mode
- **REQ-020**: Print-specific styling SHALL override screen styles
- **REQ-021**: Page break rules SHALL prevent content splitting inappropriately

### 4.3 Export Format Support

#### 4.3.1 Print Export (Priority 1)
- **REQ-022**: System SHALL provide browser print functionality
- **REQ-023**: Print dialog SHALL use system default printer settings
- **REQ-024**: Print preview SHALL accurately reflect final output

#### 4.3.2 PDF Export (Priority 2)
- **REQ-025**: System SHALL generate PDF with identical layout to print version
- **REQ-026**: PDF SHALL maintain vector graphics and searchable text
- **REQ-027**: PDF filename SHALL follow naming convention: PO_[PO_NUMBER]_[DATE].pdf

#### 4.3.3 Excel Export (Priority 2)
- **REQ-028**: System SHALL generate Excel with structured data layout
- **REQ-029**: Excel SHALL maintain data types and formatting
- **REQ-030**: Excel filename SHALL follow naming convention: PO_[PO_NUMBER]_[DATE].xlsx

---

## 5. Technical Requirements

### 5.1 Frontend Requirements

#### 5.1.1 CSS Print Media Queries
- **TECH-001**: Implement @media print styles for A4 paper format
- **TECH-002**: Set proper page size and margins in CSS
- **TECH-003**: Hide non-printable elements (.non-printable-section)
- **TECH-004**: Adjust font sizes and line heights for print readability
- **TECH-005**: Implement proper page-break rules for multi-page POs

#### 5.1.2 Vue.js Component Updates
- **TECH-006**: Update PreviewModal.vue with print-optimized CSS
- **TECH-007**: Implement export status validation in frontend
- **TECH-008**: Add loading states for export operations
- **TECH-009**: Implement error handling for failed exports

### 5.2 Backend Requirements

#### 5.2.1 Status Transition Logic
- **TECH-010**: Update export endpoint to handle both "order_created" and "outputted" statuses
- **TECH-011**: Implement status transition logic in POGenerator service
- **TECH-012**: Add database fields for export tracking (export_person_id, export_timestamp)
- **TECH-013**: Create audit log entries for status changes

#### 5.2.2 Database Schema Updates
```sql
-- Add export tracking fields to purchase_orders table
ALTER TABLE purchase_orders ADD COLUMN export_person_id INTEGER REFERENCES users(user_id);
ALTER TABLE purchase_orders ADD COLUMN last_export_at TIMESTAMP;
ALTER TABLE purchase_orders ADD COLUMN export_count INTEGER DEFAULT 0;
```

### 5.3 API Enhancements

#### 5.3.1 Export Endpoint Updates
- **TECH-014**: Modify `/api/v1/po/<po_no>/export` to handle status validation
- **TECH-015**: Update response format to include status change information
- **TECH-016**: Add export format validation and error handling
- **TECH-017**: Implement export audit logging

#### 5.3.2 New API Endpoints (Future)
- **TECH-018**: Create `/api/v1/po/<po_no>/export-history` for audit trail
- **TECH-019**: Create `/api/v1/po/<po_no>/can-export` for validation checks

---

## 6. User Interface Requirements

### 6.1 PreviewModal Enhancements

#### 6.1.1 Status-Based Button States
- **UI-001**: Show export buttons only for eligible POs (order_created, outputted)
- **UI-002**: Display status information prominently in the modal
- **UI-003**: Show export history/count when applicable
- **UI-004**: Implement loading states for all export operations

#### 6.1.2 Print Preview Improvements
- **UI-005**: Add "Print Preview" mode that matches exact print output
- **UI-006**: Implement print-specific layout toggle
- **UI-007**: Show/hide non-printable sections based on mode
- **UI-008**: Add A4 page boundaries visualization

### 6.2 Error Handling & Feedback

#### 6.2.1 User Feedback
- **UI-009**: Display clear success messages after successful exports
- **UI-010**: Show descriptive error messages for failed operations
- **UI-011**: Indicate status changes in real-time
- **UI-012**: Provide export progress indicators

#### 6.2.2 Validation Messages
- **UI-013**: Show warning if PO data is incomplete
- **UI-014**: Display status eligibility information
- **UI-015**: Provide contextual help for export options

---

## 7. Acceptance Criteria

### 7.1 Print Functionality Testing

#### Test Case 1: Print Layout Verification
- **Given**: A purchase order with complete data
- **When**: User clicks "列印" (Print) button
- **Then**: 
  - Print preview displays correctly formatted layout
  - Content fits within A4 paper boundaries
  - All text is readable and properly sized
  - Layout matches the on-screen preview exactly

#### Test Case 2: Multi-page Print Handling  
- **Given**: A purchase order with many line items
- **When**: User prints the order
- **Then**:
  - Page breaks occur at appropriate locations
  - Headers and footers appear on each page
  - No content is cut off inappropriately
  - Page numbers are displayed correctly

### 7.2 Status Transition Testing

#### Test Case 3: First Export Status Update
- **Given**: A PO with status "order_created" (已建立)
- **When**: User exports the PO successfully
- **Then**:
  - PO status changes to "outputted" (已製單)
  - Export person ID is recorded
  - Export timestamp is saved
  - Database changes are persisted

#### Test Case 4: Re-export Capability
- **Given**: A PO with status "outputted" (已製單) 
- **When**: User attempts to export again
- **Then**:
  - Export operation succeeds
  - Status remains "outputted"
  - Export count is incremented
  - New export timestamp is recorded

#### Test Case 5: Invalid Status Handling
- **Given**: A PO with status "purchased" 
- **When**: User attempts to export
- **Then**:
  - Export buttons are disabled or hidden
  - Clear message explains why export is not available
  - No server request is made

### 7.3 Cross-browser Compatibility

#### Test Case 6: Browser Print Compatibility
- **Given**: The application is opened in different browsers
- **When**: User prints a purchase order
- **Then**:
  - Print output is consistent across Chrome, Firefox, Edge
  - CSS print styles are applied correctly
  - No layout differences between browsers

---

## 8. Success Metrics

### 8.1 Quality Metrics

#### 8.1.1 Print Quality
- **Target**: 100% of printed POs have acceptable layout quality
- **Measurement**: User acceptance testing with procurement staff
- **Success Criteria**: All test POs print correctly on first attempt

#### 8.1.2 Status Accuracy
- **Target**: 100% of export operations update status correctly
- **Measurement**: Automated testing of status transitions
- **Success Criteria**: All status changes are logged and persistent

### 8.2 Performance Metrics

#### 8.2.1 Export Response Time
- **Target**: < 3 seconds for print operation initiation
- **Measurement**: Time from button click to print dialog appearance
- **Success Criteria**: 95% of operations complete within target time

#### 8.2.2 System Reliability
- **Target**: < 1% export operation failure rate
- **Measurement**: Failed exports / total export attempts
- **Success Criteria**: System handles errors gracefully with clear messaging

### 8.3 User Satisfaction

#### 8.3.1 Usability Score
- **Target**: > 4.5/5.0 user satisfaction rating
- **Measurement**: Post-implementation user survey
- **Success Criteria**: Users can successfully print POs without assistance

#### 8.3.2 Task Completion Rate
- **Target**: > 95% successful completion rate for PO export tasks
- **Measurement**: Task-based user testing
- **Success Criteria**: Users complete export tasks successfully on first attempt

---

## 9. Implementation Phases

### Phase 1: Critical Fix (Week 1)
**Priority**: P0 - Critical Bug Fix
- Fix A4 print layout issues (CSS @media print)
- Implement proper status transition logic
- Update export endpoint for status validation
- Basic testing and validation

### Phase 2: Enhancement (Week 2-3)
**Priority**: P1 - Core Functionality
- Add export audit tracking
- Implement database schema updates
- Enhanced UI feedback and error handling
- Comprehensive testing across browsers

### Phase 3: Future Improvements (Week 4+)
**Priority**: P2 - Nice to Have
- PDF export implementation
- Excel export enhancement
- Export history API
- Advanced print options

---

## 10. Dependencies and Constraints

### 10.1 Technical Dependencies
- Current Vue.js and Element Plus framework
- Existing PurchaseOrder model and database schema
- Flask backend API structure
- Browser print API support

### 10.2 Business Constraints
- Must maintain backward compatibility with existing PO data
- Cannot disrupt current procurement workflow during implementation
- Must support existing user permissions and access controls
- Print output must comply with company branding standards

### 10.3 Resource Requirements
- 1 Frontend Developer (Vue.js/CSS expertise)
- 1 Backend Developer (Python/Flask experience)  
- 1 QA Engineer for cross-browser testing
- UX review for print layout validation

---

## 11. Risk Assessment

### 11.1 Technical Risks

#### High Risk: Browser Print Inconsistencies
- **Risk**: Different browsers may render print layouts differently
- **Mitigation**: Extensive cross-browser testing and CSS normalization
- **Contingency**: Browser-specific CSS overrides if needed

#### Medium Risk: Database Migration Issues
- **Risk**: Adding new columns may affect existing data
- **Mitigation**: Proper migration scripts with rollback capability
- **Contingency**: Database backup and restore procedures

### 11.2 Business Risks

#### Medium Risk: User Adoption
- **Risk**: Users may resist changes to familiar workflow
- **Mitigation**: Clear communication and training on new features
- **Contingency**: Phased rollout with user feedback incorporation

#### Low Risk: Performance Impact
- **Risk**: Additional database fields may slow queries
- **Mitigation**: Database indexing and query optimization
- **Contingency**: Performance monitoring and optimization as needed

---

## 12. Appendix

### 12.1 Current Status Values
```
'pending' -> Initial creation state
'confirmed' -> Approved for PO creation
'order_created' (已建立) -> PO created, ready for export
'outputted' (已製單) -> PO exported/sent to supplier  
'purchased' -> Purchase confirmed
'shipped' -> Items shipped from supplier
```

### 12.2 CSS Print Media Query Template
```css
@media print {
  @page {
    size: A4;
    margin: 25mm 20mm 25mm 20mm;
  }
  
  .non-printable-section {
    display: none !important;
  }
  
  .preview-container {
    width: 100%;
    max-width: none;
    padding: 0;
  }
}
```

### 12.3 API Request/Response Examples

#### Export Request
```json
POST /api/v1/po/PO20250910001/export
{
  "format": "print",
  "quotation_no": "QT-2025-001"
}
```

#### Export Response
```json
{
  "success": true,
  "data": {
    "purchase_order_no": "PO20250910001",
    "previous_status": "order_created", 
    "current_status": "outputted",
    "export_person_id": 1001,
    "export_timestamp": "2025-09-10T10:30:00Z"
  }
}
```

---

**Document End**

*This PRD serves as the definitive guide for implementing the Purchase Order Export Feature. All development work should align with these requirements, and any changes should be approved through the standard change control process.*