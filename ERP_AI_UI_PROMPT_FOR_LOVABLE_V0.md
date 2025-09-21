# AI UI Implementation Prompt for Purchase Order Preview Modal

## Prompt for v0.dev or Lovable.dev

### Context
Create a professional Purchase Order Preview Modal for an ERP system with optimized A4 print layout, multiple view modes, and responsive design. The modal should handle purchase order document preview, editing, and printing with pixel-perfect A4 page representation.

### Component Requirements

**Create a Vue 3 + TypeScript component called `PurchaseOrderPreviewModal` with the following specifications:**

#### Core Features:
1. **Three View Modes**: Edit Mode (default), Print Preview Mode, Export Mode
2. **A4 Print Optimization**: Exact 210mm × 297mm page representation with 15mm/10mm/20mm/10mm margins
3. **Responsive Design**: Desktop (1400px), Tablet (768px), Mobile (<768px) with progressive disclosure
4. **Real-time Content Fitting**: Dynamic layout adjustment with overflow detection

#### Data Structure:
```typescript
interface PurchaseOrderData {
  purchase_order_no: string
  supplier_id: string
  supplier_name: string
  supplier_address?: string
  contact_person?: string
  contact_phone?: string
  order_date: string
  quotation_no?: string
  purchase_status: 'pending' | 'confirmed' | 'order_created' | 'outputted' | 'purchased' | 'shipped'
  subtotal_int: number
  tax_decimal1: number
  grand_total_int: number
  items: Array<{
    item_name: string
    item_specification?: string
    item_model?: string
    item_quantity: number
    item_unit: string
    unit_price: number
    line_subtotal?: number
  }>
}
```

#### Layout Specifications:

**Modal Structure (1400px width on desktop):**
```
Header (60px): Title + Status + Controls
Navigation (50px): View mode tabs + Zoom controls + Page navigation  
Content Area (730px): Document preview with scrolling
Footer (60px): Action buttons
```

**A4 Print Layout (170mm × 240mm content area):**
```
Company Header: 35mm (TSIC logo + title + status)
Supplier Info: 25mm (4×4 grid with labels and values)
Items Table: 120mm expandable (optimized column widths)
Totals Section: 15mm (right-aligned currency)
Terms Section: 25mm (compressible to 15mm)
Signatures: 12mm (two signature lines)
```

**Items Table Column Optimization:**
- 項次 (Index): 15mm (8.8%)
- 品名 (Item): 45mm (26.5%) - Primary content
- 規格 (Spec): 30mm (17.6%) - Compressed
- 型號 (Model): 25mm (14.7%) - Balanced  
- 數量 (Qty): 15mm (8.8%)
- 單位 (Unit): 12mm (7.1%)
- 單價 (Price): 18mm (10.6%) - Currency format
- 小計 (Subtotal): 18mm (10.6%) - Currency format
- 備註 (Notes): 12mm (7.1%) - Minimized

#### Typography System:
```css
/* Screen Typography */
--title-size: 24pt;     /* 20pt × 1.2 scale factor */
--subtitle-size: 17pt;  /* 14pt × 1.2 scale factor */
--header-size: 14pt;    /* 12pt × 1.2 scale factor */
--body-size: 11pt;      /* 9pt × 1.2 scale factor */

/* Print Typography */  
--print-title: 20pt;
--print-subtitle: 14pt;
--print-header: 12pt;
--print-body: 10pt;
--print-table: 9pt;
--print-small: 8pt;
```

#### Key UI Components:

**1. Modal Header:**
- Left: "採購單預覽 Purchase Order Preview"
- Center: Status badge with color coding (green for outputted, blue for order_created)
- Right: Help button + Close button

**2. Navigation Bar:**
- Tab buttons: "編輯模式", "列印預覽", "匯出模式"
- Zoom control: 50%, 75%, 100%, 125%, 150%
- Page navigation: "📄 1/1" with arrow buttons
- Settings button for print options

