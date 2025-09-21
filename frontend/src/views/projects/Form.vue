<template>
  <div class="project-form">
    <div class="page-header">
      <h1>{{ isEdit ? '編輯專案' : '新增專案' }}</h1>
    </div>

    <el-card>
      <el-form 
        ref="formRef"
        :model="form" 
        :rules="rules" 
        label-width="120px"
        :disabled="loading"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="專案代碼" prop="project_code">
              <el-input 
                v-model="form.project_code" 
                placeholder="請輸入專案代碼（選填）"
                maxlength="20"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="專案名稱" prop="project_name">
              <el-input 
                v-model="form.project_name" 
                placeholder="請輸入專案名稱"
                maxlength="200"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="專案描述" prop="description">
          <el-input 
            v-model="form.description" 
            type="textarea"
            :rows="3"
            placeholder="請輸入專案描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="專案狀態" prop="project_status">
              <el-select v-model="form.project_status" placeholder="請選擇專案狀態">
                <el-option label="進行中" value="ongoing" />
                <el-option label="已完成" value="completed" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="專案預算" prop="budget">
              <el-input-number 
                v-model="form.budget" 
                :min="0"
                :precision="0"
                :controls-position="'right'"
                placeholder="請輸入專案預算"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="開始日期" prop="start_date">
              <el-date-picker
                v-model="form.start_date"
                type="date"
                placeholder="選擇開始日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="結束日期" prop="end_date">
              <el-date-picker
                v-model="form.end_date"
                type="date"
                placeholder="選擇結束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">客戶資訊</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="客戶名稱" prop="customer_name">
              <el-input 
                v-model="form.customer_name" 
                placeholder="請輸入客戶名稱"
                maxlength="200"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客戶部門" prop="customer_department">
              <el-input 
                v-model="form.customer_department" 
                placeholder="請輸入客戶部門"
                maxlength="100"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="聯絡人" prop="customer_contact">
              <el-input 
                v-model="form.customer_contact" 
                placeholder="請輸入聯絡人姓名"
                maxlength="100"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="聯絡電話" prop="customer_phone">
              <el-input 
                v-model="form.customer_phone" 
                placeholder="請輸入聯絡電話"
                maxlength="50"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="客戶地址" prop="customer_address">
          <el-input 
            v-model="form.customer_address" 
            placeholder="請輸入客戶地址"
            maxlength="500"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="loading">
            {{ isEdit ? '更新' : '建立' }}
          </el-button>
          <el-button @click="handleCancel">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { projectsApi } from '@/api/projects'

const route = useRoute()
const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)

const isEdit = computed(() => !!route.params.id)

const form = reactive({
  project_code: '',
  project_name: '',
  description: '',
  project_status: 'ongoing',
  budget: null as number | null,
  start_date: '',
  end_date: '',
  customer_name: '',
  customer_department: '',
  customer_contact: '',
  customer_phone: '',
  customer_address: ''
})

const rules: FormRules = {
  project_name: [
    { required: true, message: '請輸入專案名稱', trigger: 'blur' },
    { min: 2, max: 200, message: '專案名稱長度在 2 到 200 個字符', trigger: 'blur' }
  ],
  project_status: [
    { required: true, message: '請選擇專案狀態', trigger: 'change' }
  ],
  start_date: [
    { required: true, message: '請選擇開始日期', trigger: 'change' }
  ],
  end_date: [
    {
      validator: (rule, value, callback) => {
        if (value && form.start_date && new Date(value) < new Date(form.start_date)) {
          callback(new Error('結束日期不能早於開始日期'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  budget: [
    { type: 'number', min: 0, message: '預算必須大於等於0', trigger: 'blur' }
  ]
}

const loadProject = async () => {
  if (!isEdit.value) return
  
  loading.value = true
  try {
    const projectId = route.params.id as string
    const project = await projectsApi.getProject(projectId)
    
    // 填充表單數據
    Object.keys(form).forEach(key => {
      if (project[key] !== undefined) {
        form[key] = project[key]
      }
    })
  } catch (error) {
    console.error('Failed to load project:', error)
    ElMessage.error('載入專案資料失敗')
    router.push('/projects')
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      const data: any = { ...form }
      
      if (isEdit.value) {
        // 更新專案
        await projectsApi.updateProject(route.params.id as string, data)
        ElMessage.success('專案更新成功')
      } else {
        // 創建新專案
        data.project_id = await projectsApi.generateProjectId()
        // 暫時設定管理者為當前用戶 (admin = 1)
        data.manager_id = 1
        await projectsApi.createProject(data)
        ElMessage.success('專案建立成功')
      }
      
      router.push('/projects')
    } catch (error) {
      console.error('Failed to save project:', error)
      ElMessage.error(isEdit.value ? '更新專案失敗' : '建立專案失敗')
    } finally {
      loading.value = false
    }
  })
}

const handleCancel = () => {
  router.push('/projects')
}

onMounted(() => {
  loadProject()
})
</script>

<style scoped>
.project-form {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 24px;
  margin: 0;
  color: #303133;
}
</style>