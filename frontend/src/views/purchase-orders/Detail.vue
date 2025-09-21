<template>
  <div class="purchase-order-detail">
    <div class="page-header">
      <h1 class="page-title">採購單詳情</h1>
      <div class="actions">
        <el-button @click="goBack">返回</el-button>
        <el-button 
          type="primary" 
          @click="editPO"
          v-if="canEdit"
        >
          編輯
        </el-button>
      </div>
    </div>

    <div class="detail-container" v-loading="loading">
      <el-card class="info-card">
        <template #header>
          <h3>基本資訊</h3>
        </template>
        
        <el-descriptions :column="2" border>
          <el-descriptions-item label="採購單號">
            {{ purchaseOrder.po_number }}
          </el-descriptions-item>
          <el-descriptions-item label="供應商">
            {{ purchaseOrder.supplier_name }}
          </el-descriptions-item>
          <el-descriptions-item label="狀態">
            <el-tag :type="getStatusType(purchaseOrder.status)">
              {{ getStatusText(purchaseOrder.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="建立時間">
            {{ formatDate(purchaseOrder.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="建立人">
            {{ purchaseOrder.created_by }}
          </el-descriptions-item>
          <el-descriptions-item label="總金額">
            <span class="amount">{{ formatCurrency(purchaseOrder.total_amount) }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <div class="notes" v-if="purchaseOrder.notes">
          <h4>備註</h4>
          <p>{{ purchaseOrder.notes }}</p>
        </div>
      </el-card>

      <el-card class="items-card">
        <template #header>
          <h3>採購項目</h3>
        </template>
        
        <el-table :data="purchaseOrder.items" stripe>
          <el-table-column prop="item_name" label="項目名稱" width="200" />
          <el-table-column prop="spec" label="規格" width="150" />
          <el-table-column prop="quantity" label="數量" width="100" align="center" />
          <el-table-column prop="unit_price" label="單價" width="120" align="right">
            <template #default="{ row }">
              {{ formatCurrency(row.unit_price) }}
            </template>
          </el-table-column>
          <el-table-column prop="subtotal" label="小計" width="120" align="right">
            <template #default="{ row }">
              {{ formatCurrency(row.subtotal) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="狀態" width="100">
            <template #default="{ row }">
              <el-tag :type="getItemStatusType(row.status)" size="small">
                {{ getItemStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="請購資訊" min-width="150">
            <template #default="{ row }">
              <div v-if="row.request_info">
                <div>請購單：{{ row.request_info.request_number || 'N/A' }}</div>
                <div>請購人：{{ row.request_info.requester || 'N/A' }}</div>
              </div>
              <div v-else>
                <div class="text-gray-400">無請購資訊</div>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card class="summary-card">
        <template #header>
          <h3>金額統計</h3>
        </template>
        
        <div class="summary">
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="summary-item">
                <label>項目小計：</label>
                <span>{{ formatCurrency(purchaseOrder.subtotal) }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="summary-item">
                <label>稅額 (5%)：</label>
                <span>{{ formatCurrency(purchaseOrder.tax_amount) }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="summary-item">
                <label>總金額：</label>
                <span class="total">{{ formatCurrency(purchaseOrder.total_amount) }}</span>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-card>

      <el-card class="history-card" v-if="purchaseOrder.status_history?.length">
        <template #header>
          <h3>狀態變更歷史</h3>
        </template>
        
        <el-timeline>
          <el-timeline-item
            v-for="(history, index) in purchaseOrder.status_history"
            :key="index"
            :timestamp="formatDate(history.timestamp)"
          >
            <div class="history-item">
              <div class="status-change">
                狀態變更為：
                <el-tag :type="getStatusType(history.status)" size="small">
                  {{ getStatusText(history.status) }}
                </el-tag>
              </div>
              <div class="operator">操作人：{{ history.operator }}</div>
              <div class="remarks" v-if="history.remarks">備註：{{ history.remarks }}</div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { formatDate, formatCurrency } from '@/utils/format'
import { procurementApi } from '@/api/procurement'

const route = useRoute()
const router = useRouter()

// Reactive data
const loading = ref(false)
const purchaseOrder = ref({
  po_number: '',
  supplier_name: '',
  status: '',
  created_at: '',
  created_by: '',
  total_amount: 0,
  subtotal: 0,
  tax_amount: 0,
  notes: '',
  items: [],
  status_history: []
})

// Computed
const canEdit = computed(() => {
  return ['order_created'].includes(purchaseOrder.value.status)
})

// Methods
const loadPODetail = async () => {
  loading.value = true
  try {
    const id = route.params.id as string
    const response = await procurementApi.getPurchaseOrder(id)
    
    // Map the API response to the component format
    purchaseOrder.value = {
      po_number: response.purchase_order_no,
      supplier_name: response.supplier_name,
      status: response.purchase_status || 'pending',
      created_at: response.created_at,
      created_by: '採購員', // Could be mapped from response.creator_id
      total_amount: response.grand_total_int || 0,
      subtotal: response.subtotal_int || 0,
      tax_amount: response.tax_decimal1 || 0,
      notes: response.notes || '',
      items: response.items?.map(item => ({
        item_name: item.item_name,
        spec: item.item_specification,
        quantity: item.item_quantity,
        unit_price: item.unit_price,
        subtotal: item.line_subtotal ? item.line_subtotal : item.unit_price * item.item_quantity,
        status: item.line_status,
        request_info: item.request_info || null
      })) || [],
      status_history: []
    }
    
    console.log('Purchase order loaded:', purchaseOrder.value)
  } catch (error) {
    console.error('載入採購單詳情失敗:', error)
    ElMessage.error('載入採購單詳情失敗')
  } finally {
    loading.value = false
  }
}

const editPO = () => {
  router.push(`/purchase-orders/${route.params.id}/edit`)
}

const goBack = () => {
  router.back()
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    order_created: '',
    purchased: 'success',
    shipped: 'warning',
    arrived: 'info',
    completed: 'success'
  }
  return statusMap[status] || ''
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    order_created: '已建立',
    purchased: '已採購',
    shipped: '已出貨',
    arrived: '已到貨',
    completed: '已完成'
  }
  return statusMap[status] || status
}

const getItemStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: 'info',
    approved: 'success',
    purchased: 'primary',
    received: 'success'
  }
  return statusMap[status] || ''
}

const getItemStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待處理',
    approved: '已核准',
    order_created: '已建立',
    purchased: '已採購',
    received: '已收貨'
  }
  return statusMap[status] || status
}

onMounted(() => {
  loadPODetail()
})
</script>

<style scoped>
.purchase-order-detail {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.detail-container {
  max-width: 1200px;
}

.info-card,
.items-card,
.summary-card,
.history-card {
  margin-bottom: 20px;
}

.info-card :deep(.el-card__header h3),
.items-card :deep(.el-card__header h3),
.summary-card :deep(.el-card__header h3),
.history-card :deep(.el-card__header h3) {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.notes {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.notes h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #606266;
}

.notes p {
  margin: 0;
  color: #303133;
  line-height: 1.5;
}

.amount {
  font-weight: bold;
  color: #409eff;
}

.summary {
  padding: 20px 0;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  font-size: 16px;
}

.summary-item .total {
  font-weight: bold;
  font-size: 18px;
  color: #409eff;
}

.history-item {
  padding: 10px 0;
}

.status-change {
  margin-bottom: 5px;
}

.operator {
  font-size: 14px;
  color: #909399;
  margin-bottom: 5px;
}

.remarks {
  font-size: 14px;
  color: #606266;
}
</style>