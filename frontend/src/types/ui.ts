// UI component related types

export interface TableColumn {
  prop?: string
  label: string
  width?: string | number
  minWidth?: string | number
  fixed?: boolean | 'left' | 'right'
  sortable?: boolean | 'custom'
  formatter?: (row: any, column: any, cellValue: any, index: number) => string
  type?: 'selection' | 'index' | 'expand'
  align?: 'left' | 'center' | 'right'
  headerAlign?: 'left' | 'center' | 'right'
  showOverflowTooltip?: boolean
  resizable?: boolean
  cellClass?: string | ((row: any) => string)
}

export interface TableAction {
  label: string
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'text'
  icon?: string
  handler: (row: any, index: number) => void
  visible?: (row: any) => boolean
  disabled?: (row: any) => boolean
}

export interface FormField {
  prop: string
  label: string
  type: 'input' | 'select' | 'date' | 'datetime' | 'number' | 'textarea' | 'switch' | 'checkbox' | 'radio' | 'cascader' | 'upload'
  placeholder?: string
  options?: SelectOption[]
  rules?: any[]
  props?: Record<string, any>
  span?: number
  offset?: number
  required?: boolean
  disabled?: boolean
  readonly?: boolean
  clearable?: boolean
  filterable?: boolean
  multiple?: boolean
  rows?: number
  maxlength?: number
  showWordLimit?: boolean
}

export interface SelectOption {
  label: string
  value: any
  disabled?: boolean
  children?: SelectOption[]
}

export interface ModalConfig {
  title: string
  width?: string | number
  fullscreen?: boolean
  center?: boolean
  closeOnClickModal?: boolean
  closeOnPressEscape?: boolean
  showClose?: boolean
  beforeClose?: (done: () => void) => void
}

export interface FilterBarField {
  prop: string
  label: string
  type: 'input' | 'select' | 'date' | 'daterange'
  placeholder?: string
  options?: SelectOption[]
  clearable?: boolean
  filterable?: boolean
  multiple?: boolean
  format?: string
  valueFormat?: string
}

export interface ChartConfig {
  type: 'line' | 'bar' | 'pie' | 'doughnut' | 'area'
  title?: string
  data: any[]
  xAxis?: string
  yAxis?: string
  colors?: string[]
  height?: number
}

export interface StatCard {
  title: string
  value: string | number
  unit?: string
  icon?: string
  color?: string
  trend?: {
    value: number
    isUp: boolean
  }
  loading?: boolean
}

export interface TabItem {
  name: string
  label: string
  count?: number
  disabled?: boolean
}

export interface StepItem {
  title: string
  description?: string
  status?: 'wait' | 'process' | 'finish' | 'error' | 'success'
}

export interface TreeNode {
  id: string | number
  label: string
  children?: TreeNode[]
  disabled?: boolean
  isLeaf?: boolean
  [key: string]: any
}

export interface UploadFile {
  name: string
  size: number
  type: string
  url?: string
  status?: 'ready' | 'uploading' | 'success' | 'error'
  percentage?: number
  response?: any
  error?: any
}

// Status badge types
export type StatusType = 'primary' | 'success' | 'info' | 'warning' | 'danger' | ''

export interface StatusConfig {
  [key: string]: {
    label: string
    type: StatusType
    icon?: string
  }
}

// Notification types
export interface NotificationItem {
  id: string
  title: string
  content?: string
  type: 'info' | 'success' | 'warning' | 'error'
  timestamp: string
  read: boolean
  action?: {
    text: string
    handler: () => void
  }
}

// Menu types
export interface MenuItem {
  id: string
  path: string
  name: string
  title: string
  icon?: string
  badge?: string | number
  roles?: string[]
  hidden?: boolean
  children?: MenuItem[]
  meta?: {
    keepAlive?: boolean
    breadcrumb?: boolean
    activeMenu?: string
  }
}

// Form validation rules
export interface ValidationRule {
  required?: boolean
  message?: string
  type?: 'string' | 'number' | 'boolean' | 'method' | 'regexp' | 'integer' | 'float' | 'array' | 'object' | 'enum' | 'date' | 'url' | 'hex' | 'email'
  pattern?: RegExp | string
  min?: number
  max?: number
  len?: number
  enum?: any[]
  whitespace?: boolean
  fields?: Record<string, ValidationRule>
  transform?: (value: any) => any
  validator?: (rule: any, value: any, callback: any, source?: any, options?: any) => void
  trigger?: 'blur' | 'change' | Array<'blur' | 'change'>
}

// Loading state
export interface LoadingState {
  global: boolean
  [key: string]: boolean
}

// Error state
export interface ErrorState {
  message: string
  code?: string | number
  details?: any
}

// Responsive breakpoints
export type BreakPoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl'

// Theme configuration
export interface ThemeConfig {
  primaryColor: string
  successColor: string
  warningColor: string
  dangerColor: string
  infoColor: string
  borderRadius: string
  fontSize: {
    small: string
    medium: string
    large: string
  }
}