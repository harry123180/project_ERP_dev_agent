<template>
  <div class="consolidation-detail">
    <!-- 頁面標題 -->
    <div class="page-header">
      <el-page-header @back="handleBack">
        <template #content>
          <div class="header-content">
            <h2>集運單詳情</h2>
            <el-tag :type="getStatusType(consolidation.logistics_status)" size="large">
              {{ getStatusLabel(consolidation.logistics_status) }}
            </el-tag>
          </div>
        </template>
        <template #breadcrumb>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首頁</el-breadcrumb-item>
            <el-breadcrumb-item :to="{ path: '/purchase-orders' }">採購管理</el-breadcrumb-item>
            <el-breadcrumb-item :to="{ path: '/purchase-orders/delivery' }">交期維護</el-breadcrumb-item>
            <el-breadcrumb-item>集運單詳情</el-breadcrumb-item>
          </el-breadcrumb>
        </template>
      </el-page-header>
    </div>

    <!-- 載入中 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <!-- 主要內容 -->
    <div v-else class="detail-content">
      <!-- 基本信息卡片 -->
      <el-card class="info-card">
        <template #header>
          <h3>集運單信息</h3>
        </template>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="集運單號">
            {{ consolidation.consolidation_id }}
          </el-descriptions-item>
          <el-descriptions-item label="集運單名稱">
            {{ consolidation.consolidation_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="物流狀態">
            <el-tag :type="getStatusType(consolidation.logistics_status)">
              {{ getStatusLabel(consolidation.logistics_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="物流廠商">
            {{ consolidation.carrier || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="物流號碼">
            {{ consolidation.tracking_number || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="預計到貨日">
            {{ formatDate(consolidation.expected_delivery_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="實際到貨日">
            {{ formatDate(consolidation.actual_delivery_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="採購單數量">
            {{ consolidation.pos_count || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="總物品數量">
            {{ calculateTotalItems() }}
          </el-descriptions-item>
          <el-descriptions-item label="備註" :span="3">
            <div class="remarks-section">
              <template v-if="!editingRemarks">
                <span>{{ consolidation.remarks || '-' }}</span>
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="startEditRemarks"
                  style="margin-left: 10px"
                >
                  編輯
                </el-button>
              </template>
              <template v-else>
                <el-input
                  v-model="tempRemarks"
                  type="textarea"
                  :rows="2"
                  style="width: 100%"
                />
                <div style="margin-top: 10px">
                  <el-button size="small" @click="cancelEditRemarks">取消</el-button>
                  <el-button size="small" type="primary" @click="saveRemarks">保存</el-button>
                </div>
              </template>
            </div>
          </el-descriptions-item>
        </el-descriptions>
        <div class="action-buttons">
          <el-button type="primary" @click="updateStatus">更新狀態</el-button>
        </div>
      </el-card>

      <!-- 採購單列表 -->
      <el-card class="po-list-card">
        <template #header>
          <h3>包含的採購單</h3>
        </template>
        <el-table :data="consolidation.pos_in_consolidation" stripe>
          <el-table-column prop="purchase_order_no" label="採購單號" width="150" />
          <el-table-column prop="supplier_name" label="供應商" width="200" />
          <el-table-column label="交貨狀態" width="100">
            <template #default>
              <el-tag type="info">
                {{ consolidation.logistics_status === 'delivered' ? '已到貨' : '未到貨' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="物流狀態" width="120">
            <template #default>
              <el-tag :type="getStatusType(consolidation.logistics_status)">
                {{ getStatusLabel(consolidation.logistics_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="預計交貨日">
            <template #default>
              {{ formatDate(consolidation.expected_delivery_date) }}
            </template>
          </el-table-column>
          <el-table-column label="備註/追蹤號">
            <template #default>
              <span v-if="consolidation.tracking_number">
                {{ consolidation.tracking_number }}
              </span>
              <span v-else-if="consolidation.remarks">
                {{ consolidation.remarks }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button
                type="primary"
                link
                size="small"
                @click="viewPODetail(row.purchase_order_no)"
              >
                查看詳情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 更新狀態對話框 -->
    <el-dialog
      v-model="statusDialog.visible"
      title="更新集運單狀態"
      width="600px"
    >
      <el-form :model="statusDialog" label-width="120px">
        <el-form-item label="物流狀態">
          <el-select v-model="statusDialog.newStatus" placeholder="選擇新狀態">
            <el-option label="已發貨" value="shipped" />
            <el-option label="物流中" value="in_transit" />
            <el-option label="對方海關" value="foreign_customs" />
            <el-option label="台灣海關" value="taiwan_customs" />
            <el-option label="已到貨" value="delivered" />
          </el-select>
        </el-form-item>
        <el-form-item label="物流廠商">
          <el-input v-model="statusDialog.carrier" placeholder="輸入物流廠商名稱" />
        </el-form-item>
        <el-form-item label="物流號碼">
          <el-input v-model="statusDialog.trackingNumber" placeholder="輸入物流追蹤號碼" />
        </el-form-item>
        <el-form-item label="預計到貨日期">
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
            placeholder="輸入備註"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitStatusUpdate">確認更新</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as deliveryApi from '@/api/delivery'

const route = useRoute()
const router = useRouter()

// 響應式數據
const loading = ref(false)
const consolidation = ref<any>({})
const editingRemarks = ref(false)
const tempRemarks = ref('')

// 狀態更新對話框
const statusDialog = reactive({
  visible: false,
  newStatus: '',
  carrier: '',
  trackingNumber: '',
  expectedDeliveryDate: '',
  remarks: ''
})

// 獲取集運單詳情
const getConsolidationDetail = async () => {
  loading.value = true
  try {
    const consolidationId = route.params.id as string
    // 獲取集運單列表並找到對應的集運單
    const response = await deliveryApi.getConsolidationList()
    if (response.success && response.data) {
      const found = response.data.find((c: any) => c.consolidation_id === consolidationId)
      if (found) {
        consolidation.value = found
      } else {
        ElMessage.error('集運單不存在')
        router.push('/purchase-orders/delivery')
      }
    }
  } catch (error) {
    console.error('載入集運單詳情失敗:', error)
    ElMessage.error('載入集運單詳情失敗')
  } finally {
    loading.value = false
  }
}

// 計算總物品數量
const calculateTotalItems = () => {
  if (consolidation.value.pos_in_consolidation) {
    return consolidation.value.pos_in_consolidation.reduce((total: number, po: any) => {
      return total + (po.items_count || po.item_count || 0)
    }, 0)
  }
  return 0
}

// 格式化日期
const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-TW')
}

// 獲取狀態類型
const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    'shipped': 'info',
    'in_transit': 'warning',
    'foreign_customs': 'warning',
    'taiwan_customs': 'warning',
    'delivered': 'success'
  }
  return statusMap[status] || 'info'
}

// 獲取狀態標籤
const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    'shipped': '已發貨',
    'in_transit': '物流中',
    'foreign_customs': '對方海關',
    'taiwan_customs': '台灣海關',
    'delivered': '已到貨'
  }
  return labelMap[status] || status
}

// 開始編輯備註
const startEditRemarks = () => {
  tempRemarks.value = consolidation.value.remarks || ''
  editingRemarks.value = true
}

// 取消編輯備註
const cancelEditRemarks = () => {
  editingRemarks.value = false
  tempRemarks.value = ''
}

// 保存備註
const saveRemarks = async () => {
  try {
    await deliveryApi.updateConsolidationStatus(consolidation.value.consolidation_id, {
      new_status: consolidation.value.logistics_status,
      remarks: tempRemarks.value
    })
    consolidation.value.remarks = tempRemarks.value
    editingRemarks.value = false
    ElMessage.success('備註更新成功')
  } catch (error) {
    console.error('更新備註失敗:', error)
    ElMessage.error('更新備註失敗')
  }
}

// 更新狀態
const updateStatus = () => {
  statusDialog.newStatus = consolidation.value.logistics_status || ''
  statusDialog.carrier = consolidation.value.carrier || ''
  statusDialog.trackingNumber = consolidation.value.tracking_number || ''
  statusDialog.expectedDeliveryDate = consolidation.value.expected_delivery_date || ''
  statusDialog.remarks = consolidation.value.remarks || ''
  statusDialog.visible = true
}

// 提交狀態更新
const submitStatusUpdate = async () => {
  try {
    await deliveryApi.updateConsolidationStatus(consolidation.value.consolidation_id, {
      new_status: statusDialog.newStatus,
      carrier: statusDialog.carrier,
      tracking_number: statusDialog.trackingNumber,
      expected_date: statusDialog.expectedDeliveryDate,
      remarks: statusDialog.remarks
    })
    
    ElMessage.success('狀態更新成功')
    statusDialog.visible = false
    await getConsolidationDetail()
  } catch (error) {
    console.error('更新狀態失敗:', error)
    ElMessage.error('更新狀態失敗')
  }
}

// 查看採購單詳情
const viewPODetail = (poNumber: string) => {
  router.push(`/purchase-orders/${poNumber}`)
}

// 返回到交期維護的集運單列表
const handleBack = () => {
  router.push('/purchase-orders/delivery?tab=consolidation')
}

onMounted(() => {
  getConsolidationDetail()
})
</script>

<style scoped>
.consolidation-detail {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.loading-container {
  background: white;
  padding: 24px;
  border-radius: 6px;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card,
.po-list-card {
  background: white;
}

.info-card :deep(.el-card__header),
.po-list-card :deep(.el-card__header) {
  background: #f5f7fa;
  padding: 16px 20px;
}

.info-card h3,
.po-list-card h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.action-buttons {
  margin-top: 20px;
  text-align: right;
}

.remarks-section {
  display: flex;
  align-items: flex-start;
  width: 100%;
}

:deep(.el-descriptions__label) {
  font-weight: 600;
  color: #606266;
}

:deep(.el-descriptions__content) {
  color: #303133;
}
</style>