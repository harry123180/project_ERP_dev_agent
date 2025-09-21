# A4 Print Layout Specifications for Purchase Order Preview

## A4 Paper Dimensions and Constraints

### Physical Specifications
```
Paper Size: A4 (ISO 216)
Width: 210mm (8.27 inches)
Height: 297mm (11.69 inches)
Aspect Ratio: √2 (1.414:1)
```

### Print Margins (Recommended)
```
Top Margin: 15mm (0.59") - Header clearance
Bottom Margin: 20mm (0.79") - Footer/binding clearance  
Left Margin: 10mm (0.39") - Binding clearance
Right Margin: 10mm (0.39") - Standard clearance

Printable Area: 190mm × 262mm
Content Safety Zone: 170mm × 240mm (accounting for printer variations)
```

### CSS Implementation
```css
@page {
    size: A4 portrait;
    margin: 15mm 10mm 20mm 10mm;
    -webkit-print-color-adjust: exact;
    color-adjust: exact;
}
```

## Detailed Layout Grid System

### Vertical Layout Allocation (240mm Content Height)

#### Section Heights with Pixel Equivalents (at 96 DPI)
```
Company Header Section:     35mm (132px) - 14.6%
Supplier Information:       25mm (95px)  - 10.4%  
Items Table Header:         8mm (30px)   - 3.3%
Items Table Content:       120mm (454px) - 50.0%
Totals Section:            15mm (57px)   - 6.3%
Terms & Conditions:        25mm (95px)   - 10.4%
Signature Section:         12mm (45px)   - 5.0%
```

#### Flexible Content Zones
```
Fixed Content (Must Fit):   95mm (39.6%)
- Header: 35mm
- Info Table: 25mm  
- Table Header: 8mm
- Totals: 15mm
- Signatures: 12mm

Variable Content:          145mm (60.4%)
- Items Table: 120mm (expandable)
- Terms Section: 25mm (compressible to 15mm minimum)

Overflow Strategy:
- Items > 12 rows: Continue to page 2
- Terms > 25mm: Compress font or continue to page 2
- Never break: Header, totals, signatures
```

### Horizontal Layout Grid (170mm Content Width)

#### Column System for Items Table
```
Total Available Width: 170mm

Optimized Column Widths:
┌──────┬─────────────┬──────────┬────────┬──────┬──────┬────────┬────────┬──────┐
│ 項次 │    品名     │   規格   │  型號  │ 數量 │ 單位 │  單價  │  小計  │ 備註 │
│ No.  │ Item Name   │   Spec   │ Model  │ Qty  │ Unit │ Price  │Subtotal│Notes │
├──────┼─────────────┼──────────┼────────┼──────┼──────┼────────┼────────┼──────┤
│ 15mm │    45mm     │   30mm   │  25mm  │ 15mm │ 12mm │  18mm  │  18mm  │ 12mm │
│ 8.8% │   26.5%     │  17.6%   │ 14.7%  │ 8.8% │ 7.1% │ 10.6%  │ 10.6%  │ 7.1% │
└──────┴─────────────┴──────────┴────────┴──────┴──────┴────────┴────────┴──────┘

Key Improvements:
- Item Name: Increased from 22% to 26.5% (most important column)
- Specification: Reduced from 18% to 17.6% (often short)
- Model: Reduced from 12% to 14.7% (balanced)
- Removed excessive padding (2mm saved per column)
- Notes: Minimized to 7.1% (rarely used in print)
```

#### Typography Scaling for Columns
```
Column Headers: 10pt Bold, #000000
Item Name: 9pt Regular, #000000 (Primary content)
Specification: 8pt Regular, #000000 (Secondary)
Model Number: 8pt Monospace, #000000 (Codes/Numbers)
Quantities: 9pt Right-aligned, #000000 (Numbers)
Currency: 9pt Monospace Right-aligned, #000000 (Financial)

Line Height: 1.1 (tight for space efficiency)
Cell Padding: 1mm vertical, 0.5mm horizontal
Border: 0.5pt solid #333333
```

## Section-by-Section Specifications

### 1. Company Header (35mm height)

#### Layout Structure
```
┌────────────────────────────────────────────────────────────────┐ 35mm
│ ┌──────────┐        採購單           ┌─────────────┐           │
│ │   TSIC   │     PURCHASE ORDER      │   Status    │           │ 20mm
│ │   LOGO   │                        │  Badge      │           │
│ └──────────┘                        └─────────────┘           │
├────────────────────────────────────────────────────────────────┤ 15mm
│                     2pt Border Line                           │
└────────────────────────────────────────────────────────────────┘
│<-- 45mm -->│<------- 80mm ------->│<-- 45mm -->│

Logo Zone: 45mm × 30mm (max logo size: 40mm × 25mm)
Title Zone: 80mm × 20mm (centered)
Status Zone: 45mm × 20mm (right-aligned)
Border: 15mm reserved for bottom border
```

