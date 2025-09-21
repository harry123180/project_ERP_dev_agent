<template>
  <div class="storage-container">
    <PageHeader 
      title="庫存管理" 
      subtitle="Storage Management"
    >
      <template #actions>
        <el-button-group>
          <el-button 
            type="primary" 
            @click="showCreateDialog = true"
            :icon="Plus"
          >
            新增儲位
          </el-button>
          <el-button 
            type="info" 
            @click="showTreeView = !showTreeView"
            :icon="showTreeView ? List : TreeTable"
          >
            {{ showTreeView ? '列表檢視' : '樹狀檢視' }}
          </el-button>
        </el-button-group>
      </template>
    </PageHeader>

    <!-- Storage Statistics -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <StatCard
          title="總儲位數"
          :value="stats.totalLocations"
          icon="Grid"
          color="#409EFF"
        />
      </el-col>
      <el-col :span="6">
        <StatCard
          title="可用儲位"
          :value="stats.availableLocations"
          icon="Check"
          color="#67C23A"
        />
      </el-col>
      <el-col :span="6">
        <StatCard
          title="使用率"
          :value="`${stats.utilizationRate}%`"
          icon="PieChart"
          color="#E6A23C"
        />
      </el-col>
      <el-col :span="6">
        <StatCard
          title="待入庫"
          :value="stats.pendingPutaway"
          icon="Upload"
          color="#F56C6C"
        />
      </el-col>
    </el-row>

    <!-- Quick Actions -->
    <el-card class="actions-card">
      <div class="actions-header">
        <h3>快速操作</h3>
      </div>
      <div class="actions-grid">
        <div class="action-item" @click="showPutawayDialog = true">
          <el-icon size="32"><Upload /></el-icon>
          <span>批量入庫</span>
        </div>
        <div class="action-item" @click="showMovementDialog = true">
          <el-icon size="32"><Sort /></el-icon>
          <span>庫存移動</span>
        </div>
        <div class="action-item" @click="generateStorageReport">
          <el-icon size="32"><Document /></el-icon>
          <span>庫存報表</span>
        </div>
        <div class="action-item" @click="optimizeStorage">
          <el-icon size="32"><Setting /></el-icon>
          <span>儲位優化</span>
        </div>
      </div>
    </el-card>

    <!-- Tree View -->
    <el-card v-if="showTreeView" class="tree-card">
      <template #header>
        <div class="card-header">
          <span>儲位階層</span>
          <div class="tree-actions">
            <el-button size="small" @click="expandAll">展開全部</el-button>
            <el-button size="small" @click="collapseAll">收合全部</el-button>
          </div>
        </div>
      </template>
      
      <StorageTree
        :tree-data="storageTree"
        :loading="loading"
        @location-click="selectLocation"
        @edit-location="editLocation"
        @view-items="viewLocationItems"
      />
    </el-card>

    <!-- List View -->
    <el-card v-else class="table-card">
      <template #header>
        <div class="card-header">
          <span>儲位列表</span>
          <!-- Filters -->
          <div class="filter-controls">
            <el-select v-model="filters.zone" placeholder="選擇區域" clearable style="width: 120px">
              <el-option 
                v-for="zone in zones" 
                :key="zone"
                :label="zone"
                :value="zone" 
              />
            </el-select>
            <el-select v-model="filters.available_only" placeholder="可用狀態" clearable style="width: 120px">
              <el-option label="僅可用" :value="true" />
              <el-option label="全部" :value="false" />
            </el-select>
            <el-button type="primary" @click="loadStorageLocations" size="small">篩選</el-button>
          </div>
        </div>
      </template>
      
      <DataTable
        :data="storageLocations"
        :columns="columns"
        :loading="loading"
        :pagination="pagination"
        @page-change="handlePageChange"
        @sort-change="handleSortChange"
      >
        <template #location="{ row }">
          <div class="location-cell">
            <div class="location-path">
              <el-tag size="small" type="primary">{{ row.zone }}</el-tag>
              <span class="separator">></span>
              <el-tag size="small" type="success">{{ row.shelf }}</el-tag>
              <span class="separator">></span>
              <el-tag size="small" type="warning">{{ row.floor }}</el-tag>
              <span class="separator">></span>
              <el-tag size="small">{{ row.position }}</el-tag>
            </div>
          </div>
        </template>
        
        <template #capacity="{ row }">
          <div class="capacity-cell">
            <el-progress
              :percentage="row.utilization_percent"
              :status="getCapacityStatus(row.utilization_percent)"
              :show-text="false"
              :stroke-width="8"
            />
            <div class="capacity-text">
              {{ row.current_capacity }} / {{ row.max_capacity }}
            </div>
          </div>
        </template>
        
        <template #status="{ row }">
          <StatusTag :status="getLocationStatus(row)" />
        </template>
        
        <template #current_items="{ row }">
          <div class="items-preview">
            <div v-if="row.current_items?.length" class="items-list">
              <div 
                v-for="(item, index) in row.current_items.slice(0, 2)" 
                :key="index"
                class="item-tag"
              >
                {{ item.item_reference }}
              </div>
              <div v-if="row.current_items.length > 2" class="more-items">
                +{{ row.current_items.length - 2 }}
              </div>
            </div>
            <span v-else class="no-items">無物品</span>
          </div>
        </template>
        
        <template #actions="{ row }">
          <el-button-group>
            <el-button 
              size="small" 
              type="primary" 
              @click="viewLocationItems(row)"
              :icon="View"
            >
              檢視
            </el-button>
            <el-button 
              size="small" 
              @click="editLocation(row)"
              :icon="Edit"
            >
              編輯
            </el-button>
            <el-button 
              size="small" 
              type="warning" 
              @click="moveItems(row)"
              :icon="Sort"
            >
              移動
            </el-button>
          </el-button-group>
        </template>
      </DataTable>
    </el-card>

    <!-- Create/Edit Location Dialog -->
    <FormDialog
      v-model="showCreateDialog"
      :title="isEditing ? '編輯儲位' : '新增儲位'"
      @confirm="handleSaveLocation"
    >
      <el-form
        ref="locationFormRef"
        :model="locationForm"
        :rules="locationRules"
        label-width="80px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="區域" prop="zone">
              <el-input v-model="locationForm.zone" placeholder="輸入區域名稱" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="貨架" prop="shelf">
              <el-input v-model="locationForm.shelf" placeholder="輸入貨架名稱" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="樓層" prop="floor">
              <el-input v-model="locationForm.floor" placeholder="輸入樓層" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="位置" prop="position">
              <el-input v-model="locationForm.position" placeholder="輸入位置" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="儲位類型">
              <el-select v-model="locationForm.storage_type" placeholder="選擇類型">
                <el-option label="貨架" value="rack" />
                <el-option label="貨櫃" value="bin" />
                <el-option label="棧板" value="pallet" />
                <el-option label="樓層" value="floor" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大容量" prop="max_capacity">
              <el-input-number
                v-model="locationForm.max_capacity"
                :min="1"
                :max="10000"
                placeholder="最大容量"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="描述">
          <el-input
            v-model="locationForm.description"
            type="textarea"
            :rows="2"
            placeholder="儲位描述"
          />
        </el-form-item>
        
        <el-form-item label="狀態">
          <el-switch
            v-model="locationForm.is_available"
            active-text="可用"
            inactive-text="不可用"
          />
        </el-form-item>
      </el-form>
    </FormDialog>

    <!-- Putaway Dialog -->
    <el-dialog
      v-model="showPutawayDialog"
      title="批量入庫作業"
      width="80%"
      top="5vh"
    >
      <PutawayOperation @close="showPutawayDialog = false" />
    </el-dialog>

    <!-- Storage Movement Dialog -->
    <el-dialog
      v-model="showMovementDialog"
      title="庫存移動"
      width="70%"
    >
      <StorageMovement @close="showMovementDialog = false" />
    </el-dialog>

    <!-- Location Items Dialog -->
    <el-dialog
      v-model="showItemsDialog"
      :title="`儲位物品 - ${selectedLocation?.zone}-${selectedLocation?.shelf}-${selectedLocation?.floor}-${selectedLocation?.position}`"
      width="70%"
    >
      <LocationItems 
        v-if="selectedLocation"
        :location="selectedLocation" 
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, List, TreeTable, Upload, Sort, Document, Setting, 
  View, Edit, PieChart, Grid, Check 
} from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import DataTable from '@/components/DataTable.vue'
import StatCard from '@/components/StatCard.vue'
import StatusTag from '@/components/StatusTag.vue'
import FormDialog from '@/components/FormDialog.vue'
import StorageTree from './StorageTree.vue'
import PutawayOperation from './PutawayOperation.vue'
import StorageMovement from './StorageMovement.vue'
import LocationItems from './LocationItems.vue'
import { useStorageStore } from '@/stores/storageStore'
import type { StorageLocation } from '@/types/storage'

