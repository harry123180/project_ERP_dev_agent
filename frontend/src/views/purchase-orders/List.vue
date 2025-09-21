<template>
  <div class="purchase-orders-list">
    <div class="page-header">
      <h1 class="page-title">採購單列表</h1>
      <div class="header-actions">
        <el-button type="primary" @click="buildFromRequisitions">
          <el-icon><DocumentCopy /></el-icon>
          建立採購單
        </el-button>
      </div>
    </div>

    <div class="filters">
      <el-form :model="filters" inline>
        <el-form-item label="供應商">
          <el-select 
            v-model="filters.supplier" 
            placeholder="選擇供應商" 
            clearable
            style="width: 200px"
          >
            <el-option label="全部" value="" />
          </el-select>
        </el-form-item>
        <el-form-item label="狀態">
          <el-select 
            v-model="filters.status" 
            placeholder="選擇狀態" 
            clearable
            style="width: 150px"
          >
            <el-option label="全部" value="" />
            <el-option label="已建立" value="order_created" />
            <el-option label="已製單" value="outputted" />
            <el-option label="已採購" value="purchased" />
            <el-option label="已發貨" value="shipped" />
            <el-option label="已撤銷" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadPurchaseOrders">搜尋</el-button>
          <el-button @click="resetFilters">重設</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-container">
      <el-table 
        :data="purchaseOrders" 
        :loading="loading"
        stripe
        @row-click="viewDetail"
      >
        <el-table-column prop="purchase_order_no" label="採購單號" width="140" />
        <el-table-column prop="supplier_name" label="供應商" width="160" />
        <el-table-column prop="grand_total_int" label="總金額" width="100">
          <template #default="{ row }">
            {{ formatCurrency(row.grand_total_int) }}
          </template>
        </el-table-column>
        <el-table-column prop="purchase_status" label="狀態" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.purchase_status)">
              {{ getStatusText(row.purchase_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="output_person_name" label="製單人" width="100">
          <template #default="{ row }">
            <el-popover
              v-if="row.output_person_name"
              placement="top"
              width="220"
              trigger="hover"
            >
              <template #reference>
                <span class="user-name">{{ row.output_person_name }}</span>
              </template>
              <div class="user-popover">
                <p><strong>製單人資訊</strong></p>
                <p>姓名: {{ row.output_person_name }}</p>
                <p>帳號: {{ row.output_person_username }}</p>
                <p>製單時間: {{ formatDate(row.output_timestamp) }}</p>
              </div>
            </el-popover>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="confirm_purchaser_name" label="採購人" width="100">
          <template #default="{ row }">
            <el-popover
              v-if="row.confirm_purchaser_name"
              placement="top"
              width="220"
              trigger="hover"
            >
              <template #reference>
                <span class="user-name">{{ row.confirm_purchaser_name }}</span>
              </template>
              <div class="user-popover">
                <p><strong>採購人資訊</strong></p>
                <p>姓名: {{ row.confirm_purchaser_name }}</p>
                <p>帳號: {{ row.confirm_purchaser_username }}</p>
                <p>採購時間: {{ formatDate(row.confirm_timestamp) }}</p>
              </div>
            </el-popover>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="建立時間" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click.stop="viewDetail(row)">詳情</el-button>
            <el-button 
              size="small" 
              type="primary" 
              @click.stop="editPO(row)"
              v-if="canEdit(row)"
            >
              編輯
            </el-button>
            <el-button 
              size="small" 
              type="success" 
              @click.stop="handleOutput(row)"
              v-if="canOutput(row)"
            >
              輸出
            </el-button>
            <el-button 
              size="small" 
              type="warning" 
              @click.stop="confirmPurchase(row)"
              v-if="canConfirmPurchase(row)"
            >
              確認採購
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click.stop="withdrawPO(row)"
              v-if="canWithdraw(row)"
            >
              撤銷
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :prev-text="'上一頁'"
          :next-text="'下一頁'"
          background
          @size-change="loadPurchaseOrders"
          @current-change="loadPurchaseOrders"
        >
          <template #sizes>
            <el-select
              :model-value="pagination.size"
              @update:model-value="loadPurchaseOrders"
              style="width: 100px"
              size="small"
            >
              <el-option
                v-for="size in [10, 20, 50, 100]"
                :key="size"
                :label="`${size}筆/頁`"
                :value="size"
              />
            </el-select>
          </template>
          <template #total>
            <span class="pagination-total">共 {{ pagination.total }} 筆</span>
          </template>
        </el-pagination>
      </div>
    </div>

    <!-- Preview Modal -->
    <PreviewModal 
      v-model:visible="previewModalVisible"
      :po-no="selectedPONo"
      @exported="handleExported"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElPopover } from 'element-plus'
import { DocumentCopy } from '@element-plus/icons-vue'
import { formatDate, formatCurrency } from '@/utils/format'
import { procurementApi } from '@/api/procurement'
import { useAuthStore } from '@/stores/auth'
import PreviewModal from './PreviewModal.vue'

const router = useRouter()
const authStore = useAuthStore()

// Reactive data
const loading = ref(false)
const purchaseOrders = ref([])
const filters = ref({
  supplier: '',
  status: ''  // 空字串表示全部，不設定預設篩選
})

const pagination = ref({
  page: 1,
  size: 20,
  total: 0
})

const previewModalVisible = ref(false)
const selectedPONo = ref('')

// Methods
const loadPurchaseOrders = async () => {
  loading.value = true
  try {
    const response = await procurementApi.getPurchaseOrders({
      ...filters.value,
      page: pagination.value.page,
      page_size: pagination.value.size
    })
    purchaseOrders.value = response.items
    pagination.value.total = response.pagination.total
  } catch (error) {
    console.error('載入採購單列表失敗:', error)
    ElMessage.error('載入採購單列表失敗')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.value = {
    supplier: '',
    status: ''
  }
  pagination.value.page = 1
  loadPurchaseOrders()
}

const buildFromRequisitions = () => {
  router.push('/purchase-orders/build-candidates')
}


const viewDetail = (row: any) => {
  router.push(`/purchase-orders/${row.purchase_order_no}`)
}

const editPO = (row: any) => {
  router.push(`/purchase-orders/${row.purchase_order_no}/edit`)
}

const canEdit = (row: any) => {
  return ['order_created', 'pending'].includes(row.purchase_status)
}

const canOutput = (row: any) => {
  return true // 所有狀態都可以輸出
}

const canConfirmPurchase = (row: any) => {
  // 只有狀態為 "已製單" (outputted) 的採購單可以確認採購
  return row.purchase_status === 'outputted'
}

const canWithdraw = (row: any) => {
  // 只有採購主管和系統管理員可以撤銷，且狀態不能為已撤銷
  return authStore.hasRole('ProcurementMgr', 'Admin') && row.purchase_status !== 'cancelled'
}

const handleOutput = (row: any) => {
  selectedPONo.value = row.purchase_order_no
  previewModalVisible.value = true
}

const handleExported = () => {
  loadPurchaseOrders()
  // 移除成功訊息，避免列印時顯示
  // ElMessage.success('採購單已成功輸出')
}

const confirmPurchase = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `確定要將採購單 ${row.purchase_order_no} 狀態更改為已採購嗎？`,
      '確認採購',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    loading.value = true
    const response = await procurementApi.confirmPurchase(row.purchase_order_no)
    
    if (response.success) {
      ElMessage.success('採購單已確認採購')
      loadPurchaseOrders()
    } else {
      ElMessage.error(response.message || '確認採購失敗')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('確認採購失敗:', error)
      ElMessage.error('確認採購失敗')
    }
  } finally {
    loading.value = false
  }
}

const withdrawPO = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `是否確定要撤銷該張採購單 ${row.purchase_order_no}？`,
      '確認撤銷',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    loading.value = true
    const response = await procurementApi.cancelPO(row.purchase_order_no, {
      reason: '管理員撤銷採購單'
    })
    
    if (response.success) {
      ElMessage.success('採購單已撤銷')
      loadPurchaseOrders()
    } else {
      ElMessage.error(response.message || '撤銷失敗')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('撤銷採購單失敗:', error)
      ElMessage.error('撤銷採購單失敗')
    }
  } finally {
    loading.value = false
  }
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: 'info',
    confirmed: 'primary', 
    order_created: '',
    outputted: 'primary',
    purchased: 'success',
    shipped: 'warning',
    cancelled: 'info'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '已建立',
    confirmed: '已製單',
    order_created: '已建立',
    outputted: '已製單',
    purchased: '已採購',
    shipped: '已發貨',
    cancelled: '已撤銷'
  }
  return statusMap[status] || status
}

onMounted(() => {
  // 不設定預設篩選，顯示所有採購單
  loadPurchaseOrders()
})
</script>

<style scoped>
.purchase-orders-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .header-actions {
    display: flex;
    gap: 8px;
  }
}

.page-title {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.filters {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.table-container {
  background: white;
  border-radius: 4px;
  padding: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
.user-name {
  color: #303133;
  cursor: default;
}

.user-popover {
  p {
    margin: 5px 0;
    font-size: 13px;
  }
  p:first-child {
    margin-bottom: 10px;
    border-bottom: 1px solid #ebeef5;
    padding-bottom: 5px;
  }
}
</style>