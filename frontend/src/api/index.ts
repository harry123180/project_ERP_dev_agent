import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// Request interceptor - Enhanced for token reliability
api.interceptors.request.use(
  (config) => {
    // Add auth token to requests with enhanced reliability checks
    const token = localStorage.getItem('auth_token')
    if (token && token !== 'null' && token !== 'undefined' && token.trim()) {
      // Ensure the token is properly formatted
      config.headers.Authorization = `Bearer ${token}`
      console.log(`[AUTH] Token attached to request: ${config.url}`)
    } else {
      // Log when no token is available for debugging
      console.log(`[AUTH] No valid token available for request: ${config.url}`)
    }
    
    // Ensure headers object exists
    config.headers = config.headers || {}
    
    return config
  },
  (error) => {
    console.error('[AUTH] Request interceptor error:', error)
    return Promise.reject(error)
  }
)

// Global flag to prevent concurrent refresh attempts
let isRefreshing = false
let refreshPromise: Promise<any> | null = null

// Response interceptor with enhanced token refresh protection
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && originalRequest) {
      // Check if this is already a refresh request to prevent infinite loop
      const isRefreshRequest = originalRequest.url?.includes('/auth/refresh')
      
      if (!isRefreshRequest && !originalRequest._retry) {
        originalRequest._retry = true
        
        // If a refresh is already in progress, wait for it
        if (isRefreshing && refreshPromise) {
          try {
            await refreshPromise
            const newToken = localStorage.getItem('auth_token')
            if (newToken) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`
              return api.request(originalRequest)
            }
          } catch {
            // If refresh failed, redirect to login
            localStorage.clear()
            if (window.location.pathname !== '/login') {
              window.location.href = '/login'
            }
          }
          return Promise.reject(error)
        }
        
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          isRefreshing = true
          
          refreshPromise = fetch('/api/v1/auth/refresh', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${refreshToken}`
            }
          })
          .then(async response => {
            if (response.ok) {
              const data = await response.json()
              localStorage.setItem('auth_token', data.access_token)
              localStorage.setItem('refresh_token', data.refresh_token)
              localStorage.setItem('user_data', JSON.stringify(data.user))
              console.log('[AUTH] Token refresh successful')
              return data.access_token
            } else {
              throw new Error(`HTTP ${response.status}`)
            }
          })
          .catch(refreshError => {
            console.error('[AUTH] Token refresh failed:', refreshError)
            localStorage.clear()
            if (window.location.pathname !== '/login') {
              window.location.href = '/login'
            }
            throw refreshError
          })
          .finally(() => {
            isRefreshing = false
            refreshPromise = null
          })
          
          try {
            const newToken = await refreshPromise
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            return api.request(originalRequest)
          } catch {
            return Promise.reject(error)
          }
        } else {
          // No refresh token, clear storage and redirect
          localStorage.clear()
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
        }
      }
    } else if (error.response?.status === 403) {
      ElMessage.error('權限不足')
    } else if (error.response?.status >= 500) {
      ElMessage.error('服務器錯誤，請稍後重試')
    } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
      ElMessage.error('網絡連接錯誤')
    }
    
    return Promise.reject(error)
  }
)

export default api

// Type definitions for common API responses
export interface ApiResponse<T = any> {
  data?: T
  message?: string
  error?: {
    code: string
    message: string
    details: Record<string, any>
  }
}

export interface PaginatedResponse<T = any> {
  items: T[]
  pagination: {
    page: number
    page_size: number
    total: number
    pages: number
  }
}

// Common API error handling
export const handleApiError = (error: any, defaultMessage = '操作失敗') => {
  const message = error.response?.data?.error?.message || error.message || defaultMessage
  ElMessage.error(message)
  return message
}

// Helper function for creating request with idempotency key
export const createIdempotentRequest = () => {
  return {
    'Idempotency-Key': `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }
}

// Export all API services
export { authApi } from './auth'
export { requisitionApi } from './requisition'
export { procurementApi } from './procurement'
export { leadtimeApi } from './leadtime'
export { receivingApi } from './receiving'
export { storageApi } from './storage'
export { inventoryApi } from './inventory'
export { accountingApi } from './accounting'
export { suppliersApi } from './suppliers'
export { projectsApi } from './projects'
export { usersApi } from './users'
export { systemApi } from './system'