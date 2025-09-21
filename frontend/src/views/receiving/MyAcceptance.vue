<template>
  <div class="my-acceptance">
    <div class="page-header">
      <h1 class="page-title">我的驗收</h1>
      <div class="header-actions">
        <el-button type="success" @click="batchApprove" :disabled="!selectedItems.length">
          <el-icon><CircleCheck /></el-icon>
          批量通過 ({{ selectedItems.length }})
        </el-button>
        <el-button type="danger" @click="batchReject" :disabled="!selectedItems.length">
          <el-icon><CircleClose /></el-icon>
          批量退回 ({{ selectedItems.length }})
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
            <el-statistic title="待驗收" :value="statistics.pending" />
            <div class="statistic-icon pending">
              <el-icon><Clock /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="statistic-card">
            <el-statistic title="驗收中" :value="statistics.inspecting" />
            <div class="statistic-icon inspecting">
              <el-icon><View /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="statistic-card">
            <el-statistic title="已通過" :value="statistics.approved" />
            <div class="statistic-icon approved">
              <el-icon><CircleCheckFilled /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="statistic-card">
            <el-statistic title="已退回" :value="statistics.rejected" />
            <div class="statistic-icon rejected">
              <el-icon><CircleCloseFilled /></el-icon>
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
        <el-form-item label="驗收狀態">
          <el-select v-model="filters.status" placeholder="選擇狀態" clearable>
            <el-option label="全部" value="" />
            <el-option label="待驗收" value="pending" />
            <el-option label="驗收中" value="inspecting" />
            <el-option label="已通過" value="approved" />
            <el-option label="已退回" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item label="優先級">
          <el-select v-model="filters.priority" placeholder="選擇優先級" clearable>
            <el-option label="全部" value="" />
            <el-option label="緊急" value="urgent" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
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
        :data="acceptanceData" 
        :loading="loading"
        stripe
        @selection-change="handleSelectionChange"
        @row-click="viewAcceptanceDetail"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="po_number" label="採購單號" width="140" />
        <el-table-column prop="supplier_name" label="供應商" width="160" />
        <el-table-column prop="item_name" label="品項名稱" width="180" />
        <el-table-column prop="received_quantity" label="收貨數量" width="100" />
        <el-table-column prop="received_date" label="收貨日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.received_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="優先級" width="100">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" size="small">
              {{ getPriorityText(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="驗收狀態" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assigned_date" label="指派日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.assigned_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="days_pending" label="待驗天數" width="100">
          <template #default="{ row }">
            <span :class="{ 'overdue-text': row.days_pending > 3 }">
              {{ row.days_pending }} 天
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <el-button size="small" @click.stop="startInspection(row)" v-if="row.status === 'pending'">
              開始驗收
            </el-button>
            <el-button 
              size="small" 
              type="success" 
              @click.stop="approveAcceptance(row)"
              v-if="['pending', 'inspecting'].includes(row.status)"
            >
              通過
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click.stop="rejectAcceptance(row)"
              v-if="['pending', 'inspecting'].includes(row.status)"
            >
              退回
            </el-button>
            <el-button size="small" type="primary" @click.stop="viewAcceptanceDetail(row)">
              詳情
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

    <!-- Approval Dialog -->
    <el-dialog
      v-model="approvalDialogVisible"
      :title="isApproving ? '驗收通過' : '驗收退回'"
      width="600px"
    >
      <el-form 
        ref="approvalFormRef"
        :model="approvalForm"
        :rules="approvalRules"
        label-width="120px"
      >
        <el-form-item label="採購單號">
          <el-input v-model="approvalForm.po_number" disabled />
        </el-form-item>
        <el-form-item label="品項名稱">
          <el-input v-model="approvalForm.item_name" disabled />
        </el-form-item>
        <el-form-item label="收貨數量">
          <el-input v-model="approvalForm.received_quantity" disabled />
        </el-form-item>
        <el-form-item v-if="isApproving" label="驗收數量" prop="accepted_quantity">
          <el-input-number
            v-model="approvalForm.accepted_quantity"
            :min="0"
            :max="approvalForm.received_quantity"
            controls-position="right"
          />
        </el-form-item>
        <el-form-item label="品質評級" prop="quality_rating">
          <el-rate
            v-model="approvalForm.quality_rating"
            :max="5"
            show-text
            :texts="['很差', '差', '一般', '好', '優秀']"
          />
        </el-form-item>
        <el-form-item label="驗收項目">
          <el-checkbox-group v-model="approvalForm.inspection_items">
            <el-checkbox label="外觀檢查">外觀檢查</el-checkbox>
            <el-checkbox label="尺寸測量">尺寸測量</el-checkbox>
            <el-checkbox label="功能測試">功能測試</el-checkbox>
            <el-checkbox label="材質檢驗">材質檢驗</el-checkbox>
            <el-checkbox label="包裝檢查">包裝檢查</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item v-if="!isApproving" label="退回原因" prop="rejection_reason">
          <el-select v-model="approvalForm.rejection_reason" placeholder="選擇退回原因">
            <el-option label="品質不符合規格" value="quality_issue" />
            <el-option label="數量不符" value="quantity_mismatch" />
            <el-option label="包裝損壞" value="package_damage" />
            <el-option label="規格錯誤" value="spec_error" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="驗收備註" prop="notes">
          <el-input
            v-model="approvalForm.notes"
            type="textarea"
            rows="4"
            :placeholder="isApproving ? '驗收意見（可選）' : '請詳細說明退回原因'"
          />
        </el-form-item>
        <el-form-item label="照片上傳">
          <el-upload
            class="upload-demo"
            drag
            multiple
            action="#"
            :auto-upload="false"
            :file-list="approvalForm.photos"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              將檔案拖到此處，或<em>點擊上傳</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支援 jpg/png 檔案，且不超過 500kb
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="approvalDialogVisible = false">取消</el-button>
        <el-button 
          :type="isApproving ? 'success' : 'danger'" 
          @click="confirmApproval" 
          :loading="saving"
        >
          {{ isApproving ? '確認通過' : '確認退回' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="`驗收詳情 - ${selectedItem.po_number}`"
      width="900px"
    >
      <el-tabs v-model="activeTab">
        <el-tab-pane label="基本資訊" name="basic">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="採購單號">{{ selectedItem.po_number }}</el-descriptions-item>
            <el-descriptions-item label="供應商">{{ selectedItem.supplier_name }}</el-descriptions-item>
            <el-descriptions-item label="品項名稱">{{ selectedItem.item_name }}</el-descriptions-item>
            <el-descriptions-item label="品項編號">{{ selectedItem.item_code }}</el-descriptions-item>
            <el-descriptions-item label="收貨數量">{{ selectedItem.received_quantity }}</el-descriptions-item>
            <el-descriptions-item label="收貨日期">{{ formatDate(selectedItem.received_date) }}</el-descriptions-item>
            <el-descriptions-item label="驗收狀態">
              <el-tag :type="getStatusType(selectedItem.status)">
                {{ getStatusText(selectedItem.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="優先級">
              <el-tag :type="getPriorityType(selectedItem.priority)" size="small">
                {{ getPriorityText(selectedItem.priority) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="指派日期">{{ formatDate(selectedItem.assigned_date) }}</el-descriptions-item>
            <el-descriptions-item label="待驗天數">{{ selectedItem.days_pending }} 天</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
        
        <el-tab-pane label="驗收記錄" name="history">
          <el-timeline>
            <el-timeline-item 
              v-for="record in selectedItem.acceptance_history" 
              :key="record.id"
              :timestamp="formatDate(record.timestamp)"
            >
              <div class="timeline-content">
                <strong>{{ record.action }}</strong> - {{ record.user }}
                <p v-if="record.comment">{{ record.comment }}</p>
                <el-tag v-if="record.status" :type="getStatusType(record.status)" size="small">
                  {{ getStatusText(record.status) }}
                </el-tag>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-tab-pane>
        
        <el-tab-pane label="品質檢測" name="quality">
          <div class="quality-info" v-if="selectedItem.quality_info">
            <el-row :gutter="20">
              <el-col :span="12">
                <h4>檢測項目</h4>
                <el-tag 
                  v-for="item in selectedItem.quality_info.inspection_items" 
                  :key="item"
                  class="inspection-tag"
                >
                  {{ item }}
                </el-tag>
              </el-col>
              <el-col :span="12">
                <h4>品質評級</h4>
                <el-rate 
                  v-model="selectedItem.quality_info.rating" 
                  disabled 
                  show-text
                  :texts="['很差', '差', '一般', '好', '優秀']"
                />
              </el-col>
            </el-row>
            <div class="quality-notes">
              <h4>檢測備註</h4>
              <p>{{ selectedItem.quality_info.notes || '無' }}</p>
            </div>
          </div>
          <el-empty v-else description="尚未進行品質檢測" />
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button @click="detailDialogVisible = false">關閉</el-button>
        <el-button 
          type="success" 
          @click="approveAcceptance(selectedItem)"
          v-if="['pending', 'inspecting'].includes(selectedItem.status)"
        >
          通過驗收
        </el-button>
        <el-button 
          type="danger" 
          @click="rejectAcceptance(selectedItem)"
          v-if="['pending', 'inspecting'].includes(selectedItem.status)"
        >
          退回驗收
        </el-button>
      </template>
    </el-dialog>

    <!-- Development Notice -->
    <div class="development-notice">
      <el-alert
        title="功能開發中"
        description="我的驗收功能正在開發中，目前顯示的是模擬資料。完整功能將包含品質檢測流程、驗收標準配置、自動化檢測報告等。"
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
  CircleCheck,
  CircleClose,
  Refresh,
  Clock,
  View,
  CircleCheckFilled,
  CircleCloseFilled,
  UploadFilled
} from '@element-plus/icons-vue'
import { formatDate } from '@/utils/format'
import request from '@/utils/request'

// Reactive data
const loading = ref(false)
const saving = ref(false)
const acceptanceData = ref([])
const selectedItems = ref([])
const approvalDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const selectedItem = ref({})
const approvalFormRef = ref()
const isApproving = ref(true)
const activeTab = ref('basic')

const filters = ref({
  poNumber: '',
  supplier: '',
  status: '',
  priority: ''
})

const pagination = ref({
  page: 1,
  size: 20,
  total: 0
})

const approvalForm = ref({
  id: '',
  po_number: '',
  item_name: '',
  received_quantity: 0,
  accepted_quantity: 0,
  quality_rating: 5,
  inspection_items: [],
  rejection_reason: '',
  notes: '',
  photos: []
})

const approvalRules = computed(() => ({
  accepted_quantity: isApproving.value ? [
    { required: true, message: '請輸入驗收數量', trigger: 'blur' }
  ] : [],
  quality_rating: [
    { required: true, message: '請進行品質評級', trigger: 'change' }
  ],
  rejection_reason: !isApproving.value ? [
    { required: true, message: '請選擇退回原因', trigger: 'change' }
  ] : [],
  notes: !isApproving.value ? [
    { required: true, message: '請詳細說明退回原因', trigger: 'blur' }
  ] : []
}))

// Mock data
const mockAcceptanceData = [
  {
    id: '1',
    po_number: 'PO202501001',
    supplier_name: '台積電材料供應商',
    item_name: '半導體材料A',
    item_code: 'IC001',
    received_quantity: 100,
    received_date: '2025-01-12',
    priority: 'high',
    status: 'pending',
    assigned_date: '2025-01-12',
    days_pending: 1,
    acceptance_history: [
      {
        id: 1,
        action: '收貨完成',
        user: '王收貨員',
        timestamp: '2025-01-12 10:00',
        comment: '外觀良好，數量正確',
        status: 'received'
      },
      {
        id: 2,
        action: '指派驗收',
        user: '系統',
        timestamp: '2025-01-12 10:30',
        comment: '指派給當前用戶進行驗收',
        status: 'pending'
      }
    ]
  },
  {
    id: '2',
    po_number: 'PO202501002',
    supplier_name: '精密機械公司',
    item_name: '精密零件B',
    item_code: 'MC002',
    received_quantity: 30,
    received_date: '2025-01-10',
    priority: 'medium',
    status: 'inspecting',
    assigned_date: '2025-01-10',
    days_pending: 3,
    acceptance_history: [
      {
        id: 1,
        action: '收貨完成',
        user: '李收貨員',
        timestamp: '2025-01-10 14:00',
        comment: '',
        status: 'received'
      },
      {
        id: 2,
        action: '開始驗收',
        user: '當前用戶',
        timestamp: '2025-01-11 09:00',
        comment: '開始進行品質檢測',
        status: 'inspecting'
      }
    ],
    quality_info: {
      inspection_items: ['外觀檢查', '尺寸測量', '功能測試'],
      rating: 4,
      notes: '整體品質良好，符合規格要求'
    }
  },
  {
    id: '3',
    po_number: 'PO202501003',
    supplier_name: '電子元件供應商',
    item_name: 'IC晶片套裝',
    item_code: 'EC003',
    received_quantity: 20,
    received_date: '2025-01-08',
    priority: 'urgent',
    status: 'approved',
    assigned_date: '2025-01-08',
    days_pending: 0,
    acceptance_history: [
      {
        id: 1,
        action: '收貨完成',
        user: '趙收貨員',
        timestamp: '2025-01-08 11:00',
        comment: '',
        status: 'received'
      },
      {
        id: 2,
        action: '開始驗收',
        user: '當前用戶',
        timestamp: '2025-01-08 13:00',
        comment: '',
        status: 'inspecting'
      },
      {
        id: 3,
        action: '驗收通過',
        user: '當前用戶',
        timestamp: '2025-01-08 16:00',
        comment: '品質優秀，全部通過驗收',
        status: 'approved'
      }
    ],
    quality_info: {
      inspection_items: ['外觀檢查', '功能測試', '材質檢驗', '包裝檢查'],
      rating: 5,
      notes: '品質優秀，完全符合要求'
    }
  }
]

// Computed statistics
const statistics = computed(() => {
  const stats = { pending: 0, inspecting: 0, approved: 0, rejected: 0 }
  acceptanceData.value.forEach(item => {
    // Map acceptance_status to simplified status for statistics
    const statusMap = {
      'pending_acceptance': 'pending',
      null: 'pending',
      undefined: 'pending',
      'accepted': 'approved',
      'rejected': 'rejected',
      'needs_review': 'inspecting'
    }
    const mappedStatus = statusMap[item.acceptance_status] || 'pending'
    stats[mappedStatus] = (stats[mappedStatus] || 0) + 1
  })
  return stats
})

// Methods
const loadData = async () => {
  loading.value = true
  try {
    // Fetch real data from API
    const response = await request({
      url: '/acceptance/mine',
      method: 'GET',
      params: {
        status: filters.value.status || ''
      }
    })

    // Transform the data to match the component structure
    const realData = (response || []).map(item => ({
      id: item.detail_id,
      po_number: item.purchase_order_no || '',
      supplier_name: item.supplier_name || '',
      item_name: item.item_name,
      item_specification: item.item_specification,
      received_quantity: item.item_quantity,
      unit: item.item_unit,
      status: item.acceptance_status === 'accepted' ? 'approved' :
              item.acceptance_status === 'rejected' ? 'rejected' :
              item.acceptance_status === 'needs_review' ? 'inspecting' : 'pending',
      acceptance_status: item.acceptance_status,
      priority: item.is_urgent ? 'high' : 'normal',
      arrival_date: item.arrival_date || item.created_at,
      request_order_no: item.request_order_no,
      item_status: item.item_status,
      needs_acceptance: item.needs_acceptance
    }))

    // Apply client-side filters
    let filteredData = [...realData]

    if (filters.value.poNumber) {
      filteredData = filteredData.filter(item =>
        item.po_number.toLowerCase().includes(filters.value.poNumber.toLowerCase())
      )
    }

    if (filters.value.supplier) {
      filteredData = filteredData.filter(item => item.supplier_name.includes(filters.value.supplier))
    }

    if (filters.value.priority) {
      filteredData = filteredData.filter(item => item.priority === filters.value.priority)
    }

    acceptanceData.value = filteredData
    pagination.value.total = filteredData.length
  } catch (error) {
    console.error('載入驗收資料失敗:', error)
    // If API fails, use empty array instead of mock data
    acceptanceData.value = []
    pagination.value.total = 0
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.value = {
    poNumber: '',
    supplier: '',
    status: '',
    priority: ''
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

const startInspection = async (row: any) => {
  try {
    const index = acceptanceData.value.findIndex(item => item.id === row.id)
    if (index !== -1) {
      acceptanceData.value[index].status = 'inspecting'
      acceptanceData.value[index].acceptance_history.push({
        id: Date.now(),
        action: '開始驗收',
        user: '當前用戶',
        timestamp: new Date().toISOString(),
        comment: '開始進行品質檢測',
        status: 'inspecting'
      })
    }
    ElMessage.success('已開始驗收')
  } catch (error) {
    ElMessage.error('開始驗收失敗')
  }
}

const approveAcceptance = (row: any) => {
  approvalForm.value = {
    id: row.id,
    po_number: row.po_number,
    item_name: row.item_name,
    received_quantity: row.received_quantity,
    accepted_quantity: row.received_quantity,
    quality_rating: 5,
    inspection_items: ['外觀檢查'],
    rejection_reason: '',
    notes: '',
    photos: []
  }
  isApproving.value = true
  approvalDialogVisible.value = true
  detailDialogVisible.value = false
}

const rejectAcceptance = (row: any) => {
  approvalForm.value = {
    id: row.id,
    po_number: row.po_number,
    item_name: row.item_name,
    received_quantity: row.received_quantity,
    accepted_quantity: 0,
    quality_rating: 1,
    inspection_items: [],
    rejection_reason: '',
    notes: '',
    photos: []
  }
  isApproving.value = false
  approvalDialogVisible.value = true
  detailDialogVisible.value = false
}

const confirmApproval = async () => {
  try {
    await approvalFormRef.value.validate()

    saving.value = true

    // Call API to confirm acceptance
    if (isApproving.value) {
      await request({
        url: '/acceptance/confirm',
        method: 'POST',
        data: {
          item_ref: {
            detail_id: approvalForm.value.id
          }
        }
      })
    }

    // Update local data
    const index = acceptanceData.value.findIndex(item => item.id === approvalForm.value.id)
    if (index !== -1) {
      const item = acceptanceData.value[index]
      item.status = isApproving.value ? 'approved' : 'rejected'
      item.acceptance_status = isApproving.value ? 'accepted' : 'rejected'

      // Add quality info if approving
      if (isApproving.value) {
        item.quality_info = {
          inspection_items: approvalForm.value.inspection_items,
          rating: approvalForm.value.quality_rating,
          notes: approvalForm.value.notes
        }
      }
    }
    
    approvalDialogVisible.value = false
    ElMessage.success(isApproving.value ? '驗收通過' : '驗收退回')
  } catch (error) {
    console.error('驗收處理失敗:', error)
    ElMessage.error('驗收處理失敗')
  } finally {
    saving.value = false
  }
}

const batchApprove = () => {
  ElMessage.success('批量通過功能開發中')
}

const batchReject = () => {
  ElMessage.success('批量退回功能開發中')
}

const viewAcceptanceDetail = (row: any) => {
  selectedItem.value = row
  activeTab.value = 'basic'
  detailDialogVisible.value = true
}

// Status/Priority getters
const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: 'warning',
    inspecting: 'primary',
    approved: 'success',
    rejected: 'danger'
  }
  return statusMap[status] || ''
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待驗收',
    inspecting: '驗收中',
    approved: '已通過',
    rejected: '已退回'
  }
  return statusMap[status] || status
}

const getPriorityType = (priority: string) => {
  const typeMap: Record<string, string> = {
    urgent: 'danger',
    high: 'warning',
    medium: 'info',
    low: 'success'
  }
  return typeMap[priority] || ''
}

const getPriorityText = (priority: string) => {
  const textMap: Record<string, string> = {
    urgent: '緊急',
    high: '高',
    medium: '中',
    low: '低'
  }
  return textMap[priority] || priority
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.my-acceptance {
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
      &.inspecting { color: #409eff; }
      &.approved { color: #67c23a; }
      &.rejected { color: #f56c6c; }
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

.overdue-text {
  color: #f56c6c;
  font-weight: bold;
}

.timeline-content {
  strong {
    color: #409eff;
  }
  
  p {
    margin: 4px 0;
    color: #909399;
    font-size: 13px;
  }
}

.quality-info {
  h4 {
    margin: 16px 0 8px 0;
    color: #303133;
  }
  
  .inspection-tag {
    margin: 4px 8px 4px 0;
  }
  
  .quality-notes {
    margin-top: 16px;
    
    p {
      color: #606266;
      line-height: 1.6;
    }
  }
}

.upload-demo {
  :deep(.el-upload-dragger) {
    width: 100%;
    height: 120px;
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

:deep(.el-checkbox-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>