#### Typography
```
Title "採購單": 20pt Bold, #000000, Center-aligned
Subtitle "PURCHASE ORDER": 14pt Regular, #333333, Center-aligned
Status Badge: 12pt SemiBold, Color-coded background
Border: 2pt solid #000000
```

### 2. Supplier Information Table (25mm height)

#### 4×4 Grid Layout
```
┌─────────────┬─────────────┬─────────────┬─────────────┐ 6.25mm
│  廠商名稱   │ ABC Company │  採購單號   │  P20240001  │ per row
├─────────────┼─────────────┼─────────────┼─────────────┤
│  廠商編號   │   S001      │  訂購日期   │ 2024/01/15  │
├─────────────┼─────────────┼─────────────┼─────────────┤
│  廠商地址   │台北市信義區 │  報價單號   │[Input Field]│
├─────────────┼─────────────┼─────────────┼─────────────┤
│  連絡電話   │02-1234-5678 │  聯絡人     │  王小明     │
└─────────────┴─────────────┴─────────────┴─────────────┘

Column Widths: 42.5mm each (170mm ÷ 4)
Cell Height: 6.25mm (25mm ÷ 4)
Cell Padding: 2mm internal
```

#### Cell Typography
```
Label Cells: 10pt SemiBold, #000000, Gray background (#f0f0f0)
Value Cells: 10pt Regular, #000000, White background
Border: 0.5pt solid #333333
Cell Internal Padding: 2mm all sides
```

### 3. Items Table (120mm base height, expandable)

#### Row Specifications
```
Header Row: 8mm height
Data Rows: 6mm height each (compact for more content)
Maximum Rows per Page: 18 rows (108mm content + 12mm for headers/spacing)
Optimal Rows: 15 rows (90mm content + 30mm buffer)

Row Calculation:
Available Height: 120mm
Header: 8mm
Per Row: 6mm
Buffer: 12mm (2mm above/below table)
Usable: 100mm ÷ 6mm = 16 rows maximum
Recommended: 15 rows (leaves 10mm buffer)
```

#### Cell Content Handling
```
Text Overflow Strategy:
- Item Name: Wrap to 2 lines max, ellipsis after
- Specification: Wrap to 2 lines max, abbreviate
- Model: Single line, ellipsis if needed
- Numeric: Single line, right-aligned
- Notes: Single line, abbreviate to "..." if long

Font Sizes by Content Importance:
Critical (Names, Prices): 9pt
Important (Specs, Quantities): 8pt  
Reference (Notes, Model): 7.5pt
```

#### Currency Formatting Optimization
```
Current Format: "NT$ 123,456" (11 characters, 18mm wide)
Optimized Format: "$123,456" (8 characters, 14mm wide)
Space Savings: 22% width reduction per currency column

Implementation:
- Column header shows currency: "單價 (NT$)"
- Cell content shows: "$123,456" 
- Maintain right alignment
- Use monospace font for alignment
```

### 4. Totals Section (15mm height)

#### Layout Structure
```
                                      ┌──────────────────┐
                小計 Subtotal:        │   $1,234,567     │ 4mm
                稅額 Tax (5%):         │     $61,728      │ 4mm  
                ──────────────────────────────────────────
                總計 Total:           │ $1,296,295       │ 7mm
                                      └──────────────────┘

Right margin: 30mm from edge
Label width: 50mm
Value width: 40mm  
Total section width: 90mm
```

#### Typography
```
Labels: 11pt Regular, #000000, Right-aligned
Values: 11pt Bold Monospace, #000000, Right-aligned  
Grand Total: 12pt Bold, #000000, Blue accent (#409eff)
Separator Line: 1pt solid #333333, 60mm width
```

### 5. Terms & Conditions (25mm height, compressible)

#### Content Strategy
```
Optimal Height: 25mm (comfortable reading)
Minimum Height: 15mm (compressed emergency)
Maximum Height: 35mm (detailed terms)

Content Adaptation:
- Standard: 5 terms, 9pt font, 25mm height
- Compressed: 5 terms, 8pt font, 15mm height  
- Extended: 7+ terms, 9pt font, 35mm+ height (page 2)
```

