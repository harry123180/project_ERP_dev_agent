<template>
  <div class="login-container">
    <div class="login-wrapper">
      <div class="login-card">
        <div class="login-header">
          <h2 class="login-title">ERP 系統登入</h2>
          <p class="login-subtitle">企業資源管理系統</p>
        </div>
        
        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="請輸入用戶名"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="請輸入密碼"
              size="large"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              class="login-button"
              :loading="authStore.loading"
              @click="handleLogin"
            >
              {{ authStore.loading ? '登入中...' : '登入' }}
            </el-button>
          </el-form-item>
        </el-form>
        
        <div class="login-footer">
          <div class="demo-accounts">
            <h4>測試帳號：</h4>
            <div class="account-list">
              <div class="account-item" @click="fillAccount('admin', 'admin123')">
                <span class="role">管理員</span>
                <span class="username">admin</span>
              </div>
              <div class="account-item" @click="fillAccount('procurement', 'proc123')">
                <span class="role">採購員</span>
                <span class="username">procurement</span>
              </div>
              <div class="account-item" @click="fillAccount('engineer', 'eng123')">
                <span class="role">工程師</span>
                <span class="username">engineer</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="login-background">
      <div class="bg-decoration"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import type { FormInstance, FormRules } from 'element-plus'

const authStore = useAuthStore()

const loginFormRef = ref<FormInstance>()
const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules: FormRules = {
  username: [
    { required: true, message: '請輸入用戶名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '請輸入密碼', trigger: 'blur' },
    { min: 6, message: '密碼長度至少6位', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  try {
    await loginFormRef.value.validate()
    await authStore.login({
      username: loginForm.username,
      password: loginForm.password
    })
  } catch (error) {
    console.error('Login failed:', error)
  }
}

const fillAccount = (username: string, password: string) => {
  loginForm.username = username
  loginForm.password = password
}
</script>

<style lang="scss" scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

.login-wrapper {
  width: 100%;
  max-width: 400px;
  padding: 20px;
  z-index: 2;
}

.login-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 40px 32px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
  
  .login-title {
    font-size: 28px;
    font-weight: 600;
    color: #2c3e50;
    margin: 0 0 8px 0;
  }
  
  .login-subtitle {
    font-size: 14px;
    color: #7f8c8d;
    margin: 0;
  }
}

.login-form {
  .el-form-item {
    margin-bottom: 24px;
  }
  
  .login-button {
    width: 100%;
    height: 48px;
    font-size: 16px;
    font-weight: 500;
    border-radius: 8px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    
    &:hover {
      opacity: 0.9;
    }
  }
}

.login-footer {
  margin-top: 32px;
  
  .demo-accounts {
    h4 {
      font-size: 14px;
      color: #7f8c8d;
      margin: 0 0 12px 0;
      text-align: center;
    }
    
    .account-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    
    .account-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      background: rgba(103, 126, 234, 0.1);
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.3s;
      
      &:hover {
        background: rgba(103, 126, 234, 0.2);
        transform: translateY(-1px);
      }
      
      .role {
        font-size: 12px;
        color: #667eea;
        font-weight: 500;
      }
      
      .username {
        font-size: 12px;
        color: #7f8c8d;
        font-family: monospace;
      }
    }
  }
}

.login-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
  
  .bg-decoration {
    position: absolute;
    width: 200%;
    height: 200%;
    top: -50%;
    left: -50%;
    background: 
      radial-gradient(circle at 25% 25%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
      radial-gradient(circle at 75% 75%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
    animation: rotate 20s linear infinite;
  }
}

@keyframes rotate {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

// Responsive design
@media (max-width: 480px) {
  .login-wrapper {
    padding: 16px;
  }
  
  .login-card {
    padding: 32px 24px;
  }
  
  .login-header .login-title {
    font-size: 24px;
  }
}
</style>