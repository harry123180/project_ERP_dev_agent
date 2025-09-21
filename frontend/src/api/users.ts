import api, { type PaginatedResponse } from './index'
import type { User, UserRoleType } from '@/types/auth'

export interface UserFilters {
  role?: UserRoleType
  active?: boolean
  page?: number
  page_size?: number
  search?: string
  department?: string
  active_only?: boolean
}

export interface UserSearchFilters {
  q?: string
  role?: UserRoleType
  department?: string
  is_active?: boolean
  page?: number
  page_size?: number
}

export interface CreateUserRequest {
  username: string
  chinese_name: string
  password: string
  department?: string
  job_title?: string
  role: UserRoleType
  is_active?: boolean
}

export interface UpdateUserRequest {
  chinese_name?: string
  department?: string
  job_title?: string
  role?: UserRoleType
  is_active?: boolean
}

export interface UpdatePasswordRequest {
  new_password: string
}

export interface ResetPasswordRequest {
  new_password: string
}

export interface UserStatistics {
  total_users: number
  active_users: number
  inactive_users: number
  role_distribution: Record<UserRoleType, number>
  department_distribution: Array<{
    department: string
    count: number
  }>
}

export interface Role {
  value: UserRoleType
  label: string
}

export const usersApi = {
  // List users (admin only)
  getUsers: async (filters: UserFilters = {}): Promise<PaginatedResponse<User>> => {
    const response = await api.get('/users', { params: filters })
    return response.data
  },

  // Search users with advanced filtering (admin only)
  searchUsers: async (filters: UserSearchFilters = {}): Promise<PaginatedResponse<User>> => {
    const response = await api.get('/users/search', { params: filters })
    return response.data
  },

  // Get user statistics (admin only)
  getUserStatistics: async (): Promise<UserStatistics> => {
    const response = await api.get('/users/statistics')
    return response.data
  },

  // Get available roles
  getRoles: async (): Promise<Role[]> => {
    const response = await api.get('/users/roles')
    return response.data.roles
  },

  // Get user profile
  getUser: async (id: number): Promise<User> => {
    const response = await api.get(`/users/${id}`)
    return response.data
  },

  // Create user (admin only)
  createUser: async (data: CreateUserRequest): Promise<User> => {
    const response = await api.post('/users', data)
    return response.data
  },

  // Update user profile
  updateUser: async (id: number, data: UpdateUserRequest): Promise<User> => {
    const response = await api.put(`/users/${id}`, data)
    return response.data
  },

  // Delete user (soft delete) (admin only)
  deleteUser: async (id: number): Promise<void> => {
    await api.delete(`/users/${id}`)
  },

  // Reset user password (admin only)
  resetUserPassword: async (id: number, data: ResetPasswordRequest): Promise<void> => {
    await api.post(`/users/${id}/reset-password`, data)
  },

  // Activate user (admin only)
  activateUser: async (id: number): Promise<void> => {
    await api.post(`/users/${id}/activate`)
  },

  // Update user password (admin only) - legacy endpoint
  updateUserPassword: async (id: number, data: UpdatePasswordRequest): Promise<void> => {
    await api.put(`/users/${id}/password`, data)
  }
}