<template>
  <div class="data-table">
    <!-- Filter Bar -->
    <div v-if="showFilterBar" class="filter-bar">
      <el-form
        :model="filters"
        :inline="true"
        @submit.prevent="handleSearch"
      >
        <el-form-item
          v-for="field in filterFields"
          :key="field.prop"
          :label="field.label"
        >
          <el-input
            v-if="field.type === 'input'"
            v-model="filters[field.prop]"
            :placeholder="field.placeholder"
            :clearable="field.clearable !== false"
            style="width: 200px"
          />
          <el-select
            v-else-if="field.type === 'select'"
            v-model="filters[field.prop]"
            :placeholder="field.placeholder"
            :clearable="field.clearable !== false"
            :filterable="field.filterable"
            :multiple="field.multiple"
            style="width: 200px"
          >
            <el-option
              v-for="option in field.options"
              :key="option.value"
              :label="option.label"
              :value="option.value"
              :disabled="option.disabled"
            />
          </el-select>
          <el-date-picker
            v-else-if="field.type === 'date'"
            v-model="filters[field.prop]"
            type="date"
            :placeholder="field.placeholder"
            :format="field.format || 'YYYY-MM-DD'"
            :value-format="field.valueFormat || 'YYYY-MM-DD'"
            style="width: 200px"
          />
          <el-date-picker
            v-else-if="field.type === 'daterange'"
            v-model="filters[field.prop]"
            type="daterange"
            range-separator="至"
            start-placeholder="開始日期"
            end-placeholder="結束日期"
            :format="field.format || 'YYYY-MM-DD'"
            :value-format="field.valueFormat || 'YYYY-MM-DD'"
            style="width: 250px"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- Toolbar -->
    <div v-if="showToolbar" class="table-toolbar">
      <div class="toolbar-left">
        <slot name="toolbar-left">
          <el-button
            v-if="showCreate"
            type="primary"
            @click="$emit('create')"
          >
            <el-icon><Plus /></el-icon>
            新增
          </el-button>
        </slot>
      </div>
      <div class="toolbar-right">
        <slot name="toolbar-right">
          <el-button
            v-if="showExport"
            @click="$emit('export')"
          >
            <el-icon><Download /></el-icon>
            導出
          </el-button>
          <el-button
            @click="handleRefresh"
          >
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </slot>
      </div>
    </div>

    <!-- Table -->
    <el-table
      :data="data"
      :loading="loading"
      stripe
      border
      :height="tableHeight"
      :max-height="maxHeight"
      :show-summary="showSummary"
      :summary-method="summaryMethod"
      :cell-class-name="getCellClassName"
      @selection-change="handleSelectionChange"
      @sort-change="handleSortChange"
      v-bind="$attrs"
    >
      <!-- Selection Column -->
      <el-table-column
        v-if="showSelection"
        type="selection"
        width="55"
        align="center"
        fixed="left"
      />

      <!-- Index Column -->
      <el-table-column
        v-if="showIndex"
        type="index"
        label="序號"
        width="60"
        align="center"
        fixed="left"
      />

      <!-- Data Columns -->
      <el-table-column
        v-for="column in columns"
        :key="column.prop || column.type"
        :prop="column.prop"
        :label="column.label"
        :width="column.width"
        :min-width="column.minWidth"
        :fixed="column.fixed"
        :sortable="column.sortable"
        :align="column.align || 'left'"
        :header-align="column.headerAlign || column.align || 'center'"
        :show-overflow-tooltip="column.showOverflowTooltip !== false"
        :resizable="column.resizable !== false"
        :formatter="column.formatter"
      >
        <template v-if="column.type === 'status'" #default="{ row }">
          <el-tag
            :type="getStatusType(row[column.prop!])"
            size="small"
          >
            {{ getStatusLabel(row[column.prop!]) }}
          </el-tag>
        </template>
        
        <template v-else-if="column.type === 'money'" #default="{ row }">
          <span class="money">{{ formatMoney(row[column.prop!]) }}</span>
        </template>
        
        <template v-else-if="column.type === 'date'" #default="{ row }">
          {{ formatDate(row[column.prop!]) }}
        </template>
        
        <template v-else-if="column.type === 'actions'" #default="{ row, $index }">
          <slot name="actions" :row="row" :index="$index">
            <el-button
              v-for="action in getVisibleActions(row)"
              :key="action.label"
              :type="action.type || 'primary'"
              :disabled="getActionDisabled(action, row)"
              size="small"
              link
              @click="action.handler(row, $index)"
            >
              <el-icon v-if="action.icon">
                <component :is="action.icon" />
              </el-icon>
              {{ action.label }}
            </el-button>
          </slot>
        </template>
        
        <template v-else-if="$slots[`column-${column.prop}`]" #default="{ row, $index }">
          <slot :name="`column-${column.prop}`" :row="row" :index="$index" />
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div v-if="showPagination" class="table-pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="pageSizes"
        :layout="paginationLayout"
        :prev-text="'上一頁'"
        :next-text="'下一頁'"
        background
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      >
        <template #sizes>
          <el-select
            :model-value="pageSize"
            @update:model-value="handleSizeChange"
            style="width: 100px"
            size="small"
          >
            <el-option
              v-for="size in pageSizes"
              :key="size"
              :label="`${size}筆/頁`"
              :value="size"
            />
          </el-select>
        </template>
        <template #total>
          <span class="pagination-total">共 {{ total }} 筆</span>
        </template>
      </el-pagination>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Search, Refresh, Plus, Download } from '@element-plus/icons-vue'
