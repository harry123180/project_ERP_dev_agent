# Purchase Order A4 Print Layout - UX Specification

## Document Information
- **Version**: 1.0
- **Created**: 2025-09-10
- **Last Updated**: 2025-09-10
- **Status**: Final
- **Author**: UX Team - Sally (UX Expert & UI Specialist)
- **Reviewers**: Development Team, Product Management

---

## 1. Executive Summary

This UX specification addresses critical print layout issues in the ERP Purchase Order system. The current implementation suffers from layout distortion, scaling problems, and misalignment when printing to A4 paper. This document provides comprehensive specifications to ensure print output matches on-screen preview exactly.

### Key UX Principles Applied
- **User-Centric Design**: Print output must be immediately usable by procurement staff
- **Consistency**: Preview should match final print output exactly 
- **Accessibility**: All text must be readable with proper contrast and sizing
- **Professional Appearance**: Output must maintain corporate standards

---

## 2. Current Problem Analysis

### 2.1 Identified Issues
Based on analysis of `PreviewModal.vue`, the current print CSS is insufficient:

```css
/* Current inadequate implementation */
@media print {
  .po-preview-modal {
    .terms-selector,
    .non-printable-section {
      display: none !important;
    }
  }
}
```

### 2.2 Root Causes
1. **No page size specification**: Missing `@page` rules for A4
2. **Inadequate margin control**: No proper margin management
3. **Missing layout constraints**: Container widths not optimized for print
4. **Font scaling issues**: No print-specific typography rules
5. **Table layout problems**: No responsive table handling for print

---

## 3. A4 Print Layout Specifications

### 3.1 Physical Dimensions

#### 3.1.1 A4 Paper Standards
- **Paper Size**: 210mm × 297mm (8.27" × 11.69")
- **Print Resolution**: 300 DPI minimum
- **Orientation**: Portrait (vertical)

#### 3.1.2 Safe Margins
```
Top Margin:     20mm (0.79") - Header clearance
Bottom Margin:  25mm (0.98") - Footer + printer margin
Left Margin:    15mm (0.59") - Text readability
Right Margin:   15mm (0.59") - Text readability
```

