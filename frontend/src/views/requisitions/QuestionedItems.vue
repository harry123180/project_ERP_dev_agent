<template>
  <div class="questioned-items">
    <div class="page-header">
      <h1>管理疑問項目</h1>
      <div class="header-actions">
        <el-button @click="fetchQuestionedItems" icon="Refresh">重新整理</el-button>
      </div>
    </div>

    <div class="filter-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input
            v-model="searchText"
            placeholder="搜尋項目名稱或請購單號"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="開始日期"
            end-placeholder="結束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleSearch"
          />
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="handleSearch" icon="Search">搜尋</el-button>
        </el-col>
      </el-row>
    </div>

    <el-card>
      <el-table
        v-loading="loading"
        :data="questionedItems"
        border
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column label="請購單號" prop="request_order_no" width="140" fixed="left">
          <template #default="{ row }">
            <el-link type="primary" @click="viewRequisition(row.request_order_no)">
              {{ row.request_order_no }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column label="項目名稱" prop="item_name" min-width="150" show-overflow-tooltip />
        <el-table-column label="規格" prop="item_specification" min-width="150" show-overflow-tooltip />
        <el-table-column label="數量" width="100">
          <template #default="{ row }">
            {{ row.item_quantity }} {{ row.item_unit }}
          </template>
        </el-table-column>
        <el-table-column label="請購人" prop="requester_name" width="100" />
        <el-table-column label="疑問原因" prop="status_note" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tooltip v-if="row.status_note" :content="row.status_note" placement="top">
              <span>{{ row.status_note }}</span>
            </el-tooltip>
            <span v-else class="text-muted">未提供原因</span>
          </template>
        </el-table-column>
        <el-table-column label="標記日期" prop="questioned_at" width="120">
          <template #default="{ row }">
            {{ formatDate(row.questioned_at) }}
          </template>
        </el-table-column>
        <el-table-column label="標記人" prop="questioned_by" width="100" />
        <el-table-column label="狀態" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="warning" size="small">有疑問</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="handleResolve(row)"
            >
              解決疑問
            </el-button>
            <el-button
              size="small"
              @click="viewDetail(row)"
            >
              查看詳情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > 0"
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 批量操作 -->
    <div v-if="selectedItems.length > 0" class="batch-actions">
      <el-card>
        <div class="batch-header">
          <span>已選擇 {{ selectedItems.length }} 個項目</span>
          <el-button type="primary" @click="handleBatchResolve">批量解決疑問</el-button>
        </div>
      </el-card>
    </div>

    <!-- 解決疑問對話框 -->
    <el-dialog
      v-model="resolveDialogVisible"
      title="解決疑問項目"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form ref="resolveFormRef" :model="resolveForm" :rules="resolveRules" label-width="120px">
        <el-form-item label="請購單號">
          <el-input v-model="resolveForm.request_order_no" disabled />
        </el-form-item>
        <el-form-item label="項目名稱">
          <el-input v-model="resolveForm.item_name" disabled />
        </el-form-item>
        <el-form-item label="原疑問原因">
          <el-input
            v-model="resolveForm.original_note"
            type="textarea"
            :rows="2"
            disabled
          />
        </el-form-item>
        <el-form-item label="解決方案" prop="resolution">
          <el-input
            v-model="resolveForm.resolution"
            type="textarea"
            :rows="3"
            placeholder="請說明如何解決此疑問"
          />
        </el-form-item>
        <el-form-item label="處理結果" prop="action">
          <el-radio-group v-model="resolveForm.action" @change="handleActionChange">
            <el-radio label="approve">轉為已核准</el-radio>
            <el-radio label="reject">拒絕此項目</el-radio>
            <el-radio label="keep">保持疑問狀態</el-radio>
          </el-radio-group>
        </el-form-item>
        <!-- 核准時需要填寫供應商和單價 -->
        <template v-if="resolveForm.action === 'approve'">
          <el-form-item label="供應商" prop="supplier_id">
            <el-select v-model="resolveForm.supplier_id" placeholder="請選擇供應商" filterable>
              <el-option
                v-for="supplier in suppliers"
                :key="supplier.supplier_id"
                :label="`${supplier.supplier_id} - ${supplier.supplier_name_zh || supplier.supplier_name}`"
                :value="supplier.supplier_id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="單價" prop="unit_price">
            <el-input-number
              v-model="resolveForm.unit_price"
              :min="0.01"
              :precision="2"
              placeholder="請輸入單價"
            />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="resolveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmResolve" :loading="resolving">確認</el-button>
      </template>
    </el-dialog>

    <!-- 詳情對話框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="疑問項目詳情"
      width="700px"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="請購單號">
          {{ currentItem?.request_order_no }}
        </el-descriptions-item>
        <el-descriptions-item label="請購人">
          {{ currentItem?.requester_name }}
        </el-descriptions-item>
        <el-descriptions-item label="項目名稱" :span="2">
          {{ currentItem?.item_name }}
        </el-descriptions-item>
        <el-descriptions-item label="規格說明" :span="2">
          {{ currentItem?.item_specification || '無' }}
        </el-descriptions-item>
        <el-descriptions-item label="數量">
          {{ currentItem?.item_quantity }} {{ currentItem?.item_unit }}
        </el-descriptions-item>
        <el-descriptions-item label="類別">
          {{ getCategoryName(currentItem?.item_category) }}
        </el-descriptions-item>
        <el-descriptions-item label="用途說明" :span="2">
          {{ currentItem?.item_description || '無' }}
        </el-descriptions-item>
        <el-descriptions-item label="疑問原因" :span="2">
          {{ currentItem?.status_note || '未提供原因' }}
        </el-descriptions-item>
        <el-descriptions-item label="標記時間">
          {{ formatDateTime(currentItem?.questioned_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="標記人">
          {{ currentItem?.questioned_by }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailDialogVisible = false">關閉</el-button>
        <el-button type="primary" @click="handleResolveFromDetail">解決疑問</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { requisitionApi } from '@/api/requisition'
import { supplierApi } from '@/api/supplier'

interface QuestionedItem {
  detail_id: number
  request_order_no: string
  item_name: string
  item_specification?: string
  item_quantity: number
  item_unit: string
  item_category?: string
  item_description?: string
  requester_name: string
  status_note?: string
  questioned_at: string
  questioned_by: string
  supplier_id?: string
  unit_price?: number
}

const router = useRouter()

// State
const loading = ref(false)
const resolving = ref(false)
const questionedItems = ref<QuestionedItem[]>([])
const selectedItems = ref<QuestionedItem[]>([])
const currentItem = ref<QuestionedItem | null>(null)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchText = ref('')
const dateRange = ref<[string, string] | null>(null)
const suppliers = ref<any[]>([])

// Dialogs
const resolveDialogVisible = ref(false)
const detailDialogVisible = ref(false)

// Forms
const resolveFormRef = ref<FormInstance>()
const resolveForm = reactive({
  detail_id: 0,
  request_order_no: '',
  item_name: '',
  original_note: '',
  resolution: '',
  action: 'approve',
  supplier_id: '',
  unit_price: 0
})

const resolveRules = reactive({
  resolution: [
    { required: true, message: '請輸入解決方案', trigger: 'blur' }
  ],
  action: [
    { required: true, message: '請選擇處理結果', trigger: 'change' }
  ],
  supplier_id: [
    {
      required: true,
      message: '請選擇供應商',
      trigger: 'change',
      validator: (rule: any, value: any, callback: any) => {
        if (resolveForm.action === 'approve' && !value) {
          callback(new Error('核准時必須選擇供應商'))
        } else {
          callback()
        }
      }
    }
  ],
  unit_price: [
    {
      required: true,
      message: '請輸入單價',
      trigger: 'blur',
      validator: (rule: any, value: any, callback: any) => {
        if (resolveForm.action === 'approve' && (!value || value <= 0)) {
          callback(new Error('核准時必須輸入有效的單價'))
        } else {
          callback()
        }
      }
    }
  ]
})

// Methods
const fetchQuestionedItems = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }

    if (searchText.value) {
      params.search = searchText.value
    }

    if (dateRange.value) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }

    const response = await requisitionApi.getQuestionedItems(params)
    questionedItems.value = response.items
    total.value = response.total
  } catch (error) {
    console.error('Failed to fetch questioned items:', error)
    ElMessage.error('獲取疑問項目失敗')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchQuestionedItems()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchQuestionedItems()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchQuestionedItems()
}

const handleSelectionChange = (selection: QuestionedItem[]) => {
  selectedItems.value = selection
}

const viewRequisition = (requisitionNo: string) => {
  router.push(`/requisitions/${requisitionNo}`)
}

const viewDetail = (item: QuestionedItem) => {
  currentItem.value = item
  detailDialogVisible.value = true
}

const handleResolve = (item: QuestionedItem) => {
  currentItem.value = item
  resolveForm.detail_id = item.detail_id
  resolveForm.request_order_no = item.request_order_no
  resolveForm.item_name = item.item_name
  resolveForm.original_note = item.status_note || ''
  resolveForm.resolution = ''
  resolveForm.action = 'approve'
  // 如果項目已有供應商和單價，自動帶入
  resolveForm.supplier_id = item.supplier_id || ''
  resolveForm.unit_price = item.unit_price || 0.01
  resolveDialogVisible.value = true
}

const handleActionChange = (value: string) => {
  // Clear supplier and price when not approving
  if (value !== 'approve') {
    resolveForm.supplier_id = ''
    resolveForm.unit_price = 0
  }
}

const handleResolveFromDetail = () => {
  detailDialogVisible.value = false
  if (currentItem.value) {
    handleResolve(currentItem.value)
  }
}

const confirmResolve = async () => {
  if (!await resolveFormRef.value?.validate()) return

  try {
    resolving.value = true

    const data: any = {
      resolution: resolveForm.resolution
    }

    if (resolveForm.action === 'approve') {
      // 轉為已核准
      await requisitionApi.approveItem(
        resolveForm.request_order_no,
        resolveForm.detail_id,
        {
          supplier_id: resolveForm.supplier_id,
          unit_price: resolveForm.unit_price,
          note: resolveForm.resolution
        }
      )
      ElMessage.success('項目已轉為已核准')
    } else if (resolveForm.action === 'reject') {
      // 拒絕項目
      await requisitionApi.rejectItem(
        resolveForm.request_order_no,
        resolveForm.detail_id,
        {
          reason: resolveForm.resolution
        }
      )
      ElMessage.success('項目已拒絕')
    } else {
      // 保持疑問狀態但添加備註
      await requisitionApi.updateItemNote(
        resolveForm.request_order_no,
        resolveForm.detail_id,
        {
          note: `${resolveForm.original_note}\n解決方案: ${resolveForm.resolution}`
        }
      )
      ElMessage.success('已更新項目備註')
    }

    resolveDialogVisible.value = false
    fetchQuestionedItems()
  } catch (error) {
    console.error('Failed to resolve item:', error)
    ElMessage.error('處理失敗')
  } finally {
    resolving.value = false
  }
}

const handleBatchResolve = async () => {
  try {
    const result = await ElMessageBox.confirm(
      `確定要批量解決 ${selectedItems.value.length} 個疑問項目嗎？所有項目將轉為已核准狀態。`,
      '批量解決確認',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    if (result === 'confirm') {
      loading.value = true
      let successCount = 0
      let failCount = 0

      for (const item of selectedItems.value) {
        try {
          // For batch approval, we need supplier and price
          // This is a limitation - batch approval needs to be done individually
          ElMessage.warning('批量核准需要逐個設置供應商和單價，請使用單個解決功能')
          return
          successCount++
        } catch (error) {
          failCount++
          console.error(`Failed to resolve item ${item.detail_id}:`, error)
        }
      }

      if (successCount > 0) {
        ElMessage.success(`成功解決 ${successCount} 個項目`)
      }
      if (failCount > 0) {
        ElMessage.warning(`${failCount} 個項目處理失敗`)
      }

      fetchQuestionedItems()
    }
  } catch (error) {
    // User cancelled
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-TW')
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-TW')
}

const getCategoryName = (code?: string) => {
  const categories: Record<string, string> = {
    office: '辦公用品',
    electronic: '電子設備',
    furniture: '辦公家具',
    consumable: '耗材用品',
    tool: '工具設備',
    other: '其他'
  }
  return categories[code || ''] || code || '-'
}

const fetchSuppliers = async () => {
  try {
    const response = await supplierApi.getSuppliers({ page_size: 100 })
    console.log('Supplier API response:', response)

    // Check if response has the correct structure
    if (response && response.data) {
      // If response is wrapped in data property
      suppliers.value = response.data.items || []
      console.log('Suppliers set from response.data.items:', suppliers.value)
    } else if (response && response.items) {
      // If response has items directly
      suppliers.value = response.items || []
      console.log('Suppliers set from response.items:', suppliers.value)
    } else if (Array.isArray(response)) {
      // If response is an array directly
      suppliers.value = response
      console.log('Suppliers set from array response:', suppliers.value)
    } else {
      console.warn('Unexpected supplier API response structure:', response)
      suppliers.value = []
    }
  } catch (error) {
    console.error('Failed to fetch suppliers:', error)
    suppliers.value = []
  }
}

onMounted(() => {
  fetchQuestionedItems()
  fetchSuppliers()
})
</script>

<style scoped>
.questioned-items {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.filter-section {
  margin-bottom: 20px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}

.batch-actions {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
}

.batch-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px;
}

.text-muted {
  color: #909399;
}

.el-pagination {
  margin-top: 20px;
  text-align: right;
}
</style>