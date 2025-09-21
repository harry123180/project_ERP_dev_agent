# Purchase Order Preview Modal - Wireframes & Visual Specifications

## Overview
This document provides detailed wireframes, visual specifications, and interaction patterns for the redesigned Purchase Order Preview Modal across all viewing modes and device types.

## Modal Architecture Overview

### Component Hierarchy
```
PreviewModal
├── ModalHeader (Title, Status, Close)
├── NavigationBar (View Mode Tabs, Controls)
├── PreviewContainer (Main Content Area)
│   ├── DocumentContent (Printable Area)
│   └── AdditionalInfo (Screen-only Content)
├── ControlPanel (Zoom, Settings, Actions)
└── ModalFooter (Primary Actions, Status)
```

## Wireframe Specifications

### 1. Desktop Edit Mode (Default View)
**Dimensions**: 1400px width × 900px height

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 採購單預覽 Purchase Order Preview                        [Status] [Help] [×]     │
├─────────────────────────────────────────────────────────────────────────────────┤
│ [編輯模式] [列印預覽] [匯出模式]     |  🔍 100% ▼  📄 1/1  ⚙️ 設定             │ 50px
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─── Document Preview Area (Scrollable Content) ─────────────────────────┐     │
│  │                                                                        │     │
│  │  ┌─ Company Header ────────────────────────────────────────────────┐   │     │
│  │  │ [TSIC Logo]           採購單              [Status: 已建立]       │   │     │ 80px
│  │  │                   PURCHASE ORDER                                │   │     │
│  │  └────────────────────────────────────────────────────────────────┘   │     │
│  │                                                                        │     │
│  │  ┌─ Supplier Information Table ─────────────────────────────────────┐   │     │
│  │  │ 廠商名稱  │ ABC Company Ltd    │ 採購單號 │ P20240001           │   │     │ 100px
│  │  │ 廠商編號  │ S001              │ 訂購日期 │ 2024/01/15          │   │     │
│  │  │ 廠商地址  │ 台北市信義區...    │ 報價單號 │ [    輸入欄位    ] │   │     │
│  │  │ 連絡電話  │ 02-1234-5678      │ 聯絡人   │ 王小明              │   │     │
│  │  └────────────────────────────────────────────────────────────────┘   │     │
│  │                                                                        │     │
│  │  ┌─ Purchase Items Table ────────────────────────────────────────────┐   │     │
│  │  │ 項次│品名        │規格      │型號    │數量  │單位│單價    │小計    │   │     │
│  │  │────┼──────────┼────────┼──────┼────┼──┼──────┼──────│   │     │ 300px
│  │  │  1 │高級辦公椅  │人體工學  │AC-2024 │ 10  │張 │$5,000 │$50,000│   │     │ Variable
│  │  │  2 │辦公桌     │L型       │DK-180  │  5  │張 │$8,000 │$40,000│   │     │
│  │  │ ...│...        │...       │...     │ ... │..│...    │...    │   │     │
│  │  └────────────────────────────────────────────────────────────────┘   │     │
│  │                                                                        │     │
│  │  ┌─ Totals Section ──────────────────────────────────────────────────┐   │     │
│  │  │                                          小計：    $90,000       │   │     │ 60px
│  │  │                                          稅額：     $4,500       │   │     │
│  │  │                                          總計：    $94,500       │   │     │
│  │  └────────────────────────────────────────────────────────────────┘   │     │
│  │                                                                        │     │
│  │  ┌─ Terms & Conditions ──────────────────────────────────────────────┐   │     │
│  │  │ 注意事項 Terms and Conditions        [模板選擇 ▼] [自訂]        │   │     │ 120px
│  │  │ ┌──────────────────────────────────────────────────────────────┐ │   │     │
│  │  │ │ 1. 付款條件：月結 30 天                                      │ │   │     │
│  │  │ │ 2. 交貨期限：訂單確認後 14 個工作天                          │ │   │     │
│  │  │ │ 3. 品質要求：須符合國家標準規範                              │ │   │     │
│  │  │ │ 4. 驗收標準：貨到 7 日內完成驗收                            │ │   │     │
│  │  │ │ 5. 保固期限：自驗收合格日起算一年                            │ │   │     │
│  │  │ └──────────────────────────────────────────────────────────────┘ │   │     │
│  │  └────────────────────────────────────────────────────────────────┘   │     │
│  │                                                                        │     │
│  │  ┌─ Signature Section ───────────────────────────────────────────────┐   │     │
│  │  │ 採購人員：________________    核准主管：________________        │   │     │ 60px
│  │  │ 日期：____________            日期：____________                │   │     │
│  │  └────────────────────────────────────────────────────────────────┘   │     │
│  │                                                                        │     │
│  │  ────────────────── 以下內容不包含在列印輸出中 ──────────────────────    │     │
│  │                                                                        │     │
│  │  ┌─ Additional Information (Screen Only) ───────────────────────────┐   │     │
│  │  │ 📋 交貨資訊 Delivery Information                                 │   │     │ 150px
│  │  │ 📍 交貨地址：台北市信義區信義路五段7號                           │   │     │
│  │  │ 📅 預計交貨日期：訂單確認後 14 個工作天                          │   │     │
│  │  │                                                                  │   │     │
│  │  │ 🏢 供應商詳細資訊 Supplier Details                              │   │     │
│  │  │ 統一編號：12345678   電子郵件：contact@supplier.com.tw          │   │     │
│  │  └──────────────────────────────────────────────────────────────────┘   │     │
│  │                                                                        │     │
│  └────────────────────────────────────────────────────────────────────────┘     │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│ [關閉]  [列印預覽] [輸出Excel] [輸出PDF] [列印]                              │ 60px
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Key Features**:
- Scrollable content area for full document review
- Editable fields clearly marked with input styling
- Clear visual separation between printable and screen-only content
- Status information prominently displayed
- Progressive disclosure with expandable sections

