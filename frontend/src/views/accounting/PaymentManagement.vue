<template>
  <div class="payment-management">
    <!-- Header with Statistics -->
    <div class="header-section">
      <h2>付款管理</h2>
      <div class="statistics-cards">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">未付款</div>
            <div class="stat-value">{{ formatCurrency(summary.unpaid.amount) }}</div>
            <div class="stat-count">{{ summary.unpaid.count }} 筆</div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">已付款</div>
            <div class="stat-value">{{ formatCurrency(summary.paid.amount) }}</div>
            <div class="stat-count">{{ summary.paid.count }} 筆</div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">電匯付款</div>
            <div class="stat-value">{{ formatCurrency(summary.paid.by_method?.remittance || 0) }}</div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">支票付款</div>
            <div class="stat-value">{{ formatCurrency(summary.paid.by_method?.check || 0) }}</div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- Filter Section -->
    <el-card class="filter-section">
      <div class="filter-row">
        <el-select
          v-model="filters.status"
          placeholder="付款狀態"
          @change="loadPurchaseOrders"
          clearable
        >
          <el-option label="未付款" value="unpaid" />
          <el-option label="已付款" value="paid" />
          <el-option label="全部" value="all" />
        </el-select>

        <el-select
          v-model="filters.supplier_id"
          placeholder="選擇供應商"
          @change="loadPurchaseOrders"
          clearable
          filterable
        >
          <el-option
            v-for="supplier in suppliers"
            :key="supplier.supplier_id"
            :label="supplier.supplier_name_zh || supplier.supplier_name_en"
            :value="supplier.supplier_id"
          />
        </el-select>

        <el-button type="primary" @click="handleBatchPayment" :disabled="selectedOrders.length === 0">
          批次設定付款 ({{ selectedOrders.length }})
        </el-button>
      </div>
    </el-card>

    <!-- Purchase Orders Table -->
    <el-card class="table-section">
      <el-table
        :data="purchaseOrders"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        :row-class-name="getRowClassName"
      >
        <el-table-column type="selection" width="50" />

        <el-table-column prop="purchase_order_no" label="採購單號" width="150" />

        <el-table-column label="供應商" min-width="200">
          <template #default="{ row }">
            {{ row.supplier_info?.supplier_name_zh || row.supplier_info?.supplier_name_en || row.supplier_name }}
          </template>
        </el-table-column>

        <el-table-column label="金額" width="120" align="right">
          <template #default="{ row }">
            {{ formatCurrency(row.grand_total_int) }}
          </template>
        </el-table-column>

        <el-table-column label="付款狀態" width="100">
          <template #default="{ row }">
            <el-tag :type="getPaymentStatusType(row.billing_status)">
              {{ getPaymentStatusText(row.billing_status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="付款方式" width="100">
          <template #default="{ row }">
            <span v-if="row.payment_method">
              {{ getPaymentMethodText(row.payment_method) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column label="付款日期" width="120">
          <template #default="{ row }">
            {{ row.payment_date || '-' }}
          </template>
        </el-table-column>

        <el-table-column label="建立日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.billing_status !== 'paid'"
              type="primary"
              size="small"
              @click="handleSinglePayment(row)"
            >
              設定付款
            </el-button>
            <el-button
              v-else
              type="info"
              size="small"
              @click="viewPaymentDetails(row)"
            >
              查看詳情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadPurchaseOrders"
          @current-change="loadPurchaseOrders"
        />
      </div>
    </el-card>

    <!-- Payment Dialog -->
    <el-dialog
      v-model="paymentDialog.visible"
      :title="paymentDialog.title"
      width="600px"
    >
      <el-form ref="paymentFormRef" :model="paymentForm" label-width="120px">
        <el-form-item label="採購單號">
          <div class="po-list">
            <el-tag v-for="po in paymentDialog.orders" :key="po" class="po-tag">
              {{ po }}
            </el-tag>
          </div>
        </el-form-item>

        <el-form-item label="總金額">
          <div class="total-amount">
            {{ formatCurrency(paymentDialog.totalAmount) }}
          </div>
        </el-form-item>

        <el-form-item label="付款方式" required>
          <el-radio-group v-model="paymentForm.payment_method">
            <el-radio label="電匯">電匯</el-radio>
            <el-radio label="支票">支票</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="付款備註">
          <el-input
            v-model="paymentForm.payment_note"
            type="textarea"
            :rows="3"
            placeholder="請輸入付款備註（選填）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="paymentDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="confirmPayment" :loading="submitting">
          確認付款
        </el-button>
      </template>
    </el-dialog>

    <!-- Payment Details Dialog -->
    <el-dialog
      v-model="detailsDialog.visible"
      title="付款詳情"
      width="500px"
    >
      <el-descriptions :column="1" border>
        <el-descriptions-item label="採購單號">
          {{ detailsDialog.order?.purchase_order_no }}
        </el-descriptions-item>
        <el-descriptions-item label="供應商">
          {{ detailsDialog.order?.supplier_info?.supplier_name_zh || detailsDialog.order?.supplier_name }}
        </el-descriptions-item>
        <el-descriptions-item label="金額">
          {{ formatCurrency(detailsDialog.order?.grand_total_int) }}
        </el-descriptions-item>
        <el-descriptions-item label="付款方式">
          {{ getPaymentMethodText(detailsDialog.order?.payment_method) }}
        </el-descriptions-item>
        <el-descriptions-item label="付款日期">
          {{ detailsDialog.order?.payment_date }}
        </el-descriptions-item>
        <el-descriptions-item label="付款備註">
          {{ detailsDialog.order?.payment_note || '無' }}
        </el-descriptions-item>
      </el-descriptions>

      <template #footer>
        <el-button @click="detailsDialog.visible = false">關閉</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// Data
const loading = ref(false)
const submitting = ref(false)
const purchaseOrders = ref<any[]>([])
const selectedOrders = ref<any[]>([])
const suppliers = ref<any[]>([])

// Summary statistics
const summary = reactive({
  unpaid: { count: 0, amount: 0 },
  paid: { count: 0, amount: 0, by_method: { remittance: 0, check: 0 } },
  total: { count: 0, amount: 0 }
})

// Filters
const filters = reactive({
  status: 'unpaid',
  supplier_id: ''
})

// Pagination
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// Payment Dialog
const paymentDialog = reactive({
  visible: false,
  title: '',
  orders: [] as string[],
  totalAmount: 0
})

const paymentForm = reactive({
  payment_method: '電匯',
  payment_note: ''
})

// Details Dialog
const detailsDialog = reactive({
  visible: false,
  order: null as any
})

// Methods
const loadPurchaseOrders = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize,
      status: filters.status
    }

    if (filters.supplier_id) {
      params.supplier_id = filters.supplier_id
    }

    const response = await api.get('/accounting/payment-management/list', { params })

    // Handle both direct data and wrapped response formats
    if (response.data) {
      if (response.data.success === true && response.data.data) {
        // Wrapped format
        purchaseOrders.value = response.data.data.items || []
        pagination.total = response.data.data.pagination?.total || 0
      } else if (response.data.items !== undefined) {
        // Direct format
        purchaseOrders.value = response.data.items || []
        pagination.total = response.data.pagination?.total || 0
      }
    }
  } catch (error: any) {
    console.error('Load error:', error)
    ElMessage.error(error.response?.data?.error?.message || '載入採購單失敗')
  } finally {
    loading.value = false
  }
}

const loadSummary = async () => {
  try {
    const response = await api.get('/accounting/payment-management/summary')

    // Handle both direct data and wrapped response formats
    if (response.data) {
      if (response.data.success === true && response.data.data) {
        // Wrapped format
        Object.assign(summary, response.data.data)
      } else if (response.data.unpaid !== undefined || response.data.paid !== undefined) {
        // Direct format
        Object.assign(summary, response.data)
      }
    }
  } catch (error: any) {
    console.error('Summary error:', error)
  }
}

const loadSuppliers = async () => {
  try {
    const response = await api.get('/suppliers')

    // Handle both direct data and wrapped response formats
    if (response.data) {
      if (response.data.success === true && response.data.data) {
        // Wrapped format
        suppliers.value = response.data.data
      } else if (Array.isArray(response.data)) {
        // Direct format - array of suppliers
        suppliers.value = response.data
      }
    }
  } catch (error: any) {
    console.error('Suppliers error:', error)
  }
}

const handleSelectionChange = (val: any[]) => {
  // Only allow selection of unpaid orders
  selectedOrders.value = val.filter(order => order.billing_status !== 'paid')
}

const handleSinglePayment = (order: any) => {
  paymentDialog.title = '設定付款'
  paymentDialog.orders = [order.purchase_order_no]
  paymentDialog.totalAmount = order.grand_total_int
  paymentDialog.visible = true

  // Reset form
  paymentForm.payment_method = '電匯'
  paymentForm.payment_note = ''
}

const handleBatchPayment = () => {
  if (selectedOrders.value.length === 0) {
    ElMessage.warning('請選擇要付款的採購單')
    return
  }

  const unpaidOrders = selectedOrders.value.filter(order => order.billing_status !== 'paid')
  if (unpaidOrders.length === 0) {
    ElMessage.warning('所選採購單都已付款')
    return
  }

  paymentDialog.title = `批次設定付款 (${unpaidOrders.length} 筆)`
  paymentDialog.orders = unpaidOrders.map(o => o.purchase_order_no)
  paymentDialog.totalAmount = unpaidOrders.reduce((sum, o) => sum + o.grand_total_int, 0)
  paymentDialog.visible = true

  // Reset form
  paymentForm.payment_method = '電匯'
  paymentForm.payment_note = ''
}

const confirmPayment = async () => {
  if (!paymentForm.payment_method) {
    ElMessage.warning('請選擇付款方式')
    return
  }

  try {
    await ElMessageBox.confirm(
      `確定要將 ${paymentDialog.orders.length} 筆採購單設定為已付款嗎？`,
      '確認付款',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    submitting.value = true

    const response = await api.post('/accounting/payment-management/update-payment', {
      purchase_order_nos: paymentDialog.orders,
      payment_method: paymentForm.payment_method,
      payment_note: paymentForm.payment_note
    })

    // Handle both direct data and wrapped response formats
    let updateCount = 0
    if (response.data) {
      if (response.data.success === true && response.data.data) {
        // Wrapped format
        updateCount = response.data.data.updated_count || 0
      } else if (response.data.updated_count !== undefined) {
        // Direct format
        updateCount = response.data.updated_count || 0
      }
    }

    if (updateCount > 0) {
      ElMessage.success(`成功設定 ${updateCount} 筆採購單為已付款`)
      paymentDialog.visible = false

      // Reload data
      await Promise.all([loadPurchaseOrders(), loadSummary()])
    } else {
      ElMessage.warning('未更新任何採購單')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Payment error:', error)
      ElMessage.error(error.response?.data?.error?.message || '付款設定失敗')
    }
  } finally {
    submitting.value = false
  }
}

const viewPaymentDetails = (order: any) => {
  detailsDialog.order = order
  detailsDialog.visible = true
}

const getRowClassName = ({ row }: { row: any }) => {
  return row.billing_status === 'paid' ? 'paid-row' : ''
}

// Helper functions
const formatCurrency = (amount: number) => {
  if (!amount) return 'NT$0'
  return `NT$${amount.toLocaleString()}`
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return dateStr.split('T')[0]
}

const getPaymentStatusType = (status: string) => {
  const types: Record<string, string> = {
    'none': 'warning',
    'pending': 'info',
    'billed': 'primary',
    'paid': 'success'
  }
  return types[status] || 'info'
}

const getPaymentStatusText = (status: string) => {
  const texts: Record<string, string> = {
    'none': '未付款',
    'pending': '待付款',
    'billed': '已請款',
    'paid': '已付款'
  }
  return texts[status] || status
}

const getPaymentMethodText = (method: string) => {
  const texts: Record<string, string> = {
    'remittance': '電匯',
    'check': '支票',
    'cash': '現金'
  }
  return texts[method] || method
}

// Lifecycle
onMounted(() => {
  Promise.all([
    loadPurchaseOrders(),
    loadSummary(),
    loadSuppliers()
  ])
})
</script>

<style scoped lang="scss">
.payment-management {
  padding: 20px;

  .header-section {
    margin-bottom: 20px;

    h2 {
      font-size: 24px;
      margin-bottom: 16px;
    }

    .statistics-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 16px;

      .stat-card {
        .stat-content {
          text-align: center;

          .stat-label {
            font-size: 14px;
            color: #909399;
            margin-bottom: 8px;
          }

          .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #303133;
            margin-bottom: 4px;
          }

          .stat-count {
            font-size: 12px;
            color: #606266;
          }
        }
      }
    }
  }

  .filter-section {
    margin-bottom: 20px;

    .filter-row {
      display: flex;
      gap: 12px;
      align-items: center;

      .el-select {
        width: 200px;
      }
    }
  }

  .table-section {
    .pagination-container {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }

    :deep(.paid-row) {
      background-color: #f0f9ff;
    }
  }

  .po-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;

    .po-tag {
      margin: 0;
    }
  }

  .total-amount {
    font-size: 20px;
    font-weight: bold;
    color: #409eff;
  }
}
</style>