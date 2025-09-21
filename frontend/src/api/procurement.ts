import api, { type PaginatedResponse, createIdempotentRequest } from './index'
import type { PurchaseOrder, PurchaseOrderItem } from '@/types/common'

export interface BuildCandidate {
  supplier_id: string
  supplier_name: string
  items: {
    detail_id: number
    item_name: string
    item_quantity: number
    item_unit: string
    unit_price: number
    item_specification?: string
    line_subtotal: number
    source_request_order_no: string
  }[]
}

export interface BuildCandidatesResponse {
  candidates: Record<string, BuildCandidate>
}

export interface CreatePORequest {
  supplier_id: string
  quotation_no?: string
  delivery_address?: string
  notes?: string
  lines: {
    detail_id: number
    quantity?: number
    unit_price?: number
  }[]
}

export interface POFilters {
  status?: string
  supplier_id?: string
  page?: number
  page_size?: number
}

export interface WithdrawPORequest {
  reason: string
}

export interface ReorganizePORequest {
  reason: string
  items: {
    detail_id: number
    action: 'keep' | 'remove'
    new_quantity?: number
    new_unit_price?: number
  }[]
}

export interface ExportPORequest {
  format: 'print' | 'pdf' | 'excel'
  quotation_no?: string
}

export interface ExportResponse {
  success: boolean
  purchase_order_no: string
  export_info: {
    previous_status: string
    current_status: string
    export_person_id: number
    export_count: number
    export_timestamp: string
  }
  message: string
}

export const procurementApi = {
  // Get approved items for PO creation
  getBuildCandidates: async (): Promise<BuildCandidatesResponse> => {
    const response = await api.get('/po/build-candidates')
    return response.data
  },

  // Create purchase order
  createPO: async (data: CreatePORequest): Promise<PurchaseOrder> => {
    const response = await api.post('/po/', data)  // 添加尾部斜線以避免重定向
    return response.data
  },

  // List purchase orders
  getPurchaseOrders: async (filters: POFilters = {}): Promise<PaginatedResponse<PurchaseOrder>> => {
    // Filter out empty string parameters
    const cleanFilters: any = {}
    Object.keys(filters).forEach(key => {
      const value = (filters as any)[key]
      if (value !== '' && value !== null && value !== undefined) {
        cleanFilters[key] = value
      }
    })

    const response = await api.get('/po/', { params: cleanFilters })  // 添加尾部斜線以避免重定向
    return response.data
  },

  // Get purchase order detail
  getPurchaseOrder: async (poNo: string): Promise<PurchaseOrder> => {
    const response = await api.get(`/po/${poNo}`)
    return response.data.data || response.data
  },

  // Update purchase order
  updatePurchaseOrder: async (poNo: string, data: Partial<CreatePORequest>): Promise<PurchaseOrder> => {
    const response = await api.put(`/po/${poNo}`, data)
    return response.data
  },

  // Confirm purchase order
  confirmPurchase: async (poNo: string): Promise<any> => {
    const headers = createIdempotentRequest()
    const response = await api.post(`/po/${poNo}/confirm-purchase`, {}, { headers })
    return response.data
  },

  // Cancel/withdraw purchase order
  cancelPO: async (poNo: string, data: WithdrawPORequest): Promise<PurchaseOrder> => {
    const headers = createIdempotentRequest()
    const response = await api.post(`/po/${poNo}/cancel`, data, { headers })
    return response.data
  },

  // Withdraw purchase order (deprecated - use cancelPO)
  withdrawPO: async (poNo: string, data: WithdrawPORequest): Promise<PurchaseOrder> => {
    const response = await api.post(`/po/${poNo}/withdraw`, data)
    return response.data
  },

  // Reorganize purchase order
  reorganizePO: async (poNo: string, data: ReorganizePORequest): Promise<PurchaseOrder> => {
    const response = await api.post(`/po/${poNo}/reorganize`, data)
    return response.data
  },

  // Export purchase order
  exportPurchaseOrder: async (poNo: string, data: ExportPORequest): Promise<ExportResponse | Blob> => {
    // For Excel and PDF, request binary data
    if (data.format === 'excel' || data.format === 'pdf') {
      const response = await api.post(`/po/${poNo}/export`, data, {
        responseType: 'blob'
      })
      return response.data
    }
    // For print format, return JSON response
    const response = await api.post(`/po/${poNo}/export`, data)
    return response.data
  }
}