// Store instance
const storageStore = useStorageStore()

// Reactive data
const loading = ref(false)
const showTreeView = ref(true)
const showCreateDialog = ref(false)
const showPutawayDialog = ref(false)
const showMovementDialog = ref(false)
const showItemsDialog = ref(false)
const isEditing = ref(false)
const selectedLocation = ref<StorageLocation | null>(null)
const locationFormRef = ref()

// Filters
const filters = reactive({
  zone: '',
  shelf: '',
  floor: '',
  available_only: null,
  storage_type: '',
  page: 1,
  page_size: 20
})

// Location form
const locationForm = reactive({
  zone: '',
  shelf: '',
  floor: '',
  position: '',
  storage_type: 'rack',
  max_capacity: 100,
  description: '',
  is_available: true
})

// Form validation rules
const locationRules = {
  zone: [
    { required: true, message: '請輸入區域名稱', trigger: 'blur' }
  ],
  shelf: [
    { required: true, message: '請輸入貨架名稱', trigger: 'blur' }
  ],
  floor: [
    { required: true, message: '請輸入樓層', trigger: 'blur' }
  ],
  position: [
    { required: true, message: '請輸入位置', trigger: 'blur' }
  ],
  max_capacity: [
    { required: true, message: '請輸入最大容量', trigger: 'blur' },
    { type: 'number', min: 1, message: '容量必須大於 0', trigger: 'blur' }
  ]
}

