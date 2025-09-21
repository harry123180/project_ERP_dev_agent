<template>
  <div class="project-expenditure">
    <!-- Expenditure Summary -->
    <el-row :gutter="20" class="summary-row">
      <el-col :span="8">
        <div class="summary-card">
          <div class="summary-title">總支出</div>
          <div class="summary-value total">
            {{ formatCurrency(expenditureSummary.total_amount) }}
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="summary-card">
          <div class="summary-title">交易筆數</div>
          <div class="summary-value count">
            {{ expenditureSummary.count }} 筆
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="summary-card">
          <div class="summary-title">供應商數</div>
          <div class="summary-value suppliers">
            {{ expenditureSummary.supplier_count }} 家
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Filters -->
    <el-card class="filter-card">
      <el-form :model="filters" inline class="filter-form">
        <el-form-item label="日期範圍">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="開始日期"
            end-placeholder="結束日期"
            @change="handleDateRangeChange"
            style="width: 240px"
          />
        </el-form-item>
        
        <el-form-item label="供應商">
          <el-select 
            v-model="filters.supplier_id" 
            placeholder="選擇供應商" 
            clearable
            style="width: 200px"
          >
            <el-option 
              v-for="supplier in suppliers" 
              :key="supplier.id"
              :label="supplier.supplier_name_zh"
              :value="supplier.id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="loadExpenditure" :icon="Search">
            搜尋
          </el-button>
          <el-button @click="resetFilters">重置</el-button>
          <el-button type="success" @click="exportData" :icon="Download">
            匯出
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Expenditure Chart -->
    <el-card v-if="chartData.length" class="chart-card">
      <template #header>
        <div class="card-header">
          <span>供應商支出分析</span>
          <el-radio-group v-model="chartType" size="small">
            <el-radio-button label="pie">圓餅圖</el-radio-button>
            <el-radio-button label="bar">柱狀圖</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      
      <div class="chart-container">
        <div ref="chartRef" style="width: 100%; height: 400px;"></div>
      </div>
    </el-card>

    <!-- Expenditure Table -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>支出明細</span>
          <div class="header-actions">
            <el-button 
              size="small" 
              type="primary" 
              @click="refreshData"
              :loading="loading"
              :icon="Refresh"
            >
              重新整理
            </el-button>
          </div>
        </div>
      </template>
      
      <DataTable
        :data="expenditures"
        :columns="columns"
        :loading="loading"
        :pagination="pagination"
        @page-change="handlePageChange"
        @sort-change="handleSortChange"
      >
        <template #amount="{ row }">
          <div class="amount-cell">
            {{ formatCurrency(row.amount) }}
          </div>
        </template>
        
        <template #supplier="{ row }">
          <div class="supplier-cell">
            <div class="supplier-name">{{ row.supplier.name }}</div>
            <div class="supplier-id">{{ row.supplier.supplier_id }}</div>
          </div>
        </template>
        
        <template #purchase_order="{ row }">
          <div class="po-cell">
            <el-link 
              type="primary" 
              @click="viewPurchaseOrder(row.purchase_order)"
            >
              {{ row.purchase_order.po_no }}
            </el-link>
            <div class="po-status">
              <StatusTag :status="getPOStatus(row.purchase_order.status)" />
            </div>
          </div>
        </template>
        
        <template #expenditure_date="{ row }">
          {{ formatDate(row.expenditure_date) }}
        </template>
        
        <template #created_at="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </DataTable>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Download, Refresh } from '@element-plus/icons-vue'
import DataTable from '@/components/DataTable.vue'
import StatusTag from '@/components/StatusTag.vue'
import { useProjectStore } from '@/stores/projectStore'
import { useSupplierStore } from '@/stores/supplierStore'
import type { Project, ProjectExpenditure } from '@/types/project'
import * as echarts from 'echarts'

interface Props {
  project: Project
}

const props = defineProps<Props>()

// Store instances
const projectStore = useProjectStore()
const supplierStore = useSupplierStore()

