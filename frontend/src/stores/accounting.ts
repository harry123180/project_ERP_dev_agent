import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { accountingApi } from '@/api'
import type { 
  BillingCandidate,
  BillingCandidatesFilters,
  BillingBatch,
  CreateBillingRequest,
  PaymentHistoryFilters,
  PaymentHistoryItem,
  MarkPaidRequest
} from '@/api/accounting'
import { handleApiError } from '@/api'

export const useAccountingStore = defineStore('accounting', () => {
  // State
  const billingCandidates = ref<BillingCandidate[]>([])
  const billingBatches = ref<BillingBatch[]>([])
  const paymentHistory = ref<PaymentHistoryItem[]>([])
  const loading = ref(false)
  const pagination = ref({
    page: 1,
    page_size: 20,
    total: 0,
    pages: 0
  })

  // Getters
  const candidatesBySupplier = computed(() => {
    const grouped: Record<string, BillingCandidate[]> = {}
    billingCandidates.value.forEach(candidate => {
      const supplierName = candidate.supplier_name
      if (!grouped[supplierName]) {
        grouped[supplierName] = []
      }
      grouped[supplierName].push(candidate)
    })
    return grouped
  })

  const totalCandidateAmount = computed(() => 
    billingCandidates.value.reduce((sum, candidate) => sum + candidate.grand_total_int, 0)
  )

  const unpaidBillings = computed(() => 
    paymentHistory.value.filter(item => item.billing_status === 'billed')
  )

  const paidBillings = computed(() => 
    paymentHistory.value.filter(item => item.billing_status === 'paid')
  )

  const totalUnpaidAmount = computed(() => 
    unpaidBillings.value.reduce((sum, item) => sum + item.amount, 0)
  )

  // Actions
  const fetchBillingCandidates = async (filters: BillingCandidatesFilters = {}) => {
    try {
      loading.value = true
      const candidates = await accountingApi.getBillingCandidates(filters)
      billingCandidates.value = candidates
    } catch (error) {
      handleApiError(error, '獲取待開票項目失敗')
    } finally {
      loading.value = false
    }
  }

  const generateBilling = async (data: CreateBillingRequest) => {
    try {
      loading.value = true
      const billing = await accountingApi.generateBilling(data)
      billingBatches.value.unshift(billing)
      
      // Remove processed candidates from list
      billingCandidates.value = billingCandidates.value.filter(
        candidate => !data.po_numbers.includes(candidate.purchase_order_no)
      )
      
      ElMessage.success('開票成功')
      return billing
    } catch (error) {
      handleApiError(error, '生成開票失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const markBillingPaid = async (billingId: string, data: MarkPaidRequest) => {
    try {
      loading.value = true
      const updatedBilling = await accountingApi.markBillingPaid(billingId, data)
      
      // Update in billing batches list
      const batchIndex = billingBatches.value.findIndex(batch => batch.billing_id === billingId)
      if (batchIndex !== -1) {
        billingBatches.value[batchIndex] = updatedBilling
      }
      
      // Refresh payment history to show updated status
      await fetchPaymentHistory()
      
      ElMessage.success('付款標記成功')
      return updatedBilling
    } catch (error) {
      handleApiError(error, '標記付款失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const markPOPaid = async (poNo: string, data: MarkPaidRequest) => {
    try {
      loading.value = true
      const updatedPO = await accountingApi.markPOPaid(poNo, data)
      
      // Refresh payment history to show updated status
      await fetchPaymentHistory()
      
      ElMessage.success('採購單付款標記成功')
      return updatedPO
    } catch (error) {
      handleApiError(error, '標記採購單付款失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchPaymentHistory = async (filters: PaymentHistoryFilters = {}) => {
    try {
      loading.value = true
      const response = await accountingApi.getPaymentHistory(filters)
      paymentHistory.value = response.items
      pagination.value = response.pagination
    } catch (error) {
      handleApiError(error, '獲取付款歷史失敗')
    } finally {
      loading.value = false
    }
  }

  const getSupplierPaymentSummary = (supplierId: string) => {
    const supplierHistory = paymentHistory.value.filter(item => 
      item.supplier_name === supplierId // This would need supplier ID matching
    )
    
    const totalAmount = supplierHistory.reduce((sum, item) => sum + item.amount, 0)
    const unpaidAmount = supplierHistory
      .filter(item => item.billing_status === 'billed')
      .reduce((sum, item) => sum + item.amount, 0)
    const paidAmount = supplierHistory
      .filter(item => item.billing_status === 'paid')
      .reduce((sum, item) => sum + item.amount, 0)

    return {
      totalAmount,
      unpaidAmount,
      paidAmount,
      itemCount: supplierHistory.length
    }
  }

  const getMonthlyPaymentSummary = (month: string) => {
    const monthHistory = paymentHistory.value.filter(item => 
      item.billing_month === month
    )
    
    const totalAmount = monthHistory.reduce((sum, item) => sum + item.amount, 0)
    const unpaidAmount = monthHistory
      .filter(item => item.billing_status === 'billed')
      .reduce((sum, item) => sum + item.amount, 0)
    const paidAmount = monthHistory
      .filter(item => item.billing_status === 'paid')
      .reduce((sum, item) => sum + item.amount, 0)

    return {
      totalAmount,
      unpaidAmount,
      paidAmount,
      itemCount: monthHistory.length
    }
  }

  const clearCandidates = () => {
    billingCandidates.value = []
  }

  return {
    // State
    billingCandidates,
    billingBatches,
    paymentHistory,
    loading,
    pagination,

    // Getters
    candidatesBySupplier,
    totalCandidateAmount,
    unpaidBillings,
    paidBillings,
    totalUnpaidAmount,

    // Actions
    fetchBillingCandidates,
    generateBilling,
    markBillingPaid,
    markPOPaid,
    fetchPaymentHistory,
    getSupplierPaymentSummary,
    getMonthlyPaymentSummary,
    clearCandidates
  }
})