import api from './index'
import type { StorageHistory } from '@/types/common'

export interface InventoryItem {
  item_id: string
  item_name: string
  item_unit: string
  item_specification?: string
  total_quantity: number
  available_quantity: number
  storage_locations: {
    storage_id: string
    area_code: string
    shelf_code: string
    floor_level: number
    front_back_position: number
    left_middle_right_position: number
    quantity: number
  }[]
  recent_movements: {
    operation_date: string
    operation_type: 'in' | 'out'
    quantity: number
    operator_name: string
    note?: string
  }[]
}

export interface InventoryFilters {
  name?: string
  spec?: string
  request_no?: string
  po_no?: string
  usage_type?: string
  zone?: string
  shelf?: string
  floor?: number
}

export interface IssueItemRequest {
  item_ref: string
  storage_id: string
  qty: number
  usage_type?: 'daily' | 'project'
  project_id?: string
  request_order_no?: string
  note?: string
}

export interface AcceptanceItem {
  detail_id: number
  item_name: string
  item_quantity: number
  item_unit: string
  item_specification?: string
  request_order_no: string
  acceptance_status: string
  source_request_item?: any
}

export interface ConfirmAcceptanceRequest {
  accepted_quantity?: number
  notes?: string
}

// New interfaces for receiving workflow
export interface ShippedItem {
  id: number
  item_name: string
  requisition_number: string
  purchase_order_number: string
  consolidation_number?: string
  specification: string
  quantity: number
  unit: string
  supplier_name: string
  supplier_region: 'domestic' | 'international'
  remarks: string
  shipped_date: string
  delivery_status: string
}

export interface ReceivingConfirmRequest {
  item_id: number
  item_name: string
  requisition_number: string
  purchase_order_number: string
  consolidation_number?: string
  quantity?: number
  unit?: string
  receiver: string
  received_at: string
  notes?: string
}

export interface BatchReceivingRequest {
  items: Array<{
    item_id: number
    requisition_number: string
    purchase_order_number: string
    consolidation_number?: string
  }>
  receiver: string
  received_at: string
  notes?: string
}

export interface PendingStorageItem {
  id: number
  item_name: string
  quantity: number
  unit: string
  source_po_number: string
  arrival_date: string
  receiver: string
  suggested_location?: string
  requisition_number: string
  consolidation_number?: string
  specification: string
}

export interface StorageAssignmentRequest {
  item_ref: {
    id: number
    po_no: string
    item_name?: string
    quantity?: number
    receiver?: string
    arrival_date?: string
  }
  area: string
  shelf: string
  floor: number
}

export interface ManualEntryRequest {
  item_name: string
  specification: string
  quantity: number
  unit: string
  storage_location: {
    area: string
    shelf: string
    floor: number
  }
  remarks?: string
}

