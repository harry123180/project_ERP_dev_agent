<template>
  <div class="supplier-form">
    <!-- Header -->
    <div class="header">
      <div class="title-section">
        <h1>{{ isEdit ? '編輯供應商' : '新增供應商' }}</h1>
        <span class="subtitle">{{ isEdit ? '編輯供應商基本資料' : '建立新的供應商資料' }}</span>
      </div>
      <div class="actions">
        <el-button @click="goBack" :icon="ArrowLeft">
          返回列表
        </el-button>
      </div>
    </div>

    <!-- Main Form -->
    <el-card class="form-card" shadow="never">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
        size="default"
        @submit.prevent="handleSubmit"
      >
        <div class="form-section">
          <h3 class="section-title">基本資訊</h3>
          
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="供應商編號" prop="supplier_id">
                <el-input
                  v-model="formData.supplier_id"
                  placeholder="請輸入供應商編號"
                  :disabled="isEdit"
                  maxlength="50"
                  show-word-limit
                />
                <div class="field-help" v-if="!isEdit">
                  供應商編號一旦建立後不可修改
                </div>
              </el-form-item>
            </el-col>
            
            <el-col :span="12">
              <el-form-item label="供應商地區" prop="supplier_region">
                <el-select
                  v-model="formData.supplier_region"
                  placeholder="請選擇供應商地區"
                  style="width: 100%"
                >
                  <el-option
                    label="國內"
                    value="domestic"
                    :icon="Location"
                  />
                  <el-option
                    label="國外"
                    value="international"
                    :icon="Position"
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="中文名稱" prop="supplier_name_zh">
                <el-input
                  v-model="formData.supplier_name_zh"
                  placeholder="請輸入供應商中文名稱"
                  maxlength="200"
                  show-word-limit
                />
              </el-form-item>
            </el-col>
            
            <el-col :span="12">
              <el-form-item label="英文名稱" prop="supplier_name_en">
                <el-input
                  v-model="formData.supplier_name_en"
                  placeholder="請輸入供應商英文名稱（選填）"
                  maxlength="200"
                  show-word-limit
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="供應商地址" prop="supplier_address">
            <el-input
              v-model="formData.supplier_address"
              type="textarea"
              placeholder="請輸入供應商地址"
              :rows="3"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
        </div>

        <div class="form-section">
          <h3 class="section-title">聯絡資訊</h3>
          
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="聯絡人" prop="supplier_contact_person">
                <el-input
                  v-model="formData.supplier_contact_person"
                  placeholder="請輸入聯絡人姓名"
                  maxlength="100"
                  show-word-limit
                />
              </el-form-item>
            </el-col>
            
            <el-col :span="12">
              <el-form-item label="聯絡電話" prop="supplier_phone">
                <el-input
                  v-model="formData.supplier_phone"
                  placeholder="請輸入聯絡電話"
                  maxlength="50"
                  show-word-limit
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="電子郵件" prop="supplier_email">
            <el-input
              v-model="formData.supplier_email"
              type="email"
              placeholder="請輸入電子郵件地址"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
        </div>

        <div class="form-section">
          <h3 class="section-title">財務資訊</h3>
          
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="統一編號" prop="supplier_tax_id">
                <el-input
                  v-model="formData.supplier_tax_id"
                  placeholder="請輸入統一編號"
                  maxlength="50"
                  show-word-limit
                />
              </el-form-item>
            </el-col>
            
            <el-col :span="12">
              <el-form-item label="付款條件" prop="payment_terms">
                <el-select
                  v-model="formData.payment_terms"
                  placeholder="請選擇付款條件"
                  style="width: 100%"
                  filterable
                  allow-create
                >
                  <el-option label="現金" value="cash" />
                  <el-option label="月結30天" value="net_30" />
                  <el-option label="月結60天" value="net_60" />
                  <el-option label="月結90天" value="net_90" />
                  <el-option label="預付款" value="prepaid" />
                  <el-option label="貨到付款" value="cod" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="銀行帳戶" prop="bank_account">
            <el-input
              v-model="formData.bank_account"
              type="textarea"
              placeholder="請輸入銀行帳戶資訊"
              :rows="2"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
        </div>

        <div class="form-section">
          <h3 class="section-title">其他資訊</h3>
          
          <el-form-item label="備註" prop="supplier_remark">
            <el-input
              v-model="formData.supplier_remark"
              type="textarea"
              placeholder="請輸入備註"
              :rows="3"
              maxlength="1000"
              show-word-limit
            />
          </el-form-item>

          <el-form-item label="啟用狀態" prop="is_active" v-if="isEdit">
            <el-switch
              v-model="formData.is_active"
              :active-text="formData.is_active ? '已啟用' : '已停用'"
              :inactive-text="formData.is_active ? '已啟用' : '已停用'"
              active-color="#67c23a"
              inactive-color="#f56c6c"
            />
          </el-form-item>
        </div>

        <!-- Form Actions -->
        <div class="form-actions">
          <el-button @click="goBack" size="large">
            取消
          </el-button>
          <el-button 
            type="primary" 
            @click="handleSubmit"
            :loading="loading"
            size="large"
          >
            {{ isEdit ? '更新' : '建立' }}
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { ArrowLeft, Location, Position } from '@element-plus/icons-vue'
import { useSuppliersStore } from '@/stores/suppliers'
import type { Supplier } from '@/stores/suppliers'

