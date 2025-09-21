# Purchase Order Output UI/UX Specification

## Overview

This specification defines the complete user interface and user experience design for the purchase order output functionality in the ERP system. The design maintains consistency with the existing Element Plus-based UI architecture while introducing new interactive elements for purchase order document generation and status management.

## Design System Foundation

### Color Palette
- **Primary**: #409eff (Element Plus primary blue)
- **Success**: #67c23a (Green for successful actions)
- **Warning**: #e6a23c (Orange for pending actions)
- **Danger**: #f56c6c (Red for critical actions)
- **Info**: #909399 (Gray for informational elements)
- **Background**: #f5f7fa (Light gray for containers)
- **Text Primary**: #303133 (Dark gray for headers)
- **Text Secondary**: #606266 (Medium gray for descriptions)

### Typography
- **Headers**: 24px, font-weight: 500, color: #303133
- **Subheaders**: 16px, font-weight: 500, color: #303133
- **Body Text**: 14px, color: #606266
- **Button Text**: 14px, font-weight: 500
- **Labels**: 14px, font-weight: 400, color: #606266

### Spacing
- **Container Padding**: 20px
- **Element Margins**: 8px, 12px, 16px, 20px
- **Card Border Radius**: 4px
- **Button Border Radius**: 4px

## 1. Purchase Order List Enhancements

### 1.1 Output Button Design