**3. Document Content:**
```html
<!-- Company Header -->
<div class="company-header">
  <img src="/tsic-logo.png" alt="TSIC Logo" class="company-logo" />
  <div class="title-section">
    <h1>採購單</h1>
    <h2>PURCHASE ORDER</h2>
  </div>
  <div class="status-section">
    <span class="status-badge">{{ statusDisplay }}</span>
  </div>
</div>

<!-- Supplier Information Table -->
<table class="supplier-info-table">
  <tr>
    <td class="label">廠商名稱</td>
    <td class="value">{{ supplier_name }}</td>
    <td class="label">採購單號</td>
    <td class="value">{{ purchase_order_no }}</td>
  </tr>
  <!-- 3 more rows with supplier details -->
</table>

<!-- Items Table with optimized columns -->
<div class="items-section">
  <h3>採購明細 Purchase Items</h3>
  <table class="items-table">
    <thead>
      <tr>
        <th class="col-index">項次</th>
        <th class="col-item-name">品名</th>
        <th class="col-specification">規格</th>
        <th class="col-model">型號</th>
        <th class="col-quantity">數量</th>
        <th class="col-unit">單位</th>
        <th class="col-price">單價</th>
        <th class="col-subtotal">小計</th>
        <th class="col-notes">備註</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(item, index) in items" :key="index">
        <td>{{ index + 1 }}</td>
        <td>{{ item.item_name }}</td>
        <td>{{ item.item_specification || '-' }}</td>
        <td>{{ item.item_model || '-' }}</td>
        <td class="text-right">{{ item.item_quantity.toLocaleString() }}</td>
        <td>{{ item.item_unit }}</td>
        <td class="text-right currency">{{ formatCurrency(item.unit_price) }}</td>
        <td class="text-right currency">{{ formatCurrency(item.line_subtotal) }}</td>
        <td>-</td>
      </tr>
    </tbody>
  </table>
</div>

<!-- Totals Section -->
<div class="totals-section">
  <div class="total-row">
    <span class="label">小計 Subtotal：</span>
    <span class="value currency">{{ formatCurrency(subtotal_int) }}</span>
  </div>
  <div class="total-row">
    <span class="label">稅額 Tax (5%)：</span>
    <span class="value currency">{{ formatCurrency(tax_decimal1) }}</span>
  </div>
  <div class="total-row grand-total">
    <span class="label">總計 Total：</span>
    <span class="value currency">{{ formatCurrency(grand_total_int) }}</span>
  </div>
</div>
```

**4. Print Preview Mode:**
- Show exact A4 page boundaries (210mm × 297mm)
- Display page shadow and borders
- Add zoom controls and page navigation
- Show print boundary indicators
- Currency format optimization ("$123,456" instead of "NT$ 123,456")

**5. Responsive Behavior:**
- Desktop: Full modal with side-by-side layouts
- Tablet: Stacked sections with accordion disclosure
- Mobile: Single column with progressive disclosure

#### Styling Requirements:

**CSS Variables:**
```css
:root {
  --primary-blue: #409eff;
  --success-green: #67c23a;
  --warning-orange: #e6a23c;
  --danger-red: #f56c6c;
  --text-primary: #303133;
  --text-regular: #606266;
  --border-base: #dcdfe6;
  --background-base: #f5f7fa;
}
```

**Print-First CSS Structure:**
```css
@media print {
  @page { 
    size: A4 portrait; 
    margin: 15mm 10mm 20mm 10mm; 
  }
  
  .preview-container {
    width: 170mm !important;
    max-height: 240mm !important;
    font-size: 9pt;
  }
  
  .company-header { height: 35mm; }
  .supplier-info { height: 25mm; }
  .items-section { min-height: 120mm; }
  .totals-section { height: 15mm; }
  .terms-section { height: 25mm; min-height: 15mm; }
  .signature-section { height: 12mm; }
  
  /* Hide non-printable elements */
  .non-printable,
  .el-input,
  .el-select,
  .status-info { display: none !important; }
}

/* Print preview simulation */
@media screen {
  .print-preview-mode .preview-container {
    width: 210mm !important;
    min-height: 297mm !important;
    margin: 0 auto;
    background: white;
    box-shadow: 0 0 20px rgba(0,0,0,0.1);
    padding: 15mm 10mm 20mm 10mm;
    box-sizing: border-box;
    transform-origin: top center;
    position: relative;
  }
  
  /* Page boundary indicator */
  .print-preview-mode .preview-container::after {
    content: 'A4 Page Boundary';
    position: absolute;
    top: 297mm;
    left: 0;
    right: 0;
    border-top: 2px dashed #ff0000;
    font-size: 10px;
    color: #ff0000;
    text-align: center;
  }
}
```

