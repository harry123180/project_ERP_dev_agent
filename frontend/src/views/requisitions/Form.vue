<template>
  <div class="requisition-form">
    <PageHeader
      :title="isEdit ? '編輯請購單' : '新增請購單'"
      :subtitle="isEdit ? `編輯 ${requisitionId}` : '創建新的請購申請'"
      :show-back="true"
      @back="handleBack"
    />

    <el-card>
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
        @submit.prevent="handleSubmit"
      >
        <!-- Basic Information -->
        <div class="form-section">
          <h3 class="section-title">基本信息</h3>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="用途類型" prop="usage_type" required>
                <el-radio-group v-model="formData.usage_type">
                  <el-radio label="daily">日常用品</el-radio>
                  <el-radio label="project">專案用品</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item
                v-if="formData.usage_type === 'project'"
                label="專案編號"
                prop="project_id"
                required
              >
                <el-select
                  v-model="formData.project_id"
                  placeholder="選擇專案"
                  filterable
                  clearable
                  style="width: 100%"
                >
                  <el-option
                    v-for="project in projects"
                    :key="project.project_id"
                    :label="`${project.project_id} - ${project.project_name}`"
                    :value="project.project_id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 加急設定區塊 -->
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="加急設定">
                <el-checkbox
                  v-model="formData.is_urgent"
                  @change="onUrgentChange"
                  class="urgent-checkbox"
                >
                  <span class="urgent-label">此為加急請購單</span>
                </el-checkbox>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 加急詳細資訊區塊 -->
          <div v-if="formData.is_urgent" class="urgent-details">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item
                  label="期望到貨日期"
                  prop="expected_delivery_date"
                  required
                >
                  <el-date-picker
                    v-model="formData.expected_delivery_date"
                    type="date"
                    placeholder="選擇期望到貨日期"
                    format="YYYY/MM/DD"
                    value-format="YYYY-MM-DD"
                    style="width: 100%"
                    :disabled-date="disabledDate"
                    class="urgent-date-picker"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item
                  label="加急原因"
                  prop="urgent_reason"
                  required
                >
                  <el-input
                    v-model="formData.urgent_reason"
                    type="textarea"
                    :rows="3"
                    placeholder="請詳細說明加急原因"
                    maxlength="200"
                    show-word-limit
                    class="urgent-reason-input"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>

        <!-- Items List -->
        <div class="form-section">
          <div class="section-header">
            <h3 class="section-title">請購項目</h3>
            <el-button
              type="primary"
              :icon="Plus"
              @click="addItem"
            >
              新增項目
            </el-button>
          </div>

          <el-table
            :data="formData.items"
            border
            style="width: 100%"
          >
            <el-table-column type="index" label="序號" width="60" align="center" />
            <el-table-column label="項目名稱" min-width="150">
              <template #default="{ row, $index }">
                <el-input
                  v-model="row.item_name"
                  placeholder="請輸入項目名稱"
                  :class="{ 'is-error': getFieldError($index, 'item_name') }"
                />
                <div v-if="getFieldError($index, 'item_name')" class="field-error">
                  {{ getFieldError($index, 'item_name') }}
                </div>
              </template>
            </el-table-column>
            
            <el-table-column label="規格說明" min-width="150">
              <template #default="{ row }">
                <el-input
                  v-model="row.item_specification"
                  placeholder="請輸入規格說明"
                  type="textarea"
                  :rows="2"
                />
              </template>
            </el-table-column>
            
            <el-table-column label="數量" width="120">
              <template #default="{ row, $index }">
                <el-input-number
                  v-model="row.item_quantity"
                  :min="1"
                  :precision="0"
                  controls-position="right"
                  style="width: 100%"
                  :class="{ 'is-error': getFieldError($index, 'item_quantity') }"
                />
                <div v-if="getFieldError($index, 'item_quantity')" class="field-error">
                  {{ getFieldError($index, 'item_quantity') }}
                </div>
              </template>
            </el-table-column>
            
            <el-table-column label="單位" width="100">
              <template #default="{ row }">
                <el-select
                  v-model="row.item_unit"
                  placeholder="選擇單位"
                  style="width: 100%"
                >
                  <el-option label="個" value="個" />
                  <el-option label="箱" value="箱" />
                  <el-option label="包" value="包" />
                  <el-option label="套" value="套" />
                  <el-option label="張" value="張" />
                  <el-option label="公斤" value="公斤" />
                  <el-option label="公尺" value="公尺" />
                  <el-option label="瓶" value="瓶" />
                </el-select>
              </template>
            </el-table-column>
            
            <el-table-column label="類別" width="120">
              <template #default="{ row }">
                <el-select
                  v-model="row.item_category"
                  placeholder="選擇類別"
                  filterable
                  style="width: 100%"
                >
                  <el-option
                    v-for="category in categories"
                    :key="category.category_code"
                    :label="category.category_name"
                    :value="category.category_code"
                  />
                </el-select>
              </template>
            </el-table-column>
            
            <el-table-column label="用途說明" min-width="150">
              <template #default="{ row }">
                <el-input
                  v-model="row.item_description"
                  placeholder="請說明用途"
                  type="textarea"
                  :rows="2"
                />
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="80" fixed="right">
              <template #default="{ $index }">
                <el-button
                  type="danger"
                  :icon="Delete"
                  size="small"
                  @click="removeItem($index)"
                />
              </template>
            </el-table-column>
          </el-table>

          <div v-if="formData.items.length === 0" class="empty-items">
            <el-empty description="請添加請購項目" :image-size="60">
              <el-button type="primary" @click="addItem">添加第一個項目</el-button>
            </el-empty>
          </div>
        </div>
        
        <!-- Form Actions -->
        <div class="form-actions">
          <el-button @click="handleBack">取消</el-button>
          <el-button
            type="info"
            :loading="submitting"
            @click="handleSaveDraft"
          >
            保存草稿
          </el-button>
          <el-button
            type="primary"
            :loading="submitting"
            @click="handleSubmit"
          >
            提交審核
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import { PageHeader } from '@/components'
import { useRequisitionStore, useAuthStore } from '@/stores'
import { projectsApi } from '@/api'
import type { CreateRequisitionRequest } from '@/api/requisition'

