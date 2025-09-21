import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { procurementApi } from '@/api'
import type { PurchaseOrder } from '@/types/common'
import type { 
  BuildCandidatesResponse,
  CreatePORequest,
  POFilters,
  WithdrawPORequest,
  ReorganizePORequest
} from '@/api/procurement'
import { handleApiError } from '@/api'

export const useProcurementStore = defineStore('procurement', () => {
  // State
  const purchaseOrders = ref<PurchaseOrder[]>([])
  const buildCandidates = ref<BuildCandidatesResponse | null>(null)
  const currentPO = ref<PurchaseOrder | null>(null)
  const loading = ref(false)
  const pagination = ref({
    page: 1,
    page_size: 20,
    total: 0,
    pages: 0
  })
  const filters = ref<POFilters>({
    status: '',
    supplier_id: '',
    page: 1,
    page_size: 20
  })

  // Getters
  const poBySupplier = computed(() => {
    const grouped: Record<string, PurchaseOrder[]> = {}
    purchaseOrders.value.forEach(po => {
      const supplierId = po.supplier_id
      if (!grouped[supplierId]) {
        grouped[supplierId] = []
      }
      grouped[supplierId].push(po)
    })
    return grouped
  })

  const activePOs = computed(() => 
    purchaseOrders.value.filter(po => po.purchase_status === 'order_created')
  )

  const poById = computed(() => (poNo: string) => 
    purchaseOrders.value.find(po => po.purchase_order_no === poNo)
  )

  // Actions
  const fetchBuildCandidates = async () => {
    try {
      loading.value = true
      const candidates = await procurementApi.getBuildCandidates()
      buildCandidates.value = candidates
      return candidates
    } catch (error) {
      handleApiError(error, '獲取採購建單候選項失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const createPO = async (data: CreatePORequest) => {
    try {
      loading.value = true
      const po = await procurementApi.createPO(data)
      purchaseOrders.value.unshift(po)
      ElMessage.success('採購單創建成功')
      
      // Refresh build candidates to remove used items
      await fetchBuildCandidates()
      
      return po
    } catch (error) {
      handleApiError(error, '創建採購單失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchPurchaseOrders = async (newFilters?: Partial<POFilters>) => {
    try {
      loading.value = true
      if (newFilters) {
        filters.value = { ...filters.value, ...newFilters }
      }

      const response = await procurementApi.getPurchaseOrders(filters.value)
      purchaseOrders.value = response.items
      pagination.value = response.pagination
    } catch (error) {
      handleApiError(error, '獲取採購單列表失敗')
    } finally {
      loading.value = false
    }
  }

  const fetchPurchaseOrderDetail = async (poNo: string) => {
    try {
      loading.value = true
      const po = await procurementApi.getPurchaseOrder(poNo)
      currentPO.value = po
      return po
    } catch (error) {
      handleApiError(error, '獲取採購單詳情失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const updatePurchaseOrder = async (poNo: string, data: Partial<CreatePORequest>) => {
    try {
      loading.value = true
      const updatedPO = await procurementApi.updatePurchaseOrder(poNo, data)
      
      // Update in list
      const index = purchaseOrders.value.findIndex(po => po.purchase_order_no === poNo)
      if (index !== -1) {
        purchaseOrders.value[index] = updatedPO
      }
      
      // Update current if it's the same one
      if (currentPO.value?.purchase_order_no === poNo) {
        currentPO.value = updatedPO
      }

      ElMessage.success('採購單更新成功')
      return updatedPO
    } catch (error) {
      handleApiError(error, '更新採購單失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const confirmPurchase = async (poNo: string) => {
    try {
      loading.value = true
      const confirmedPO = await procurementApi.confirmPurchase(poNo)
      
      // Update in list
      const index = purchaseOrders.value.findIndex(po => po.purchase_order_no === poNo)
      if (index !== -1) {
        purchaseOrders.value[index] = confirmedPO
      }
      
      // Update current if it's the same one
      if (currentPO.value?.purchase_order_no === poNo) {
        currentPO.value = confirmedPO
      }

      ElMessage.success('採購單確認成功')
      return confirmedPO
    } catch (error) {
      handleApiError(error, '確認採購單失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const withdrawPO = async (poNo: string, data: WithdrawPORequest) => {
    try {
      loading.value = true
      const withdrawnPO = await procurementApi.withdrawPO(poNo, data)
      
      // Update in list
      const index = purchaseOrders.value.findIndex(po => po.purchase_order_no === poNo)
      if (index !== -1) {
        purchaseOrders.value[index] = withdrawnPO
      }
      
      // Update current if it's the same one
      if (currentPO.value?.purchase_order_no === poNo) {
        currentPO.value = withdrawnPO
      }

      ElMessage.success('採購單已撤回')
      return withdrawnPO
    } catch (error) {
      handleApiError(error, '撤回採購單失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const reorganizePO = async (poNo: string, data: ReorganizePORequest) => {
    try {
      loading.value = true
      const reorganizedPO = await procurementApi.reorganizePO(poNo, data)
      
      // Update in list
      const index = purchaseOrders.value.findIndex(po => po.purchase_order_no === poNo)
      if (index !== -1) {
        purchaseOrders.value[index] = reorganizedPO
      }
      
      // Update current if it's the same one
      if (currentPO.value?.purchase_order_no === poNo) {
        currentPO.value = reorganizedPO
      }

      ElMessage.success('採購單重組成功')
      return reorganizedPO
    } catch (error) {
      handleApiError(error, '重組採購單失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const clearCurrentPO = () => {
    currentPO.value = null
  }

  const clearBuildCandidates = () => {
    buildCandidates.value = null
  }

  return {
    // State
    purchaseOrders,
    buildCandidates,
    currentPO,
    loading,
    pagination,
    filters,

    // Getters
    poBySupplier,
    activePOs,
    poById,

    // Actions
    fetchBuildCandidates,
    createPO,
    fetchPurchaseOrders,
    fetchPurchaseOrderDetail,
    updatePurchaseOrder,
    confirmPurchase,
    withdrawPO,
    reorganizePO,
    clearCurrentPO,
    clearBuildCandidates
  }
})