#### Visual Design
- **Button Text**: "輸出採購單" (Output Purchase Order)
- **Button Type**: Primary button with custom styling
- **Icon**: Document export icon (el-icon-download or el-icon-document-copy)
- **Size**: Small (height: 32px)
- **Color**: Primary blue (#409eff)
- **Hover State**: Darker blue (#337ecc)
- **Disabled State**: Light gray (#c0c4cc) with opacity 0.6

#### Placement
- **Location**: Action column (rightmost column) in the purchase order table
- **Order**: After "詳情" (Detail) button, before "編輯" (Edit) button
- **Alignment**: Left-aligned with other action buttons
- **Spacing**: 8px gap between buttons

#### Visibility Rules
```typescript
// Show output button only for eligible statuses
const canOutputPO = (status: string): boolean => {
  return ['pending', 'order_created'].includes(status)
}
```

#### Button Component Structure
```vue
<el-button
  v-if="canOutputPO(row.status)"
  size="small"
  type="primary"
  :icon="Download"
  @click.stop="handleOutputPO(row)"
  class="output-button"
>
  輸出採購單
</el-button>
```

### 1.2 Table Column Updates

#### Action Column Width
- **Current Width**: 150px
- **New Width**: 200px (to accommodate new button)

#### Status Column Enhancement
- **Add new status indicators**:
  - `pending`: Orange tag "待處理"
  - `order_created`: Blue tag "已製單" 
  - `confirmed`: Green tag "已確認"
  - `purchased`: Success tag "已採購"

## 2. Purchase Order Preview Modal

### 2.1 Modal Design Specifications

#### Modal Container
- **Width**: 1200px (large modal for document preview)
- **Min-Height**: 700px
- **Max-Height**: 90vh (scrollable if content exceeds)
- **Background**: White
- **Border Radius**: 8px
- **Box Shadow**: 0 4px 12px rgba(0, 0, 0, 0.15)
- **Overlay**: Dark backdrop with 50% opacity

#### Modal Header
- **Title**: "採購單預覽" (Purchase Order Preview)
- **Font Size**: 18px
- **Font Weight**: 600
- **Color**: #303133
- **Background**: White with bottom border (1px solid #ebeef5)
- **Padding**: 16px 24px
- **Close Button**: Standard Element Plus close icon (top-right)

#### Modal Body Structure
```html
<div class="po-preview-body">
  <!-- Company Header -->
  <div class="company-header">...</div>
  
  <!-- Document Info Section -->
  <div class="document-info">...</div>
  
  <!-- Supplier Info Section -->
  <div class="supplier-info">...</div>
  
  <!-- Items Table -->
  <div class="items-section">...</div>
  
  <!-- Financial Summary -->
  <div class="financial-summary">...</div>
  
  <!-- Terms and Footer -->
  <div class="document-footer">...</div>
</div>
```

### 2.2 Preview Content Layout

#### Company Header Section
- **Company Name**: "百兆豐國際有限公司"
- **Document Title**: "採購單" (large, centered)
- **Logo Placeholder**: 64x64px square on the left
- **Styling**: Centered layout with consistent brand colors

#### Document Information Grid
```css
.document-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin: 24px 0;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 4px;
}
```

**Left Column - Supplier Information**:
- 廠商名稱 (Supplier Name)
- 廠商編號 (Supplier ID)  
- 廠商地址 (Supplier Address)
- 連絡電話 (Contact Phone)
- 聯絡人 (Contact Person)

**Right Column - Order Information**:
- 訂購日期 (Order Date)
- 報價單號 (Quotation Number)
- 採購單號 (Purchase Order Number)

#### Items Table Design
- **Table Style**: Bordered table with alternating row colors
- **Header Background**: #f5f7fa
- **Border**: 1px solid #ebeef5
- **Cell Padding**: 12px 8px

**Table Columns**:
1. 項目 (Item Number) - 60px
2. 產品型號 (Product Model) - 120px
3. 名稱 (Name) - 150px
4. 規格 (Specification) - 120px
5. 數量 (Quantity) - 80px
6. 單位 (Unit) - 60px
7. 單價 (Unit Price) - 100px
8. 金額 (Amount) - 100px

#### Financial Summary Section
```css
.financial-summary {
  width: 300px;
  margin-left: auto;
  margin-top: 16px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 4px;
}
```

**Summary Rows**:
- 未稅金額 (NTD): Right-aligned currency format
- 稅金 5%: Right-aligned with 1 decimal place
- 合計: Bold text, larger font, right-aligned

### 2.3 Modal Footer Actions

#### Button Layout
```css
.modal-footer {
  display: flex;
  justify-content: space-between;
  padding: 16px 24px;
  background: #f8f9fa;
  border-top: 1px solid #ebeef5;
}
```

#### Left Side - Cancel Action
- **Cancel Button**: Secondary button "取消"
- **Icon**: Close icon
- **Action**: Close modal without action

#### Right Side - Export Actions
```html
<div class="export-actions">
  <el-button
    type="success"
    :icon="DocumentCopy"
    :loading="excelLoading"
    @click="exportExcel"
  >
    輸出 Excel
  </el-button>
  
  <el-button
    type="danger"
    :icon="Document"
    :loading="pdfLoading"
    @click="exportPDF"
  >
    輸出 PDF
  </el-button>
</div>
```

#### Loading States
- **Button Loading**: Show spinner icon with disabled state
- **Loading Text**: "處理中..." (Processing...)
- **Progress Indicator**: Optional progress bar for large files

## 3. Navigation Menu Enhancement

### 3.1 New Menu Item Design

#### Menu Item Properties
- **Text**: "確認採購狀態" (Confirm Purchase Status)
- **Icon**: CheckCircle or DocumentChecked icon
- **Placement**: Under "採購單管理" (Purchase Order Management) section
- **Route**: `/purchase-orders/confirm-status`

#### Icon Design
- **Size**: 20px
- **Color**: Inherit from parent menu styling
- **Active State**: Primary color (#409eff)

#### Menu Structure Update
```html
<el-menu-item-group title="採購管理">
  <el-menu-item index="/purchase-orders">
    <el-icon><List /></el-icon>
    <span>採購單列表</span>
  </el-menu-item>
  <el-menu-item index="/purchase-orders/build-candidates">
    <el-icon><DocumentCopy /></el-icon>
    <span>建立採購單</span>
  </el-menu-item>
  <el-menu-item index="/purchase-orders/confirm-status">
    <el-icon><CircleCheck /></el-icon>
    <span>確認採購狀態</span>
  </el-menu-item>
</el-menu-item-group>
```

## 4. Confirm Purchase Status Page

### 4.1 Page Layout Structure

#### Page Header
```css
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
```
- **Title**: "確認採購狀態" (24px, font-weight: 500)
- **Subtitle**: "管理已製單的採購單，確認採購狀態" (14px, color: #606266)

#### Filters Section (Optional)
```css
.filters {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 4px;
  margin-bottom: 20px;
}
```
- **Date Range Filter**: Order created date range
- **Supplier Filter**: Dropdown for specific supplier
- **Amount Filter**: Min/max amount range

### 4.2 Status List Table Design

#### Table Configuration
- **Loading State**: Skeleton loading for better UX
- **Empty State**: Custom illustration with "暫無待確認的採購單"
- **Row Hover**: Light background highlight
- **Row Selection**: Checkbox for batch operations (future enhancement)

#### Table Columns Specification

1. **採購單號 (PO Number)**
   - Width: 140px
   - Format: Clickable link to detail page
   - Color: Primary blue for links

2. **供應商 (Supplier)**
   - Width: 180px
   - Display: Supplier name with ID in parentheses
   - Truncate: Long names with tooltip

3. **金額 (Amount)**
   - Width: 120px
   - Format: Currency with NT$ prefix
   - Alignment: Right-aligned
   - Color: #606266

4. **製單日期 (Output Date)**
   - Width: 140px
   - Format: YYYY-MM-DD HH:mm
   - Color: #606266

5. **製單人員 (Output By)**
   - Width: 120px
   - Display: User name or ID
   - Color: #606266

6. **操作 (Actions)**
   - Width: 120px
   - Contains confirm button

#### Confirm Button Design
```vue
<el-button
  type="success"
  size="small"
  :icon="CircleCheck"
  @click="confirmPurchase(row)"
  :loading="row.confirming"
>
  確認採購
</el-button>
```

### 4.3 Confirmation Dialog

#### Dialog Properties
- **Type**: Warning confirmation dialog
- **Title**: "確認採購狀態"
- **Message**: "確認將採購單 {po_number} 標記為已採購？"
- **Description**: "此操作將把採購單狀態變更為「已採購」，並記錄確認人員和時間。"
- **Icon**: Warning icon (QuestionFilled)
- **Confirm Text**: "確認採購"
- **Cancel Text**: "取消"

#### Dialog Content
```html
<confirm-dialog
  v-model:visible="showConfirmDialog"
  type="warning"
  title="確認採購狀態"
  :message="`確認將採購單 ${selectedPO.po_number} 標記為已採購？`"
  description="此操作將把採購單狀態變更為「已採購」，並記錄確認人員和時間。"
  confirm-text="確認採購"
  cancel-text="取消"
  :loading="confirmLoading"
  @confirm="handleConfirmPurchase"
  @cancel="handleCancelConfirm"
/>
```

## 5. User Feedback and Interaction Flows

### 5.1 Success Messages

#### Export Success
```typescript
ElMessage({
  type: 'success',
  message: `採購單 ${poNumber} 已成功輸出為 ${fileType} 格式`,
  duration: 3000,
  showClose: true
})
```

#### Confirmation Success
```typescript
ElMessage({
  type: 'success',
  message: `採購單 ${poNumber} 狀態已確認為「已採購」`,
  duration: 3000,
  showClose: true
})
```

### 5.2 Loading States

#### Export Loading
- **Button Loading**: Spinner icon on export buttons
- **Modal Loading**: Overlay with loading spinner
- **Progress Text**: "正在生成文件，請稍候..." (Generating document, please wait...)

#### Table Loading
- **Skeleton Loading**: Use Element Plus skeleton components
- **Rows**: Show 5 skeleton rows while loading
- **Columns**: Match actual table structure

### 5.3 Error States

#### Export Error
```typescript
ElMessage({
  type: 'error',
  message: '文件生成失敗，請檢查網路連接後重試',
  duration: 5000,
  showClose: true
})
```

#### Network Error
```typescript
ElNotification({
  type: 'error',
  title: '網路錯誤',
  message: '無法連接到伺服器，請檢查網路連接',
  duration: 0, // Manual close
  position: 'top-right'
})
```

### 5.4 Empty States

#### No Orders to Confirm
```html
<el-empty
  image="https://shadow.elemecdn.com/app/element/hamburger.9cf7b091-55e9-11e9-a976-7f4d0b07eef6.png"
  description="暫無待確認的採購單"
>
  <template #extra>
    <el-button type="primary" @click="refreshData">
      重新整理
    </el-button>
  </template>
</el-empty>
```

## 6. Responsive Design Considerations

### 6.1 Mobile Adaptations (≤768px)

#### Preview Modal
- **Width**: 95vw (full width with margin)
- **Height**: 90vh (full height)
- **Scrollable**: Vertical scroll for all content
- **Button Stack**: Export buttons stacked vertically

#### Table Adaptations
- **Hidden Columns**: Hide less critical columns on mobile
- **Priority Order**: PO Number > Supplier > Amount > Actions
- **Responsive Table**: Horizontal scroll for full table view

### 6.2 Tablet Adaptations (768px-1024px)

#### Modal Adjustments
- **Width**: 90vw (responsive width)
- **Maintain**: Two-column layout for document info
- **Font Scaling**: Slightly smaller fonts if needed

## 7. Accessibility Considerations

### 7.1 Keyboard Navigation
- **Tab Order**: Logical tab sequence through modal elements
- **Enter Key**: Confirm actions on focused buttons
- **Escape Key**: Close modals and cancel operations

### 7.2 Screen Reader Support
- **ARIA Labels**: Proper labels for all interactive elements
- **Live Regions**: Announce status changes and loading states
- **Semantic HTML**: Use proper heading hierarchy

### 7.3 Color and Contrast
- **High Contrast**: Ensure 4.5:1 contrast ratio for all text
- **Color Independence**: Don't rely solely on color for information
- **Focus Indicators**: Clear focus rings for keyboard users

## 8. Animation and Transitions

### 8.1 Modal Animations
- **Enter**: Fade in with slight scale (0.9 to 1.0)
- **Exit**: Fade out with scale (1.0 to 0.9)
- **Duration**: 300ms ease-out

### 8.2 Button States
- **Hover**: Smooth color transition (200ms)
- **Loading**: Smooth spinner rotation
- **Success**: Brief scale animation on success

### 8.3 Table Updates
- **Row Addition**: Slide in from top
- **Status Change**: Color transition for status tags
- **Loading**: Skeleton fade-in/out

## Implementation Notes for Developer

### Vue.js Components to Use

#### Core Components
```typescript
// Element Plus Components
import {
  ElDialog,
  ElTable,
  ElTableColumn,
  ElButton,
  ElTag,
  ElMessage,
  ElNotification,
  ElEmpty,
  ElSkeleton,
  ElLoading
} from 'element-plus'

// Icons
import {
  Download,
  Document,
  DocumentCopy,
  CircleCheck,
  QuestionFilled,
  Close
} from '@element-plus/icons-vue'
```

#### Custom Components
1. **PurchaseOrderPreview.vue**: Main preview modal component
2. **ExportActions.vue**: Export button group component
3. **ConfirmPurchaseDialog.vue**: Status confirmation dialog
4. **POStatusTag.vue**: Enhanced status tag component

### State Management with Pinia

#### Store Structure
```typescript
// stores/purchaseOrderOutput.ts
export const usePurchaseOrderOutputStore = defineStore('purchaseOrderOutput', {
  state: () => ({
    previewModalVisible: false,
    currentPO: null as PurchaseOrder | null,
    exportLoading: {
      excel: false,
      pdf: false
    },
    confirmationOrders: [] as PurchaseOrder[],
    confirmLoading: false
  }),
  
  actions: {
    async previewPO(poId: string) { /* ... */ },
    async exportExcel(poId: string) { /* ... */ },
    async exportPDF(poId: string) { /* ... */ },
    async confirmPurchase(poId: string) { /* ... */ }
  }
})
```

### API Integration Points

#### New API Endpoints Required
```typescript
// api/procurement.ts additions
export const procurementApi = {
  // ... existing methods
  
  // Preview purchase order data
  previewPO: async (poNo: string): Promise<PurchaseOrderPreview> => {
    const response = await api.get(`/po/${poNo}/preview`)
    return response.data
  },
  
  // Export purchase order
  exportPO: async (poNo: string, format: 'excel' | 'pdf'): Promise<Blob> => {
    const response = await api.post(`/po/${poNo}/export`, 
      { format }, 
      { responseType: 'blob' }
    )
    return response.data
  },
  
  // Get orders awaiting confirmation
  getPendingConfirmation: async (): Promise<PurchaseOrder[]> => {
    const response = await api.get('/po/pending-confirmation')
    return response.data
  },
  
  // Confirm purchase status
  confirmPurchaseStatus: async (poNo: string): Promise<PurchaseOrder> => {
    const response = await api.post(`/po/${poNo}/confirm-purchase`)
    return response.data
  }
}
```

### File Download Handling

```typescript
// utils/fileDownload.ts
export const downloadFile = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

// Usage in component
const handleExportExcel = async (poNumber: string) => {
  try {
    exportLoading.value.excel = true
    const blob = await procurementApi.exportPO(poNumber, 'excel')
    downloadFile(blob, `採購單_${poNumber}.xlsx`)
    ElMessage.success(`採購單 ${poNumber} 已成功輸出為 Excel 格式`)
  } catch (error) {
    ElMessage.error('Excel 輸出失敗，請重試')
  } finally {
    exportLoading.value.excel = false
  }
}
```

### Error Handling Best Practices

```typescript
// composables/useErrorHandler.ts
export const useErrorHandler = () => {
  const handleError = (error: any, context: string) => {
    console.error(`Error in ${context}:`, error)
    
    if (error.response?.status === 403) {
      ElMessage.error('您沒有執行此操作的權限')
    } else if (error.response?.status === 404) {
      ElMessage.error('找不到相關資料')
    } else if (error.code === 'NETWORK_ERROR') {
      ElNotification({
        type: 'error',
        title: '網路錯誤',
        message: '無法連接到伺服器，請檢查網路連接',
        duration: 0
      })
    } else {
      ElMessage.error('操作失敗，請重試')
    }
  }
  
  return { handleError }
}
```

### Performance Optimization

#### Lazy Loading
```typescript
// Lazy load preview modal
const PurchaseOrderPreview = defineAsyncComponent(
  () => import('@/components/PurchaseOrderPreview.vue')
)
```

#### Virtual Scrolling (for large lists)
```vue
<el-virtual-list
  :data="confirmationOrders"
  :height="400"
  :item-size="60"
  :key-field="'id'"
>
  <template #default="{ item }">
    <POConfirmationRow :order="item" />
  </template>
</el-virtual-list>
```

### Testing Considerations

#### Component Testing
```typescript
// tests/components/PurchaseOrderPreview.test.ts
describe('PurchaseOrderPreview', () => {
  it('should display purchase order information correctly', () => {
    // Test preview content rendering
  })
  
  it('should handle export actions properly', async () => {
    // Test export functionality
  })
  
  it('should handle loading states', () => {
    // Test loading indicators
  })
})
```

#### E2E Testing Scenarios
1. **Preview Flow**: Open preview modal, verify content, export files
2. **Confirmation Flow**: Navigate to confirmation page, confirm orders
3. **Error Scenarios**: Network errors, permission errors, validation errors
4. **Responsive**: Test on different screen sizes

This comprehensive UI/UX specification provides detailed guidance for implementing the purchase order output functionality while maintaining consistency with the existing ERP system design language and ensuring excellent user experience across all interaction points.