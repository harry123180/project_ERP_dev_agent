<template>
  <div class="supplier-purchase-orders">
    <div class="header">
      <div class="header-left">
        <el-button icon="ArrowLeft" @click="$router.go(-1)" circle />
        <h1>供應商採購單</h1>
      </div>
      <div class="header-info" v-if="supplier">
        <div class="supplier-card">
          <div class="supplier-name">
            <span class="label">供應商：</span>
            <span class="value">{{ supplier.supplier_name_zh }}</span>
            <el-tag v-if="supplier.supplier_region === 'international'" type="warning" size="small">國外</el-tag>
            <el-tag v-else type="success" size="small">國內</el-tag>
          </div>
          <div class="supplier-contact">
            <span class="label">聯絡人：</span>
            <span class="value">{{ supplier.supplier_contact_person || '-' }}</span>
          </div>
          <div class="supplier-phone">
            <span class="label">電話：</span>
            <span class="value">{{ supplier.supplier_phone || '-' }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Summary Cards -->
    <div class="summary-cards" v-if="summary">
      <div class="summary-card">
        <div class="summary-value">{{ summary.total_orders }}</div>
        <div class="summary-label">總採購單數</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">NT$ {{ formatAmount(summary.total_amount) }}</div>
        <div class="summary-label">總採購金額</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">{{ summary.pending_orders }}</div>
        <div class="summary-label">待處理訂單</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">{{ summary.completed_orders }}</div>
        <div class="summary-label">已完成訂單</div>
      </div>
    </div>
    
    <div class="filters">
      <el-form :model="filters" layout="inline" class="filter-form">
        <el-form-item label="採購單狀態">
          <el-select v-model="filters.status" placeholder="選擇狀態" clearable style="width: 150px">
            <el-option label="全部" value=""></el-option>
            <el-option label="訂單建立" value="order_created"></el-option>
            <el-option label="已輸出" value="outputted"></el-option>
            <el-option label="已確認" value="confirmed"></el-option>
            <el-option label="已出貨" value="shipped"></el-option>
            <el-option label="已到貨" value="arrived"></el-option>
            <el-option label="已完成" value="completed"></el-option>
            <el-option label="已取消" value="cancelled"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="訂單日期">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="開始日期"
            end-placeholder="結束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="fetchPurchaseOrders">查詢</el-button>
          <el-button icon="Refresh" @click="resetFilters">重置</el-button>
          <el-button type="success" icon="Download" @click="exportPurchaseOrders">匯出</el-button>
        </el-form-item>
      </el-form>
    </div>
    
    <div class="content">
      <el-table
        :data="purchaseOrders"
        v-loading="loading"
        stripe
        border
        @sort-change="handleSortChange"
      >
        <el-table-column prop="purchase_order_no" label="採購單號" width="150" sortable="custom">
          <template #default="scope">
            <el-link type="primary" @click="viewPurchaseOrder(scope.row)">
              {{ scope.row.purchase_order_no }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="order_date" label="訂單日期" width="120" sortable="custom">
          <template #default="scope">
            {{ formatDate(scope.row.order_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="purchase_status" label="狀態" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.purchase_status)">
              {{ getStatusText(scope.row.purchase_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="grand_total_int" label="總金額" width="150" align="right" sortable="custom">
          <template #default="scope">
            NT$ {{ formatAmount(scope.row.grand_total_int) }}
          </template>
        </el-table-column>
        <el-table-column prop="expected_delivery_date" label="預計交貨日" width="120">
          <template #default="scope">
            {{ formatDate(scope.row.expected_delivery_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="delivery_status" label="交貨狀態" width="120">
          <template #default="scope">
            <el-tag :type="getDeliveryStatusType(scope.row.delivery_status)">
              {{ getDeliveryStatusText(scope.row.delivery_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="payment_method" label="付款方式" width="120">
          <template #default="scope">
            {{ scope.row.payment_method || supplier?.payment_terms || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              icon="View"
              @click="viewPurchaseOrder(scope.row)"
            >
              查看
            </el-button>
            <el-button
              v-if="scope.row.purchase_status === 'order_created'"
              type="warning"
              size="small"
              icon="Printer"
              @click="printPurchaseOrder(scope.row)"
            >
              列印
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination" v-if="total > 0">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="fetchPurchaseOrders"
          @current-change="fetchPurchaseOrders"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'

const route = useRoute()
const router = useRouter()

const supplier = ref<any>(null)
const purchaseOrders = ref<any[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const summary = ref<any>(null)

const filters = ref({
  status: '',
  dateRange: null as any
})

const fetchSupplierPurchaseOrders = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    
    if (filters.value.status) {
      params.status = filters.value.status
    }
    
    if (filters.value.dateRange && filters.value.dateRange.length === 2) {
      params.start_date = filters.value.dateRange[0]
      params.end_date = filters.value.dateRange[1]
    }
    
    const response = await api.get(`/suppliers/${route.params.id}/purchase-orders`, { params })
    
    const data = response.data
    supplier.value = data.supplier
    purchaseOrders.value = data.purchase_orders || []
    total.value = data.pagination?.total || 0
    summary.value = data.summary
  } catch (error) {
    console.error('Error fetching purchase orders:', error)
    ElMessage.error('載入採購單資料時發生錯誤')
  } finally {
    loading.value = false
  }
}

const fetchPurchaseOrders = fetchSupplierPurchaseOrders

const resetFilters = () => {
  filters.value = {
    status: '',
    dateRange: null
  }
  currentPage.value = 1
  fetchPurchaseOrders()
}

const handleSortChange = ({ prop, order }: any) => {
  // Implement sorting logic if needed
  console.log('Sort:', prop, order)
  fetchPurchaseOrders()
}

const viewPurchaseOrder = (po: any) => {
  router.push(`/purchase-orders/${po.purchase_order_no}`)
}

const printPurchaseOrder = (po: any) => {
  // Implement print logic
  ElMessage.info('列印功能開發中')
}

const exportPurchaseOrders = () => {
  // Implement export logic
  ElMessage.info('匯出功能開發中')
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-TW')
}

const formatAmount = (amount: number) => {
  if (!amount) return '0'
  return amount.toLocaleString('zh-TW')
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    'order_created': 'info',
    'outputted': 'warning',
    'confirmed': 'primary',
    'shipped': '',
    'arrived': '',
    'completed': 'success',
    'cancelled': 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'draft': '草稿',
    'pending': '待處理',
    'order_created': '訂單建立',
    'outputted': '已輸出',
    'confirmed': '已確認',
    'purchased': '已採購',
    'shipped': '已出貨',
    'arrived': '已到貨',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

const getDeliveryStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    'not_shipped': 'info',
    'pending': 'warning',
    'shipped': '',
    'in_transit': 'primary',
    'foreign_customs': 'danger',
    'taiwan_customs': 'danger',
    'delivered': 'success',
    'delayed': 'danger'
  }
  return statusMap[status] || 'info'
}

const getDeliveryStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'not_shipped': '未發貨',
    'pending': '待交貨',
    'shipped': '已發貨',
    'in_transit': '運送中',
    'foreign_customs': '對方海關',
    'taiwan_customs': '台灣海關',
    'delivered': '已交貨',
    'delayed': '延遲'
  }
  return statusMap[status] || status || '待交貨'
}

onMounted(() => {
  fetchSupplierPurchaseOrders()
})
</script>

<style scoped>
.supplier-purchase-orders {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-left h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.supplier-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.supplier-name,
.supplier-contact,
.supplier-phone {
  display: flex;
  align-items: center;
  gap: 10px;
}

.supplier-card .label {
  color: #909399;
  font-size: 14px;
}

.supplier-card .value {
  color: #303133;
  font-size: 14px;
  font-weight: 500;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.summary-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  text-align: center;
}

.summary-value {
  font-size: 28px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 10px;
}

.summary-label {
  font-size: 14px;
  color: #909399;
}

.filters {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow: hidden;
}

.pagination {
  padding: 20px;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .summary-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .header {
    flex-direction: column;
    gap: 15px;
  }
}
</style>