// Utility types for better TypeScript support

// Make all properties optional
export type Partial<T> = {
  [P in keyof T]?: T[P]
}

// Make all properties required
export type Required<T> = {
  [P in keyof T]-?: T[P]
}

// Pick specific properties from a type
export type Pick<T, K extends keyof T> = {
  [P in K]: T[P]
}

// Omit specific properties from a type
export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>

// Create a new type with some properties optional
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

// Create a new type with some properties required
export type RequiredBy<T, K extends keyof T> = Omit<T, K> & Required<Pick<T, K>>

// Extract the type of array elements
export type ArrayElement<T> = T extends readonly (infer U)[] ? U : never

// Extract the return type of a function
export type ReturnType<T extends (...args: any) => any> = T extends (...args: any) => infer R ? R : any

// Extract the parameter types of a function
export type Parameters<T extends (...args: any) => any> = T extends (...args: infer P) => any ? P : never

// Create a type that allows string keys with a specific value type
export type Record<K extends keyof any, T> = {
  [P in K]: T
}

// Union to intersection type
export type UnionToIntersection<U> = (U extends any ? (k: U) => void : never) extends (k: infer I) => void ? I : never

// Deep partial type
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

// Deep readonly type
export type DeepReadonly<T> = {
  readonly [P in keyof T]: T[P] extends object ? DeepReadonly<T[P]> : T[P]
}

// Value of object type
export type ValueOf<T> = T[keyof T]

// Non-nullable type
export type NonNullable<T> = T extends null | undefined ? never : T

// Conditional type utilities
export type If<C extends boolean, T, F> = C extends true ? T : F

// String manipulation types
export type Capitalize<S extends string> = S extends `${infer F}${infer R}` ? `${Uppercase<F>}${R}` : S

export type Uncapitalize<S extends string> = S extends `${infer F}${infer R}` ? `${Lowercase<F>}${R}` : S

// API response wrapper types
export type APIResponse<T = any> = {
  data: T
  message?: string
  success: boolean
}

export type APIError = {
  error: {
    code: string
    message: string
    details?: Record<string, any>
  }
}

export type APIResult<T = any> = APIResponse<T> | APIError

// Pagination types
export type PaginationMeta = {
  page: number
  page_size: number
  total: number
  pages: number
}

export type PaginatedData<T = any> = {
  items: T[]
  pagination: PaginationMeta
}

// Form data types
export type FormData<T = any> = {
  [K in keyof T]: T[K]
}

export type FormErrors<T = any> = {
  [K in keyof T]?: string | string[]
}

export type FormValidation<T = any> = {
  data: FormData<T>
  errors: FormErrors<T>
  isValid: boolean
}

// Event handler types
export type EventHandler<T = any> = (event: T) => void
export type AsyncEventHandler<T = any> = (event: T) => Promise<void>

// Component props types
export type ComponentProps<T = any> = {
  [K in keyof T]: T[K]
}

export type WithOptionalProps<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

// Status types
export type LoadingStatus = 'idle' | 'loading' | 'success' | 'error'

export type AsyncState<T = any> = {
  data: T | null
  status: LoadingStatus
  error: string | null
}

// Configuration types
export type Config<T = any> = {
  [K in keyof T]: T[K]
}

export type DeepConfig<T> = {
  [P in keyof T]: T[P] extends object ? DeepConfig<T[P]> : T[P]
}

// ID types for different entities
export type UserId = number
export type RequestOrderNo = string
export type PurchaseOrderNo = string
export type SupplierId = string
export type StorageId = string
export type ProjectId = string

// Timestamp types
export type Timestamp = string
export type DateString = string
export type TimeString = string

// Money amount type (stored as integer cents)
export type MoneyAmount = number

// Quantity type
export type Quantity = number

// Business entity base type
export type BaseEntity = {
  created_at?: Timestamp
  updated_at?: Timestamp
}

// Generic CRUD operations result types
export type CreateResult<T> = T
export type UpdateResult<T> = T
export type DeleteResult = { success: boolean }
export type ReadResult<T> = T
export type ListResult<T> = PaginatedData<T>

// Permission check result
export type HasPermission = boolean

// Filter types
export type StringFilter = string
export type NumberFilter = number
export type DateFilter = DateString
export type DateRangeFilter = [DateString, DateString]
export type BooleanFilter = boolean
export type ArrayFilter<T> = T[]

// Sort types
export type SortDirection = 'asc' | 'desc'
export type SortField = string
export type SortConfig = {
  field: SortField
  direction: SortDirection
}

// Search types
export type SearchQuery = string
export type SearchField = string
export type SearchConfig = {
  query: SearchQuery
  fields?: SearchField[]
}

// Export types
export type ExportFormat = 'csv' | 'xlsx' | 'pdf'
export type ExportConfig = {
  format: ExportFormat
  filename?: string
  columns?: string[]
}

// Import types  
export type ImportFormat = 'csv' | 'xlsx'
export type ImportResult = {
  success: boolean
  imported_count: number
  error_count: number
  errors?: string[]
}