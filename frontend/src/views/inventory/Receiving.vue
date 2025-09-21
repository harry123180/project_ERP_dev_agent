<template>
  <div class="receiving-management">
    <!-- Filter Section -->
    <div class="filter-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>收貨管理 - 統一收貨作業</span>
            <el-button type="primary" @click="refreshData">
              <el-icon><Refresh /></el-icon>
              重新整理
            </el-button>
          </div>
        </template>
        
        <el-form :inline="true" :model="filters">
          <el-form-item label="採購單號">
            <el-input v-model="filters.po_number" placeholder="輸入採購單號" clearable style="width: 200px" />
          </el-form-item>
          <el-form-item label="集運單號">
            <el-input v-model="filters.consolidation_number" placeholder="輸入集運單號" clearable style="width: 200px" />
          </el-form-item>
          <el-form-item label="供應商">
            <el-select v-model="filters.supplier_id" placeholder="選擇供應商" clearable style="width: 200px">
              <el-option v-for="supplier in suppliers" :key="supplier.supplier_id" :label="supplier.supplier_name_zh" :value="supplier.supplier_id" />
            </el-select>
          </el-form-item>
          <el-form-item label="收貨狀態">
            <el-select v-model="filters.status" placeholder="選擇狀態" clearable style="width: 150px">
              <el-option label="全部" value="" />
              <el-option label="待收貨" value="pending" />
              <el-option label="已到貨" value="arrived" />
              <el-option label="部分收貨" value="partial" />
              <el-option label="延期到貨" value="delayed" />
            </el-select>
          </el-form-item>
          <el-form-item label="預計到貨日">
            <el-date-picker
              v-model="filters.expected_date"
              type="date"
              placeholder="選擇日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 160px"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadReceivingList" :loading="loading">
              <el-icon><Search /></el-icon>
              查詢
            </el-button>
            <el-button @click="resetFilters">重設</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- Statistics Section -->
    <div class="stats-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ stats.pendingItems }}</div>
              <div class="stat-label">待收貨品項</div>
              <div class="statistic-icon pending">
                <el-icon><Clock /></el-icon>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ stats.arrivedItems }}</div>
              <div class="stat-label">已到貨品項</div>
              <div class="statistic-icon arrived">
                <el-icon><Van /></el-icon>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ stats.delayedItems }}</div>
              <div class="stat-label">延期品項</div>
              <div class="statistic-icon delayed">
                <el-icon><Warning /></el-icon>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ stats.thisMonthItems }}</div>
              <div class="stat-label">本月收貨</div>
              <div class="statistic-icon this-month">
                <el-icon><Calendar /></el-icon>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- Receiving List -->
    <div class="receiving-list">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>已發貨待收貨品項 ({{ receivingList.length }} 項)</span>
            <div>
              <el-button size="small" @click="batchReceive" :disabled="!selectedItems.length" type="success">
                <el-icon><Check /></el-icon>
                批量收貨
              </el-button>
            </div>
          </div>
        </template>
        
        <!-- Desktop Table View -->
        <div class="desktop-table" v-if="!isMobileView">
          <el-table 
            :data="receivingList" 
            v-loading="loading"
            @selection-change="handleSelectionChange"
            stripe
            :default-expand-all="false"
            row-key="id"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column type="expand" width="50">
              <template #default="{ row }">
                <div class="expand-content">
                  <el-row :gutter="20">
                    <el-col :span="12">
                      <el-descriptions :column="1" border size="small">
                        <el-descriptions-item label="請購單號">
                          <el-link type="primary" @click="viewRequisitionDetail(row.requisition_number)">
                            {{ row.requisition_number }}
                          </el-link>
                        </el-descriptions-item>
                        <el-descriptions-item label="採購單號">
                          <el-link type="primary" @click="viewPODetail(row.purchase_order_number)">
                            {{ row.purchase_order_number }}
                          </el-link>
                        </el-descriptions-item>
                        <el-descriptions-item label="集運單號">
                          <span v-if="row.consolidation_number">{{ row.consolidation_number }}</span>
                          <span v-else class="no-data">-</span>
                        </el-descriptions-item>
                      </el-descriptions>
                    </el-col>
                    <el-col :span="12">
                      <el-descriptions :column="1" border size="small">
                        <el-descriptions-item label="完整規格">
                          {{ row.specification || '-' }}
                        </el-descriptions-item>
                        <el-descriptions-item label="備註">
                          {{ row.remarks || '-' }}
                        </el-descriptions-item>
                        <el-descriptions-item label="供應商地區">
                          <el-tag size="small" :type="row.supplier_region === 'domestic' ? 'success' : 'warning'">
                            {{ row.supplier_region === 'domestic' ? '國內供應商' : '國外供應商' }}
                          </el-tag>
                        </el-descriptions-item>
                      </el-descriptions>
                    </el-col>
                  </el-row>
                </div>
              </template>
            </el-table-column>
            
            <!-- Primary Info - Always Visible -->
            <el-table-column label="品項信息" min-width="300">
              <template #default="{ row }">
                <div class="item-primary-info">
                  <div class="item-name">{{ row.item_name }}</div>
                  <div class="item-meta">
                    <el-tag size="small" type="info">{{ row.quantity }} {{ row.unit }}</el-tag>
                    <span class="spec-preview">{{ (row.specification || '').substring(0, 20) }}{{ (row.specification || '').length > 20 ? '...' : '' }}</span>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <!-- Order Info -->
            <el-table-column label="單據信息" min-width="200">
              <template #default="{ row }">
                <div class="order-info">
                  <div class="order-numbers">
                    <div class="order-item">
                      <span class="order-label">PO:</span>
                      <el-link type="primary" @click="viewPODetail(row.purchase_order_number)" class="order-link">
                        {{ row.purchase_order_number }}
                      </el-link>
                    </div>
                    <div class="order-item" v-if="row.consolidation_number">
                      <span class="order-label">集運:</span>
                      <span class="order-value">{{ row.consolidation_number }}</span>
                    </div>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <!-- Supplier & Status -->
            <el-table-column label="供應商 & 狀態" min-width="200">
              <template #default="{ row }">
                <div class="supplier-status-info">
                  <div class="supplier-name">{{ row.supplier_name }}</div>
                  <div class="status-delivery">
                    <el-tag 
                      :type="getDeliveryStatusType(row.delivery_status)"
                      size="small"
                    >
                      {{ row.delivery_status }}
                    </el-tag>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <!-- Expected Date & Overdue -->
            <el-table-column label="預計到貨 & 延期" min-width="180">
              <template #default="{ row }">
                <div class="delivery-timing">
                  <div class="expected-date">
                    {{ row.expected_delivery_date ? formatDate(row.expected_delivery_date) : '-' }}
                  </div>
                  <div class="overdue-status">
                    <span v-if="getDaysOverdue(row.expected_delivery_date) > 0" class="overdue-text">
                      延期 {{ getDaysOverdue(row.expected_delivery_date) }} 天
                    </span>
                    <span v-else class="on-time-text">準時</span>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <!-- Actions -->
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button 
                    size="small" 
                    type="success" 
                    @click="confirmItemReceived(row)"
                  >
                    <el-icon><Check /></el-icon>
                    收貨
                  </el-button>
                  <el-button 
                    size="small" 
                    type="primary" 
                    @click="viewReceiptDetail(row)"
                  >
                    詳情
                  </el-button>
                  <el-button 
                    v-if="getDaysOverdue(row.expected_delivery_date) > 0"
                    size="small" 
                    type="warning" 
                    @click="updateDeliveryDate(row)"
                  >
                    更新交期
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- Mobile Card View -->
        <div class="mobile-cards" v-else>
          <div class="mobile-actions">
            <el-checkbox v-model="selectAll" @change="handleSelectAll" :indeterminate="isIndeterminate">
              全選
            </el-checkbox>
            <el-button size="small" @click="batchReceive" :disabled="!selectedItems.length" type="success">
              批量收貨 ({{ selectedItems.length }})
            </el-button>
          </div>
          
          <div class="receiving-cards">
            <el-card 
              v-for="item in receivingList" 
              :key="item.id" 
              class="receiving-card"
              :class="{ 'selected': selectedItems.includes(item) }"
              @click="toggleItemSelection(item)"
            >
              <div class="card-header">
                <el-checkbox 
                  :model-value="selectedItems.includes(item)"
                  @click.stop
                  @change="toggleItemSelection(item)"
                />
                <div class="item-name">{{ item.item_name }}</div>
                <el-button 
                  size="small" 
                  type="success" 
                  @click.stop="confirmItemReceived(item)"
                >
                  收貨
                </el-button>
              </div>
              
              <div class="card-content">
                <div class="info-row">
                  <span class="label">數量:</span>
                  <el-tag size="small" type="info">{{ item.quantity }} {{ item.unit }}</el-tag>
                </div>
                
                <div class="info-row">
                  <span class="label">狀態:</span>
                  <el-tag 
                    :type="getDeliveryStatusType(item.delivery_status)"
                    size="small"
                  >
                    {{ item.delivery_status }}
                  </el-tag>
                </div>
                
                <div class="info-row">
                  <span class="label">供應商:</span>
                  <span class="value">{{ item.supplier_name }}</span>
                  <el-tag size="small" :type="item.supplier_region === 'domestic' ? 'success' : 'warning'">
                    {{ item.supplier_region === 'domestic' ? '國內' : '國外' }}
                  </el-tag>
                </div>
                
                <div class="info-row">
                  <span class="label">採購單:</span>
                  <el-link type="primary" @click.stop="viewPODetail(item.purchase_order_number)">
                    {{ item.purchase_order_number }}
                  </el-link>
                </div>
                
                <div class="info-row" v-if="item.consolidation_number">
                  <span class="label">集運單:</span>
                  <span class="value">{{ item.consolidation_number }}</span>
                </div>
                
                <div class="info-row" v-if="item.specification">
                  <span class="label">規格:</span>
                  <span class="value spec-text">{{ item.specification }}</span>
                </div>
                
                <div class="info-row" v-if="item.remarks">
                  <span class="label">備註:</span>
                  <span class="value">{{ item.remarks }}</span>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Item Receiving Confirmation Dialog -->
    <el-dialog v-model="receivingDetailVisible" title="收貨確認" width="600px">
      <div v-if="currentReceivingItem" class="receiving-detail">
        <div class="item-info">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="品名">{{ currentReceivingItem.item_name }}</el-descriptions-item>
            <el-descriptions-item label="規格">{{ currentReceivingItem.specification }}</el-descriptions-item>
            <el-descriptions-item label="數量">{{ currentReceivingItem.quantity }} {{ currentReceivingItem.unit }}</el-descriptions-item>
            <el-descriptions-item label="請購單號">{{ currentReceivingItem.requisition_number }}</el-descriptions-item>
            <el-descriptions-item label="採購單號">{{ currentReceivingItem.purchase_order_number }}</el-descriptions-item>
            <el-descriptions-item label="集運單號">{{ currentReceivingItem.consolidation_number || '-' }}</el-descriptions-item>
            <el-descriptions-item label="供應商">{{ currentReceivingItem.supplier_name }}</el-descriptions-item>
            <el-descriptions-item label="物流狀態">
              <el-tag 
                :type="getDeliveryStatusType(currentReceivingItem.delivery_status)"
                size="small"
              >
                {{ currentReceivingItem.delivery_status }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="收貨人">{{ receivingPersonnel }}</el-descriptions-item>
            <el-descriptions-item label="收貨時間" :span="2">{{ formatDateTime(new Date()) }}</el-descriptions-item>
          </el-descriptions>
        </div>
        
        <div class="receiving-form">
          <el-alert 
            title="收貨後將自動加入到儲位管理的待入庫物料列表" 
            type="info" 
            show-icon 
            :closable="false"
            style="margin-bottom: 20px"
          />
          <el-form :model="receivingForm" :rules="receivingRules" ref="receivingFormRef" label-width="120px">
            <el-form-item label="收貨備註">
              <el-input 
                v-model="receivingForm.notes" 
                type="textarea" 
                rows="3" 
                placeholder="記錄收貨狀況、問題或其他備註..."
                style="width: 100%"
              />
            </el-form-item>
          </el-form>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="receivingDetailVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmReceiving" :loading="confirmLoading">確認收貨</el-button>
      </template>
    </el-dialog>

    <!-- Batch Receive Dialog -->
    <el-dialog v-model="batchReceiveVisible" title="批量收貨" width="700px">
      <div class="batch-receive-content">
        <el-alert title="批量收貨確認" type="warning" show-icon>
          您即將確認以下 {{ selectedItems.length }} 項已發貨物料已收貨。
        </el-alert>
        
        <div class="selected-items">
          <h4>選擇的品項</h4>
          <el-table :data="selectedItems" size="small" max-height="300">
            <el-table-column prop="item_name" label="品名" />
            <el-table-column prop="purchase_order_number" label="採購單號" width="120" />
            <el-table-column prop="supplier_name" label="供應商" width="150" />
            <el-table-column label="物流狀態" width="100">
              <template #default="{ row }">
                <el-tag 
                  :type="getDeliveryStatusType(row.delivery_status)"
                  size="small"
                >
                  {{ row.delivery_status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="數量" width="100">
              <template #default="{ row }">
                {{ row.quantity }} {{ row.unit }}
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <el-form :model="batchForm" label-width="120px">
          <el-form-item label="收貨人員">
            <el-input v-model="batchForm.receiver" :value="receivingPersonnel" disabled />
          </el-form-item>
          <el-form-item label="收貨時間">
            <el-date-picker 
              v-model="batchForm.received_time" 
              type="datetime" 
              placeholder="選擇收貨時間"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="批量備註">
            <el-input v-model="batchForm.notes" type="textarea" rows="3" placeholder="請記錄收貨狀況和備註..." />
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <el-button @click="batchReceiveVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmBatchReceive" :loading="batchLoading">確認收貨</el-button>
      </template>
    </el-dialog>

    <!-- Item Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="`收貨詳情 - ${selectedItem?.purchase_order_number || ''}`"
      width="800px"
    >
      <div v-if="selectedItem" class="item-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="品項名稱">{{ selectedItem.item_name }}</el-descriptions-item>
          <el-descriptions-item label="規格">{{ selectedItem.specification || '-' }}</el-descriptions-item>
          <el-descriptions-item label="數量">{{ selectedItem.quantity }} {{ selectedItem.unit }}</el-descriptions-item>
          <el-descriptions-item label="請購單號">{{ selectedItem.requisition_number }}</el-descriptions-item>
          <el-descriptions-item label="採購單號">{{ selectedItem.purchase_order_number }}</el-descriptions-item>
          <el-descriptions-item label="集運單號">{{ selectedItem.consolidation_number || '-' }}</el-descriptions-item>
          <el-descriptions-item label="供應商">{{ selectedItem.supplier_name }}</el-descriptions-item>
          <el-descriptions-item label="供應商地區">
            <el-tag :type="selectedItem.supplier_region === 'domestic' ? 'success' : 'warning'" size="small">
              {{ selectedItem.supplier_region === 'domestic' ? '國內供應商' : '國外供應商' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="物流狀態">
            <el-tag :type="getDeliveryStatusType(selectedItem.delivery_status)" size="small">
              {{ selectedItem.delivery_status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="預計到貨日">
            {{ selectedItem.expected_delivery_date ? formatDate(selectedItem.expected_delivery_date) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="延期狀況">
            <span v-if="getDaysOverdue(selectedItem.expected_delivery_date) > 0" class="overdue-text">
              延期 {{ getDaysOverdue(selectedItem.expected_delivery_date) }} 天
            </span>
            <span v-else class="on-time-text">準時</span>
          </el-descriptions-item>
          <el-descriptions-item label="備註" :span="2">{{ selectedItem.remarks || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="receipt-history" v-if="selectedItem.receipt_history && selectedItem.receipt_history.length > 0">
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
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">關閉</el-button>
        <el-button type="primary" @click="confirmItemReceived(selectedItem)">立即收貨</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Check, Clock, Van, Warning, Calendar } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { inventoryApi, type ShippedItem, type ReceivingConfirmRequest, type BatchReceivingRequest } from '@/api/inventory'

// Router and store
const router = useRouter()
const authStore = useAuthStore()

// Reactive data
const loading = ref(false)
const confirmLoading = ref(false)
const batchLoading = ref(false)
const receivingList = ref<any[]>([])
const selectedItems = ref<any[]>([])
const suppliers = ref<any[]>([])

// New dialog states
const detailDialogVisible = ref(false)
const selectedItem = ref<any>(null)

// Form references
const receivingFormRef = ref()

// Enhanced receiving form
const receivingForm = reactive({
  notes: ''
})

// Form validation rules
const receivingRules = {}

// Responsive design
const screenWidth = ref(window.innerWidth)
const isMobileView = computed(() => screenWidth.value < 768)

// Mobile selection state
const selectAll = ref(false)
const isIndeterminate = computed(() => {
  return selectedItems.value.length > 0 && selectedItems.value.length < receivingList.value.length
})

// Filters
const filters = reactive({
  supplier_id: '',
  po_number: '',
  consolidation_number: '',
  status: '',
  expected_date: ''
})

// Statistics
const stats = computed(() => {
  const today = new Date()
  const thisMonth = today.getMonth()
  
  return {
    pendingItems: receivingList.value.filter(item => 
      item.delivery_status === '已發貨' || item.delivery_status === '運送中'
    ).length,
    arrivedItems: receivingList.value.filter(item => 
      item.delivery_status === '已到貨' || item.delivery_status === '最後一哩'
    ).length,
    delayedItems: receivingList.value.filter(item => 
      getDaysOverdue(item.expected_delivery_date) > 0
    ).length,
    thisMonthItems: receivingList.value.filter(item => {
      if (!item.received_at) return false
      const receivedDate = new Date(item.received_at)
      return receivedDate.getMonth() === thisMonth && receivedDate.getFullYear() === today.getFullYear()
    }).length
  }
})

// Dialog states
const receivingDetailVisible = ref(false)
const batchReceiveVisible = ref(false)
const currentReceivingItem = ref<any>(null)
const receivingPersonnel = computed(() => authStore.currentUser?.chinese_name || '')

// Batch receive form
const batchForm = reactive({
  receiver: '',
  received_time: new Date(),
  notes: ''
})

// Methods
const loadReceivingList = async () => {
  try {
    loading.value = true
    
    // Get shipped items from the API
    const filterParams = {
      po_number: filters.po_number,
      consolidation_number: filters.consolidation_number,
      supplier_id: filters.supplier_id
    }
    
    const data = await inventoryApi.getShippedItems(filterParams)
    receivingList.value = data
    
  } catch (error) {
    console.error('Failed to load receiving list:', error)
    ElMessage.error('載入收貨列表失敗')
  } finally {
    loading.value = false
  }
}

const loadSuppliers = async () => {
  try {
    // Call the suppliers API to get actual supplier data
    suppliers.value = await inventoryApi.getSuppliers()
  } catch (error) {
    console.error('Failed to load suppliers:', error)
    ElMessage.error('載入供應商列表失敗')
  }
}

const refreshData = () => {
  loadReceivingList()
  loadSuppliers()
}

const handleSelectionChange = (selection: any[]) => {
  selectedItems.value = selection
  updateSelectAllState()
}

const handleSelectAll = (checked: boolean) => {
  if (checked) {
    selectedItems.value = [...receivingList.value]
  } else {
    selectedItems.value = []
  }
}

const toggleItemSelection = (item: any) => {
  const index = selectedItems.value.findIndex(selected => selected.id === item.id)
  if (index > -1) {
    selectedItems.value.splice(index, 1)
  } else {
    selectedItems.value.push(item)
  }
  updateSelectAllState()
}

const updateSelectAllState = () => {
  selectAll.value = selectedItems.value.length === receivingList.value.length
}

// Window resize handler
const handleResize = () => {
  screenWidth.value = window.innerWidth
}

const confirmItemReceived = async (item: any) => {
  currentReceivingItem.value = item
  
  // Reset form
  receivingForm.notes = ''
  
  receivingDetailVisible.value = true
}

const confirmReceiving = async () => {
  try {
    await receivingFormRef.value.validate()
    confirmLoading.value = true
    
    const receivingData: ReceivingConfirmRequest = {
      item_id: currentReceivingItem.value.id,
      item_name: currentReceivingItem.value.item_name,
      requisition_number: currentReceivingItem.value.requisition_number,
      purchase_order_number: currentReceivingItem.value.purchase_order_number,
      consolidation_number: currentReceivingItem.value.consolidation_number,
      quantity: currentReceivingItem.value.quantity,
      unit: currentReceivingItem.value.unit,
      receiver: receivingPersonnel.value,
      received_at: new Date().toISOString(),
      notes: receivingForm.notes
    }
    
    // Call API to confirm item received
    await inventoryApi.confirmItemReceived(receivingData)
    
    ElMessage.success('物料收貨確認成功，已加入待入庫列表')
    receivingDetailVisible.value = false
    
    // 從列表中移除已收貨的品項
    const itemId = currentReceivingItem.value.id
    receivingList.value = receivingList.value.filter(item => item.id !== itemId)
    
    currentReceivingItem.value = null
    // 重新載入列表以確保資料同步
    await loadReceivingList()
  } catch (error) {
    console.error('Failed to confirm receiving:', error)
    ElMessage.error('確認收貨失敗')
  } finally {
    confirmLoading.value = false
  }
}


const batchReceive = () => {
  if (selectedItems.value.length === 0) {
    ElMessage.warning('請選擇要批量收貨的品項')
    return
  }
  
  batchForm.receiver = receivingPersonnel.value
  batchForm.received_time = new Date()
  batchForm.notes = ''
  batchReceiveVisible.value = true
}

const confirmBatchReceive = async () => {
  try {
    batchLoading.value = true
    
    const batchData: BatchReceivingRequest = {
      items: selectedItems.value.map(item => ({
        item_id: item.id,
        requisition_number: item.requisition_number,
        purchase_order_number: item.purchase_order_number,
        consolidation_number: item.consolidation_number
      })),
      receiver: batchForm.receiver,
      received_at: batchForm.received_time.toISOString(),
      notes: batchForm.notes
    }
    
    // Call API for batch receiving - items will go to pending storage
    await inventoryApi.batchConfirmReceived(batchData)
    
    ElMessage.success({
      message: `成功批量收貨 ${selectedItems.value.length} 個品項！已全部加入待入庫列表，請至儲位管理分配儲位。`,
      duration: 5000,
      showClose: true
    })
    batchReceiveVisible.value = false
    
    // 從列表中移除已批量收貨的品項
    const selectedIds = selectedItems.value.map(item => item.id)
    receivingList.value = receivingList.value.filter(item => !selectedIds.includes(item.id))
    
    selectedItems.value = []
    // 重新載入列表以確保資料同步
    await loadReceivingList()
  } catch (error) {
    console.error('Failed to batch confirm receiving:', error)
    ElMessage.error('批量收貨失敗')
  } finally {
    batchLoading.value = false
  }
}



const viewPODetail = (poNo: string) => {
  router.push(`/purchase-orders/${poNo}`)
}

const viewRequisitionDetail = (reqNo: string) => {
  router.push(`/requisitions/${reqNo}`)
}

// Utility functions
const getDeliveryStatusType = (status: string) => {
  const statusMap: { [key: string]: string } = {
    '已發貨': 'success',
    '運送中': 'warning', 
    '海運中': 'info',
    '清關中': 'warning',
    '最後一哩': 'success',
    '即將到達': 'success',
    '延遲': 'danger',
    '異常': 'danger'
  }
  return statusMap[status] || 'info'
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('zh-TW')
}

const formatDateTime = (date: Date | string) => {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleString('zh-TW')
}

// New utility functions from PendingReceipt
const getDaysOverdue = (expectedDate: string) => {
  if (!expectedDate) return 0
  const expected = new Date(expectedDate)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  expected.setHours(0, 0, 0, 0)
  
  const diffTime = today.getTime() - expected.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  return diffDays > 0 ? diffDays : 0
}

const resetFilters = () => {
  filters.supplier_id = ''
  filters.po_number = ''
  filters.consolidation_number = ''
  filters.status = ''
  filters.expected_date = ''
  loadReceivingList()
}

const viewReceiptDetail = (item: any) => {
  selectedItem.value = item
  detailDialogVisible.value = true
}

const updateDeliveryDate = (item: any) => {
  ElMessage.info('更新交期功能開發中')
}

const getQualityStatusType = (status: string) => {
  const statusMap: { [key: string]: string } = {
    good: 'success',
    minor_defect: 'warning',
    major_defect: 'danger',
    rejected: 'danger'
  }
  return statusMap[status] || ''
}

const getQualityStatusText = (status: string) => {
  const statusMap: { [key: string]: string } = {
    good: '良好',
    minor_defect: '輕微瑕疵',
    major_defect: '重大瑕疵',
    rejected: '不合格'
  }
  return statusMap[status] || status
}

// Initialize
onMounted(() => {
  loadReceivingList()
  loadSuppliers()
  window.addEventListener('resize', handleResize)
})

// Cleanup
const cleanup = () => {
  window.removeEventListener('resize', handleResize)
}

// Add cleanup on component unmount
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', cleanup)
}
</script>

<style scoped>
.receiving-management {
  padding: 20px;
}

.filter-section,
.stats-section,
.receiving-list {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-card {
  text-align: center;
}

.stat-item {
  padding: 10px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.supplier-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.supplier-name {
  font-weight: bold;
}

.supplier-region {
  font-size: 12px;
}

.progress-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.progress-text {
  font-size: 12px;
  color: #666;
  text-align: center;
}

.expand-content {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 6px;
  margin: 10px;
}

.receiving-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.po-info {
  margin-bottom: 20px;
}

.items-section h4,
.receiving-notes h4 {
  margin-bottom: 10px;
  color: #303133;
}

.received-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
}

.received-time {
  font-size: 10px;
  color: #666;
}

.batch-receive-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.selected-pos h4 {
  margin-bottom: 10px;
  color: #303133;
}

/* ETA date styling */
.overdue {
  color: #f56c6c;
  font-weight: bold;
}

.urgent {
  color: #e6a23c;
  font-weight: bold;
}

.warning {
  color: #e6a23c;
}

.normal {
  color: #606266;
}

/* Delivery status styling */
.no-data {
  color: #909399;
  font-style: italic;
}

/* New responsive design styles */

/* Desktop Table Improvements */
.desktop-table {
  width: 100%;
  overflow-x: auto;
}

.item-primary-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.item-name {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
  line-height: 1.4;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.spec-preview {
  font-size: 12px;
  color: #666;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
}

.order-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.order-numbers {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.order-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.order-label {
  color: #666;
  font-size: 11px;
  min-width: 30px;
}

.order-link {
  font-size: 13px;
  text-decoration: none;
}

.order-value {
  font-size: 13px;
  color: #303133;
}

.supplier-status-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.supplier-status-info .supplier-name {
  font-weight: 500;
  color: #303133;
  font-size: 13px;
}

.status-delivery {
  display: flex;
  align-items: center;
}

/* Enhanced expand content */
.expand-content {
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
  margin: 10px;
  border: 1px solid #e4e7ed;
}

/* Mobile Card View Styles */
.mobile-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mobile-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.receiving-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.receiving-card {
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.receiving-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.receiving-card.selected {
  border-color: #409eff;
  background: #f0f7ff;
}

.receiving-card .card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 16px 12px;
  border-bottom: 1px solid #f0f0f0;
}

.receiving-card .card-header .item-name {
  flex: 1;
  font-weight: 600;
  font-size: 15px;
  color: #303133;
  line-height: 1.4;
}

.card-content {
  padding: 12px 16px 16px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.info-row .label {
  font-size: 12px;
  color: #666;
  min-width: 50px;
  font-weight: 500;
}

.info-row .value {
  flex: 1;
  font-size: 13px;
  color: #303133;
  word-break: break-all;
}

.info-row .spec-text {
  font-size: 12px;
  line-height: 1.4;
  color: #666;
  background: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
  margin-top: 4px;
}

/* Enhanced statistics cards */
.stat-card {
  position: relative;
}

.statistic-icon {
  position: absolute;
  top: 16px;
  right: 16px;
  font-size: 24px;
  opacity: 0.6;
}

.statistic-icon.pending { color: #e6a23c; }
.statistic-icon.arrived { color: #67c23a; }
.statistic-icon.delayed { color: #f56c6c; }
.statistic-icon.this-month { color: #409eff; }

/* Delivery timing column */
.delivery-timing {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.expected-date {
  font-size: 13px;
  color: #303133;
}

.overdue-status {
  display: flex;
  align-items: center;
}

.overdue-text {
  color: #f56c6c;
  font-weight: bold;
  font-size: 12px;
}

.on-time-text {
  color: #67c23a;
  font-size: 12px;
}

/* Action buttons */
.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.action-buttons .el-button {
  width: 100%;
  min-width: 60px;
}

/* Receiving form styles */
.receiving-form {
  margin-top: 20px;
}

.quantity-info {
  margin-left: 10px;
  color: #666;
  font-size: 13px;
}

/* Item detail dialog */
.item-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.receipt-history {
  margin-top: 20px;
}

.receipt-history h4 {
  margin: 16px 0 12px 0;
  color: #303133;
}

/* Responsive breakpoints */
@media (max-width: 768px) {
  .desktop-table {
    display: none;
  }
  
  .stats-section .el-col {
    margin-bottom: 10px;
  }
  
  .filter-section .el-form {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-section .el-form-item {
    margin-right: 0;
    margin-bottom: 12px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .action-buttons {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 2px;
  }
  
  .action-buttons .el-button {
    width: auto;
    flex: 1;
    min-width: 50px;
  }
}

@media (min-width: 769px) {
  .mobile-cards {
    display: none;
  }
}
</style>