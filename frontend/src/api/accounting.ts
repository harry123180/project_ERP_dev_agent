import api, { type PaginatedResponse, createIdempotentRequest } from './index'
import type { PurchaseOrder } from '@/types/common'

export interface BillingCandidate {
  purchase_order_no: string
  supplier_name: string
  order_date: string
  grand_total_int: number
  billing_status: string
}

export interface BillingCandidatesFilters {
  supplier_id?: string
  month?: string
}

export interface BillingBatch {
  billing_id: string
  supplier_id: string
  supplier_name: string
  billing_month: string
  total_amount: number
  payment_terms: string
  due_date?: string
  billing_status: 'billed' | 'paid'
  payment_method?: 'remittance' | 'check' | 'cash'
  created_at: string
  purchase_orders: BillingCandidate[]
}

export interface CreateBillingRequest {
  supplier_id: string
  month: string
  payment_terms: string
  due_date?: string
  po_numbers: string[]
}

export interface PaymentHistoryFilters {
  supplier_id?: string
  month?: string
  paid?: boolean
  page?: number
  page_size?: number
}

export interface PaymentHistoryItem {
  billing_id?: string
  purchase_order_no?: string
  supplier_name: string
  amount: number
  billing_month?: string
  payment_method?: string
  billing_status: string
  created_at: string
  paid_at?: string
}

export interface MarkPaidRequest {
  payment_method: 'remittance' | 'check' | 'cash'
  paid_date?: string
  notes?: string
}

export interface InvoiceSearchFilters {
  supplier_id: string
  invoice_month: string
}

export interface InvoiceSearchResponse {
  purchase_orders: any[]
  search_period: {
    start_date: string
    end_date: string
    payment_days: number
  }
}

export interface InvoiceExportRequest {
  supplier_id: string
  invoice_month: string
  search_results: string[]
}

export const accountingApi = {
  // Get unbilled purchase orders for billing
  getBillingCandidates: async (filters: BillingCandidatesFilters = {}): Promise<BillingCandidate[]> => {
    const response = await api.get('/ap/billing/candidates', { params: filters })
    return response.data
  },

  // Generate billing batch
  generateBilling: async (data: CreateBillingRequest): Promise<BillingBatch> => {
    const response = await api.post('/ap/billing', data)
    return response.data
  },

  // Mark billing batch as paid
  markBillingPaid: async (billingId: string, data: MarkPaidRequest): Promise<BillingBatch> => {
    const headers = createIdempotentRequest()
    const response = await api.post(`/ap/billing/${billingId}/mark-paid`, data, { headers })
    return response.data
  },

  // Mark individual PO as paid
  markPOPaid: async (poNo: string, data: MarkPaidRequest): Promise<PurchaseOrder> => {
    const response = await api.post(`/ap/po/${poNo}/mark-paid`, data)
    return response.data
  },

  // Get payment history
  getPaymentHistory: async (filters: PaymentHistoryFilters = {}): Promise<PaginatedResponse<PaymentHistoryItem>> => {
    const response = await api.get('/ap/history', { params: filters })
    return response.data
  },

  // Invoice management search
  searchInvoiceManagement: async (filters: InvoiceSearchFilters): Promise<InvoiceSearchResponse> => {
    const response = await api.get('/accounting/invoice-management/search', { params: filters })
    return response.data
  },

  // Export invoice management data
  exportInvoiceManagement: async (data: InvoiceExportRequest): Promise<Blob> => {
    const response = await api.post('/accounting/invoice-management/export', data, {
      responseType: 'blob'
    })
    return response.data
  }
}