#### 3.1.3 Content Area
- **Available Width**: 180mm (7.09")
- **Available Height**: 252mm (9.92")
- **Content Area**: 180mm × 252mm

### 3.2 Layout Grid System

#### 3.2.1 Vertical Layout Structure
```
┌─────────────────────────────────────────────────────┐
│ Company Header (80mm height)                        │
├─────────────────────────────────────────────────────┤
│ Supplier Info Table (40mm height)                   │
├─────────────────────────────────────────────────────┤
│ Purchase Items Table (Variable, min 60mm)           │
├─────────────────────────────────────────────────────┤
│ Totals Section (25mm height)                        │
├─────────────────────────────────────────────────────┤
│ Terms & Conditions (30mm height)                    │
├─────────────────────────────────────────────────────┤
│ Signature Section (37mm height)                     │
└─────────────────────────────────────────────────────┘
```

#### 3.2.2 Horizontal Layout Proportions
- **Logo Section**: 50mm width (27.8%)
- **Header Center**: 80mm width (44.4%)
- **Header Right**: 50mm width (27.8%)

---

## 4. Component Layout Specifications

### 4.1 Company Header Section

#### 4.1.1 Dimensions
- **Total Height**: 80mm
- **Logo Maximum Size**: 45mm × 30mm
- **Title Font Size**: 24pt (8.5mm)
- **Subtitle Font Size**: 14pt (5mm)

#### 4.1.2 Layout Rules
```css
.company-header {
  height: 80mm;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 2pt solid #000;
  margin-bottom: 10mm;
}

.company-logo {
  max-width: 45mm;
  max-height: 30mm;
  object-fit: contain;
}

.title {
  font-size: 24pt;
  font-weight: bold;
  line-height: 1.2;
}

.subtitle {
  font-size: 14pt;
  font-weight: normal;
  line-height: 1.2;
}
```

### 4.2 Supplier Information Table

#### 4.2.1 4×4 Table Specifications
- **Total Height**: 40mm
- **Row Height**: 10mm
- **Border Width**: 0.5pt
- **Cell Padding**: 2mm

#### 4.2.2 Column Widths
```
Label 1:  35mm (19.4%)  | Value 1:  55mm (30.6%)
Label 2:  35mm (19.4%)  | Value 2:  55mm (30.6%)
```

#### 4.2.3 Table Layout CSS
```css
.info-table {
  width: 100%;
  height: 40mm;
  border-collapse: collapse;
  margin-bottom: 10mm;
}

.info-table td {
  padding: 2mm;
  border: 0.5pt solid #333;
  vertical-align: middle;
  font-size: 10pt;
  line-height: 1.2;
}

.info-table .label {
  width: 35mm;
  background: #f0f0f0;
  font-weight: 600;
}

.info-table .value {
  width: 55mm;
}
```

### 4.3 Purchase Items Table

#### 4.3.1 Column Width Distribution
```
項次 (Index):        12mm (6.7%)
品名 (Item Name):    45mm (25%)
規格 (Spec):         30mm (16.7%)
型號 (Model):        25mm (13.9%)
數量 (Quantity):     18mm (10%)
單位 (Unit):         15mm (8.3%)
單價 (Unit Price):   20mm (11.1%)
小計 (Subtotal):     25mm (13.9%)
備註 (Remarks):      25mm (13.9%)
```

#### 4.3.2 Table Styling
```css
.el-table {
  font-size: 9pt;
  line-height: 1.1;
}

.el-table th {
  background: #f5f5f5 !important;
  font-size: 10pt;
  font-weight: 600;
  padding: 2mm !important;
  border: 0.5pt solid #333 !important;
}

.el-table td {
  padding: 1.5mm !important;
  border: 0.5pt solid #333 !important;
  font-size: 9pt;
}

.el-table .cell {
  line-height: 1.2;
  word-break: break-word;
  overflow: hidden;
}
```

### 4.4 Totals Section

#### 4.4.1 Dimensions & Alignment
- **Height**: 25mm
- **Alignment**: Right-aligned
- **Right Margin**: 30mm from edge
- **Font Size**: 11pt (12pt for grand total)

#### 4.4.2 Layout CSS
```css
.totals-section {
  height: 25mm;
  margin: 8mm 30mm 8mm 0;
  text-align: right;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.total-row {
  margin-bottom: 2mm;
  font-size: 11pt;
  line-height: 1.3;
}

.grand-total {
  font-size: 12pt;
  font-weight: bold;
  border-top: 1pt solid #333;
  padding-top: 2mm;
  margin-top: 2mm;
}
```

### 4.5 Terms & Conditions Section

#### 4.5.1 Specifications
- **Height**: 30mm (expandable)
- **Font Size**: 9pt
- **Line Height**: 1.3
- **Margin**: 5mm bottom

#### 4.5.2 Styling
```css
.terms-section {
  min-height: 30mm;
  margin-bottom: 5mm;
}

.terms-content {
  font-size: 9pt;
  line-height: 1.3;
  white-space: pre-line;
  border: 0.5pt solid #ccc;
  padding: 3mm;
}
```

### 4.6 Signature Section

#### 4.6.1 Layout Specifications
- **Total Height**: 37mm
- **Row Height**: 15mm each
- **Signature Line Length**: 60mm
- **Font Size**: 10pt

#### 4.6.2 Signature Layout CSS
```css
.signature-section {
  height: 37mm;
  margin-top: 10mm;
}

.signature-row {
  height: 15mm;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 7mm;
}

.signature-item {
  display: flex;
  align-items: center;
  width: 80mm;
}

.signature-line {
  width: 60mm;
  border-bottom: 1pt solid #333;
  height: 1pt;
  margin-left: 5mm;
}
```

---

## 5. Typography Guidelines

### 5.1 Font Stack
**Primary**: `"PingFang TC", "Helvetica Neue", Arial, "Microsoft JhengHei", sans-serif`
**Fallback**: System fonts with Chinese support

### 5.2 Font Size Hierarchy
```css
/* Print-optimized font sizes */
h1 (Main Title):      24pt (8.5mm)
h2 (Subtitle):        14pt (5mm)  
h3 (Section Headers): 12pt (4.2mm)
Body Text:           10pt (3.5mm)
Table Headers:       10pt (3.5mm)
Table Cells:          9pt (3.2mm)
Terms Text:           9pt (3.2mm)
Small Text:           8pt (2.8mm)
```

### 5.3 Line Height Standards
- **Headlines**: 1.2
- **Body Text**: 1.3
- **Table Content**: 1.1
- **Dense Text**: 1.1

### 5.4 Font Weight Usage
- **Bold (600)**: Headers, labels, grand total
- **Semi-bold (500)**: Table headers, important values
- **Regular (400)**: Body text, values
- **Light (300)**: Not recommended for print

---

## 6. Print-Specific CSS Media Queries

### 6.1 Complete Print Stylesheet

```css
@media print {
  /* Page Setup */
  @page {
    size: A4 portrait;
    margin: 20mm 15mm 25mm 15mm;
    
    /* Print optimization */
    -webkit-print-color-adjust: exact;
    color-adjust: exact;
    print-color-adjust: exact;
    
    /* Page break settings */
    orphans: 3;
    widows: 3;
  }
  
  /* Hide non-printable elements */
  .el-dialog__wrapper,
  .el-dialog__header,
  .dialog-footer,
  .terms-selector,
  .non-printable-section,
  .el-loading-mask,
  .el-input,
  .el-select {
    display: none !important;
  }
  
  /* Main container adjustments */
  .po-preview-modal .el-dialog,
  .po-preview-modal .el-dialog__body,
  .preview-container {
    width: 100% !important;
    max-width: 180mm !important;
    height: auto !important;
    padding: 0 !important;
    margin: 0 !important;
    box-shadow: none !important;
    border: none !important;
    border-radius: 0 !important;
    background: white !important;
    color: black !important;
  }
  
  /* Company Header */
  .company-header {
    height: 80mm !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    border-bottom: 2pt solid #000 !important;
    margin-bottom: 10mm !important;
    page-break-inside: avoid !important;
  }
  
  .company-logo {
    max-width: 45mm !important;
    max-height: 30mm !important;
    object-fit: contain !important;
  }
  
  .title {
    font-size: 24pt !important;
    font-weight: bold !important;
    line-height: 1.2 !important;
    color: #000 !important;
  }
  
  .subtitle {
    font-size: 14pt !important;
    font-weight: normal !important;
    line-height: 1.2 !important;
    color: #333 !important;
  }
  
  /* Supplier Information Table */
  .info-table {
    width: 100% !important;
    height: 40mm !important;
    border-collapse: collapse !important;
    margin-bottom: 10mm !important;
    page-break-inside: avoid !important;
  }
  
  .info-table td {
    padding: 2mm !important;
    border: 0.5pt solid #333 !important;
    vertical-align: middle !important;
    font-size: 10pt !important;
    line-height: 1.2 !important;
    color: #000 !important;
  }
  
  .info-table .label {
    width: 35mm !important;
    background: #f0f0f0 !important;
    font-weight: 600 !important;
  }
  
  .info-table .value {
    width: 55mm !important;
  }
  
  /* Purchase Items Table */
  .el-table {
    font-size: 9pt !important;
    line-height: 1.1 !important;
    border-collapse: collapse !important;
    width: 100% !important;
    margin-bottom: 8mm !important;
  }
  
  .el-table th {
    background: #f5f5f5 !important;
    font-size: 10pt !important;
    font-weight: 600 !important;
    padding: 2mm !important;
    border: 0.5pt solid #333 !important;
    color: #000 !important;
  }
  
  .el-table td {
    padding: 1.5mm !important;
    border: 0.5pt solid #333 !important;
    font-size: 9pt !important;
    color: #000 !important;
  }
  
  .el-table .cell {
    line-height: 1.2 !important;
    word-break: break-word !important;
    overflow: hidden !important;
    padding: 0 !important;
  }
  
  /* Column-specific widths */
  .el-table .el-table__cell:nth-child(1) { width: 12mm !important; } /* 項次 */
  .el-table .el-table__cell:nth-child(2) { width: 45mm !important; } /* 品名 */
  .el-table .el-table__cell:nth-child(3) { width: 30mm !important; } /* 規格 */
  .el-table .el-table__cell:nth-child(4) { width: 25mm !important; } /* 型號 */
  .el-table .el-table__cell:nth-child(5) { width: 18mm !important; } /* 數量 */
  .el-table .el-table__cell:nth-child(6) { width: 15mm !important; } /* 單位 */
  .el-table .el-table__cell:nth-child(7) { width: 20mm !important; } /* 單價 */
  .el-table .el-table__cell:nth-child(8) { width: 25mm !important; } /* 小計 */
  .el-table .el-table__cell:nth-child(9) { width: 25mm !important; } /* 備註 */
  
  /* Totals Section */
  .totals-section {
    height: 25mm !important;
    margin: 8mm 30mm 8mm 0 !important;
    text-align: right !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    page-break-inside: avoid !important;
  }
  
  .total-row {
    margin-bottom: 2mm !important;
    font-size: 11pt !important;
    line-height: 1.3 !important;
    color: #000 !important;
  }
  
  .grand-total {
    font-size: 12pt !important;
    font-weight: bold !important;
    border-top: 1pt solid #333 !important;
    padding-top: 2mm !important;
    margin-top: 2mm !important;
  }
  
  /* Terms & Conditions */
  .section {
    margin-bottom: 5mm !important;
  }
  
  .section-title {
    font-size: 12pt !important;
    font-weight: bold !important;
    margin-bottom: 3mm !important;
    color: #000 !important;
    border-bottom: 1pt solid #333 !important;
    padding-bottom: 1mm !important;
  }
  
  /* Terms content handling for textarea */
  .el-textarea__inner {
    display: none !important;
  }
  
  /* Add a print-only terms display */
  .terms-print-content {
    display: block !important;
    font-size: 9pt !important;
    line-height: 1.3 !important;
    white-space: pre-line !important;
    border: 0.5pt solid #ccc !important;
    padding: 3mm !important;
    min-height: 25mm !important;
    color: #000 !important;
  }
  
  /* Signature Section */
  .signature-section {
    height: 37mm !important;
    margin-top: 10mm !important;
    page-break-inside: avoid !important;
  }
  
  .signature-row {
    height: 15mm !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    margin-bottom: 7mm !important;
  }
  
  .signature-item {
    display: flex !important;
    align-items: center !important;
    width: 80mm !important;
    font-size: 10pt !important;
    color: #000 !important;
  }
  
  .signature-line {
    width: 60mm !important;
    border-bottom: 1pt solid #333 !important;
    height: 1pt !important;
    margin-left: 5mm !important;
  }
  
  /* Page break management */
  .company-header,
  .info-table-section,
  .totals-section,
  .signature-section {
    page-break-inside: avoid !important;
  }
  
  .el-table tbody tr {
    page-break-inside: avoid !important;
  }
  
  /* Ensure proper page breaks */
  h3 {
    page-break-after: avoid !important;
  }
}

/* Screen preview mode enhancements */
@media screen {
  .po-preview-modal .preview-container.print-preview-mode {
    width: 180mm;
    min-height: 252mm;
    margin: 0 auto;
    background: white;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
    padding: 20mm 15mm 25mm 15mm;
    box-sizing: border-box;
  }
}
```

### 6.2 Browser-Specific Adjustments

```css
/* Chrome print adjustments */
@media print and (-webkit-min-device-pixel-ratio: 0) {
  .company-header {
    -webkit-print-color-adjust: exact;
  }
  
  .info-table .label {
    -webkit-print-color-adjust: exact;
  }
}

/* Firefox print adjustments */
@-moz-document url-prefix() {
  @media print {
    .el-table th {
      background: #f5f5f5 !important;
      color-adjust: exact;
    }
  }
}
```

---

## 7. Implementation Guidelines

### 7.1 Component Updates Required

#### 7.1.1 Template Modifications
1. Add print-only terms content display
2. Implement print preview toggle
3. Add A4 page boundary visualization

#### 7.1.2 Script Enhancements
```javascript
// Add print preview mode
const printPreviewMode = ref(false)

const togglePrintPreview = () => {
  printPreviewMode.value = !printPreviewMode.value
}

// Enhanced print handling
const handlePrint = () => {
  // Ensure terms content is properly displayed for print
  const termsTextarea = document.querySelector('.el-textarea__inner')
  const termsPrintContent = document.createElement('div')
  termsPrintContent.className = 'terms-print-content'
  termsPrintContent.textContent = termsContent.value
  
  if (termsTextarea && termsTextarea.parentNode) {
    termsTextarea.parentNode.appendChild(termsPrintContent)
  }
  
  // Trigger print
  setTimeout(() => {
    window.print()
    
    // Cleanup after print dialog
    setTimeout(() => {
      if (termsPrintContent.parentNode) {
        termsPrintContent.parentNode.removeChild(termsPrintContent)
      }
    }, 100)
  }, 100)
}
```

### 7.2 Testing Requirements

#### 7.2.1 Cross-Browser Testing
- Chrome 90+ (primary)
- Firefox 88+
- Edge 90+
- Safari 14+

#### 7.2.2 Print Testing Checklist
- [ ] A4 paper size recognition
- [ ] Margin accuracy (measure with ruler)
- [ ] Font size readability
- [ ] Table alignment and borders
- [ ] Page break behavior
- [ ] Color/grayscale output
- [ ] Multi-page handling

---

## 8. User Experience Considerations

### 8.1 Print Preview Mode
- Toggle button to switch between screen and print layout
- A4 page boundary visualization
- Zoom controls for preview inspection
- Print-safe area indicators

### 8.2 Error Prevention
- Validation warnings for incomplete data
- Print readiness checklist
- Browser compatibility notifications
- Paper size confirmation prompts

### 8.3 Accessibility
- High contrast ratios for text
- Readable font sizes (minimum 9pt)
- Proper heading hierarchy
- Screen reader compatibility

---

## 9. Success Metrics

### 9.1 Quality Measurements
- **Layout Accuracy**: 100% match between preview and print
- **Text Readability**: All text ≥9pt font size
- **Margin Compliance**: Within ±2mm of specification
- **Page Break Quality**: No inappropriate content splitting

### 9.2 User Testing Goals
- **Task Completion**: 95% successful PO printing on first attempt
- **Time to Print**: ≤30 seconds from preview to printed output  
- **User Satisfaction**: ≥4.5/5.0 rating
- **Error Rate**: <2% print quality issues

---

## 10. Implementation Checklist

### Phase 1: CSS Implementation
- [ ] Implement complete @media print stylesheet
- [ ] Add page size and margin specifications
- [ ] Configure font sizes and line heights
- [ ] Set up table column widths
- [ ] Implement page break rules

### Phase 2: Component Updates
- [ ] Add terms content print display
- [ ] Implement print preview mode
- [ ] Add A4 boundary visualization
- [ ] Enhance print handling function

### Phase 3: Testing & Validation
- [ ] Cross-browser print testing
- [ ] Physical print measurement verification
- [ ] Multi-page document testing
- [ ] User acceptance testing

### Phase 4: Documentation & Training
- [ ] Update user documentation
- [ ] Create print troubleshooting guide
- [ ] Provide training materials
- [ ] Document maintenance procedures

---

## 11. Appendix

### 11.1 Measurement Conversions
```
1mm = 2.834pt = 3.779px (at 96 DPI)
1pt = 0.353mm = 1.333px (at 96 DPI)
1inch = 25.4mm = 72pt = 96px (at 96 DPI)
```

### 11.2 A4 Print Specifications Reference
```
A4 Dimensions: 210mm × 297mm
Printable Area: 180mm × 252mm (with 15mm margins)
Content Width: 180mm = 510.236pt = 680.315px
Content Height: 252mm = 714.331pt = 952.441px
```

### 11.3 Browser Print Behavior Notes

#### Chrome
- Excellent CSS support
- Accurate @page margin handling
- Reliable print color adjustment

#### Firefox  
- Good CSS support
- May require color-adjust: exact
- Consistent margin rendering

#### Safari
- Limited @page support
- May need -webkit-print-color-adjust
- Variable margin behavior

#### Edge
- Similar to Chrome behavior
- Good standards compliance
- Reliable print output

---

**Document End**

*This UX specification provides comprehensive guidelines for implementing professional-quality A4 print layouts in the ERP Purchase Order system. All measurements and specifications are designed to ensure consistent, high-quality print output across different browsers and printer configurations.*