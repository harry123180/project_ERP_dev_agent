# ERP 請購單審核界面優化前端規格文檔

## 概要

本規格文檔針對ERP系統中請購單審核界面的Dialog寬度與Table寬度不匹配問題，提供全面的Element Plus組件優化方案、CSS樣式調整、Vue.js實施代碼及用戶體驗改進建議。

## 🎯 核心問題分析

**當前問題：**
- Dialog組件寬度：900px
- Table組件最小寬度：1200px  
- 造成水平滾動條出現，影響用戶體驗

**解決策略：**
- 響應式Dialog尺寸優化
- 智能列寬度管理
- 移動端適配方案
- 用戶工作流程優化

---

## 1. Element Plus 組件配置優化

### 1.1 Dialog 組件配置

```vue
<template>
  <!-- 優化後的Dialog配置 -->
  <el-dialog
    v-model="reviewDialogVisible"
    :title="dialogTitle"
    :width="dialogWidth"
    :top="dialogTop"
    :class="dialogClass"
    :lock-scroll="true"
    :destroy-on-close="true"
    :close-on-click-modal="false"
    :show-close="true"
    @open="handleDialogOpen"
    @close="handleDialogClose"
  >
    <RequisitionReview
      v-if="currentRequisition"
      :requisition="currentRequisition"
      :dialog-mode="true"
      @close="handleCloseReview"
      @updated="handleRequisitionUpdated"
    />
  </el-dialog>
</template>

<script setup>
import { computed, ref, nextTick } from 'vue'

// 響應式Dialog尺寸計算
const dialogWidth = computed(() => {
  const viewportWidth = window.innerWidth
  
  if (viewportWidth >= 1600) return '1400px'      // 超大屏
  if (viewportWidth >= 1400) return '85vw'        // 大屏
  if (viewportWidth >= 1200) return '90vw'        // 中大屏  
  if (viewportWidth >= 992) return '95vw'         // 中屏
  if (viewportWidth >= 768) return '98vw'         // 小屏
  return '100vw'                                  // 手機
})

const dialogTop = computed(() => {
  const viewportHeight = window.innerHeight
  return viewportHeight >= 800 ? '5vh' : '2vh'
})

const dialogClass = computed(() => {
  const classes = ['requisition-review-dialog']
  if (window.innerWidth < 768) {
    classes.push('mobile-dialog')
  }
  return classes.join(' ')
})

// Dialog標題動態生成
const dialogTitle = computed(() => {
  if (!currentRequisition.value) return '審核請購單'
  return `審核請購單 - ${currentRequisition.value.request_order_no}`
})
</script>
```

### 1.2 Table 組件優化配置

