<template>
  <div class="supplier-detail" v-loading="loading">
    <!-- Header -->
    <div class="header">
      <div class="title-section">
        <h1>供應商詳情</h1>
        <span class="subtitle" v-if="supplier">
          {{ supplier.supplier_name_zh }} ({{ supplier.supplier_id }})
        </span>
      </div>
      <div class="actions">
        <el-button @click="goBack" :icon="ArrowLeft">
          返回列表
        </el-button>
        <el-button 
          type="warning" 
          :icon="Edit" 
          @click="editSupplier"
          v-if="canManageSuppliers"
        >
          編輯供應商
        </el-button>
      </div>
    </div>
    
    <!-- Main Content -->
    <div class="content" v-if="supplier">
      <!-- Basic Info Card -->
      <el-card class="info-card" shadow="never">
        <template #header>
          <div class="card-header">
            <h3>基本資訊</h3>
            <el-tag 
              :type="supplier.is_active ? 'success' : 'danger'"
              size="default"
            >
              {{ supplier.is_active ? '啟用' : '停用' }}
            </el-tag>
          </div>
        </template>
        
        <div class="info-grid">
          <div class="info-section">
            <h4 class="section-title">供應商資訊</h4>
            <div class="info-items">
              <div class="info-item">
                <label>供應商編號</label>
                <span class="value">{{ supplier.supplier_id }}</span>
              </div>
              <div class="info-item">
                <label>中文名稱</label>
                <span class="value">{{ supplier.supplier_name_zh }}</span>
              </div>
              <div class="info-item" v-if="supplier.supplier_name_en">
                <label>英文名稱</label>
                <span class="value">{{ supplier.supplier_name_en }}</span>
              </div>
              <div class="info-item">
                <label>供應商地區</label>
                <el-tag 
                  :type="supplier.supplier_region === 'domestic' ? 'success' : 'warning'"
                  size="small"
                >
                  {{ supplier.supplier_region === 'domestic' ? '國內' : '國外' }}
                </el-tag>
              </div>
              <div class="info-item" v-if="supplier.supplier_address">
                <label>地址</label>
                <span class="value address">{{ supplier.supplier_address }}</span>
              </div>
            </div>
          </div>
          
          <div class="info-section">
            <h4 class="section-title">聯絡資訊</h4>
            <div class="info-items">
              <div class="info-item" v-if="supplier.supplier_contact_person">
                <label>聯絡人</label>
                <span class="value">{{ supplier.supplier_contact_person }}</span>
              </div>
              <div class="info-item" v-if="supplier.supplier_phone">
                <label>聯絡電話</label>
                <span class="value">
                  <el-link :href="`tel:${supplier.supplier_phone}`" type="primary">
                    {{ supplier.supplier_phone }}
                  </el-link>
                </span>
              </div>
              <div class="info-item" v-if="supplier.supplier_email">
                <label>電子郵件</label>
                <span class="value">
                  <el-link :href="`mailto:${supplier.supplier_email}`" type="primary">
                    {{ supplier.supplier_email }}
                  </el-link>
                </span>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Financial Info Card -->
      <el-card class="info-card" shadow="never" v-if="hasFinancialInfo">
        <template #header>
          <div class="card-header">
            <h3>財務資訊</h3>
          </div>
        </template>
        
        <div class="info-grid">
          <div class="info-section">
            <div class="info-items">
              <div class="info-item" v-if="supplier.supplier_tax_id">
                <label>統一編號</label>
                <span class="value">{{ supplier.supplier_tax_id }}</span>
              </div>
              <div class="info-item" v-if="supplier.payment_terms">
                <label>付款條件</label>
                <span class="value">{{ formatPaymentTerms(supplier.payment_terms) }}</span>
              </div>
              <div class="info-item" v-if="supplier.bank_account">
                <label>銀行帳戶</label>
                <span class="value bank-account">{{ supplier.bank_account }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Remarks Card -->
      <el-card class="info-card" shadow="never" v-if="supplier.supplier_remark">
        <template #header>
          <div class="card-header">
            <h3>備註</h3>
          </div>
        </template>
        
        <div class="remark-content">
          {{ supplier.supplier_remark }}
        </div>
      </el-card>

      <!-- System Info Card -->
      <el-card class="info-card" shadow="never">
        <template #header>
          <div class="card-header">
            <h3>系統資訊</h3>
          </div>
        </template>
        
        <div class="info-grid">
          <div class="info-section">
            <div class="info-items">
              <div class="info-item">
                <label>建立時間</label>
                <span class="value">{{ formatDateTime(supplier.created_at) }}</span>
              </div>
              <div class="info-item">
                <label>最後更新</label>
                <span class="value">{{ formatDateTime(supplier.updated_at) }}</span>
              </div>
              <div class="info-item">
                <label>啟用狀態</label>
                <el-tag 
                  :type="supplier.is_active ? 'success' : 'danger'"
                  size="small"
                >
                  {{ supplier.is_active ? '啟用中' : '已停用' }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Action Buttons -->
      <div class="action-section">
        <div class="primary-actions">
          <el-button 
            type="primary" 
            size="large"
            :icon="Document"
            @click="goToPurchaseOrders"
          >
            查看採購單
          </el-button>
        </div>
        
        <div class="secondary-actions" v-if="canManageSuppliers">
          <el-button 
            type="warning" 
            size="large"
            :icon="Edit"
            @click="editSupplier"
          >
            編輯供應商
          </el-button>
          <el-button 
            :type="supplier.is_active ? 'danger' : 'success'" 
            size="large"
            :icon="supplier.is_active ? 'Close' : 'Check'"
            @click="toggleSupplierStatus"
            :loading="statusLoading"
          >
            {{ supplier.is_active ? '停用' : '啟用' }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <el-empty 
      v-else-if="!loading" 
      description="找不到供應商資料"
      :image-size="200"
    >
      <el-button @click="goBack">返回列表</el-button>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ArrowLeft, Edit, Document, Check, Close 
} from '@element-plus/icons-vue'
import { useSuppliersStore } from '@/stores/suppliers'
import { useAuthStore } from '@/stores/auth'
import type { Supplier } from '@/stores/suppliers'

const route = useRoute()
const router = useRouter()
const suppliersStore = useSuppliersStore()
const authStore = useAuthStore()

// Reactive data
const statusLoading = ref(false)

// Computed properties
const supplier = computed(() => suppliersStore.currentSupplier)
const loading = computed(() => suppliersStore.loading)

const canManageSuppliers = computed(() => 
  authStore.hasRole('Admin', 'ProcurementMgr', 'Procurement')
)

const hasFinancialInfo = computed(() => {
  if (!supplier.value) return false
  return supplier.value.supplier_tax_id || 
         supplier.value.payment_terms || 
         supplier.value.bank_account
})

// Methods
const fetchSupplier = async () => {
  try {
    await suppliersStore.fetchSupplierById(route.params.id as string)
  } catch (error) {
    ElMessage.error('無法載入供應商資料')
    goBack()
  }
}

const goBack = () => {
  router.push('/suppliers')
}

const editSupplier = () => {
  router.push(`/suppliers/${route.params.id}/edit`)
}

const goToPurchaseOrders = () => {
  router.push(`/suppliers/${route.params.id}/purchase-orders`)
}

const toggleSupplierStatus = async () => {
  if (!supplier.value) return
  
  const action = supplier.value.is_active ? '停用' : '啟用'
  
  try {
    await ElMessageBox.confirm(
      `確定要${action}這個供應商嗎？`,
      '確認操作',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    statusLoading.value = true
    
    await suppliersStore.updateSupplier(supplier.value.supplier_id, {
      is_active: !supplier.value.is_active
    })
    
    ElMessage.success(`供應商已${action}`)
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(`${action}供應商失敗`)
    }
  } finally {
    statusLoading.value = false
  }
}

const formatPaymentTerms = (terms: string) => {
  const termsMap: Record<string, string> = {
    'cash': '現金',
    'net_30': '月結30天',
    'net_60': '月結60天',
    'net_90': '月結90天',
    'prepaid': '預付款',
    'cod': '貨到付款'
  }
  return termsMap[terms] || terms
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Lifecycle
onMounted(() => {
  fetchSupplier()
})
</script>

<style scoped>
.supplier-detail {
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

.content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card {
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  background: white;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

.info-section {
  display: flex;
  flex-direction: column;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.info-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item label {
  font-size: 12px;
  color: #909399;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.info-item .value {
  font-size: 14px;
  color: #303133;
  font-weight: 400;
  line-height: 1.4;
}

.info-item .value.address,
.info-item .value.bank-account {
  white-space: pre-line;
  line-height: 1.6;
}

.remark-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  white-space: pre-line;
  padding: 16px;
  background-color: #f9f9f9;
  border-radius: 6px;
}

.action-section {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 32px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.primary-actions,
.secondary-actions {
  display: flex;
  gap: 12px;
}

/* Element Plus customizations */
:deep(.el-card__header) {
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  background-color: #fafafa;
}

:deep(.el-card__body) {
  padding: 24px;
}

:deep(.el-button) {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

:deep(.el-button--large) {
  padding: 12px 24px;
  font-size: 16px;
}

:deep(.el-tag) {
  border: none;
  font-weight: 500;
}

:deep(.el-link) {
  font-size: 14px;
  font-weight: 400;
}

:deep(.el-empty) {
  padding: 60px 0;
}

/* Loading overlay */
:deep(.el-loading-mask) {
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 8px;
}

/* Hover effects */
.info-card {
  transition: all 0.3s ease;
}

.info-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.action-section {
  transition: all 0.3s ease;
}

.action-section:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* Responsive adjustments */
@media (max-width: 992px) {
  .info-grid {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .action-section {
    flex-direction: column;
    align-items: center;
    gap: 16px;
  }
  
  .primary-actions,
  .secondary-actions {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .supplier-detail {
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
  
  .actions {
    justify-content: center;
  }
  
  .content {
    gap: 16px;
  }
  
  .info-grid {
    gap: 20px;
  }
  
  :deep(.el-card__header) {
    padding: 16px 20px;
  }
  
  :deep(.el-card__body) {
    padding: 20px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
  
  .primary-actions,
  .secondary-actions {
    flex-direction: column;
  }
  
  .primary-actions .el-button,
  .secondary-actions .el-button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .supplier-detail {
    padding: 12px;
  }
  
  .content {
    gap: 12px;
  }
  
  :deep(.el-card__header) {
    padding: 12px 16px;
  }
  
  :deep(.el-card__body) {
    padding: 16px;
  }
  
  .section-title {
    font-size: 14px;
    margin-bottom: 12px;
  }
  
  .info-items {
    gap: 10px;
  }
  
  .action-section {
    margin-top: 20px;
    padding: 16px;
    gap: 12px;
  }
}

/* Focus states for accessibility */
:deep(.el-button:focus-visible) {
  outline: 2px solid #409eff;
  outline-offset: 2px;
}

:deep(.el-tag) {
  transition: all 0.3s ease;
}

/* Print styles */
@media print {
  .supplier-detail {
    background: white;
    padding: 0;
  }
  
  .header .actions,
  .action-section {
    display: none;
  }
  
  .info-card {
    border: 1px solid #ddd;
    page-break-inside: avoid;
    margin-bottom: 20px;
  }
  
  :deep(.el-card__header) {
    background: #f5f5f5;
    -webkit-print-color-adjust: exact;
    color-adjust: exact;
  }
}

/* Animation for status changes */
.info-item .value {
  transition: color 0.3s ease;
}

.info-item:hover .value {
  color: #409eff;
}

/* Custom scrollbar for long content */
.remark-content {
  max-height: 200px;
  overflow-y: auto;
}

.remark-content::-webkit-scrollbar {
  width: 6px;
}

.remark-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.remark-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.remark-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>