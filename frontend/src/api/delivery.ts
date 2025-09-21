import api from './index'

// 定義介面
export interface DeliveryMaintenanceResponse {
  success: boolean
  data: PurchaseOrder[]
  summary: {
    total_pos: number
    need_status_update: number
    can_create_consolidation: number
    domestic_count: number
    international_count: number
  }
}

export interface PurchaseOrder {
  po_number: string
  supplier_id: string
  supplier_name: string
  supplier_region: 'domestic' | 'international'
  delivery_status: string
  expected_delivery_date?: string
  actual_delivery_date?: string
  remarks: string
  status_update_required: boolean
  consolidation_id?: string
  item_count: number
  can_create_consolidation: boolean
}

export interface ConsolidationListResponse {
  success: boolean
  data: Consolidation[]
}

export interface Consolidation {
  consolidation_id: string
  pos: Array<{
    po_number: string
    supplier_name: string
    item_count: number
  }>
  total_items: number
  logistics_status: string
  expected_delivery?: string
}

export interface MaintenanceListParams {
  page?: number
  page_size?: number
  status?: string
  supplier_region?: string
  po_number?: string
}

export interface UpdateStatusRequest {
  new_status: string
  expected_date?: string
  remarks?: string
}

export interface UpdateRemarksRequest {
  remarks: string
}

export interface CreateConsolidationRequest {
  consolidation_name?: string
  purchase_order_nos: string[]
}

// API 函數
export const getMaintenanceList = async (params?: MaintenanceListParams): Promise<DeliveryMaintenanceResponse> => {
  const response = await api.get('/delivery/maintenance-list', { params })
  return response.data
}

export const getConsolidationList = async (): Promise<ConsolidationListResponse> => {
  const response = await api.get('/delivery/consolidation-list')
  return response.data
}

export const updateDeliveryStatus = async (poNumber: string, data: UpdateStatusRequest): Promise<any> => {
  const response = await api.put(`/delivery/orders/${poNumber}/status`, data)
  return response.data
}

export const updateRemarks = async (poNumber: string, data: UpdateRemarksRequest): Promise<any> => {
  const response = await api.put(`/delivery/orders/${poNumber}/remarks`, data)
  return response.data
}

export const createConsolidation = async (data: CreateConsolidationRequest): Promise<any> => {
  const response = await api.post('/delivery/consolidations', data)
  return response.data
}

// 更新集運單狀態
export interface UpdateConsolidationStatusRequest {
  new_status: string
  carrier?: string
  tracking_number?: string
  expected_date?: string
  remarks?: string
}

export const updateConsolidationStatus = async (consolidationId: string, data: UpdateConsolidationStatusRequest): Promise<any> => {
  const response = await api.put(`/delivery/consolidations/${consolidationId}/status`, data)
  return response.data
}

export default {
  getMaintenanceList,
  getConsolidationList,
  updateDeliveryStatus,
  updateRemarks,
  createConsolidation,
  updateConsolidationStatus
}