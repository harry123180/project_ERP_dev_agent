import request from './index'

interface SupplierQuery {
  page?: number
  page_size?: number
  region?: string
  active?: boolean
  q?: string
}

interface SupplierData {
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
  is_active?: boolean
}

interface PurchaseOrderQuery {
  page?: number
  page_size?: number
  status?: string
  start_date?: string
  end_date?: string
}

const supplierApi = {
  // Get list of suppliers
  getSuppliers(params?: SupplierQuery) {
    return request.get('/suppliers', { params })
  },

  // Get supplier by ID
  getSupplier(id: string) {
    return request.get(`/suppliers/${id}`)
  },

  // Create new supplier
  createSupplier(data: SupplierData) {
    return request.post('/suppliers', data)
  },

  // Update supplier
  updateSupplier(id: string, data: Partial<SupplierData>) {
    return request.put(`/suppliers/${id}`, data)
  },

  // Delete supplier (soft delete)
  deleteSupplier(id: string) {
    return request.delete(`/suppliers/${id}`)
  },

  // Get suppliers summary for dropdowns
  getSuppliersSummary(params?: { region?: string; active?: boolean }) {
    return request.get('/suppliers/summary', { params })
  },

  // Get purchase orders for a specific supplier
  getSupplierPurchaseOrders(supplierId: string, params?: PurchaseOrderQuery) {
    return request.get(`/suppliers/${supplierId}/purchase-orders`, { params })
  },

  // Get supplier statistics
  getSupplierStats(supplierId: string) {
    return request.get(`/suppliers/${supplierId}/stats`)
  },

  // Export supplier data
  exportSuppliers(params?: SupplierQuery) {
    return request.get('/suppliers/export', { 
      params,
      responseType: 'blob'
    })
  },

  // Import suppliers from file
  importSuppliers(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return request.post('/suppliers/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}

export { supplierApi }
export default supplierApi