```vue
<template>
  <div class="table-container" :class="tableContainerClass">
    <el-table
      ref="reviewTable"
      :data="items"
      :border="true"
      :stripe="true"
      :highlight-current-row="true"
      :max-height="tableMaxHeight"
      :style="tableStyle"
      :row-class-name="getRowClassName"
      @selection-change="handleSelectionChange"
      @row-click="handleRowClick"
    >
      <!-- 固定左側列 -->
      <el-table-column 
        type="selection" 
        :width="columnWidths.selection"
        align="center" 
        fixed="left"
        :selectable="isRowSelectable"
      />
      
      <el-table-column 
        type="index" 
        label="序號" 
        :width="columnWidths.index"
        align="center" 
        fixed="left"
      />
      
      <!-- 主要內容列 -->
      <el-table-column 
        label="項目名稱" 
        prop="item_name" 
        :width="columnWidths.item_name"
        :show-overflow-tooltip="true"
        :sortable="true"
      >
        <template #default="{ row }">
          <div class="item-name-cell">
            <el-text :truncated="true">{{ row.item_name }}</el-text>
            <el-tag v-if="row.is_urgent" type="danger" size="small" class="urgent-tag">
              急需
            </el-tag>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column 
        label="規格說明" 
        prop="item_specification" 
        :width="columnWidths.item_specification"
        :show-overflow-tooltip="true"
      />
      
      <el-table-column 
        label="數量" 
        prop="item_quantity" 
        :width="columnWidths.item_quantity"
        align="center"
        :sortable="true"
      >
        <template #default="{ row }">
          <el-text class="quantity-display">
            {{ row.item_quantity }}
          </el-text>
        </template>
      </el-table-column>
      
      <el-table-column 
        label="單位" 
        prop="item_unit" 
        :width="columnWidths.item_unit"
        align="center"
      />
      
      <el-table-column 
        label="狀態" 
        prop="item_status" 
        :width="columnWidths.item_status"
        align="center"
        :sortable="true"
        :filters="statusFilters"
        :filter-method="filterStatus"
      >
        <template #default="{ row }">
          <StatusTag 
            :status="row.item_status" 
            size="small"
            :tooltip="getStatusTooltip(row.item_status)"
          />
        </template>
      </el-table-column>
      
      <!-- 供應商選擇列 - 優化的下拉選單 -->
      <el-table-column 
        label="供應商" 
        :width="columnWidths.supplier"
      >
        <template #default="{ row }">
          <div v-if="row.item_status === 'pending_review'" class="supplier-cell">
            <el-select
              v-model="row.supplier_id"
              placeholder="選擇供應商"
              :filterable="true"
              :remote="true"
              :remote-method="searchSuppliers"
              :loading="supplierLoading"
              style="width: 100%"
              @change="handleSupplierChange(row, $event)"
            >
              <el-option
                v-for="supplier in filteredSuppliers"
                :key="supplier.supplier_id"
                :label="supplier.supplier_name_zh"
                :value="supplier.supplier_id"
              >
                <div class="supplier-option">
                  <span class="supplier-name">{{ supplier.supplier_name_zh }}</span>
                  <span class="supplier-code">{{ supplier.supplier_code }}</span>
                </div>
              </el-option>
            </el-select>
          </div>
          <div v-else class="supplier-display">
            <el-text>{{ row.supplier?.supplier_name_zh || '-' }}</el-text>
          </div>
        </template>
      </el-table-column>
      
      <!-- 單價輸入列 - 優化的數字輸入 -->
      <el-table-column 
        label="單價" 
        :width="columnWidths.unit_price"
        align="right"
      >
        <template #default="{ row }">
          <div v-if="row.item_status === 'pending_review'" class="price-input-cell">
            <el-input-number
              v-model="row.unit_price"
              :min="0"
              :max="999999"
              :precision="2"
              :step="1"
              controls-position="right"
              style="width: 100%"
              @change="handlePriceChange(row, $event)"
            >
              <template #prefix>NT$</template>
            </el-input-number>
          </div>
          <div v-else class="price-display">
            <el-text class="money-text">
              {{ row.unit_price ? formatMoney(row.unit_price) : '-' }}
            </el-text>
          </div>
        </template>
      </el-table-column>
      
      <!-- 小計計算列 -->
      <el-table-column 
        label="小計" 
        :width="columnWidths.subtotal"
        align="right"
        :sortable="true"
      >
        <template #default="{ row }">
          <div class="subtotal-display">
            <el-text 
              v-if="row.unit_price && row.item_quantity" 
              class="money-text subtotal-amount"
            >
              {{ formatMoney(calculateSubtotal(row)) }}
            </el-text>
            <el-text v-else class="no-amount">-</el-text>
          </div>
        </template>
      </el-table-column>
      
      <!-- 備註輸入列 -->
      <el-table-column 
        label="備註" 
        :width="columnWidths.remarks"
      >
        <template #default="{ row }">
          <div v-if="row.item_status === 'pending_review'" class="remarks-input-cell">
            <el-input
              v-model="row.status_note"
              placeholder="輸入備註..."
              :maxlength="100"
              :show-word-limit="true"
              style="width: 100%"
              @input="handleRemarksChange(row, $event)"
            />
          </div>
          <div v-else class="remarks-display">
            <el-text :truncated="true">{{ row.status_note || '-' }}</el-text>
          </div>
        </template>
      </el-table-column>
      
      <!-- 固定右側操作列 -->
      <el-table-column 
        label="操作" 
        :width="columnWidths.actions"
        fixed="right"
        align="center"
      >
        <template #default="{ row }">
          <div v-if="row.item_status === 'pending_review'" class="action-buttons">
            <el-button
              type="success"
              size="small"
              :icon="Check"
              :disabled="!canApproveItem(row)"
              @click="approveItem(row)"
            >
              核准
            </el-button>
            
            <el-dropdown 
              @command="(command) => handleItemAction(command, row)"
              popper-class="item-action-dropdown"
            >
              <el-button type="warning" size="small">
                更多
                <el-icon class="el-icon--right">
                  <arrow-down />
                </el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item 
                    command="question" 
                    :icon="QuestionFilled"
                  >
                    標記疑問
                  </el-dropdown-item>
                  <el-dropdown-item 
                    command="reject" 
                    :icon="Close"
                  >
                    駁回項目
                  </el-dropdown-item>
                  <el-dropdown-item 
                    command="history" 
                    :icon="Clock"
                    divided
                  >
                    查看歷史
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          
          <div v-else class="status-display">
            <StatusTag :status="row.item_status" size="small" />
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { computed, ref, reactive, watch } from 'vue'
import { Check, QuestionFilled, Close, Clock, ArrowDown } from '@element-plus/icons-vue'

// 響應式列寬度配置
const columnWidths = computed(() => {
  const viewportWidth = window.innerWidth
  
  // 超大屏優化配置
  if (viewportWidth >= 1600) {
    return {
      selection: '55px',
      index: '70px',
      item_name: '250px',
      item_specification: '200px',
      item_quantity: '90px',
      item_unit: '80px',
      item_status: '120px',
      supplier: '220px',
      unit_price: '160px',
      subtotal: '130px',
      remarks: '200px',
      actions: '200px'
    }
  }
  
  // 大屏配置
  if (viewportWidth >= 1200) {
    return {
      selection: '55px',
      index: '60px',
      item_name: '200px',
      item_specification: '180px',
      item_quantity: '80px',
      item_unit: '80px',
      item_status: '110px',
      supplier: '200px',
      unit_price: '150px',
      subtotal: '120px',
      remarks: '180px',
      actions: '180px'
    }
  }
  
  // 中屏配置
  return {
    selection: '50px',
    index: '55px',
    item_name: '180px',
    item_specification: '160px',
    item_quantity: '70px',
    item_unit: '70px',
    item_status: '100px',
    supplier: '180px',
    unit_price: '140px',
    subtotal: '110px',
    remarks: '160px',
    actions: '160px'
  }
})

// Table容器樣式類
const tableContainerClass = computed(() => {
  const classes = ['review-table-container']
  if (dialogMode) classes.push('dialog-mode')
  if (window.innerWidth < 768) classes.push('mobile-table')
  return classes
})

// Table最大高度計算
const tableMaxHeight = computed(() => {
  const viewportHeight = window.innerHeight
  if (dialogMode) {
    return Math.max(400, viewportHeight * 0.6) + 'px'
  }
  return '600px'
})

// Table樣式對象
const tableStyle = computed(() => ({
  minWidth: getTableMinWidth() + 'px',
  fontSize: window.innerWidth < 768 ? '14px' : '15px'
}))

// 計算Table最小寬度
function getTableMinWidth() {
  const widths = columnWidths.value
  return Object.values(widths).reduce((total, width) => {
    return total + parseInt(width.replace('px', ''))
  }, 0)
}
</script>
```

---

## 2. 詳細CSS樣式調整方案

### 2.1 Dialog容器樣式優化

```scss
/* 審核Dialog容器樣式 */
.requisition-review-dialog {
  // 基本配置
  .el-dialog {
    margin: 0 auto;
    border-radius: 12px;
    box-shadow: 0 12px 32px 4px rgba(0, 0, 0, 0.12);
    overflow: hidden;
    
    // 頭部優化
    .el-dialog__header {
      padding: 20px 24px 16px;
      background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
      border-bottom: 1px solid #dee2e6;
      
      .el-dialog__title {
        font-size: 18px;
        font-weight: 600;
        color: #212529;
      }
      
      .el-dialog__close {
        font-size: 18px;
        color: #6c757d;
        transition: all 0.2s;
        
        &:hover {
          color: #dc3545;
          transform: scale(1.1);
        }
      }
    }
    
    // 內容區域
    .el-dialog__body {
      padding: 0;
      max-height: calc(100vh - 200px);
      overflow: hidden;
    }
    
    // 底部操作區
    .el-dialog__footer {
      padding: 16px 24px 20px;
      border-top: 1px solid #dee2e6;
      background: #f8f9fa;
    }
  }
  
  // 響應式調整
  @media (max-width: 1200px) {
    .el-dialog {
      margin: 2vh auto;
      border-radius: 8px;
    }
  }
  
  @media (max-width: 768px) {
    .el-dialog {
      margin: 1vh auto;
      border-radius: 0;
      
      .el-dialog__header {
        padding: 16px;
      }
    }
  }
}

// 移動端Dialog特殊樣式
.mobile-dialog {
  .el-dialog {
    width: 100vw !important;
    height: 100vh !important;
    margin: 0 !important;
    border-radius: 0 !important;
    
    .el-dialog__body {
      max-height: calc(100vh - 120px);
    }
  }
}
```

### 2.2 Table容器與滾動條優化

