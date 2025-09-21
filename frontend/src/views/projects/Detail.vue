<template>
  <div class="project-detail">
    <div class="page-header">
      <div class="header-left">
        <el-button icon="ArrowLeft" circle @click="$router.back()" />
        <h1>專案詳情</h1>
      </div>
      <div class="header-actions">
        <el-button type="primary" icon="Edit" @click="handleEdit">編輯</el-button>
      </div>
    </div>

    <div v-loading="loading" class="content-wrapper">
      <!-- 基本資訊 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>基本資訊</span>
            <el-tag :type="project.project_status === 'ongoing' ? 'success' : 'info'">
              {{ project.project_status === 'ongoing' ? '進行中' : '已完成' }}
            </el-tag>
          </div>
        </template>
        
        <el-descriptions :column="2" border>
          <el-descriptions-item label="專案代碼">
            {{ project.project_code || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="專案名稱">
            {{ project.project_name }}
          </el-descriptions-item>
          <el-descriptions-item label="專案描述" :span="2">
            {{ project.description || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="開始日期">
            {{ formatDate(project.start_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="結束日期">
            {{ formatDate(project.end_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="專案負責人">
            {{ project.manager?.chinese_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="負責人部門">
            {{ project.manager?.department || '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 預算資訊 -->
      <el-card class="budget-card">
        <template #header>
          <span>預算與花費</span>
        </template>
        
        <div class="budget-overview">
          <div class="budget-item">
            <div class="label">專案預算</div>
            <div class="value">NT$ {{ formatAmount(project.budget || 0) }}</div>
          </div>
          <div class="budget-item">
            <div class="label">已花費金額</div>
            <div class="value" :class="{ 'text-danger': isOverBudget }">
              NT$ {{ formatAmount(actualExpenditure) }}
            </div>
          </div>
          <div class="budget-item">
            <div class="label">剩餘預算</div>
            <div class="value" :class="{ 'text-danger': budgetRemaining < 0 }">
              NT$ {{ formatAmount(budgetRemaining) }}
            </div>
          </div>
          <div class="budget-item">
            <div class="label">預算使用率</div>
            <div class="value">
              <el-progress 
                :percentage="budgetUsagePercent"
                :status="progressStatus"
                :stroke-width="20"
              />
            </div>
          </div>
        </div>
      </el-card>

      <!-- 花費統計 -->
      <el-card class="statistics-card">
        <template #header>
          <span>花費統計</span>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-label">過去一週花費</div>
              <div class="stat-value">NT$ {{ formatAmount(statistics.week_total || 0) }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-label">過去一個月花費</div>
              <div class="stat-value">NT$ {{ formatAmount(statistics.month_total || 0) }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-label">專案總花費</div>
              <div class="stat-value">NT$ {{ formatAmount(statistics.all_time_total || 0) }}</div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 客戶資訊 -->
      <el-card class="customer-card" v-if="hasCustomerInfo">
        <template #header>
          <span>客戶資訊</span>
        </template>
        
        <el-descriptions :column="2" border>
          <el-descriptions-item label="客戶名稱">
            {{ project.customer_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="客戶部門">
            {{ project.customer_department || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="聯絡人">
            {{ project.customer_contact || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="聯絡電話">
            {{ project.customer_phone || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="客戶地址" :span="2">
            {{ project.customer_address || '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 相關請購單 -->
      <el-card class="requisitions-card">
        <template #header>
          <div class="card-header">
            <span>相關請購單</span>
            <el-button size="small" icon="Refresh" @click="fetchRelatedRequisitions">
              重新整理
            </el-button>
          </div>
        </template>
        
        <el-table :data="relatedRequisitions" v-loading="requisitionsLoading">
          <el-table-column prop="request_order_no" label="請購單號" width="150" />
          <el-table-column prop="submit_date" label="提交日期" width="120">
            <template #default="scope">
              {{ formatDate(scope.row.submit_date) }}
            </template>
          </el-table-column>
          <el-table-column prop="requester_name" label="請購人" width="100" />
          <el-table-column prop="total_amount" label="金額" width="120" align="right">
            <template #default="scope">
              NT$ {{ formatAmount(scope.row.total_amount || 0) }}
            </template>
          </el-table-column>
          <el-table-column prop="order_status" label="狀態" width="100">
            <template #default="scope">
              <el-tag size="small" :type="getStatusType(scope.row.order_status)">
                {{ getStatusText(scope.row.order_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template #default="scope">
              <el-button 
                size="small" 
                type="primary" 
                link
                @click="viewRequisition(scope.row)"
              >
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <el-empty v-if="!relatedRequisitions.length && !requisitionsLoading" description="暫無相關請購單" />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { projectsApi } from '@/api/projects'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const requisitionsLoading = ref(false)
const project = ref<any>({})
const statistics = ref<any>({})
const relatedRequisitions = ref<any[]>([])

const hasCustomerInfo = computed(() => {
  return project.value.customer_name ||
         project.value.customer_department ||
         project.value.customer_contact ||
         project.value.customer_phone ||
         project.value.customer_address
})

const actualExpenditure = computed(() => {
  return relatedRequisitions.value.reduce((sum, req) => sum + (req.total_amount || 0), 0)
})

const budgetRemaining = computed(() => {
  const budget = project.value.budget || 0
  return budget - actualExpenditure.value
})

const budgetUsagePercent = computed(() => {
  const budget = project.value.budget || 0
  if (!budget) return 0
  return Math.min(100, Math.round((actualExpenditure.value / budget) * 100))
})

const isOverBudget = computed(() => {
  return budgetRemaining.value < 0
})

const progressStatus = computed(() => {
  const percent = budgetUsagePercent.value
  if (percent >= 100) return 'exception'
  if (percent >= 90) return 'warning'
  return 'success'
})

const fetchProject = async () => {
  loading.value = true
  try {
    const projectId = route.params.id as string
    const data = await projectsApi.getProject(projectId)
    project.value = data
    
    // 統計資料將在獲取請購單後計算
  } catch (error) {
    console.error('Failed to fetch project:', error)
    ElMessage.error('載入專案資料失敗')
    router.push('/projects')
  } finally {
    loading.value = false
  }
}

const fetchStatistics = async () => {
  try {
    const projectId = route.params.id as string
    // 計算實際統計資料
    const totalAmount = relatedRequisitions.value.reduce((sum, req) => sum + (req.total_amount || 0), 0)
    statistics.value = {
      week_total: totalAmount, // 暫時使用總金額，實際應該根據日期篩選
      month_total: totalAmount, // 暫時使用總金額，實際應該根據日期篩選
      all_time_total: totalAmount
    }
  } catch (error) {
    console.error('Failed to fetch statistics:', error)
  }
}

const fetchRelatedRequisitions = async () => {
  requisitionsLoading.value = true
  try {
    // 從API獲取相關請購單
    const projectId = route.params.id as string
    const data = await projectsApi.getProjectRequisitions(projectId)
    // 將 API 返回的字段映射到前端需要的格式
    relatedRequisitions.value = data.map(item => ({
      request_order_no: item.requisition_no,
      submit_date: item.requisition_date,
      requester_name: item.applicant_name,
      total_amount: item.total_amount,
      order_status: item.status,
      ...item
    }))
  } catch (error) {
    console.error('Failed to fetch requisitions:', error)
    ElMessage.error('獲取請購單失敗')
  } finally {
    requisitionsLoading.value = false
  }
}

const handleEdit = () => {
  router.push(`/projects/${route.params.id}/edit`)
}

const viewRequisition = (requisition: any) => {
  router.push(`/requisitions/${requisition.request_order_no}`)
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-TW')
}

const formatAmount = (amount: number) => {
  return amount.toLocaleString('zh-TW')
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'draft': '草稿',
    'pending': '待審核',
    'reviewed': '已審核',
    'approved': '已核准',
    'rejected': '已拒絕',
    'cancelled': '已取消',
    'completed': '已完成'
  }
  return statusMap[status] || status
}

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'draft': 'info',
    'pending': 'warning',
    'reviewed': 'primary',
    'approved': 'success',
    'rejected': 'danger',
    'cancelled': 'info',
    'completed': 'success'
  }
  return typeMap[status] || 'info'
}

onMounted(async () => {
  await fetchProject()
  await fetchRelatedRequisitions()
  // 在獲取請購單後計算統計
  fetchStatistics()
})
</script>

<style scoped>
.project-detail {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-left h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.budget-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.budget-item {
  text-align: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.budget-item .label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 10px;
}

.budget-item .value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.text-danger {
  color: #f56c6c !important;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
}

@media (max-width: 768px) {
  .budget-overview {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>