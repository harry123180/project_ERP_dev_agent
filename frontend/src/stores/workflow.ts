/**
 * Master Workflow Store
 * Orchestrates the complete ERP workflow from requisition to accounting
 * Architecture Lead: Winston
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { WorkflowStep, WorkflowData, WorkflowTransition } from '@/types/workflow'

// Workflow step definitions
export const WORKFLOW_STEPS: Record<string, WorkflowStep> = {
  requisition: {
    id: 'requisition',
    name: '工程師請購',
    description: 'Engineers create purchase requisitions',
    component: 'RequisitionForm',
    roles: ['Everyone'],
    status: 'draft'
  },
  approval: {
    id: 'approval', 
    name: '採購審核',
    description: 'Procurement team reviews and approves requisitions',
    component: 'ApprovalReview',
    roles: ['Procurement', 'ProcurementMgr'],
    status: 'in_review'
  },
  procurement: {
    id: 'procurement',
    name: '採購單生成',
    description: 'Create purchase orders from approved requisitions',
    component: 'ProcurementOrder',
    roles: ['Procurement', 'ProcurementMgr'],
    status: 'approved'
  },
  confirmation: {
    id: 'confirmation',
    name: '供應商確認',
    description: 'Supplier confirms purchase orders',
    component: 'SupplierConfirmation',
    roles: ['Procurement', 'ProcurementMgr'],
    status: 'confirmed'
  },
  shipping: {
    id: 'shipping',
    name: '交期維護',
    description: 'Track shipping and delivery milestones',
    component: 'ShippingTracking',
    roles: ['Procurement', 'ProcurementMgr'],
    status: 'shipped'
  },
  receiving: {
    id: 'receiving',
    name: '收貨確認',
    description: 'Confirm receipt of delivered items',
    component: 'ReceivingConfirmation',
    roles: ['Everyone'],
    status: 'received'
  },
  storage: {
    id: 'storage',
    name: '儲位分配',
    description: 'Assign storage locations for received items',
    component: 'StorageAssignment',
    roles: ['Everyone'],
    status: 'stored'
  },
  acceptance: {
    id: 'acceptance',
    name: '請購人驗收',
    description: 'Original requestor accepts received items',
    component: 'AcceptanceConfirmation',
    roles: ['Everyone'],
    status: 'accepted'
  },
  inventory: {
    id: 'inventory',
    name: '庫存查詢領用',
    description: 'Query inventory and issue items for use',
    component: 'InventoryManagement',
    roles: ['Everyone'],
    status: 'issued'
  },
  accounting: {
    id: 'accounting',
    name: '會計請款付款',
    description: 'Generate billing and process payments',
    component: 'BillingPayment',
    roles: ['Accountant', 'ProcurementMgr', 'Admin'],
    status: 'paid'
  }
}

// Valid workflow transitions
export const WORKFLOW_TRANSITIONS: Record<string, string[]> = {
  requisition: ['approval'],
  approval: ['procurement', 'requisition'], // Can reject back to requisition
  procurement: ['confirmation'],
  confirmation: ['shipping'],
  shipping: ['receiving'],
  receiving: ['storage'],
  storage: ['acceptance'],
  acceptance: ['inventory'],
  inventory: ['accounting'],
  accounting: [] // Terminal state
}

export const useWorkflowStore = defineStore('workflow', () => {
  // State
  const currentStep = ref<string>('requisition')
  const workflowData = ref<WorkflowData>({})
  const isTransitioning = ref(false)
  const transitionHistory = ref<WorkflowTransition[]>([])
  const errors = ref<string[]>([])

  // Getters
  const getCurrentStep = computed(() => WORKFLOW_STEPS[currentStep.value])
  
  const getNextSteps = computed(() => {
    return WORKFLOW_TRANSITIONS[currentStep.value]?.map(stepId => WORKFLOW_STEPS[stepId]) || []
  })
  
  const canTransitionTo = computed(() => (targetStep: string) => {
    return WORKFLOW_TRANSITIONS[currentStep.value]?.includes(targetStep) || false
  })
  
  const isStepCompleted = computed(() => (stepId: string) => {
    return transitionHistory.value.some(transition => transition.toStep === stepId && transition.success)
  })
  
  const getStepProgress = computed(() => {
    const steps = Object.keys(WORKFLOW_STEPS)
    const currentIndex = steps.indexOf(currentStep.value)
    return {
      current: currentIndex + 1,
      total: steps.length,
      percentage: Math.round(((currentIndex + 1) / steps.length) * 100)
    }
  })

  // Actions
  const initializeWorkflow = (initialData: Partial<WorkflowData> = {}) => {
    currentStep.value = 'requisition'
    workflowData.value = {
      requisitionId: null,
      purchaseOrderId: null,
      items: [],
      supplier: null,
      project: null,
      totalAmount: 0,
      status: 'draft',
      createdBy: null,
      createdAt: new Date().toISOString(),
      ...initialData
    }
    transitionHistory.value = []
    errors.value = []
  }

  const validateTransition = async (fromStep: string, toStep: string): Promise<boolean> => {
    // Clear previous errors
    errors.value = []
    
    // Check if transition is allowed
    if (!canTransitionTo.value(toStep)) {
      errors.value.push(`Cannot transition from ${fromStep} to ${toStep}`)
      return false
    }

    // Step-specific validation
    switch (toStep) {
      case 'approval':
        if (!workflowData.value.items || workflowData.value.items.length === 0) {
          errors.value.push('Requisition must have at least one item')
          return false
        }
        break
      
      case 'procurement':
        if (!workflowData.value.items?.every(item => item.approved)) {
          errors.value.push('All items must be approved before creating purchase orders')
          return false
        }
        break
      
      case 'confirmation':
        if (!workflowData.value.purchaseOrderId) {
          errors.value.push('Purchase order must be created before confirmation')
          return false
        }
        break
      
      case 'shipping':
        if (workflowData.value.status !== 'confirmed') {
          errors.value.push('Purchase order must be confirmed before shipping')
          return false
        }
        break
      
      case 'receiving':
        if (!workflowData.value.trackingInfo) {
          errors.value.push('Shipping information required before receiving')
          return false
        }
        break
      
      case 'storage':
        if (!workflowData.value.receivedItems?.length) {
          errors.value.push('Items must be received before storage assignment')
          return false
        }
        break
      
      case 'acceptance':
        if (!workflowData.value.storageAssignments?.length) {
          errors.value.push('Items must be stored before acceptance')
          return false
        }
        break
      
      case 'inventory':
        if (!workflowData.value.acceptedItems?.length) {
          errors.value.push('Items must be accepted before inventory management')
          return false
        }
        break
      
      case 'accounting':
        if (!workflowData.value.inventoryRecords?.length) {
          errors.value.push('Inventory records required before billing')
          return false
        }
        break
    }

    return true
  }

  const transitionTo = async (targetStep: string, data: Partial<WorkflowData> = {}): Promise<boolean> => {
    const fromStep = currentStep.value
    
    // Validate transition
    const isValid = await validateTransition(fromStep, targetStep)
    if (!isValid) {
      return false
    }

    isTransitioning.value = true
    
    try {
      // Update workflow data
      workflowData.value = {
        ...workflowData.value,
        ...data,
        status: WORKFLOW_STEPS[targetStep].status,
        updatedAt: new Date().toISOString()
      }

      // Record transition
      const transition: WorkflowTransition = {
        fromStep,
        toStep: targetStep,
        timestamp: new Date().toISOString(),
        data: { ...data },
        success: true
      }
      
      transitionHistory.value.push(transition)
      
      // Update current step
      currentStep.value = targetStep
      
      // Emit analytics event
      window.dispatchEvent(new CustomEvent('workflow-transition', {
        detail: { fromStep, toStep: targetStep, data }
      }))
      
      return true
    } catch (error) {
      // Record failed transition
      const failedTransition: WorkflowTransition = {
        fromStep,
        toStep: targetStep,
        timestamp: new Date().toISOString(),
        data: { ...data },
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }
      
      transitionHistory.value.push(failedTransition)
      errors.value.push(`Failed to transition to ${targetStep}: ${error}`)
      
      return false
    } finally {
      isTransitioning.value = false
    }
  }

  const progressToNext = async (data: Partial<WorkflowData> = {}): Promise<boolean> => {
    const nextSteps = getNextSteps.value
    if (nextSteps.length === 0) {
      errors.value.push('No next step available')
      return false
    }
    
    // If multiple next steps, use the first one by default
    // In practice, you might want to let the user choose
    const nextStep = nextSteps[0].id
    return await transitionTo(nextStep, data)
  }

  const goBack = async (): Promise<boolean> => {
    // Find valid previous steps that can transition to current step
    const possiblePrevious = Object.entries(WORKFLOW_TRANSITIONS)
      .filter(([_, transitions]) => transitions.includes(currentStep.value))
      .map(([step, _]) => step)
    
    if (possiblePrevious.length === 0) {
      errors.value.push('Cannot go back from current step')
      return false
    }
    
    // Go to the most recent previous step
    const previousStep = possiblePrevious[possiblePrevious.length - 1]
    return await transitionTo(previousStep)
  }

  const jumpToStep = async (targetStep: string, data: Partial<WorkflowData> = {}): Promise<boolean> => {
    // Allow jumping to any step if user has proper permissions
    // This is useful for admin users or handling edge cases
    if (!WORKFLOW_STEPS[targetStep]) {
      errors.value.push(`Invalid step: ${targetStep}`)
      return false
    }
    
    currentStep.value = targetStep
    workflowData.value = {
      ...workflowData.value,
      ...data,
      status: WORKFLOW_STEPS[targetStep].status,
      updatedAt: new Date().toISOString()
    }
    
    return true
  }

  const resetWorkflow = () => {
    initializeWorkflow()
  }

  const getWorkflowSummary = computed(() => ({
    currentStep: getCurrentStep.value,
    progress: getStepProgress.value,
    data: workflowData.value,
    history: transitionHistory.value,
    errors: errors.value,
    isTransitioning: isTransitioning.value
  }))

  return {
    // State
    currentStep,
    workflowData,
    isTransitioning,
    transitionHistory,
    errors,
    
    // Getters
    getCurrentStep,
    getNextSteps,
    canTransitionTo,
    isStepCompleted,
    getStepProgress,
    getWorkflowSummary,
    
    // Actions
    initializeWorkflow,
    validateTransition,
    transitionTo,
    progressToNext,
    goBack,
    jumpToStep,
    resetWorkflow
  }
})