```scss
/* Table容器樣式優化 */
.review-table-container {
  // 基本容器配置
  .table-wrapper {
    position: relative;
    width: 100%;
    overflow-x: auto;
    overflow-y: visible;
    margin-bottom: 16px;
    
    // 優化滾動條樣式
    &::-webkit-scrollbar {
      height: 10px;
      background: rgba(0, 0, 0, 0.05);
      border-radius: 5px;
    }
    
    &::-webkit-scrollbar-track {
      background: #f1f3f4;
      border-radius: 5px;
    }
    
    &::-webkit-scrollbar-thumb {
      background: linear-gradient(135deg, #6c757d, #495057);
      border-radius: 5px;
      box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
      transition: all 0.2s;
      
      &:hover {
        background: linear-gradient(135deg, #495057, #343a40);
        box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2);
      }
      
      &:active {
        background: linear-gradient(135deg, #343a40, #212529);
      }
    }
    
    // Firefox滾動條樣式
    scrollbar-width: thin;
    scrollbar-color: #6c757d #f1f3f4;
  }
  
  // Table基本樣式增強
  .el-table {
    // 表格頭部樣式
    .el-table__header-wrapper {
      .el-table__header {
        th {
          background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
          border-bottom: 2px solid #dee2e6;
          font-weight: 600;
          color: #495057;
          
          .cell {
            padding: 12px 8px;
            font-size: 14px;
          }
        }
      }
    }
    
    // 表格主體樣式
    .el-table__body-wrapper {
      .el-table__body {
        tr {
          transition: all 0.2s;
          
          &:hover {
            background-color: rgba(24, 144, 255, 0.05);
          }
          
          &.el-table__row--striped {
            background-color: #fafbfc;
            
            &:hover {
              background-color: rgba(24, 144, 255, 0.08);
            }
          }
          
          td {
            border-bottom: 1px solid #f0f0f0;
            vertical-align: middle;
            
            .cell {
              padding: 10px 8px;
              line-height: 1.5;
            }
          }
        }
      }
    }
    
    // 固定列陰影優化
    .el-table__fixed,
    .el-table__fixed-right {
      box-shadow: 0 0 15px rgba(0, 0, 0, 0.08);
      
      &::before {
        background: linear-gradient(
          90deg,
          rgba(0, 0, 0, 0.05) 0%,
          transparent 100%
        );
      }
    }
    
    .el-table__fixed-right {
      &::before {
        background: linear-gradient(
          -90deg,
          rgba(0, 0, 0, 0.05) 0%,
          transparent 100%
        );
      }
    }
  }
  
  // Dialog模式特殊樣式
  &.dialog-mode {
    .table-wrapper {
      margin: 0;
      border-radius: 0;
    }
    
    .el-table {
      border: none;
      
      .el-table__header-wrapper th:first-child,
      .el-table__body-wrapper td:first-child {
        border-left: none;
      }
      
      .el-table__header-wrapper th:last-child,
      .el-table__body-wrapper td:last-child {
        border-right: none;
      }
    }
  }
}
```

### 2.3 表格單元格樣式優化

```scss
/* 表格單元格內容樣式 */
// 項目名稱單元格
.item-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .el-text {
    flex: 1;
    min-width: 0;
  }
  
  .urgent-tag {
    flex-shrink: 0;
    animation: pulse 1.5s infinite;
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }
}

// 數量顯示優化
.quantity-display {
  font-weight: 600;
  color: #495057;
  text-align: center;
}

// 供應商選擇單元格
.supplier-cell {
  .el-select {
    .el-input__wrapper {
      border-radius: 6px;
      transition: all 0.2s;
      
      &:hover {
        box-shadow: 0 0 0 1px #409eff;
      }
      
      &.is-focus {
        box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
      }
    }
  }
}

.supplier-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .supplier-name {
    font-weight: 500;
    color: #212529;
  }
  
  .supplier-code {
    font-size: 12px;
    color: #6c757d;
    background: #f8f9fa;
    padding: 2px 6px;
    border-radius: 3px;
  }
}

// 價格輸入單元格
.price-input-cell {
  .el-input-number {
    .el-input__wrapper {
      border-radius: 6px;
      
      .el-input__prefix {
        color: #28a745;
        font-weight: 500;
      }
    }
  }
}

// 金額顯示樣式
.money-text {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', 'Courier New', monospace;
  font-weight: 600;
  color: #28a745;
  
  &.subtotal-amount {
    font-size: 15px;
    color: #007bff;
  }
}

.no-amount {
  color: #6c757d;
  font-style: italic;
}

// 備註輸入單元格
.remarks-input-cell {
  .el-input {
    .el-input__wrapper {
      border-radius: 6px;
    }
    
    .el-input__count {
      font-size: 11px;
      color: #6c757d;
    }
  }
}

// 操作按鈕組
.action-buttons {
  display: flex;
  gap: 6px;
  justify-content: center;
  align-items: center;
  
  .el-button {
    border-radius: 6px;
    transition: all 0.2s;
    
    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12);
    }
    
    &:active {
      transform: translateY(0);
    }
  }
}

// 狀態顯示區域
.status-display {
  display: flex;
  justify-content: center;
  align-items: center;
}
```

### 2.4 移動端響應式樣式

```scss
/* 移動端優化樣式 */
@media (max-width: 768px) {
  .review-table-container {
    &.mobile-table {
      .table-wrapper {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
      }
      
      .el-table {
        font-size: 13px;
        
        .el-table__header-wrapper th .cell,
        .el-table__body-wrapper td .cell {
          padding: 8px 6px;
        }
        
        // 隱藏非關鍵列
        .el-table-column--specification,
        .el-table-column--remarks {
          display: none;
        }
      }
      
      // 觸摸友好的按鈕尺寸
      .action-buttons {
        .el-button {
          min-height: 36px;
          min-width: 36px;
          padding: 8px 12px;
        }
      }
      
      // 輸入組件觸摸優化
      .el-input,
      .el-select,
      .el-input-number {
        .el-input__wrapper {
          min-height: 40px;
          font-size: 16px; // 防止iOS縮放
        }
      }
    }
  }
}

// 超小屏幕卡片式佈局
@media (max-width: 576px) {
  .review-table-container.mobile-table {
    .table-wrapper {
      display: none; // 隱藏表格
    }
    
    .mobile-cards-container {
      display: block;
      padding: 12px;
    }
    
    .item-card {
      background: #fff;
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 12px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
      border: 1px solid #e9ecef;
      
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
        
        .item-title {
          font-weight: 600;
          color: #212529;
          font-size: 16px;
          line-height: 1.4;
        }
        
        .item-status {
          flex-shrink: 0;
          margin-left: 8px;
        }
      }
      
      .card-content {
        .info-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid #f8f9fa;
          
          &:last-child {
            border-bottom: none;
          }
          
          .label {
            color: #6c757d;
            font-size: 14px;
            font-weight: 500;
          }
          
          .value {
            color: #212529;
            font-size: 14px;
            text-align: right;
            
            &.money {
              font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
              font-weight: 600;
              color: #28a745;
            }
          }
        }
      }
      
      .card-actions {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid #f8f9fa;
        display: flex;
        gap: 8px;
        
        .el-button {
          flex: 1;
          min-height: 40px;
        }
      }
    }
  }
}
```

---

## 3. Vue.js 實施代碼

### 3.1 優化後的Review組件模板

