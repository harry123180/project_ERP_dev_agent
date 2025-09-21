import api from './index'
import type { SystemSettings } from '@/types/common'

export interface SystemSettingsData {
  tax_rate: number
  default_payment_terms: string
  system_name: string
  company_name: string
  [key: string]: any
}

export interface UpdateSettingsRequest {
  settings: {
    setting_key: string
    setting_value: string
  }[]
}

export const systemApi = {
  // Get system settings
  getSettings: async (): Promise<SystemSettingsData> => {
    const response = await api.get('/system/settings')
    return response.data
  },

  // Update system settings (admin only)
  updateSettings: async (data: UpdateSettingsRequest): Promise<SystemSettingsData> => {
    const response = await api.put('/system/settings', data)
    return response.data
  }
}