interface RequisitionItem {
  item_name: string
  item_quantity: number
  item_unit: string
  item_specification?: string
  item_description?: string
  item_category?: string
}

interface FormData {
  usage_type: 'daily' | 'project'
  project_id?: string
  items: RequisitionItem[]
  // 加急相關欄位
  is_urgent: boolean
  expected_delivery_date?: string
  urgent_reason?: string
}

const route = useRoute()
const router = useRouter()
const requisitionStore = useRequisitionStore()
const authStore = useAuthStore()

// Form ref
const formRef = ref<FormInstance>()

// State
const submitting = ref(false)
const projects = ref<any[]>([])
const categories = ref<any[]>([])

// Computed
const isEdit = computed(() => !!route.params.id)
const requisitionId = computed(() => route.params.id as string)

// Form data
const formData = reactive<FormData>({
  usage_type: 'daily',
  items: [],
  // 加急相關欄位
  is_urgent: false,
  expected_delivery_date: '',
  urgent_reason: ''
})

// Form validation errors
const itemErrors = ref<Record<number, Record<string, string>>>({})

// Form rules
const formRules = {
  usage_type: [
    { required: true, message: '請選擇用途類型', trigger: 'change' }
  ],
  project_id: [
    {
      required: true,
      message: '請選擇專案編號',
      trigger: 'change',
      validator: (rule: any, value: any, callback: any) => {
        if (formData.usage_type === 'project' && !value) {
          callback(new Error('專案類型必須選擇專案編號'))
        } else {
          callback()
        }
      }
    }
  ],
  expected_delivery_date: [
    {
      required: true,
      message: '請選擇期望到貨日期',
      trigger: 'change',
      validator: (rule: any, value: any, callback: any) => {
        if (formData.is_urgent && !value) {
          callback(new Error('加急請購單必須填寫期望到貨日期'))
        } else {
          callback()
        }
      }
    }
  ],
  urgent_reason: [
    {
      required: true,
      message: '請說明加急原因',
      trigger: 'blur',
      validator: (rule: any, value: any, callback: any) => {
        if (formData.is_urgent && !value?.trim()) {
          callback(new Error('加急請購單必須說明加急原因'))
        } else {
          callback()
        }
      }
    }
  ]
}

// Methods
const getFieldError = (index: number, field: string) => {
  return itemErrors.value[index]?.[field]
}

// 加急功能相關方法
const onUrgentChange = (isUrgent: boolean) => {
  if (!isUrgent) {
    // 取消加急時清空相關欄位
    formData.expected_delivery_date = ''
    formData.urgent_reason = ''
  }
}

const disabledDate = (time: Date) => {
  // 禁用今天之前的日期
  return time.getTime() < Date.now() - 8.64e7
}