// Table columns
const columns = [
  { prop: 'location', label: '儲位位置', minWidth: 200, slot: 'location' },
  { prop: 'storage_type', label: '類型', width: 100 },
  { prop: 'capacity', label: '容量使用率', width: 150, slot: 'capacity' },
  { prop: 'is_available', label: '狀態', width: 100, slot: 'status' },
  { prop: 'current_items', label: '當前物品', minWidth: 150, slot: 'current_items' },
  { prop: 'updated_at', label: '更新時間', width: 150 },
  { prop: 'actions', label: '操作', width: 200, slot: 'actions', fixed: 'right' }
]

// Computed properties
const storageLocations = computed(() => storageStore.storageLocations)
const storageTree = computed(() => storageStore.storageTree)
const pagination = computed(() => storageStore.pagination)

const zones = computed(() => {
  const zoneSet = new Set(storageLocations.value.map(loc => loc.zone))
  return Array.from(zoneSet).filter(zone => zone)
})

const stats = computed(() => {
  const locations = storageLocations.value
  const totalLocations = locations.length
  const availableLocations = locations.filter(loc => loc.is_available).length
  const totalCapacity = locations.reduce((sum, loc) => sum + (loc.max_capacity || 0), 0)
  const usedCapacity = locations.reduce((sum, loc) => sum + (loc.current_capacity || 0), 0)
  const utilizationRate = totalCapacity > 0 ? Math.round((usedCapacity / totalCapacity) * 100) : 0
  
  return {
    totalLocations,
    availableLocations,
    utilizationRate,
    pendingPutaway: 0 // This should come from API
  }
})

