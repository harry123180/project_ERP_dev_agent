<template>
  <div class="consolidation-management">
    <!-- 頁面標題 -->
    <div class="page-header">
      <h1>集運單管理</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        新建集運單
      </el-button>
    </div>

    <!-- 統計卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="總集運單數" :value="consolidationList.length" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="運送中" :value="inTransitCount" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="已到貨" :value="deliveredCount" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="可加入集運" :value="eligiblePOs.length" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 集運單列表 -->
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <span>集運單列表</span>
          <el-button text @click="loadConsolidations">
            <el-icon><Refresh /></el-icon>
            重新整理
          </el-button>
        </div>
      </template>

      <el-table :data="consolidationList" stripe style="width: 100%">
        <el-table-column type="expand">
          <template #default="props">
            <div class="expand-content">
              <h4>包含採購單：</h4>
              <el-table :data="props.row.purchase_orders" size="small">
                <el-table-column prop="po_number" label="採購單號" width="150" />
                <el-table-column prop="supplier_name" label="供應商" />
                <el-table-column prop="item_count" label="項目數" width="80" />
                <el-table-column prop="total_amount" label="金額" width="120">
                  <template #default="scope">
                    {{ formatCurrency(scope.row.total_amount) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100">
                  <template #default="scope">
                    <el-button 
                      type="danger" 
                      size="small" 
                      text
                      @click="removePOFromConsolidation(props.row.id, scope.row.po_number)"
                    >
                      移除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="consolidation_no" label="集運單號" width="150" />
        <el-table-column prop="name" label="集運單名稱" />
        <el-table-column label="採購單數" width="100">
          <template #default="scope">
            {{ scope.row.purchase_orders?.length || 0 }}
          </template>
        </el-table-column>
        
        <el-table-column prop="logistics_status" label="物流狀態" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.logistics_status)">
              {{ getStatusText(scope.row.logistics_status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="expected_delivery" label="預計到貨" width="150">
          <template #default="scope">
            {{ formatDate(scope.row.expected_delivery) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="tracking_number" label="追蹤號碼" />
        
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="scope">
            <el-button size="small" @click="updateStatus(scope.row)">
              更新狀態
            </el-button>
            <el-button size="small" @click="addPOsToConsolidation(scope.row)">
              加入採購單
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建集運單對話框 -->
    <el-dialog 
      v-model="showCreateDialog" 
      title="新建集運單"
      width="800px"
    >
      <el-form :model="newConsolidation" label-width="100px">
        <el-form-item label="集運單名稱" required>
          <el-input 
            v-model="newConsolidation.name" 
            placeholder="輸入集運單名稱（選填，系統會自動生成）"
          />
        </el-form-item>
        
        <el-form-item label="預計到貨日">
          <el-date-picker
            v-model="newConsolidation.expected_delivery"
            type="date"
            placeholder="選擇預計到貨日期"
          />
        </el-form-item>

        <el-form-item label="選擇採購單" required>
          <div class="po-selection">
            <el-alert type="info" :closable="false" style="margin-bottom: 10px">
              請選擇至少2張國際已發貨的採購單
            </el-alert>
            
            <el-table 
              ref="poTable"
              :data="eligiblePOs" 
              @selection-change="handleSelectionChange"
              max-height="300"
            >
              <el-table-column type="selection" width="55" />
              <el-table-column prop="po_number" label="採購單號" width="120" />
              <el-table-column prop="supplier_name" label="供應商" />
              <el-table-column prop="expected_delivery_date" label="預計到貨" width="120">
                <template #default="scope">
                  {{ formatDate(scope.row.expected_delivery_date) }}
                </template>
              </el-table-column>
              <el-table-column prop="remarks" label="追蹤號碼" />
            </el-table>
            
            <div class="selection-summary">
              已選擇: {{ selectedPOs.length }} 張採購單
            </div>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="createConsolidation"
          :disabled="selectedPOs.length < 2"
        >
          建立集運單
        </el-button>
      </template>
    </el-dialog>

    <!-- 更新狀態對話框 -->
    <el-dialog 
      v-model="showStatusDialog" 
      title="更新集運單狀態"
      width="600px"
    >
      <el-form :model="statusUpdate" label-width="120px">
        <el-form-item label="當前狀態">
          <el-tag :type="getStatusType(currentConsolidation?.logistics_status)">
            {{ getStatusText(currentConsolidation?.logistics_status) }}
          </el-tag>
        </el-form-item>
        
        <el-form-item label="新狀態" required>
          <el-select v-model="statusUpdate.status" placeholder="選擇新狀態">
            <el-option label="已發貨" value="shipped" />
            <el-option label="對方海關" value="foreign_customs" />
            <el-option label="台灣海關" value="taiwan_customs" />
            <el-option label="物流中" value="in_transit" />
            <el-option label="已到貨" value="delivered" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="承運商">
          <el-input v-model="statusUpdate.carrier" placeholder="例如: DHL, FedEx" />
        </el-form-item>
        
        <el-form-item label="追蹤號碼">
          <el-input v-model="statusUpdate.tracking_number" placeholder="輸入物流追蹤號碼" />
        </el-form-item>
        
        <el-form-item label="海關申報號">
          <el-input v-model="statusUpdate.customs_declaration_no" placeholder="輸入海關申報號碼" />
        </el-form-item>
        
        <el-form-item label="備註">
          <el-input 
            v-model="statusUpdate.remarks" 
            type="textarea" 
            rows="3"
            placeholder="輸入備註資訊"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showStatusDialog = false">取消</el-button>
        <el-button type="primary" @click="saveStatusUpdate">確認更新</el-button>
      </template>
    </el-dialog>

    <!-- 加入採購單對話框 -->
    <el-dialog 
      v-model="showAddPODialog" 
      title="加入採購單到集運單"
      width="700px"
    >
      <el-alert type="warning" :closable="false" style="margin-bottom: 15px">
        選擇要加入到集運單「{{ currentConsolidation?.name }}」的採購單
      </el-alert>
      
      <el-table 
        ref="addPOTable"
        :data="eligiblePOs" 
        @selection-change="handleAddPOSelection"
        max-height="400"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="po_number" label="採購單號" width="120" />
        <el-table-column prop="supplier_name" label="供應商" />
        <el-table-column prop="remarks" label="追蹤號碼" />
      </el-table>
      
      <template #footer>
        <el-button @click="showAddPODialog = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="confirmAddPOs"
          :disabled="selectedAddPOs.length === 0"
        >
          確認加入 ({{ selectedAddPOs.length }})
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { deliveryAPI } from '@/api/delivery'
import type { PurchaseOrder, ShipmentConsolidation } from '@/api/delivery'

// 響應式數據
const consolidationList = ref<ShipmentConsolidation[]>([])
const eligiblePOs = ref<PurchaseOrder[]>([])
const selectedPOs = ref<PurchaseOrder[]>([])
const selectedAddPOs = ref<PurchaseOrder[]>([])
const currentConsolidation = ref<ShipmentConsolidation | null>(null)

// 對話框控制
const showCreateDialog = ref(false)
const showStatusDialog = ref(false)
const showAddPODialog = ref(false)

// 表單數據
const newConsolidation = ref({
  name: '',
  expected_delivery: null,
  po_numbers: [] as string[]
})

const statusUpdate = ref({
  status: '',
  carrier: '',
  tracking_number: '',
  customs_declaration_no: '',
  remarks: ''
})

// 計算屬性
const inTransitCount = computed(() => 
  consolidationList.value.filter(c => c.logistics_status === 'in_transit').length
)

const deliveredCount = computed(() => 
  consolidationList.value.filter(c => c.logistics_status === 'delivered').length
)

// 載入資料
const loadConsolidations = async () => {
  try {
    const response = await deliveryAPI.getConsolidationList()
    consolidationList.value = response.data
  } catch (error) {
    ElMessage.error('載入集運單列表失敗')
    console.error(error)
  }
}

const loadEligiblePOs = async () => {
  try {
    const response = await deliveryAPI.getMaintenanceList()
    // 篩選可加入集運的採購單（國際已發貨且未加入集運）
    eligiblePOs.value = response.data.filter((po: PurchaseOrder) => 
      po.supplier_region === 'international' && 
      po.delivery_status === 'shipped' && 
      !po.consolidation_id
    )
  } catch (error) {
    ElMessage.error('載入可用採購單失敗')
    console.error(error)
  }
}

// 創建集運單
const handleSelectionChange = (selection: PurchaseOrder[]) => {
  selectedPOs.value = selection
}

const createConsolidation = async () => {
  if (selectedPOs.value.length < 2) {
    ElMessage.warning('請至少選擇2張採購單')
    return
  }

  try {
    const data = {
      name: newConsolidation.value.name || `集運單-${new Date().toLocaleDateString('zh-TW')}`,
      po_numbers: selectedPOs.value.map(po => po.po_number),
      expected_delivery: newConsolidation.value.expected_delivery
    }
    
    await deliveryAPI.createConsolidation(data)
    ElMessage.success('集運單建立成功')
    
    showCreateDialog.value = false
    newConsolidation.value = { name: '', expected_delivery: null, po_numbers: [] }
    selectedPOs.value = []
    
    await loadConsolidations()
    await loadEligiblePOs()
  } catch (error) {
    ElMessage.error('建立集運單失敗')
    console.error(error)
  }
}

// 更新狀態
const updateStatus = (consolidation: ShipmentConsolidation) => {
  currentConsolidation.value = consolidation
  statusUpdate.value = {
    status: consolidation.logistics_status || 'shipped',
    carrier: consolidation.carrier || '',
    tracking_number: consolidation.tracking_number || '',
    customs_declaration_no: consolidation.customs_declaration_no || '',
    remarks: consolidation.remarks || ''
  }
  showStatusDialog.value = true
}

const saveStatusUpdate = async () => {
  if (!currentConsolidation.value) return
  
  try {
    await deliveryAPI.updateConsolidationStatus(
      currentConsolidation.value.id, 
      statusUpdate.value
    )
    ElMessage.success('狀態更新成功')
    showStatusDialog.value = false
    await loadConsolidations()
  } catch (error) {
    ElMessage.error('狀態更新失敗')
    console.error(error)
  }
}

// 加入採購單到集運單
const addPOsToConsolidation = (consolidation: ShipmentConsolidation) => {
  currentConsolidation.value = consolidation
  showAddPODialog.value = true
}

const handleAddPOSelection = (selection: PurchaseOrder[]) => {
  selectedAddPOs.value = selection
}

const confirmAddPOs = async () => {
  if (!currentConsolidation.value || selectedAddPOs.value.length === 0) return
  
  try {
    await deliveryAPI.addPOsToConsolidation(
      currentConsolidation.value.id,
      selectedAddPOs.value.map(po => po.po_number)
    )
    ElMessage.success('採購單加入成功')
    showAddPODialog.value = false
    selectedAddPOs.value = []
    await loadConsolidations()
    await loadEligiblePOs()
  } catch (error) {
    ElMessage.error('加入採購單失敗')
    console.error(error)
  }
}

// 移除採購單
const removePOFromConsolidation = async (consolidationId: string, poNumber: string) => {
  try {
    await ElMessageBox.confirm(
      `確定要從集運單中移除採購單 ${poNumber} 嗎？`,
      '確認移除',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await deliveryAPI.removePOFromConsolidation(consolidationId, poNumber)
    ElMessage.success('採購單已移除')
    await loadConsolidations()
    await loadEligiblePOs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除失敗')
      console.error(error)
    }
  }
}

// 輔助函數
const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'shipped': 'info',
    'foreign_customs': 'warning',
    'taiwan_customs': 'warning',
    'in_transit': '',
    'delivered': 'success'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    'shipped': '已發貨',
    'foreign_customs': '對方海關',
    'taiwan_customs': '台灣海關',
    'in_transit': '物流中',
    'delivered': '已到貨'
  }
  return textMap[status] || status
}

const formatDate = (date: string | null) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-TW')
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: 'TWD',
    minimumFractionDigits: 0
  }).format(amount)
}

// 初始化
onMounted(() => {
  loadConsolidations()
  loadEligiblePOs()
})
</script>

<style scoped>
.consolidation-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 500;
  margin: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.list-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.expand-content {
  padding: 20px;
}

.expand-content h4 {
  margin-bottom: 15px;
  color: #606266;
}

.po-selection {
  width: 100%;
}

.selection-summary {
  margin-top: 10px;
  text-align: right;
  color: #909399;
  font-size: 14px;
}
</style>