const route = useRoute()
const router = useRouter()
const suppliersStore = useSuppliersStore()

// Form reference
const formRef = ref<FormInstance>()

// Computed properties
const isEdit = computed(() => !!route.params.id)
const loading = computed(() => suppliersStore.loading)

// Form data
const formData = reactive<Partial<Supplier>>({
  supplier_id: '',
  supplier_name_zh: '',
  supplier_name_en: '',
  supplier_address: '',
  supplier_phone: '',
  supplier_email: '',
  supplier_contact_person: '',
  supplier_tax_id: '',
  supplier_region: 'domestic',
  supplier_remark: '',
  payment_terms: '',
  bank_account: '',
  is_active: true
})

// Form validation rules
const formRules = {
  supplier_id: [
    { required: true, message: '請輸入供應商編號', trigger: 'blur' },
    { min: 2, max: 50, message: '供應商編號長度應為2-50個字符', trigger: 'blur' },
    { 
      pattern: /^[A-Za-z0-9_-]+$/, 
      message: '供應商編號只能包含字母、數字、底線和短橫線', 
      trigger: 'blur' 
    }
  ],
  supplier_name_zh: [
    { required: true, message: '請輸入供應商中文名稱', trigger: 'blur' },
    { min: 2, max: 200, message: '供應商名稱長度應為2-200個字符', trigger: 'blur' }
  ],
  supplier_name_en: [
    { max: 200, message: '英文名稱長度不能超過200個字符', trigger: 'blur' }
  ],
  supplier_region: [
    { required: true, message: '請選擇供應商地區', trigger: 'change' }
  ],
  supplier_email: [
    { 
      type: 'email', 
      message: '請輸入正確的電子郵件格式', 
      trigger: ['blur', 'change'] 
    }
  ],
  supplier_phone: [
    { 
      pattern: /^[\d\s\-\+\(\)]+$/, 
      message: '請輸入有效的電話號碼', 
      trigger: 'blur' 
    }
  ]
}