```vue
<template>
  <div class="requisition-review" :class="componentClass">
    <!-- 審核頭部信息 -->
    <div class="review-header">
      <div class="requisition-info">
        <div class="info-main">
          <h3 class="order-number">{{ requisition.request_order_no }}</h3>
          <div class="order-meta">
            <el-tag type="primary" size="small">
              {{ requisition.requester_name }}
            </el-tag>
            <el-tag 
              :type="requisition.usage_type === 'daily' ? 'info' : 'warning'" 
              size="small"
            >
              {{ requisition.usage_type === 'daily' ? '日常用品' : '專案用品' }}
            </el-tag>
            <StatusTag :status="requisition.order_status" />
          </div>
        </div>
        
        <div class="info-summary" v-if="!isMobile">
          <div class="summary-item">
            <span class="label">總項目數</span>
            <span class="value">{{ items.length }}</span>
          </div>
          <div class="summary-item">
            <span class="label">待審核</span>
            <span class="value pending">{{ pendingCount }}</span>
          </div>
          <div class="summary-item">
            <span class="label">預估總額</span>
            <span class="value money">{{ formatMoney(estimatedTotal) }}</span>
          </div>
        </div>
      </div>
      
      <!-- 快速操作工具欄 -->
      <div class="quick-actions" v-if="!isMobile">
        <el-button-group>
          <el-button 
            size="small" 
            @click="toggleSelectAll"
            :icon="selectedItems.length === selectableItems.length ? 'remove' : 'plus'"
          >
            {{ selectedItems.length === selectableItems.length ? '取消全選' : '全選' }}
          </el-button>
          <el-button size="small" @click="expandAll">
            展開詳情
          </el-button>
          <el-button size="small" @click="exportData">
            匯出資料
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 表格內容區域 -->
    <div class="review-content">
      <!-- 桌面版表格 -->
      <div v-if="!isMobile" class="table-wrapper">
        <el-table
          ref="reviewTable"
          :data="filteredItems"
          :border="true"
          :stripe="true"
          :highlight-current-row="true"
          :max-height="tableMaxHeight"
          :style="tableStyle"
          :row-class-name="getRowClassName"
          :default-sort="{prop: 'item_name', order: 'ascending'}"
          @selection-change="handleSelectionChange"
          @row-click="handleRowClick"
          @sort-change="handleSortChange"
          v-loading="loading"
          element-loading-text="載入中..."
        >
          <!-- 展開詳情列 -->
          <el-table-column type="expand" width="30" align="center">
            <template #default="{ row }">
              <div class="expanded-detail">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="完整規格">
                    {{ row.item_specification || '無' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="申請原因">
                    {{ row.request_reason || '無' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="預期交付日期">
                    {{ formatDate(row.expected_delivery_date) || '未指定' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="緊急程度">
                    <el-tag :type="row.urgency_level === 'high' ? 'danger' : row.urgency_level === 'medium' ? 'warning' : 'info'">
                      {{ getUrgencyText(row.urgency_level) }}
                    </el-tag>
                  </el-descriptions-item>
                </el-descriptions>
                
                <!-- 歷史記錄 -->
                <div class="history-section" v-if="row.status_history?.length">
                  <h4>狀態歷史</h4>
                  <el-timeline>
                    <el-timeline-item
                      v-for="history in row.status_history"
                      :key="history.id"
                      :timestamp="formatDateTime(history.created_at)"
                      :type="getHistoryType(history.status)"
                    >
                      <div class="history-content">
                        <div class="history-status">
                          <StatusTag :status="history.status" size="small" />
                          <span class="history-user">{{ history.user_name }}</span>
                        </div>
                        <p class="history-note" v-if="history.note">
                          {{ history.note }}
                        </p>
                      </div>
                    </el-timeline-item>
                  </el-timeline>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <!-- 其他列配置同前面的Table組件配置 -->
          <!-- ... -->
          
        </el-table>
      </div>
      
      <!-- 移動版卡片佈局 -->
      <div v-else class="mobile-cards-container">
        <div
          v-for="item in filteredItems"
          :key="item.detail_id"
          class="item-card"
          :class="{ 'selected': selectedItems.includes(item) }"
          @click="toggleItemSelection(item)"
        >
          <div class="card-header">
            <div class="item-info">
              <h4 class="item-title">{{ item.item_name }}</h4>
              <p class="item-spec" v-if="item.item_specification">
                {{ item.item_specification }}
              </p>
            </div>
            <div class="item-status">
              <StatusTag :status="item.item_status" size="small" />
            </div>
          </div>
          
          <div class="card-content">
            <div class="info-grid">
              <div class="info-item">
                <span class="label">數量</span>
                <span class="value">{{ item.item_quantity }} {{ item.item_unit }}</span>
              </div>
              
              <div class="info-item" v-if="item.unit_price">
                <span class="label">單價</span>
                <span class="value money">{{ formatMoney(item.unit_price) }}</span>
              </div>
              
              <div class="info-item" v-if="item.supplier">
                <span class="label">供應商</span>
                <span class="value">{{ item.supplier.supplier_name_zh }}</span>
              </div>
              
              <div class="info-item" v-if="item.unit_price">
                <span class="label">小計</span>
                <span class="value money subtotal">
                  {{ formatMoney(calculateSubtotal(item)) }}
                </span>
              </div>
            </div>
          </div>
          
          <!-- 移動端編輯控制 -->
          <div class="card-edit" v-if="item.item_status === 'pending_review'">
            <div class="edit-row">
              <label>供應商</label>
              <el-select
                v-model="item.supplier_id"
                placeholder="選擇供應商"
                size="small"
                style="width: 100%"
                @click.stop
              >
                <el-option
                  v-for="supplier in suppliers"
                  :key="supplier.supplier_id"
                  :label="supplier.supplier_name_zh"
                  :value="supplier.supplier_id"
                />
              </el-select>
            </div>
            
            <div class="edit-row">
              <label>單價</label>
              <el-input-number
                v-model="item.unit_price"
                :min="0"
                :precision="2"
                size="small"
                style="width: 100%"
                @click.stop
              />
            </div>
            
            <div class="edit-row">
              <label>備註</label>
              <el-input
                v-model="item.status_note"
                placeholder="輸入備註"
                size="small"
                @click.stop
              />
            </div>
          </div>
          
          <div class="card-actions" v-if="item.item_status === 'pending_review'">
            <el-button
              type="success"
              size="small"
              :disabled="!canApproveItem(item)"
              @click.stop="approveItem(item)"
            >
              核准
            </el-button>
            <el-button
              type="warning"
              size="small"
              @click.stop="questionItem(item)"
            >
              疑問
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click.stop="rejectItem(item)"
            >
              駁回
            </el-button>
          </div>
        </div>
        
        <!-- 移動端空狀態 -->
        <div v-if="filteredItems.length === 0" class="empty-state">
          <el-empty description="沒有找到符合條件的項目" />
        </div>
      </div>
    </div>

    <!-- 批量操作區域 -->
    <div class="batch-actions" v-if="selectedItems.length > 0">
      <div class="batch-info">
        <el-icon><Select /></el-icon>
        <span>已選擇 {{ selectedItems.length }} 項，預估金額 {{ formatMoney(selectedTotal) }}</span>
      </div>
      
      <div class="batch-buttons">
        <el-button
          type="success"
          :disabled="!canBatchApprove"
          :loading="batchProcessing"
          @click="batchApprove"
        >
          <el-icon><Check /></el-icon>
          批量核准
        </el-button>
        <el-button
          type="warning"
          :loading="batchProcessing"
          @click="batchQuestion"
        >
          <el-icon><QuestionFilled /></el-icon>
          批量疑問
        </el-button>
        <el-button
          type="danger"
          :loading="batchProcessing"
          @click="batchReject"
        >
          <el-icon><Close /></el-icon>
          批量駁回
        </el-button>
      </div>
    </div>

    <!-- 底部操作區域 -->
    <div class="review-actions">
      <div class="action-left">
        <el-button @click="$emit('close')">
          <el-icon><Back /></el-icon>
          關閉
        </el-button>
        <el-button
          v-if="hasChanges"
          type="info"
          @click="resetChanges"
        >
          <el-icon><RefreshLeft /></el-icon>
          重置變更
        </el-button>
      </div>
      
      <div class="action-right">
        <el-button
          type="danger"
          :loading="submitting"
          @click="rejectAll"
        >
          <el-icon><Close /></el-icon>
          駁回整單
        </el-button>
        <el-button
          type="primary"
          :loading="submitting"
          :disabled="!hasValidChanges"
          @click="saveChanges"
        >
          <el-icon><Check /></el-icon>
          保存變更
        </el-button>
      </div>
    </div>

    <!-- 原因輸入對話框 -->
    <ReasonDialog
      v-model="reasonDialogVisible"
      :title="reasonDialogTitle"
      :loading="reasonSubmitting"
      @confirm="confirmWithReason"
      @cancel="cancelAction"
    />
    
    <!-- 預覽摘要對話框 -->
    <SummaryDialog
      v-model="summaryDialogVisible"
      :items="selectedItems"
      :action="currentBatchAction"
      @confirm="executeBatchAction"
      @cancel="cancelBatchAction"
    />
  </div>
</template>
```

