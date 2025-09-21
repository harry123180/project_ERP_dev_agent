<template>
  <div class="requisition-list">
    <PageHeader
      title="請購單列表"
      subtitle="管理所有請購申請"
      :show-refresh="true"
      @refresh="handleRefresh"
    >
      <template #extra>
        <el-button
          type="primary"
          :icon="Plus"
          @click="createRequisition"
        >
          新增請購單
        </el-button>
      </template>
    </PageHeader>

    <DataTable
      :data="requisitions"
      :columns="columns"
      :actions="actions"
      :loading="loading"
      :show-pagination="true"
      :total="pagination.total"
      :page-size="pagination.page_size"
      :filter-fields="filterFields"
      :initial-filters="getInitialFilters()"
      :row-class-name="getRowClassName"
      @search="handleSearch"
      @page-change="handlePageChange"
      @size-change="handleSizeChange"
    />

    <!-- Review Dialog -->
    <el-dialog
      v-model="reviewDialogVisible"
      title="審核請購單"
      width="95vw"
      style="max-width: 1400px"
      destroy-on-close
    >
      <RequisitionReview
        v-if="currentRequisition"
        :requisition="currentRequisition"
        @close="handleCloseReview"
        @updated="handleRequisitionUpdated"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, View, Edit, Delete } from '@element-plus/icons-vue'
import { DataTable, PageHeader } from '@/components'
import RequisitionReview from './Review.vue'
import { useRequisitionStore, useAuthStore } from '@/stores'
import { requisitionApi } from '@/api/requisition'
import type { TableColumn, TableAction, FilterBarField } from '@/types/ui'
import type { RequestOrder } from '@/types/common'

const router = useRouter()
const requisitionStore = useRequisitionStore()
const authStore = useAuthStore()

// Computed
const userRole = computed(() => authStore.userRole)

// State
const loading = ref(false)
const reviewDialogVisible = ref(false)
const currentRequisition = ref<RequestOrder | null>(null)

// Data
const requisitions = computed(() => requisitionStore.requisitions)
const pagination = computed(() => requisitionStore.pagination)
const permissions = computed(() => requisitionStore.permissions)

// Table configuration
const columns: TableColumn[] = [
  {
    prop: 'request_order_no',
    label: '請購單號',
    width: '160px',
    fixed: 'left'
  },
  {
    prop: 'is_urgent',
    label: '加急',
    width: '70px',
    align: 'center',
    formatter: (row) => row.is_urgent ? '加急' : '',
    cellClass: (row) => row.is_urgent ? 'urgent-cell' : ''
  },
  {
    prop: 'requester_name',
    label: '申請人',
    width: '120px'
  },
  {
    prop: 'usage_type',
    label: '用途類型',
    width: '100px',
    formatter: (row) => row.usage_type === 'daily' ? '日常' : '專案'
  },
  {
    prop: 'project_id',
    label: '專案編號',
    width: '120px',
    showOverflowTooltip: true
  },
  {
    prop: 'submit_date',
    label: '提交日期',
    width: '120px',
    type: 'date'
  },
  {
    prop: 'order_status',
    label: '狀態',
    width: '100px',
    type: 'status'
  },
  {
    prop: 'summary.total_items',
    label: '總項目數',
    width: '100px',
    align: 'center'
  },
  {
    prop: 'summary.approved_items',
    label: '已核准',
    width: '80px',
    align: 'center',
    formatter: (row) => row.summary?.approved_items || 0
  },
  {
    prop: 'summary.rejected_items',
    label: '已駁回',
    width: '80px',
    align: 'center',
    formatter: (row) => row.summary?.rejected_items || 0,
    cellClass: (row) => (row.summary?.rejected_items || 0) > 0 ? 'rejected-cell' : ''
  },
  {
    prop: 'summary.questioned_items',
    label: '有疑問',
    width: '80px',
    align: 'center',
    formatter: (row) => row.summary?.questioned_items || 0,
    cellClass: (row) => (row.summary?.questioned_items || 0) > 0 ? 'questioned-cell' : ''
  },
  {
    prop: 'created_at',
    label: '創建時間',
    width: '160px',
    type: 'date'
  },
  {
    type: 'actions',
    label: '操作',
    width: '200px',
    fixed: 'right'
  }
]

