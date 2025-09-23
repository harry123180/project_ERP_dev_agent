<template>
  <div class="delivery-maintenance">
    <!-- 頁面標題 -->
    <div class="page-header">
      <h1 class="page-title">交期維護</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateConsolidation = true" :disabled="selectedPOs.length < 2">
          <el-icon><Plus /></el-icon>
          新增集運單
        </el-button>
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          重新整理
        </el-button>
      </div>
    </div>

    <!-- 統計卡片 -->
    <div class="stats-container">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">
                <div style="font-size: 14px; color: #909399; margin-bottom: 5px;">國內: {{ summary.domestic_shipped || 0 }}/{{ summary.domestic_total || 0 }}</div>
                <div style="font-size: 14px; color: #909399;">國外: {{ summary.international_shipped || 0 }}/{{ summary.international_total || 0 }}</div>
              </div>
              <div class="stat-label">已發貨總數</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card urgent">
            <div class="stat-content">
              <div class="stat-number">
                <div style="font-size: 14px; color: #909399; margin-bottom: 5px;">國內: {{ summary.domestic_unshipped || 0 }}</div>
                <div style="font-size: 14px; color: #909399;">國外: {{ summary.international_unshipped || 0 }}</div>
              </div>
              <div class="stat-label">未發貨總數</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card info">
            <div class="stat-content">
              <div class="stat-number">{{ consolidations.length || 0 }}</div>
              <div class="stat-label">集運單數量</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ summary.today_expected || 0 }}</div>
              <div class="stat-label">今日預計到貨</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- Tabs 分頁 -->
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <!-- 國內採購列表 Tab -->
      <el-tab-pane label="國內採購列表" name="domestic">
        <!-- 篩選條件 -->
        <div class="filters">
          <el-form :model="filters" inline>
            <el-form-item label="採購單號">
              <el-input 
                v-model="filters.poNumber" 
                placeholder="輸入採購單號"
                clearable
              />
            </el-form-item>
            <el-form-item label="交貨狀態">
              <el-select v-model="filters.deliveryStatus" placeholder="選擇狀態" clearable style="width: 200px">
                <el-option label="全部" value="" />
                <el-option label="已發貨" value="shipped" />
                <el-option label="已到貨" value="delivered" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadData">搜尋</el-button>
              <el-button @click="resetFilters">重設</el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 國內採購單列表 -->
        <div class="table-container">
          <el-table 
            :data="deliveryData" 
            :loading="loading"
            stripe
          >
            <el-table-column prop="po_number" label="採購單號" width="140" />
            <el-table-column prop="supplier_name" label="供應商" width="200" />
            <el-table-column label="交貨狀態" width="100">
              <template #default="{ row }">
                <el-tag :type="row.delivery_status === 'delivered' ? 'success' : 'warning'">
                  {{ row.delivery_status === 'delivered' ? '已到貨' : '未到貨' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="物流狀態" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.delivery_status)">
                  {{ getDomesticStatusLabel(row.delivery_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="expected_delivery_date" label="預計交貨日" width="120">
              <template #default="{ row }">
                {{ formatDate(row.expected_delivery_date) }}
              </template>
            </el-table-column>
            <el-table-column prop="remarks" label="備註/追蹤號" min-width="150" />
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button 
                  size="small" 
                  type="primary"
                  @click="updateStatus(row)"
                >
                  更新狀態
                </el-button>
                <el-button 
                  size="small"
                  @click="updateRemarks(row)"
                >
                  編輯備註
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分頁 -->
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :total="pagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="loadData"
            @current-change="loadData"
            style="margin-top: 20px"
          />
        </div>
      </el-tab-pane>

      <!-- 國外採購列表 Tab -->
      <el-tab-pane label="國外採購列表" name="international">
        <!-- 篩選條件 -->
        <div class="filters">
          <el-form :model="filtersInt" inline>
            <el-form-item label="採購單號">
              <el-input 
                v-model="filtersInt.poNumber" 
                placeholder="輸入採購單號"
                clearable
              />
            </el-form-item>
            <el-form-item label="交貨狀態">
              <el-select v-model="filtersInt.deliveryStatus" placeholder="選擇狀態" clearable style="width: 200px">
                <el-option label="全部" value="" />
                <el-option label="已發貨" value="shipped" />
                <el-option label="物流" value="in_transit" />
                <el-option label="對方海關" value="foreign_customs" />
                <el-option label="台灣海關" value="taiwan_customs" />
                <el-option label="已到貨" value="delivered" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadInternationalData">搜尋</el-button>
              <el-button @click="resetInternationalFilters">重設</el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 國外採購單列表 -->
        <div class="table-container">
          <el-table 
            :data="internationalData" 
            :loading="loadingInt"
            stripe
            @selection-change="handleSelectionChange"
          >
            <el-table-column 
              type="selection" 
              width="55"
              :selectable="canSelectForConsolidation"
            />
            <el-table-column prop="po_number" label="採購單號" width="140" />
            <el-table-column prop="supplier_name" label="供應商" width="180" />
            <el-table-column label="交貨狀態" width="100">
              <template #default="{ row }">
                <el-tag :type="row.delivery_status === 'delivered' ? 'success' : 'warning'">
                  {{ row.delivery_status === 'delivered' ? '已到貨' : '未到貨' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="物流狀態" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.delivery_status)">
                  {{ getStatusLabel(row.delivery_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="expected_delivery_date" label="預計交貨日" width="120">
              <template #default="{ row }">
                {{ formatDate(row.expected_delivery_date) }}
              </template>
            </el-table-column>
            <el-table-column prop="remarks" label="備註/追蹤號" min-width="150" />
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button 
                  size="small" 
                  type="primary"
                  @click="updateStatus(row)"
                >
                  更新狀態
                </el-button>
                <el-button 
                  size="small"
                  @click="updateRemarks(row)"
                >
                  編輯備註
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分頁 -->
          <el-pagination
            v-model:current-page="paginationInt.page"
            v-model:page-size="paginationInt.size"
            :total="paginationInt.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="loadInternationalData"
            @current-change="loadInternationalData"
            style="margin-top: 20px"
          />
        </div>

        <!-- 選擇提示 -->
        <div v-if="selectedPOs.length > 0" class="selection-info">
          已選擇 {{ selectedPOs.length }} 張採購單
          <el-button v-if="selectedPOs.length >= 2" type="primary" size="small" @click="showCreateConsolidation = true">
            建立集運單
          </el-button>
        </div>
      </el-tab-pane>

      <!-- 集運單列表 Tab -->
      <el-tab-pane label="集運單列表" name="consolidations">
        <div class="consolidation-list">
          <!-- 集運單卡片列表 -->
          <el-row :gutter="16">
            <el-col v-for="consol in consolidations" :key="consol.consolidation_id" :span="12">
              <el-card class="consolidation-card">
                <template #header>
                  <div class="card-header">
                    <span class="consol-title">{{ consol.consolidation_name || consol.consolidation_id }}</span>
                    <el-tag :type="getConsolStatusType(consol.logistics_status)">
                      {{ getConsolStatusLabel(consol.logistics_status) }}
                    </el-tag>
                  </div>
                </template>
                
                <div class="consol-info">
                  <el-row>
                    <el-col :span="12">
                      <div class="info-item">
                        <span class="label">採購單數量：</span>
                        <span class="value">{{ consol.po_count || consol.purchase_orders?.length || 0 }}</span>
                      </div>
                    </el-col>
                    <el-col :span="12">
                      <div class="info-item">
                        <span class="label">總物品數量：</span>
                        <span class="value">{{ calculateTotalItems(consol) }}</span>
                      </div>
                    </el-col>
                  </el-row>
                  
                  <div class="info-item" v-if="consol.carrier || consol.tracking_number">
                    <span class="label">物流廠商：</span>
                    <span class="value">{{ consol.carrier || '-' }}</span>
                  </div>
                  
                  <div class="info-item" v-if="consol.tracking_number">
                    <span class="label">物流號碼：</span>
                    <span class="value">{{ consol.tracking_number || '-' }}</span>
                  </div>
                  
                  <div class="info-item">
                    <span class="label">預計到貨：</span>
                    <span class="value">{{ formatDate(consol.expected_delivery_date) }}</span>
                  </div>
                  
                  <div class="info-item" v-if="consol.remarks">
                    <span class="label">備註：</span>
                    <span class="value">{{ consol.remarks }}</span>
                  </div>
                </div>
                
                <template #footer>
                  <div class="card-footer">
                    <el-button size="small" @click="viewConsolidation(consol)">查看詳情</el-button>
                    <el-button size="small" type="primary" @click="updateConsolStatus(consol)">更新狀態</el-button>
                  </div>
                </template>
              </el-card>
            </el-col>
          </el-row>
          
          <!-- 無資料提示 -->
          <el-empty v-if="consolidations.length === 0" description="暫無集運單" />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 更新狀態對話框 -->
    <el-dialog
      v-model="statusDialog.visible"
      title="更新交貨狀態"
      width="500px"
    >
      <el-form :model="statusDialog" label-width="100px">
        <el-form-item label="採購單號">
          <el-input :value="statusDialog.poNumber" readonly />
        </el-form-item>
        <el-form-item label="新狀態">
          <el-select v-model="statusDialog.newStatus" placeholder="選擇新狀態">
            <el-option v-if="statusDialog.region === 'domestic'" label="已發貨" value="shipped" />
            <el-option v-if="statusDialog.region === 'domestic'" label="已到貨" value="delivered" />
            <el-option v-if="statusDialog.region === 'international'" label="已發貨" value="shipped" />
            <el-option v-if="statusDialog.region === 'international'" label="物流" value="in_transit" />
            <el-option v-if="statusDialog.region === 'international'" label="對方海關" value="foreign_customs" />
            <el-option v-if="statusDialog.region === 'international'" label="台灣海關" value="taiwan_customs" />
            <el-option v-if="statusDialog.region === 'international'" label="已到貨" value="delivered" />
          </el-select>
        </el-form-item>
        <el-form-item label="預計到貨日">
          <el-date-picker
            v-model="statusDialog.expectedDeliveryDate"
            type="date"
            placeholder="選擇預計到貨日期"
            format="YYYY/MM/DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="備註">
          <el-input
            v-model="statusDialog.remarks"
            type="textarea"
            :rows="3"
            placeholder="輸入備註或追蹤號碼"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitStatusUpdate">確認更新</el-button>
      </template>
    </el-dialog>

    <!-- 編輯備註對話框 -->
    <el-dialog
      v-model="remarksDialog.visible"
      title="編輯備註"
      width="500px"
    >
      <el-form :model="remarksDialog" label-width="100px">
        <el-form-item label="採購單號">
          <el-input :value="remarksDialog.poNumber" readonly />
        </el-form-item>
        <el-form-item label="備註">
          <el-input
            v-model="remarksDialog.remarks"
            type="textarea"
            :rows="4"
            placeholder="輸入備註或追蹤號碼"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="remarksDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitRemarksUpdate">確認更新</el-button>
      </template>
    </el-dialog>

    <!-- 新增集運單對話框 -->
    <el-dialog
      v-model="showCreateConsolidation"
      title="新增集運單"
      width="600px"
    >
      <el-form label-width="100px">
        <el-form-item label="集運單名稱">
          <el-input v-model="newConsolidation.consolidation_name" placeholder="輸入集運單名稱（選填）" />
        </el-form-item>
        <el-form-item label="選擇採購單">
          <div class="selected-pos">
            <el-tag 
              v-for="po in selectedPOs" 
              :key="po.po_number"
              closable
              @close="removeFromSelection(po)"
              style="margin: 2px"
            >
              {{ po.po_number }} - {{ po.supplier_name }}
            </el-tag>
          </div>
          <div v-if="selectedPOs.length < 2" class="tip-text">
            請至少選擇2張國際已發貨採購單
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateConsolidation = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="createConsolidation"
          :disabled="selectedPOs.length < 2"
        >
          建立集運單
        </el-button>
      </template>
    </el-dialog>

    <!-- 更新集運單狀態對話框 -->
    <el-dialog
      v-model="consolStatusDialog.visible"
      title="更新集運單狀態"
      width="600px"
    >
      <el-form :model="consolStatusDialog" label-width="120px">
        <el-form-item label="集運單名稱">
          <el-input :value="consolStatusDialog.consolidationName" readonly />
        </el-form-item>
        <el-form-item label="物流狀態">
          <el-select v-model="consolStatusDialog.newStatus" placeholder="選擇新狀態">
            <el-option label="已發貨" value="shipped" />
            <el-option label="物流中" value="in_transit" />
            <el-option label="對方海關" value="foreign_customs" />
            <el-option label="台灣海關" value="taiwan_customs" />
            <el-option label="已到貨" value="delivered" />
          </el-select>
        </el-form-item>
        <el-form-item label="物流廠商">
          <el-input
            v-model="consolStatusDialog.carrier"
            placeholder="輸入物流廠商名稱"
          />
        </el-form-item>
        <el-form-item label="物流號碼">
          <el-input
            v-model="consolStatusDialog.trackingNumber"
            placeholder="輸入物流追蹤號碼"
          />
        </el-form-item>
        <el-form-item label="預計到貨日期">
          <el-date-picker
            v-model="consolStatusDialog.expectedDeliveryDate"
            type="date"
            placeholder="選擇預計到貨日期"
            format="YYYY/MM/DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="備註">
          <el-input
            v-model="consolStatusDialog.remarks"
            type="textarea"
            :rows="3"
            placeholder="輸入備註"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="consolStatusDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitConsolStatusUpdate">確認更新</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import * as deliveryApi from '@/api/delivery'

const router = useRouter()

// 定義類型
interface PurchaseOrder {
  po_number: string
  supplier_id: string
  supplier_name: string
  supplier_region: string
  delivery_status: string
  expected_delivery_date: string
  actual_delivery_date?: string
  remarks: string
  status_update_required: boolean
  consolidation_id?: string
  item_count: number
  can_create_consolidation: boolean
}

interface Consolidation {
  consolidation_id: string
  consolidation_name?: string
  po_count?: number
  purchase_orders?: Array<{
    po_number: string
    purchase_order_no: string
    supplier_name: string
    item_count: number
    items_count: number
  }>
  pos?: Array<{
    po_number: string
    supplier_name: string
    item_count: number
  }>
  total_items?: number
  logistics_status: string
  status?: string
  expected_delivery?: string
  expected_delivery_date?: string
  carrier?: string
  tracking_number?: string
  remarks?: string
}

// 響應式數據
const loading = ref(false)
const loadingInt = ref(false)
const activeTab = ref('domestic')
const deliveryData = ref<PurchaseOrder[]>([])
const internationalData = ref<PurchaseOrder[]>([])
const consolidations = ref<Consolidation[]>([])
const selectedPOs = ref<PurchaseOrder[]>([])
const showCreateConsolidation = ref(false)

// 國內篩選條件
const filters = reactive({
  poNumber: '',
  supplierRegion: 'domestic',
  deliveryStatus: ''
})

// 國外篩選條件
const filtersInt = reactive({
  poNumber: '',
  deliveryStatus: ''
})

// 國內分頁
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 國外分頁
const paginationInt = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 統計資料
const summary = reactive({
  domestic_total: 0,
  domestic_shipped: 0,
  domestic_unshipped: 0,
  international_total: 0,
  international_shipped: 0,
  international_unshipped: 0,
  today_expected: 0
})

// 狀態更新對話框
const statusDialog = reactive({
  visible: false,
  poNumber: '',
  currentStatus: '',
  newStatus: '',
  expectedDeliveryDate: '',
  remarks: '',
  region: 'domestic' // 'domestic' or 'international'
})

// 備註編輯對話框
const remarksDialog = reactive({
  visible: false,
  poNumber: '',
  remarks: ''
})

// 新集運單
const newConsolidation = reactive({
  consolidation_name: '',
  purchase_order_nos: [] as string[]
})

// 集運單狀態更新對話框
const consolStatusDialog = reactive({
  visible: false,
  consolidationId: '',
  consolidationName: '',
  currentStatus: '',
  newStatus: '',
  carrier: '',
  trackingNumber: '',
  expectedDeliveryDate: '',
  remarks: ''
})

// 判斷是否可選擇加入集運（只在國外採購列表可選）
const canSelectForConsolidation = (row: PurchaseOrder) => {
  return row.delivery_status === 'shipped' && 
         !row.consolidation_id
}

// 處理選擇變化
const handleSelectionChange = (selection: PurchaseOrder[]) => {
  selectedPOs.value = selection
}

// 從選擇中移除
const removeFromSelection = (po: PurchaseOrder) => {
  const index = selectedPOs.value.findIndex(p => p.po_number === po.po_number)
  if (index > -1) {
    selectedPOs.value.splice(index, 1)
  }
}

// 載入國內資料
const loadData = async () => {
  loading.value = true
  try {
    const response = await deliveryApi.getMaintenanceList({
      page: pagination.page,
      page_size: pagination.size,
      status: filters.deliveryStatus,
      supplier_region: 'domestic',
      po_number: filters.poNumber
    })
    
    if (response.success) {
      deliveryData.value = response.data
      pagination.total = response.data.length
      updateSummary()
    }
  } catch (error) {
    console.error('載入失敗:', error)
    ElMessage.error('載入資料失敗')
  } finally {
    loading.value = false
  }
}

// 載入國外資料
const loadInternationalData = async () => {
  loadingInt.value = true
  try {
    const response = await deliveryApi.getMaintenanceList({
      page: paginationInt.page,
      page_size: paginationInt.size,
      status: filtersInt.deliveryStatus,
      supplier_region: 'international',
      po_number: filtersInt.poNumber
    })
    
    if (response.success) {
      internationalData.value = response.data
      paginationInt.total = response.data.length
      updateSummary()
    }
  } catch (error) {
    console.error('載入失敗:', error)
    ElMessage.error('載入國外資料失敗')
  } finally {
    loadingInt.value = false
  }
}

// 更新統計資料
const updateSummary = () => {
  // 計算國內統計
  summary.domestic_total = deliveryData.value.length
  summary.domestic_shipped = deliveryData.value.filter(po => 
    po.delivery_status === 'shipped' || po.delivery_status === 'delivered'
  ).length
  summary.domestic_unshipped = deliveryData.value.filter(po => 
    po.delivery_status === 'not_shipped' || !po.delivery_status
  ).length
  
  // 計算國外統計
  summary.international_total = internationalData.value.length
  summary.international_shipped = internationalData.value.filter(po => 
    po.delivery_status !== 'not_shipped' && po.delivery_status && po.delivery_status !== 'delivered'
  ).length
  summary.international_unshipped = internationalData.value.filter(po => 
    po.delivery_status === 'not_shipped' || !po.delivery_status
  ).length
  
  // 計算今日預計到貨數量
  const today = new Date().toISOString().split('T')[0]
  const allPOs = [...deliveryData.value, ...internationalData.value]
  summary.today_expected = allPOs.filter(po => {
    if (!po.expected_delivery_date) return false
    const expectedDate = new Date(po.expected_delivery_date).toISOString().split('T')[0]
    // Count items expected today that haven't been delivered yet
    // (includes shipped items that are in transit)
    return expectedDate === today && po.delivery_status !== 'delivered'
  }).length
}

// 載入集運單列表
const loadConsolidations = async () => {
  try {
    const response = await deliveryApi.getConsolidationList()
    if (response.success) {
      consolidations.value = response.data
    }
  } catch (error) {
    console.error('載入集運單失敗:', error)
    ElMessage.error('載入集運單失敗')
  }
}

// 更新狀態
const updateStatus = (row: PurchaseOrder) => {
  statusDialog.poNumber = row.po_number
  statusDialog.currentStatus = row.delivery_status
  statusDialog.newStatus = row.delivery_status
  statusDialog.expectedDeliveryDate = row.expected_delivery_date || ''
  statusDialog.remarks = row.remarks
  statusDialog.region = activeTab.value === 'domestic' ? 'domestic' : 'international'
  statusDialog.visible = true
}

// 提交狀態更新
const submitStatusUpdate = async () => {
  try {
    await deliveryApi.updateDeliveryStatus(statusDialog.poNumber, {
      new_status: statusDialog.newStatus,
      expected_date: statusDialog.expectedDeliveryDate,
      remarks: statusDialog.remarks
    })
    
    ElMessage.success('狀態更新成功')
    statusDialog.visible = false
    await loadAllData()
  } catch (error) {
    ElMessage.error('狀態更新失敗')
    console.error(error)
  }
}

// 編輯備註
const updateRemarks = (row: PurchaseOrder) => {
  remarksDialog.poNumber = row.po_number
  remarksDialog.remarks = row.remarks
  remarksDialog.visible = true
}

// 提交備註更新
const submitRemarksUpdate = async () => {
  try {
    await deliveryApi.updateRemarks(remarksDialog.poNumber, {
      remarks: remarksDialog.remarks
    })
    
    ElMessage.success('備註更新成功')
    remarksDialog.visible = false
    await loadData()
  } catch (error) {
    ElMessage.error('備註更新失敗')
    console.error(error)
  }
}

// 建立集運單
const createConsolidation = async () => {
  if (selectedPOs.value.length < 2) {
    ElMessage.warning('請至少選擇2張採購單')
    return
  }
  
  try {
    const purchase_order_nos = selectedPOs.value.map(po => po.po_number)
    await deliveryApi.createConsolidation({
      consolidation_name: newConsolidation.consolidation_name,
      purchase_order_nos
    })
    
    ElMessage.success('集運單建立成功')
    showCreateConsolidation.value = false
    selectedPOs.value = []
    newConsolidation.consolidation_name = ''
    
    await loadData()
    await loadConsolidations()
  } catch (error) {
    ElMessage.error('建立集運單失敗')
    console.error(error)
  }
}

// 查看集運單詳情
const viewConsolidation = (consol: Consolidation) => {
  router.push(`/purchase-orders/consolidation/${consol.consolidation_id}`)
}

// 更新集運單狀態
// 計算集運單總物品數量
const calculateTotalItems = (consol: Consolidation) => {
  if (consol.purchase_orders) {
    return consol.purchase_orders.reduce((total, po) => {
      return total + (po.items_count || po.item_count || 0)
    }, 0)
  }
  return consol.total_items || 0
}

const updateConsolStatus = (consol: Consolidation) => {
  consolStatusDialog.consolidationId = consol.consolidation_id
  consolStatusDialog.consolidationName = consol.consolidation_name || consol.consolidation_id
  consolStatusDialog.currentStatus = consol.logistics_status || consol.status || ''
  consolStatusDialog.newStatus = ''
  consolStatusDialog.carrier = consol.carrier || ''
  consolStatusDialog.trackingNumber = consol.tracking_number || ''
  consolStatusDialog.expectedDeliveryDate = consol.expected_delivery_date || ''
  consolStatusDialog.remarks = consol.remarks || ''
  consolStatusDialog.visible = true
}

const submitConsolStatusUpdate = async () => {
  try {
    await deliveryApi.updateConsolidationStatus(consolStatusDialog.consolidationId, {
      new_status: consolStatusDialog.newStatus,
      carrier: consolStatusDialog.carrier,
      tracking_number: consolStatusDialog.trackingNumber,
      expected_date: consolStatusDialog.expectedDeliveryDate,
      remarks: consolStatusDialog.remarks
    })
    
    ElMessage.success('集運單狀態更新成功')
    consolStatusDialog.visible = false
    loadConsolidations()
  } catch (error) {
    console.error('更新集運單狀態失敗:', error)
    ElMessage.error('更新集運單狀態失敗')
  }
}

// Tab 切換
const handleTabChange = (name: string) => {
  selectedPOs.value = [] // 清空選擇
  if (name === 'domestic') {
    loadData()
  } else if (name === 'international') {
    loadInternationalData()
  } else if (name === 'consolidations') {
    loadConsolidations()
  }
}

// 重設國內篩選
const resetFilters = () => {
  filters.poNumber = ''
  filters.deliveryStatus = ''
  loadData()
}

// 重設國外篩選
const resetInternationalFilters = () => {
  filtersInt.poNumber = ''
  filtersInt.deliveryStatus = ''
  loadInternationalData()
}

// 重新整理
const refreshData = async () => {
  await loadAllData()
}

// 格式化日期
const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-TW')
}

// 取得狀態標籤（國外）
const getStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    'not_shipped': '未發貨',
    'shipped': '已發貨',
    'foreign_customs': '對方海關',
    'taiwan_customs': '台灣海關',
    'in_transit': '物流',
    'delivered': '已到貨'
  }
  return statusMap[status] || status
}

// 取得狀態標籤（國內）
const getDomesticStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    'not_shipped': '未發貨',
    'shipped': '已發貨',
    'in_transit': '物流',
    'delivered': '已到貨'
  }
  return statusMap[status] || status
}

// 取得狀態類型
const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'not_shipped': 'info',
    'shipped': '',
    'foreign_customs': 'danger',
    'taiwan_customs': 'danger',
    'in_transit': 'warning',
    'delivered': 'success'
  }
  return typeMap[status] || 'info'
}

// 取得集運單狀態標籤
const getConsolStatusLabel = (status: string) => {
  return getStatusLabel(status)
}

// 取得集運單狀態類型
const getConsolStatusType = (status: string) => {
  return getStatusType(status)
}

// 初始化載入所有資料
const loadAllData = async () => {
  await Promise.all([
    loadData(),
    loadInternationalData(),
    loadConsolidations()
  ])
  // Update summary after all data is loaded
  updateSummary()
}

// 初始化
onMounted(() => {
  // Check if there's a tab query parameter
  const urlParams = new URLSearchParams(window.location.search)
  const tabParam = urlParams.get('tab')
  if (tabParam === 'consolidation') {
    activeTab.value = 'consolidations'
  }
  
  loadAllData()
})
</script>

<style scoped>
.delivery-maintenance {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.stats-container {
  margin-bottom: 20px;
}

.stat-card {
  height: 100px;
}

.stat-card.urgent {
  border-left: 4px solid #f56c6c;
}

.stat-card.info {
  border-left: 4px solid #409eff;
}

.stat-content {
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.filters {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.table-container {
  background: white;
  padding: 16px;
  border-radius: 4px;
}

.selection-info {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: white;
  padding: 12px 20px;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 100;
}

.consolidation-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.consol-title {
  font-weight: bold;
  font-size: 16px;
}

.consol-info {
  .info-item {
    margin-bottom: 12px;
    
    .label {
      color: #909399;
      margin-right: 8px;
    }
    
    .value {
      color: #303133;
      font-weight: 500;
    }
  }
}

.po-list {
  margin-top: 12px;
  
  .label {
    color: #909399;
    margin-bottom: 8px;
    display: block;
  }
}

.card-footer {
  display: flex;
  gap: 8px;
}

.selected-pos {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 8px;
  min-height: 60px;
  background: #f5f7fa;
}

.tip-text {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 8px;
}
</style>