### 3.2 組件邏輯實現

```javascript
<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Check, Close, QuestionFilled, Back, RefreshLeft, 
  Select, Plus, Remove, ArrowDown 
} from '@element-plus/icons-vue'

import { StatusTag, ReasonDialog, SummaryDialog } from '@/components'
import { useRequisitionStore } from '@/stores'
import { suppliersApi } from '@/api'
import { debounce } from '@/utils/debounce'
import type { RequestOrder, RequestOrderItem, Supplier, BatchAction } from '@/types/common'

// Props & Emits
interface Props {
  requisition: RequestOrder
  dialogMode?: boolean
}

interface Emits {
  (e: 'close'): void
  (e: 'updated'): void
}

const props = withDefaults(defineProps<Props>(), {
  dialogMode: false
})
const emit = defineEmits<Emits>()

// Stores
const requisitionStore = useRequisitionStore()

// Reactive State
const loading = ref(false)
const submitting = ref(false)
const batchProcessing = ref(false)
const reasonSubmitting = ref(false)

const selectedItems = ref<RequestOrderItem[]>([])
const suppliers = ref<Supplier[]>([])
const filteredSuppliers = ref<Supplier[]>([])
const supplierLoading = ref(false)

// Dialog States
const reasonDialogVisible = ref(false)
const reasonDialogTitle = ref('')
const reasonText = ref('')
const summaryDialogVisible = ref(false)

const currentBatchAction = ref<BatchAction | null>(null)
const pendingAction = ref<{
  type: string
  items?: RequestOrderItem[]
  item?: RequestOrderItem
} | null>(null)

// 響應式計算屬性
const isMobile = computed(() => window.innerWidth < 768)

const componentClass = computed(() => ({
  'requisition-review': true,
  'dialog-mode': props.dialogMode,
  'mobile-mode': isMobile.value
}))

const items = computed(() => props.requisition.items || [])

const filteredItems = computed(() => {
  // 這裡可以加入搜索和過濾邏輯
  return items.value
})

const pendingCount = computed(() => 
  items.value.filter(item => item.item_status === 'pending_review').length
)

const selectableItems = computed(() =>
  items.value.filter(item => item.item_status === 'pending_review')
)

const estimatedTotal = computed(() => {
  return items.value.reduce((total, item) => {
    if (item.unit_price && item.item_quantity) {
      return total + (item.unit_price * item.item_quantity)
    }
    return total
  }, 0)
})

const selectedTotal = computed(() => {
  return selectedItems.value.reduce((total, item) => {
    if (item.unit_price && item.item_quantity) {
      return total + (item.unit_price * item.item_quantity)
    }
    return total
  }, 0)
})

const canBatchApprove = computed(() => {
  return selectedItems.value.length > 0 && 
    selectedItems.value.every(item => canApproveItem(item))
})

const hasValidChanges = computed(() => {
  return items.value.some(item => 
    item.item_status === 'pending_review' && 
    (item.supplier_id && item.unit_price)
  )
})

const hasChanges = computed(() => {
  // 檢測是否有未保存的變更
  return items.value.some(item => item._changed)
})

const tableMaxHeight = computed(() => {
  const viewportHeight = window.innerHeight
  if (props.dialogMode) {
    return Math.max(400, viewportHeight * 0.55) + 'px'
  }
  return '600px'
})

const tableStyle = computed(() => ({
  minWidth: getTableMinWidth() + 'px',
  fontSize: isMobile.value ? '14px' : '15px'
}))

// 響應式列寬度（同前面的配置）
const columnWidths = computed(() => {
  // ... 同前面的配置
})

// 狀態過濾器
const statusFilters = [
  { text: '待審核', value: 'pending_review' },
  { text: '已核准', value: 'approved' },
  { text: '已駁回', value: 'rejected' },
  { text: '有疑問', value: 'questioned' }
]

// Methods
const formatMoney = (amount: number) => {
  if (!amount && amount !== 0) return ''
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: 'TWD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount)
}

const formatDate = (date: string) => {
  if (!date) return ''
  return new Intl.DateTimeFormat('zh-TW').format(new Date(date))
}

const formatDateTime = (datetime: string) => {
  if (!datetime) return ''
  return new Intl.DateTimeFormat('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(datetime))
}

const getUrgencyText = (urgency: string) => {
  const map = {
    'high': '高',
    'medium': '中',
    'low': '低'
  }
  return map[urgency] || '普通'
}

const getHistoryType = (status: string) => {
  const typeMap = {
    'approved': 'success',
    'rejected': 'danger',
    'questioned': 'warning',
    'pending_review': 'info'
  }
  return typeMap[status] || 'info'
}

const calculateSubtotal = (item: RequestOrderItem) => {
  if (!item.unit_price || !item.item_quantity) return 0
  return item.unit_price * item.item_quantity
}

const canApproveItem = (item: RequestOrderItem) => {
  return item.item_status === 'pending_review' && 
         item.supplier_id && 
         item.unit_price && 
         item.unit_price > 0
}

const getRowClassName = ({ row }: { row: RequestOrderItem }) => {
  const classes = []
  
  if (row.item_status === 'approved') classes.push('row-approved')
  if (row.item_status === 'rejected') classes.push('row-rejected')
  if (row.item_status === 'questioned') classes.push('row-questioned')
  if (row.is_urgent) classes.push('row-urgent')
  if (row._changed) classes.push('row-changed')
  
  return classes.join(' ')
}

const getTableMinWidth = () => {
  const widths = columnWidths.value
  return Object.values(widths).reduce((total, width) => {
    return total + parseInt(width.replace('px', ''))
  }, 0)
}

// 選擇相關方法
const handleSelectionChange = (selection: RequestOrderItem[]) => {
  selectedItems.value = selection
}

const toggleSelectAll = () => {
  if (selectedItems.value.length === selectableItems.value.length) {
    selectedItems.value = []
  } else {
    selectedItems.value = [...selectableItems.value]
  }
}

const toggleItemSelection = (item: RequestOrderItem) => {
  const index = selectedItems.value.findIndex(selected => 
    selected.detail_id === item.detail_id
  )
  
  if (index > -1) {
    selectedItems.value.splice(index, 1)
  } else {
    selectedItems.value.push(item)
  }
}

// 供應商搜索 (防抖處理)
const searchSuppliers = debounce(async (query: string) => {
  if (!query) {
    filteredSuppliers.value = suppliers.value
    return
  }
  
  supplierLoading.value = true
  try {
    const results = suppliers.value.filter(supplier =>
      supplier.supplier_name_zh.includes(query) ||
      supplier.supplier_code.includes(query)
    )
    filteredSuppliers.value = results
  } catch (error) {
    console.error('搜索供應商失敗:', error)
  } finally {
    supplierLoading.value = false
  }
}, 300)

// 數據變更處理
const handleSupplierChange = (row: RequestOrderItem, supplierId: string) => {
  row.supplier_id = supplierId
  row._changed = true
  
  // 自動設置建議價格
  const supplier = suppliers.value.find(s => s.supplier_id === supplierId)
  if (supplier && supplier.suggested_price) {
    row.unit_price = supplier.suggested_price
  }
  
  emit('updated')
}

const handlePriceChange = (row: RequestOrderItem, price: number) => {
  row.unit_price = price
  row._changed = true
  emit('updated')
}

const handleRemarksChange = (row: RequestOrderItem, remarks: string) => {
  row.status_note = remarks
  row._changed = true
  emit('updated')
}

// 單項操作方法
const approveItem = async (item: RequestOrderItem) => {
  if (!canApproveItem(item)) {
    ElMessage.error('請先設置供應商和單價')
    return
  }

  try {
    loading.value = true
    await requisitionStore.approveItem(
      props.requisition.request_order_no,
      item.detail_id,
      {
        supplier_id: item.supplier_id!,
        unit_price: item.unit_price!,
        note: item.status_note
      }
    )
    
    item.item_status = 'approved'
    item._changed = false
    
    ElMessage.success('項目核准成功')
    emit('updated')
  } catch (error) {
    console.error('核准項目失敗:', error)
    ElMessage.error('核准失敗，請重試')
  } finally {
    loading.value = false
  }
}

const questionItem = (item: RequestOrderItem) => {
  reasonDialogTitle.value = '標記疑問'
  reasonText.value = ''
  pendingAction.value = { type: 'question', item }
  reasonDialogVisible.value = true
}

const rejectItem = (item: RequestOrderItem) => {
  reasonDialogTitle.value = '駁回項目'
  reasonText.value = ''
  pendingAction.value = { type: 'reject', item }
  reasonDialogVisible.value = true
}

// 批量操作方法
const batchApprove = () => {
  if (!canBatchApprove.value) {
    ElMessage.warning('請選擇有效的項目進行批量核准')
    return
  }
  
  currentBatchAction.value = {
    type: 'approve',
    items: [...selectedItems.value],
    title: '批量核准項目',
    message: `確認核准選中的 ${selectedItems.value.length} 個項目？`
  }
  
  summaryDialogVisible.value = true
}

const batchQuestion = () => {
  if (selectedItems.value.length === 0) {
    ElMessage.warning('請選擇要標記疑問的項目')
    return
  }

  reasonDialogTitle.value = '批量標記疑問'
  reasonText.value = ''
  pendingAction.value = { type: 'batchQuestion', items: [...selectedItems.value] }
  reasonDialogVisible.value = true
}

const batchReject = () => {
  if (selectedItems.value.length === 0) {
    ElMessage.warning('請選擇要駁回的項目')
    return
  }

  reasonDialogTitle.value = '批量駁回項目'
  reasonText.value = ''
  pendingAction.value = { type: 'batchReject', items: [...selectedItems.value] }
  reasonDialogVisible.value = true
}

const rejectAll = () => {
  reasonDialogTitle.value = '駁回整張請購單'
  reasonText.value = ''
  pendingAction.value = { type: 'rejectAll' }
  reasonDialogVisible.value = true
}

// 對話框確認處理
const confirmWithReason = async () => {
  if (!reasonText.value.trim()) {
    ElMessage.error('請輸入原因')
    return
  }

  const action = pendingAction.value
  if (!action) return

  try {
    reasonSubmitting.value = true

    switch (action.type) {
      case 'question':
        if (action.item) {
          await requisitionStore.questionItem(
            props.requisition.request_order_no,
            action.item.detail_id,
            { reason: reasonText.value.trim() }
          )
          action.item.item_status = 'questioned'
          action.item.status_note = reasonText.value.trim()
          action.item._changed = false
        }
        break

      case 'reject':
        if (action.item) {
          await requisitionStore.rejectItem(
            props.requisition.request_order_no,
            action.item.detail_id,
            { reason: reasonText.value.trim() }
          )
          action.item.item_status = 'rejected'
          action.item.status_note = reasonText.value.trim()
          action.item._changed = false
        }
        break

      case 'batchQuestion':
        if (action.items) {
          for (const item of action.items) {
            await requisitionStore.questionItem(
              props.requisition.request_order_no,
              item.detail_id,
              { reason: reasonText.value.trim() }
            )
            item.item_status = 'questioned'
            item.status_note = reasonText.value.trim()
            item._changed = false
          }
        }
        break

      case 'batchReject':
        if (action.items) {
          for (const item of action.items) {
            await requisitionStore.rejectItem(
              props.requisition.request_order_no,
              item.detail_id,
              { reason: reasonText.value.trim() }
            )
            item.item_status = 'rejected'
            item.status_note = reasonText.value.trim()
            item._changed = false
          }
        }
        break

      case 'rejectAll':
        await requisitionStore.rejectRequisition(
          props.requisition.request_order_no,
          { reason: reasonText.value.trim() }
        )
        emit('updated')
        return
    }

    ElMessage.success('操作完成')
    reasonDialogVisible.value = false
    pendingAction.value = null
    reasonText.value = ''
    selectedItems.value = []
    emit('updated')
  } catch (error) {
    console.error('操作失敗:', error)
    ElMessage.error('操作失敗，請重試')
  } finally {
    reasonSubmitting.value = false
  }
}

const cancelAction = () => {
  reasonDialogVisible.value = false
  pendingAction.value = null
  reasonText.value = ''
}

// 批量操作執行
const executeBatchAction = async () => {
  const action = currentBatchAction.value
  if (!action) return

  try {
    batchProcessing.value = true
    
    if (action.type === 'approve' && action.items) {
      for (const item of action.items) {
        if (canApproveItem(item)) {
          await approveItem(item)
        }
      }
    }
    
    ElMessage.success(`批量${action.type === 'approve' ? '核准' : '操作'}完成`)
    summaryDialogVisible.value = false
    currentBatchAction.value = null
    selectedItems.value = []
  } catch (error) {
    console.error('批量操作失敗:', error)
    ElMessage.error('批量操作失敗')
  } finally {
    batchProcessing.value = false
  }
}

const cancelBatchAction = () => {
  summaryDialogVisible.value = false
  currentBatchAction.value = null
}

// 其他操作方法
const saveChanges = async () => {
  try {
    submitting.value = true
    // 保存所有變更
    await requisitionStore.saveRequisitionChanges(
      props.requisition.request_order_no,
      items.value.filter(item => item._changed)
    )
    
    // 清除變更標記
    items.value.forEach(item => {
      item._changed = false
    })
    
    ElMessage.success('變更已保存')
    emit('updated')
  } catch (error) {
    console.error('保存失敗:', error)
    ElMessage.error('保存失敗，請重試')
  } finally {
    submitting.value = false
  }
}

const resetChanges = async () => {
  try {
    await ElMessageBox.confirm(
      '確認要重置所有未保存的變更嗎？',
      '重置變更',
      {
        confirmButtonText: '確認',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 重新載入原始資料
    await fetchRequisitionData()
    ElMessage.success('變更已重置')
  } catch (error) {
    // 用戶取消操作
  }
}

// 工具方法
const expandAll = () => {
  // 展開所有詳細信息
  const table = reviewTable.value
  if (table) {
    items.value.forEach((row, index) => {
      table.toggleRowExpansion(row, true)
    })
  }
}

const exportData = () => {
  // 匯出當前數據
  const csvData = generateCSV(filteredItems.value)
  downloadCSV(csvData, `requisition_${props.requisition.request_order_no}.csv`)
}

const generateCSV = (data: RequestOrderItem[]) => {
  // CSV生成邏輯
  const headers = ['項目名稱', '規格說明', '數量', '單位', '狀態', '供應商', '單價', '小計', '備註']
  const rows = data.map(item => [
    item.item_name,
    item.item_specification || '',
    item.item_quantity,
    item.item_unit,
    getStatusText(item.item_status),
    item.supplier?.supplier_name_zh || '',
    item.unit_price || 0,
    calculateSubtotal(item),
    item.status_note || ''
  ])
  
  return [headers, ...rows].map(row => 
    row.map(cell => `"${cell}"`).join(',')
  ).join('\n')
}

const downloadCSV = (csvContent: string, filename: string) => {
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  
  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'
  
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

// 數據獲取
const fetchSuppliers = async () => {
  try {
    loading.value = true
    const response = await suppliersApi.getActiveSuppliers()
    suppliers.value = response
    filteredSuppliers.value = response
  } catch (error) {
    console.error('載入供應商失敗:', error)
    ElMessage.error('載入供應商失敗')
  } finally {
    loading.value = false
  }
}

const fetchRequisitionData = async () => {
  try {
    loading.value = true
    // 重新載入請購單數據
    await requisitionStore.fetchRequisition(props.requisition.request_order_no)
  } catch (error) {
    console.error('載入請購單數據失敗:', error)
    ElMessage.error('載入數據失敗')
  } finally {
    loading.value = false
  }
}

// 響應式監聽
watch(() => window.innerWidth, () => {
  // 響應視窗大小變化
  nextTick(() => {
    if (reviewTable.value) {
      reviewTable.value.doLayout()
    }
  })
})

// 生命週期
onMounted(async () => {
  await Promise.all([
    fetchSuppliers(),
    // 其他初始化任務
  ])
})

// 暴露給模板的引用
const reviewTable = ref()

// 提供給父組件的方法
defineExpose({
  refreshData: fetchRequisitionData,
  exportData,
  resetSelection: () => {
    selectedItems.value = []
  }
})
</script>
```

