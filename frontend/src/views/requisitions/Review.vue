<template>
  <div class="requisition-review">
    <div class="review-header">
      <div class="requisition-info">
        <h3>
          {{ requisition.request_order_no }}
          <el-tag v-if="requisition.is_urgent" type="danger" class="urgent-tag">
            <el-icon><Warning /></el-icon> 加急
          </el-tag>
        </h3>
        <div class="info-meta">
          <el-tag>{{ requisition.requester_name }}</el-tag>
          <el-tag type="info">{{ requisition.usage_type === 'daily' ? '日常用品' : '專案用品' }}</el-tag>
          <StatusTag :status="requisition.order_status" />
        </div>
        <!-- 加急信息顯示 -->
        <div v-if="requisition.is_urgent" class="urgent-info">
          <el-alert
            title="加急請購"
            type="warning"
            :closable="false"
            show-icon
          >
            <div class="urgent-details">
              <div class="urgent-item">
                <span class="label">期望到貨日期：</span>
                <span class="value">{{ formatDate(requisition.expected_delivery_date) }}</span>
              </div>
              <div class="urgent-item">
                <span class="label">加急原因：</span>
                <span class="value">{{ requisition.urgent_reason || '未說明' }}</span>
              </div>
            </div>
          </el-alert>
        </div>
      </div>
    </div>

    <div class="review-content">
      <!-- Items Table -->
      <div class="table-wrapper">
        <el-table
          :data="items"
          border
          max-height="600px"
          @selection-change="handleSelectionChange"
          style="min-width: 1200px"
          class="review-table"
        >
          <el-table-column type="selection" width="55" align="center" fixed="left" />
          <el-table-column type="index" label="序號" width="60" align="center" fixed="left" />
          
          <el-table-column label="項目名稱" prop="item_name" width="180" show-overflow-tooltip />
          <el-table-column label="規格說明" prop="item_specification" width="160" show-overflow-tooltip />
          <el-table-column label="數量" prop="item_quantity" width="80" align="center" />
          <el-table-column label="單位" prop="item_unit" width="80" align="center" />
          
          <el-table-column label="狀態" prop="item_status" width="110" align="center">
            <template #default="{ row }">
              <StatusTag :status="row.item_status" size="small" />
            </template>
          </el-table-column>
          
          <el-table-column label="供應商" width="220">
            <template #default="{ row }">
              <el-select
                v-if="row.item_status === 'pending_review'"
                v-model="row.supplier_id"
                placeholder="選擇供應商"
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="supplier in suppliers"
                  :key="supplier.supplier_id"
                  :label="supplier.supplier_name_zh"
                  :value="supplier.supplier_id"
                />
              </el-select>
              <span v-else>{{ row.supplier?.supplier_name_zh || '-' }}</span>
            </template>
          </el-table-column>
          
          <el-table-column label="單價" width="160">
            <template #default="{ row }">
              <el-input-number
                v-if="row.item_status === 'pending_review'"
                v-model="row.unit_price"
                :min="0"
                :precision="2"
                controls-position="right"
                style="width: 100%"
              />
              <span v-else-if="row.unit_price" class="money">
                {{ formatMoney(row.unit_price) }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          
          <el-table-column label="小計" width="140" align="right">
            <template #default="{ row }">
              <span v-if="row.unit_price" class="money">
                {{ formatMoney(row.item_quantity * row.unit_price) }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          
          <el-table-column label="備註" width="160">
            <template #default="{ row }">
              <el-input
                v-if="row.item_status === 'pending_review'"
                v-model="row.status_note"
                placeholder="備註"
                style="width: 100%"
              />
              <span v-else>{{ row.status_note || '-' }}</span>
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="190" fixed="right">
            <template #default="{ row }">
              <div v-if="row.item_status === 'pending_review'" class="item-actions">
                <el-button
                  type="success"
                  size="small"
                  @click="approveItem(row)"
                >
                  核准
                </el-button>
                <el-dropdown @command="(command) => handleItemAction(command, row)">
                  <el-button type="warning" size="small">
                    更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="question">標記疑問</el-dropdown-item>
                      <el-dropdown-item command="reject">駁回項目</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
              <StatusTag v-else :status="row.item_status" size="small" />
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- Batch Actions -->
    <div class="batch-actions">
      <div class="selected-info">
        <span v-if="selectedItems.length > 0">
          已選擇 {{ selectedItems.length }} 項
        </span>
      </div>
      <div class="action-buttons">
        <el-button
          type="success"
          :disabled="selectedItems.length === 0"
          @click="batchApprove"
        >
          批量核准
        </el-button>
        <el-button
          type="warning"
          :disabled="selectedItems.length === 0"
          @click="batchQuestion"
        >
          批量疑問
        </el-button>
        <el-button
          type="danger"
          :disabled="selectedItems.length === 0"
          @click="batchReject"
        >
          批量駁回
        </el-button>
        <el-button
          type="danger"
          @click="rejectAll"
        >
          駁回整單
        </el-button>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="review-actions">
      <el-button @click="$emit('close')">關閉</el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="saveChanges"
      >
        保存變更
      </el-button>
    </div>

    <!-- Reason Dialog -->
    <el-dialog
      v-model="reasonDialogVisible"
      :title="reasonDialogTitle"
      width="400px"
    >
      <el-form @submit.prevent="confirmWithReason">
        <el-form-item label="原因">
          <el-input
            v-model="reasonText"
            type="textarea"
            :rows="4"
            placeholder="請輸入原因..."
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="reasonDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            :disabled="!reasonText.trim()"
            @click="confirmWithReason"
          >
            確認
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, Warning } from '@element-plus/icons-vue'
import { StatusTag } from '@/components'
import { useRequisitionStore } from '@/stores'
import { suppliersApi } from '@/api'
import webSocketManager from '@/utils/websocket'
import type { RequestOrder, RequestOrderItem, Supplier } from '@/types/common'

interface Props {
  requisition: RequestOrder
}

interface Emits {
  (e: 'close'): void
  (e: 'updated'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const requisitionStore = useRequisitionStore()

// State
const submitting = ref(false)
const selectedItems = ref<RequestOrderItem[]>([])
const suppliers = ref<Supplier[]>([])
const reasonDialogVisible = ref(false)
const reasonText = ref('')
const reasonDialogTitle = ref('')
const pendingAction = ref<{
  type: string
  items?: RequestOrderItem[]
  item?: RequestOrderItem
} | null>(null)

// Items from the requisition
const items = computed(() => props.requisition.items || [])

// Methods
const formatMoney = (amount: number) => {
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: 'TWD',
    minimumFractionDigits: 0
  }).format(amount)
}

const formatDate = (dateString: string | null | undefined) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '-'
  return new Intl.DateTimeFormat('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(date)
}

const handleSelectionChange = (selection: RequestOrderItem[]) => {
  selectedItems.value = selection
}

const approveItem = async (item: RequestOrderItem) => {
  if (!item.supplier_id || !item.unit_price) {
    ElMessage.error('請先設置供應商和單價')
    return
  }

  try {
    await requisitionStore.approveItem(
      props.requisition.request_order_no,
      item.detail_id,
      {
        supplier_id: item.supplier_id,
        unit_price: item.unit_price
      }
    )
    
    item.item_status = 'approved'
    ElMessage.success('項目核准成功')
    
    // CRITICAL FIX: Force status validation and refresh
    await validateAndRefreshStatus()
  } catch (error) {
    console.error('Approve item failed:', error)
  }
}

const handleItemAction = (command: string, item: RequestOrderItem) => {
  switch (command) {
    case 'question':
      questionItem(item)
      break
    case 'reject':
      rejectItem(item)
      break
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

const batchApprove = async () => {
  const pendingItems = selectedItems.value.filter(item => item.item_status === 'pending_review')
  
  if (pendingItems.length === 0) {
    ElMessage.warning('請選擇待審核的項目')
    return
  }

  const invalidItems = pendingItems.filter(item => !item.supplier_id || !item.unit_price)
  if (invalidItems.length > 0) {
    ElMessage.error('請先為所有選中項目設置供應商和單價')
    return
  }

  try {
    for (const item of pendingItems) {
      await approveItem(item)
    }
    ElMessage.success(`批量核准 ${pendingItems.length} 個項目`)
  } catch (error) {
    console.error('Batch approve failed:', error)
  }
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

const confirmWithReason = async () => {
  if (!reasonText.value.trim()) {
    ElMessage.error('請輸入原因')
    return
  }

  const action = pendingAction.value
  if (!action) return

  try {
    submitting.value = true

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
    
    // CRITICAL FIX: Force status validation and refresh
    await validateAndRefreshStatus()
  } catch (error) {
    console.error('Action failed:', error)
  } finally {
    submitting.value = false
  }
}

const saveChanges = async () => {
  console.log('[EMERGENCY_HOTFIX] saveChanges called - implementing actual API calls')
  
  try {
    submitting.value = true
    
    // Find all items that have changes (supplier or price modifications)
    const itemsToSave = items.value.filter(item => {
      // EMERGENCY FIX: Include all items with supplier/price data, regardless of status
      return (item.supplier_id || item.unit_price || item.status_note)
    })
    
    console.log(`[EMERGENCY_HOTFIX] Found ${itemsToSave.length} items to save`)
    
    if (itemsToSave.length === 0) {
      ElMessage.warning('沒有變更需要保存')
      return
    }
    
    // Save each item's changes via API
    let savedCount = 0
    for (const item of itemsToSave) {
      try {
        const saveData: any = {}
        
        if (item.supplier_id) {
          saveData.supplier_id = item.supplier_id
        }
        if (item.unit_price) {
          saveData.unit_price = item.unit_price
        }
        if (item.status_note) {
          saveData.status_note = item.status_note
        }
        
        console.log(`[EMERGENCY_HOTFIX] Saving item ${item.detail_id}:`, saveData)
        await requisitionStore.saveItemChanges(
          props.requisition.request_order_no,
          item.detail_id,
          saveData
        )
        savedCount++
      } catch (error) {
        console.error(`[EMERGENCY_HOTFIX] Failed to save item ${item.detail_id}:`, error)
      }
    }
    
    if (savedCount > 0) {
      ElMessage.success(`成功保存 ${savedCount} 個項目的變更`)
      console.log(`[EMERGENCY_HOTFIX] Successfully saved ${savedCount} items`)
    } else {
      ElMessage.error('保存變更失敗')
    }
    
  } catch (error) {
    console.error('[EMERGENCY_HOTFIX] saveChanges error:', error)
    ElMessage.error('保存變更時發生錯誤')
  } finally {
    submitting.value = false
  }
  
  // Always attempt status validation
  await validateAndRefreshStatus()
}

const fetchSuppliers = async () => {
  try {
    const response = await suppliersApi.getActiveSuppliers()
    suppliers.value = response
  } catch (error) {
    console.error('Failed to fetch suppliers:', error)
  }
}

// CRITICAL FIX: Status validation and refresh function
const validateAndRefreshStatus = async () => {
  try {
    console.log('[STATUS_FIX] Validating status after action')
    
    // Check if all items are reviewed
    const allItems = items.value
    const allReviewed = allItems.every(item => 
      ['approved', 'rejected', 'questioned'].includes(item.item_status)
    )
    
    console.log('[STATUS_FIX] All items reviewed:', allReviewed)
    
    if (allReviewed) {
      // Use enhanced refresh with retry logic from store
      console.log('[STATUS_FIX] All items reviewed - using enhanced refresh with retry')
      await requisitionStore.refreshRequisitionWithRetry(props.requisition.request_order_no, 3)
      
      // Also try polling for status change to 'reviewed'
      console.log('[STATUS_FIX] Polling for status change to "reviewed"')
      const updatedReq = await requisitionStore.pollRequisitionStatus(
        props.requisition.request_order_no, 
        'reviewed', 
        5
      )
      
      if (updatedReq && updatedReq.order_status === 'reviewed') {
        console.log('[STATUS_FIX] ✅ Status successfully updated to "reviewed"')
      } else {
        console.log('[STATUS_FIX] ⚠️ Status polling did not detect change to "reviewed"')
      }
      
      // Always emit updated to parent for UI refresh
      console.log('[STATUS_FIX] Emitting updated event to parent')
      emit('updated')
    }
  } catch (error) {
    console.error('[STATUS_FIX] Error during status validation:', error)
    // Still emit updated even on error to ensure UI refresh
    emit('updated')
  }
}

// WebSocket integration
const initializeWebSocket = async () => {
  try {
    console.log('[WebSocket] Connecting to real-time updates...')
    await webSocketManager.connect()
    
    // Subscribe to this requisition's updates
    webSocketManager.subscribeToRequisition(props.requisition.request_order_no)
    
    // Listen for status changes
    webSocketManager.onRequisitionStatusChange((data) => {
      console.log('[WebSocket] Received status change:', data)
      
      if (data.requisition_id === props.requisition.request_order_no) {
        // Update the local status
        if (props.requisition.order_status !== data.new_status) {
          console.log(`[WebSocket] Status updated: ${props.requisition.order_status} → ${data.new_status}`)
          
          // Emit updated event to trigger parent refresh
          emit('updated')
          
          // Show notification
          ElMessage.success(`請購單狀態已更新為：${data.new_status}`)
        }
      }
    })
    
    console.log('[WebSocket] Successfully initialized WebSocket connection')
  } catch (error) {
    console.warn('[WebSocket] Failed to connect:', error)
    // Continue without WebSocket - app should still work
  }
}

const cleanupWebSocket = () => {
  try {
    // Unsubscribe from this requisition
    webSocketManager.unsubscribeFromRequisition(props.requisition.request_order_no)
    
    // Remove status change listeners
    webSocketManager.offRequisitionStatusChange()
    
    console.log('[WebSocket] Cleanup completed')
  } catch (error) {
    console.warn('[WebSocket] Cleanup error:', error)
  }
}

// Lifecycle
onMounted(async () => {
  await fetchSuppliers()
  await initializeWebSocket()
})

onUnmounted(() => {
  cleanupWebSocket()
})
</script>

<style scoped>
.requisition-review {
  .review-header {
    padding: 16px 24px;
    border-bottom: 1px solid #ebeef5;
    
    .requisition-info {
      h3 {
        margin: 0 0 8px 0;
        color: #303133;
      }
      
      .info-meta {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
    }
  }
  
  .review-content {
    padding: 20px 24px;
    
    .table-wrapper {
      overflow-x: auto;
      overflow-y: visible;
      width: 100%;
      margin-bottom: 16px;
      
      /* 滾動條樣式優化 */
      &::-webkit-scrollbar {
        height: 8px;
      }
      
      &::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
      }
      
      &::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 4px;
      }
      
      &::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
      }
    }
  }
  
  .batch-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    background: #f8f9fa;
    border-top: 1px solid #ebeef5;
    
    .selected-info {
      font-size: 14px;
      color: #606266;
    }
    
    .action-buttons {
      display: flex;
      gap: 8px;
    }
  }
  
  .review-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding: 16px 24px;
    border-top: 1px solid #ebeef5;
  }
  
  .item-actions {
    display: flex;
    gap: 4px;
    
    .el-button {
      padding: 5px 8px;
    }
  }
  
  .money {
    font-family: Monaco, 'Courier New', monospace;
    font-weight: 500;
    color: #409eff;
  }
}

