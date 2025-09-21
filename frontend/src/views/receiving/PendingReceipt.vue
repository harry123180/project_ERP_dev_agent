<template>
  <div class="pending-receipt">
    <div class="page-header">
      <h1 class="page-title">待收貨列表</h1>
      <div class="header-actions">
        <el-button type="success" @click="batchReceive" :disabled="!selectedItems.length">
          <el-icon><Checked /></el-icon>
          批量收貨 ({{ selectedItems.length }})
        </el-button>
        <el-button type="primary" @click="refreshData">
          <el-icon><Refresh /></el-icon>
          重新整理
        </el-button>
      </div>
    </div>

    <!-- Statistics Cards -->
    <div class="statistics-container">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="statistic-card">
            <el-statistic title="待收貨訂單" :value="statistics.pending" />
            <div class="statistic-icon pending">
              <el-icon><Clock /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="statistic-card">
            <el-statistic title="已到貨" :value="statistics.arrived" />
            <div class="statistic-icon arrived">
              <el-icon><Van /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="statistic-card">
            <el-statistic title="延期到貨" :value="statistics.delayed" />
            <div class="statistic-icon delayed">
              <el-icon><Warning /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="statistic-card">
            <el-statistic title="本月收貨" :value="statistics.thisMonth" />
            <div class="statistic-icon this-month">
              <el-icon><Calendar /></el-icon>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div class="filters">
      <el-form :model="filters" inline>
        <el-form-item label="採購單號">
          <el-input 
            v-model="filters.poNumber" 
            placeholder="輸入採購單號"
            clearable
          />
        </el-form-item>
        <el-form-item label="供應商">
          <el-select v-model="filters.supplier" placeholder="選擇供應商" clearable>
            <el-option label="全部" value="" />
            <el-option label="台積電材料供應商" value="supplier_a" />
            <el-option label="精密機械公司" value="supplier_b" />
            <el-option label="電子元件供應商" value="supplier_c" />
          </el-select>
        </el-form-item>
        <el-form-item label="收貨狀態">
          <el-select v-model="filters.status" placeholder="選擇狀態" clearable>
            <el-option label="全部" value="" />
            <el-option label="待收貨" value="pending" />
            <el-option label="已到貨" value="arrived" />
            <el-option label="部分收貨" value="partial" />
            <el-option label="延期到貨" value="delayed" />
          </el-select>
        </el-form-item>
        <el-form-item label="預計到貨日">
          <el-date-picker
            v-model="filters.expectedDate"
            type="date"
            placeholder="選擇日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜尋</el-button>
          <el-button @click="resetFilters">重設</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-container">
      <el-table 
        :data="pendingReceiptData" 
        :loading="loading"
        stripe
        @selection-change="handleSelectionChange"
        @row-click="viewReceiptDetail"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="po_number" label="採購單號" width="140" />
        <el-table-column prop="supplier_name" label="供應商" width="180" />
        <el-table-column prop="item_name" label="品項名稱" width="200" />
        <el-table-column prop="ordered_quantity" label="訂購數量" width="100" />
        <el-table-column prop="received_quantity" label="已收數量" width="100" />
        <el-table-column prop="pending_quantity" label="待收數量" width="100">
          <template #default="{ row }">
            <span class="pending-quantity">{{ row.pending_quantity }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="expected_delivery_date" label="預計到貨日" width="120">
          <template #default="{ row }">
            {{ formatDate(row.expected_delivery_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="狀態" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="days_overdue" label="延期天數" width="100">
          <template #default="{ row }">
            <span v-if="row.days_overdue > 0" class="overdue-text">
              {{ row.days_overdue }} 天
            </span>
            <span v-else class="on-time-text">準時</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click.stop="receiveGoods(row)">收貨</el-button>
            <el-button size="small" type="primary" @click.stop="viewReceiptDetail(row)">
              詳情
            </el-button>
            <el-button 
              size="small" 
              type="warning" 
              @click.stop="updateDeliveryDate(row)"
              v-if="row.status === 'delayed'"
            >
              更新交期
            </el-button>
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

    <!-- Receive Goods Dialog -->
    <el-dialog
      v-model="receiveDialogVisible"
      title="收貨確認"
      width="600px"
    >
      <el-form 
        ref="receiveFormRef"
        :model="receiveForm"
        :rules="receiveRules"
        label-width="120px"
      >
        <el-form-item label="採購單號">
          <el-input v-model="receiveForm.po_number" disabled />
        </el-form-item>
        <el-form-item label="品項名稱">
          <el-input v-model="receiveForm.item_name" disabled />
        </el-form-item>
        <el-form-item label="待收數量">
          <el-input v-model="receiveForm.pending_quantity" disabled />
        </el-form-item>
        <el-form-item label="實收數量" prop="received_quantity">
          <el-input-number
            v-model="receiveForm.received_quantity"
            :min="0"
            :max="receiveForm.pending_quantity"
            controls-position="right"
          />
        </el-form-item>
        <el-form-item label="收貨日期" prop="received_date">
          <el-date-picker
            v-model="receiveForm.received_date"
            type="date"
            placeholder="選擇收貨日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="收貨地點" prop="location">
          <el-select v-model="receiveForm.location" placeholder="選擇收貨地點">
            <el-option label="倉庫A" value="warehouse_a" />
            <el-option label="倉庫B" value="warehouse_b" />
            <el-option label="暫存區" value="temp_storage" />
          </el-select>
        </el-form-item>
        <el-form-item label="品質狀況" prop="quality_status">
          <el-select v-model="receiveForm.quality_status" placeholder="選擇品質狀況">
            <el-option label="良好" value="good" />
            <el-option label="輕微瑕疵" value="minor_defect" />
            <el-option label="重大瑕疵" value="major_defect" />
            <el-option label="不合格" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item label="備註">
          <el-input
            v-model="receiveForm.notes"
            type="textarea"
            rows="3"
            placeholder="收貨備註（如有異常請詳細說明）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="receiveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmReceive" :loading="saving">
          確認收貨
        </el-button>
      </template>
    </el-dialog>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="`收貨詳情 - ${selectedItem.po_number}`"
      width="800px"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="採購單號">{{ selectedItem.po_number }}</el-descriptions-item>
        <el-descriptions-item label="供應商">{{ selectedItem.supplier_name }}</el-descriptions-item>
        <el-descriptions-item label="品項名稱">{{ selectedItem.item_name }}</el-descriptions-item>
        <el-descriptions-item label="品項編號">{{ selectedItem.item_code }}</el-descriptions-item>
        <el-descriptions-item label="訂購數量">{{ selectedItem.ordered_quantity }}</el-descriptions-item>
        <el-descriptions-item label="已收數量">{{ selectedItem.received_quantity }}</el-descriptions-item>
        <el-descriptions-item label="待收數量">{{ selectedItem.pending_quantity }}</el-descriptions-item>
        <el-descriptions-item label="單位">{{ selectedItem.unit }}</el-descriptions-item>
        <el-descriptions-item label="預計到貨日">{{ formatDate(selectedItem.expected_delivery_date) }}</el-descriptions-item>
        <el-descriptions-item label="狀態">
          <el-tag :type="getStatusType(selectedItem.status)">
            {{ getStatusText(selectedItem.status) }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <div class="receipt-history" v-if="selectedItem.receipt_history">
        <h4>收貨記錄</h4>
        <el-table :data="selectedItem.receipt_history" size="small">
          <el-table-column prop="received_date" label="收貨日期" width="120">
            <template #default="{ row }">
              {{ formatDate(row.received_date) }}
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="收貨數量" width="100" />
          <el-table-column prop="location" label="收貨地點" width="120" />
          <el-table-column prop="quality_status" label="品質狀況" width="100">
            <template #default="{ row }">
              <el-tag :type="getQualityStatusType(row.quality_status)" size="small">
                {{ getQualityStatusText(row.quality_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="received_by" label="收貨人" width="100" />
          <el-table-column prop="notes" label="備註" />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">關閉</el-button>
        <el-button type="primary" @click="receiveGoods(selectedItem)">立即收貨</el-button>
      </template>
    </el-dialog>

    <!-- Development Notice -->
    <div class="development-notice">
      <el-alert
        title="功能開發中"
        description="待收貨列表功能正在開發中，目前顯示的是模擬資料。完整功能將包含批量收貨、品質檢驗、庫存更新等。"
        type="info"
        show-icon
        :closable="false"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Checked, 
  Refresh, 
  Clock, 
  Van, 
  Warning, 
  Calendar 
} from '@element-plus/icons-vue'
import { formatDate } from '@/utils/format'

// Reactive data
const loading = ref(false)
const saving = ref(false)
const pendingReceiptData = ref([])
const selectedItems = ref([])
const receiveDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const selectedItem = ref({})
const receiveFormRef = ref()

const filters = ref({
  poNumber: '',
  supplier: '',
  status: '',
  expectedDate: ''
})

const pagination = ref({
  page: 1,
  size: 20,
  total: 0
})

const receiveForm = ref({
  id: '',
  po_number: '',
  item_name: '',
  pending_quantity: 0,
  received_quantity: 0,
  received_date: '',
  location: '',
  quality_status: '',
  notes: ''
})

const receiveRules = {
  received_quantity: [
    { required: true, message: '請輸入實收數量', trigger: 'blur' }
  ],
  received_date: [
    { required: true, message: '請選擇收貨日期', trigger: 'change' }
  ],
  location: [
    { required: true, message: '請選擇收貨地點', trigger: 'change' }
  ],
  quality_status: [
    { required: true, message: '請選擇品質狀況', trigger: 'change' }
  ]
}

// Mock data
const mockReceiptData = [
  {
    id: '1',
    po_number: 'PO202501001',
    supplier_name: '台積電材料供應商',
    item_name: '半導體材料A',
    item_code: 'IC001',
    ordered_quantity: 100,
    received_quantity: 0,
    pending_quantity: 100,
    unit: '個',
    expected_delivery_date: '2025-01-15',
    status: 'pending',
    days_overdue: 0,
    receipt_history: []
  },
  {
    id: '2',
    po_number: 'PO202501002',
    supplier_name: '精密機械公司',
    item_name: '精密零件B',
    item_code: 'MC002',
    ordered_quantity: 50,
    received_quantity: 20,
    pending_quantity: 30,
    unit: '組',
    expected_delivery_date: '2025-01-12',
    status: 'partial',
    days_overdue: 0,
    receipt_history: [
      {
        received_date: '2025-01-10',
        quantity: 20,
        location: '倉庫A',
        quality_status: 'good',
        received_by: '王收貨員',
        notes: '品質良好'
      }
    ]
  },
  {
    id: '3',
    po_number: 'PO202501003',
    supplier_name: '電子元件供應商',
    item_name: 'IC晶片套裝',
    item_code: 'EC003',
    ordered_quantity: 20,
    received_quantity: 0,
    pending_quantity: 20,
    unit: '套',
    expected_delivery_date: '2025-01-08',
    status: 'delayed',
    days_overdue: 2,
    receipt_history: []
  }
]

// Computed statistics
const statistics = computed(() => {
  const today = new Date()
  const thisMonth = today.getMonth()
  
  return {
    pending: pendingReceiptData.value.filter(item => item.status === 'pending').length,
    arrived: pendingReceiptData.value.filter(item => item.status === 'arrived').length,
    delayed: pendingReceiptData.value.filter(item => item.status === 'delayed').length,
    thisMonth: pendingReceiptData.value.filter(item => {
      if (!item.receipt_history || item.receipt_history.length === 0) return false
      const latestReceipt = new Date(item.receipt_history[item.receipt_history.length - 1].received_date)
      return latestReceipt.getMonth() === thisMonth
    }).length
  }
})

// Methods
const loadData = async () => {
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))
    
    let filteredData = [...mockReceiptData]
    
    // Apply filters
    if (filters.value.poNumber) {
      filteredData = filteredData.filter(item => 
        item.po_number.toLowerCase().includes(filters.value.poNumber.toLowerCase())
      )
    }
    
    if (filters.value.supplier) {
      filteredData = filteredData.filter(item => item.supplier_name.includes(filters.value.supplier))
    }
    
    if (filters.value.status) {
      filteredData = filteredData.filter(item => item.status === filters.value.status)
    }
    
    if (filters.value.expectedDate) {
      filteredData = filteredData.filter(item => item.expected_delivery_date === filters.value.expectedDate)
    }
    
    pendingReceiptData.value = filteredData
    pagination.value.total = filteredData.length
  } catch (error) {
    console.error('載入待收貨資料失敗:', error)
    ElMessage.error('載入待收貨資料失敗')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.value = {
    poNumber: '',
    supplier: '',
    status: '',
    expectedDate: ''
  }
  pagination.value.page = 1
  loadData()
}

const refreshData = () => {
  loadData()
  ElMessage.success('資料已重新整理')
}

const handleSelectionChange = (selection: any[]) => {
  selectedItems.value = selection
}

const receiveGoods = (row: any) => {
  receiveForm.value = {
    id: row.id,
    po_number: row.po_number,
    item_name: row.item_name,
    pending_quantity: row.pending_quantity,
    received_quantity: row.pending_quantity,
    received_date: new Date().toISOString().split('T')[0],
    location: '',
    quality_status: '',
    notes: ''
  }
  receiveDialogVisible.value = true
}

const confirmReceive = async () => {
  try {
    await receiveFormRef.value.validate()
    
    saving.value = true
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Update local data
    const index = pendingReceiptData.value.findIndex(item => item.id === receiveForm.value.id)
    if (index !== -1) {
      const item = pendingReceiptData.value[index]
      item.received_quantity += receiveForm.value.received_quantity
      item.pending_quantity -= receiveForm.value.received_quantity
      
      // Add to receipt history
      if (!item.receipt_history) item.receipt_history = []
      item.receipt_history.push({
        received_date: receiveForm.value.received_date,
        quantity: receiveForm.value.received_quantity,
        location: receiveForm.value.location,
        quality_status: receiveForm.value.quality_status,
        received_by: '當前用戶',
        notes: receiveForm.value.notes
      })
      
      // Update status
      if (item.pending_quantity === 0) {
        item.status = 'completed'
      } else {
        item.status = 'partial'
      }
    }
    
    receiveDialogVisible.value = false
    ElMessage.success('收貨成功')
  } catch (error) {
    console.error('收貨失敗:', error)
    ElMessage.error('收貨失敗')
  } finally {
    saving.value = false
  }
}

const batchReceive = () => {
  ElMessage.success('批量收貨功能開發中')
}

const updateDeliveryDate = (row: any) => {
  ElMessage.success('更新交期功能開發中')
}

const viewReceiptDetail = (row: any) => {
  selectedItem.value = row
  detailDialogVisible.value = true
}

// Status/Type getters
const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: 'warning',
    arrived: 'success',
    partial: 'primary',
    delayed: 'danger',
    completed: 'info'
  }
  return statusMap[status] || ''
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待收貨',
    arrived: '已到貨',
    partial: '部分收貨',
    delayed: '延期到貨',
    completed: '收貨完成'
  }
  return statusMap[status] || status
}

const getQualityStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    good: 'success',
    minor_defect: 'warning',
    major_defect: 'danger',
    rejected: 'danger'
  }
  return statusMap[status] || ''
}

const getQualityStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    good: '良好',
    minor_defect: '輕微瑕疵',
    major_defect: '重大瑕疵',
    rejected: '不合格'
  }
  return statusMap[status] || status
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.pending-receipt {
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

.statistics-container {
  margin-bottom: 20px;

  .statistic-card {
    position: relative;
    
    .statistic-icon {
      position: absolute;
      top: 16px;
      right: 16px;
      font-size: 24px;
      opacity: 0.6;
      
      &.pending { color: #e6a23c; }
      &.arrived { color: #67c23a; }
      &.delayed { color: #f56c6c; }
      &.this-month { color: #409eff; }
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

.pending-quantity {
  font-weight: bold;
  color: #409eff;
}

.overdue-text {
  color: #f56c6c;
  font-weight: bold;
}

.on-time-text {
  color: #67c23a;
}

.receipt-history {
  margin-top: 20px;
  
  h4 {
    margin: 16px 0 12px 0;
    color: #303133;
  }
}

.development-notice {
  margin-top: 20px;
}

:deep(.el-alert__description) {
  margin-top: 8px;
  font-size: 13px;
}

:deep(.el-statistic__content) {
  font-size: 32px;
  font-weight: bold;
}

:deep(.el-select) {
  width: 100%;
}
</style>