const validateItems = () => {
  itemErrors.value = {}
  let hasError = false

  if (formData.items.length === 0) {
    ElMessage.error('請至少添加一個請購項目')
    return false
  }

  formData.items.forEach((item, index) => {
    const errors: Record<string, string> = {}

    if (!item.item_name?.trim()) {
      errors.item_name = '項目名稱不能為空'
      hasError = true
    }

    if (!item.item_quantity || item.item_quantity < 1) {
      errors.item_quantity = '數量必須大於0'
      hasError = true
    }

    if (Object.keys(errors).length > 0) {
      itemErrors.value[index] = errors
    }
  })

  if (hasError) {
    ElMessage.error('請檢查項目信息填寫')
  }

  return !hasError
}

const addItem = () => {
  formData.items.push({
    item_name: '',
    item_quantity: 1,
    item_unit: '個',
    item_specification: '',
    item_description: '',
    item_category: ''
  })
}

const removeItem = (index: number) => {
  formData.items.splice(index, 1)
  // Clean up errors for removed item
  delete itemErrors.value[index]
}

const handleBack = () => {
  router.go(-1)
}

const handleSaveDraft = async () => {
  if (!await formRef.value?.validate()) return
  if (!validateItems()) return

  try {
    submitting.value = true
    
    const requestData: CreateRequisitionRequest = {
      usage_type: formData.usage_type,
      project_id: formData.project_id,
      status: 'draft',  // CRITICAL FIX: Explicitly set draft status
      items: formData.items.map(item => ({
        item_name: item.item_name.trim(),
        item_quantity: item.item_quantity,
        item_unit: item.item_unit,
        item_specification: item.item_specification?.trim(),
        item_description: item.item_description?.trim(),
        item_category: item.item_category
      })),
      // 加急相關欄位
      is_urgent: formData.is_urgent,
      expected_delivery_date: formData.is_urgent ? formData.expected_delivery_date : undefined,
      urgent_reason: formData.is_urgent ? formData.urgent_reason : undefined
    }

    if (isEdit.value) {
      await requisitionStore.updateRequisition(requisitionId.value, requestData)
      ElMessage.success('請購單保存成功')
    } else {
      await requisitionStore.createRequisition(requestData)
      ElMessage.success('請購單創建成功')
    }
    
    router.push('/requisitions')
  } catch (error) {
    console.error('Save failed:', error)
  } finally {
    submitting.value = false
  }
}

