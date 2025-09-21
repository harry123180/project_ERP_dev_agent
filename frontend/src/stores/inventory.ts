import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { inventoryApi, receivingApi, storageApi } from '@/api'
import type { 
  InventoryItem,
  InventoryFilters,
  IssueItemRequest,
  AcceptanceItem,
  ConfirmAcceptanceRequest
} from '@/api/inventory'
import type { 
  ReceivingItem,
  ReceivingDetail,
  ReceivingFilters,
  ConfirmReceivingRequest
} from '@/api/receiving'
import type {
  PutAwayItem,
  PutAwayFilters,
  StorageTreeNode,
  AssignStorageRequest,
  QuickStorageRequest
} from '@/api/storage'
import { handleApiError } from '@/api'

export const useInventoryStore = defineStore('inventory', () => {
  // State
  const items = ref<InventoryItem[]>([])
  const receivingItems = ref<ReceivingItem[]>([])
  const putAwayItems = ref<PutAwayItem[]>([])
  const acceptanceItems = ref<AcceptanceItem[]>([])
  const storageTree = ref<StorageTreeNode[]>([])
  const currentItem = ref<InventoryItem | null>(null)
  const currentReceivingDetail = ref<ReceivingDetail | null>(null)
  const loading = ref(false)

  // Getters
  const itemsByLocation = computed(() => {
    const grouped: Record<string, InventoryItem[]> = {}
    items.value.forEach(item => {
      item.storage_locations.forEach(location => {
        const locationKey = `${location.area_code}-${location.shelf_code}-${location.floor_level}`
        if (!grouped[locationKey]) {
          grouped[locationKey] = []
        }
        if (!grouped[locationKey].find(i => i.item_id === item.item_id)) {
          grouped[locationKey].push(item)
        }
      })
    })
    return grouped
  })

  const availableStock = computed(() => 
    items.value.filter(item => item.available_quantity > 0)
  )

  const itemById = computed(() => (id: string) => 
    items.value.find(item => item.item_id === id)
  )

  const pendingAcceptanceCount = computed(() => 
    acceptanceItems.value.filter(item => item.acceptance_status === 'pending_acceptance').length
  )

  // Inventory Actions
  const fetchInventory = async (filters: InventoryFilters = {}) => {
    try {
      loading.value = true
      const inventoryData = await inventoryApi.queryInventory(filters)
      items.value = inventoryData
    } catch (error) {
      handleApiError(error, '獲取庫存數據失敗')
    } finally {
      loading.value = false
    }
  }

  const issueItem = async (data: IssueItemRequest) => {
    try {
      loading.value = true
      const movementHistory = await inventoryApi.issueItem(data)
      
      // Refresh inventory to get updated quantities
      await fetchInventory()
      
      ElMessage.success('物品領用成功')
      return movementHistory
    } catch (error) {
      handleApiError(error, '物品領用失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  // Receiving Actions
  const fetchReceivingItems = async (filters: ReceivingFilters = {}) => {
    try {
      loading.value = true
      const items = await receivingApi.getReceivingItems(filters)
      receivingItems.value = items
    } catch (error) {
      handleApiError(error, '獲取收貨項目失敗')
    } finally {
      loading.value = false
    }
  }

  const fetchReceivingDetail = async (poNo: string) => {
    try {
      loading.value = true
      const detail = await receivingApi.getReceivingDetail(poNo)
      currentReceivingDetail.value = detail
      return detail
    } catch (error) {
      handleApiError(error, '獲取收貨詳情失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const confirmReceiving = async (poNo: string, detailId: number, data: ConfirmReceivingRequest = {}) => {
    try {
      loading.value = true
      const updatedItem = await receivingApi.confirmReceiving(poNo, detailId, data)
      
      // Refresh receiving items and detail
      await fetchReceivingItems()
      if (currentReceivingDetail.value?.purchase_order.purchase_order_no === poNo) {
        await fetchReceivingDetail(poNo)
      }
      
      ElMessage.success('收貨確認成功')
      return updatedItem
    } catch (error) {
      handleApiError(error, '確認收貨失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  // Storage Actions
  const fetchPutAwayItems = async (filters: PutAwayFilters = {}) => {
    try {
      loading.value = true
      const items = await storageApi.getPutAwayItems(filters)
      putAwayItems.value = items
    } catch (error) {
      handleApiError(error, '獲取上架項目失敗')
    } finally {
      loading.value = false
    }
  }

  const fetchStorageTree = async () => {
    try {
      loading.value = true
      const tree = await storageApi.getStorageTree()
      storageTree.value = tree
    } catch (error) {
      handleApiError(error, '獲取儲存位置樹失敗')
    } finally {
      loading.value = false
    }
  }

  const assignStorage = async (data: AssignStorageRequest) => {
    try {
      loading.value = true
      const movementHistory = await storageApi.assignStorage(data)
      
      // Refresh put away items
      await fetchPutAwayItems()
      
      ElMessage.success('儲存位置分配成功')
      return movementHistory
    } catch (error) {
      handleApiError(error, '分配儲存位置失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const quickStorageIn = async (data: QuickStorageRequest) => {
    try {
      loading.value = true
      const movementHistory = await storageApi.quickStorageIn(data)
      
      // Refresh inventory
      await fetchInventory()
      
      ElMessage.success('快速入庫成功')
      return movementHistory
    } catch (error) {
      handleApiError(error, '快速入庫失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  // Acceptance Actions
  const fetchAcceptanceItems = async () => {
    try {
      loading.value = true
      const items = await inventoryApi.getMyAcceptanceItems()
      acceptanceItems.value = items
    } catch (error) {
      handleApiError(error, '獲取驗收項目失敗')
    } finally {
      loading.value = false
    }
  }

  const confirmAcceptance = async (detailId: number, data: ConfirmAcceptanceRequest = {}) => {
    try {
      loading.value = true
      const updatedItem = await inventoryApi.confirmAcceptance(detailId, data)
      
      // Refresh acceptance items
      await fetchAcceptanceItems()
      
      ElMessage.success('驗收確認成功')
      return updatedItem
    } catch (error) {
      handleApiError(error, '確認驗收失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const clearCurrentItem = () => {
    currentItem.value = null
  }

  const clearCurrentReceivingDetail = () => {
    currentReceivingDetail.value = null
  }

  return {
    // State
    items,
    receivingItems,
    putAwayItems,
    acceptanceItems,
    storageTree,
    currentItem,
    currentReceivingDetail,
    loading,

    // Getters
    itemsByLocation,
    availableStock,
    itemById,
    pendingAcceptanceCount,

    // Actions
    fetchInventory,
    issueItem,
    fetchReceivingItems,
    fetchReceivingDetail,
    confirmReceiving,
    fetchPutAwayItems,
    fetchStorageTree,
    assignStorage,
    quickStorageIn,
    fetchAcceptanceItems,
    confirmAcceptance,
    clearCurrentItem,
    clearCurrentReceivingDetail
  }
})