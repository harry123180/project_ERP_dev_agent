import api from './index'
import type { Storage, StorageHistory, RequestOrderItem } from '@/types/common'

export interface PutAwayItem {
  item_id: string
  item_name: string
  item_quantity: number
  item_unit: string
  item_specification?: string
  source_type: string
  source_no: string
  source_line: number
  status: string
  request_item?: RequestOrderItem
}

export interface PutAwayFilters {
  status?: 'arrived'
}

export interface StorageTreeNode {
  zone: string
  shelves: {
    shelf: string
    floors: {
      floor: number
      positions: StoragePosition[]
    }[]
  }[]
}

export interface StoragePosition {
  storage_id: string
  front_back_position: number
  left_middle_right_position: number
  is_active: boolean
  current_inventory: number
}

export interface AssignStorageRequest {
  item_id: string
  storage_id: string
  quantity: number
  source_type: string
  source_no: string
  source_line: number
  note?: string
}

export interface QuickStorageRequest {
  item_name: string
  item_quantity: number
  item_unit: string
  storage_id: string
  source_type: string
  source_no: string
  note?: string
}

export interface CreateZoneRequest {
  area_code: string
}

export interface CreateShelfRequest {
  area_code: string
  shelf_code: string
  floor_count: number
  position_count: number
}

export const storageApi = {
  // List items ready for storage assignment
  getPutAwayItems: async (filters: PutAwayFilters = {}): Promise<PutAwayItem[]> => {
    const response = await api.get('/putaway', { params: filters })
    return response.data
  },

  // Assign storage location
  assignStorage: async (data: AssignStorageRequest): Promise<StorageHistory> => {
    const response = await api.post('/putaway/assign', data)
    return response.data
  },

  // Get storage hierarchy
  getStorageTree: async (): Promise<StorageTreeNode[]> => {
    const response = await api.get('/storage/tree')
    return response.data
  },

  // Quick storage entry
  quickStorageIn: async (data: QuickStorageRequest): Promise<StorageHistory> => {
    const response = await api.post('/storage/quick-in', data)
    return response.data
  },

  // Admin endpoints for storage management
  createZone: async (data: CreateZoneRequest): Promise<any> => {
    const response = await api.post('/storage/admin/zones', data)
    return response.data
  },

  createShelf: async (data: CreateShelfRequest): Promise<any> => {
    const response = await api.post('/storage/admin/shelves', data)
    return response.data
  }
}