const handleSubmit = async () => {
  if (!await formRef.value?.validate()) return
  if (!validateItems()) return

  try {
    const result = await ElMessageBox.confirm(
      '提交後將無法修改，確定要提交審核嗎？',
      '提交確認',
      {
        confirmButtonText: '確定提交',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    if (result === 'confirm') {
      submitting.value = true
      
      if (isEdit.value) {
        // For existing requisitions, first update then submit
        const requestData: CreateRequisitionRequest = {
          usage_type: formData.usage_type,
          project_id: formData.project_id,
          status: 'draft',  // Keep as draft for update
          items: formData.items.map(item => ({
            item_name: item.item_name.trim(),
            item_quantity: item.item_quantity,
            item_unit: item.item_unit,
            item_specification: item.item_specification?.trim(),
            item_description: item.item_description?.trim(),
            item_category: item.item_category
          })),
          // 加急相關欄位
          is_urgent: formData.is_urgent,
          expected_delivery_date: formData.is_urgent ? formData.expected_delivery_date : undefined,
          urgent_reason: formData.is_urgent ? formData.urgent_reason : undefined
        }
        await requisitionStore.updateRequisition(requisitionId.value, requestData)
        await requisitionStore.submitRequisition(requisitionId.value)
      } else {
        // CRITICAL FIX: For new requisitions, create directly with submitted status
        const requestData: CreateRequisitionRequest = {
          usage_type: formData.usage_type,
          project_id: formData.project_id,
          status: 'submitted',  // CRITICAL FIX: Set to submitted status
          items: formData.items.map(item => ({
            item_name: item.item_name.trim(),
            item_quantity: item.item_quantity,
            item_unit: item.item_unit,
            item_specification: item.item_specification?.trim(),
            item_description: item.item_description?.trim(),
            item_category: item.item_category
          })),
          // 加急相關欄位
          is_urgent: formData.is_urgent,
          expected_delivery_date: formData.is_urgent ? formData.expected_delivery_date : undefined,
          urgent_reason: formData.is_urgent ? formData.urgent_reason : undefined
        }
        await requisitionStore.createRequisition(requestData)
      }
      
      ElMessage.success('請購單已提交審核')
      router.push('/requisitions')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Submit failed:', error)
    }
  } finally {
    submitting.value = false
  }
}

const fetchProjects = async () => {
  try {
    const response = await projectsApi.getActiveProjects()
    projects.value = response
  } catch (error) {
    console.error('Failed to fetch projects:', error)
  }
}

const fetchCategories = async () => {
  try {
    const response = await request.get('/item-categories')
    console.log('Categories response:', response.data) // 除錯用

    if (response.data.success && Array.isArray(response.data.data)) {
      // 只載入啟用的類別
      const activeCategories = response.data.data.filter((cat: any) => cat.is_active)

      if (activeCategories.length > 0) {
        categories.value = activeCategories
        console.log('Loaded categories:', categories.value.length) // 除錯用
      } else {
        // 如果沒有啟用的類別，至少提供一個選項
        categories.value = [
          { category_code: 'other', category_name: '其他' }
        ]
        console.warn('No active categories found, using default')
      }
    } else {
      console.error('Invalid categories response format:', response.data)
      categories.value = [
        { category_code: 'other', category_name: '其他' }
      ]
    }
  } catch (error) {
    console.error('Failed to fetch categories:', error)
    // 如果載入失敗，使用預設類別
    categories.value = [
      { category_code: 'other', category_name: '其他' }
    ]
    ElMessage.warning('無法載入物品種類，使用預設選項')
  }
}

const loadRequisition = async () => {
  if (!isEdit.value) return

  try {
    const requisition = await requisitionStore.fetchRequisitionDetail(requisitionId.value)

    // Populate form data
    formData.usage_type = requisition.usage_type || 'daily'
    formData.project_id = requisition.project_id
    formData.is_urgent = requisition.is_urgent || false
    formData.expected_delivery_date = requisition.expected_delivery_date || ''
    formData.urgent_reason = requisition.urgent_reason || ''

    // Map requisition items to form items
    if (requisition.items && requisition.items.length > 0) {
      formData.items = requisition.items.map((item: any) => ({
        item_name: item.item_name || '',
        item_quantity: item.item_quantity || 1,
        item_unit: item.item_unit || '個',
        item_specification: item.item_specification || '',
        item_description: item.item_description || '',
        item_category: item.item_category || ''
      }))
    } else {
      // If no items, add one empty item
      addItem()
    }

    ElMessage.success('請購單數據載入完成')
  } catch (error) {
    ElMessage.error('載入請購單失敗')
    router.push('/requisitions')
  }
}

// Initialize with one empty item for new requisitions
onMounted(async () => {
  // 並行載入專案和類別
  await Promise.all([
    fetchProjects(),
    fetchCategories()
  ])

  if (isEdit.value) {
    await loadRequisition()
  } else {
    addItem()
  }
})
</script>

<style scoped>
.requisition-form {
  .form-section {
    margin-bottom: 32px;
    
    .section-title {
      margin: 0 0 16px 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      border-bottom: 2px solid #409eff;
      padding-bottom: 8px;
    }
    
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
  }
  
  .empty-items {
    text-align: center;
    padding: 40px;
    border: 2px dashed #dcdfe6;
    border-radius: 6px;
    margin-top: 16px;
  }
  
  .form-actions {
    display: flex;
    justify-content: center;
    gap: 16px;
    padding-top: 24px;
    border-top: 1px solid #ebeef5;
    margin-top: 32px;
  }
  
  .field-error {
    color: #f56c6c;
    font-size: 12px;
    margin-top: 4px;
    line-height: 1;
  }
  
  .is-error {
    :deep(.el-input__inner) {
      border-color: #f56c6c;
    }
    
    :deep(.el-input-number .el-input__inner) {
      border-color: #f56c6c;
    }
  }

  /* 加急設定樣式 */
  .urgent-details {
    background: #fff2f0;
    border: 1px solid #ffccc7;
    border-radius: 6px;
    padding: 16px;
    margin-top: 16px;
  }

  .urgent-details .el-form-item__label {
    color: #cf1322;
    font-weight: 600;
  }

  .urgent-checkbox .urgent-label {
    color: #cf1322;
    font-weight: 600;
  }

  .urgent-date-picker :deep(.el-input__inner) {
    border-color: #ff7875;
  }

  .urgent-date-picker :deep(.el-input__inner:focus) {
    border-color: #cf1322;
    box-shadow: 0 0 0 2px rgba(207, 19, 34, 0.2);
  }

  .urgent-reason-input :deep(.el-textarea__inner) {
    border-color: #ff7875;
  }

  .urgent-reason-input :deep(.el-textarea__inner:focus) {
    border-color: #cf1322;
    box-shadow: 0 0 0 2px rgba(207, 19, 34, 0.2);
  }
}

/* Responsive */
@media (max-width: 768px) {
  .requisition-form {
    .section-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;
    }
    
    .form-actions {
      flex-direction: column;
      
      .el-button {
        width: 100%;
      }
    }
  }
}
</style>