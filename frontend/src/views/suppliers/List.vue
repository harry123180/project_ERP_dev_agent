<template>
  <div class="suppliers-list">
    <!-- Header Section -->
    <div class="header">
      <div class="title-section">
        <h1>供應商管理</h1>
        <span class="subtitle">管理供應商資料和聯絡資訊</span>
      </div>
      <div class="actions">
        <el-button 
          type="primary" 
          :icon="Plus" 
          @click="createSupplier"
          v-if="canManageSuppliers"
        >
          新增供應商
        </el-button>
      </div>
    </div>

    <!-- Filters Section -->
    <el-card class="filters-card" shadow="never">
      <el-form :model="filters" :inline="true" class="filter-form">
        <el-form-item label="供應商名稱">
          <el-input
            v-model="filters.search"
            placeholder="搜尋供應商名稱或編號"
            :prefix-icon="Search"
            clearable
            style="width: 250px"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        
        <el-form-item label="地區">
          <el-select 
            v-model="filters.region" 
            placeholder="選擇地區" 
            clearable
            style="width: 150px"
          >
            <el-option label="國內" value="domestic" />
            <el-option label="國外" value="international" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="狀態">
          <el-select 
            v-model="filters.status" 
            placeholder="選擇狀態" 
            clearable
            style="width: 120px"
          >
            <el-option label="啟用" value="active" />
            <el-option label="停用" value="inactive" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">
            搜尋
          </el-button>
          <el-button :icon="Refresh" @click="resetFilters">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Statistics Cards -->
    <div class="stats-row">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-number">{{ pagination.total }}</div>
          <div class="stat-label">總供應商數</div>
        </div>
        <el-icon class="stat-icon" color="#409eff">
          <Shop />
        </el-icon>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-number">{{ activeCount }}</div>
          <div class="stat-label">啟用中</div>
        </div>
        <el-icon class="stat-icon" color="#67c23a">
          <Check />
        </el-icon>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-number">{{ domesticCount }}</div>
          <div class="stat-label">國內供應商</div>
        </div>
        <el-icon class="stat-icon" color="#e6a23c">
          <Location />
        </el-icon>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-number">{{ internationalCount }}</div>
          <div class="stat-label">國外供應商</div>
        </div>
        <el-icon class="stat-icon" color="#f56c6c">
          <Position />
        </el-icon>
      </el-card>
    </div>

    <!-- Main Table -->
    <el-card class="table-card" shadow="never">
      <el-table
        :data="suppliers"
        v-loading="loading"
        row-key="supplier_id"
        stripe
        border
        style="width: 100%"
        :default-sort="{prop: 'supplier_name_zh', order: 'ascending'}"
        @sort-change="handleSortChange"
      >
        <el-table-column 
          prop="supplier_id" 
          label="供應商編號" 
          width="140"
          sortable="custom"
          show-overflow-tooltip
        />
        
        <el-table-column 
          prop="supplier_name_zh" 
          label="供應商名稱" 
          min-width="200"
          sortable="custom"
          show-overflow-tooltip
        >
          <template #default="scope">
            <div class="supplier-name">
              <div class="name-zh">{{ scope.row.supplier_name_zh }}</div>
              <div class="name-en" v-if="scope.row.supplier_name_en">
                {{ scope.row.supplier_name_en }}
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column 
          prop="supplier_region" 
          label="地區" 
          width="100"
          align="center"
        >
          <template #default="scope">
            <el-tag 
              :type="scope.row.supplier_region === 'domestic' ? 'success' : 'warning'"
              size="small"
            >
              {{ scope.row.supplier_region === 'domestic' ? '國內' : '國外' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column 
          prop="supplier_contact_person" 
          label="聯絡人" 
          width="120"
          show-overflow-tooltip
        />
        
        <el-table-column 
          prop="supplier_phone" 
          label="聯絡電話" 
          width="140"
          show-overflow-tooltip
        />
        
        <el-table-column 
          prop="supplier_email" 
          label="電子郵件" 
          width="180"
          show-overflow-tooltip
        />
        
        <el-table-column 
          prop="is_active" 
          label="狀態" 
          width="100"
          align="center"
        >
          <template #default="scope">
            <el-tag 
              :type="scope.row.is_active ? 'success' : 'danger'"
              size="small"
            >
              {{ scope.row.is_active ? '啟用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column 
          prop="updated_at" 
          label="更新時間" 
          width="140"
          sortable="custom"
        >
          <template #default="scope">
            {{ formatDate(scope.row.updated_at) }}
          </template>
        </el-table-column>
        
        <el-table-column 
          label="操作" 
          width="200" 
          fixed="right"
          align="center"
        >
          <template #default="scope">
            <div class="action-buttons">
              <el-button 
                type="primary" 
                size="small" 
                :icon="View"
                @click="viewSupplier(scope.row.supplier_id)"
              >
                詳情
              </el-button>
              <el-button 
                type="warning" 
                size="small" 
                :icon="Edit"
                @click="editSupplier(scope.row.supplier_id)"
                v-if="canManageSuppliers"
              >
                編輯
              </el-button>
              <el-button 
                type="info" 
                size="small" 
                :icon="Document"
                @click="viewPurchaseOrders(scope.row.supplier_id)"
              >
                採購單
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Plus, Search, Refresh, Shop, Check, Location, Position, 
  View, Edit, Document 
} from '@element-plus/icons-vue'
import { useSuppliersStore } from '@/stores/suppliers'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const suppliersStore = useSuppliersStore()
const authStore = useAuthStore()

// Reactive data
const filters = ref({
  search: '',
  region: '',
  status: ''
})

// Computed properties
const suppliers = computed(() => suppliersStore.suppliers)
const loading = computed(() => suppliersStore.loading)
const pagination = computed(() => suppliersStore.pagination)

const activeCount = computed(() => 
  suppliers.value.filter(s => s.is_active).length
)

const domesticCount = computed(() => 
  suppliers.value.filter(s => s.supplier_region === 'domestic').length
)

const internationalCount = computed(() => 
  suppliers.value.filter(s => s.supplier_region === 'international').length
)

const canManageSuppliers = computed(() => 
  authStore.hasRole('Admin', 'ProcurementMgr', 'Procurement')
)

// Methods
const fetchSuppliers = async () => {
  try {
    await suppliersStore.fetchSuppliers({
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      q: filters.value.search || undefined,
      region: filters.value.region || undefined,
      active: filters.value.status ? filters.value.status === 'active' : undefined
    })
  } catch (error) {
    ElMessage.error('載入供應商資料失敗')
  }
}

const handleSearch = () => {
  pagination.value.page = 1
  fetchSuppliers()
}

const resetFilters = () => {
  filters.value = {
    search: '',
    region: '',
    status: ''
  }
  pagination.value.page = 1
  fetchSuppliers()
}

const handleSizeChange = (size: number) => {
  pagination.value.page_size = size
  fetchSuppliers()
}

const handleCurrentChange = (page: number) => {
  pagination.value.page = page
  fetchSuppliers()
}

const handleSortChange = ({ prop, order }: { prop: string, order: string }) => {
  // Implement sort logic if needed by backend
  console.log('Sort change:', prop, order)
}

const createSupplier = () => {
  router.push('/suppliers/create')
}

const viewSupplier = (id: string) => {
  router.push(`/suppliers/${id}`)
}

const editSupplier = (id: string) => {
  router.push(`/suppliers/${id}/edit`)
}

const viewPurchaseOrders = (id: string) => {
  router.push(`/suppliers/${id}/purchase-orders`)
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-TW')
}

// Lifecycle
onMounted(() => {
  fetchSuppliers()
})

// Watchers
watch(() => filters.value.region, () => {
  if (pagination.value.page === 1) {
    fetchSuppliers()
  } else {
    pagination.value.page = 1
  }
})

watch(() => filters.value.status, () => {
  if (pagination.value.page === 1) {
    fetchSuppliers()
  } else {
    pagination.value.page = 1
  }
})
</script>

<style scoped>
.suppliers-list {
  padding: 24px;
  background-color: #f5f5f5;
  min-height: calc(100vh - 60px);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.title-section h1 {
  color: #303133;
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #909399;
  font-size: 14px;
  font-weight: 400;
}

.actions {
  display: flex;
  gap: 12px;
}

.filters-card {
  margin-bottom: 20px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.filter-form {
  margin: 0;
}

.filter-form .el-form-item {
  margin-bottom: 0;
  margin-right: 24px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  transition: all 0.3s ease;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.stat-icon {
  font-size: 32px;
  opacity: 0.8;
}

.table-card {
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  overflow: hidden;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.supplier-name {
  line-height: 1.4;
}

.name-zh {
  font-weight: 500;
  color: #303133;
  margin-bottom: 2px;
}

.name-en {
  font-size: 12px;
  color: #909399;
  font-style: italic;
}

.action-buttons {
  display: flex;
  gap: 6px;
  justify-content: center;
  flex-wrap: wrap;
}

.action-buttons .el-button {
  margin: 0;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 20px;
  background-color: #fafafa;
  border-top: 1px solid #e4e7ed;
}

/* Table customization */
:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table th) {
  background-color: #fafafa;
  color: #606266;
  font-weight: 600;
}

:deep(.el-table tr:hover > td) {
  background-color: #f5f7fa !important;
}

:deep(.el-table .el-tag) {
  border: none;
  font-weight: 500;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .suppliers-list {
    padding: 16px;
  }
  
  .header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .title-section h1 {
    font-size: 24px;
  }
  
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .stat-card :deep(.el-card__body) {
    padding: 16px;
  }
  
  .stat-number {
    font-size: 20px;
  }
  
  .stat-icon {
    font-size: 24px;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 4px;
  }
  
  .action-buttons .el-button {
    width: 100%;
    margin: 0;
  }
}

@media (max-width: 480px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
  
  .filter-form {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .filter-form .el-form-item {
    margin-right: 0;
    margin-bottom: 0;
  }
}

/* Loading and empty states */
:deep(.el-loading-mask) {
  background-color: rgba(255, 255, 255, 0.8);
}

:deep(.el-table__empty-block) {
  padding: 60px 0;
}

:deep(.el-table__empty-text) {
  color: #909399;
  font-size: 14px;
}
</style>