### 2. Desktop Print Preview Mode
**Dimensions**: 1400px width × 900px height

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 列印預覽模式 Print Preview Mode                              [Help] [×]         │
├─────────────────────────────────────────────────────────────────────────────────┤
│ [返回編輯] [列印預覽] [匯出模式]  |  🔍 75% ▼  📄 1/1 ◄►  📏 顯示邊界  ⚙️      │ 50px
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│           ┌───── A4 Page Simulation (210mm × 297mm) ──────┐                    │
│           │ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │                    │
│           │ ┃                                          ┃ │                    │
│           │ ┃  [TSIC]      採購單        [已建立]      ┃ │                    │
│           │ ┃           PURCHASE ORDER                 ┃ │                    │
│           │ ┃ ─────────────────────────────────────────┃ │                    │
│           │ ┃                                          ┃ │                    │
│           │ ┃ ┌─廠商資訊─┬─────────┬─PO資訊─┬───────┐ ┃ │                    │
│           │ ┃ │廠商名稱  │ABC Co   │採購單號│P20240001│ ┃ │                    │
│           │ ┃ │廠商編號  │S001     │訂購日期│01/15    │ ┃ │                    │
│           │ ┃ │廠商地址  │台北...  │報價單號│Q001     │ ┃ │                    │
│           │ ┃ │連絡電話  │02-1234  │聯絡人  │王小明   │ ┃ │                    │
│           │ ┃ └─────────┴─────────┴───────┴───────┘ ┃ │                    │
│           │ ┃                                          ┃ │                    │
│           │ ┃ 採購明細 Purchase Items                   ┃ │                    │
│           │ ┃ ┌─┬─────────┬──────┬──────┬───┬─┬────┐ ┃ │                    │
│           │ ┃ │項│品名     │規格  │型號  │數量│單│單價│ ┃ │                    │
│           │ ┃ ├─┼─────────┼──────┼──────┼───┼─┼────┤ ┃ │                    │
│           │ ┃ │1│高級辦公椅│人體工學│AC-2024│10 │張│5000│ ┃ │                    │
│           │ ┃ │2│辦公桌   │L型    │DK-180 │5  │張│8000│ ┃ │                    │
│           │ ┃ │3│電腦螢幕 │24吋   │MON-24 │8  │台│3000│ ┃ │                    │
│           │ ┃ │.│...      │...    │...    │.. │..│... │ ┃ │                    │
│           │ ┃ └─┴─────────┴──────┴──────┴───┴─┴────┘ ┃ │                    │
│           │ ┃                                          ┃ │                    │
│           │ ┃                              小計：90000 ┃ │                    │
│           │ ┃                              稅額： 4500 ┃ │                    │
│           │ ┃                              總計：94500 ┃ │                    │
│           │ ┃                                          ┃ │                    │
│           │ ┃ 注意事項 Terms and Conditions             ┃ │                    │
│           │ ┃ 1. 付款條件：月結 30 天                  ┃ │                    │
│           │ ┃ 2. 交貨期限：訂單確認後 14 個工作天      ┃ │                    │
│           │ ┃ 3. 品質要求：須符合國家標準規範          ┃ │                    │
│           │ ┃                                          ┃ │                    │
│           │ ┃ 採購人員：________  核准主管：________   ┃ │                    │
│           │ ┃ 日期：______      日期：______         ┃ │                    │ 
│           │ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │                    │
│           └──────────────────────────────────────────────┘                    │
│                                                                                 │
│  🔍 Zoom: 50% | 75% | 100% | 125% | 150%    📐 Page Boundaries: ON             │
│  📏 Ruler Guide: OFF    🎯 Safe Zone: OFF    📄 Page 1 of 1                    │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│ [返回編輯] [列印設定] [列印] [另存PDF] [分享連結]                              │ 60px
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Key Features**:
- WYSIWYG A4 page representation with exact proportions
- Clear page boundaries with visual indicators
- Zoom controls for detailed inspection
- Print-optimized typography and spacing
- Real-time content fitting feedback

