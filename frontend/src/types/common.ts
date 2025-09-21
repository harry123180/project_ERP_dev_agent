export interface BaseEntity {
  created_at?: string
  updated_at?: string
}

export interface Supplier extends BaseEntity {
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
}

export interface ItemCategory extends BaseEntity {
  category_id: number
  category_code: string
  category_name: string
  sort_order: number
  is_active: boolean
}

export interface RequestOrder extends BaseEntity {
  request_order_no: string
  requester_id: number
  requester_name: string
  usage_type: 'daily' | 'project'
  project_id?: string
  submit_date?: string
  order_status: 'draft' | 'submitted' | 'reviewed'
  // 加急相關欄位
  is_urgent: boolean
  expected_delivery_date?: string
  urgent_reason?: string
  summary?: {
    total_items: number
    approved_items: number
    rejected_items: number
    questioned_items: number
    pending_items: number
  }
}

export interface RequestOrderItem extends BaseEntity {
  detail_id: number
  request_order_no: string
  item_name: string
  item_quantity: number
  item_unit: string
  item_specification?: string
  item_description?: string
  item_category?: string
  item_status: ItemStatus
  acceptance_status: 'pending_acceptance' | 'accepted'
  supplier_id?: string
  unit_price?: number
  material_serial_no?: string
  status_note?: string
  needs_acceptance: boolean
  subtotal: number
  supplier?: Supplier
  category_info?: ItemCategory
}



// 加急相關類型定義
export interface CreateRequisitionRequest {
  usage_type: 'daily' | 'project'
  project_id?: string
  status?: string
  items: RequisitionItem[]
  // 加急相關欄位
  is_urgent: boolean
  expected_delivery_date?: string
  urgent_reason?: string
}

export interface RequisitionItem {
  item_name: string
  item_quantity: number
  item_unit: string
  item_specification?: string
  item_description?: string
  item_category?: string
  needs_acceptance?: boolean
}

export interface UrgentSupplier {
  supplier_id: string
  supplier_name_zh: string
  urgent_item_count: number
}

export interface PurchaseOrder extends BaseEntity {
  purchase_order_no: string
  supplier_id: string
  supplier_name: string
  supplier_address?: string
  contact_phone?: string
  contact_person?: string
  supplier_tax_id?: string
  order_date?: string
  quotation_no?: string
  delivery_address?: string
  creation_date?: string
  creator_id: number
  output_person_id?: number
  notes?: string
  confirm_purchaser_id?: number
  purchase_status: 'order_created' | 'purchased'
  shipping_status: 'none' | 'shipped' | 'in_transit' | 'customs_clearance' | 'expected_arrival' | 'arrived'
  shipped_at?: string
  eta_date?: string
  arrival_date?: string
  carrier?: string
  tracking_no?: string
  logistics_note?: string
  subtotal_int: number
  tax_decimal1: number
  grand_total_int: number
  billing_status: 'none' | 'billed' | 'paid'
  payment_method?: 'remittance' | 'check' | 'cash'
  due_date?: string
  billed_month?: string
  supplier?: Supplier
  creator?: any
  confirm_purchaser?: any
}

export interface PurchaseOrderItem extends BaseEntity {
  detail_id: number
  purchase_order_no: string
  item_name: string
  item_quantity: number
  item_unit: string
  unit_price: number
  item_specification?: string
  item_model?: string
  line_status: 'order_created' | 'purchased' | 'shipped' | 'arrived'
  line_subtotal_int: number
  line_subtotal: number
  source_request_order_no?: string
  source_detail_id?: number
  source_request_item?: RequestOrderItem
}

export interface Storage extends BaseEntity {
  storage_id: string
  area_code: string
  shelf_code: string
  floor_level: number
  front_back_position: number
  left_middle_right_position: number
  is_active: boolean
  current_inventory: number
}

export interface StorageHistory extends BaseEntity {
  history_id: number
  storage_id: string
  item_id: string
  operation_type: 'in' | 'out'
  operation_date: string
  operator_id: number
  quantity: number
  source_type?: string
  source_no?: string
  source_line?: number
  note?: string
  request_item_id?: number
  storage?: Storage
  operator?: any
  request_item?: RequestOrderItem
}

export interface Project extends BaseEntity {
  project_id: string
  project_name: string
  project_status: 'ongoing' | 'completed'
  start_date?: string
  end_date?: string
  total_expenditure: number
  customer_name?: string
  customer_contact?: string
  customer_address?: string
  customer_phone?: string
  customer_department?: string
  supplier_breakdown: ProjectSupplierExpenditure[]
}

export interface ProjectSupplierExpenditure extends BaseEntity {
  record_id: number
  project_id: string
  supplier_id: string
  expenditure_amount: number
  supplier?: Supplier
}

export interface SystemSettings extends BaseEntity {
  setting_id: number
  setting_type: string
  setting_key: string
  setting_value: string
  setting_description?: string
}

export type ItemStatus = 
  | 'draft' 
  | 'pending_review' 
  | 'approved' 
  | 'rejected' 
  | 'questioned' 
  | 'unavailable' 
  | 'order_created' 
  | 'purchased' 
  | 'shipped' 
  | 'arrived' 
  | 'warehoused' 
  | 'issued'

export interface PaginationParams {
  page?: number
  page_size?: number
}

export interface SortParams {
  sort?: string
  order?: 'asc' | 'desc'
}

export interface ListResponse<T> {
  items: T[]
  pagination: {
    page: number
    page_size: number
    total: number
    pages: number
  }
}

export interface SelectOption {
  label: string
  value: any
  disabled?: boolean
}

export interface BreadcrumbItem {
  text: string
  to?: string
}

// Form related types
export interface FormRules {
  [key: string]: any[]
}

// Status mapping for display
export const STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  submitted: '已提交',
  reviewed: '已審核',
  pending_review: '待審核',
  approved: '已核准',
  rejected: '已駁回',
  questioned: '有疑問',
  unavailable: '無法取得',
  order_created: '已建單',
  purchased: '已採購',
  shipped: '已出貨',
  arrived: '已到貨',
  received: '已收貨',
  warehoused: '已入庫',
  issued: '已領用',
  cancelled: '已撤銷',
  none: '無',
  billed: '已開票',
  paid: '已付款',
  domestic: '國內',
  international: '國外',
  daily: '日常',
  project: '專案',
  ongoing: '進行中',
  completed: '已完成',
  pending_acceptance: '待驗收',
  accepted: '已驗收'
}

// Status type mapping for styling
export const STATUS_TYPES: Record<string, string> = {
  draft: '',
  submitted: 'warning',
  reviewed: 'success',
  pending_review: 'warning',
  approved: 'success',
  rejected: 'danger',
  questioned: 'warning',
  unavailable: 'info',
  order_created: 'primary',
  purchased: 'success',
  shipped: 'primary',
  arrived: 'success',
  received: 'success',
  warehoused: 'success',
  issued: 'info',
  cancelled: 'info',
  none: '',
  billed: 'warning',
  paid: 'success'
}