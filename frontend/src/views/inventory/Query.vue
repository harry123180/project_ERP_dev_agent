<template>
  <div class="inventory-query">
    <!-- Search Filters Section -->
    <div class="search-section">
      <el-card class="filter-card">
        <template #header>
          <div class="card-header">
            <span>庫存查詢條件</span>
            <el-button size="small" @click="resetFilters">重置</el-button>
          </div>
        </template>
        
        <el-form :model="filters" label-width="100px" :inline="true">
          <el-form-item label="物料名稱">
            <el-input v-model="filters.name" placeholder="輸入物料名稱" clearable style="width: 200px" @keyup.enter="searchInventory" />
          </el-form-item>
          <el-form-item label="規格說明">
            <el-input v-model="filters.spec" placeholder="輸入規格說明" clearable style="width: 200px" @keyup.enter="searchInventory" />
          </el-form-item>
          <el-form-item label="請購單號">
            <el-input v-model="filters.request_no" placeholder="輸入請購單號" clearable style="width: 200px" @keyup.enter="searchInventory" />
          </el-form-item>
          <el-form-item label="採購單號">
            <el-input v-model="filters.po_no" placeholder="輸入採購單號" clearable style="width: 200px" @keyup.enter="searchInventory" />
          </el-form-item>
        </el-form>
        
        <el-form :model="filters" label-width="100px" :inline="true">
          <el-form-item label="儲存區域">
            <el-select v-model="filters.zone" placeholder="選擇區域" clearable style="width: 120px">
              <el-option v-for="zone in availableZones" :key="zone" :label="zone" :value="zone" />
            </el-select>
          </el-form-item>
          <el-form-item label="貨架">
            <el-select v-model="filters.shelf" placeholder="選擇貨架" clearable style="width: 100px">
              <el-option v-for="shelf in availableShelves" :key="shelf" :label="shelf" :value="shelf" />
            </el-select>
          </el-form-item>
          <el-form-item label="樓層">
            <el-select v-model="filters.floor" placeholder="選擇樓層" clearable style="width: 100px">
              <el-option v-for="floor in availableFloors" :key="floor" :label="`第${floor}層`" :value="floor" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="searchInventory" :loading="loading">
              <el-icon><Search /></el-icon>
              查詢
            </el-button>
            <el-button @click="exportInventory" :disabled="!inventoryItems.length">
              <el-icon><Download /></el-icon>
              匯出
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- Inventory Results Table -->
    <div class="results-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>庫存清單 ({{ inventoryItems.length }} 筆)</span>
            <div>
              <el-button size="small" @click="refreshData">
                <el-icon><Refresh /></el-icon>
                重新整理
              </el-button>
            </div>
          </div>
        </template>
        
        <el-table 
          :data="inventoryItems" 
          v-loading="loading"
          stripe
        >
          <el-table-column prop="item_name" label="物料名稱" width="180">
            <template #default="{ row }">
              <div class="item-info">
                <div class="item-name">{{ row.item_name }}</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="item_specification" label="規格" width="200">
            <template #default="{ row }">
              <div class="item-spec-column">{{ row.item_specification || '-' }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="usage_type" label="用途" width="100" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="getUsageTagType(row.usage_type)">
                {{ getUsageLabel(row.usage_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="total_quantity" label="總庫存數量" width="120" align="right">
            <template #default="{ row }">
              <el-tag :type="getQuantityTagType(row.total_quantity)">
                {{ row.total_quantity }} {{ row.unit }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="batch_count" label="批次數量" width="90" align="center">
            <template #default="{ row }">
              <el-badge :value="row.batch_count" type="primary">
                <el-tag size="small" type="info">{{ row.batch_count }} 批</el-tag>
              </el-badge>
            </template>
          </el-table-column>
          <el-table-column prop="storage_location_count" label="儲存位置" width="100" align="center">
            <template #default="{ row }">
              <el-tag size="small" type="success">{{ row.storage_location_count }} 個位置</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="last_received_date" label="最近收貨" width="100">
            <template #default="{ row }">
              {{ formatDate(row.last_received_date) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" @click="viewItemDetails(row)">
                <el-icon><View /></el-icon>
                詳情
              </el-button>
              <el-button size="small" type="info" @click="viewItemHistory(row)">
                <el-icon><Clock /></el-icon>
                履歷
              </el-button>
              <el-button size="small" @click="showIssueDialog(row)">
                <el-icon><Minus /></el-icon>
                領用
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- Issue Item Dialog -->
    <el-dialog v-model="issueDialogVisible" title="物料領用" width="500px">
      <el-form :model="issueForm" :rules="issueRules" ref="issueFormRef" label-width="100px">
        <el-form-item label="物料名稱">
          <el-input :value="selectedItem?.item_name" disabled />
        </el-form-item>
        <el-form-item label="可用數量">
          <el-input :value="`${selectedItem?.total_quantity || 0} ${selectedItem?.unit || ''}`" disabled />
        </el-form-item>
        <el-alert
          title="注意"
          description="此物料有多個批次，請前往詳情頁面選擇特定批次進行領用"
          type="info"
          show-icon
          :closable="false"
          style="margin-bottom: 15px;"
        />
        <el-form-item label="領用數量" prop="quantity">
          <el-input-number 
            v-model="issueForm.quantity" 
            :min="0.01" 
            :max="selectedItem?.current_quantity || 0"
            :precision="2"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="用途類型" prop="usage_type">
          <el-select v-model="issueForm.usage_type" style="width: 100%">
            <el-option label="日常使用" value="daily" />
            <el-option label="專案使用" value="project" />
          </el-select>
        </el-form-item>
        <el-form-item label="備註">
          <el-input v-model="issueForm.note" type="textarea" rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="issueDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmIssue" :loading="issueLoading">確認領用</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Download, Refresh, Minus, Clock, View } from '@element-plus/icons-vue'
import { inventoryApi, type InventoryFilters } from '@/api/inventory'
import { useRouter } from 'vue-router'

// Router
const router = useRouter()

// Reactive data
const loading = ref(false)
const inventoryItems = ref<any[]>([])
const storageTree = ref<any[]>([])

// Search filters
const filters = reactive<InventoryFilters>({
  name: '',
  spec: '',
  request_no: '',
  po_no: '',
  zone: '',
  shelf: '',
  floor: undefined
})

// Computed options based on storage tree
const availableZones = computed(() => {
  return storageTree.value.map(area => area.area_code)
})

const availableShelves = computed(() => {
  if (!filters.zone) return []
  const selectedZone = storageTree.value.find(area => area.area_code === filters.zone)
  if (!selectedZone) return []
  return selectedZone.shelves.map((shelf: any) => shelf.shelf_code)
})

const availableFloors = computed(() => {
  if (!filters.zone || !filters.shelf) return []
  const selectedZone = storageTree.value.find(area => area.area_code === filters.zone)
  if (!selectedZone) return []
  const selectedShelf = selectedZone.shelves.find((shelf: any) => shelf.shelf_code === filters.shelf)
  if (!selectedShelf) return []
  return selectedShelf.floors.map((floor: any) => floor.floor_level)
})

// Watch for zone changes to reset dependent fields
watch(() => filters.zone, (newZone) => {
  if (!newZone) {
    filters.shelf = ''
    filters.floor = undefined
  } else {
    // Check if current shelf is still valid
    if (filters.shelf && !availableShelves.value.includes(filters.shelf)) {
      filters.shelf = ''
      filters.floor = undefined
    }
  }
})

// Watch for shelf changes to reset floor
watch(() => filters.shelf, (newShelf) => {
  if (!newShelf) {
    filters.floor = undefined
  } else {
    // Check if current floor is still valid
    if (filters.floor && !availableFloors.value.includes(filters.floor)) {
      filters.floor = undefined
    }
  }
})

// Issue dialog
const issueDialogVisible = ref(false)
const issueLoading = ref(false)
const selectedItem = ref<any>(null)
const issueForm = reactive({
  quantity: 0,
  usage_type: 'daily',
  note: ''
})
const issueFormRef = ref()

// Form rules
const issueRules = {
  quantity: [
    { required: true, message: '請輸入領用數量', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '領用數量必須大於0', trigger: 'blur' }
  ],
  usage_type: [
    { required: true, message: '請選擇用途類型', trigger: 'change' }
  ]
}

// Methods
const loadStorageTree = async () => {
  try {
    const tree = await inventoryApi.getStorageTree()
    storageTree.value = tree
  } catch (error) {
    console.error('Failed to load storage tree:', error)
    // Use fallback values if API fails
    storageTree.value = [
      {
        area_code: 'Z1',
        shelves: [
          { shelf_code: 'A', floors: [{ floor_level: 1 }, { floor_level: 2 }, { floor_level: 3 }] },
          { shelf_code: 'B', floors: [{ floor_level: 1 }, { floor_level: 2 }, { floor_level: 3 }] }
        ]
      },
      {
        area_code: 'Z2',
        shelves: [
          { shelf_code: 'A', floors: [{ floor_level: 1 }, { floor_level: 2 }, { floor_level: 3 }] },
          { shelf_code: 'B', floors: [{ floor_level: 1 }, { floor_level: 2 }, { floor_level: 3 }] }
        ]
      }
    ]
  }
}

const searchInventory = async () => {
  try {
    loading.value = true
    // Build query params from filters
    const queryParams: any = {}
    
    if (filters.name) queryParams.name = filters.name
    if (filters.spec) queryParams.spec = filters.spec
    if (filters.request_no) queryParams.request_no = filters.request_no
    if (filters.po_no) queryParams.po_no = filters.po_no
    if (filters.zone) queryParams.zone = filters.zone
    if (filters.shelf) queryParams.shelf = filters.shelf
    if (filters.floor) queryParams.floor = filters.floor
    
    // Use new grouped inventory API through the API service
    const data = await inventoryApi.getInventoryItemsGrouped(queryParams)
    inventoryItems.value = data
    
    if (data.length === 0) {
      ElMessage.info('未找到符合條件的庫存資料')
    } else {
      ElMessage.success(`找到 ${data.length} 筆庫存資料`)
    }
  } catch (error) {
    console.error('Query inventory error:', error)
    ElMessage.error('查詢庫存失敗')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  Object.assign(filters, {
    name: '',
    spec: '',
    request_no: '',
    po_no: '',
    zone: '',
    shelf: '',
    floor: undefined
  })
  searchInventory()
}

const refreshData = () => {
  searchInventory()
}

const viewItemDetails = (item: any) => {
  router.push(`/inventory/items/${encodeURIComponent(item.item_key)}/details`)
}

const viewItemHistory = (item: any) => {
  router.push(`/inventory/items/${encodeURIComponent(item.item_key)}/details?tab=history`)
}

const showIssueDialog = (item: any) => {
  selectedItem.value = item
  issueForm.quantity = 1
  issueForm.usage_type = 'daily'
  issueForm.note = ''
  issueDialogVisible.value = true
}

const confirmIssue = async () => {
  try {
    await issueFormRef.value?.validate()
    issueLoading.value = true
    
    // Note: For grouped items, we need to implement batch selection for issuing
    // This is a placeholder - in Phase 1, we'll show a message
    ElMessage.info('批次物料領用功能將在後續版本中實現，請使用詳情頁面進行操作')
    issueDialogVisible.value = false
    
  } catch (error) {
    ElMessage.error('物料領用失敗')
  } finally {
    issueLoading.value = false
  }
}

const exportInventory = async () => {
  try {
    const blob = await inventoryApi.exportInventory(filters)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `inventory_${new Date().toISOString().split('T')[0]}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('匯出成功')
  } catch (error) {
    ElMessage.error('匯出失敗')
  }
}

const viewSource = (sourceNo: string) => {
  // Navigate to source document
  ElMessage.info(`檢視來源單號: ${sourceNo}`)
}

const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('zh-TW')
}

const getQuantityTagType = (quantity: number) => {
  if (quantity <= 0) return 'danger'
  if (quantity <= 10) return 'warning'
  return 'success'
}

const getUsageTagType = (usageType: string) => {
  switch (usageType) {
    case 'daily': return 'info'
    case 'project': return 'warning'
    case 'production': return 'success'
    case 'maintenance': return 'danger'
    default: return ''
  }
}

const getUsageLabel = (usageType: string) => {
  const usageMap: Record<string, string> = {
    'daily': '日常使用',
    'project': '專案使用',
    'production': '生產用',
    'maintenance': '維護用',
    'office': '辦公用',
    'it': 'IT設備'
  }
  return usageMap[usageType] || usageType || '一般'
}

// Initialize
onMounted(async () => {
  await loadStorageTree()
  searchInventory()
})
</script>

<style scoped>
.inventory-query {
  padding: 20px;
}

.search-section, .results-section {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-card .el-form {
  margin-bottom: 10px;
}

.item-info .item-name {
  font-weight: bold;
  color: #303133;
}

.item-spec-column {
  font-size: 13px;
  color: #606266;
  line-height: 1.4;
}

.storage-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.storage-details {
  font-size: 12px;
  color: #666;
}
</style>