// Reactive data
const loading = ref(false)
const chartRef = ref()
const chartInstance = ref<echarts.ECharts | null>(null)
const chartType = ref('pie')
const dateRange = ref<[Date, Date] | null>(null)

// Filters
const filters = reactive({
  start_date: '',
  end_date: '',
  supplier_id: null,
  page: 1,
  page_size: 20
})

// Table columns
const columns = [
  { prop: 'expenditure_date', label: '支出日期', width: 120, sortable: true, slot: 'expenditure_date' },
  { prop: 'amount', label: '金額', width: 150, sortable: true, slot: 'amount' },
  { prop: 'supplier', label: '供應商', minWidth: 200, slot: 'supplier' },
  { prop: 'purchase_order', label: '採購訂單', width: 180, slot: 'purchase_order' },
  { prop: 'created_at', label: '建立時間', width: 160, slot: 'created_at' }
]

// Computed properties
const expenditures = computed(() => projectStore.currentProjectExpenditures)
const pagination = computed(() => projectStore.expenditurePagination)
const suppliers = computed(() => supplierStore.suppliers)

const expenditureSummary = computed(() => {
  const total_amount = expenditures.value.reduce((sum, exp) => sum + (exp.amount || 0), 0)
  const supplier_ids = new Set(expenditures.value.map(exp => exp.supplier.id))
  
  return {
    total_amount,
    count: expenditures.value.length,
    supplier_count: supplier_ids.size
  }
})

const chartData = computed(() => {
  const supplierExpenditure = new Map()
  
  expenditures.value.forEach(exp => {
    const supplierId = exp.supplier.id
    const supplierName = exp.supplier.name
    const amount = exp.amount || 0
    
    if (supplierExpenditure.has(supplierId)) {
      supplierExpenditure.set(supplierId, {
        name: supplierName,
        value: supplierExpenditure.get(supplierId).value + amount
      })
    } else {
      supplierExpenditure.set(supplierId, {
        name: supplierName,
        value: amount
      })
    }
  })
  
  return Array.from(supplierExpenditure.values())
    .sort((a, b) => b.value - a.value)
    .slice(0, 10) // Top 10 suppliers
})

// Methods
const loadExpenditure = async () => {
  loading.value = true
  try {
    await projectStore.fetchProjectExpenditure(props.project.id, filters)
  } catch (error) {
    ElMessage.error('載入支出記錄失敗')
  } finally {
    loading.value = false
  }
}

const loadSuppliers = async () => {
  try {
    await supplierStore.fetchSuppliers()
  } catch (error) {
    console.error('載入供應商列表失敗:', error)
  }
}

const resetFilters = () => {
  dateRange.value = null
  Object.assign(filters, {
    start_date: '',
    end_date: '',
    supplier_id: null,
    page: 1,
    page_size: 20
  })
  loadExpenditure()
}

const refreshData = () => {
  loadExpenditure()
}

const handleDateRangeChange = (dates: [Date, Date] | null) => {
  if (dates) {
    filters.start_date = dates[0].toISOString().split('T')[0]
    filters.end_date = dates[1].toISOString().split('T')[0]
  } else {
    filters.start_date = ''
    filters.end_date = ''
  }
}

const handlePageChange = (page: number) => {
  filters.page = page
  loadExpenditure()
}

const handleSortChange = (sort: any) => {
  loadExpenditure()
}

const exportData = async () => {
  try {
    const data = expenditures.value.map(exp => ({
      '專案代碼': props.project.project_code,
      '專案名稱': props.project.project_name,
      '支出日期': formatDate(exp.expenditure_date),
      '供應商': exp.supplier.name,
      '採購訂單': exp.purchase_order.po_no,
      '金額': exp.amount,
      '建立時間': formatDateTime(exp.created_at)
    }))
    
    // Here you would implement actual export functionality
    // For now, just show success message
    ElMessage.success('匯出功能開發中')
  } catch (error) {
    ElMessage.error('匯出失敗')
  }
}

const viewPurchaseOrder = (po: any) => {
  // Navigate to purchase order detail
  ElMessage.info(`檢視採購訂單: ${po.po_no}`)
}

