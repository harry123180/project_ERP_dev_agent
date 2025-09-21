import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      name: 'Layout',
      component: () => import('@/layout/index.vue'),
      meta: { requiresAuth: true },
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
          meta: { title: '儀表板', icon: 'Dashboard' }
        },
        {
          path: 'profile',
          name: 'Profile',
          component: () => import('@/views/Profile.vue'),
          meta: { title: '個人資料', icon: 'User', hideInMenu: true }
        },
        {
          path: 'requisitions',
          name: 'Requisitions',
          component: () => import('@/views/requisitions/index.vue'),
          meta: { title: '請購管理', icon: 'Document' },
          children: [
            {
              path: '',
              name: 'RequisitionList',
              component: () => import('@/views/requisitions/List.vue'),
              meta: { title: '請購單列表' }
            },
            {
              path: 'create',
              name: 'RequisitionCreate',
              component: () => import('@/views/requisitions/Form.vue'),
              meta: { title: '新增請購單' }
            },
            {
              path: ':id/edit',
              name: 'RequisitionEdit',
              component: () => import('@/views/requisitions/Form.vue'),
              meta: { title: '編輯請購單', hideInMenu: true }
            },
            {
              path: ':id',
              name: 'RequisitionDetail',
              component: () => import('@/views/requisitions/Detail.vue'),
              meta: { title: '請購單詳情', hideInMenu: true }
            },
            {
              path: 'questioned-items',
              name: 'QuestionedItems',
              component: () => import('@/views/requisitions/QuestionedItems.vue'),
              meta: { title: '管理疑問項目', requiresRole: ['Admin', 'ProcurementMgr', 'Procurement', 'Manager'] }
            }
          ]
        },
        {
          path: 'purchase-orders',
          name: 'PurchaseOrders',
          component: () => import('@/views/purchase-orders/index.vue'),
          meta: { title: '採購管理', icon: 'ShoppingCart', requiresRole: ['Admin', 'ProcurementMgr', 'Procurement', 'Manager'] },
          children: [
            {
              path: '',
              name: 'PurchaseOrderList',
              component: () => import('@/views/purchase-orders/List.vue'),
              meta: { title: '採購單列表' }
            },
            {
              path: 'create',
              name: 'PurchaseOrderCreate',
              component: () => import('@/views/purchase-orders/Form.vue'),
              meta: { title: '新增採購單' }
            },
            {
              path: 'build-candidates',
              name: 'PurchaseOrderBuildCandidates',
              component: () => import('@/views/purchase-orders/BuildCandidates.vue'),
              meta: { title: '建立採購單' }
            },
            {
              path: 'delivery',
              name: 'PurchaseOrderDelivery',
              component: () => import('@/views/purchase-orders/DeliveryMaintenance.vue'),
              meta: { title: '交期維護' }
            },
            {
              path: 'consolidation/:id',
              name: 'ConsolidationDetail',
              component: () => import('@/views/purchase-orders/ConsolidationDetail.vue'),
              meta: { title: '集運單詳情', hideInMenu: true }
            },
            {
              path: 'price-history',
              name: 'PurchaseOrderPriceHistory',
              component: () => import('@/views/purchase-orders/PriceHistory.vue'),
              meta: { title: '歷史價格查詢' }
            },
            {
              path: 'questions',
              name: 'PurchaseOrderQuestions',
              component: () => import('@/views/purchase-orders/QuestionsOverview.vue'),
              meta: { title: '疑問總覽' }
            },
            {
              path: ':id/edit',
              name: 'PurchaseOrderEdit',
              component: () => import('@/views/purchase-orders/Form.vue'),
              meta: { title: '編輯採購單', hideInMenu: true }
            },
            {
              path: ':id',
              name: 'PurchaseOrderDetail',
              component: () => import('@/views/purchase-orders/Detail.vue'),
              meta: { title: '採購單詳情', hideInMenu: true }
            }
          ]
        },
        {
          path: 'projects',
          name: 'Projects',
          component: () => import('@/views/projects/index.vue'),
          meta: { title: '專案管理', icon: 'FolderOpened', requiresRole: ['Admin', 'Manager', 'ProcurementMgr', 'Procurement', 'Accountant'] },
          children: [
            {
              path: '',
              name: 'ProjectList',
              component: () => import('@/views/projects/List.vue'),
              meta: { title: '專案列表' }
            },
            {
              path: 'create',
              name: 'ProjectCreate',
              component: () => import('@/views/projects/Form.vue'),
              meta: { title: '新增專案' }
            },
            {
              path: ':id',
              name: 'ProjectDetail',
              component: () => import('@/views/projects/Detail.vue'),
              meta: { title: '專案詳情', hideInMenu: true }
            },
            {
              path: ':id/edit',
              name: 'ProjectEdit',
              component: () => import('@/views/projects/Form.vue'),
              meta: { title: '編輯專案', hideInMenu: true }
            }
          ]
        },
        {
          path: 'inventory',
          name: 'Inventory',
          component: () => import('@/views/inventory/index.vue'),
          redirect: '/inventory/query',
          meta: { title: '庫存管理', icon: 'Box' },
          children: [
            {
              path: 'query',
              name: 'InventoryQuery',
              component: () => import('@/views/inventory/Query.vue'),
              meta: { title: '庫存查詢' }
            },
            {
              path: 'receiving',
              name: 'InventoryReceiving',
              component: () => import('@/views/inventory/Receiving.vue'),
              meta: { title: '收貨管理' }
            },
            {
              path: 'storage',
              name: 'Storage',
              component: () => import('@/views/inventory/Storage.vue'),
              meta: { title: '儲位管理' }
            },
            {
              path: 'acceptance',
              name: 'Acceptance',
              component: () => import('@/views/inventory/Acceptance.vue'),
              meta: { title: '驗收管理' }
            },
            {
              path: 'items/:itemKey/details',
              name: 'InventoryItemDetails',
              component: () => import('@/views/inventory/ItemDetails.vue'),
              meta: { title: '物料詳情', hideInMenu: true }
            }
          ]
        },
        {
          path: 'accounting',
          name: 'Accounting',
          component: () => import('@/views/accounting/index.vue'),
          meta: { title: '會計管理', icon: 'Money', requiresRole: ['Admin', 'ProcurementMgr', 'Accountant'] },
          children: [
            {
              path: '',
              name: 'AccountingDashboard',
              component: () => import('@/views/accounting/Dashboard.vue'),
              meta: { title: '請款管理' }
            },
            {
              path: 'payment-management',
              name: 'PaymentManagement',
              component: () => import('@/views/accounting/PaymentManagement.vue'),
              meta: { title: '付款管理' }
            }
          ]
        },
        {
          path: 'suppliers',
          name: 'Suppliers',
          component: () => import('@/views/suppliers/index.vue'),
          meta: { title: '供應商管理', icon: 'Shop', requiresRole: ['Admin', 'Manager', 'ProcurementMgr', 'Procurement', 'Accountant'] },
          children: [
            {
              path: '',
              name: 'SupplierList',
              component: () => import('@/views/suppliers/List.vue'),
              meta: { title: '供應商列表' }
            },
            {
              path: 'create',
              name: 'SupplierCreate',
              component: () => import('@/views/suppliers/Form.vue'),
              meta: { title: '新增供應商' }
            },
            {
              path: ':id',
              name: 'SupplierDetail',
              component: () => import('@/views/suppliers/Detail.vue'),
              meta: { title: '供應商詳情', hideInMenu: true }
            },
            {
              path: ':id/edit',
              name: 'SupplierEdit',
              component: () => import('@/views/suppliers/Form.vue'),
              meta: { title: '編輯供應商', hideInMenu: true }
            },
            {
              path: ':id/purchase-orders',
              name: 'SupplierPurchaseOrders',
              component: () => import('@/views/suppliers/PurchaseOrders.vue'),
              meta: { title: '供應商採購單', hideInMenu: true }
            }
          ]
        },
        {
          path: 'system',
          name: 'System',
          component: () => import('@/views/system/index.vue'),
          meta: { title: '系統管理', icon: 'Setting', requiresRole: ['Admin'] },
          children: [
            {
              path: 'users',
              name: 'Users',
              component: () => import('@/views/system/Users.vue'),
              meta: { title: '用戶管理' }
            },
            {
              path: 'settings',
              name: 'Settings',
              component: () => import('@/views/system/Settings.vue'),
              meta: { title: '系統設定' }
            },
            {
              path: 'po-settings',
              name: 'POSettings',
              component: () => import('@/views/system/POSettings.vue'),
              meta: { title: '採購單資訊設定' }
            }
          ]
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/404.vue')
    }
  ]
})

// Navigation guards
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // Initialize auth state from localStorage if not already done
  if (!authStore.token && localStorage.getItem('auth_token')) {
    authStore.initializeAuth()
  }
  
  // Check if route requires authentication
  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    next('/login')
    return
  }
  
  // If authenticated user tries to access login page, redirect to dashboard
  if (to.path === '/login' && authStore.isAuthenticated) {
    next('/')
    return
  }
  
  // Check role-based access
  if (to.meta.requiresRole) {
    const requiredRoles = Array.isArray(to.meta.requiresRole) ? to.meta.requiresRole : [to.meta.requiresRole]
    if (!authStore.hasRole(...requiredRoles)) {
      // Redirect to dashboard or show access denied
      next('/')
      return
    }
  }
  
  next()
})

export default router