import api from './index'
import type { PurchaseOrder } from '@/types/common'

export interface ShipmentData {
  purchase_order_no: string
  supplier_name: string
  shipping_status: string
  shipped_at?: string
  eta_date?: string
  arrival_date?: string
  carrier?: string
  tracking_no?: string
  logistics_note?: string
}

export interface LeadTimeFilters {
  visible_only?: boolean
}

export interface UpdateMilestoneRequest {
  shipping_status: 'shipped' | 'in_transit' | 'customs_clearance' | 'expected_arrival' | 'arrived'
  shipped_at?: string
  eta_date?: string
  arrival_date?: string
  carrier?: string
  tracking_no?: string
  logistics_note?: string
}

export interface ConsolidationData {
  consolidation_id: string
  consolidation_name: string
  container_no?: string
  shipping_method: string
  departure_port?: string
  destination_port?: string
  etd_date?: string
  eta_date?: string
  arrival_date?: string
  customs_status?: string
  tracking_info?: string
  notes?: string
  purchase_orders: PurchaseOrder[]
  created_at?: string
}

export interface CreateConsolidationRequest {
  consolidation_name: string
  container_no?: string
  shipping_method: string
  departure_port?: string
  destination_port?: string
  etd_date?: string
  eta_date?: string
  notes?: string
}

export interface AddPOToConsolidationRequest {
  purchase_order_no: string
}

export interface BulkMilestoneUpdateRequest {
  shipping_status: string
  shipped_at?: string
  eta_date?: string
  arrival_date?: string
  carrier?: string
  tracking_no?: string
  logistics_note?: string
}

export const leadtimeApi = {
  // Get shipment tracking data
  getShipments: async (filters: LeadTimeFilters = {}): Promise<ShipmentData[]> => {
    const response = await api.get('/leadtime', { params: filters })
    return response.data
  },

  // Update shipping milestone
  updateMilestone: async (poNo: string, data: UpdateMilestoneRequest): Promise<PurchaseOrder> => {
    const response = await api.post(`/po/${poNo}/milestone`, data)
    return response.data
  },

  // Create consolidation
  createConsolidation: async (data: CreateConsolidationRequest): Promise<ConsolidationData> => {
    const response = await api.post('/consolidations', data)
    return response.data
  },

  // Get consolidations
  getConsolidations: async (): Promise<ConsolidationData[]> => {
    const response = await api.get('/consolidations')
    return response.data
  },

  // Get consolidation detail
  getConsolidation: async (id: string): Promise<ConsolidationData> => {
    const response = await api.get(`/consolidations/${id}`)
    return response.data
  },

  // Add PO to consolidation
  addPOToConsolidation: async (consolidationId: string, data: AddPOToConsolidationRequest): Promise<ConsolidationData> => {
    const response = await api.post(`/consolidations/${consolidationId}/po`, data)
    return response.data
  },

  // Bulk update milestone for consolidation
  bulkUpdateMilestone: async (consolidationId: string, data: BulkMilestoneUpdateRequest): Promise<ConsolidationData> => {
    const response = await api.post(`/consolidations/${consolidationId}/bulk-milestone`, data)
    return response.data
  }
}