#### Layout
```
┌─────────────────────────────────────────────────┐
│ 注意事項 Terms and Conditions                   │ 5mm header
├─────────────────────────────────────────────────┤
│ 1. 付款條件：月結 30 天                        │
│ 2. 交貨期限：訂單確認後 14 個工作天            │ 20mm
│ 3. 品質要求：須符合國家標準規範                │ content
│ 4. 驗收標準：貨到 7 日內完成驗收               │
│ 5. 保固期限：自驗收合格日起算一年              │
└─────────────────────────────────────────────────┘

Border: 0.5pt solid #cccccc
Internal Padding: 3mm all sides
Line Height: 1.3 for readability
```

### 6. Signature Section (12mm height)

#### Layout Structure
```
┌─────────────────────┬─────────────────────┐ 6mm
│ 採購人員：_______   │ 核准主管：_______   │ per row
├─────────────────────┼─────────────────────┤
│ 日期：_________     │ 日期：_________     │ 6mm
└─────────────────────┴─────────────────────┘

Each signature field: 85mm width
Signature line: 60mm width, 1pt solid #333333
Label width: 25mm
```

## Multi-Page Handling Strategy

### Page Break Logic
```
Page 1 Priority Content (Must Fit):
1. Company Header
2. Supplier Information  
3. Items Table Header + First 8 items
4. Totals Section
5. Basic Terms (compressed if needed)
6. Signature Section

Page 2 Continuation:
1. Items Table Continuation Header
2. Remaining Items (9+ onwards)
3. Extended Terms (if needed)
4. Additional Notes/Information
```

### Continuation Indicators
```
Page 1 Footer: "續下頁 (Continued on next page)"
Page 2 Header: "採購單 (續) Purchase Order (Continued)"
Page Numbers: "Page 1 of 2" format
Item Numbering: Continuous across pages
```

## Responsive Print Scaling

### Browser Zoom Compensation
```
Default Scale: 100% (actual size)
Browser Zoom 90%: Scale up 111% (1/0.9)
Browser Zoom 110%: Scale down 91% (1/1.1)
Browser Zoom 125%: Scale down 80% (1/1.25)

CSS Implementation:
@media print {
    .preview-container {
        transform: scale(var(--print-scale, 1));
        transform-origin: top left;
    }
}
```

### Printer-Specific Adjustments
```
HP LaserJet: Standard scaling (100%)
Canon ImageClass: Scale down 98% (slight oversizing)
Brother Laser: Scale up 102% (slight undersizing)
Epson Inkjet: Scale down 97% (larger margins)

Implementation: User-selectable printer profiles
```

## Quality Assurance Checkpoints

### Visual Verification Points
1. **Content Boundaries**: All content within 170mm × 240mm safety zone
2. **Text Readability**: Minimum 8pt font size maintained
3. **Currency Alignment**: All currency values right-aligned consistently  
4. **Table Integrity**: No broken rows, consistent column widths
5. **Professional Appearance**: Clean borders, proper spacing

### Print Test Requirements
1. **Physical Print Test**: Actual A4 paper output verification
2. **Cross-Browser Testing**: Chrome, Firefox, Edge, Safari
3. **PDF Generation Testing**: Consistent output across PDF generators
4. **Scale Verification**: Measure printed output with ruler
5. **Usability Testing**: Real users printing real documents

### Success Criteria
- [ ] 100% content fits within A4 boundaries
- [ ] No text smaller than 8pt in final output
- [ ] Currency columns align perfectly  
- [ ] Print time < 30 seconds from preview
- [ ] User satisfaction rating > 4.0/5.0

## Implementation CSS Classes

### Utility Classes for Print Layout
```css
/* Print-optimized typography */
.print-title { font-size: 20pt; font-weight: bold; }
.print-subtitle { font-size: 14pt; font-weight: normal; }
.print-header { font-size: 12pt; font-weight: bold; }
.print-body { font-size: 10pt; font-weight: normal; }
.print-small { font-size: 9pt; font-weight: normal; }
.print-tiny { font-size: 8pt; font-weight: normal; }

/* Layout constraints */
.print-page { width: 170mm; max-height: 240mm; }
.print-header-section { height: 35mm; }
.print-info-section { height: 25mm; }
.print-items-section { min-height: 120mm; }
.print-totals-section { height: 15mm; }
.print-terms-section { height: 25mm; min-height: 15mm; }
.print-signature-section { height: 12mm; }

/* Column widths */
.col-index { width: 15mm; }
.col-item-name { width: 45mm; }
.col-specification { width: 30mm; }
.col-model { width: 25mm; }
.col-quantity { width: 15mm; }
.col-unit { width: 12mm; }
.col-price { width: 18mm; }
.col-subtotal { width: 18mm; }
.col-notes { width: 12mm; }
```

This specification provides the precise measurements and implementation guidelines needed to create a professional, print-optimized A4 layout that addresses all the identified issues with the current system.