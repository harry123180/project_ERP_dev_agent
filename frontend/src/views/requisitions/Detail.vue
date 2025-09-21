<template>
  <div class="requisition-detail">
    <PageHeader
      :title="`請購單詳情`"
      :subtitle="requisitionId"
      :badge="requisition?.order_status"
      :badge-type="getStatusType(requisition?.order_status)"
      :show-back="true"
      :show-refresh="true"
      @back="handleBack"
      @refresh="handleRefresh"
    >
      <template #extra>
        <div class="detail-actions">
          <el-button
            v-if="canEdit"
            type="primary"
            :icon="Edit"
            @click="editRequisition"
          >
            編輯
          </el-button>
          <el-button
            v-if="canSubmit"
            type="success"
            :icon="Check"
            @click="submitRequisition"
          >
            提交審核
          </el-button>
          <el-button
            v-if="canReview"
            type="warning"
            :icon="DocumentChecked"
            @click="openReviewDialog"
          >
            審核
          </el-button>
        </div>
      </template>
    </PageHeader>

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="requisition" class="detail-content">
      <!-- Basic Information -->
      <el-card class="info-card">
        <template #header>
          <h3>基本信息</h3>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="請購單號">
            {{ requisition.request_order_no }}
          </el-descriptions-item>
          <el-descriptions-item label="申請人">
            {{ requisition.requester_name }}
          </el-descriptions-item>
          <el-descriptions-item label="用途類型">
            <el-tag :type="requisition.usage_type === 'project' ? 'warning' : 'info'">
              {{ requisition.usage_type === 'daily' ? '日常用品' : '專案用品' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="專案編號" v-if="requisition.project_id">
            {{ requisition.project_id }}
          </el-descriptions-item>
          <el-descriptions-item label="請購狀態">
            <StatusTag :status="requisition.order_status" />
          </el-descriptions-item>
          <el-descriptions-item label="提交日期">
            {{ formatDate(requisition.submit_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="採購狀態" v-if="requisition.order_status === 'reviewed' || requisition.order_status === 'approved'">
            <el-tag :type="getPurchaseStatusType(requisition.purchase_status)">
              {{ getPurchaseStatusText(requisition.purchase_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="入庫狀態" v-if="requisition.purchase_status === 'arrived'">
            <el-tag :type="getStorageStatusType(requisition.storage_status)">
              {{ getStorageStatusText(requisition.storage_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="驗收狀態" v-if="requisition.purchase_status === 'arrived'">
            <el-tag :type="getAcceptanceStatusType(requisition.acceptance_status)">
              {{ getAcceptanceStatusText(requisition.acceptance_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="創建時間">
            {{ formatDate(requisition.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新時間">
            {{ formatDate(requisition.updated_at) }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- Summary Statistics -->
      <el-card v-if="requisition.summary" class="summary-card">
        <template #header>
          <h3>項目統計</h3>
        </template>
        <el-row :gutter="20">
          <el-col :span="6">
            <StatCard
              title="總項目數"
              :value="requisition.summary.total_items || 0"
              icon="DocumentCopy"
              color="primary"
            />
          </el-col>
          <el-col :span="6">
            <StatCard
              title="已核准"
              :value="requisition.summary.approved_items || 0"
              icon="Check"
              color="success"
            />
          </el-col>
          <el-col :span="6">
            <StatCard
              title="已駁回"
              :value="requisition.summary.rejected_items || 0"
              icon="Close"
              color="danger"
            />
          </el-col>
          <el-col :span="6">
            <StatCard
              title="有疑問"
              :value="requisition.summary.questioned_items || 0"
              icon="QuestionFilled"
              color="warning"
            />
          </el-col>
        </el-row>
      </el-card>

      <!-- Items List -->
      <el-card class="items-card">
        <template #header>
          <h3>請購項目</h3>
        </template>
        <el-table :data="requisitionItems" border stripe>
          <el-table-column type="index" label="序號" width="60" align="center" />
          <el-table-column label="項目名稱" prop="item_name" min-width="150" show-overflow-tooltip />
          <el-table-column label="規格說明" prop="item_specification" min-width="150" show-overflow-tooltip />
          <el-table-column label="數量" prop="item_quantity" width="80" align="center" />
          <el-table-column label="單位" prop="item_unit" width="80" align="center" />
          <el-table-column label="類別" prop="item_category" width="100" align="center">
            <template #default="{ row }">
              {{ getCategoryName(row.item_category) }}
            </template>
          </el-table-column>
          <el-table-column label="請購狀態" prop="item_status" width="100" align="center">
            <template #default="{ row }">
              <StatusTag :status="row.item_status" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="採購狀態" width="100" align="center" v-if="requisition.order_status === 'reviewed' || requisition.order_status === 'approved'">
            <template #default="{ row }">
              <el-tag :type="getItemStatusType(row.item_status)" size="small">
                {{ getItemStatusText(row.item_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="入庫狀態" width="100" align="center" v-if="hasPurchaseOrder">
            <template #default="{ row }">
              <el-tag :type="getStorageStatusType(row.storage_status)" size="small">
                {{ getStorageStatusText(row.storage_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="驗收狀態" width="100" align="center" v-if="hasPurchaseOrder">
            <template #default="{ row }">
              <el-tag :type="getAcceptanceStatusType(row.acceptance_status)" size="small">
                {{ getAcceptanceStatusText(row.acceptance_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="供應商" prop="supplier" width="120" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.supplier?.supplier_name_zh || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="單價" prop="unit_price" width="100" align="right">
            <template #default="{ row }">
              <span v-if="row.unit_price" class="money">{{ formatMoney(row.unit_price) }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="小計" prop="subtotal" width="100" align="right">
            <template #default="{ row }">
              <span v-if="row.subtotal" class="money">{{ formatMoney(row.subtotal) }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="備註" prop="status_note" min-width="150" show-overflow-tooltip />
        </el-table>
      </el-card>
    </div>

    <!-- Review Dialog -->
    <el-dialog
      v-model="reviewDialogVisible"
      title="審核請購單"
      width="95vw"
      style="max-width: 1400px"
      destroy-on-close
    >
      <RequisitionReview
        v-if="requisition"
        :requisition="requisition"
        @close="handleCloseReview"
        @updated="handleRequisitionUpdated"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Check, DocumentChecked } from '@element-plus/icons-vue'
import { PageHeader, StatusTag, StatCard } from '@/components'
import RequisitionReview from './Review.vue'
import { useRequisitionStore, useAuthStore } from '@/stores'
import type { RequestOrder, RequestOrderItem } from '@/types/common'
import { STATUS_TYPES } from '@/types/common'

const route = useRoute()
const router = useRouter()
const requisitionStore = useRequisitionStore()
const authStore = useAuthStore()

// State
const loading = ref(false)
const reviewDialogVisible = ref(false)

// Computed
const requisitionId = computed(() => route.params.id as string)
const requisition = computed(() => requisitionStore.currentRequisition)
const requisitionItems = computed(() => {
  return requisition.value?.items || []
})

// Permissions
const canEdit = computed(() => {
  if (!requisition.value) return false
  return requisition.value.order_status === 'draft' &&
         (authStore.hasRole('Admin') || authStore.user?.user_id === requisition.value.requester_id)
})

const canSubmit = computed(() => {
  if (!requisition.value) return false
  return requisition.value.order_status === 'draft' &&
         (authStore.hasRole('Admin') || authStore.user?.user_id === requisition.value.requester_id)
})

const canReview = computed(() => {
  if (!requisition.value) return false
  return requisition.value.order_status === 'submitted' &&
         authStore.hasRole('Admin', 'ProcurementMgr', 'Procurement', 'Manager')
})

const hasPurchaseOrder = computed(() => {
  if (!requisition.value) return false
  return requisition.value.purchase_status && requisition.value.purchase_status !== 'none'
})

// Methods
const getStatusType = (status?: string) => {
  return STATUS_TYPES[status || ''] || ''
}

const formatDate = (date?: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-TW')
}

const formatMoney = (amount: number) => {
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: 'TWD',
    minimumFractionDigits: 0
  }).format(amount)
}

const getCategoryName = (code?: string) => {
  const categories = {
    office: '辦公用品',
    electronic: '電子設備',
    furniture: '辦公家具',
    consumable: '耗材用品',
    tool: '工具設備',
    other: '其他'
  }
  return categories[code as keyof typeof categories] || code || '-'
}

// 採購狀態映射 (根據 item_status)
const getItemStatusText = (status?: string) => {
  const statusMap: Record<string, string> = {
    'draft': '草稿',
    'pending_review': '待審核',
    'approved': '已核准',
    'rejected': '已拒絕',
    'questioned': '有疑問',
    'reviewed': '已審核',
    'unavailable': '不可用',
    'order_created': '已製單',
    'purchased': '已採購',
    'shipped': '已發貨',
    'arrived': '已到貨',
    'warehoused': '已入庫',
    'delivered': '已送達',
    'received': '已收貨',
    'issued': '已發放',
    'cancelled': '已取消'
  }
  return statusMap[status || 'pending_review'] || status || '待審核'
}

const getItemStatusType = (status?: string) => {
  const typeMap: Record<string, string> = {
    'draft': 'info',
    'pending_review': 'warning',
    'approved': 'success',
    'rejected': 'danger',
    'questioned': 'warning',
    'reviewed': 'primary',
    'unavailable': 'danger',
    'order_created': 'primary',
    'purchased': 'primary',
    'shipped': 'warning',
    'arrived': 'success',
    'warehoused': 'success',
    'delivered': 'success',
    'received': 'success',
    'issued': 'success',
    'cancelled': 'info'
  }
  return typeMap[status || 'pending_review'] || 'info'
}

// 保留舊的函數名稱以避免破壞其他地方的引用
const getPurchaseStatusText = getItemStatusText
const getPurchaseStatusType = getItemStatusType

// 入庫狀態映射
const getStorageStatusText = (status?: string) => {
  const statusMap: Record<string, string> = {
    'pending': '待入庫',
    'partial': '部分入庫',
    'completed': '已入庫'
  }
  return statusMap[status || 'pending'] || '待入庫'
}

const getStorageStatusType = (status?: string) => {
  const typeMap: Record<string, string> = {
    'pending': 'warning',
    'partial': 'primary',
    'completed': 'success'
  }
  return typeMap[status || 'pending'] || 'warning'
}

// 驗收狀態映射
const getAcceptanceStatusText = (status?: string) => {
  const statusMap: Record<string, string> = {
    'pending': '待驗收',
    'inspecting': '驗收中',
    'passed': '驗收合格',
    'failed': '驗收不合格',
    'partial': '部分驗收'
  }
  return statusMap[status || 'pending'] || '待驗收'
}

const getAcceptanceStatusType = (status?: string) => {
  const typeMap: Record<string, string> = {
    'pending': 'warning',
    'inspecting': 'primary',
    'passed': 'success',
    'failed': 'danger',
    'partial': 'warning'
  }
  return typeMap[status || 'pending'] || 'warning'
}

// Event handlers
const handleBack = () => {
  router.go(-1)
}

const handleRefresh = async () => {
  await fetchRequisitionDetail()
}

const editRequisition = () => {
  router.push(`/requisitions/${requisitionId.value}/edit`)
}

const submitRequisition = async () => {
  try {
    await ElMessageBox.confirm(
      '提交後將無法修改，確定要提交審核嗎？',
      '提交確認',
      {
        confirmButtonText: '確定提交',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await requisitionStore.submitRequisition(requisitionId.value)
    ElMessage.success('請購單已提交審核')
    await fetchRequisitionDetail()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Submit failed:', error)
    }
  }
}

const openReviewDialog = () => {
  reviewDialogVisible.value = true
}

const handleCloseReview = () => {
  reviewDialogVisible.value = false
}

const handleRequisitionUpdated = () => {
  handleCloseReview()
  fetchRequisitionDetail()
  ElMessage.success('請購單審核完成')
}

const fetchRequisitionDetail = async () => {
  try {
    loading.value = true
    await requisitionStore.fetchRequisitionDetail(requisitionId.value)

    // 使用後端返回的實際狀態數據，不再強制覆蓋
  } catch (error) {
    ElMessage.error('獲取請購單詳情失敗')
    router.push('/requisitions')
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  fetchRequisitionDetail()
})
</script>

<style scoped>
.requisition-detail {
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

  .detail-actions {
    display: flex;
    gap: 8px;
  }

  .info-card,
  .summary-card,
  .items-card {
    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }

  .money {
    font-family: Monaco, 'Courier New', monospace;
    font-weight: 500;
    color: #409eff;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .requisition-detail {
    .detail-actions {
      flex-direction: column;
      
      .el-button {
        width: 100%;
      }
    }
    
    .summary-card {
      :deep(.el-col) {
        margin-bottom: 16px;
      }
    }
  }
}
</style>