// Consolidated type exports
export * from './auth'
export * from './common'
export * from './ui'
export * from './utils'

// Re-export commonly used types with aliases
export type {
  User as AuthUser,
  UserRoleType as Role,
  LoginRequest,
  LoginResponse
} from './auth'

export type {
  RequestOrder as Requisition,
  RequestOrderItem as RequisitionItem,
  PurchaseOrder as PO,
  PurchaseOrderItem as POItem,
  Supplier,
  Storage,
  StorageHistory,
  Project,
  ItemStatus,
  PaginationParams,
  ListResponse,
  SelectOption as Option,
  STATUS_LABELS,
  STATUS_TYPES
} from './common'

export type {
  TableColumn,
  TableAction,
  FormField,
  ModalConfig,
  FilterBarField,
  ChartConfig,
  StatCard,
  TabItem,
  StepItem,
  TreeNode,
  StatusType,
  StatusConfig,
  MenuItem,
  ValidationRule,
  LoadingState,
  ErrorState
} from './ui'

export type {
  APIResponse,
  APIError,
  PaginatedData,
  FormData,
  FormErrors,
  FormValidation,
  EventHandler,
  AsyncEventHandler,
  LoadingStatus,
  AsyncState,
  UserId,
  RequestOrderNo,
  PurchaseOrderNo,
  SupplierId,
  Timestamp,
  MoneyAmount,
  Quantity,
  BaseEntity,
  HasPermission,
  SortDirection,
  SearchQuery,
  ExportFormat,
  ImportFormat
} from './utils'