const actions: TableAction[] = [
  {
    label: '查看',
    type: 'primary',
    icon: 'View',
    handler: (row) => viewRequisition(row.request_order_no)
  },
  {
    label: '編輯',
    type: 'primary',
    icon: 'Edit',
    handler: (row) => editRequisition(row.request_order_no),
    visible: (row) => row.order_status === 'draft' && canEdit(row)
  },
  {
    label: '審核',
    type: 'warning',
    icon: 'DocumentChecked',
    handler: (row) => reviewRequisition(row),
    visible: (row) => row.order_status === 'submitted' && canReview()
  },
  {
    label: '刪除',
    type: 'danger',
    icon: 'Delete',
    handler: (row) => deleteRequisition(row.request_order_no),
    visible: (row) => row.order_status === 'draft' && canDelete(row)
  },
  {
    label: '撤銷',
    type: 'danger',
    icon: 'Delete',
    handler: (row) => withdrawRequisition(row.request_order_no),
    visible: (row) => row.order_status === 'submitted' && canWithdraw(row)
  }
]

const filterFields = computed<FilterBarField[]>(() => [
  ...(permissions.value.can_view_all ? [{
    prop: 'mine',
    label: '範圍',
    type: 'select',
    options: [
      { label: '我的請購單', value: true },
      { label: '所有請購單', value: false }
    ],
    clearable: false
  }] : []),
  {
    prop: 'status',
    label: '狀態',
    type: 'select',
    options: [
      { label: '草稿', value: 'draft' },
      { label: '已提交', value: 'submitted' },
      { label: '已審核', value: 'reviewed' },
      { label: '已撤銷', value: 'cancelled' }
    ]
  },
  {
    prop: 'usage_type',
    label: '用途類型',
    type: 'select',
    options: [
      { label: '日常', value: 'daily' },
      { label: '專案', value: 'project' }
    ]
  },
  {
    prop: 'project_id',
    label: '專案編號',
    type: 'input',
    placeholder: '請輸入專案編號'
  },
  {
    prop: 'submit_date_range',
    label: '提交日期',
    type: 'daterange'
  }
])

// Permission helpers
const canEdit = (row: RequestOrder) => {
  return authStore.hasRole('Admin') || 
         (authStore.user?.user_id === row.requester_id)
}

const canDelete = (row: RequestOrder) => {
  return authStore.hasRole('Admin') || 
         (authStore.user?.user_id === row.requester_id)
}

const canWithdraw = (row: RequestOrder) => {
  // Only procurement managers and admins can withdraw submitted/reviewed requisitions
  return authStore.hasRole('ProcurementMgr', 'Admin', 'Manager')
}

const canReview = () => {
  return authStore.hasRole('Admin', 'ProcurementMgr', 'Procurement', 'Manager')
}

// 設定加急列的樣式
const getRowClassName = (params: { row: RequestOrder }) => {
  if (params.row.is_urgent) {
    return 'urgent-row'
  }
  return ''
}

const getInitialFilters = () => {
  // For non-privileged users, don't show the 'mine' filter since they can only see their own
  if (!permissions.value.can_view_all) {
    return {}
  }
  // For privileged users, default to showing all requisitions
  return { mine: false }
}

// Event handlers
const handleSearch = (filters: any) => {
  fetchRequisitions(filters)
}

const handleRefresh = () => {
  fetchRequisitions()
}

const handlePageChange = (page: number) => {
  fetchRequisitions({ page })
}

const handleSizeChange = (size: number) => {
  fetchRequisitions({ page: 1, page_size: size })
}

