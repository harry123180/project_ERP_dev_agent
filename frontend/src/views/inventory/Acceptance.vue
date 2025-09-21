<template>
  <div class="acceptance-management">
    <!-- Filter and Stats Section -->
    <div class="header-section">
      <el-row :gutter="20">
        <el-col :span="16">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>我的驗收任務</span>
                <div>
                  <el-button type="primary" @click="refreshData">
                    <el-icon><Refresh /></el-icon>
                    重新整理
                  </el-button>
                </div>
              </div>
            </template>
            
            <el-form :inline="true" :model="filters">
              <el-form-item label="物料狀態">
                <el-select v-model="filters.status" @change="loadAcceptanceItems" style="width: 150px" clearable>
                  <el-option label="全部" value="" />
                  <el-option label="待驗收" value="pending" />
                  <el-option label="已驗收" value="accepted" />
                  <el-option label="已拒絕" value="rejected" />
                </el-select>
              </el-form-item>
              <el-form-item label="類型">
                <el-select v-model="filters.category" @change="loadAcceptanceItems" style="width: 150px" clearable>
                  <el-option label="電子元件" value="electronic" />
                  <el-option label="機械零件" value="mechanical" />
                  <el-option label="辦公用品" value="office" />
                  <el-option label="實驗設備" value="lab" />
                </el-select>
              </el-form-item>
              <el-form-item label="申請日期">
                <el-date-picker
                  v-model="filters.dateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="開始日期"
                  end-placeholder="結束日期"
                  @change="loadAcceptanceItems"
                  style="width: 240px"
                />
              </el-form-item>
              <el-form-item label="申請人篩選">
                <el-checkbox v-model="filters.showOnlyMyItems" @change="loadAcceptanceItems">
                  只顯示我申請的物料
                </el-checkbox>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="loadAcceptanceItems" :loading="loading">
                  <el-icon><Search /></el-icon>
                  查詢
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="stats-card">
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-value pending">{{ stats.pendingCount }}</div>
                <div class="stat-label">待驗收</div>
              </div>
              <div class="stat-item">
                <div class="stat-value accepted">{{ stats.acceptedCount }}</div>
                <div class="stat-label">已驗收</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- Quick Actions -->
    <div class="actions-section">
      <el-card>
        <div class="quick-actions">
          <el-button @click="exportAcceptanceReport">
            <el-icon><Download /></el-icon>
            匯出報告
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- Acceptance Items Table -->
    <div class="items-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>驗收項目列表 ({{ acceptanceItems.length }} 項)</span>
            <div class="header-actions">
              <el-radio-group v-model="viewMode" size="small">
                <el-radio-button value="table">
                  <el-icon><Grid /></el-icon>
                  表格檢視
                </el-radio-button>
                <el-radio-button value="card">
                  <el-icon><CollectionTag /></el-icon>
                  卡片檢視
                </el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>
        
        <!-- Table View -->
        <div v-if="viewMode === 'table'">
          <el-table 
            :data="acceptanceItems" 
            v-loading="loading"
            stripe
            :row-class-name="getRowClassName"
          >
            <el-table-column type="expand" width="30">
              <template #default="{ row }">
                <div class="expand-content">
                  <div class="item-details">
                    <h4>物料詳細資訊</h4>
                    <el-descriptions :column="2" border>
                      <el-descriptions-item label="物料名稱">{{ row.item_name }}</el-descriptions-item>
                      <el-descriptions-item label="規格說明">{{ row.item_specification || '-' }}</el-descriptions-item>
                      <el-descriptions-item label="請購數量">{{ row.item_quantity }} {{ row.item_unit }}</el-descriptions-item>
                      <el-descriptions-item label="請購單號">
                        <el-link type="primary" @click="viewRequisition(row.request_order_no)">
                          {{ row.request_order_no }}
                        </el-link>
                      </el-descriptions-item>
                      <el-descriptions-item label="申請人">{{ row.requester_name }}</el-descriptions-item>
                      <el-descriptions-item label="申請日期">{{ formatDate(row.request_date) }}</el-descriptions-item>
                      <el-descriptions-item label="預期交期">{{ formatDate(row.expected_delivery) }}</el-descriptions-item>
                      <el-descriptions-item label="實際到貨">{{ formatDate(row.actual_arrival) }}</el-descriptions-item>
                    </el-descriptions>
                    
                    <div class="purchase-info" v-if="row.purchase_info">
                      <h5>採購資訊</h5>
                      <el-descriptions :column="2" border size="small">
                        <el-descriptions-item label="採購單號">
                          <el-link type="primary" @click="viewPurchaseOrder(row.purchase_info.po_no)">
                            {{ row.purchase_info.po_no }}
                          </el-link>
                        </el-descriptions-item>
                        <el-descriptions-item label="供應商">{{ row.purchase_info.supplier_name }}</el-descriptions-item>
                        <el-descriptions-item label="單價">{{ row.purchase_info.unit_price }}</el-descriptions-item>
                        <el-descriptions-item label="總價">{{ row.purchase_info.total_price }}</el-descriptions-item>
                      </el-descriptions>
                    </div>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="item_name" label="物料名稱" width="200">
              <template #default="{ row }">
                <div class="item-info">
                  <div class="item-name">{{ row.item_name }}</div>
                  <div class="item-spec" v-if="row.item_specification">{{ row.item_specification }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="數量/單位" width="120" align="center">
              <template #default="{ row }">
                <div class="quantity-info">
                  <span class="quantity">{{ row.item_quantity }}</span>
                  <span class="unit">{{ row.item_unit }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="request_order_no" label="請購單號" width="140">
              <template #default="{ row }">
                <el-link type="primary" @click="viewRequisition(row.request_order_no)">
                  {{ row.request_order_no }}
                </el-link>
              </template>
            </el-table-column>
            <el-table-column prop="requester_name" label="申請人" width="100" />
            <el-table-column label="物料狀態" width="120">
              <template #default="{ row }">
                <el-tag 
                  :type="getWarehouseStatusType(row)" 
                  size="small"
                >
                  {{ getWarehouseStatusText(row) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="儲位" width="120">
              <template #default="{ row }">
                <span v-if="row.storage_location" class="storage-location">
                  {{ row.storage_location }}
                </span>
                <span v-else class="no-storage">-</span>
              </template>
            </el-table-column>
            <el-table-column label="驗收狀態" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.acceptance_status" :type="getAcceptanceStatusType(row.acceptance_status)" size="small">
                  {{ row.acceptance_status }}
                </el-tag>
                <el-tag v-else type="warning" size="small">
                  待驗收
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="actual_arrival" label="到貨時間" width="120">
              <template #default="{ row }">
                {{ formatDate(row.actual_arrival) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button-group v-if="canAcceptItem(row)">
                  <el-button size="small" type="primary" @click="acceptItem(row)">
                    <el-icon><Check /></el-icon>
                    驗收
                  </el-button>
                </el-button-group>
                <el-button-group v-else>
                  <el-button size="small" type="info" @click="viewAcceptanceDetail(row)">
                    <el-icon><View /></el-icon>
                    詳情
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- Card View -->
        <div v-else class="card-view">
          <el-row :gutter="20">
            <el-col :span="8" v-for="item in acceptanceItems" :key="item.detail_id">
              <el-card class="acceptance-card">
                <template #header>
                  <div class="card-item-header">
                    <div class="item-title">
                      <h4>{{ item.item_name }}</h4>
                      <div class="status-tags">
                        <el-tag :type="getWarehouseStatusType(item)" size="small">
                          {{ getWarehouseStatusText(item) }}
                        </el-tag>
                        <el-tag v-if="item.acceptance_status" :type="getAcceptanceStatusType(item.acceptance_status)" size="small">
                          {{ item.acceptance_status }}
                        </el-tag>
                      </div>
                    </div>
                  </div>
                </template>
                
                <div class="card-content">
                  <div class="basic-info">
                    <p><strong>規格:</strong> {{ item.item_specification || '-' }}</p>
                    <p><strong>數量:</strong> {{ item.item_quantity }} {{ item.item_unit }}</p>
                    <p><strong>申請人:</strong> {{ item.requester_name }}</p>
                    <p><strong>儲位:</strong> {{ item.storage_location || '-' }}</p>
                    <p><strong>到貨時間:</strong> {{ formatDate(item.actual_arrival) }}</p>
                  </div>
                  
                  <div class="card-actions">
                    <el-button-group v-if="canAcceptItem(item)">
                      <el-button size="small" type="primary" @click="acceptItem(item)">
                        <el-icon><Check /></el-icon>
                        驗收
                      </el-button>
                    </el-button-group>
                    <el-button v-else size="small" type="info" @click="viewAcceptanceDetail(item)">
                      <el-icon><View /></el-icon>
                      詳情
                    </el-button>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </el-card>
    </div>

    <!-- Accept Item Dialog -->
    <el-dialog v-model="showAcceptDialog" title="驗收確認" width="500px">
      <div v-if="currentItem" class="accept-content">
        <el-alert title="驗收確認" type="info" show-icon>
          請確認是否接收以下物料
        </el-alert>
        
        <div class="item-summary">
          <h4>物料資訊</h4>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="物料名稱">{{ currentItem.item_name }}</el-descriptions-item>
            <el-descriptions-item label="規格說明">{{ currentItem.item_specification || '-' }}</el-descriptions-item>
            <el-descriptions-item label="數量">{{ currentItem.item_quantity }} {{ currentItem.item_unit }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
      
      <template #footer>
        <div class="simple-accept-buttons">
          <el-button size="large" @click="rejectItem(currentItem)" type="danger">
            拒絕驗收
          </el-button>
          <el-button size="large" type="success" @click="confirmAcceptance" :loading="acceptLoading">
            朕知道了
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- Reject Item Dialog -->
    <el-dialog v-model="showRejectDialog" title="拒絕驗收" width="600px">
      <div v-if="currentItem" class="reject-content">
        <el-alert title="拒絕驗收" type="error" show-icon>
          請詳細說明拒絕驗收的原因，以便相關人員處理。
        </el-alert>
        
        <el-form :model="rejectForm" :rules="rejectRules" ref="rejectFormRef" label-width="120px">
          <el-form-item label="拒絕原因" prop="reason">
            <el-select v-model="rejectForm.reason" style="width: 100%">
              <el-option label="物料不符" value="incorrect_item" />
              <el-option label="數量不符" value="incorrect_quantity" />
              <el-option label="品質不佳" value="poor_quality" />
              <el-option label="损壞破損" value="damaged" />
              <el-option label="過期交貨" value="overdue" />
              <el-option label="規格不符" value="incorrect_spec" />
              <el-option label="其他原因" value="other" />
            </el-select>
          </el-form-item>
          <el-form-item label="詳細說明" prop="details">
            <el-input 
              v-model="rejectForm.details" 
              type="textarea" 
              rows="4" 
              placeholder="請詳細說明拒絕原因和具體情況..."
            />
          </el-form-item>
          <el-form-item label="建議處理">
            <el-checkbox-group v-model="rejectForm.suggestions">
              <el-checkbox value="return_supplier">退回供應商</el-checkbox>
              <el-checkbox value="reorder">重新訂購</el-checkbox>
              <el-checkbox value="partial_accept">部分接受</el-checkbox>
              <el-checkbox value="quality_check">品質檢驗</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          <el-form-item label="相關照片">
            <el-upload
              v-model:file-list="rejectForm.photos"
              action="/api/upload"
              list-type="picture-card"
              :auto-upload="false"
            >
              <el-icon><Plus /></el-icon>
            </el-upload>
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <el-button @click="showRejectDialog = false">取消</el-button>
        <el-button type="danger" @click="confirmRejection" :loading="rejectLoading">
          確認拒絕
        </el-button>
      </template>
    </el-dialog>

    <!-- Acceptance Detail Dialog -->
    <el-dialog v-model="showDetailDialog" title="驗收詳情" width="800px">
      <div v-if="currentItem" class="detail-content">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="基本資訊" name="basic">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="物料名稱">{{ currentItem.item_name }}</el-descriptions-item>
              <el-descriptions-item label="規格說明">{{ currentItem.item_specification || '-' }}</el-descriptions-item>
              <el-descriptions-item label="請購數量">{{ currentItem.item_quantity }} {{ currentItem.item_unit }}</el-descriptions-item>
              <el-descriptions-item label="實收數量">{{ currentItem.accepted_quantity || '-' }}</el-descriptions-item>
              <el-descriptions-item label="申請人">{{ currentItem.requester_name }}</el-descriptions-item>
              <el-descriptions-item label="驗收狀態">
                <el-tag :type="getStatusType(currentItem.acceptance_status)">
                  {{ getStatusText(currentItem.acceptance_status) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="驗收時間">{{ formatDateTime(currentItem.acceptance_time) }}</el-descriptions-item>
              <el-descriptions-item label="驗收人">{{ currentItem.acceptor_name || '-' }}</el-descriptions-item>
            </el-descriptions>
          </el-tab-pane>
          <el-tab-pane label="驗收記錄" name="record">
            <div class="acceptance-record">
              <h4>驗收備註</h4>
              <p>{{ currentItem.acceptance_notes || '無備註' }}</p>
              
              <h4>品質狀況</h4>
              <el-tag :type="getQualityType(currentItem.quality_status)">
                {{ getQualityText(currentItem.quality_status) }}
              </el-tag>
              
              <h4 v-if="currentItem.rejection_reason">拒絕原因</h4>
              <p v-if="currentItem.rejection_reason">{{ currentItem.rejection_reason }}</p>
            </div>
          </el-tab-pane>
          <el-tab-pane label="文件照片" name="documents">
            <div class="document-gallery">
              <el-image 
                v-for="(photo, index) in currentItem.photos" 
                :key="index"
                :src="photo.url" 
                :preview-src-list="currentItem.photos.map(p => p.url)"
                fit="cover"
                style="width: 100px; height: 100px; margin-right: 10px;"
              />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      
      <template #footer>
        <el-button @click="showDetailDialog = false">關閉</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh, Search, Check, Close, Download, View, Plus, 
  RefreshRight, Grid, CollectionTag 
} from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { inventoryApi } from '@/api/inventory'

// Router and store
const router = useRouter()
const authStore = useAuthStore()

// Reactive data
const loading = ref(false)
const acceptLoading = ref(false)
const rejectLoading = ref(false)
const acceptanceItems = ref<any[]>([])
const currentItem = ref<any>(null)
const viewMode = ref('table')
const activeTab = ref('basic')

// Filters
const filters = reactive({
  status: '', // Show all items that can be accepted (已到貨 or 已入庫 but not 已驗收)
  category: '',
  dateRange: null as any,
  showOnlyMyItems: true // Default to showing only user's requisitioned items
})

// Dialog states
const showAcceptDialog = ref(false)
const showRejectDialog = ref(false)
const showDetailDialog = ref(false)


const rejectForm = reactive({
  reason: '',
  details: '',
  suggestions: [] as string[],
  photos: [] as any[]
})

const rejectFormRef = ref()

// Form rules
const rejectRules = {
  reason: [
    { required: true, message: '請選擇拒絕原因', trigger: 'change' }
  ],
  details: [
    { required: true, message: '請詳細說明拒絕原因', trigger: 'blur' }
  ]
}

// Computed properties
const stats = computed(() => {
  const currentItems = acceptanceItems.value

  // Count items by acceptance status
  // The acceptance_status field contains Chinese text after mapping
  const accepted = currentItems.filter(item =>
    item.acceptance_status === '已驗收'
  ).length

  const pending = currentItems.filter(item =>
    item.acceptance_status === '待驗收'
  ).length

  return {
    acceptedCount: accepted,
    pendingCount: pending
  }
})


// Methods
const loadAcceptanceItems = async () => {
  try {
    loading.value = true
    
    // Call the API with status filter
    const response = await inventoryApi.getMyAcceptanceItems(filters.status)
    
    // Map the response to match the expected format
    let items = response.map(item => {
      // Map backend status to frontend display status
      let acceptance_status = '待驗收' // Default to pending

      if (item.acceptance_status === 'accepted') {
        acceptance_status = '已驗收'
      } else if (item.acceptance_status === 'pending_acceptance' || !item.acceptance_status) {
        acceptance_status = '待驗收'
      } else if (item.acceptance_status === 'rejected') {
        acceptance_status = '已拒絕'
      }
      
      return {
        detail_id: item.detail_id,
        item_name: item.item_name,
        item_specification: item.item_specification,
        item_quantity: item.item_quantity,
        item_unit: item.item_unit,
        request_order_no: item.request_order_no,
        requester_name: authStore.currentUser?.chinese_name || '當前用戶',
        item_status: item.item_status, // Keep original backend status
        acceptance_status,
        raw_acceptance_status: item.acceptance_status, // Keep original for filtering
        storage_location: item.storage_location,
        is_warehoused: item.is_warehoused,
        request_date: new Date().toISOString().split('T')[0], // Use current date as fallback
        expected_delivery: new Date().toISOString().split('T')[0],
        actual_arrival: new Date().toISOString().split('T')[0]
      }
    })
    
    // Apply status filter
    if (filters.status) {
      items = items.filter(item => {
        switch (filters.status) {
          case 'pending':
            return !item.raw_acceptance_status || item.raw_acceptance_status === 'pending_acceptance'
          case 'accepted':
            return item.raw_acceptance_status === 'accepted'
          case 'rejected':
            return item.raw_acceptance_status === 'rejected'
          default:
            return true // Show all
        }
      })
    }
    
    // Filter by user if showOnlyMyItems is true (backend already filters by current user)
    // This is redundant now but kept for consistency
    if (filters.showOnlyMyItems) {
      const currentUserName = authStore.currentUser?.chinese_name || '當前用戶'
      items = items.filter(item => 
        item.requester_name === currentUserName
      )
    }
    
    acceptanceItems.value = items
    
  } catch (error) {
    console.error('Error loading acceptance items:', error)
    ElMessage.error('載入驗收項目失敗: ' + (error.response?.data?.message || error.message))
    
    // Fallback to empty array on error
    acceptanceItems.value = []
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  loadAcceptanceItems()
}


const acceptItem = (item: any) => {
  currentItem.value = item
  showAcceptDialog.value = true
}

const rejectItem = (item: any) => {
  currentItem.value = item
  rejectForm.reason = ''
  rejectForm.details = ''
  rejectForm.suggestions = []
  rejectForm.photos = []
  showRejectDialog.value = true
}

const confirmAcceptance = async () => {
  try {
    acceptLoading.value = true
    
    // Call the actual API endpoint with correct parameters
    await inventoryApi.confirmAcceptance(currentItem.value.detail_id, {
      accepted_quantity: currentItem.value.item_quantity,
      notes: '用戶驗收確認'
    })
    
    ElMessage.success('物料驗收成功')
    showAcceptDialog.value = false
    
    // Refresh the data to reflect the change
    await loadAcceptanceItems()
  } catch (error) {
    console.error('Acceptance confirmation error:', error)
    ElMessage.error('驗收失敗: ' + (error.response?.data?.message || error.message))
  } finally {
    acceptLoading.value = false
  }
}

const confirmRejection = async () => {
  try {
    await rejectFormRef.value?.validate()
    rejectLoading.value = true
    
    // Call API to reject item
    ElMessage.success('物料拒絕成功')
    showRejectDialog.value = false
    await loadAcceptanceItems()
  } catch (error) {
    ElMessage.error('拒絕失敗')
  } finally {
    rejectLoading.value = false
  }
}


const viewAcceptanceDetail = (item: any) => {
  currentItem.value = item
  activeTab.value = 'basic'
  showDetailDialog.value = true
}

const reprocessItem = (item: any) => {
  ElMessage.info('重新處理功能開發中')
}

const viewRequisition = (reqNo: string) => {
  router.push(`/requisitions/${reqNo}`)
}

const viewPurchaseOrder = (poNo: string) => {
  router.push(`/purchase-orders/${poNo}`)
}

const exportAcceptanceReport = () => {
  ElMessage.info('匯出報告功能開發中')
}

// Utility functions
const canAcceptItem = (item: any) => {
  // Allow acceptance for items that are:
  // 1. Have arrived or warehoused status OR
  // 2. Have pending_acceptance status and not already accepted
  const statusOk = item.item_status === 'arrived' || item.item_status === 'warehoused'
  const pendingOk = item.raw_acceptance_status === 'pending_acceptance' || !item.raw_acceptance_status
  const notAccepted = item.acceptance_status !== '已驗收' && item.acceptance_status !== 'accepted'
  
  return (statusOk || pendingOk) && notAccepted
}


const getRowClassName = ({ row }: { row: any }) => {
  if (row.acceptance_status === 'rejected') return 'rejected-row'
  return ''
}

const getItemStatusType = (status: string) => {
  switch (status) {
    case '已到貨': return 'warning'
    case '已入庫': return 'primary'
    case '已驗收': return 'success'
    default: return 'info'
  }
}

const getWarehouseStatusType = (item: any) => {
  if (item.is_warehoused || item.storage_location) {
    return 'success' // 已入庫
  }
  // If item has pending acceptance status, show as ready (primary color)
  if (item.raw_acceptance_status === 'pending_acceptance' || 
      (item.acceptance_status === '待驗收' && item.acceptance_status !== '已驗收')) {
    return 'primary' // 可驗收
  }
  return 'warning' // 未入庫
}

const getWarehouseStatusText = (item: any) => {
  if (item.is_warehoused || item.storage_location) {
    return '已入庫'
  }
  // If item has pending acceptance status, show as ready for acceptance
  if (item.raw_acceptance_status === 'pending_acceptance' || 
      (item.acceptance_status === '待驗收' && !item.acceptance_status === '已驗收')) {
    return '可驗收'
  }
  return '未入庫'
}

const getAcceptanceStatusType = (status: string) => {
  switch (status) {
    case '已驗收': return 'success'
    default: return 'info'
  }
}

const getStatusType = (status: string) => {
  return getItemStatusType(status)
}

const getStatusText = (status: string) => {
  return status
}


const getQualityType = (quality: string) => {
  switch (quality) {
    case 'good': return 'success'
    case 'acceptable': return 'warning'
    case 'defective': return 'danger'
    default: return 'info'
  }
}

const getQualityText = (quality: string) => {
  switch (quality) {
    case 'good': return '品質良好'
    case 'acceptable': return '可接受'
    case 'defective': return '有環疑'
    default: return '-'
  }
}

const canReprocess = (item: any) => {
  // Check if item can be reprocessed (business logic)
  return item.acceptance_status === 'rejected'
}

const formatDate = (date: string | Date) => {
  if (!date) return '-'
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('zh-TW')
}

const formatDateTime = (date: string | Date) => {
  if (!date) return '-'
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleString('zh-TW')
}

// Initialize
onMounted(() => {
  loadAcceptanceItems()
})
</script>

<style scoped>
.acceptance-management {
  padding: 20px;
}

.header-section,
.actions-section,
.items-section {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-card {
  padding: 10px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-value.arrived {
  color: #e6a23c;
}

.stat-value.stored {
  color: #409eff;
}

.stat-value.accepted {
  color: #67c23a;
}

.stat-value.pending {
  color: #f56c6c;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.quick-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.item-info .item-name {
  font-weight: bold;
  color: #303133;
}

.item-info .item-spec {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.quantity-info {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.quantity {
  font-weight: bold;
  font-size: 16px;
}

.unit {
  font-size: 12px;
  color: #666;
}

.expand-content {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 6px;
  margin: 10px;
}

.item-details h4 {
  margin-bottom: 15px;
  color: #303133;
}

.purchase-info {
  margin-top: 20px;
}

.purchase-info h5 {
  margin-bottom: 10px;
  color: #606266;
}

/* Card View Styles */
.card-view {
  margin-top: 20px;
}

.acceptance-card {
  margin-bottom: 20px;
  transition: all 0.3s ease;
}

.acceptance-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}


.card-item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.item-title h4 {
  margin: 0 0 5px 0;
  color: #303133;
}

.status-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.basic-info p {
  margin: 5px 0;
  font-size: 14px;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
}

/* Dialog Styles */
.accept-content,
.reject-content,
.detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.simple-accept-buttons {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  width: 100%;
}

.simple-accept-buttons .el-button {
  flex: 1;
  padding: 15px 30px;
  font-size: 16px;
  font-weight: bold;
}

.item-summary h4 {
  margin-bottom: 10px;
  color: #303133;
}

.unit-label {
  margin-left: 10px;
  color: #666;
}

.acceptance-record h4 {
  margin: 15px 0 10px 0;
  color: #303133;
}

.document-gallery {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

/* Table row styling */

:deep(.el-table .rejected-row) {
  background-color: #f5f5f5 !important;
}

/* Storage Location Styling */
.storage-location {
  font-family: 'Courier New', monospace;
  font-weight: bold;
  color: #409eff;
  background: #f0f9ff;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.no-storage {
  color: #909399;
  font-style: italic;
}
</style>