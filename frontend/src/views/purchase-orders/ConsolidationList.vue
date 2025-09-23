<template>
  <div class="consolidation-list">
    <div class="page-header">
      <h1 class="page-title">集運列表</h1>
      <div class="header-actions">
        <el-button type="primary" @click="refreshData">
          <el-icon><Refresh /></el-icon>
          重新整理
        </el-button>
      </div>
    </div>

    <!-- Summary Stats -->
    <div class="stats-container">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ summary.total_consolidations }}</div>
              <div class="stat-label">集運單總數</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card info">
            <div class="stat-content">
              <div class="stat-number">{{ summary.total_purchase_orders }}</div>
              <div class="stat-label">集運採購單數</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card warning">
            <div class="stat-content">
              <div class="stat-number">{{ getStatusCount('taiwan_customs') + getStatusCount('foreign_customs') }}</div>
              <div class="stat-label">海關清關中</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card success">
            <div class="stat-content">
              <div class="stat-number">{{ getStatusCount('delivered') }}</div>
              <div class="stat-label">已到貨</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div class="filters">
      <el-form :model="filters" inline>
        <el-form-item label="集運單ID">
          <el-input 
            v-model="filters.consolidationId" 
            placeholder="輸入集運單ID"
            clearable
          />
        </el-form-item>
        <el-form-item label="物流狀態">
          <el-select v-model="filters.logisticsStatus" placeholder="選擇物流狀態" clearable>
            <el-option label="全部" value="" />
            <el-option label="已發貨" value="shipped" />
            <el-option label="對方海關" value="foreign_customs" />
            <el-option label="台灣海關" value="taiwan_customs" />
            <el-option label="運送中" value="in_transit" />
            <el-option label="已到貨" value="delivered" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜尋</el-button>
          <el-button @click="resetFilters">重設</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-container">
      <el-table 
        :data="consolidationData" 
        :loading="loading"
        stripe
        :expand-row-keys="expandedRows"
        row-key="consolidation_id"
        @expand-change="handleRowExpand"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-content">
              <h4>集運內採購單詳情</h4>
              <el-table 
                :data="row.purchase_orders" 
                size="small"
                :show-header="true"
              >
                <el-table-column prop="purchase_order_no" label="採購單號" width="150" />
                <el-table-column prop="supplier_name" label="供應商" width="200" />
                <el-table-column prop="delivery_status" label="交貨狀態" width="120">
                  <template #default="{ row: poRow }">
                    <el-tag :type="getDeliveryStatusType(poRow.delivery_status)" size="small">
                      {{ getDeliveryStatusText(poRow.delivery_status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="remarks" label="備註" width="200">
                  <template #default="{ row: poRow }">
                    <div class="remarks-cell">
                      {{ poRow.remarks || '-' }}
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="subtotal" label="金額" width="100">
                  <template #default="{ row: poRow }">
                    ${{ poRow.subtotal.toLocaleString() }}
                  </template>
                </el-table-column>
                <el-table-column prop="items_count" label="項目數" width="80" />
                <el-table-column prop="added_at" label="加入時間" width="150">
                  <template #default="{ row: poRow }">
                    {{ formatDate(poRow.added_at) }}
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="consolidation_id" label="集運單ID" width="150" />
        <el-table-column prop="consolidation_name" label="集運單名稱" width="200" />
        <el-table-column prop="logistics_status" label="物流狀態" width="120">
          <template #default="{ row }">
            <el-tag :type="getDeliveryStatusType(row.logistics_status)" size="small">
              {{ getDeliveryStatusText(row.logistics_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="po_count" label="採購單數" width="100" />
        <el-table-column prop="carrier" label="承運商" width="120">
          <template #default="{ row }">
            {{ row.carrier || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="tracking_number" label="追蹤號碼" width="150">
          <template #default="{ row }">
            <div class="tracking-cell">
              {{ row.tracking_number || '-' }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="expected_delivery_date" label="預期到貨日" width="120">
          <template #default="{ row }">
            {{ formatDate(row.expected_delivery_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="remarks" label="備註" width="200">
          <template #default="{ row }">
            <div class="remarks-cell">
              {{ row.remarks || '-' }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <div class="action-buttons">
              <!-- Status Update Button -->
              <el-button 
                type="primary" 
                size="small" 
                @click="showStatusUpdateDialog(row)"
              >
                更新狀態
              </el-button>
              
              <!-- Remarks Update Button -->
              <el-button 
                size="small" 
                @click="showRemarksDialog(row)"
              >
                備註
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </div>

    <!-- Status Update Dialog -->
    <el-dialog
      v-model="statusDialogVisible"
      title="更新集運物流狀態"
      width="700px"
    >
      <el-form 
        ref="statusFormRef"
        :model="statusForm"
        :rules="statusRules"
        label-width="120px"
      >
        <el-form-item label="集運單ID">
          <el-input v-model="statusForm.consolidation_id" disabled />
        </el-form-item>
        <el-form-item label="集運單名稱">
          <el-input v-model="statusForm.consolidation_name" disabled />
        </el-form-item>
        <el-form-item label="目前狀態">
          <el-tag :type="getDeliveryStatusType(statusForm.current_status)">
            {{ getDeliveryStatusText(statusForm.current_status) }}
          </el-tag>
        </el-form-item>
        <el-form-item label="新狀態" prop="new_status">
          <el-select v-model="statusForm.new_status" placeholder="選擇新狀態">
            <el-option label="已發貨" value="shipped" />
            <el-option label="對方海關" value="foreign_customs" />
            <el-option label="台灣海關" value="taiwan_customs" />
            <el-option label="運送中" value="in_transit" />
            <el-option label="已到貨" value="delivered" />
          </el-select>
        </el-form-item>
        <el-form-item label="預期到貨日">
          <el-date-picker
            v-model="statusForm.expected_date"
            type="date"
            placeholder="選擇預期到貨日期"
            :disabled-date="(date: Date) => date < new Date()"
          />
        </el-form-item>
        <el-form-item label="承運商">
          <el-input v-model="statusForm.carrier" placeholder="例如：DHL Express" />
        </el-form-item>
        <el-form-item label="追蹤號碼">
          <el-input v-model="statusForm.tracking_number" placeholder="例如：1234567890" />
        </el-form-item>
        <el-form-item label="海關申報號">
          <el-input v-model="statusForm.customs_declaration_no" placeholder="海關申報號碼" />
        </el-form-item>
        <el-form-item label="備註/追蹤信息">
          <el-input
            v-model="statusForm.remarks"
            type="textarea"
            rows="3"
            placeholder="請輸入物流狀態更新備註或追蹤信息"
          />
        </el-form-item>
        <el-form-item label="物流備註">
          <el-input
            v-model="statusForm.logistics_notes"
            type="textarea"
            rows="2"
            placeholder="詳細物流備註"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveStatusUpdate" :loading="saving">
          更新狀態
        </el-button>
      </template>
    </el-dialog>

    <!-- Remarks Dialog -->
    <el-dialog
      v-model="remarksDialogVisible"
      title="更新集運備註"
      width="500px"
    >
      <el-form 
        ref="remarksFormRef"
        :model="remarksForm"
        label-width="120px"
      >
        <el-form-item label="集運單ID">
          <el-input v-model="remarksForm.consolidation_id" disabled />
        </el-form-item>
        <el-form-item label="備註/追蹤信息">
          <el-input
            v-model="remarksForm.remarks"
            type="textarea"
            rows="4"
            placeholder="請輸入集運備註、物流追蹤號碼或其他相關信息"
          />
        </el-form-item>
        <el-alert
          title="備註更新說明"
          description="更新集運單備註將自動同步到該集運單內的所有採購單和項目"
          type="info"
          :closable="false"
          show-icon
        />
      </el-form>
      <template #footer>
        <el-button @click="remarksDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRemarks" :loading="saving">
          儲存
        </el-button>
      </template>
    </el-dialog>

    <!-- Status Progress Timeline -->
    <div class="timeline-container" v-if="selectedConsolidation">
      <el-card>
        <template #header>
          <div class="timeline-header">
            <span>物流狀態進度：{{ selectedConsolidation.consolidation_name }}</span>
          </div>
        </template>
        <el-timeline>
          <el-timeline-item
            v-for="(stage, index) in getTimelineStages(selectedConsolidation.logistics_status)"
            :key="index"
            :type="stage.type"
            :icon="stage.icon"
            :timestamp="stage.timestamp"
          >
            <div class="timeline-content">
              <h4>{{ stage.title }}</h4>
              <p v-if="stage.description">{{ stage.description }}</p>
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/format'
import { deliveryApi, type ConsolidationOrder } from '@/api/delivery.ts'

// Reactive data
const loading = ref(false)
const saving = ref(false)
const consolidationData = ref<ConsolidationOrder[]>([])
const summary = ref({
  total_consolidations: 0,
  total_purchase_orders: 0,
  status_distribution: {} as Record<string, number>
})

// Dialog states
const statusDialogVisible = ref(false)
const remarksDialogVisible = ref(false)

// Form refs
const statusFormRef = ref()
const remarksFormRef = ref()

// Selected consolidation
const selectedConsolidation = ref<ConsolidationOrder | null>(null)

// Expanded rows for table
const expandedRows = ref<string[]>([])

const filters = ref({
  consolidationId: '',
  logisticsStatus: ''
})

const pagination = ref({
  page: 1,
  size: 20,
  total: 0
})

// Status Update Form
const statusForm = ref({
  consolidation_id: '',
  consolidation_name: '',
  current_status: '',
  new_status: '',
  expected_date: '',
  carrier: '',
  tracking_number: '',
  customs_declaration_no: '',
  remarks: '',
  logistics_notes: ''
})

const statusRules = {
  new_status: [
    { required: true, message: '請選擇新狀態', trigger: 'change' }
  ]
}

// Remarks Form
const remarksForm = ref({
  consolidation_id: '',
  remarks: ''
})

// Computed
const getStatusCount = (status: string) => {
  return summary.value.status_distribution[status] || 0
}

// Methods
const loadData = async () => {
  loading.value = true
  try {
    const response = await deliveryApi.getConsolidationList({
      page: pagination.value.page,
      page_size: pagination.value.size,
      consolidation_id: filters.value.consolidationId,
      logistics_status: filters.value.logisticsStatus
    })
    
    if (response.success) {
      consolidationData.value = response.data
      pagination.value.total = response.pagination.total
      summary.value = response.summary
    } else {
      throw new Error(response.error?.message || 'API調用失敗')
    }
  } catch (error) {
    console.error('載入集運列表失敗:', error)
    ElMessage.error('載入資料失敗')
    
    // Fallback to mock data for development
    loadMockData()
  } finally {
    loading.value = false
  }
}

const loadMockData = () => {
  // Mock data matching PRD structure
  consolidationData.value = [
    {
      consolidation_id: 'CONS20250110001',
      consolidation_name: 'Consolidation_20250110_001',
      logistics_status: 'foreign_customs',
      expected_delivery_date: '2025-01-25',
      carrier: 'DHL Express',
      tracking_number: '1234567890',
      remarks: 'DHL追蹤號：1234567890，預計海關清關：2025-01-20',
      po_count: 2,
      purchase_orders: [
        {
          purchase_order_no: 'PO20250110002',
          supplier_name: '美商英特爾',
          supplier_region: 'international',
          delivery_status: 'foreign_customs',
          remarks: 'DHL追蹤號：1234567890',
          subtotal: 280000,
          items_count: 5,
          added_at: '2025-01-10T10:30:00Z'
        },
        {
          purchase_order_no: 'PO20250110004',
          supplier_name: '日商索尼',
          supplier_region: 'international',
          delivery_status: 'foreign_customs',
          remarks: 'DHL追蹤號：1234567890',
          subtotal: 150000,
          items_count: 3,
          added_at: '2025-01-10T10:30:00Z'
        }
      ],
      created_by: 1,
      created_at: '2025-01-10T10:30:00Z',
      updated_at: '2025-01-10T14:20:00Z'
    },
    {
      consolidation_id: 'CONS20250109001',
      consolidation_name: 'Consolidation_20250109_001',
      logistics_status: 'delivered',
      expected_delivery_date: '2025-01-15',
      actual_delivery_date: '2025-01-14',
      carrier: 'FedEx',
      tracking_number: '9876543210',
      remarks: 'FedEx追蹤號：9876543210，已順利到貨',
      po_count: 1,
      purchase_orders: [
        {
          purchase_order_no: 'PO20250109001',
          supplier_name: '韓商三星',
          supplier_region: 'international',
          delivery_status: 'delivered',
          remarks: 'FedEx追蹤號：9876543210',
          subtotal: 320000,
          items_count: 4,
          added_at: '2025-01-09T09:15:00Z'
        }
      ],
      created_by: 1,
      created_at: '2025-01-09T09:15:00Z',
      updated_at: '2025-01-14T16:45:00Z'
    }
  ]
  
  summary.value = {
    total_consolidations: 2,
    total_purchase_orders: 3,
    status_distribution: {
      shipped: 0,
      foreign_customs: 1,
      taiwan_customs: 0,
      in_transit: 0,
      delivered: 1
    }
  }
  
  pagination.value.total = 2
}

const resetFilters = () => {
  filters.value = {
    consolidationId: '',
    logisticsStatus: ''
  }
  pagination.value.page = 1
  loadData()
}

const refreshData = () => {
  loadData()
  ElMessage.success('資料已重新整理')
}

const handleRowExpand = (row: ConsolidationOrder, expanded: boolean) => {
  if (expanded) {
    expandedRows.value.push(row.consolidation_id)
  } else {
    const index = expandedRows.value.indexOf(row.consolidation_id)
    if (index > -1) {
      expandedRows.value.splice(index, 1)
    }
  }
}

// Status Update Dialog
const showStatusUpdateDialog = (row: ConsolidationOrder) => {
  selectedConsolidation.value = row
  statusForm.value = {
    consolidation_id: row.consolidation_id,
    consolidation_name: row.consolidation_name,
    current_status: row.logistics_status,
    new_status: '',
    expected_date: row.expected_delivery_date || '',
    carrier: row.carrier || '',
    tracking_number: row.tracking_number || '',
    customs_declaration_no: row.customs_declaration_no || '',
    remarks: row.remarks || '',
    logistics_notes: ''
  }
  statusDialogVisible.value = true
}

const saveStatusUpdate = async () => {
  try {
    await statusFormRef.value.validate()
    
    saving.value = true
    
    const response = await deliveryApi.updateConsolidationStatus(statusForm.value.consolidation_id, {
      new_status: statusForm.value.new_status,
      expected_date: statusForm.value.expected_date,
      carrier: statusForm.value.carrier,
      tracking_number: statusForm.value.tracking_number,
      customs_declaration_no: statusForm.value.customs_declaration_no,
      remarks: statusForm.value.remarks,
      logistics_notes: statusForm.value.logistics_notes
    })
    
    if (response.success) {
      statusDialogVisible.value = false
      ElMessage.success(`狀態更新成功，影響 ${response.data.affected_pos} 個採購單和 ${response.data.affected_items} 個項目`)
      loadData() // Refresh data
    } else {
      throw new Error(response.error?.message || '狀態更新失敗')
    }
  } catch (error) {
    console.error('更新集運狀態失敗:', error)
    ElMessage.error('更新狀態失敗')
  } finally {
    saving.value = false
  }
}

// Remarks Dialog
const showRemarksDialog = (row: ConsolidationOrder) => {
  selectedConsolidation.value = row
  remarksForm.value = {
    consolidation_id: row.consolidation_id,
    remarks: row.remarks || ''
  }
  remarksDialogVisible.value = true
}

const saveRemarks = async () => {
  try {
    saving.value = true
    
    // Use the consolidation status update API with only remarks
    const response = await deliveryApi.updateConsolidationStatus(remarksForm.value.consolidation_id, {
      new_status: selectedConsolidation.value!.logistics_status, // Keep current status
      remarks: remarksForm.value.remarks
    })
    
    if (response.success) {
      remarksDialogVisible.value = false
      ElMessage.success('備註更新成功')
      loadData() // Refresh data
    } else {
      throw new Error(response.error?.message || '備註更新失敗')
    }
  } catch (error) {
    console.error('更新集運備註失敗:', error)
    ElMessage.error('更新備註失敗')
  } finally {
    saving.value = false
  }
}

const getDeliveryStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    shipped: 'primary',
    foreign_customs: 'warning',
    taiwan_customs: 'warning', 
    in_transit: 'primary',
    delivered: 'success'
  }
  return statusMap[status] || 'info'
}

const getDeliveryStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    shipped: '已發貨',
    foreign_customs: '對方海關',
    taiwan_customs: '台灣海關',
    in_transit: '運送中',
    delivered: '已到貨'
  }
  return statusMap[status] || status
}

const getTimelineStages = (currentStatus: string) => {
  const stages = [
    { key: 'shipped', title: '已發貨', description: '商品已從供應商處發出' },
    { key: 'foreign_customs', title: '對方海關', description: '商品在出口國海關清關中' },
    { key: 'taiwan_customs', title: '台灣海關', description: '商品在台灣海關清關中' },
    { key: 'in_transit', title: '運送中', description: '商品正在運送途中' },
    { key: 'delivered', title: '已到貨', description: '商品已成功到達目的地' }
  ]
  
  const currentIndex = stages.findIndex(stage => stage.key === currentStatus)
  
  return stages.map((stage, index) => {
    const isCompleted = index <= currentIndex
    const isCurrent = index === currentIndex
    
    return {
      ...stage,
      type: isCompleted ? 'success' : 'info',
      icon: isCompleted ? 'success' : isCurrent ? 'warning' : 'info',
      timestamp: isCurrent ? '進行中' : isCompleted ? '已完成' : '待處理'
    }
  })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.consolidation-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .header-actions {
    display: flex;
    gap: 8px;
  }
}

.page-title {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.stats-container {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  
  &.info {
    border-left: 4px solid #409eff;
  }
  
  &.warning {
    border-left: 4px solid #e6a23c;
  }
  
  &.success {
    border-left: 4px solid #67c23a;
  }
  
  .stat-content {
    .stat-number {
      font-size: 24px;
      font-weight: bold;
      color: #303133;
      margin-bottom: 5px;
    }
    
    .stat-label {
      font-size: 14px;
      color: #606266;
    }
  }
}

.filters {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.table-container {
  background: white;
  border-radius: 4px;
  padding: 20px;
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.expand-content {
  padding: 20px;
  background: #fafafa;
  border-radius: 4px;
  margin: 0 20px;
  
  h4 {
    margin: 0 0 16px 0;
    color: #303133;
    font-size: 16px;
  }
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.remarks-cell, .tracking-cell {
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.timeline-container {
  margin-top: 20px;
}

.timeline-header {
  display: flex;
  align-items: center;
  font-weight: 500;
  color: #303133;
}

.timeline-content {
  h4 {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: #303133;
  }
  
  p {
    margin: 0;
    font-size: 12px;
    color: #606266;
  }
}

/* Form and dialog styling same as DeliveryMaintenance.vue */
:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-dialog__header) {
  padding: 20px 20px 10px;
  
  .el-dialog__title {
    font-size: 18px;
    font-weight: 600;
  }
}

:deep(.el-dialog__body) {
  padding: 10px 20px;
}

:deep(.el-dialog__footer) {
  padding: 10px 20px 20px;
  text-align: right;
}

:deep(.el-textarea__inner) {
  resize: vertical;
}

:deep(.el-form-item) {
  margin-bottom: 18px;
}

/* Table styling */
:deep(.el-table) {
  .el-table__header {
    th {
      background-color: #fafafa;
      color: #606266;
      font-weight: 500;
    }
  }
  
  .el-table__body {
    tr:hover > td {
      background-color: #f5f7fa;
    }
  }
  
  .el-table__expand-column .el-table__expand-icon {
    font-size: 12px;
  }
}

/* Tags styling */
:deep(.el-tag) {
  border-radius: 4px;
  
  &.el-tag--success {
    background-color: #f0f9ff;
    color: #67c23a;
    border-color: #b3e5d1;
  }
  
  &.el-tag--info {
    background-color: #f4f4f5;
    color: #909399;
    border-color: #d3d4d6;
  }
  
  &.el-tag--warning {
    background-color: #fdf6ec;
    color: #e6a23c;
    border-color: #f5dab1;
  }
  
  &.el-tag--primary {
    background-color: #ecf5ff;
    color: #409eff;
    border-color: #b3d8ff;
  }
}

/* Timeline styling */
:deep(.el-timeline-item__timestamp) {
  font-size: 12px;
  color: #606266;
}
</style>