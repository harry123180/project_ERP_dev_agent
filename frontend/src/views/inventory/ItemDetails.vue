<template>
  <div class="inventory-item-details">
    <!-- Header with basic item info -->
    <div class="header-section">
      <el-card>
        <template #header>
          <div class="header-content">
            <div class="item-info">
              <h2 class="item-name">{{ itemDetails?.item_name }}</h2>
              <p class="item-spec" v-if="itemDetails?.item_specification">
                {{ itemDetails.item_specification }}
              </p>
            </div>
            <div class="actions">
              <el-button @click="refreshData" :loading="loading">
                <el-icon><Refresh /></el-icon>
                重新整理
              </el-button>
              <el-button @click="goBack">
                <el-icon><ArrowLeft /></el-icon>
                返回
              </el-button>
            </div>
          </div>
        </template>
        
        <div class="summary-cards">
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="summary-card">
                <div class="summary-value">{{ itemDetails?.total_quantity || 0 }}</div>
                <div class="summary-label">總庫存數量</div>
                <div class="summary-unit">{{ itemDetails?.unit }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-card">
                <div class="summary-value">{{ itemDetails?.batch_count || 0 }}</div>
                <div class="summary-label">批次數量</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-card">
                <div class="summary-value">{{ itemDetails?.storage_distribution?.length || 0 }}</div>
                <div class="summary-label">儲存位置</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-card">
                <div class="summary-value">
                  {{ formatDate(itemDetails?.batches?.[0]?.received_date) || '-' }}
                </div>
                <div class="summary-label">最近收貨日期</div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-card>
    </div>

    <!-- Tabs for detailed information -->
    <div class="details-section">
      <el-card>
        <el-tabs v-model="activeTab" @tab-change="handleTabChange">
          <!-- Basic Information Tab -->
          <el-tab-pane label="基本資訊" name="basic">
            <div class="basic-info">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="物料名稱">
                  {{ itemDetails?.item_name }}
                </el-descriptions-item>
                <el-descriptions-item label="規格說明">
                  {{ itemDetails?.item_specification || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="單位">
                  {{ itemDetails?.unit }}
                </el-descriptions-item>
                <el-descriptions-item label="總庫存數量">
                  <el-tag :type="getQuantityTagType(itemDetails?.total_quantity)">
                    {{ itemDetails?.total_quantity }} {{ itemDetails?.unit }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="批次總數">
                  {{ itemDetails?.batch_count }}
                </el-descriptions-item>
                <el-descriptions-item label="儲存位置總數">
                  {{ itemDetails?.storage_distribution?.length || 0 }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </el-tab-pane>

          <!-- Batch Breakdown Tab -->
          <el-tab-pane label="批次分佈" name="batches">
            <div class="batches-info">
              <el-table :data="itemDetails?.batches" v-loading="loading" stripe>
                <el-table-column prop="batch_id" label="批次ID" width="100" />
                <el-table-column prop="source_po_number" label="來源採購單" width="150">
                  <template #default="{ row }">
                    <el-link type="primary" @click="viewPO(row.source_po_number)">
                      {{ row.source_po_number }}
                    </el-link>
                  </template>
                </el-table-column>
                <el-table-column prop="current_quantity" label="目前數量" width="120" align="right">
                  <template #default="{ row }">
                    <el-tag :type="getQuantityTagType(row.current_quantity)" size="small">
                      {{ row.current_quantity }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="original_quantity" label="原始數量" width="120" align="right">
                  <template #default="{ row }">
                    {{ row.original_quantity }}
                  </template>
                </el-table-column>
                <el-table-column prop="received_date" label="收貨日期" width="120">
                  <template #default="{ row }">
                    {{ formatDate(row.received_date) }}
                  </template>
                </el-table-column>
                <el-table-column prop="receiver_name" label="收貨人" width="100">
                  <template #default="{ row }">
                    {{ row.receiver_name }}
                  </template>
                </el-table-column>
                <el-table-column prop="batch_status" label="狀態" width="100">
                  <template #default="{ row }">
                    <el-tag 
                      :type="row.batch_status === 'active' ? 'success' : 'info'" 
                      size="small"
                    >
                      {{ row.batch_status === 'active' ? '正常' : '已耗盡' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="150">
                  <template #default="{ row }">
                    <el-button size="small" @click="viewBatchDetails(row.batch_id)">
                      <el-icon><View /></el-icon>
                      詳情
                    </el-button>
                    <el-button size="small" @click="viewBatchHistory(row.batch_id)">
                      <el-icon><Clock /></el-icon>
                      履歷
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>

          <!-- Storage Distribution Tab -->
          <el-tab-pane label="儲存分佈" name="storage">
            <div class="storage-info">
              <el-table :data="itemDetails?.storage_distribution" v-loading="loading" stripe>
                <el-table-column prop="storage_id" label="儲存位置" width="200">
                  <template #default="{ row }">
                    <el-tag type="info" size="small">{{ row.storage_id }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="位置描述" width="200">
                  <template #default="{ row }">
                    {{ row.area_code }}-{{ row.shelf_code }}-第{{ row.floor_level }}層
                  </template>
                </el-table-column>
                <el-table-column prop="quantity" label="數量" width="120" align="right">
                  <template #default="{ row }">
                    <el-tag :type="getQuantityTagType(row.quantity)" size="small">
                      {{ row.quantity }} {{ itemDetails?.unit }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="佔比" width="120" align="right">
                  <template #default="{ row }">
                    {{ ((row.quantity / itemDetails?.total_quantity) * 100).toFixed(1) }}%
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="150">
                  <template #default="{ row }">
                    <el-button size="small" @click="viewStorageDetails(row.storage_id)">
                      <el-icon><View /></el-icon>
                      查看
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>

          <!-- Movement History Tab -->
          <el-tab-pane label="異動履歷" name="history">
            <div class="history-info">
              <div class="history-controls">
                <el-button @click="loadHistory" :loading="historyLoading">
                  <el-icon><Refresh /></el-icon>
                  重新載入
                </el-button>
                <el-button @click="exportHistory">
                  <el-icon><Download /></el-icon>
                  匯出履歷
                </el-button>
              </div>
              
              <el-table :data="historyData.movements" v-loading="historyLoading" stripe>
                <el-table-column prop="movement_date" label="異動時間" width="160">
                  <template #default="{ row }">
                    {{ formatDateTime(row.movement_date) }}
                  </template>
                </el-table-column>
                <el-table-column prop="movement_type" label="異動類型" width="100">
                  <template #default="{ row }">
                    <el-tag 
                      :type="row.movement_type === 'in' ? 'success' : 'warning'" 
                      size="small"
                    >
                      {{ row.movement_type === 'in' ? '入庫' : '出庫' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="movement_subtype" label="異動子類型" width="120">
                  <template #default="{ row }">
                    {{ getMovementSubtypeText(row.movement_subtype) }}
                  </template>
                </el-table-column>
                <el-table-column prop="quantity" label="數量" width="100" align="right">
                  <template #default="{ row }">
                    {{ row.quantity }}
                  </template>
                </el-table-column>
                <el-table-column label="儲存位置" width="200">
                  <template #default="{ row }">
                    <div v-if="row.from_storage_id && row.to_storage_id">
                      {{ row.from_storage_id }} → {{ row.to_storage_id }}
                    </div>
                    <div v-else-if="row.to_storage_id">
                      入庫至 {{ row.to_storage_id }}
                    </div>
                    <div v-else-if="row.from_storage_id">
                      從 {{ row.from_storage_id }} 出庫
                    </div>
                    <div v-else>-</div>
                  </template>
                </el-table-column>
                <el-table-column prop="operator.chinese_name" label="操作人員" width="100" />
                <el-table-column prop="reference_number" label="參考單號" width="150">
                  <template #default="{ row }">
                    <el-link v-if="row.reference_number" type="primary">
                      {{ row.reference_number }}
                    </el-link>
                    <span v-else>-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="notes" label="備註" min-width="200">
                  <template #default="{ row }">
                    {{ row.notes || '-' }}
                  </template>
                </el-table-column>
              </el-table>
              
              <!-- Pagination -->
              <div class="pagination-wrapper" v-if="historyData.pagination">
                <el-pagination
                  v-model:current-page="historyData.pagination.page"
                  v-model:page-size="historyData.pagination.per_page"
                  :page-sizes="[10, 20, 50, 100]"
                  :total="historyData.pagination.total"
                  layout="total, sizes, prev, pager, next, jumper"
                  @size-change="handleHistorySizeChange"
                  @current-change="handleHistoryPageChange"
                />
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh, ArrowLeft, View, Clock, Download 
} from '@element-plus/icons-vue'

// Router
const route = useRoute()
const router = useRouter()

// Reactive data
const loading = ref(false)
const historyLoading = ref(false)
const activeTab = ref('basic')
const itemDetails = ref<any>(null)
const historyData = reactive<any>({
  movements: [],
  pagination: null
})

// Props from route
const itemKey = route.params.itemKey as string

// Methods
const loadItemDetails = async () => {
  try {
    loading.value = true
    // Use axios API instance for consistent authentication
    const { inventoryApi } = await import('@/api')
    const data = await inventoryApi.getInventoryItemDetails(itemKey)
    itemDetails.value = data
    
  } catch (error) {
    console.error('Error loading item details:', error)
    ElMessage.error('載入物料詳情失敗')
  } finally {
    loading.value = false
  }
}

const loadHistory = async (page: number = 1, perPage: number = 20) => {
  try {
    historyLoading.value = true
    // Use axios API instance for consistent authentication
    const { inventoryApi } = await import('@/api')
    const data = await inventoryApi.getInventoryItemHistory(itemKey, page, perPage)
    historyData.movements = data.movements
    historyData.pagination = data.pagination
    
  } catch (error) {
    console.error('Error loading item history:', error)
    ElMessage.error('載入異動履歷失敗')
  } finally {
    historyLoading.value = false
  }
}

const refreshData = () => {
  loadItemDetails()
  if (activeTab.value === 'history') {
    loadHistory()
  }
}

const goBack = () => {
  router.back()
}

const handleTabChange = (tabName: string) => {
  if (tabName === 'history' && historyData.movements.length === 0) {
    loadHistory()
  }
}

const handleHistoryPageChange = (page: number) => {
  loadHistory(page, historyData.pagination?.per_page || 20)
}

const handleHistorySizeChange = (size: number) => {
  loadHistory(1, size)
}

// Helper methods
const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('zh-TW')
}

const formatDateTime = (dateString: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-TW')
}

const getQuantityTagType = (quantity: number) => {
  if (!quantity || quantity <= 0) return 'danger'
  if (quantity <= 10) return 'warning'
  return 'success'
}

const getMovementSubtypeText = (subtype: string) => {
  const subtypeMap: Record<string, string> = {
    'receiving': '收貨入庫',
    'issue': '領用出庫',
    'transfer': '庫位轉移',
    'adjustment': '盤點調整'
  }
  return subtypeMap[subtype] || subtype
}

const viewPO = (poNumber: string) => {
  ElMessage.info(`檢視採購單: ${poNumber}`)
}

const viewBatchDetails = (batchId: number) => {
  ElMessage.info(`檢視批次詳情: ${batchId}`)
}

const viewBatchHistory = (batchId: number) => {
  ElMessage.info(`檢視批次履歷: ${batchId}`)
}

const viewStorageDetails = (storageId: string) => {
  ElMessage.info(`檢視儲存位置: ${storageId}`)
}

const exportHistory = () => {
  ElMessage.info('匯出履歷功能開發中')
}

// Initialize
onMounted(() => {
  if (!itemKey) {
    ElMessage.error('無效的物料識別碼')
    router.back()
    return
  }
  
  loadItemDetails()
})
</script>

<style scoped>
.inventory-item-details {
  padding: 20px;
}

.header-section {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.item-info .item-name {
  margin: 0;
  color: #303133;
  font-size: 24px;
  font-weight: bold;
}

.item-info .item-spec {
  margin: 5px 0 0;
  color: #909399;
  font-size: 14px;
}

.summary-cards {
  margin-top: 20px;
}

.summary-card {
  text-align: center;
  padding: 20px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  background: #FAFAFA;
}

.summary-value {
  font-size: 28px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 8px;
}

.summary-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.summary-unit {
  font-size: 12px;
  color: #909399;
}

.details-section {
  margin-bottom: 20px;
}

.basic-info {
  padding: 20px;
}

.history-controls {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.batches-info, .storage-info, .history-info {
  padding: 20px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .summary-cards .el-col {
    margin-bottom: 15px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
}
</style>