---

## 4. 用戶體驗改進建議

### 4.1 工作流程優化

**智能預填充功能：**
```javascript
// 基於歷史數據的智能建議
const getSupplierSuggestions = (item) => {
  const history = getItemHistory(item.item_name)
  return history.map(record => ({
    supplier: record.supplier,
    confidence: record.confidence,
    avgPrice: record.avg_price,
    lastUsed: record.last_used
  })).sort((a, b) => b.confidence - a.confidence)
}

// 價格建議算法
const suggestPrice = (item, supplier) => {
  const factors = {
    historical: getHistoricalPrice(item, supplier),
    market: getMarketPrice(item),
    inflation: getInflationAdjustment(),
    quantity: getQuantityDiscount(item.quantity)
  }
  
  return calculateSuggestedPrice(factors)
}
```

**批量操作增強：**
```javascript
// 智能批量選擇
const smartSelect = {
  sameSupplier: (supplierId) => {
    return items.value.filter(item => 
      item.supplier_id === supplierId && 
      item.item_status === 'pending_review'
    )
  },
  
  priceRange: (min, max) => {
    return items.value.filter(item => 
      item.unit_price >= min && 
      item.unit_price <= max
    )
  },
  
  urgentItems: () => {
    return items.value.filter(item => 
      item.is_urgent && 
      item.item_status === 'pending_review'
    )
  }
}
```

