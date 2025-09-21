import api, { type PaginatedResponse } from './index'
import type { RequestOrder, RequestOrderItem } from '@/types/common'

export interface RequisitionFilters {
  mine?: boolean
  status?: string
  page?: number
  page_size?: number
}

export interface CreateRequisitionRequest {
  usage_type: 'daily' | 'project'
  project_id?: string
  status?: 'draft' | 'submitted'  // CRITICAL FIX: Add status field
  items: {
    item_name: string
    item_quantity: number
    item_unit: string
    item_specification?: string
    item_description?: string
    item_category?: string
  }[]
}

export interface ApproveItemRequest {
  supplier_id: string
  unit_price: number
}

export interface RejectItemRequest {
  reason: string
}

export interface QuestionItemRequest {
  reason: string
}

export interface RejectRequisitionRequest {
  reason: string
}

export interface SaveChangesRequest {
  supplier_id?: string
  unit_price?: number
  status_note?: string
}

export interface CancelRequisitionRequest {
  reason: string
}

export const requisitionApi = {
  // List requisitions
  getRequisitions: async (filters: RequisitionFilters = {}): Promise<PaginatedResponse<RequestOrder>> => {
    const response = await api.get('/requisitions', { params: filters })
    return response.data
  },

  // Get requisition detail
  getRequisition: async (id: string): Promise<RequestOrder> => {
    const response = await api.get(`/requisitions/${id}`)
    return response.data
  },

  // Create requisition
  createRequisition: async (data: CreateRequisitionRequest): Promise<RequestOrder> => {
    const response = await api.post('/requisitions', data)
    return response.data
  },

  // Update requisition
  updateRequisition: async (id: string, data: Partial<CreateRequisitionRequest>): Promise<RequestOrder> => {
    const response = await api.put(`/requisitions/${id}`, data)
    return response.data
  },

  // Submit requisition
  submitRequisition: async (id: string): Promise<RequestOrder> => {
    const response = await api.post(`/requisitions/${id}/submit`)
    return response.data
  },

  // Approve requisition item
  approveItem: async (requisitionId: string, detailId: number, data: ApproveItemRequest): Promise<RequestOrderItem> => {
    const response = await api.post(`/requisitions/${requisitionId}/lines/${detailId}/approve`, data)
    return response.data
  },

  // Question requisition item
  questionItem: async (requisitionId: string, detailId: number, data: QuestionItemRequest): Promise<RequestOrderItem> => {
    const response = await api.post(`/requisitions/${requisitionId}/lines/${detailId}/question`, data)
    return response.data
  },

  // Reject requisition item
  rejectItem: async (requisitionId: string, detailId: number, data: RejectItemRequest): Promise<RequestOrderItem> => {
    const response = await api.post(`/requisitions/${requisitionId}/lines/${detailId}/reject`, data)
    return response.data
  },

  // Reject entire requisition
  rejectRequisition: async (id: string, data: RejectRequisitionRequest): Promise<RequestOrder> => {
    const response = await api.post(`/requisitions/${id}/reject`, data)
    return response.data
  },

  // Save changes to item without approval - EMERGENCY HOTFIX
  saveItemChanges: async (requisitionId: string, detailId: number, data: SaveChangesRequest): Promise<RequestOrderItem> => {
    const payload = { ...data, detail_id: detailId }
    console.log(`[EMERGENCY_HOTFIX] Making API call to /requisitions/${requisitionId}/fix-status with payload:`, payload)
    const response = await api.post(`/requisitions/${requisitionId}/fix-status`, payload)
    return response.data
  },

  // Cancel/withdraw requisition
  cancelRequisition: async (id: string, data: CancelRequisitionRequest): Promise<RequestOrder> => {
    const response = await api.post(`/requisitions/${id}/cancel`, data)
    return response.data
  },

  // Get questioned items
  getQuestionedItems: async (params?: any): Promise<any> => {
    const response = await api.get('/requisitions/questioned-items', { params })
    return response.data
  },

  // Update item note
  updateItemNote: async (requisitionId: string, detailId: number, data: { note: string }): Promise<RequestOrderItem> => {
    const response = await api.patch(`/requisitions/${requisitionId}/lines/${detailId}/note`, data)
    return response.data
  }
}

// 取得有加急項目的供應商列表
export async function getUrgentSuppliers(): Promise<any[]> {
  const response = await api.get('/api/v1/requisitions/urgent-suppliers')
  return response.data
}