const initChart = () => {
  if (!chartRef.value) return
  
  chartInstance.value = echarts.init(chartRef.value)
  renderChart()
}

const renderChart = () => {
  if (!chartInstance.value || !chartData.value.length) return
  
  const option = chartType.value === 'pie' ? getPieChartOption() : getBarChartOption()
  chartInstance.value.setOption(option)
}

const getPieChartOption = () => ({
  title: {
    text: '供應商支出分佈',
    left: 'center',
    top: 20,
    textStyle: {
      fontSize: 16,
      fontWeight: 'bold'
    }
  },
  tooltip: {
    trigger: 'item',
    formatter: (params: any) => {
      return `${params.name}<br/>金額: ${formatCurrency(params.value)}<br/>比例: ${params.percent}%`
    }
  },
  legend: {
    type: 'scroll',
    orient: 'vertical',
    right: 10,
    top: 60,
    bottom: 20
  },
  series: [{
    name: '支出金額',
    type: 'pie',
    radius: ['40%', '70%'],
    center: ['40%', '50%'],
    avoidLabelOverlap: false,
    label: {
      show: false
    },
    emphasis: {
      label: {
        show: true,
        fontSize: '14',
        fontWeight: 'bold'
      }
    },
    labelLine: {
      show: false
    },
    data: chartData.value
  }]
})

const getBarChartOption = () => ({
  title: {
    text: '供應商支出分析',
    left: 'center',
    textStyle: {
      fontSize: 16,
      fontWeight: 'bold'
    }
  },
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    },
    formatter: (params: any) => {
      const data = params[0]
      return `${data.name}<br/>金額: ${formatCurrency(data.value)}`
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: chartData.value.map(item => item.name),
    axisLabel: {
      rotate: 45,
      fontSize: 12
    }
  },
  yAxis: {
    type: 'value',
    axisLabel: {
      formatter: (value: number) => {
        return (value / 1000) + 'K'
      }
    }
  },
  series: [{
    name: '支出金額',
    type: 'bar',
    data: chartData.value.map(item => item.value),
    itemStyle: {
      color: '#409EFF'
    }
  }]
})

const getPOStatus = (status: string) => {
  const statusMap: Record<string, any> = {
    'draft': { text: '草稿', type: 'info' },
    'confirmed': { text: '已確認', type: 'primary' },
    'shipped': { text: '已發貨', type: 'warning' },
    'received': { text: '已收貨', type: 'success' },
    'cancelled': { text: '已取消', type: 'danger' }
  }
  return statusMap[status] || { text: status, type: 'default' }
}

const formatCurrency = (amount: number | null | undefined) => {
  if (!amount) return 'NT$ 0'
  return `NT$ ${amount.toLocaleString()}`
}

const formatDate = (dateString: string | null | undefined) => {
  if (!dateString) return '—'
  return new Date(dateString).toLocaleDateString('zh-TW')
}

const formatDateTime = (dateString: string | null | undefined) => {
  if (!dateString) return '—'
  return new Date(dateString).toLocaleString('zh-TW')
}

// Watchers
watch(chartType, () => {
  nextTick(() => {
    renderChart()
  })
})

watch(chartData, () => {
  nextTick(() => {
    renderChart()
  })
}, { deep: true })

// Lifecycle
onMounted(() => {
  loadExpenditure()
  loadSuppliers()
  nextTick(() => {
    initChart()
  })
})
</script>

<style scoped>
.project-expenditure {
  padding: 10px;
}

.summary-row {
  margin-bottom: 20px;
}

.summary-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 10px;
  text-align: center;
}

.summary-title {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 10px;
}

.summary-value {
  font-size: 24px;
  font-weight: bold;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  margin-bottom: 0;
}

.chart-card, .table-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.chart-container {
  padding: 20px 0;
}

.amount-cell {
  font-weight: bold;
  color: #F56C6C;
}

.supplier-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.supplier-name {
  font-weight: 500;
  color: #333;
}

.supplier-id {
  font-size: 12px;
  color: #666;
}

.po-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.po-status {
  align-self: flex-start;
}
</style>