### 3. Tablet View (768px - 1199px)

```
┌─────────────────────────────────────────────┐
│ 採購單預覽                         [×]      │
├─────────────────────────────────────────────┤
│ [編輯] [預覽] [匯出]     🔍 75%  📄 1/1   │ 40px
├─────────────────────────────────────────────┤
│                                             │
│  ┌─ Document Content (Stacked Layout) ─┐   │
│  │                                     │   │
│  │  [TSIC]    採購單        [Status]   │   │ 60px
│  │         PURCHASE ORDER              │   │
│  │  ─────────────────────────────────  │   │
│  │                                     │   │
│  │  ┌─ Supplier Info (2×4 Grid) ────┐  │   │
│  │  │ 廠商名稱  │ ABC Company Ltd  │  │   │ 80px
│  │  │ 採購單號  │ P20240001        │  │   │
│  │  │ 廠商編號  │ S001             │  │   │
│  │  │ 訂購日期  │ 2024/01/15       │  │   │
│  │  └─────────────────────────────────┘  │   │
│  │                                     │   │
│  │  ── More Info (Accordion) ──       │   │ 20px
│  │                                     │   │
│  │  ┌─ Items (Simplified Table) ────┐  │   │
│  │  │ 1. 高級辦公椅 × 10        50K │  │   │
│  │  │ 2. 辦公桌 × 5            40K │  │   │ Variable
│  │  │ 3. 電腦螢幕 × 8           24K │  │   │
│  │  │ ... (點擊查看全部)           │  │   │
│  │  └─────────────────────────────────┘  │   │
│  │                                     │   │
│  │  總計：$94,500                      │   │ 30px
│  │                                     │   │
│  │  ── Terms (Collapsed) ──           │   │ 20px
│  │                                     │   │
│  └─────────────────────────────────────┘   │
│                                             │
├─────────────────────────────────────────────┤
│ [關閉] [列印預覽] [Export ▼] [列印]        │ 50px
└─────────────────────────────────────────────┘
```

**Key Adaptations**:
- Stacked layout instead of side-by-side
- Accordion sections for optional content
- Simplified table view with expandable details
- Touch-optimized control sizes (44px minimum)
- Reduced modal chrome for content focus

### 4. Mobile View (<768px)

```
┌─────────────────────────────────┐
│ ≡ 採購單預覽              [×]  │ 44px
├─────────────────────────────────┤
│ ● 編輯 ○ 預覽 ○ 匯出           │ 40px
├─────────────────────────────────┤
│                                 │
│ [TSIC]     採購單      [狀態]   │ 50px
│         PURCHASE ORDER          │
│ ─────────────────────────────── │
│                                 │
│ 📋 基本資訊                     │ 30px
│ 廠商：ABC Company Ltd           │
│ 單號：P20240001                 │
│ 日期：2024/01/15                │
│ [👁 展開詳細資訊]                │ 20px
│                                 │
│ 📦 採購項目 (3項)               │ 30px
│ ┌─────────────────────────────┐ │
│ │ 1. 高級辦公椅 × 10          │ │
│ │    NT$ 5,000 → $50,000     │ │ 60px
│ │ ────────────────────────────│ │
│ │ 2. 辦公桌 × 5               │ │
│ │    NT$ 8,000 → $40,000     │ │ 60px
│ │ ────────────────────────────│ │
│ │ [+展開查看更多項目]          │ │ 30px
│ └─────────────────────────────┘ │
│                                 │
│ 💰 金額總計                     │ 30px
│ 小計：$90,000                   │
│ 稅額：$4,500                    │
│ 總計：$94,500                   │ 20px each
│                                 │
│ 📄 條款說明                     │ 30px
│ [展開查看詳細條款]              │ 20px
│                                 │
├─────────────────────────────────┤
│ [🖨 列印] [📤 分享] [💾 存檔]     │ 50px
└─────────────────────────────────┘
```

