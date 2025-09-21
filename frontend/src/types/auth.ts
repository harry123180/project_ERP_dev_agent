export interface User {
  user_id: number
  chinese_name: string
  username: string
  department?: string
  job_title?: string
  role: string
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  user: User
  expires_in: number
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

export interface UserRole {
  value: string
  label: string
}

export type UserRoleType = 'Admin' | 'ProcurementMgr' | 'Procurement' | 'Accountant' | 'Everyone'