/**
 * Storage Management Store
 * Handles storage locations, put-away operations, and inventory movements
 * Architecture Lead: Winston
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { 
  StorageLocation, 
  StorageTree, 
  StorageFilters, 
  PutAwayItem,
  StorageAssignment 
} from '@/types/storage'
import { apiClient } from '@/utils/api'
import { ElMessage } from 'element-plus'

export const useStorageStore = defineStore('storage', () => {
  // State
  const storageTree = ref<StorageTree | null>(null)
  const storageLocations = ref<StorageLocation[]>([])
  const putAwayItems = ref<PutAwayItem[]>([])
  const currentAssignment = ref<StorageAssignment | null>(null)
  const loading = ref(false)
  const putAwayLoading = ref(false)
  
  // Filters
  const filters = ref<StorageFilters>({
    zone: undefined,
    shelf: undefined,
    floor: undefined,
    available_only: false,
    storage_type: undefined
  })
  
  // Pagination
  const pagination = ref({
    page: 1,
    page_size: 50,
    total: 0,
    has_more: false
  })

  // Getters
  const availableLocations = computed(() => 
    storageLocations.value.filter(location => location.is_available)
  )
  
  const fullLocations = computed(() => 
    storageLocations.value.filter(location => 
      location.current_capacity >= location.max_capacity
    )
  )
  
  const nearFullLocations = computed(() => 
    storageLocations.value.filter(location => 
      location.utilization_percent > 90 && location.utilization_percent < 100
    )
  )
  
  const filteredLocations = computed(() => {
    let filtered = storageLocations.value
    
    if (filters.value.zone) {
      filtered = filtered.filter(loc => loc.zone === filters.value.zone)
    }
    
    if (filters.value.shelf) {
      filtered = filtered.filter(loc => loc.shelf === filters.value.shelf)
    }
    
    if (filters.value.floor) {
      filtered = filtered.filter(loc => loc.floor === filters.value.floor)
    }
    
    if (filters.value.available_only) {
      filtered = filtered.filter(loc => loc.is_available)
    }
    
    if (filters.value.storage_type) {
      filtered = filtered.filter(loc => loc.storage_type === filters.value.storage_type)
    }
    
    return filtered
  })
  
  const priorityPutAwayItems = computed(() => 
    putAwayItems.value
      .filter(item => item.priority >= 8)
      .sort((a, b) => b.priority - a.priority)
  )
  
  const getStorageStats = computed(() => ({
    total_locations: storageLocations.value.length,
    available_locations: availableLocations.value.length,
    full_locations: fullLocations.value.length,
    near_full_locations: nearFullLocations.value.length,
    utilization_rate: storageLocations.value.length > 0 
      ? Math.round((fullLocations.value.length / storageLocations.value.length) * 100)
      : 0
  }))
  
  const getZones = computed(() => {
    if (!storageTree.value) return []
    return storageTree.value.storage_tree.map(zone => zone.zone_name)
  })
  
  const getShelvesByZone = computed(() => (zoneName: string) => {
    if (!storageTree.value) return []
    const zone = storageTree.value.storage_tree.find(z => z.zone_name === zoneName)
    return zone ? zone.shelves.map(shelf => shelf.shelf_name) : []
  })
  
  const getFloorsByShelf = computed(() => (zoneName: string, shelfName: string) => {
    if (!storageTree.value) return []
    const zone = storageTree.value.storage_tree.find(z => z.zone_name === zoneName)
    const shelf = zone?.shelves.find(s => s.shelf_name === shelfName)
    return shelf ? shelf.floors.map(floor => floor.floor_name) : []
  })

  // Actions
  const fetchStorageTree = async (refresh = false) => {
    if (!refresh && storageTree.value) return storageTree.value
    
    loading.value = true
    
    try {
      const response = await apiClient.get('/api/v1/storage/tree')
      
      if (response.data.success) {
        storageTree.value = response.data.data
        return response.data.data
      } else {
        throw new Error(response.data.error?.message || 'Failed to fetch storage tree')
      }
    } catch (error) {
      console.error('Error fetching storage tree:', error)
      ElMessage.error('Failed to load storage hierarchy')
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchStorageLocations = async (options: {
    page?: number
    page_size?: number
    refresh?: boolean
  } = {}) => {
    if (!options.refresh && storageLocations.value.length > 0 && !loading.value) {
      return
    }
    
    loading.value = true
    
    try {
      const params = new URLSearchParams({
        page: (options.page || pagination.value.page).toString(),
        page_size: (options.page_size || pagination.value.page_size).toString(),
        ...(filters.value.zone && { zone: filters.value.zone }),
        ...(filters.value.shelf && { shelf: filters.value.shelf }),
        ...(filters.value.floor && { floor: filters.value.floor }),
        ...(filters.value.available_only && { available_only: 'true' }),
        ...(filters.value.storage_type && { storage_type: filters.value.storage_type })
      })
      
      const response = await apiClient.get(`/api/v1/storage/locations?${params}`)
      
      if (response.data.success) {
        storageLocations.value = response.data.data
        pagination.value = response.data.pagination
      } else {
        throw new Error(response.data.error?.message || 'Failed to fetch storage locations')
      }
    } catch (error) {
      console.error('Error fetching storage locations:', error)
      ElMessage.error('Failed to load storage locations')
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchPutAwayItems = async () => {
    putAwayLoading.value = true
    
    try {
      const response = await apiClient.get('/api/v1/storage/putaway')
      
      if (response.data.success) {
        putAwayItems.value = response.data.data.items
        return response.data.data
      } else {
        throw new Error(response.data.error?.message || 'Failed to fetch putaway items')
      }
    } catch (error) {
      console.error('Error fetching putaway items:', error)
      ElMessage.error('Failed to load items for putaway')
      throw error
    } finally {
      putAwayLoading.value = false
    }
  }

  const assignStorage = async (assignment: {
    po_item_id: number
    storage_id: number
    quantity: number
    notes?: string
  }) => {
    loading.value = true
    
    try {
      const response = await apiClient.post('/api/v1/storage/putaway/assign', assignment)
      
      if (response.data.success) {
        const result = response.data.data
        
        // Remove assigned item from putaway list
        const index = putAwayItems.value.findIndex(item => item.id === assignment.po_item_id)
        if (index !== -1) {
          putAwayItems.value.splice(index, 1)
        }
        
        // Update storage location capacity if it's in our list
        const storageIndex = storageLocations.value.findIndex(loc => loc.id === assignment.storage_id)
        if (storageIndex !== -1) {
          storageLocations.value[storageIndex].current_capacity += assignment.quantity
          storageLocations.value[storageIndex].utilization_percent = 
            Math.round((storageLocations.value[storageIndex].current_capacity / 
                      storageLocations.value[storageIndex].max_capacity) * 100)
          
          // Update availability if full
          if (storageLocations.value[storageIndex].current_capacity >= 
              storageLocations.value[storageIndex].max_capacity) {
            storageLocations.value[storageIndex].is_available = false
          }
        }
        
        currentAssignment.value = {
          id: result.storage_history_id,
          item_reference: result.item_reference,
          storage_location: result.storage_location,
          quantity_stored: result.quantity_stored,
          movement_date: result.movement_date,
          notes: assignment.notes
        }
        
        ElMessage.success('Storage location assigned successfully')
        return result
      } else {
        throw new Error(response.data.error?.message || 'Failed to assign storage')
      }
    } catch (error) {
      console.error('Error assigning storage:', error)
      const message = error.response?.data?.error?.message || 'Failed to assign storage location'
      ElMessage.error(message)
      throw error
    } finally {
      loading.value = false
    }
  }

  const createStorageZone = async (zoneData: {
    zone_name: string
    zone_type: string
    description?: string
    max_capacity?: number
  }) => {
    loading.value = true
    
    try {
      const response = await apiClient.post('/api/v1/storage/admin/zones', zoneData)
      
      if (response.data.success) {
        ElMessage.success('Storage zone created successfully')
        
        // Refresh storage tree to include new zone
        await fetchStorageTree(true)
        
        return response.data.data
      } else {
        throw new Error(response.data.error?.message || 'Failed to create storage zone')
      }
    } catch (error) {
      console.error('Error creating storage zone:', error)
      const message = error.response?.data?.error?.message || 'Failed to create storage zone'
      ElMessage.error(message)
      throw error
    } finally {
      loading.value = false
    }
  }

  const createStorageShelf = async (shelfData: {
    zone: string
    shelf_name: string
    shelf_type: string
    description?: string
    max_capacity?: number
  }) => {
    loading.value = true
    
    try {
      const response = await apiClient.post('/api/v1/storage/admin/shelves', shelfData)
      
      if (response.data.success) {
        ElMessage.success('Storage shelf created successfully')
        
        // Refresh storage tree to include new shelf
        await fetchStorageTree(true)
        
        return response.data.data
      } else {
        throw new Error(response.data.error?.message || 'Failed to create storage shelf')
      }
    } catch (error) {
      console.error('Error creating storage shelf:', error)
      const message = error.response?.data?.error?.message || 'Failed to create storage shelf'
      ElMessage.error(message)
      throw error
    } finally {
      loading.value = false
    }
  }

  const setFilters = (newFilters: Partial<StorageFilters>) => {
    filters.value = { ...filters.value, ...newFilters }
    // Reset pagination when filters change
    pagination.value.page = 1
  }

  const clearFilters = () => {
    filters.value = {
      zone: undefined,
      shelf: undefined,
      floor: undefined,
      available_only: false,
      storage_type: undefined
    }
    pagination.value.page = 1
  }

  const findOptimalStorage = (itemRequirements: {
    estimated_size: number
    item_type?: string
    priority: number
  }) => {
    // Algorithm to find best storage location based on:
    // 1. Available capacity
    // 2. Location proximity (same zone preferred)  
    // 3. Item type compatibility
    // 4. Utilization efficiency
    
    let candidates = availableLocations.value.filter(
      loc => loc.max_capacity - loc.current_capacity >= itemRequirements.estimated_size
    )
    
    if (candidates.length === 0) return null
    
    // Score each candidate location
    candidates = candidates.map(location => ({
      ...location,
      score: calculateStorageScore(location, itemRequirements)
    }))
    
    // Sort by score (highest first)
    candidates.sort((a, b) => (b as any).score - (a as any).score)
    
    return candidates[0]
  }

  const calculateStorageScore = (
    location: StorageLocation, 
    requirements: { estimated_size: number; item_type?: string; priority: number }
  ): number => {
    let score = 100 // Base score
    
    // Prefer locations with similar utilization (avoid fragmentation)
    const targetUtilization = 80
    const utilizationDiff = Math.abs(location.utilization_percent - targetUtilization)
    score -= utilizationDiff * 0.5
    
    // Prefer locations with adequate but not excessive capacity
    const capacityRatio = requirements.estimated_size / (location.max_capacity - location.current_capacity)
    if (capacityRatio > 0.5 && capacityRatio <= 0.8) {
      score += 20 // Optimal capacity usage
    } else if (capacityRatio <= 0.3) {
      score -= 10 // Wasteful for small items
    }
    
    // Priority items get better locations (closer to entrance, easier access)
    if (requirements.priority >= 8) {
      if (location.zone?.toLowerCase().includes('main') || 
          location.zone?.toLowerCase().includes('a')) {
        score += 15
      }
    }
    
    // Prefer locations with lower current capacity (easier access)
    score += (100 - location.utilization_percent) * 0.2
    
    return Math.max(0, score)
  }

  const refreshAll = async () => {
    await Promise.all([
      fetchStorageTree(true),
      fetchStorageLocations({ refresh: true }),
      fetchPutAwayItems()
    ])
  }

  return {
    // State
    storageTree,
    storageLocations,
    putAwayItems,
    currentAssignment,
    loading,
    putAwayLoading,
    filters,
    pagination,
    
    // Getters
    availableLocations,
    fullLocations,
    nearFullLocations,
    filteredLocations,
    priorityPutAwayItems,
    getStorageStats,
    getZones,
    getShelvesByZone,
    getFloorsByShelf,
    
    // Actions
    fetchStorageTree,
    fetchStorageLocations,
    fetchPutAwayItems,
    assignStorage,
    createStorageZone,
    createStorageShelf,
    setFilters,
    clearFilters,
    findOptimalStorage,
    refreshAll
  }
})