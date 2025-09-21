<template>
  <div class="price-history">
    <div class="page-header">
      <h1 class="page-title">歷史價格查詢</h1>
      <div class="header-actions">
        <el-button type="success" @click="exportData">
          <el-icon><Download /></el-icon>
          匯出資料
        </el-button>
        <el-button type="primary" @click="refreshData">
          <el-icon><Refresh /></el-icon>
          重新整理
        </el-button>
      </div>
    </div>

    <div class="filters">
      <el-form :model="filters" inline>
        <el-form-item label="品項編號">
          <el-input 
            v-model="filters.itemCode" 
            placeholder="輸入品項編號"
            clearable
          />
        </el-form-item>
        <el-form-item label="品項名稱">
          <el-input 
            v-model="filters.itemName" 
            placeholder="輸入品項名稱"
            clearable
          />
        </el-form-item>
        <el-form-item label="供應商">
          <el-select v-model="filters.supplier" placeholder="選擇供應商" clearable>
            <el-option label="全部" value="" />
            <el-option label="台積電材料供應商" value="supplier_a" />
            <el-option label="精密機械公司" value="supplier_b" />
            <el-option label="電子元件供應商" value="supplier_c" />
          </el-select>
        </el-form-item>
        <el-form-item label="價格區間">
          <el-input-number 
            v-model="filters.minPrice" 
            placeholder="最低價格"
            :min="0"
            controls-position="right"
          />
          <span style="margin: 0 8px;">~</span>
          <el-input-number 
            v-model="filters.maxPrice" 
            placeholder="最高價格"
            :min="0"
            controls-position="right"
          />
        </el-form-item>
        <el-form-item label="時間範圍">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            start-placeholder="開始日期"
            end-placeholder="結束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜尋</el-button>
          <el-button @click="resetFilters">重設</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-container">
      <el-table 
        :data="priceHistoryData" 
        :loading="loading"
        stripe
        @row-click="viewPriceDetail"
      >
        <el-table-column prop="item_code" label="品項編號" width="120" />
        <el-table-column prop="item_name" label="品項名稱" width="200" />
        <el-table-column prop="supplier_name" label="供應商" width="180" />
        <el-table-column prop="unit_price" label="單價" width="100">
          <template #default="{ row }">
            {{ formatCurrency(row.unit_price) }}
          </template>
        </el-table-column>
        <el-table-column prop="currency" label="幣別" width="80" />
        <el-table-column prop="quantity" label="採購數量" width="100" />
        <el-table-column prop="total_amount" label="總金額" width="120">
          <template #default="{ row }">
            {{ formatCurrency(row.total_amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="purchase_date" label="採購日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.purchase_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="po_number" label="採購單號" width="140" />
        <el-table-column prop="price_trend" label="價格趨勢" width="100">
          <template #default="{ row }">
            <el-tag :type="getPriceTrendType(row.price_trend)">
              {{ getPriceTrendText(row.price_trend) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click.stop="viewPriceDetail(row)">詳情</el-button>
            <el-button size="small" type="primary" @click.stop="viewTrend(row)">
              趨勢圖
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
          background
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </div>

    <!-- Price Trend Chart Dialog -->
    <el-dialog
      v-model="trendDialogVisible"
      :title="`${selectedItem.item_name} - 價格趨勢圖`"
      width="800px"
    >
      <div class="trend-chart-container">
        <div class="chart-placeholder">
          <el-icon class="chart-icon"><TrendCharts /></el-icon>
          <p>價格趨勢圖表將在此顯示</p>
          <p class="chart-description">
            顯示該品項在不同時間點的價格變化趨勢，包含最高價、最低價、平均價等統計資訊
          </p>
        </div>
      </div>
      <template #footer>
        <el-button @click="trendDialogVisible = false">關閉</el-button>
      </template>
    </el-dialog>

    <!-- Price Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      title="價格詳情"
      width="600px"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="品項編號">{{ selectedItem.item_code }}</el-descriptions-item>
        <el-descriptions-item label="品項名稱">{{ selectedItem.item_name }}</el-descriptions-item>
        <el-descriptions-item label="供應商">{{ selectedItem.supplier_name }}</el-descriptions-item>
        <el-descriptions-item label="採購單號">{{ selectedItem.po_number }}</el-descriptions-item>
        <el-descriptions-item label="單價">{{ formatCurrency(selectedItem.unit_price) }}</el-descriptions-item>
        <el-descriptions-item label="幣別">{{ selectedItem.currency }}</el-descriptions-item>
        <el-descriptions-item label="採購數量">{{ selectedItem.quantity }}</el-descriptions-item>
        <el-descriptions-item label="總金額">{{ formatCurrency(selectedItem.total_amount) }}</el-descriptions-item>
        <el-descriptions-item label="採購日期">{{ formatDate(selectedItem.purchase_date) }}</el-descriptions-item>
        <el-descriptions-item label="價格趨勢">
          <el-tag :type="getPriceTrendType(selectedItem.price_trend)">
            {{ getPriceTrendText(selectedItem.price_trend) }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <div class="price-statistics">
        <h4>價格統計資訊</h4>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-statistic title="歷史最高價" :value="selectedItem.max_price" :precision="2" prefix="$" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="歷史最低價" :value="selectedItem.min_price" :precision="2" prefix="$" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="平均價格" :value="selectedItem.avg_price" :precision="2" prefix="$" />
          </el-col>
        </el-row>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">關閉</el-button>
        <el-button type="primary" @click="viewTrend(selectedItem)">查看趨勢圖</el-button>
      </template>
    </el-dialog>

    <!-- Development Notice -->
    <div class="development-notice">
      <el-alert
        title="功能開發中"
        description="歷史價格查詢功能正在開發中，目前顯示的是模擬資料。完整功能將包含價格趨勢分析、供應商比價、價格預測等。"
        type="info"
        show-icon
        :closable="false"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Refresh, TrendCharts } from '@element-plus/icons-vue'
import { formatDate, formatCurrency } from '@/utils/format'

// Reactive data
const loading = ref(false)
const priceHistoryData = ref([])
const trendDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const selectedItem = ref({})

const filters = ref({
  itemCode: '',
  itemName: '',
  supplier: '',
  minPrice: null,
  maxPrice: null,
  dateRange: []
})

const pagination = ref({
  page: 1,
  size: 20,
  total: 0
})

// Mock data for development
const mockPriceData = [
  {
    id: '1',
    item_code: 'IC001',
    item_name: '半導體材料A',
    supplier_name: '台積電材料供應商',
    unit_price: 150.00,
    currency: 'TWD',
    quantity: 100,
    total_amount: 15000.00,
    purchase_date: '2025-01-05',
    po_number: 'PO202501001',
    price_trend: 'up',
    max_price: 180.00,
    min_price: 120.00,
    avg_price: 145.00
  },
  {
    id: '2',
    item_code: 'MC002',
    item_name: '精密零件B',
    supplier_name: '精密機械公司',
    unit_price: 250.00,
    currency: 'TWD',
    quantity: 50,
    total_amount: 12500.00,
    purchase_date: '2025-01-03',
    po_number: 'PO202501002',
    price_trend: 'down',
    max_price: 280.00,
    min_price: 240.00,
    avg_price: 255.00
  },
  {
    id: '3',
    item_code: 'EC003',
    item_name: 'IC晶片套裝',
    supplier_name: '電子元件供應商',
    unit_price: 500.00,
    currency: 'TWD',
    quantity: 20,
    total_amount: 10000.00,
    purchase_date: '2025-01-01',
    po_number: 'PO202501003',
    price_trend: 'stable',
    max_price: 520.00,
    min_price: 480.00,
    avg_price: 500.00
  },
  {
    id: '4',
    item_code: 'IC001',
    item_name: '半導體材料A',
    supplier_name: '台積電材料供應商',
    unit_price: 145.00,
    currency: 'TWD',
    quantity: 150,
    total_amount: 21750.00,
    purchase_date: '2024-12-20',
    po_number: 'PO202412020',
    price_trend: 'stable',
    max_price: 180.00,
    min_price: 120.00,
    avg_price: 145.00
  }
]

// Methods
const loadData = async () => {
  loading.value = true
  try {
    // Simulate API call with mock data
    await new Promise(resolve => setTimeout(resolve, 500))
    
    let filteredData = [...mockPriceData]
    
    // Apply filters
    if (filters.value.itemCode) {
      filteredData = filteredData.filter(item => 
        item.item_code.toLowerCase().includes(filters.value.itemCode.toLowerCase())
      )
    }
    
    if (filters.value.itemName) {
      filteredData = filteredData.filter(item => 
        item.item_name.toLowerCase().includes(filters.value.itemName.toLowerCase())
      )
    }
    
    if (filters.value.supplier) {
      filteredData = filteredData.filter(item => item.supplier_name.includes(filters.value.supplier))
    }
    
    if (filters.value.minPrice !== null) {
      filteredData = filteredData.filter(item => item.unit_price >= filters.value.minPrice)
    }
    
    if (filters.value.maxPrice !== null) {
      filteredData = filteredData.filter(item => item.unit_price <= filters.value.maxPrice)
    }
    
    if (filters.value.dateRange && filters.value.dateRange.length === 2) {
      const [startDate, endDate] = filters.value.dateRange
      filteredData = filteredData.filter(item => {
        const itemDate = new Date(item.purchase_date)
        return itemDate >= new Date(startDate) && itemDate <= new Date(endDate)
      })
    }
    
    priceHistoryData.value = filteredData
    pagination.value.total = filteredData.length
  } catch (error) {
    console.error('載入價格歷史失敗:', error)
    ElMessage.error('載入價格歷史失敗')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.value = {
    itemCode: '',
    itemName: '',
    supplier: '',
    minPrice: null,
    maxPrice: null,
    dateRange: []
  }
  pagination.value.page = 1
  loadData()
}

const refreshData = () => {
  loadData()
  ElMessage.success('資料已重新整理')
}

const exportData = () => {
  ElMessage.success('價格資料匯出功能開發中')
}

const viewPriceDetail = (row: any) => {
  selectedItem.value = row
  detailDialogVisible.value = true
}

const viewTrend = (row: any) => {
  selectedItem.value = row
  trendDialogVisible.value = true
  detailDialogVisible.value = false
}

const getPriceTrendType = (trend: string) => {
  const trendMap: Record<string, string> = {
    up: 'danger',
    down: 'success',
    stable: 'info'
  }
  return trendMap[trend] || ''
}

const getPriceTrendText = (trend: string) => {
  const trendMap: Record<string, string> = {
    up: '上漲',
    down: '下跌',
    stable: '穩定'
  }
  return trendMap[trend] || trend
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.price-history {
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
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.trend-chart-container {
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 4px;
}

.chart-placeholder {
  text-align: center;
  color: #909399;

  .chart-icon {
    font-size: 48px;
    margin-bottom: 16px;
  }

  p {
    margin: 8px 0;
  }

  .chart-description {
    font-size: 12px;
    color: #c0c4cc;
  }
}

.price-statistics {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;

  h4 {
    margin: 0 0 16px 0;
    color: #303133;
  }
}

.development-notice {
  margin-top: 20px;
}

:deep(.el-alert__description) {
  margin-top: 8px;
  font-size: 13px;
}

:deep(.el-input-number) {
  width: 120px;
}

:deep(.el-date-editor) {
  width: 240px;
}
</style>