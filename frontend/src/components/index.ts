// Component exports for easier importing

// Core components
export { default as DataTable } from './DataTable.vue'
export { default as FormDialog } from './FormDialog.vue' 
export { default as StatusTag } from './StatusTag.vue'
export { default as PageHeader } from './PageHeader.vue'
export { default as StatCard } from './StatCard.vue'
export { default as ConfirmDialog } from './ConfirmDialog.vue'

// Re-export useful functions and types
// Note: statusConfigs is not exported from StatusTag.vue - removed invalid export
// export { statusConfigs } from './StatusTag.vue'
// export { useConfirmDialog } from './ConfirmDialog.vue'

// Component type definitions
export type DataTableInstance = InstanceType<typeof import('./DataTable.vue').default>
export type FormDialogInstance = InstanceType<typeof import('./FormDialog.vue').default>

// Common component props interfaces
export interface DataTableProps {
  data?: any[]
  loading?: boolean
  columns: import('@/types/ui').TableColumn[]
  actions?: import('@/types/ui').TableAction[]
  showFilterBar?: boolean
  filterFields?: import('@/types/ui').FilterBarField[]
  showToolbar?: boolean
  showCreate?: boolean
  showExport?: boolean
  showSelection?: boolean
  showIndex?: boolean
  showPagination?: boolean
  total?: number
  pageSize?: number
}

export interface FormDialogProps {
  visible?: boolean
  title?: string
  fields: import('@/types/ui').FormField[]
  data?: Record<string, any>
  rules?: Record<string, any>
  submitting?: boolean
}

export interface StatusTagProps {
  status: string
  size?: 'large' | 'default' | 'small'
  showText?: boolean
  customLabels?: Record<string, string>
  customTypes?: Record<string, import('@/types/ui').StatusType>
}

export interface StatCardProps {
  title: string
  value: string | number
  unit?: string
  icon?: string
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  loading?: boolean
  trend?: {
    value: number
    isUp: boolean
  }
}

export interface PageHeaderProps {
  title: string
  subtitle?: string
  description?: string
  badge?: string | number
  showBack?: boolean
  showRefresh?: boolean
  breadcrumb?: import('@/types').BreadcrumbItem[]
  tabs?: import('@/types').TabItem[]
  activeTab?: string
}