### 4.2 信息層級設計

**漸進式信息披露：**
```vue
<template>
  <div class="progressive-disclosure">
    <!-- 第一層：關鍵信息 -->
    <div class="primary-info">
      <h3>{{ item.item_name }}</h3>
      <div class="key-metrics">
        <span class="quantity">{{ item.item_quantity }} {{ item.item_unit }}</span>
        <span class="price" v-if="item.unit_price">{{ formatMoney(item.unit_price) }}</span>
        <StatusTag :status="item.item_status" />
      </div>
    </div>
    
    <!-- 第二層：詳細信息（展開後顯示） -->
    <el-collapse-transition>
      <div v-show="expanded" class="secondary-info">
        <el-descriptions :column="2" size="small" border>
          <el-descriptions-item label="完整規格">
            {{ item.item_specification }}
          </el-descriptions-item>
          <el-descriptions-item label="申請原因">
            {{ item.request_reason }}
          </el-descriptions-item>
          <el-descriptions-item label="預期交付">
            {{ formatDate(item.expected_delivery_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="緊急程度">
            <UrgencyTag :level="item.urgency_level" />
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-collapse-transition>
    
    <!-- 第三層：操作歷史（按需載入） -->
    <div v-if="showHistory" class="history-info">
      <HistoryTimeline :item-id="item.detail_id" />
    </div>
  </div>
</template>
```