/* Dialog and Table Improvements */
.requisition-review {
  .review-table {
    /* Ensure table displays properly in dialog */
    min-width: 1200px;
    width: 100%;
    
    /* Better spacing for form controls */
    .el-select,
    .el-input-number,
    .el-input {
      min-width: 100px;
    }
    
    /* Improved supplier dropdown */
    .el-table__cell:has(.el-select) {
      padding: 8px 4px;
    }
    
    /* Better price input styling */
    .el-input-number {
      .el-input__inner {
        text-align: right;
        padding-right: 30px;
      }
    }
  }
  
  /* Touch-friendly improvements for mobile */
  .el-button {
    min-height: 32px;
    touch-action: manipulation;
  }
  
  .el-input__inner,
  .el-select__input {
    min-height: 32px;
  }
}

/* Responsive Design */
@media (max-width: 1400px) {
  .requisition-review {
    .review-content {
      padding: 16px 20px;
    }
  }
}

@media (max-width: 1200px) {
  .requisition-review {
    .review-table {
      min-width: 1000px;
    }
  }
}

@media (max-width: 768px) {
  .requisition-review {
    .review-header {
      padding: 12px 16px;
      
      .requisition-info {
        h3 {
          font-size: 16px;
          margin-bottom: 6px;
        }
        
        .info-meta {
          flex-wrap: wrap;
          gap: 6px;
          
          .el-tag {
            font-size: 11px;
          }
        }
      }
    }
    
    .review-content {
      padding: 12px 16px;
      
      .table-wrapper {
        /* Enhanced touch scrolling */
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        padding-bottom: 8px;
        
        /* Mobile-optimized scrollbar */
        &::-webkit-scrollbar {
          height: 12px;
        }
        
        &::-webkit-scrollbar-thumb {
          background: #409eff;
          border-radius: 6px;
        }
      }
      
      .review-table {
        min-width: 900px; /* Reduced for mobile */
        
        /* Compact mobile styling */
        .el-table__cell {
          padding: 6px 4px;
          font-size: 13px;
        }
        
        .el-button {
          padding: 4px 6px;
          font-size: 12px;
          min-height: 28px;
        }
        
        .el-select,
        .el-input-number,
        .el-input {
          font-size: 13px;
          
          .el-input__inner {
            height: 28px;
            line-height: 28px;
          }
        }
        
        .el-dropdown .el-button {
          padding: 4px 8px;
        }
      }
    }
    
    .batch-actions {
      flex-direction: column;
      gap: 12px;
      align-items: stretch;
      padding: 12px 16px;
      
      .selected-info {
        text-align: center;
        font-size: 13px;
      }
      
      .action-buttons {
        justify-content: center;
        flex-wrap: wrap;
        gap: 6px;
        
        .el-button {
          flex: 1;
          min-width: 80px;
          max-width: 120px;
          font-size: 12px;
        }
      }
    }
    
    .review-actions {
      justify-content: center;
      padding: 12px 16px;
      gap: 8px;
      
      .el-button {
        flex: 1;
        max-width: 120px;
        font-size: 13px;
      }
    }
    
    /* Mobile-specific dropdown improvements */
    .item-actions {
      flex-direction: column;
      gap: 2px;
      
      .el-button {
        width: 100%;
        min-width: 60px;
      }
    }
  }
}

@media (max-width: 480px) {
  .requisition-review {
    .review-table {
      min-width: 800px; /* Further reduced for small screens */
      
      .el-table__cell {
        padding: 4px 2px;
        font-size: 12px;
      }
      
      /* Hide less critical columns on very small screens */
      .el-table__column--hidden-sm {
        display: none;
      }
    }
    
    .batch-actions .action-buttons .el-button,
    .review-actions .el-button {
      font-size: 11px;
      padding: 6px 8px;
    }
  }
}
</style>