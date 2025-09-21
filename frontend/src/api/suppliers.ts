import api, { type PaginatedResponse } from './index'
import type { Supplier } from '@/types/common'

export interface SupplierFilters {
  region?: 'domestic' | 'international'
  active?: boolean
  page?: number
  page_size?: number
  search?: string
}

export interface CreateSupplierRequest {
  supplier_id: string
  supplier_name_zh: string
  supplier_name_en?: string
  supplier_address?: string
  supplier_phone?: string
  supplier_email?: string
  supplier_contact_person?: string
  supplier_tax_id?: string
  supplier_region: 'domestic' | 'international'
  supplier_remark?: string
  payment_terms?: string
  bank_account?: string
}

export interface UpdateSupplierRequest extends Partial<CreateSupplierRequest> {
  is_active?: boolean
}

export const suppliersApi = {
  // List suppliers
  getSuppliers: async (filters: SupplierFilters = {}): Promise<PaginatedResponse<Supplier>> => {
    const response = await api.get('/suppliers', { params: filters })
    return response.data
  },

  // Get supplier detail
  getSupplier: async (id: string): Promise<Supplier> => {
    const response = await api.get(`/suppliers/${id}`)
    return response.data
  },

  // Create supplier
  createSupplier: async (data: CreateSupplierRequest): Promise<Supplier> => {
    const response = await api.post('/suppliers', data)
    return response.data
  },

  // Update supplier
  updateSupplier: async (id: string, data: UpdateSupplierRequest): Promise<Supplier> => {
    const response = await api.put(`/suppliers/${id}`, data)
    return response.data
  },

  // Get all active suppliers for dropdown
  getActiveSuppliers: async (): Promise<Supplier[]> => {
    const response = await api.get('/suppliers', { 
      params: { active: true, page_size: 1000 } 
    })
    return response.data.items || []
  }
}