import type { TableColumn, TableAction, FilterBarField } from '@/types/ui'
import { STATUS_LABELS, STATUS_TYPES } from '@/types/common'

interface Props {
  // Data
  data?: any[]
  loading?: boolean
  
  // Columns
  columns: TableColumn[]
  actions?: TableAction[]
  
  // Filter
  showFilterBar?: boolean
  filterFields?: FilterBarField[]
  
  // Toolbar
  showToolbar?: boolean
  showCreate?: boolean
  showExport?: boolean
  
  // Table features
  showSelection?: boolean
  showIndex?: boolean
  showSummary?: boolean
  summaryMethod?: Function
  tableHeight?: string | number
  maxHeight?: string | number
  
  // Pagination
  showPagination?: boolean
  total?: number
  pageSize?: number
  pageSizes?: number[]
  paginationLayout?: string
  
  // Initial filters
  initialFilters?: Record<string, any>
}

const props = withDefaults(defineProps<Props>(), {
  data: () => [],
  loading: false,
  showFilterBar: true,
  filterFields: () => [],
  showToolbar: true,
  showCreate: true,
  showExport: false,
  showSelection: false,
  showIndex: false,
  showSummary: false,
  showPagination: true,
  total: 0,
  pageSize: 20,
  pageSizes: () => [10, 20, 50, 100],
  paginationLayout: 'total, sizes, prev, pager, next, jumper',
  initialFilters: () => ({})
})

interface Emits {
  (e: 'search', filters: Record<string, any>): void
  (e: 'reset'): void
  (e: 'refresh'): void
  (e: 'create'): void
  (e: 'export'): void
  (e: 'selection-change', selection: any[]): void
  (e: 'sort-change', sort: { column: any; prop: string; order: string }): void
  (e: 'page-change', page: number): void
  (e: 'size-change', size: number): void
}

const emit = defineEmits<Emits>()

// Filter state
const filters = ref<Record<string, any>>({ ...props.initialFilters })

// Pagination state
const currentPage = ref(1)
const pageSize = ref(props.pageSize)

// Methods
const handleSearch = () => {
  currentPage.value = 1
  emit('search', { ...filters.value })
}

const handleReset = () => {
  filters.value = { ...props.initialFilters }
  currentPage.value = 1
  emit('reset')
}

const handleRefresh = () => {
  emit('refresh')
}

const handleSelectionChange = (selection: any[]) => {
  emit('selection-change', selection)
}

const handleSortChange = (sort: { column: any; prop: string; order: string }) => {
  emit('sort-change', sort)
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  emit('page-change', page)
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  emit('size-change', size)
}

// Status helpers
const getStatusLabel = (status: string) => {
  return STATUS_LABELS[status] || status
}

const getStatusType = (status: string) => {
  return STATUS_TYPES[status] || ''
}

// Action helpers
const getVisibleActions = (row: any) => {
  return props.actions?.filter(action => 
    !action.visible || action.visible(row)
  ) || []
}

const getActionDisabled = (action: TableAction, row: any) => {
  return action.disabled ? action.disabled(row) : false
}

// Formatters
const formatMoney = (amount: number) => {
  if (typeof amount !== 'number') return amount
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: 'TWD',
    minimumFractionDigits: 0
  }).format(amount)
}

const formatDate = (date: string) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-TW')
}

// Cell class name handler for dynamic styling
const getCellClassName = ({ row, column, columnIndex }: any) => {
  // Find the column definition
  const colDef = props.columns[columnIndex - (props.showSelection ? 1 : 0) - (props.showIndex ? 1 : 0)]
  
  if (colDef && colDef.cellClass) {
    // If cellClass is a function, call it with the row
    if (typeof colDef.cellClass === 'function') {
      return colDef.cellClass(row)
    }
    // If cellClass is a string, return it directly
    return colDef.cellClass
  }
  
  return ''
}

// Watch for prop changes
watch(() => props.pageSize, (newSize) => {
  pageSize.value = newSize
})

// Auto search on filter changes
watch(filters, () => {
  if (props.showFilterBar) {
    handleSearch()
  }
}, { deep: true })

// Expose methods for parent components
defineExpose({
  search: handleSearch,
  reset: handleReset,
  refresh: handleRefresh,
  getCurrentFilters: () => filters.value,
  getCurrentPage: () => currentPage.value,
  getPageSize: () => pageSize.value
})
</script>

<style scoped>
.data-table {
  .filter-bar {
    background: #f8f9fa;
    padding: 16px;
    margin-bottom: 16px;
    border-radius: 4px;
  }

  .table-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    .toolbar-left, .toolbar-right {
      display: flex;
      gap: 8px;
    }
  }

  .table-pagination {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }

  .money {
    font-weight: 500;
    color: #409eff;
  }
}
</style>