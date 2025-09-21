<template>
  <div class="project-details">
    <!-- Project Overview -->
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card title="專案資訊">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="專案代碼">
              <el-tag type="primary">{{ project.project_code }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="專案名稱">
              {{ project.project_name }}
            </el-descriptions-item>
            <el-descriptions-item label="專案經理">
              <div v-if="project.manager">
                <el-avatar size="small" class="mr-2">
                  {{ project.manager.name.charAt(0) }}
                </el-avatar>
                {{ project.manager.name }}
              </div>
              <span v-else class="text-gray-400">未指定</span>
            </el-descriptions-item>
            <el-descriptions-item label="狀態">
              <StatusTag :status="projectStatus" />
            </el-descriptions-item>
            <el-descriptions-item label="開始日期">
              {{ formatDate(project.start_date) }}
            </el-descriptions-item>
            <el-descriptions-item label="結束日期">
              {{ formatDate(project.end_date) }}
            </el-descriptions-item>
            <el-descriptions-item label="建立時間">
              {{ formatDateTime(project.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="更新時間">
              {{ formatDateTime(project.updated_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="專案描述" :span="2">
              <div class="project-description">
                {{ project.project_description || '無描述' }}
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card title="預算概況">
          <div class="budget-overview">
            <div class="budget-item">
              <div class="budget-label">總預算</div>
              <div class="budget-value primary">
                {{ formatCurrency(project.budget) }}
              </div>
            </div>
            
            <div class="budget-item">
              <div class="budget-label">已支出</div>
              <div class="budget-value danger">
                {{ formatCurrency(project.total_expenditure) }}
              </div>
            </div>
            
            <div class="budget-item">
              <div class="budget-label">剩餘預算</div>
              <div class="budget-value" :class="remainingBudgetClass">
                {{ formatCurrency(project.remaining_budget) }}
              </div>
            </div>
            
            <div class="budget-progress">
              <div class="budget-label">預算使用率</div>
              <el-progress
                :percentage="project.budget_utilization_percent || 0"
                :status="getBudgetProgressStatus(project.budget_utilization_percent)"
                :stroke-width="12"
              />
              <div class="progress-text">
                {{ (project.budget_utilization_percent || 0).toFixed(1) }}%
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Expenditure Breakdown -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>供應商支出分佈</span>
              <el-button 
                size="small" 
                type="primary" 
                @click="$emit('expenditure-view', project)"
              >
                檢視詳細
              </el-button>
            </div>
          </template>
          
          <div v-if="project.expenditure_breakdown?.length" class="expenditure-list">
            <div 
              v-for="expenditure in project.expenditure_breakdown" 
              :key="expenditure.supplier_id"
              class="expenditure-item"
            >
              <div class="supplier-info">
                <div class="supplier-name">{{ expenditure.supplier_name }}</div>
                <div class="supplier-stats">
                  {{ expenditure.transaction_count }} 筆交易
                </div>
              </div>
              <div class="expenditure-amount">
                {{ formatCurrency(expenditure.total_amount) }}
              </div>
            </div>
          </div>
          <div v-else class="no-data">
            暫無支出記錄
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>近期採購訂單</span>
            </div>
          </template>
          
          <div v-if="project.recent_purchase_orders?.length" class="po-list">
            <div 
              v-for="po in project.recent_purchase_orders" 
              :key="po.id"
              class="po-item"
            >
              <div class="po-info">
                <div class="po-number">{{ po.po_no }}</div>
                <div class="po-supplier">{{ po.supplier_name }}</div>
                <div class="po-date">{{ formatDate(po.created_at) }}</div>
              </div>
              <div class="po-amount">
                <div class="amount">{{ formatCurrency(po.total_amount) }}</div>
                <StatusTag :status="getPOStatus(po.status)" />
              </div>
            </div>
          </div>
          <div v-else class="no-data">
            暫無相關採購訂單
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Project Timeline (if available) -->
    <el-row style="margin-top: 20px;">
      <el-col :span="24">
        <el-card title="專案時程">
          <div class="timeline-container">
            <el-timeline>
              <el-timeline-item
                v-if="project.start_date"
                timestamp="專案開始"
                :placement="timelinePlacement"
              >
                專案於 {{ formatDate(project.start_date) }} 開始
              </el-timeline-item>
              
              <el-timeline-item
                timestamp="專案建立"
                :placement="timelinePlacement"
              >
                專案於 {{ formatDate(project.created_at) }} 建立
              </el-timeline-item>
              
              <el-timeline-item
                v-if="project.updated_at && project.updated_at !== project.created_at"
                timestamp="最後更新"
                :placement="timelinePlacement"
              >
                專案於 {{ formatDate(project.updated_at) }} 更新
              </el-timeline-item>
              
              <el-timeline-item
                v-if="project.end_date"
                timestamp="預計結束"
                :placement="timelinePlacement"
                :type="getTimelineEndType()"
              >
                專案預計於 {{ formatDate(project.end_date) }} 結束
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import StatusTag from '@/components/StatusTag.vue'
import type { Project } from '@/types/project'

interface Props {
  project: Project
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'expenditure-view': [project: Project]
}>()

// Computed properties
const projectStatus = computed(() => {
  if (!props.project.is_active) return { text: '非活躍', type: 'info' }
  if (props.project.end_date && new Date(props.project.end_date) < new Date()) {
    return { text: '已完成', type: 'success' }
  }
  return { text: '活躍', type: 'success' }
})

const remainingBudgetClass = computed(() => {
  const remaining = props.project.remaining_budget || 0
  if (remaining < 0) return 'danger'
  if (remaining < (props.project.budget || 0) * 0.1) return 'warning'
  return 'success'
})

const timelinePlacement = computed(() => 'top')

// Methods
const getBudgetProgressStatus = (percentage: number | null | undefined) => {
  const percent = percentage || 0
  if (percent >= 100) return 'exception'
  if (percent >= 90) return 'warning'
  return 'success'
}

const getPOStatus = (status: string) => {
  const statusMap: Record<string, any> = {
    'draft': { text: '草稿', type: 'info' },
    'confirmed': { text: '已確認', type: 'primary' },
    'shipped': { text: '已發貨', type: 'warning' },
    'received': { text: '已收貨', type: 'success' },
    'cancelled': { text: '已取消', type: 'danger' }
  }
  return statusMap[status] || { text: status, type: 'default' }
}

const getTimelineEndType = () => {
  if (!props.project.end_date) return 'primary'
  const endDate = new Date(props.project.end_date)
  const now = new Date()
  if (endDate < now) return 'success'
  
  const daysUntilEnd = Math.ceil((endDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
  if (daysUntilEnd <= 30) return 'warning'
  return 'primary'
}

const formatCurrency = (amount: number | null | undefined) => {
  if (!amount) return 'NT$ 0'
  return `NT$ ${amount.toLocaleString()}`
}

const formatDate = (dateString: string | null | undefined) => {
  if (!dateString) return '未設定'
  return new Date(dateString).toLocaleDateString('zh-TW')
}

const formatDateTime = (dateString: string | null | undefined) => {
  if (!dateString) return '未設定'
  return new Date(dateString).toLocaleString('zh-TW')
}
</script>

<style scoped>
.project-details {
  padding: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.budget-overview {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.budget-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.budget-label {
  font-size: 14px;
  color: #666;
}

.budget-value {
  font-size: 16px;
  font-weight: bold;
}

.budget-value.primary {
  color: #409EFF;
}

.budget-value.success {
  color: #67C23A;
}

.budget-value.warning {
  color: #E6A23C;
}

.budget-value.danger {
  color: #F56C6C;
}

.budget-progress {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 15px 0;
}

.progress-text {
  text-align: center;
  font-weight: bold;
  color: #409EFF;
}

.expenditure-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.expenditure-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409EFF;
}

.supplier-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.supplier-name {
  font-weight: bold;
  color: #333;
}

.supplier-stats {
  font-size: 12px;
  color: #666;
}

.expenditure-amount {
  font-size: 16px;
  font-weight: bold;
  color: #F56C6C;
}

.po-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.po-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 6px;
  transition: all 0.3s;
}

.po-item:hover {
  background: #f8f9fa;
  border-color: #409EFF;
}

.po-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.po-number {
  font-weight: bold;
  color: #409EFF;
}

.po-supplier {
  font-size: 13px;
  color: #666;
}

.po-date {
  font-size: 12px;
  color: #999;
}

.po-amount {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 5px;
}

.amount {
  font-weight: bold;
  color: #333;
}

.no-data {
  text-align: center;
  color: #999;
  padding: 40px 0;
}

.project-description {
  line-height: 1.6;
  color: #666;
}

.timeline-container {
  padding: 20px 0;
}

.mr-2 {
  margin-right: 8px;
}

.text-gray-400 {
  color: #999;
}
</style>