**Currency Formatting Function:**
```typescript
const formatCurrency = (amount: number, showPrefix: boolean = true): string => {
  const formatted = amount.toLocaleString('zh-TW')
  if (printPreviewMode.value) {
    return `$${formatted}` // Optimized for print
  }
  return showPrefix ? `NT$ ${formatted}` : formatted
}
```

#### Interactive Features:

**1. View Mode Switching:**
- Smooth transitions between edit/preview/export modes
- State preservation when switching modes
- Animation: 300ms cubic-bezier(0.4, 0, 0.2, 1)

**2. Zoom Functionality:**
- Zoom levels: 50%, 75%, 100%, 125%, 150%
- Smooth scale transitions with transform-origin: top center
- Zoom state persists during modal session

**3. Content Overflow Detection:**
- Real-time measurement of content height
- Warning when content exceeds 240mm
- Automatic suggestions (multi-page, font adjustment)

**4. Print Optimization:**
- Automatic font size adjustment for content fitting
- Dynamic column width allocation based on content
- Smart page breaks for multi-page documents

#### Error States and Loading:

**Loading State:**
```html
<div class="loading-overlay">
  <div class="loading-spinner"></div>
  <p>正在載入採購單資料...</p>
  <div class="progress-bar">
    <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
  </div>
</div>
```

**Content Overflow Warning:**
```html
<div class="overflow-warning" v-if="contentOverflow">
  <div class="warning-icon">⚠️</div>
  <div class="warning-content">
    <h4>版面配置警告</h4>
    <p>內容超出A4頁面範圍 ({{ overflowAmount }}mm)</p>
    <div class="warning-actions">
      <button @click="autoAdjust">🔧 自動調整</button>
      <button @click="multiPage">📄 多頁模式</button>
      <button @click="ignoreWarning">❌ 忽略</button>
    </div>
  </div>
</div>
```

#### Accessibility Requirements:

- ARIA labels and roles for all interactive elements
- Keyboard navigation support (Tab, Enter, Escape, Arrow keys)
- Screen reader announcements for state changes
- High contrast mode support
- Focus management within modal

#### Sample Data for Testing:

```javascript
const samplePOData = {
  purchase_order_no: "P20240001",
  supplier_id: "S001",
  supplier_name: "ABC Office Equipment Co., Ltd.",
  supplier_address: "台北市信義區信義路五段7號",
  contact_person: "王小明",
  contact_phone: "02-1234-5678",
  order_date: "2024-01-15",
  quotation_no: "Q20240001",
  purchase_status: "order_created",
  subtotal_int: 90000,
  tax_decimal1: 4500,
  grand_total_int: 94500,
  items: [
    {
      item_name: "高級辦公椅",
      item_specification: "人體工學設計，可調整高度",
      item_model: "AC-2024",
      item_quantity: 10,
      item_unit: "張",
      unit_price: 5000,
      line_subtotal: 50000
    },
    {
      item_name: "辦公桌",
      item_specification: "L型設計，含抽屜",
      item_model: "DK-180",
      item_quantity: 5,
      item_unit: "張", 
      unit_price: 8000,
      line_subtotal: 40000
    }
    // Add more items for testing overflow scenarios
  ]
}
```

#### Implementation Notes:

1. **Start with the basic modal structure** with three view mode tabs
2. **Implement the A4 print preview simulation** with exact dimensions
3. **Create the responsive table layout** with optimized column widths  
4. **Add the currency formatting optimization** for print vs screen
5. **Implement zoom controls** with smooth scaling
6. **Add content overflow detection** with visual warnings
7. **Test thoroughly** across different screen sizes and print scenarios

#### Success Criteria:
- [ ] All content fits within A4 boundaries at 100% zoom
- [ ] Print preview matches actual print output
- [ ] Currency columns align perfectly in all zoom levels
- [ ] Modal is fully responsive on mobile devices
- [ ] Loading states and error handling work smoothly
- [ ] Accessibility standards are met (WCAG 2.1 AA)

This prompt provides comprehensive specifications for creating a professional, print-optimized Purchase Order Preview Modal that solves all the identified UX issues while maintaining excellent usability across all device types.