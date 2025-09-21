import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { requisitionApi } from '@/api'
import type { RequestOrder, RequestOrderItem } from '@/types/common'
import type { 
  RequisitionFilters, 
  CreateRequisitionRequest, 
  ApproveItemRequest,
  RejectItemRequest,
  QuestionItemRequest,
  RejectRequisitionRequest,
  SaveChangesRequest
} from '@/api/requisition'
import { handleApiError } from '@/api'

export const useRequisitionStore = defineStore('requisition', () => {
  // State
  const requisitions = ref<RequestOrder[]>([])
  const currentRequisition = ref<RequestOrder | null>(null)
  const loading = ref(false)
  const pagination = ref({
    page: 1,
    page_size: 20,
    total: 0,
    pages: 0
  })
  const permissions = ref({
    can_view_all: false,
    user_role: '',
    filtered_to_own: true
  })
  const filters = ref<RequisitionFilters>({
    mine: undefined,  // Let the backend decide based on user role
    status: '',
    page: 1,
    page_size: 20
  })

  // Getters
  const pendingRequisitions = computed(() => 
    requisitions.value.filter(req => req.order_status === 'submitted')
  )

  const myRequisitions = computed(() => 
    requisitions.value.filter(req => req.requester_id === 0) // This would be current user ID
  )

  const requisitionById = computed(() => (id: string) => 
    requisitions.value.find(req => req.request_order_no === id)
  )

  // Actions
  const fetchRequisitions = async (newFilters?: Partial<RequisitionFilters>) => {
    try {
      loading.value = true
      if (newFilters) {
        filters.value = { ...filters.value, ...newFilters }
      }

      const response = await requisitionApi.getRequisitions(filters.value)
      requisitions.value = response.items
      pagination.value = response.pagination
      if (response.permissions) {
        permissions.value = response.permissions
      }
    } catch (error) {
      handleApiError(error, '獲取請購單列表失敗')
    } finally {
      loading.value = false
    }
  }

  const fetchRequisitionDetail = async (id: string) => {
    try {
      loading.value = true
      const requisition = await requisitionApi.getRequisition(id)
      currentRequisition.value = requisition
      return requisition
    } catch (error) {
      handleApiError(error, '獲取請購單詳情失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const createRequisition = async (data: CreateRequisitionRequest) => {
    try {
      loading.value = true
      const requisition = await requisitionApi.createRequisition(data)
      requisitions.value.unshift(requisition)
      ElMessage.success('請購單創建成功')
      return requisition
    } catch (error) {
      handleApiError(error, '創建請購單失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const updateRequisition = async (id: string, data: Partial<CreateRequisitionRequest>) => {
    try {
      loading.value = true
      const updatedRequisition = await requisitionApi.updateRequisition(id, data)
      
      // Update in list
      const index = requisitions.value.findIndex(req => req.request_order_no === id)
      if (index !== -1) {
        requisitions.value[index] = updatedRequisition
      }
      
      // Update current if it's the same one
      if (currentRequisition.value?.request_order_no === id) {
        currentRequisition.value = updatedRequisition
      }

      ElMessage.success('請購單更新成功')
      return updatedRequisition
    } catch (error) {
      handleApiError(error, '更新請購單失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const submitRequisition = async (id: string) => {
    try {
      loading.value = true
      const submittedRequisition = await requisitionApi.submitRequisition(id)
      
      // Update in list
      const index = requisitions.value.findIndex(req => req.request_order_no === id)
      if (index !== -1) {
        requisitions.value[index] = submittedRequisition
      }
      
      // Update current if it's the same one
      if (currentRequisition.value?.request_order_no === id) {
        currentRequisition.value = submittedRequisition
      }

      ElMessage.success('請購單提交成功')
      return submittedRequisition
    } catch (error) {
      handleApiError(error, '提交請購單失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const approveItem = async (requisitionId: string, detailId: number, data: ApproveItemRequest) => {
    try {
      loading.value = true
      const updatedItem = await requisitionApi.approveItem(requisitionId, detailId, data)
      
      // CRITICAL FIX: Enhanced refresh with retry logic
      await refreshRequisitionWithRetry(requisitionId, 3)
      
      ElMessage.success('項目審核通過')
      return updatedItem
    } catch (error) {
      handleApiError(error, '審核項目失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const questionItem = async (requisitionId: string, detailId: number, data: QuestionItemRequest) => {
    try {
      loading.value = true
      const updatedItem = await requisitionApi.questionItem(requisitionId, detailId, data)
      
      // CRITICAL FIX: Enhanced refresh with retry logic
      await refreshRequisitionWithRetry(requisitionId, 3)
      
      ElMessage.success('項目標記為有疑問')
      return updatedItem
    } catch (error) {
      handleApiError(error, '標記項目疑問失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const rejectItem = async (requisitionId: string, detailId: number, data: RejectItemRequest) => {
    try {
      loading.value = true
      const updatedItem = await requisitionApi.rejectItem(requisitionId, detailId, data)
      
      // CRITICAL FIX: Enhanced refresh with retry logic
      await refreshRequisitionWithRetry(requisitionId, 3)
      
      ElMessage.success('項目已駁回')
      return updatedItem
    } catch (error) {
      handleApiError(error, '駁回項目失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const rejectRequisition = async (id: string, data: RejectRequisitionRequest) => {
    try {
      loading.value = true
      const rejectedRequisition = await requisitionApi.rejectRequisition(id, data)
      
      // Update in list
      const index = requisitions.value.findIndex(req => req.request_order_no === id)
      if (index !== -1) {
        requisitions.value[index] = rejectedRequisition
      }
      
      // Update current if it's the same one
      if (currentRequisition.value?.request_order_no === id) {
        currentRequisition.value = rejectedRequisition
      }

      ElMessage.success('請購單已駁回')
      return rejectedRequisition
    } catch (error) {
      handleApiError(error, '駁回請購單失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  // CRITICAL FIX: Enhanced refresh with retry and status polling
  const refreshRequisitionWithRetry = async (requisitionId: string, maxRetries: number = 3) => {
    console.log(`[STORE_FIX] Refreshing requisition ${requisitionId} with retry logic`)
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(`[STORE_FIX] Refresh attempt ${attempt}/${maxRetries}`)
        
        // Add delay between attempts to allow backend processing
        if (attempt > 1) {
          await new Promise(resolve => setTimeout(resolve, 1000 * attempt))
        }
        
        const refreshedRequisition = await requisitionApi.getRequisition(requisitionId)
        
        // Update current requisition
        if (currentRequisition.value?.request_order_no === requisitionId) {
          console.log(`[STORE_FIX] Updating current requisition status: ${currentRequisition.value.order_status} -> ${refreshedRequisition.order_status}`)
          currentRequisition.value = refreshedRequisition
        }
        
        // Update in list if found
        const index = requisitions.value.findIndex(req => req.request_order_no === requisitionId)
        if (index !== -1) {
          console.log(`[STORE_FIX] Updating requisition in list status: ${requisitions.value[index].order_status} -> ${refreshedRequisition.order_status}`)
          requisitions.value[index] = refreshedRequisition
        }
        
        console.log(`[STORE_FIX] Successfully refreshed requisition on attempt ${attempt}`)
        return refreshedRequisition
        
      } catch (error) {
        console.error(`[STORE_FIX] Refresh attempt ${attempt} failed:`, error)
        if (attempt === maxRetries) {
          throw error
        }
      }
    }
  }
  
  // CRITICAL FIX: Status polling for real-time updates
  const pollRequisitionStatus = async (requisitionId: string, expectedStatus: string, maxAttempts: number = 5) => {
    console.log(`[STORE_FIX] Polling for status change to '${expectedStatus}' for requisition ${requisitionId}`)
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        const requisition = await requisitionApi.getRequisition(requisitionId)
        console.log(`[STORE_FIX] Poll attempt ${attempt}: current status '${requisition.order_status}'`)
        
        if (requisition.order_status === expectedStatus) {
          console.log(`[STORE_FIX] Status change detected! Updating store.`)
          
          // Update current requisition
          if (currentRequisition.value?.request_order_no === requisitionId) {
            currentRequisition.value = requisition
          }
          
          // Update in list
          const index = requisitions.value.findIndex(req => req.request_order_no === requisitionId)
          if (index !== -1) {
            requisitions.value[index] = requisition
          }
          
          return requisition
        }
        
        // Wait before next poll
        if (attempt < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, 1000))
        }
        
      } catch (error) {
        console.error(`[STORE_FIX] Poll attempt ${attempt} failed:`, error)
      }
    }
    
    console.log(`[STORE_FIX] Polling completed without status change to '${expectedStatus}'`)
    return null
  }

  // EMERGENCY HOTFIX: Save changes without approval
  const saveItemChanges = async (requisitionId: string, detailId: number, data: SaveChangesRequest) => {
    try {
      console.log(`[STORE_HOTFIX] Saving changes for ${requisitionId}/${detailId}:`, data)
      const updatedItem = await requisitionApi.saveItemChanges(requisitionId, detailId, data)
      
      // Update the item in the current requisition if it exists
      if (currentRequisition.value?.request_order_no === requisitionId) {
        const itemIndex = currentRequisition.value.items?.findIndex(item => item.detail_id === detailId)
        if (itemIndex !== -1 && currentRequisition.value.items) {
          currentRequisition.value.items[itemIndex] = updatedItem
        }
      }
      
      console.log(`[STORE_HOTFIX] Changes saved successfully for ${requisitionId}/${detailId}`)
      return updatedItem
    } catch (error) {
      handleApiError(error, '保存變更失敗')
      throw error
    }
  }

  const clearCurrentRequisition = () => {
    currentRequisition.value = null
  }

  return {
    // State
    requisitions,
    currentRequisition,
    loading,
    pagination,
    permissions,
    filters,

    // Getters
    pendingRequisitions,
    myRequisitions,
    requisitionById,

    // Actions
    fetchRequisitions,
    fetchRequisitionDetail,
    createRequisition,
    updateRequisition,
    submitRequisition,
    approveItem,
    questionItem,
    rejectItem,
    rejectRequisition,
    clearCurrentRequisition,
    // CRITICAL FIX: New status management methods
    refreshRequisitionWithRetry,
    pollRequisitionStatus,
    // EMERGENCY HOTFIX: Save changes method
    saveItemChanges
  }
})