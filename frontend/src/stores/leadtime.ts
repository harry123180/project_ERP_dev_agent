import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { leadtimeApi } from '@/api'
import type { 
  ShipmentData,
  LeadTimeFilters,
  UpdateMilestoneRequest,
  ConsolidationData,
  CreateConsolidationRequest,
  AddPOToConsolidationRequest,
  BulkMilestoneUpdateRequest
} from '@/api/leadtime'
import { handleApiError } from '@/api'

export const useLeadTimeStore = defineStore('leadtime', () => {
  // State
  const shipments = ref<ShipmentData[]>([])
  const consolidations = ref<ConsolidationData[]>([])
  const currentShipment = ref<ShipmentData | null>(null)
  const currentConsolidation = ref<ConsolidationData | null>(null)
  const loading = ref(false)

  // Getters
  const activeShipments = computed(() => 
    shipments.value.filter(shipment => 
      shipment.shipping_status !== 'none' && shipment.shipping_status !== 'arrived'
    )
  )

  const domesticShipments = computed(() => 
    shipments.value.filter(shipment => 
      // This would need to be determined by supplier region or other criteria
      true // Placeholder
    )
  )

  const internationalShipments = computed(() => 
    shipments.value.filter(shipment => 
      // This would need to be determined by supplier region or other criteria
      true // Placeholder
    )
  )

  const shipmentsByStatus = computed(() => {
    const grouped: Record<string, ShipmentData[]> = {}
    shipments.value.forEach(shipment => {
      const status = shipment.shipping_status || 'none'
      if (!grouped[status]) {
        grouped[status] = []
      }
      grouped[status].push(shipment)
    })
    return grouped
  })

  // Actions
  const fetchShipments = async (filters: LeadTimeFilters = {}) => {
    try {
      loading.value = true
      const shipmentsData = await leadtimeApi.getShipments(filters)
      shipments.value = shipmentsData
    } catch (error) {
      handleApiError(error, '獲取發貨跟蹤數據失敗')
    } finally {
      loading.value = false
    }
  }

  const updateMilestone = async (poNo: string, data: UpdateMilestoneRequest) => {
    try {
      loading.value = true
      const updatedPO = await leadtimeApi.updateMilestone(poNo, data)
      
      // Update shipment in list
      const shipmentIndex = shipments.value.findIndex(s => s.purchase_order_no === poNo)
      if (shipmentIndex !== -1) {
        shipments.value[shipmentIndex] = {
          ...shipments.value[shipmentIndex],
          shipping_status: data.shipping_status,
          shipped_at: data.shipped_at,
          eta_date: data.eta_date,
          arrival_date: data.arrival_date,
          carrier: data.carrier,
          tracking_no: data.tracking_no,
          logistics_note: data.logistics_note
        }
      }

      ElMessage.success('發貨里程碑更新成功')
      return updatedPO
    } catch (error) {
      handleApiError(error, '更新發貨里程碑失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchConsolidations = async () => {
    try {
      loading.value = true
      const consolidationsData = await leadtimeApi.getConsolidations()
      consolidations.value = consolidationsData
    } catch (error) {
      handleApiError(error, '獲取拼櫃信息失敗')
    } finally {
      loading.value = false
    }
  }

  const fetchConsolidationDetail = async (id: string) => {
    try {
      loading.value = true
      const consolidation = await leadtimeApi.getConsolidation(id)
      currentConsolidation.value = consolidation
      return consolidation
    } catch (error) {
      handleApiError(error, '獲取拼櫃詳情失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const createConsolidation = async (data: CreateConsolidationRequest) => {
    try {
      loading.value = true
      const consolidation = await leadtimeApi.createConsolidation(data)
      consolidations.value.unshift(consolidation)
      ElMessage.success('拼櫃創建成功')
      return consolidation
    } catch (error) {
      handleApiError(error, '創建拼櫃失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const addPOToConsolidation = async (consolidationId: string, data: AddPOToConsolidationRequest) => {
    try {
      loading.value = true
      const updatedConsolidation = await leadtimeApi.addPOToConsolidation(consolidationId, data)
      
      // Update in list
      const index = consolidations.value.findIndex(c => c.consolidation_id === consolidationId)
      if (index !== -1) {
        consolidations.value[index] = updatedConsolidation
      }
      
      // Update current if it's the same one
      if (currentConsolidation.value?.consolidation_id === consolidationId) {
        currentConsolidation.value = updatedConsolidation
      }

      ElMessage.success('採購單已加入拼櫃')
      return updatedConsolidation
    } catch (error) {
      handleApiError(error, '添加採購單到拼櫃失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const bulkUpdateMilestone = async (consolidationId: string, data: BulkMilestoneUpdateRequest) => {
    try {
      loading.value = true
      const updatedConsolidation = await leadtimeApi.bulkUpdateMilestone(consolidationId, data)
      
      // Update in list
      const index = consolidations.value.findIndex(c => c.consolidation_id === consolidationId)
      if (index !== -1) {
        consolidations.value[index] = updatedConsolidation
      }
      
      // Update current if it's the same one
      if (currentConsolidation.value?.consolidation_id === consolidationId) {
        currentConsolidation.value = updatedConsolidation
      }

      // Update related shipments
      updatedConsolidation.purchase_orders.forEach(po => {
        const shipmentIndex = shipments.value.findIndex(s => s.purchase_order_no === po.purchase_order_no)
        if (shipmentIndex !== -1) {
          shipments.value[shipmentIndex] = {
            ...shipments.value[shipmentIndex],
            shipping_status: data.shipping_status,
            shipped_at: data.shipped_at,
            eta_date: data.eta_date,
            arrival_date: data.arrival_date,
            carrier: data.carrier,
            tracking_no: data.tracking_no,
            logistics_note: data.logistics_note
          }
        }
      })

      ElMessage.success('批量更新里程碑成功')
      return updatedConsolidation
    } catch (error) {
      handleApiError(error, '批量更新里程碑失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const clearCurrentShipment = () => {
    currentShipment.value = null
  }

  const clearCurrentConsolidation = () => {
    currentConsolidation.value = null
  }

  return {
    // State
    shipments,
    consolidations,
    currentShipment,
    currentConsolidation,
    loading,

    // Getters
    activeShipments,
    domesticShipments,
    internationalShipments,
    shipmentsByStatus,

    // Actions
    fetchShipments,
    updateMilestone,
    fetchConsolidations,
    fetchConsolidationDetail,
    createConsolidation,
    addPOToConsolidation,
    bulkUpdateMilestone,
    clearCurrentShipment,
    clearCurrentConsolidation
  }
})