// Methods
const fetchSupplier = async () => {
  if (!isEdit.value) return
  
  try {
    const supplier = await suppliersStore.fetchSupplierById(route.params.id as string)
    Object.assign(formData, supplier)
  } catch (error) {
    ElMessage.error('載入供應商資料失敗')
    goBack()
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    // Validate form
    await formRef.value.validate()
    
    // Show confirmation
    await ElMessageBox.confirm(
      `確定要${isEdit.value ? '更新' : '建立'}這個供應商嗎？`,
      '確認操作',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // Submit form
    if (isEdit.value) {
      await suppliersStore.updateSupplier(route.params.id as string, formData)
      ElMessage.success('供應商資料更新成功')
    } else {
      await suppliersStore.createSupplier(formData)
      ElMessage.success('供應商建立成功')
    }
    
    goBack()
  } catch (error: any) {
    if (error === 'cancel') {
      return // User cancelled
    }
    
    // Handle specific error cases
    if (error?.response?.data?.error?.code === 'SUPPLIER_EXISTS') {
      ElMessage.error('供應商編號已存在，請使用不同的編號')
      return
    }
    
    if (error?.response?.data?.error?.code === 'INVALID_REGION') {
      ElMessage.error('供應商地區選擇無效')
      return
    }
    
    ElMessage.error(`${isEdit.value ? '更新' : '建立'}供應商失敗`)
  }
}

const goBack = () => {
  router.push('/suppliers')
}

// Lifecycle
onMounted(() => {
  if (isEdit.value) {
    fetchSupplier()
  }
})
</script>

<style scoped>
.supplier-form {
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

.form-card {
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  background: white;
}

.form-card :deep(.el-card__body) {
  padding: 32px;
}

.form-section {
  margin-bottom: 32px;
}

.form-section:last-of-type {
  margin-bottom: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 20px 0;
  padding-bottom: 12px;
  border-bottom: 2px solid #f0f0f0;
  position: relative;
}

.section-title::before {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 60px;
  height: 2px;
  background-color: #409eff;
}

.field-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.form-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
}

/* Form item customization */
:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

:deep(.el-form-item__error) {
  position: static;
  margin-top: 4px;
  font-size: 12px;
}

/* Input customization */
:deep(.el-input__wrapper) {
  border-radius: 6px;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  border-color: #c0c4cc;
}

:deep(.el-input.is-focus .el-input__wrapper) {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

:deep(.el-textarea__inner) {
  border-radius: 6px;
  transition: all 0.3s ease;
}

:deep(.el-textarea.is-focus .el-textarea__inner) {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

/* Select customization */
:deep(.el-select .el-input.is-focus .el-input__wrapper) {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

/* Switch customization */
:deep(.el-switch) {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

:deep(.el-switch__label) {
  font-size: 14px;
  color: #606266;
}

/* Button customization */
:deep(.el-button) {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

:deep(.el-button--large) {
  padding: 12px 24px;
  font-size: 16px;
}

:deep(.el-button--primary) {
  background-color: #409eff;
  border-color: #409eff;
}

:deep(.el-button--primary:hover) {
  background-color: #66b1ff;
  border-color: #66b1ff;
}

/* Row and column spacing */
:deep(.el-row) {
  margin-left: -12px;
  margin-right: -12px;
}

:deep(.el-col) {
  padding-left: 12px;
  padding-right: 12px;
}

/* Disabled input styling */
:deep(.el-input.is-disabled .el-input__wrapper) {
  background-color: #f5f7fa;
  border-color: #e4e7ed;
  color: #c0c4cc;
}

/* Word limit styling */
:deep(.el-input__count) {
  color: #909399;
  font-size: 12px;
}

:deep(.el-textarea__count) {
  color: #909399;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.8);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .supplier-form {
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
  
  .form-card :deep(.el-card__body) {
    padding: 24px;
  }
  
  .section-title {
    font-size: 16px;
  }
  
  .form-actions {
    flex-direction: column;
    gap: 12px;
  }
  
  .form-actions .el-button {
    width: 100%;
  }
  
  /* Stack form items on mobile */
  :deep(.el-row) {
    flex-direction: column;
  }
  
  :deep(.el-col) {
    width: 100% !important;
    flex: none !important;
    max-width: 100% !important;
  }
}

@media (max-width: 480px) {
  .form-card :deep(.el-card__body) {
    padding: 16px;
  }
  
  .form-section {
    margin-bottom: 24px;
  }
  
  .section-title {
    font-size: 14px;
    margin-bottom: 16px;
  }
}

/* Loading state */
:deep(.el-loading-mask) {
  background-color: rgba(255, 255, 255, 0.8);
}

/* Focus and hover animations */
.form-card {
  transition: all 0.3s ease;
}

.form-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

/* Form validation styling */
:deep(.el-form-item.is-error .el-input__wrapper) {
  border-color: #f56c6c;
  box-shadow: 0 0 0 2px rgba(245, 108, 108, 0.1);
}

:deep(.el-form-item.is-error .el-textarea__inner) {
  border-color: #f56c6c;
  box-shadow: 0 0 0 2px rgba(245, 108, 108, 0.1);
}

:deep(.el-form-item.is-success .el-input__wrapper) {
  border-color: #67c23a;
}

:deep(.el-form-item.is-success .el-textarea__inner) {
  border-color: #67c23a;
}
</style>