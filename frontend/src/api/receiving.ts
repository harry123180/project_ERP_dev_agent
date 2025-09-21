import api from './index'
import type { PurchaseOrder, RequestOrderItem } from '@/types/common'

export interface ReceivingFilters {
  region?: 'domestic' | 'international'
  supplier_id?: string
}

export interface ReceivingItem {
  detail_id: number
  purchase_order_no: string
  item_name: string
  item_quantity: number
  item_unit: string
  item_specification?: string
  unit_price: number
  line_subtotal: number
  received_quantity: number
  pending_quantity: number
  supplier_name: string
  order_date?: string
}

export interface ReceivingDetail {
  purchase_order: PurchaseOrder
  items: ReceivingItem[]
}

export interface ConfirmReceivingRequest {
  received_quantity?: number
  notes?: string
}

export const receivingApi = {
  // List items ready for receiving
  getReceivingItems: async (filters: ReceivingFilters = {}): Promise<ReceivingItem[]> => {
    const response = await api.get('/receiving', { params: filters })
    return response.data
  },

  // Get receiving details for a specific PO
  getReceivingDetail: async (poNo: string): Promise<ReceivingDetail> => {
    const response = await api.get(`/receiving/po/${poNo}`)
    return response.data
  },

  // Confirm item receipt
  confirmReceiving: async (poNo: string, detailId: number, data: ConfirmReceivingRequest = {}): Promise<RequestOrderItem> => {
    const response = await api.post(`/receiving/po/${poNo}/items/${detailId}/confirm`, data)
    return response.data
  }
}