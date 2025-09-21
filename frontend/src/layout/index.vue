<template>
  <el-container class="layout-container">
    <el-aside :width="sidebarWidth" class="sidebar-container">
      <div class="logo-container">
        <h2>ERP 系統</h2>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapsed"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        unique-opened
        router
      >
        <template v-for="route in menuRoutes" :key="route.path">
          <el-sub-menu v-if="route.children && route.children.length > 1" :index="`/${route.path}`">
            <template #title>
              <el-icon><component :is="route.meta?.icon || 'Menu'" /></el-icon>
              <span>{{ route.meta?.title }}</span>
            </template>
            <el-menu-item 
              v-for="child in route.children" 
              :key="child.path"
              :index="`/${route.path}${child.path ? '/' + child.path : ''}`"
            >
              {{ child.meta?.title }}
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="`/${route.path}`">
            <el-icon><component :is="route.meta?.icon || 'Menu'" /></el-icon>
            <template #title>{{ route.meta?.title }}</template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header class="header-container">
        <div class="header-left">
          <el-button :icon="Fold" text @click="toggleSidebar" />
          <breadcrumb />
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-dropdown">
              <el-avatar :size="32" :src="userAvatar">
                {{ userName.slice(0, 1) }}
              </el-avatar>
              <span class="user-name">{{ userName }}</span>
              <el-icon class="arrow-down"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">個人資料</el-dropdown-item>
                <el-dropdown-item command="password">修改密碼</el-dropdown-item>
                <el-dropdown-item divided command="logout">登出</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main class="main-container">
        <router-view />
      </el-main>
    </el-container>
    
    <!-- Change Password Dialog -->
    <el-dialog
      v-model="passwordDialogVisible"
      title="修改密碼"
      width="400px"
    >
      <el-form 
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="120px"
      >
        <el-form-item label="當前密碼" prop="currentPassword">
          <el-input 
            v-model="passwordForm.currentPassword"
            type="password"
            show-password
            placeholder="請輸入當前密碼"
          />
        </el-form-item>
        <el-form-item label="新密碼" prop="newPassword">
          <el-input 
            v-model="passwordForm.newPassword"
            type="password"
            show-password
            placeholder="請輸入新密碼"
          />
        </el-form-item>
        <el-form-item label="確認新密碼" prop="confirmPassword">
          <el-input 
            v-model="passwordForm.confirmPassword"
            type="password"
            show-password
            placeholder="請再次輸入新密碼"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleChangePassword" :loading="passwordLoading">
          確認
        </el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Fold, ArrowDown } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import Breadcrumb from './components/Breadcrumb.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// Sidebar state
const isCollapsed = ref(false)
const sidebarWidth = computed(() => isCollapsed.value ? '64px' : '200px')

// User info
const userName = computed(() => authStore.userName)
const userAvatar = ref('')

// Menu
const activeMenu = ref('')
const menuRoutes = computed(() => {
  const routes = router.getRoutes()
    .find(r => r.path === '/')?.children || []
  
  return routes.filter(route => {
    if (!route.meta?.title || route.meta.hideInMenu) return false
    
    // Check role-based access
    if (route.meta.requiresRole) {
      const requiredRoles = Array.isArray(route.meta.requiresRole) ? route.meta.requiresRole : [route.meta.requiresRole]
      return authStore.hasRole(...requiredRoles)
    }
    
    return true
  }).map(route => ({
    ...route,
    children: route.children?.filter(child => !child.meta?.hideInMenu)
  }))
})

// Password change
const passwordDialogVisible = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref()
const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordRules = {
  currentPassword: [
    { required: true, message: '請輸入當前密碼', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '請輸入新密碼', trigger: 'blur' },
    { min: 6, message: '密碼長度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '請確認新密碼', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: any) => {
        if (value !== passwordForm.value.newPassword) {
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
const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

const handleCommand = (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'password':
      router.push('/profile')
      break
    case 'logout':
      handleLogout()
      break
  }
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('確定要登出嗎？', '提示', {
      confirmButtonText: '確定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await authStore.logout()
  } catch {
    // User cancelled
  }
}

const handleChangePassword = async () => {
  try {
    await passwordFormRef.value.validate()
    
    passwordLoading.value = true
    await authStore.changePassword(passwordForm.value.currentPassword, passwordForm.value.newPassword)
    
    passwordDialogVisible.value = false
    resetPasswordForm()
  } catch (error) {
    // Error handled by auth store
  } finally {
    passwordLoading.value = false
  }
}

const resetPasswordForm = () => {
  passwordForm.value = {
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
  passwordFormRef.value?.clearValidate()
}

// Watch route changes to update active menu
watch(
  () => route.path,
  (path) => {
    activeMenu.value = path
  },
  { immediate: true }
)

// Watch dialog visibility to reset form
watch(passwordDialogVisible, (visible) => {
  if (!visible) {
    resetPasswordForm()
  }
})
</script>

<style lang="scss" scoped>
.layout-container {
  height: 100vh;
}

.sidebar-container {
  background: #304156;
  transition: width 0.3s;
  overflow: hidden;
  
  .logo-container {
    height: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #2b2f3a;
    border-bottom: 1px solid #464c5b;
    
    h2 {
      color: #fff;
      font-size: 18px;
      margin: 0;
    }
  }
  
  .el-menu {
    border: none;
    height: calc(100vh - 50px);
    overflow-y: auto;
  }
}

.header-container {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 50px;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .header-right {
    .user-dropdown {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 4px;
      transition: background-color 0.3s;
      
      &:hover {
        background: #f5f5f5;
      }
      
      .user-name {
        font-size: 14px;
        color: #606266;
      }
      
      .arrow-down {
        font-size: 12px;
        color: #909399;
      }
    }
  }
}

.main-container {
  background: #f0f2f5;
  padding: 0;
  overflow-y: auto;
}

:deep(.el-menu--collapse) {
  width: 64px;
}
</style>