**Mobile Optimizations**:
- Hamburger menu for navigation
- Card-based information presentation
- Swipe gestures for view switching
- Thumb-friendly button placement
- Progressive disclosure for complex data
- Single-column layout throughout

## Interactive States and Behaviors

### Loading States

#### Initial Load
```
┌─────────────────────────────────────────────┐
│ 採購單預覽 - 載入中...                      │
├─────────────────────────────────────────────┤
│                                             │
│         ⌛ 正在載入採購單資料...             │
│                                             │
│         ████████████░░░░░░░░ 60%            │
│                                             │
│         📄 P20240001 - ABC Company          │
│                                             │
└─────────────────────────────────────────────┘
```

#### Print Preview Generation
```
┌─────────────────────────────────────────────┐
│ 正在產生列印預覽...                         │
├─────────────────────────────────────────────┤
│                                             │
│         🖨 正在最佳化版面配置...             │
│                                             │
│         ████████░░░░░░░░░░░░ 40%            │
│                                             │
│         預計完成時間：3秒                   │
│                                             │
└─────────────────────────────────────────────┘
```

### Error States

#### Content Overflow Warning
```
┌─────────────────────────────────────────────┐
│ ⚠️ 版面配置警告                             │
├─────────────────────────────────────────────┤
│                                             │
│ 🚨 內容超出A4頁面範圍                       │
│                                             │
│ 問題：採購項目過多 (18項 > 15項建議)       │
│ 建議：                                      │
│ • 分成兩頁列印                              │
│ • 調整字體大小                              │
│ • 簡化項目描述                              │
│                                             │
│ [🔧 自動調整] [📄 多頁模式] [❌ 忽略]       │
│                                             │
└─────────────────────────────────────────────┘
```

#### Network Error
```
┌─────────────────────────────────────────────┐
│ ❌ 載入失敗                                 │
├─────────────────────────────────────────────┤
│                                             │
│         🌐 網路連線異常                     │
│                                             │
│         無法載入採購單 P20240001            │
│         請檢查網路連線後重試                │
│                                             │
│         [🔄 重新載入] [❌ 關閉]              │
│                                             │
└─────────────────────────────────────────────┘
```

### Success States

#### Export Success
```
┌─────────────────────────────────────────────┐
│ ✅ 輸出成功                                 │
├─────────────────────────────────────────────┤
│                                             │
│         📄 採購單 P20240001 已輸出PDF       │
│                                             │
│         檔案大小：1.2MB                     │
│         輸出時間：2024/01/15 14:30          │
│                                             │
│         [📁 開啟資料夾] [📤 分享] [❌ 關閉]   │
│                                             │
└─────────────────────────────────────────────┘
```

### Animation Specifications

#### View Mode Transitions
```css
.mode-transition {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    transform-origin: center center;
}

.edit-to-preview {
    transform: scale(0.85) translateY(-20px);
    opacity: 0;
}

.preview-enter {
    transform: scale(1) translateY(0);
    opacity: 1;
}
```

#### Zoom Transitions
```css
.zoom-transition {
    transition: transform 0.4s ease-out;
    transform-origin: center top;
}

.zoom-50 { transform: scale(0.5); }
.zoom-75 { transform: scale(0.75); }
.zoom-100 { transform: scale(1); }
.zoom-125 { transform: scale(1.25); }
.zoom-150 { transform: scale(1.5); }
```

#### Loading Animations
```css
@keyframes loadingPulse {
    0% { opacity: 0.4; }
    50% { opacity: 1; }
    100% { opacity: 0.4; }
}

.loading-skeleton {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: loadingPulse 2s infinite;
}
```

## Accessibility Specifications

### Keyboard Navigation
```
Tab Order:
1. Modal Header Controls (Help, Close)
2. Navigation Tabs (Edit, Preview, Export)  
3. Zoom Controls
4. Page Navigation
5. Settings Button
6. Document Content (if focusable)
7. Footer Action Buttons

Keyboard Shortcuts:
ESC: Close modal
SPACE: Toggle print preview
+/-: Zoom in/out
←→: Navigate pages
ENTER: Confirm actions
```

