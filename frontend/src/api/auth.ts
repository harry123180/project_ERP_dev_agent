import api from './index'
import type { LoginRequest, LoginResponse, ChangePasswordRequest, User } from '@/types/auth'

export const authApi = {
  // Login
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await api.post('/auth/login', credentials)
    return response.data
  },

  // Logout
  logout: async (): Promise<void> => {
    await api.post('/auth/logout')
  },

  // Refresh token
  refresh: async (): Promise<LoginResponse> => {
    const response = await api.post('/auth/refresh')
    return response.data
  },

  // Get current user profile
  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/auth/me')
    return response.data
  },

  // Change password
  changePassword: async (data: ChangePasswordRequest): Promise<void> => {
    await api.post('/auth/change-password', data)
  }
}