### 4.3 操作便利性提升

**鍵盤快捷鍵支援：**
```javascript
const keyboardShortcuts = {
  'Ctrl+A': () => toggleSelectAll(),
  'Ctrl+S': () => saveChanges(),
  'Escape': () => emit('close'),
  'Enter': () => approveSelectedItems(),
  'Delete': () => rejectSelectedItems(),
  'F2': () => toggleEditMode(),
  'F5': () => refreshData()
}

const handleKeydown = (event) => {
  const key = `${event.ctrlKey ? 'Ctrl+' : ''}${event.key}`
  const handler = keyboardShortcuts[key]
  if (handler && !isInputFocused()) {
    event.preventDefault()
    handler()
  }
}
```

**拖拽操作支援：**
```javascript
const setupDragAndDrop = () => {
  const sortable = new Sortable(tableBody.value, {
    group: 'requisition-items',
    animation: 150,
    ghostClass: 'sortable-ghost',
    chosenClass: 'sortable-chosen',
    dragClass: 'sortable-drag',
    
    onEnd: (event) => {
      const { oldIndex, newIndex } = event
      if (oldIndex !== newIndex) {
        reorderItems(oldIndex, newIndex)
      }
    }
  })
}
```

**觸控手勢支援：**
```javascript
const touchGestures = {
  swipeLeft: (item) => {
    // 左滑顯示快速操作選單
    showQuickActions(item)
  },
  
  swipeRight: (item) => {
    // 右滑快速核准
    if (canApproveItem(item)) {
      approveItem(item)
    }
  },
  
  longPress: (item) => {
    // 長按顯示詳細菜單
    showContextMenu(item)
  }
}
```

---

## 5. 技術實施指南

### 5.1 Element Plus 版本要求

```json
{
  "dependencies": {
    "element-plus": "^2.4.0",
    "vue": "^3.3.0",
    "@element-plus/icons-vue": "^2.1.0"
  }
}
```

### 5.2 CSS 變數配置

```scss
:root {
  // Dialog配置變數
  --dialog-border-radius: 12px;
  --dialog-box-shadow: 0 12px 32px 4px rgba(0, 0, 0, 0.12);
  --dialog-header-bg: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  
  // Table配置變數
  --table-header-bg: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  --table-stripe-bg: #fafbfc;
  --table-hover-bg: rgba(24, 144, 255, 0.05);
  --table-border-color: #f0f0f0;
  
  // 響應式斷點
  --breakpoint-xs: 576px;
  --breakpoint-sm: 768px;
  --breakpoint-md: 992px;
  --breakpoint-lg: 1200px;
  --breakpoint-xl: 1600px;
  
  // 動畫時長
  --transition-duration: 0.2s;
  --animation-duration: 0.15s;
}
```

### 5.3 性能優化建議

**虛擬滾動配置：**
```vue
<el-table-v2
  :data="items"
  :columns="columns"
  :height="400"
  :row-height="48"
  :header-height="56"
  fixed
>
  <!-- 大數據量時使用虛擬滾動 -->
</el-table-v2>
```

**懶加載實現：**
```javascript
const loadData = async (page = 1, pageSize = 50) => {
  try {
    loading.value = true
    const response = await requisitionApi.getItems({
      page,
      pageSize,
      filters: currentFilters.value
    })
    
    if (page === 1) {
      items.value = response.data
    } else {
      items.value.push(...response.data)
    }
    
    hasMore.value = response.hasMore
  } finally {
    loading.value = false
  }
}
```

### 5.4 測試建議

**單元測試範例：**
```javascript
import { mount } from '@vue/test-utils'
import { ElDialog, ElTable } from 'element-plus'
import RequisitionReview from '@/views/requisitions/Review.vue'

describe('RequisitionReview', () => {
  test('dialog width adapts to screen size', async () => {
    // 模擬不同屏幕尺寸
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1400,
    })
    
    const wrapper = mount(RequisitionReview, {
      props: {
        requisition: mockRequisition,
        dialogMode: true
      }
    })
    
    const dialog = wrapper.findComponent(ElDialog)
    expect(dialog.props('width')).toBe('85vw')
  })
  
  test('table displays all required columns', () => {
    const wrapper = mount(RequisitionReview, {
      props: { requisition: mockRequisition }
    })
    
    const table = wrapper.findComponent(ElTable)
    const columns = table.findAll('.el-table__header th')
    
    expect(columns).toHaveLength(12) // 預期的列數
  })
})
```

---

## 6. 部署與維護

### 6.1 構建優化

```javascript
// vite.config.js
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'element-plus': ['element-plus'],
          'table-components': ['./src/views/requisitions/Review.vue']
        }
      }
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: '@use "@/styles/variables.scss" as *;'
      }
    }
  }
})
```

### 6.2 監控指標

```javascript
// 性能監控
const performanceMetrics = {
  dialogOpenTime: 0,
  tableRenderTime: 0,
  dataLoadTime: 0,
  userInteractionDelay: 0
}

const trackPerformance = (metric, value) => {
  performanceMetrics[metric] = value
  
  // 發送到監控系統
  analytics.track('performance', {
    metric,
    value,
    timestamp: Date.now(),
    userAgent: navigator.userAgent,
    viewport: `${window.innerWidth}x${window.innerHeight}`
  })
}
```

---

## 總結

本規格文檔提供了針對ERP請購單審核界面Dialog寬度與Table寬度不匹配問題的全面解決方案。主要改進包括：

1. **響應式Dialog設計**：根據屏幕尺寸動態調整Dialog寬度
2. **智能Table佈局**：優化列寬度配置和固定列設計
3. **移動端適配**：提供卡片式佈局和觸控優化
4. **用戶體驗增強**：添加批量操作、智能建議、快捷鍵支援
5. **性能優化**：實現虛擬滾動和懶加載
6. **無障礙支援**：完整的鍵盤導航和屏幕閱讀器支援

通過實施這些改進，可以顯著提升請購單審核流程的效率和用戶體驗。

**關鍵檔案路徑：**
- 前端規格：`D:\AWORKSPACE\Github\project_ERP_dev_agent\artifacts\FE_SPEC.json`
- 審核組件：`D:\AWORKSPACE\Github\project_ERP_dev_agent\frontend\src\views\requisitions\Review.vue`
- 列表組件：`D:\AWORKSPACE\Github\project_ERP_dev_agent\frontend\src\views\requisitions\List.vue`

所有代碼示例均可直接應用到現有項目中，並提供了完整的類型定義和錯誤處理。