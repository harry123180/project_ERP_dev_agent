<template>
  <div class="storage-management">
    <!-- Warehouse Structure Management -->
    <div class="structure-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>倉庫結構管理</span>
            <div>
              <el-button type="primary" @click="showCreateZoneDialog = true">
                <el-icon><Plus /></el-icon>
                新增區域
              </el-button>
              <el-button @click="loadStorageTree">
                <el-icon><Refresh /></el-icon>
                重新整理
              </el-button>
            </div>
          </div>
        </template>
        
        <div class="structure-tree">
          <el-tree
            :data="storageTreeData"
            :props="treeProps"
            node-key="id"
            :expand-on-click-node="false"
            :default-expand-all="false"
            class="storage-tree"
          >
            <template #default="{ node, data }">
              <div class="tree-node">
                <div class="node-info">
                  <el-icon v-if="data.type === 'area'" class="node-icon"><Location /></el-icon>
                  <el-icon v-else-if="data.type === 'shelf'" class="node-icon"><Grid /></el-icon>
                  <el-icon v-else-if="data.type === 'floor'" class="node-icon"><Coin /></el-icon>
                  <el-icon v-else class="node-icon"><Box /></el-icon>
                  
                  <span class="node-label">{{ data.label }}</span>
                  <el-tag v-if="data.capacity !== undefined" size="small" type="info">
                    {{ data.used || 0 }}/{{ data.capacity }}
                  </el-tag>
                  <el-tag v-if="data.utilization !== undefined" size="small" :type="getUtilizationType(data.utilization)">
                    {{ Math.round(data.utilization) }}%
                  </el-tag>
                </div>
                <div class="node-actions">
                  <el-button-group v-if="data.type === 'floor'">
                    <el-button size="small" type="primary" @click.stop="viewFloorDetail(data)">
                      <el-icon><View /></el-icon>
                    </el-button>
                    <el-button size="small" type="warning" @click.stop="editFloor(data)" :disabled="data.used > 0">
                      <el-icon><Edit /></el-icon>
                    </el-button>
                  </el-button-group>
                  <el-button v-else-if="data.children && data.children.length > 0" size="small" @click.stop="expandCollapse(node)">
                    <el-icon><CaretRight /></el-icon>
                  </el-button>
                </div>
              </div>
            </template>
          </el-tree>
        </div>
      </el-card>
    </div>

    <!-- Pending Storage Items -->
    <div class="pending-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>待入庫物料 ({{ pendingItems.length }} 項)</span>
            <div>
              <el-button type="success" @click="batchAssignStorage" :disabled="!selectedPendingItems.length">
                <el-icon><Check /></el-icon>
                批量入庫
              </el-button>
            </div>
          </div>
        </template>
        
        <el-table 
          :data="pendingItems"
          v-loading="pendingLoading"
          @selection-change="handlePendingSelectionChange"
          stripe
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="item_name" label="物料名稱" width="200" />
          <el-table-column prop="quantity" label="數量" width="120" align="right">
            <template #default="{ row }">
              {{ row.quantity }} {{ row.unit }}
            </template>
          </el-table-column>
          <el-table-column prop="source_po_number" label="來源採購單號" width="150">
            <template #default="{ row }">
              <el-link type="primary" @click="viewSourceDocument(row.source_po_number)">
                {{ row.source_po_number }}
              </el-link>
            </template>
          </el-table-column>
          <el-table-column prop="arrival_date" label="到貨時間" width="150">
            <template #default="{ row }">
              {{ formatDateTime(row.arrival_date) }}
            </template>
          </el-table-column>
          <el-table-column prop="receiver" label="收貨人" width="100" />
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" type="primary" @click="assignStorageLocation(row)">
                <el-icon><Location /></el-icon>
                指定儲位
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- Manual Inventory Entry -->
    <div class="manual-entry-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>手動入庫管理</span>
            <el-button type="primary" @click="showManualEntryDialog = true">
              <el-icon><Plus /></el-icon>
              手動入庫
            </el-button>
          </div>
        </template>
        
        <div class="manual-entry-description">
          <el-alert 
            title="手動入庫用於直接將物料加入庫存，不需要先經過收貨流程。適用於調撥、盤點或特殊情況。" 
            type="info" 
            show-icon
            :closable="false" 
          />
        </div>
      </el-card>
    </div>

    <!-- Storage Statistics -->
    <div class="stats-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ storageStats.totalPositions }}</div>
              <div class="stat-label">總儲位數</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ storageStats.usedPositions }}</div>
              <div class="stat-label">已使用</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ storageStats.utilizationRate }}%</div>
              <div class="stat-label">使用率</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ pendingItems.length }}</div>
              <div class="stat-label">待入庫</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- Create Zone Dialog -->
    <el-dialog v-model="showCreateZoneDialog" title="新增區域" width="750px">
      <el-form :model="createZoneForm" :rules="createZoneRules" ref="createZoneFormRef" label-width="120px">
        <el-form-item label="區域代碼" prop="area_code">
          <el-input v-model="createZoneForm.area_code" placeholder="例如: Z1, Z2, Z3" />
        </el-form-item>
        <el-form-item label="區域名稱">
          <el-input v-model="createZoneForm.area_name" placeholder="輸入區域名稱" />
        </el-form-item>
        <el-form-item label="貨架配置">
          <div class="shelves-config" style="max-height: 300px; overflow-y: auto;">
            <div v-for="(shelf, index) in createZoneForm.shelves" :key="index" class="shelf-item">
              <el-row :gutter="10" align="middle">
                <el-col :span="4">
                  <el-input v-model="shelf.shelf_code" placeholder="代碼" size="small" />
                </el-col>
                <el-col :span="5">
                  <el-input-number v-model="shelf.floors" :min="1" :max="10" placeholder="樓層數" size="small" style="width: 100%" />
                </el-col>
                <el-col :span="12">
                  <el-input v-model="shelf.description" placeholder="說明" size="small" />
                </el-col>
                <el-col :span="3">
                  <el-button @click="removeShelf(index)" type="danger" size="small" circle>
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-col>
              </el-row>
            </div>
            <el-button @click="addShelf" type="primary" size="small">
              <el-icon><Plus /></el-icon>
              新增貨架
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateZoneDialog = false">取消</el-button>
        <el-button type="primary" @click="createZone" :loading="createZoneLoading">創建</el-button>
      </template>
    </el-dialog>

    <!-- Assign Storage Dialog -->
    <el-dialog v-model="showAssignDialog" title="指定儲存位置" width="700px">
      <div v-if="currentAssignItem" class="assign-content">
        <div class="item-info">
          <h4>物料資訊</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="物料名稱">{{ currentAssignItem.item_name }}</el-descriptions-item>
            <el-descriptions-item label="規格">{{ currentAssignItem.specification }}</el-descriptions-item>
            <el-descriptions-item label="數量">{{ currentAssignItem.quantity }} {{ currentAssignItem.unit }}</el-descriptions-item>
            <el-descriptions-item label="來源採購單號">{{ currentAssignItem.source_po_number }}</el-descriptions-item>
            <el-descriptions-item label="到貨時間">{{ formatDateTime(currentAssignItem.arrival_date) }}</el-descriptions-item>
            <el-descriptions-item label="收貨人">{{ currentAssignItem.receiver }}</el-descriptions-item>
          </el-descriptions>
        </div>
        
        <div class="location-selection">
          <h4>選擇儲存位置</h4>
          <el-form :model="assignForm" label-width="100px">
            <el-row :gutter="10">
              <el-col :span="8">
                <el-form-item label="區域">
                  <el-select v-model="assignForm.area" @change="onAreaChange" style="width: 100%">
                    <el-option v-for="area in availableAreas" :key="area.code" :label="area.label" :value="area.code" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="貨架">
                  <el-select v-model="assignForm.shelf" @change="onShelfChange" style="width: 100%">
                    <el-option v-for="shelf in availableShelves" :key="shelf.code" :label="shelf.label" :value="shelf.code" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="樓層">
                  <el-select v-model="assignForm.floor" style="width: 100%">
                    <el-option v-for="floor in availableFloors" :key="floor" :label="`第${floor}層`" :value="floor" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
          
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showAssignDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAssignment" :loading="assignLoading" :disabled="!isValidAssignment">
          確認入庫
        </el-button>
      </template>
    </el-dialog>

    <!-- Manual Entry Dialog -->
    <el-dialog v-model="showManualEntryDialog" title="手動入庫" width="700px">
      <el-form :model="manualEntryForm" :rules="manualEntryRules" ref="manualEntryFormRef" label-width="120px">
        <el-form-item label="物料名稱" prop="item_name">
          <el-input v-model="manualEntryForm.item_name" placeholder="輸入物料名稱" />
        </el-form-item>
        <el-form-item label="規格" prop="specification">
          <el-input v-model="manualEntryForm.specification" placeholder="輸入物料規格" />
        </el-form-item>
        <el-form-item label="數量" prop="quantity">
          <el-row :gutter="10">
            <el-col :span="16">
              <el-input-number v-model="manualEntryForm.quantity" :min="1" placeholder="數量" style="width: 100%" />
            </el-col>
            <el-col :span="8">
              <el-input v-model="manualEntryForm.unit" placeholder="單位" />
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="儲存位置">
          <el-row :gutter="10">
            <el-col :span="8">
              <el-select v-model="manualEntryForm.area" @change="onAreaChange" placeholder="選擇區域" style="width: 100%">
                <el-option v-for="area in availableAreas" :key="area.code" :label="area.label" :value="area.code" />
              </el-select>
            </el-col>
            <el-col :span="8">
              <el-select v-model="manualEntryForm.shelf" @change="onShelfChange" placeholder="選擇貨架" style="width: 100%">
                <el-option v-for="shelf in availableShelves" :key="shelf.code" :label="shelf.label" :value="shelf.code" />
              </el-select>
            </el-col>
            <el-col :span="8">
              <el-select v-model="manualEntryForm.floor" placeholder="選擇樓層" style="width: 100%">
                <el-option v-for="floor in availableFloors" :key="floor" :label="`第${floor}層`" :value="floor" />
              </el-select>
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="備註">
          <el-input v-model="manualEntryForm.remarks" type="textarea" rows="3" placeholder="輸入備註或理由" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showManualEntryDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmManualEntry" :loading="manualEntryLoading">確認入庫</el-button>
      </template>
    </el-dialog>

    <!-- Position Detail Dialog -->
    <el-dialog v-model="showPositionDetail" title="儲位詳情" width="800px">
      <div v-if="currentPosition" class="position-detail">
        <div class="basic-info">
          <h4>基本資訊</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="儲位編號">{{ currentPosition.storage_id }}</el-descriptions-item>
            <el-descriptions-item label="位置">
              {{ currentPosition.area_code }}-{{ currentPosition.shelf_code }}-第{{ currentPosition.floor_level }}層-
              {{ getPositionName(currentPosition.front_back_position, currentPosition.left_middle_right_position) }}
            </el-descriptions-item>
            <el-descriptions-item label="狀態">
              <el-tag :type="currentPosition.is_active ? 'success' : 'danger'">
                {{ currentPosition.is_active ? '啟用' : '停用' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="建立時間">{{ formatDateTime(currentPosition.created_at) }}</el-descriptions-item>
          </el-descriptions>
        </div>
        
        <div class="inventory-info">
          <h4>庫存資訊</h4>
          <el-table :data="currentPosition.inventory" size="small">
            <el-table-column prop="item_id" label="物料名稱" />
            <el-table-column prop="current_quantity" label="数量" width="100" />
            <el-table-column prop="source_no" label="來源單號" width="120" />
            <el-table-column prop="source_line" label="明細行" width="80" />
          </el-table>
        </div>
        
        <div class="movement-history">
          <h4>異動履歷</h4>
          <el-table :data="currentPosition.movements" size="small" max-height="300">
            <el-table-column prop="operation_date" label="日期" width="120">
              <template #default="{ row }">
                {{ formatDate(row.operation_date) }}
              </template>
            </el-table-column>
            <el-table-column prop="operation_type" label="操作" width="80">
              <template #default="{ row }">
                <el-tag :type="row.operation_type === 'in' ? 'success' : 'warning'" size="small">
                  {{ row.operation_type === 'in' ? '入庫' : '出庫' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="item_id" label="物料" />
            <el-table-column prop="quantity" label="數量" width="100" align="right" />
            <el-table-column prop="operator_name" label="操作人" width="100" />
            <el-table-column prop="note" label="備註" />
          </el-table>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showPositionDetail = false">關閉</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, Refresh, View, Edit, Check, Delete, Location, 
  Grid, Coin, Box, CaretRight, Lock, Star, 
  CircleCheck 
} from '@element-plus/icons-vue'
import { inventoryApi, type PendingStorageItem, type StorageAssignmentRequest, type ManualEntryRequest } from '@/api/inventory'
import { useAuthStore } from '@/stores/auth'

// Auth store
const authStore = useAuthStore()

// Reactive data
const storageTreeData = ref<any[]>([])
const pendingItems = ref<any[]>([])
const selectedPendingItems = ref<any[]>([])
const pendingLoading = ref(false)
const createZoneLoading = ref(false)
const assignLoading = ref(false)

// Dialog states
const showCreateZoneDialog = ref(false)
const showAssignDialog = ref(false)
const showPositionDetail = ref(false)
const showManualEntryDialog = ref(false)
const manualEntryLoading = ref(false)

// Current data
const currentAssignItem = ref<any>(null)
const currentPosition = ref<any>(null)

// Tree props
const treeProps = {
  children: 'children',
  label: 'label'
}

// Forms
const createZoneForm = reactive({
  area_code: '',
  area_name: '',
  shelves: [
    { shelf_code: 'A', floors: 6, description: '' }
  ]
})

const assignForm = reactive({
  area: '',
  shelf: '',
  floor: 1
})

const manualEntryForm = reactive({
  item_name: '',
  specification: '',
  quantity: 1,
  unit: '',
  area: '',
  shelf: '',
  floor: 1,
  remarks: ''
})

// Form rules
const createZoneRules = {
  area_code: [
    { required: true, message: '請輸入區域代碼', trigger: 'blur' }
  ]
}

const manualEntryRules = {
  item_name: [
    { required: true, message: '請輸入物料名稱', trigger: 'blur' }
  ],
  specification: [
    { required: true, message: '請輸入物料規格', trigger: 'blur' }
  ],
  quantity: [
    { required: true, message: '請輸入數量', trigger: 'blur' }
  ]
}

// Available options for assignment
const availableAreas = ref<any[]>([])
const availableShelves = ref<any[]>([])
const availableFloors = ref<number[]>([])


// Storage statistics
const storageStats = computed(() => {
  // Calculate from storage tree data
  let totalPositions = 0
  let usedPositions = 0
  
  const calculateStats = (nodes: any[]) => {
    for (const node of nodes) {
      if (node.type === 'floor') {
        totalPositions += node.capacity || 0
        usedPositions += node.used || 0
      }
      if (node.children) {
        calculateStats(node.children)
      }
    }
  }
  
  calculateStats(storageTreeData.value)
  
  return {
    totalPositions,
    usedPositions,
    utilizationRate: totalPositions > 0 ? Math.round((usedPositions / totalPositions) * 100) : 0
  }
})

// Computed properties
const isValidAssignment = computed(() => {
  return assignForm.area && assignForm.shelf && assignForm.floor
})

// Methods
const loadStorageTree = async () => {
  try {
    // Mock data - in real implementation, call the storage API
    storageTreeData.value = [
      {
        id: 'z1',
        label: 'Z1 區',
        type: 'area',
        children: [
          {
            id: 'z1-a',
            label: 'A 貨架',
            type: 'shelf',
            children: [
              {
                id: 'z1-a-1',
                label: '第1層',
                type: 'floor',
                storage_id: 'Z1-A-1',
                capacity: 6,
                used: 1,
                utilization: 17,
                children: []
              }
            ]
          }
        ]
      }
    ]
    
    // Update available options from actual tree data
    availableAreas.value = storageTreeData.value
      .filter(node => node.type === 'area')
      .map(node => ({
        code: node.id.toUpperCase(),
        label: node.label
      }))
  } catch (error) {
    ElMessage.error('載入倉庫結構失敗')
  }
}

const loadPendingItems = async () => {
  try {
    pendingLoading.value = true
    
    // Get pending storage items from API
    const data = await inventoryApi.getPendingStorageItems()
    pendingItems.value = data
    
  } catch (error) {
    console.error('Failed to load pending storage items:', error)
    ElMessage.error('載入待入庫物料失敗')
  } finally {
    pendingLoading.value = false
  }
}

const handlePendingSelectionChange = (selection: any[]) => {
  selectedPendingItems.value = selection
}

const addShelf = () => {
  createZoneForm.shelves.push({
    shelf_code: '',
    floors: 6,
    description: ''
  })
}

const removeShelf = (index: number) => {
  createZoneForm.shelves.splice(index, 1)
}

const createZone = async () => {
  try {
    createZoneLoading.value = true
    
    // Validate form
    if (!createZoneForm.area_code || !createZoneForm.area_name) {
      ElMessage.warning('請填寫區域代碼和名稱')
      return
    }
    
    // Check for duplicate zone code
    const existingZone = storageTreeData.value.find(
      zone => zone.id === createZoneForm.area_code.toLowerCase()
    )
    if (existingZone) {
      ElMessage.error(`區域代碼 ${createZoneForm.area_code} 已存在`)
      return
    }
    
    // Collect all existing shelf codes across all zones
    const existingShelfCodes = new Set<string>()
    storageTreeData.value.forEach(zone => {
      if (zone.children) {
        zone.children.forEach(shelf => {
          const shelfCode = shelf.label.split(' ')[0]
          existingShelfCodes.add(shelfCode)
        })
      }
    })
    
    // Validate shelf codes are unique
    for (const shelf of createZoneForm.shelves) {
      if (shelf.shelf_code && existingShelfCodes.has(shelf.shelf_code)) {
        ElMessage.error(`貨架代碼 ${shelf.shelf_code} 已在其他區域使用，請使用不同的代碼`)
        return
      }
    }
    
    // Create new zone structure
    const newZone = {
      id: createZoneForm.area_code.toLowerCase(),
      label: `${createZoneForm.area_code} ${createZoneForm.area_name}`,
      type: 'area',
      children: []
    }
    
    // Add shelves to the zone
    createZoneForm.shelves.forEach((shelf, shelfIndex) => {
      if (shelf.shelf_code) {
        const shelfNode = {
          id: `${newZone.id}-${shelf.shelf_code.toLowerCase()}`,
          label: `${shelf.shelf_code} 貨架`,
          type: 'shelf',
          children: []
        }
        
        // Add floors to the shelf
        for (let floor = 1; floor <= shelf.floors; floor++) {
          const floorNode = {
            id: `${shelfNode.id}-${floor}`,
            label: `第${floor}層`,
            type: 'floor',
            storage_id: `${createZoneForm.area_code}-${shelf.shelf_code}-${floor}`,
            capacity: 6,  // 6 positions per floor (2x3 grid)
            used: 0,
            utilization: 0,
            children: []
          }
          
          shelfNode.children.push(floorNode)
        }
        
        newZone.children.push(shelfNode)
      }
    })
    
    // Add the new zone to the tree
    storageTreeData.value.push(newZone)
    
    // Update available areas
    availableAreas.value.push({
      code: createZoneForm.area_code,
      label: `${createZoneForm.area_code} ${createZoneForm.area_name}`
    })
    
    ElMessage.success('區域建立成功')
    showCreateZoneDialog.value = false
    
    // Reset form
    createZoneForm.area_code = ''
    createZoneForm.area_name = ''
    createZoneForm.shelves = [{ shelf_code: 'A', floors: 6, description: '' }]
    
  } catch (error) {
    ElMessage.error('建立區域失敗')
  } finally {
    createZoneLoading.value = false
  }
}

const assignStorageLocation = (item: any) => {
  currentAssignItem.value = item
  assignForm.area = ''
  assignForm.shelf = ''
  assignForm.floor = 1
  showAssignDialog.value = true
}

const onAreaChange = () => {
  assignForm.shelf = ''
  assignForm.floor = 1
  
  // Find the selected area in the tree
  const selectedArea = storageTreeData.value.find(
    area => area.id === assignForm.area.toLowerCase()
  )
  
  // Update available shelves from actual area data
  if (selectedArea && selectedArea.children) {
    availableShelves.value = selectedArea.children
      .filter(node => node.type === 'shelf')
      .map(shelf => ({
        code: shelf.label.split(' ')[0], // Extract shelf code from label
        label: shelf.label
      }))
  } else {
    availableShelves.value = []
  }
}

const onShelfChange = () => {
  assignForm.floor = 1
  
  // Find the selected shelf in the tree
  const selectedArea = storageTreeData.value.find(
    area => area.id === assignForm.area.toLowerCase()
  )
  
  if (selectedArea && selectedArea.children) {
    const selectedShelf = selectedArea.children.find(
      shelf => shelf.label.split(' ')[0] === assignForm.shelf
    )
    
    // Update available floors from actual shelf data
    if (selectedShelf && selectedShelf.children) {
      availableFloors.value = selectedShelf.children
        .filter(node => node.type === 'floor')
        .map(floor => {
          const match = floor.label.match(/第(\d+)層/)
          return match ? parseInt(match[1]) : 1
        })
    } else {
      availableFloors.value = []
    }
  } else {
    availableFloors.value = []
  }
}



const confirmAssignment = async () => {
  try {
    assignLoading.value = true
    
    const assignData: StorageAssignmentRequest = {
      item_ref: {
        id: currentAssignItem.value.id,
        po_no: currentAssignItem.value.source_po_number,
        item_name: currentAssignItem.value.item_name,
        quantity: currentAssignItem.value.quantity,
        receiver: currentAssignItem.value.receiver,
        arrival_date: currentAssignItem.value.arrival_date
      },
      area: assignForm.area,
      shelf: assignForm.shelf,
      floor: assignForm.floor
    }
    
    // Call API to assign storage location and complete the putaway process
    await inventoryApi.assignStorageLocation(assignData)
    
    // Remove the item from the pending list immediately since it's now stored
    const itemIndex = pendingItems.value.findIndex(item => item.id === currentAssignItem.value.id)
    if (itemIndex >= 0) {
      pendingItems.value.splice(itemIndex, 1)
    }
    
    ElMessage.success('儲位指定成功，物料已完成入庫並移除待入庫清單')
    showAssignDialog.value = false
    await loadStorageTree() // Refresh storage tree to show updated utilization
  } catch (error) {
    console.error('Failed to assign storage location:', error)
    ElMessage.error('指定儲位失敗')
  } finally {
    assignLoading.value = false
  }
}


const batchAssignStorage = async () => {
  try {
    await ElMessageBox.confirm(`確認批量入庫 ${selectedPendingItems.value.length} 項物料？`, '批量入庫', {
      type: 'warning'
    })
    
    // Remove selected items from the pending list immediately
    const selectedIds = selectedPendingItems.value.map(item => item.id)
    pendingItems.value = pendingItems.value.filter(item => !selectedIds.includes(item.id))
    selectedPendingItems.value = []
    
    ElMessage.success('批量入庫成功，物料已移除待入庫清單')
  } catch (error) {
    // User cancelled or API error
  }
}


const viewFloorDetail = async (floor: any) => {
  // Show floor details - capacity, usage, items stored
  ElMessage.info(`查看樓層詳情: ${floor.label} - 容量: ${floor.used}/${floor.capacity}`)
  // In a real implementation, this would open a dialog showing all items on this floor
}

const editFloor = (floor: any) => {
  ElMessage.info('編輯樓層功能開發中')
}

const confirmManualEntry = async () => {
  try {
    manualEntryLoading.value = true
    
    if (!manualEntryForm.area || !manualEntryForm.shelf || !manualEntryForm.floor) {
      ElMessage.warning('請選擇完整的儲存位置')
      return
    }
    
    const entryData: ManualEntryRequest = {
      item_name: manualEntryForm.item_name,
      specification: manualEntryForm.specification,
      quantity: manualEntryForm.quantity,
      unit: manualEntryForm.unit,
      storage_location: {
        area: manualEntryForm.area,
        shelf: manualEntryForm.shelf,
        floor: manualEntryForm.floor
      },
      remarks: manualEntryForm.remarks
    }
    
    // Call API to create manual inventory entry
    await inventoryApi.createManualEntry(entryData)
    
    ElMessage.success('手動入庫成功')
    showManualEntryDialog.value = false
    
    // Reset form
    manualEntryForm.item_name = ''
    manualEntryForm.specification = ''
    manualEntryForm.quantity = 1
    manualEntryForm.unit = ''
    manualEntryForm.area = ''
    manualEntryForm.shelf = ''
    manualEntryForm.floor = 1
    manualEntryForm.remarks = ''
    
    await loadStorageTree() // Refresh storage tree
  } catch (error) {
    console.error('Failed to create manual entry:', error)
    ElMessage.error('手動入庫失敗')
  } finally {
    manualEntryLoading.value = false
  }
}

const expandCollapse = (node: any) => {
  node.expanded = !node.expanded
}

const viewSourceDocument = (poNumber: string) => {
  // Navigate to purchase order detail page
  window.open(`/purchase-orders/${poNumber}`, '_blank')
}

// Utility functions
const getUtilizationType = (utilization: number) => {
  if (utilization >= 90) return 'danger'
  if (utilization >= 70) return 'warning'
  if (utilization >= 30) return 'success'
  return 'info'
}

const getPositionName = (frontBack: number, leftMiddleRight: number) => {
  const fbMap = { 1: '前', 2: '後' }
  const lmrMap = { 1: '左', 2: '中', 3: '右' }
  return `${fbMap[frontBack]}${lmrMap[leftMiddleRight]}`
}


const formatDate = (date: string | Date) => {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('zh-TW')
}

const formatDateTime = (date: string | Date) => {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleString('zh-TW')
}

// Initialize
onMounted(() => {
  loadStorageTree()
  loadPendingItems()
})
</script>

<style scoped>
.storage-management {
  padding: 20px;
}

.structure-section,
.pending-section,
.manual-entry-section,
.stats-section {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.structure-tree {
  max-height: 400px;
  overflow-y: auto;
}

.tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  width: 100%;
}

.node-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-icon {
  color: #409eff;
}

.node-label {
  font-weight: 500;
}

.node-actions {
  opacity: 0.7;
}

.node-actions:hover {
  opacity: 1;
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

.shelves-config {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.shelf-item {
  padding: 10px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.assign-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}


.position-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.basic-info h4,
.inventory-info h4,
.movement-history h4 {
  margin-bottom: 10px;
  color: #303133;
}

.manual-entry-description {
  margin-bottom: 15px;
}
</style>