const handleCloseReview = () => {
  reviewDialogVisible.value = false
  currentRequisition.value = null
}

const handleRequisitionUpdated = () => {
  handleCloseReview()
  fetchRequisitions()
  ElMessage.success('請購單審核完成')
}

// Actions
const fetchRequisitions = async (params?: any) => {
  try {
    loading.value = true
    await requisitionStore.fetchRequisitions(params)
  } catch (error) {
    console.error('Failed to fetch requisitions:', error)
  } finally {
    loading.value = false
  }
}

const createRequisition = () => {
  router.push('/requisitions/create')
}

const viewRequisition = (id: string) => {
  router.push(`/requisitions/${id}`)
}

const editRequisition = (id: string) => {
  router.push(`/requisitions/${id}/edit`)
}

const reviewRequisition = async (requisition: RequestOrder) => {
  try {
    const fullRequisition = await requisitionStore.fetchRequisitionDetail(requisition.request_order_no)
    currentRequisition.value = fullRequisition
    reviewDialogVisible.value = true
  } catch (error) {
    ElMessage.error('獲取請購單詳情失敗')
  }
}

const deleteRequisition = async (id: string) => {
  try {
    await ElMessageBox.confirm(
      '確定要刪除這個請購單嗎？',
      '刪除確認',
      {
        confirmButtonText: '刪除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await requisitionApi.cancelRequisition(id, {
      reason: '管理員刪除草稿請購單'
    })
    
    if (response.success) {
      ElMessage.success('請購單已刪除')
      fetchRequisitions()
    } else {
      ElMessage.error(response.message || '刪除失敗')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('刪除請購單失敗:', error)
      ElMessage.error('刪除失敗')
    }
  }
}

const withdrawRequisition = async (id: string) => {
  try {
    await ElMessageBox.confirm(
      '是否確定要撤銷該張請購單？',
      '確認撤銷',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await requisitionApi.cancelRequisition(id, {
      reason: '管理員撤銷請購單'
    })
    
    if (response.success) {
      ElMessage.success('請購單已撤銷')
      fetchRequisitions()
    } else {
      ElMessage.error(response.message || '撤銷失敗')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('撤銷請購單失敗:', error)
      ElMessage.error('撤銷請購單失敗')
    }
  }
}

// Lifecycle
onMounted(() => {
  // For privileged users, explicitly show all requisitions on initial load
  const initialFilters = getInitialFilters()
  fetchRequisitions(initialFilters)
})
</script>

<style scoped>
.requisition-list {
  .el-dialog {
    .el-dialog__body {
      padding: 0;
    }
  }
}

/* Visual alerts for rejected and questioned items */
:deep(.rejected-cell) {
  background-color: #fef0f0 !important;
  color: #f56c6c !important;
  font-weight: 600 !important;
}

:deep(.questioned-cell) {
  background-color: #fdf6ec !important;
  color: #e6a23c !important;
  font-weight: 600 !important;
}

/* 加急項目樣式 */
:deep(.urgent-row) {
  background-color: #fff2f0 !important;
}

:deep(.urgent-row:hover) {
  background-color: #ffe7e6 !important;
}

:deep(.urgent-cell) {
  color: #cf1322;
  font-weight: 600;
}

/* 加急標籤樣式 */
:deep(.el-table .urgent-row td:nth-child(3)) {
  color: #cf1322;
  font-weight: bold;
}

/* Dark mode support */
.dark {
  :deep(.rejected-cell) {
    background-color: #2d1b1b !important;
    color: #f56c6c !important;
  }

  :deep(.questioned-cell) {
    background-color: #2b2416 !important;
    color: #e6a23c !important;
  }

  :deep(.urgent-row) {
    background-color: #2d1b1b !important;
  }

  :deep(.urgent-row:hover) {
    background-color: #3d1b1b !important;
  }
}
</style>