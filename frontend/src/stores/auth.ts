import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api/auth'
import type { User, LoginRequest, LoginResponse } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const user = ref<User | null>(null)
  const loading = ref(false)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const userRole = computed(() => user.value?.role || '')
  const userName = computed(() => user.value?.chinese_name || user.value?.username || '')

  // Actions
  const login = async (credentials: LoginRequest) => {
    try {
      loading.value = true
      const response = await authApi.login(credentials)
      
      setAuthData(response)
      
      ElMessage.success('登入成功')
      // Navigate using window.location to avoid router issues
      window.location.href = '/'
    } catch (error: any) {
      ElMessage.error(error.response?.data?.error?.message || '登入失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    try {
      if (token.value) {
        await authApi.logout()
      }
    } catch (error) {
      console.error('Logout API error:', error)
    } finally {
      clearAuthData()
      ElMessage.success('已登出')
      window.location.href = '/login'
    }
  }

  const refreshAuthToken = async () => {
    try {
      if (!refreshToken.value) {
        throw new Error('No refresh token available')
      }
      
      // Use direct axios call to avoid interceptor loop
      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${refreshToken.value}`
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      const data = await response.json()
      setAuthData(data)
      return true
    } catch (error) {
      console.error('Token refresh failed:', error)
      clearAuthData()
      window.location.href = '/login'
      return false
    }
  }

  const changePassword = async (currentPassword: string, newPassword: string) => {
    try {
      await authApi.changePassword({ current_password: currentPassword, new_password: newPassword })
      ElMessage.success('密碼修改成功')
    } catch (error: any) {
      ElMessage.error(error.response?.data?.error?.message || '密碼修改失敗')
      throw error
    }
  }

  const setAuthData = (data: LoginResponse) => {
    token.value = data.access_token
    refreshToken.value = data.refresh_token
    user.value = data.user
    
    // Store in localStorage
    localStorage.setItem('auth_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user_data', JSON.stringify(data.user))
  }

  const clearAuthData = () => {
    token.value = null
    refreshToken.value = null
    user.value = null
    
    // Clear localStorage
    localStorage.removeItem('auth_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_data')
  }

  const initializeAuth = () => {
    // Restore auth state from localStorage
    const storedToken = localStorage.getItem('auth_token')
    const storedRefreshToken = localStorage.getItem('refresh_token')
    const storedUser = localStorage.getItem('user_data')

    if (storedToken && storedRefreshToken && storedUser) {
      try {
        token.value = storedToken
        refreshToken.value = storedRefreshToken
        user.value = JSON.parse(storedUser)
      } catch (error) {
        console.error('Failed to parse stored user data:', error)
        clearAuthData()
      }
    }
  }

  const hasRole = (...roles: string[]): boolean => {
    if (!user.value) return false
    if (user.value.role === 'Admin') return true // Admin has all permissions
    return roles.includes(user.value.role)
  }

  const updateUserProfile = (updatedUser: Partial<User>) => {
    if (user.value) {
      user.value = { ...user.value, ...updatedUser }
      localStorage.setItem('user_data', JSON.stringify(user.value))
    }
  }

  return {
    // State
    token,
    refreshToken,
    user,
    loading,
    
    // Getters
    isAuthenticated,
    userRole,
    userName,
    
    // Actions
    login,
    logout,
    refreshAuthToken,
    changePassword,
    initializeAuth,
    hasRole,
    updateUserProfile,
    clearAuthData
  }
})