export const inventoryApi = {
  // Query inventory with filters (legacy)
  queryInventory: async (filters: InventoryFilters = {}): Promise<InventoryItem[]> => {
    const response = await api.get('/inventory', { params: filters })
    return response.data
  },

  // New grouped inventory APIs
  getInventoryItemsGrouped: async (filters: InventoryFilters = {}): Promise<any[]> => {
    const response = await api.get('/inventory/items', { params: filters })
    return response.data
  },

  getInventoryItemDetails: async (itemKey: string): Promise<any> => {
    const response = await api.get(`/inventory/items/${encodeURIComponent(itemKey)}/details`)
    return response.data
  },

  getInventoryItemHistory: async (itemKey: string, page: number = 1, perPage: number = 20): Promise<any> => {
    const response = await api.get(`/inventory/items/${encodeURIComponent(itemKey)}/history`, {
      params: { page, per_page: perPage }
    })
    return response.data
  },

  getBatchDetails: async (batchId: number): Promise<any> => {
    const response = await api.get(`/inventory/batches/${batchId}/details`)
    return response.data
  },

  getBatchHistory: async (batchId: number, page: number = 1, perPage: number = 20): Promise<any> => {
    const response = await api.get(`/inventory/batches/${batchId}/history`, {
      params: { page, per_page: perPage }
    })
    return response.data
  },

  // Issue inventory item
  issueItem: async (data: IssueItemRequest): Promise<StorageHistory> => {
    const response = await api.post('/inventory/issue', data)
    return response.data
  },

  // Get pending acceptance items
  getMyAcceptanceItems: async (status?: string): Promise<AcceptanceItem[]> => {
    const params = status ? { status } : {}
    const response = await api.get('/acceptance/mine', { params })
    return response.data
  },

  // Confirm acceptance
  confirmAcceptance: async (detailId: number, data: ConfirmAcceptanceRequest = {}): Promise<AcceptanceItem> => {
    const response = await api.post('/acceptance/confirm', {
      item_ref: {
        detail_id: detailId
      },
      ...data
    })
    return response.data
  },

  // New Receiving Management APIs
  getShippedItems: async (filters: any = {}): Promise<ShippedItem[]> => {
    const response = await api.get('/receiving/shipped-items', { params: filters })
    return response.data
  },

  confirmItemReceived: async (data: ReceivingConfirmRequest): Promise<any> => {
    const response = await api.post('/receiving/confirm', data)
    return response.data
  },

  batchConfirmReceived: async (data: BatchReceivingRequest): Promise<any> => {
    const response = await api.post('/receiving/batch-confirm', data)
    return response.data
  },

  // Legacy Receiving Management APIs (for backward compatibility)
  getReceivingList: async (filters: any = {}): Promise<any[]> => {
    const response = await api.get('/receiving', { params: filters })
    return response.data
  },

  getReceivingDetails: async (poNo: string): Promise<any> => {
    const response = await api.get(`/receiving/po/${poNo}`)
    return response.data
  },

  confirmItemReceivedLegacy: async (poNo: string, detailId: number): Promise<any> => {
    const response = await api.post(`/receiving/po/${poNo}/items/${detailId}/confirm`)
    return response.data
  },

  // Storage Management APIs
  getStorageTree: async (): Promise<any[]> => {
    const response = await api.get('/storage/tree')
    return response.data
  },

  createZone: async (data: any): Promise<any> => {
    const response = await api.post('/storage/admin/zones', data)
    return response.data
  },

  // Updated Storage Management APIs
  getPendingStorageItems: async (): Promise<PendingStorageItem[]> => {
    const response = await api.get('/putaway/pending')
    return response.data
  },

  assignStorageLocation: async (data: StorageAssignmentRequest): Promise<any> => {
    const response = await api.post('/putaway/assign', data)
    return response.data
  },

  createManualEntry: async (data: ManualEntryRequest): Promise<any> => {
    const response = await api.post('/storage/manual-entry', data)
    return response.data
  },

  // Legacy methods (for backward compatibility)
  getPendingItems: async (status: string = 'arrived'): Promise<any[]> => {
    const response = await api.get('/putaway', { params: { status } })
    return response.data
  },

  assignStorage: async (data: any): Promise<any> => {
    const response = await api.post('/putaway/assign', data)
    return response.data
  },

  // Additional helper methods
  getSuppliers: async (): Promise<any[]> => {
    const response = await api.get('/suppliers/summary')
    return response.data
  },

  // Batch operations
  batchReceiveItems: async (items: any[]): Promise<any> => {
    const response = await api.post('/receiving/batch', { items })
    return response.data
  },

  batchAssignStorage: async (items: any[]): Promise<any> => {
    const response = await api.post('/putaway/batch-assign', { items })
    return response.data
  },

  // Export functions
  exportInventory: async (filters: InventoryFilters = {}): Promise<any> => {
    const response = await api.get('/inventory/export', { params: filters, responseType: 'blob' })
    return response.data
  },

  exportAcceptanceReport: async (filters: any = {}): Promise<any> => {
    const response = await api.get('/acceptance/export', { params: filters, responseType: 'blob' })
    return response.data
  }
}