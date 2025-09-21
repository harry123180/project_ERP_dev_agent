<template>
  <div class="invoice-management">
    <div class="page-header">
      <h1>請款管理</h1>
      <p class="subtitle">智能請款單查核系統</p>
    </div>

    <!-- Search Section -->
    <el-card class="search-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="header-title">查詢條件</span>
        </div>
      </template>

      <el-form :model="searchForm" ref="searchFormRef" :inline="true" class="search-form">
        <el-form-item
          label="供應商"
          prop="supplierId"
          :rules="[{ required: true, message: '請選擇供應商', trigger: 'change' }]"
        >
          <el-select
            v-model="searchForm.supplierId"
            placeholder="請選擇供應商"
            filterable
            remote
            :remote-method="searchSuppliers"
            :loading="suppliersLoading"
            style="width: 280px"
            clearable
            @change="onSupplierChange"
          >
            <el-option
              v-for="supplier in suppliers"
              :key="supplier.supplier_id"
              :label="`${supplier.supplier_name_zh} (${supplier.supplier_id})`"
              :value="supplier.supplier_id"
            >
              <div class="supplier-option">
                <div class="supplier-name">{{ supplier.supplier_name_zh }}</div>
                <div class="supplier-details">{{ supplier.supplier_id }} | {{ supplier.supplier_region === 'domestic' ? '國內' : '國外' }}</div>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item
          label="請款月份"
          prop="invoiceMonth"
          :rules="[{ required: true, message: '請選擇請款月份', trigger: 'change' }]"
        >
          <el-date-picker
            v-model="searchForm.invoiceMonth"
            type="month"
            placeholder="選擇請款月份"
            format="YYYY年MM月"
            value-format="YYYY-MM"
            style="width: 200px"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="handleSearch"
            :disabled="!canSearch"
            :loading="searching"
          >
            <el-icon><Search /></el-icon>
            搜尋
          </el-button>
          <el-button @click="resetForm">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- Date Range Display -->
      <div v-if="dateRange.startDate" class="date-range-info">
        <el-alert
          :title="`搜尋範圍：${dateRange.startDate} ~ ${dateRange.endDate} (付款條件：${dateRange.paymentDays}天)`"
          type="info"
          show-icon
          :closable="false"
        />
      </div>
    </el-card>

    <!-- Results Section -->
    <el-card v-if="searchResults.length > 0 || hasSearched" class="results-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="header-title">查核結果</span>
          <div class="header-actions">
            <span class="result-summary">
              共找到 {{ searchResults.length }} 筆採購記錄，總金額：NT$ {{ totalAmount.toLocaleString() }}
            </span>
            <el-button
              type="success"
              @click="exportToExcel"
              :disabled="searchResults.length === 0"
              :loading="exporting"
            >
              <el-icon><Download /></el-icon>
              匯出 Excel
            </el-button>
          </div>
        </div>
      </template>

      <!-- No Results -->
      <el-empty
        v-if="hasSearched && searchResults.length === 0"
        description="未找到符合條件的採購記錄"
        :image-size="120"
      />

      <!-- Results List -->
      <div v-else class="results-container">
        <div
          v-for="po in searchResults"
          :key="po.purchase_order_no"
          class="po-card"
          :class="{ 'expanded': expandedCards.includes(po.purchase_order_no) }"
        >
          <!-- PO Header -->
          <div class="po-header" @click="toggleCard(po.purchase_order_no)">
            <div class="po-info">
              <div class="po-number">{{ po.purchase_order_no }}</div>
              <div class="po-date">{{ formatDate(po.order_date) }}</div>
              <div class="po-status" :class="`status-${po.purchase_status}`">
                {{ getStatusText(po.purchase_status) }}
              </div>
            </div>
            <div class="po-amount">
              <div class="amount-main">NT$ {{ po.grand_total_int?.toLocaleString() || 0 }}</div>
              <div class="amount-details">
                未稅：{{ po.subtotal_int?.toLocaleString() || 0 }} |
                稅額：{{ po.tax_decimal1?.toLocaleString() || 0 }}
              </div>
            </div>
            <div class="po-toggle">
              <el-icon>
                <component :is="expandedCards.includes(po.purchase_order_no) ? 'ArrowUp' : 'ArrowDown'" />
              </el-icon>
            </div>
          </div>

          <!-- PO Details (Expandable) -->
          <el-collapse-transition>
            <div v-show="expandedCards.includes(po.purchase_order_no)" class="po-details">
              <el-divider style="margin: 12px 0;" />

              <!-- Purchase Order Information -->
              <div class="po-info-grid">
                <div class="info-row">
                  <label>報價單號：</label>
                  <span>{{ po.quotation_no || '無' }}</span>
                </div>
                <div class="info-row">
                  <label>交貨地址：</label>
                  <span>{{ po.delivery_address || '無' }}</span>
                </div>
                <div class="info-row">
                  <label>建立人員：</label>
                  <span>{{ po.creator_name || '系統' }}</span>
                </div>
                <div class="info-row">
                  <label>確認人員：</label>
                  <span>{{ po.confirm_purchaser_name || '未確認' }}</span>
                </div>
              </div>

              <!-- Items List -->
              <div class="items-section">
                <h4>採購明細 ({{ po.items?.length || 0 }} 項)</h4>
                <el-table :data="po.items" size="small" stripe>
                  <el-table-column prop="item_name" label="項目名稱" min-width="150" />
                  <el-table-column prop="item_specification" label="規格說明" min-width="120" />
                  <el-table-column prop="item_quantity" label="數量" width="80" align="right">
                    <template #default="scope">
                      {{ scope.row.item_quantity }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="item_unit" label="單位" width="60" />
                  <el-table-column prop="unit_price" label="單價" width="100" align="right">
                    <template #default="scope">
                      {{ scope.row.unit_price?.toLocaleString() }}
                    </template>
                  </el-table-column>
                  <el-table-column label="小計" width="120" align="right">
                    <template #default="scope">
                      NT$ {{ scope.row.line_subtotal?.toLocaleString() }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="line_status" label="狀態" width="80">
                    <template #default="scope">
                      <el-tag :type="getLineStatusType(scope.row.line_status)" size="small">
                        {{ getLineStatusText(scope.row.line_status) }}
                      </el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <!-- Notes -->
              <div v-if="po.notes" class="notes-section">
                <label>備註：</label>
                <p>{{ po.notes }}</p>
              </div>
            </div>
          </el-collapse-transition>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Search, Refresh, Download, ArrowUp, ArrowDown } from '@element-plus/icons-vue'
import { suppliersApi } from '@/api/suppliers'
import { accountingApi } from '@/api/accounting'
import * as XLSX from 'xlsx'

// Interfaces
interface Supplier {
  supplier_id: string
  supplier_name_zh: string
  supplier_name_en?: string
  supplier_region: 'domestic' | 'international'
  payment_terms?: string
}

interface PurchaseOrderItem {
  detail_id: number
  item_name: string
  item_specification?: string
  item_quantity: number
  item_unit: string
  unit_price: number
  line_subtotal: number
  line_status: string
}

interface PurchaseOrder {
  purchase_order_no: string
  supplier_name: string
  order_date: string
  purchase_status: string
  subtotal_int: number
  tax_decimal1: number
  grand_total_int: number
  quotation_no?: string
  delivery_address?: string
  creator_name?: string
  confirm_purchaser_name?: string
  notes?: string
  items?: PurchaseOrderItem[]
}

interface DateRange {
  startDate: string
  endDate: string
  paymentDays: number
}

// Reactive data
const searchFormRef = ref<FormInstance>()
const searchForm = reactive({
  supplierId: '',
  invoiceMonth: ''
})

const suppliers = ref<Supplier[]>([])
const suppliersLoading = ref(false)
const searching = ref(false)
const exporting = ref(false)
const hasSearched = ref(false)

const searchResults = ref<PurchaseOrder[]>([])
const expandedCards = ref<string[]>([])
const dateRange = ref<DateRange>({
  startDate: '',
  endDate: '',
  paymentDays: 0
})

// Computed properties
const canSearch = computed(() => {
  return searchForm.supplierId && searchForm.invoiceMonth
})

const totalAmount = computed(() => {
  return searchResults.value.reduce((sum, po) => sum + (po.grand_total_int || 0), 0)
})

// Methods
const searchSuppliers = async (query?: string) => {
  if (!query) {
    loadAllSuppliers()
    return
  }

  suppliersLoading.value = true
  try {
    const response = await suppliersApi.getSuppliers({ search: query })
    suppliers.value = response.items || []
  } catch (error) {
    console.error('搜尋供應商失敗:', error)
    ElMessage.error('搜尋供應商失敗')
  } finally {
    suppliersLoading.value = false
  }
}

const loadAllSuppliers = async () => {
  suppliersLoading.value = true
  try {
    suppliers.value = await suppliersApi.getActiveSuppliers()
  } catch (error) {
    console.error('載入供應商失敗:', error)
    ElMessage.error('載入供應商失敗')
  } finally {
    suppliersLoading.value = false
  }
}

const onSupplierChange = () => {
  // Clear previous results when supplier changes
  searchResults.value = []
  expandedCards.value = []
  hasSearched.value = false
  dateRange.value = { startDate: '', endDate: '', paymentDays: 0 }
}

const handleSearch = async () => {
  if (!searchFormRef.value) return

  const valid = await searchFormRef.value.validate().catch(() => false)
  if (!valid) return

  searching.value = true
  expandedCards.value = []

  try {
    const data = await accountingApi.searchInvoiceManagement({
      supplier_id: searchForm.supplierId,
      invoice_month: searchForm.invoiceMonth
    })

    searchResults.value = data.purchase_orders || []
    dateRange.value = {
      startDate: data.search_period?.start_date || '',
      endDate: data.search_period?.end_date || '',
      paymentDays: data.search_period?.payment_days || 0
    }

    hasSearched.value = true

    if (searchResults.value.length === 0) {
      ElMessage.info('未找到符合條件的採購記錄')
    } else {
      ElMessage.success(`找到 ${searchResults.value.length} 筆採購記錄`)
    }
  } catch (error) {
    console.error('搜尋失敗:', error)
    ElMessage.error('搜尋採購記錄失敗，請檢查網路連線')
    searchResults.value = []
    hasSearched.value = true
  } finally {
    searching.value = false
  }
}

const resetForm = () => {
  searchForm.supplierId = ''
  searchForm.invoiceMonth = ''
  searchResults.value = []
  expandedCards.value = []
  hasSearched.value = false
  dateRange.value = { startDate: '', endDate: '', paymentDays: 0 }
  searchFormRef.value?.clearValidate()
}

const toggleCard = (poNumber: string) => {
  const index = expandedCards.value.indexOf(poNumber)
  if (index > -1) {
    expandedCards.value.splice(index, 1)
  } else {
    expandedCards.value.push(poNumber)
  }
}

const exportToExcel = async () => {
  if (searchResults.value.length === 0) return

  exporting.value = true

  try {
    const blob = await accountingApi.exportInvoiceManagement({
      supplier_id: searchForm.supplierId,
      invoice_month: searchForm.invoiceMonth,
      search_results: searchResults.value.map(po => po.purchase_order_no)
    })

    // Create download link
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url

    // Generate filename
    const supplierName = suppliers.value.find(s => s.supplier_id === searchForm.supplierId)?.supplier_name_zh || searchForm.supplierId
    const filename = `請款管理-${supplierName}-${searchForm.invoiceMonth}.xlsx`
    link.download = filename

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('Excel 檔案下載完成')
  } catch (error) {
    console.error('匯出失敗:', error)
    ElMessage.error('匯出 Excel 失敗，請稍後重試')
  } finally {
    exporting.value = false
  }
}

// Utility functions
const formatDate = (date: string) => {
  if (!date) return '無'
  return new Date(date).toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': '待處理',
    'confirmed': '已確認',
    'order_created': '已建單',
    'outputted': '已輸出',
    'purchased': '已採購',
    'shipped': '已出貨',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

const getLineStatusText = (status: string) => {
  // Handle empty or falsy values
  if (!status || status.trim() === '') {
    return '未知'
  }

  const statusMap: Record<string, string> = {
    'active': '進行中',
    'cancelled': '已取消',
    'completed': '已完成'
  }
  return statusMap[status] || status
}

const getLineStatusType = (status: string) => {
  // Handle empty or falsy values
  if (!status || status.trim() === '') {
    return 'info'
  }

  const typeMap: Record<string, string> = {
    'active': 'primary',
    'cancelled': 'danger',
    'completed': 'success'
  }
  return typeMap[status] || 'info'
}

// Lifecycle
onMounted(() => {
  loadAllSuppliers()
})
</script>

<style scoped>
.invoice-management {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 28px;
  font-weight: 600;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.search-card, .results-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-weight: 600;
  font-size: 16px;
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.result-summary {
  font-size: 14px;
  color: #606266;
}

.search-form {
  margin-bottom: 16px;
}

.supplier-option {
  line-height: 1.4;
}

.supplier-name {
  font-weight: 500;
  color: #303133;
}

.supplier-details {
  font-size: 12px;
  color: #909399;
}

.date-range-info {
  margin-top: 16px;
}

.results-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.po-card {
  border: 1px solid #EBEEF5;
  border-radius: 8px;
  transition: all 0.2s ease;
  background: #ffffff;
}

.po-card:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.po-card.expanded {
  border-color: #409EFF;
}

.po-header {
  display: flex;
  align-items: center;
  padding: 16px;
  cursor: pointer;
  user-select: none;
}

.po-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
}

.po-number {
  font-weight: 600;
  color: #303133;
  font-size: 16px;
}

.po-date {
  color: #606266;
  font-size: 14px;
}

.po-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-pending {
  background: #FDF6EC;
  color: #E6A23C;
}

.status-confirmed, .status-order_created {
  background: #EDF2FC;
  color: #409EFF;
}

.status-purchased, .status-outputted {
  background: #F0F9FF;
  color: #67C23A;
}

.status-shipped {
  background: #F5F7FA;
  color: #909399;
}

.status-cancelled {
  background: #FEF0F0;
  color: #F56C6C;
}

.po-amount {
  text-align: right;
  margin-right: 16px;
}

.amount-main {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.amount-details {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.po-toggle {
  color: #C0C4CC;
}

.po-details {
  padding: 0 16px 16px 16px;
}

.po-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.info-row {
  display: flex;
}

.info-row label {
  font-weight: 500;
  color: #606266;
  min-width: 80px;
  margin-right: 8px;
}

.info-row span {
  color: #303133;
}

.items-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.notes-section {
  margin-top: 16px;
  padding: 12px;
  background: #F5F7FA;
  border-radius: 4px;
}

.notes-section label {
  font-weight: 500;
  color: #606266;
  margin-bottom: 8px;
  display: block;
}

.notes-section p {
  margin: 0;
  color: #303133;
  line-height: 1.6;
}

:deep(.el-table .el-table__cell) {
  padding: 8px 0;
}

:deep(.el-table th.el-table__cell) {
  background: #FAFAFA;
  font-weight: 600;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #EBEEF5;
}

:deep(.el-card__body) {
  padding: 20px;
}
</style>