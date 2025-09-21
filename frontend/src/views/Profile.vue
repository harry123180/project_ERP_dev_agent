<template>
  <div class="profile-container">
    <div class="profile-header">
      <h1>個人資料</h1>
    </div>
    
    <div class="profile-content">
      <el-card class="profile-card">
        <template #header>
          <div class="card-header">
            <span>基本資訊</span>
            <el-button 
              v-if="!isEditing" 
              type="primary" 
              @click="startEdit"
              icon="Edit"
            >
              編輯
            </el-button>
          </div>
        </template>
        
        <el-form 
          ref="profileFormRef"
          :model="profileForm" 
          :rules="rules"
          label-width="120px"
          :disabled="!isEditing"
        >
          <el-form-item label="用戶名稱">
            <el-input v-model="profileForm.username" disabled />
          </el-form-item>
          
          <el-form-item label="暱稱" prop="chinese_name">
            <el-input v-model="profileForm.chinese_name" placeholder="請輸入暱稱" />
          </el-form-item>
          
          <el-form-item label="職稱" prop="job_title">
            <el-input v-model="profileForm.job_title" placeholder="請輸入職稱" />
          </el-form-item>
          
          <el-form-item label="部門名稱" prop="department">
            <el-input v-model="profileForm.department" placeholder="請輸入部門名稱" />
          </el-form-item>
          
          <el-form-item label="角色">
            <el-tag :type="getRoleTagType(profileForm.role)">
              {{ getRoleText(profileForm.role) }}
            </el-tag>
          </el-form-item>
          
          <el-form-item label="帳號狀態">
            <el-tag :type="profileForm.is_active ? 'success' : 'danger'">
              {{ profileForm.is_active ? '啟用' : '停用' }}
            </el-tag>
          </el-form-item>
          
          <el-form-item label="建立時間">
            <span>{{ formatDate(profileForm.created_at) }}</span>
          </el-form-item>
          
          <el-form-item label="最後更新">
            <span>{{ formatDate(profileForm.updated_at) }}</span>
          </el-form-item>
          
          <el-form-item v-if="isEditing">
            <el-button type="primary" @click="saveProfile">保存</el-button>
            <el-button @click="cancelEdit">取消</el-button>
          </el-form-item>
        </el-form>
      </el-card>
      
      <el-card class="password-card">
        <template #header>
          <span>修改密碼</span>
        </template>
        
        <el-form 
          ref="passwordFormRef"
          :model="passwordForm" 
          :rules="passwordRules"
          label-width="120px"
        >
          <el-form-item label="當前密碼" prop="current_password">
            <el-input 
              v-model="passwordForm.current_password" 
              type="password"
              placeholder="請輸入當前密碼"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="新密碼" prop="new_password">
            <el-input 
              v-model="passwordForm.new_password" 
              type="password"
              placeholder="請輸入新密碼（至少6個字符）"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="確認新密碼" prop="confirm_password">
            <el-input 
              v-model="passwordForm.confirm_password" 
              type="password"
              placeholder="請再次輸入新密碼"
              show-password
            />
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" @click="changePassword">修改密碼</el-button>
            <el-button @click="resetPasswordForm">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

// Store
const authStore = useAuthStore()

// Form refs
const profileFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()

// State
const isEditing = ref(false)
const loading = ref(false)

// Profile form data
const profileForm = reactive({
  username: '',
  chinese_name: '',
  job_title: '',
  department: '',
  role: '',
  is_active: true,
  created_at: '',
  updated_at: ''
})

// Original data for cancel
const originalProfile = ref({})

// Password form data
const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

// Validation rules
const rules: FormRules = {
  chinese_name: [
    { required: true, message: '請輸入暱稱', trigger: 'blur' },
    { min: 2, max: 20, message: '暱稱長度在 2 到 20 個字符', trigger: 'blur' }
  ],
  job_title: [
    { max: 50, message: '職稱不能超過 50 個字符', trigger: 'blur' }
  ],
  department: [
    { max: 50, message: '部門名稱不能超過 50 個字符', trigger: 'blur' }
  ]
}

const passwordRules: FormRules = {
  current_password: [
    { required: true, message: '請輸入當前密碼', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '請輸入新密碼', trigger: 'blur' },
    { min: 6, message: '密碼長度至少 6 個字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '請確認新密碼', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('兩次輸入的密碼不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// Methods
const loadProfile = async () => {
  loading.value = true
  try {
    const response = await api.get('/profile')
    const data = response.data.data
    Object.assign(profileForm, data)
    originalProfile.value = { ...data }
  } catch (error) {
    console.error('Failed to load profile:', error)
    ElMessage.error('載入個人資料失敗')
  } finally {
    loading.value = false
  }
}

const startEdit = () => {
  isEditing.value = true
  originalProfile.value = { ...profileForm }
}

const cancelEdit = () => {
  Object.assign(profileForm, originalProfile.value)
  isEditing.value = false
}

const saveProfile = async () => {
  if (!profileFormRef.value) return
  
  await profileFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      loading.value = true
      const response = await api.put('/profile', {
        chinese_name: profileForm.chinese_name,
        job_title: profileForm.job_title,
        department: profileForm.department
      })

      // Handle different response structures
      const data = response.data.data || response.data
      const updatedUser = data.user || data
      Object.assign(profileForm, updatedUser)

      // Update the auth store with the new profile data
      authStore.updateUserProfile({
        chinese_name: updatedUser.chinese_name,
        job_title: updatedUser.job_title,
        department: updatedUser.department
      })

      isEditing.value = false
      ElMessage.success('個人資料更新成功')
    } catch (error) {
      console.error('Failed to update profile:', error)
      ElMessage.error('更新個人資料失敗')
    } finally {
      loading.value = false
    }
  })
}

const changePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      loading.value = true
      await api.put('/profile/password', {
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password
      })
      
      ElMessage.success('密碼修改成功')
      resetPasswordForm()
    } catch (error: any) {
      console.error('Failed to change password:', error)
      if (error.response?.data?.error?.code === 'INVALID_PASSWORD') {
        ElMessage.error('當前密碼不正確')
      } else {
        ElMessage.error('修改密碼失敗')
      }
    } finally {
      loading.value = false
    }
  })
}

const resetPasswordForm = () => {
  passwordForm.current_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
  passwordFormRef.value?.resetFields()
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-TW')
}

const getRoleText = (role: string) => {
  const roleMap: Record<string, string> = {
    'Admin': '系統管理員',
    'Procurement': '採購專員',
    'ProcurementMgr': '採購經理',
    'Manager': '部門經理',
    'IT': 'IT專員',
    'Everyone': '一般用戶'
  }
  return roleMap[role] || role
}

const getRoleTagType = (role: string) => {
  const typeMap: Record<string, string> = {
    'Admin': 'danger',
    'ProcurementMgr': 'warning',
    'Procurement': 'primary',
    'Manager': 'success',
    'IT': 'info',
    'Everyone': ''
  }
  return typeMap[role] || ''
}

// Lifecycle
onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.profile-header {
  margin-bottom: 20px;
}

.profile-header h1 {
  font-size: 24px;
  color: #303133;
  margin: 0;
}

.profile-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.profile-card,
.password-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.el-form {
  padding: 20px 20px 0;
}

.el-form-item:last-child {
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .profile-content {
    grid-template-columns: 1fr;
  }
}
</style>