import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export interface Supplier {
  supplier_id: string
  supplier_name_zh: string
  supplier_name_en?: string
  supplier_address?: string
  supplier_phone?: string
  supplier_email?: string
  supplier_contact_person?: string
  supplier_tax_id?: string
  supplier_region: 'domestic' | 'international'
  supplier_remark?: string
  payment_terms?: string
  bank_account?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SupplierSummary {
  supplier_id: string
  supplier_name_zh: string
  supplier_name_en?: string
  supplier_region: 'domestic' | 'international'
  is_active: boolean
}

export interface SuppliersListParams {
  page?: number
  page_size?: number
  region?: 'domestic' | 'international'
  active?: boolean
  q?: string
}

export interface SuppliersListResponse {
  items: Supplier[]
  pagination: {
    page: number
    page_size: number
    total: number
    pages: number
    has_next: boolean
    has_prev: boolean
  }
}

export const useSuppliersStore = defineStore('suppliers', () => {
  // State
  const suppliers = ref<Supplier[]>([])
  const currentSupplier = ref<Supplier | null>(null)
  const suppliersSummary = ref<SupplierSummary[]>([])
  const loading = ref(false)
  const pagination = ref({
    page: 1,
    page_size: 20,
    total: 0,
    pages: 0,
    has_next: false,
    has_prev: false
  })

  // Getters
  const activeSuppliers = computed(() => 
    suppliers.value.filter(supplier => supplier.is_active)
  )

  const domesticSuppliers = computed(() => 
    suppliers.value.filter(supplier => supplier.supplier_region === 'domestic')
  )

  const internationalSuppliers = computed(() => 
    suppliers.value.filter(supplier => supplier.supplier_region === 'international')
  )

  const getSupplierById = computed(() => {
    return (id: string) => suppliers.value.find(supplier => supplier.supplier_id === id)
  })

  // Actions
  const fetchSuppliers = async (params: SuppliersListParams = {}) => {
    loading.value = true
    try {
      const response = await api.get<SuppliersListResponse>('/suppliers', {
        params: {
          page: params.page || 1,
          page_size: params.page_size || 20,
          ...(params.region && { region: params.region }),
          ...(params.active !== undefined && { active: params.active }),
          ...(params.q && { q: params.q })
        }
      })

      // response.data is already the SuppliersListResponse object
      const data = response.data
      suppliers.value = data.items || []
      pagination.value = data.pagination || {
        page: 1,
        page_size: 20,
        total: 0,
        pages: 0,
        has_next: false,
        has_prev: false
      }
      
      return data
    } catch (error) {
      console.error('Error fetching suppliers:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchSupplierById = async (id: string) => {
    loading.value = true
    try {
      const response = await api.get<Supplier>(`/suppliers/${id}`)
      const supplier = response.data
      currentSupplier.value = supplier
      return supplier
    } catch (error) {
      console.error('Error fetching supplier:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const createSupplier = async (supplierData: Partial<Supplier>) => {
    loading.value = true
    try {
      const response = await api.post<Supplier>('/suppliers', supplierData)
      suppliers.value.unshift(response.data)
      return response.data
    } catch (error) {
      console.error('Error creating supplier:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const updateSupplier = async (id: string, supplierData: Partial<Supplier>) => {
    loading.value = true
    try {
      const response = await api.put<Supplier>(`/suppliers/${id}`, supplierData)
      
      const index = suppliers.value.findIndex(supplier => supplier.supplier_id === id)
      if (index !== -1) {
        suppliers.value[index] = response.data
      }
      
      if (currentSupplier.value?.supplier_id === id) {
        currentSupplier.value = response.data
      }
      
      return response.data
    } catch (error) {
      console.error('Error updating supplier:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchSuppliersSummary = async (params: { region?: string; active?: boolean } = {}) => {
    loading.value = true
    try {
      const response = await api.get<SupplierSummary[]>('/suppliers/summary', {
        params: {
          ...(params.region && { region: params.region }),
          ...(params.active !== undefined && { active: params.active })
        }
      })
      
      const summaryData = response.data || []
      suppliersSummary.value = summaryData
      return summaryData
    } catch (error) {
      console.error('Error fetching suppliers summary:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const clearCurrentSupplier = () => {
    currentSupplier.value = null
  }

  const clearSuppliers = () => {
    suppliers.value = []
    pagination.value = {
      page: 1,
      page_size: 20,
      total: 0,
      pages: 0,
      has_next: false,
      has_prev: false
    }
  }

  return {
    // State
    suppliers,
    currentSupplier,
    suppliersSummary,
    loading,
    pagination,
    
    // Getters
    activeSuppliers,
    domesticSuppliers,
    internationalSuppliers,
    getSupplierById,
    
    // Actions
    fetchSuppliers,
    fetchSupplierById,
    createSupplier,
    updateSupplier,
    fetchSuppliersSummary,
    clearCurrentSupplier,
    clearSuppliers
  }
})