### Screen Reader Support
```html
<!-- Modal Accessibility -->
<div role="dialog" 
     aria-labelledby="modal-title" 
     aria-describedby="modal-description"
     aria-modal="true">

<!-- Tab Navigation -->
<div role="tablist" aria-label="Preview modes">
    <button role="tab" aria-selected="true" aria-controls="edit-panel">
        編輯模式
    </button>
    <button role="tab" aria-selected="false" aria-controls="preview-panel">
        列印預覽
    </button>
</div>

<!-- Content Areas -->
<div role="tabpanel" id="edit-panel" aria-labelledby="edit-tab">
    <!-- Edit content -->
</div>

<!-- Status Announcements -->
<div aria-live="polite" aria-atomic="true" class="sr-only">
    <!-- Dynamic status updates -->
</div>
```

### Color and Contrast

#### Color Palette
```scss
// Primary Colors
$primary-blue: #409eff;      // Buttons, links
$success-green: #67c23a;     // Success states
$warning-orange: #e6a23c;    // Warnings
$danger-red: #f56c6c;        // Errors
$info-blue: #909399;         // Information

// Neutral Colors  
$text-primary: #303133;      // Main text (4.5:1 contrast)
$text-regular: #606266;      // Secondary text (3:1 contrast)
$text-secondary: #909399;    // Placeholder text (3:1 contrast)
$border-base: #dcdfe6;       // Borders
$background-base: #f5f7fa;   // Backgrounds

// Print Colors
$print-black: #000000;       // Print text
$print-border: #333333;      // Print borders
$print-background: #f0f0f0;  // Print table headers
```

#### High Contrast Mode Support
```css
@media (prefers-contrast: high) {
    .preview-modal {
        --text-color: #000000;
        --background-color: #ffffff;
        --border-color: #000000;
        border: 2px solid var(--border-color);
    }
    
    .status-badge {
        border: 2px solid currentColor;
    }
}
```

## Component Implementation Guide

### Vue 3 Component Structure
```typescript
// PreviewModal.vue
<template>
  <el-dialog 
    v-model="visible"
    :width="modalWidth"
    :fullscreen="isMobile"
    custom-class="po-preview-modal"
    @close="handleClose"
  >
    <template #header>
      <PreviewHeader 
        :title="modalTitle"
        :status="poData.status"
        @help="showHelp"
      />
    </template>
    
    <PreviewNavigation 
      v-model:mode="currentMode"
      v-model:zoom="currentZoom"
      :pages="totalPages"
      :current-page="currentPage"
      @mode-change="handleModeChange"
      @zoom-change="handleZoomChange"
    />
    
    <PreviewContainer 
      :mode="currentMode"
      :zoom="currentZoom"
      :data="poData"
      @content-overflow="handleContentOverflow"
    >
      <DocumentContent :data="poData" />
      <AdditionalInfo v-if="currentMode === 'edit'" :data="poData" />
    </PreviewContainer>
    
    <template #footer>
      <PreviewActions 
        :mode="currentMode"
        :can-export="canExport"
        @print="handlePrint"
        @export="handleExport"
        @close="handleClose"
      />
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useBreakpoints } from '@/composables/useBreakpoints'

// Component imports
import PreviewHeader from './components/PreviewHeader.vue'
import PreviewNavigation from './components/PreviewNavigation.vue'
import PreviewContainer from './components/PreviewContainer.vue'
import DocumentContent from './components/DocumentContent.vue'
import AdditionalInfo from './components/AdditionalInfo.vue'
import PreviewActions from './components/PreviewActions.vue'

// Types
interface PreviewMode = 'edit' | 'preview' | 'export'

// Props & Emits
const props = defineProps<{
  visible: boolean
  poNo: string
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'exported': []
}>()

// Responsive breakpoints
const { isMobile, isTablet, isDesktop } = useBreakpoints()

// Modal configuration
const modalWidth = computed(() => {
  if (isMobile.value) return '100%'
  if (isTablet.value) return '95%'
  return '1400px'
})

// State management
const currentMode = ref<PreviewMode>('edit')
const currentZoom = ref(100)
const currentPage = ref(1)
const totalPages = ref(1)

// Mode switching with animations
const handleModeChange = (mode: PreviewMode) => {
  currentMode.value = mode
  // Trigger appropriate animations
}

// Zoom handling
const handleZoomChange = (zoom: number) => {
  currentZoom.value = zoom
  // Recalculate layout if needed
}

// Content overflow detection
const handleContentOverflow = (overflow: boolean) => {
  if (overflow) {
    // Show warning and suggestions
  }
}
</script>
```

This comprehensive wireframe and specification document provides all the visual and functional details needed to implement the redesigned Purchase Order Preview Modal with professional UX standards and accessibility compliance.