// Methods
const loadStorageLocations = async () => {
  loading.value = true
  try {
    await storageStore.fetchStorageLocations(filters)
  } catch (error) {
    ElMessage.error('載入儲位列表失敗')
  } finally {
    loading.value = false
  }
}

const loadStorageTree = async () => {
  loading.value = true
  try {
    await storageStore.fetchStorageTree()
  } catch (error) {
    ElMessage.error('載入儲位樹失敗')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  filters.page = page
  loadStorageLocations()
}

const handleSortChange = (sort: any) => {
  loadStorageLocations()
}

const selectLocation = (location: StorageLocation) => {
  selectedLocation.value = location
}

const editLocation = (location: StorageLocation) => {
  Object.assign(locationForm, location)
  selectedLocation.value = location
  isEditing.value = true
  showCreateDialog.value = true
}

const viewLocationItems = (location: StorageLocation) => {
  selectedLocation.value = location
  showItemsDialog.value = true
}

const moveItems = (location: StorageLocation) => {
  selectedLocation.value = location
  showMovementDialog.value = true
}

const handleSaveLocation = async () => {
  if (!locationFormRef.value) return
  
  try {
    await locationFormRef.value.validate()
    
    if (isEditing.value) {
      await storageStore.updateStorageLocation(selectedLocation.value!.id, locationForm)
      ElMessage.success('儲位更新成功')
    } else {
      await storageStore.createStorageLocation(locationForm)
      ElMessage.success('儲位建立成功')
    }
    
    showCreateDialog.value = false
    resetForm()
    loadStorageLocations()
    if (showTreeView.value) {
      loadStorageTree()
    }
  } catch (error) {
    ElMessage.error(isEditing.value ? '儲位更新失敗' : '儲位建立失敗')
  }
}

const resetForm = () => {
  Object.assign(locationForm, {
    zone: '',
    shelf: '',
    floor: '',
    position: '',
    storage_type: 'rack',
    max_capacity: 100,
    description: '',
    is_available: true
  })
  isEditing.value = false
  selectedLocation.value = null
}

const expandAll = () => {
  // Implement tree expansion
  ElMessage.info('展開全部功能')
}

const collapseAll = () => {
  // Implement tree collapse
  ElMessage.info('收合全部功能')
}

const generateStorageReport = () => {
  ElMessage.info('生成庫存報表功能開發中')
}

const optimizeStorage = () => {
  ElMessage.info('儲位優化功能開發中')
}

const getCapacityStatus = (utilization: number) => {
  if (utilization >= 100) return 'exception'
  if (utilization >= 90) return 'warning'
  return 'success'
}

const getLocationStatus = (location: StorageLocation) => {
  if (!location.is_available) return { text: '不可用', type: 'danger' }
  if (location.current_capacity >= location.max_capacity) return { text: '已滿', type: 'warning' }
  return { text: '可用', type: 'success' }
}

// Lifecycle
onMounted(() => {
  loadStorageLocations()
  loadStorageTree()
})
</script>

<style scoped>
.storage-container {
  padding: 20px;
}

.stats-row {
  margin: 20px 0;
}

.actions-card {
  margin: 20px 0;
}

.actions-header h3 {
  margin: 0 0 15px 0;
  color: #333;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.action-item:hover {
  background: #e3f2fd;
  border-color: #409EFF;
}

.action-item span {
  font-size: 14px;
  color: #666;
}

.tree-card, .table-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tree-actions, .filter-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.location-cell {
  display: flex;
  flex-direction: column;
}

.location-path {
  display: flex;
  align-items: center;
  gap: 5px;
}

.separator {
  color: #ccc;
  font-size: 12px;
}

.capacity-cell {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.capacity-text {
  font-size: 12px;
  color: #666;
  text-align: center;
}

.items-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.items-list {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
}

.item-tag {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  color: #0369a1;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 3px;
}

.more-items {
  background: #f3f4f6;
  color: #6b7280;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 3px;
}

.no-items {
  color: #9ca3af;
  font-size: 12px;
}
</style>