<template>
  <div class="projects-container">
    <PageHeader 
      title="專案管理" 
      subtitle="Project Management"
      @add="showCreateDialog = true"
    >
      <template #actions>
        <el-button 
          type="primary" 
          @click="showCreateDialog = true"
          :icon="Plus"
        >
          新增專案
        </el-button>
      </template>
    </PageHeader>

    <!-- Filters -->
    <el-card class="filter-card">
      <el-form :model="filters" inline class="filter-form">
        <el-form-item label="專案狀態">
          <el-select v-model="filters.status" placeholder="選擇狀態" clearable>
            <el-option label="活躍" value="active" />
            <el-option label="非活躍" value="inactive" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="專案經理">
          <el-select v-model="filters.manager_id" placeholder="選擇經理" clearable>
            <el-option 
              v-for="manager in managers" 
              :key="manager.id"
              :label="manager.chinese_name"
              :value="manager.id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="搜尋">
          <el-input
            v-model="filters.search"
            placeholder="專案名稱或代碼"
            :prefix-icon="Search"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="loadProjects" :icon="Search">
            搜尋
          </el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Project Statistics -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <StatCard
          title="總專案數"
          :value="stats.totalProjects"
          icon="Folder"
          color="#409EFF"
        />
      </el-col>
      <el-col :span="6">
        <StatCard
          title="活躍專案"
          :value="stats.activeProjects"
          icon="Flag"
          color="#67C23A"
        />
      </el-col>
      <el-col :span="6">
        <StatCard
          title="總預算"
          :value="formatCurrency(stats.totalBudget)"
          icon="Money"
          color="#E6A23C"
        />
      </el-col>
      <el-col :span="6">
        <StatCard
          title="已支出"
          :value="formatCurrency(stats.totalExpenditure)"
          icon="CreditCard"
          color="#F56C6C"
        />
      </el-col>
    </el-row>

    <!-- Projects Table -->
    <el-card class="table-card">
      <DataTable
        :data="projects"
        :columns="columns"
        :loading="loading"
        :pagination="pagination"
        @page-change="handlePageChange"
        @sort-change="handleSortChange"
      >
        <template #status="{ row }">
          <StatusTag :status="getProjectStatus(row)" />
        </template>
        
        <template #budget="{ row }">
          <div class="budget-info">
            <div class="budget-amount">{{ formatCurrency(row.budget) }}</div>
            <div class="budget-usage">
              <el-progress
                :percentage="row.budget_utilization_percent"
                :status="getBudgetProgressStatus(row.budget_utilization_percent)"
                :show-text="false"
                :stroke-width="6"
              />
              <span class="usage-text">
                已使用: {{ formatCurrency(row.total_expenditure) }}
              </span>
            </div>
          </div>
        </template>
        
        <template #actions="{ row }">
          <el-button-group>
            <el-button 
              size="small" 
              type="primary" 
              @click="viewProject(row)"
              :icon="View"
            >
              檢視
            </el-button>
            <el-button 
              size="small" 
              @click="editProject(row)"
              :icon="Edit"
            >
              編輯
            </el-button>
            <el-button 
              size="small" 
              type="info" 
              @click="viewExpenditure(row)"
              :icon="Money"
            >
              支出
            </el-button>
          </el-button-group>
        </template>
      </DataTable>
    </el-card>

    <!-- Create/Edit Project Dialog -->
    <FormDialog
      v-model="showCreateDialog"
      :title="isEditing ? '編輯專案' : '新增專案'"
      @confirm="handleSaveProject"
    >
      <el-form
        ref="projectFormRef"
        :model="projectForm"
        :rules="projectRules"
        label-width="100px"
      >
        <el-form-item label="專案代碼" prop="project_code">
          <el-input
            v-model="projectForm.project_code"
            :disabled="isEditing"
            placeholder="輸入專案代碼"
          />
        </el-form-item>
        
        <el-form-item label="專案名稱" prop="project_name">
          <el-input
            v-model="projectForm.project_name"
            placeholder="輸入專案名稱"
          />
        </el-form-item>
        
        <el-form-item label="專案描述">
          <el-input
            v-model="projectForm.project_description"
            type="textarea"
            :rows="3"
            placeholder="輸入專案描述"
          />
        </el-form-item>
        
        <el-form-item label="專案經理">
          <el-select v-model="projectForm.manager_id" placeholder="選擇專案經理">
            <el-option 
              v-for="manager in managers" 
              :key="manager.id"
              :label="manager.chinese_name"
              :value="manager.id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="預算">
          <el-input-number
            v-model="projectForm.budget"
            :min="0"
            :precision="2"
            placeholder="輸入預算金額"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="開始日期">
              <el-date-picker
                v-model="projectForm.start_date"
                type="date"
                placeholder="選擇開始日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="結束日期">
              <el-date-picker
                v-model="projectForm.end_date"
                type="date"
                placeholder="選擇結束日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="狀態">
          <el-switch
            v-model="projectForm.is_active"
            active-text="活躍"
            inactive-text="非活躍"
          />
        </el-form-item>
      </el-form>
    </FormDialog>

    <!-- Project Details Dialog -->
    <el-dialog
      v-model="showDetailsDialog"
      :title="selectedProject?.project_name"
      width="80%"
      top="5vh"
    >
      <ProjectDetails
        v-if="selectedProject"
        :project="selectedProject"
        @expenditure-view="viewExpenditure"
      />
    </el-dialog>

    <!-- Expenditure Dialog -->
    <el-dialog
      v-model="showExpenditureDialog"
      title="專案支出記錄"
      width="70%"
      top="10vh"
    >
      <ProjectExpenditure
        v-if="selectedProject"
        :project="selectedProject"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, View, Edit, Money } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import DataTable from '@/components/DataTable.vue'
import StatCard from '@/components/StatCard.vue'
import StatusTag from '@/components/StatusTag.vue'
import FormDialog from '@/components/FormDialog.vue'
import ProjectDetails from './ProjectDetails.vue'
import ProjectExpenditure from './ProjectExpenditure.vue'
import { useProjectStore } from '@/stores/projectStore'
import { useAuthStore } from '@/stores/auth'
import type { Project } from '@/types/project'

// Store instances
const projectStore = useProjectStore()
const authStore = useAuthStore()

// Reactive data
const loading = ref(false)
const showCreateDialog = ref(false)
const showDetailsDialog = ref(false)
const showExpenditureDialog = ref(false)
const isEditing = ref(false)
const selectedProject = ref<Project | null>(null)
const projectFormRef = ref()

// Filters
const filters = reactive({
  status: '',
  manager_id: null,
  search: '',
  page: 1,
  page_size: 20
})

// Project form
const projectForm = reactive({
  project_code: '',
  project_name: '',
  project_description: '',
  manager_id: null,
  budget: null,
  start_date: null,
  end_date: null,
  is_active: true
})

// Form validation rules
const projectRules = {
  project_code: [
    { required: true, message: '請輸入專案代碼', trigger: 'blur' },
    { min: 2, max: 20, message: '專案代碼長度在 2 到 20 個字符', trigger: 'blur' }
  ],
  project_name: [
    { required: true, message: '請輸入專案名稱', trigger: 'blur' },
    { min: 2, max: 200, message: '專案名稱長度在 2 到 200 個字符', trigger: 'blur' }
  ]
}

// Table columns
const columns = [
  { prop: 'project_code', label: '專案代碼', width: 120, sortable: true },
  { prop: 'project_name', label: '專案名稱', minWidth: 200, sortable: true },
  { prop: 'manager.name', label: '專案經理', width: 120 },
  { prop: 'budget', label: '預算/支出', width: 200, slot: 'budget' },
  { prop: 'start_date', label: '開始日期', width: 120, sortable: true },
  { prop: 'end_date', label: '結束日期', width: 120, sortable: true },
  { prop: 'is_active', label: '狀態', width: 100, slot: 'status' },
  { prop: 'actions', label: '操作', width: 250, slot: 'actions', fixed: 'right' }
]

// Computed properties
const projects = computed(() => projectStore.projects)
const pagination = computed(() => projectStore.pagination)
const managers = computed(() => authStore.managers || [])

const stats = computed(() => ({
  totalProjects: projects.value.length,
  activeProjects: projects.value.filter(p => p.is_active).length,
  totalBudget: projects.value.reduce((sum, p) => sum + (p.budget || 0), 0),
  totalExpenditure: projects.value.reduce((sum, p) => sum + (p.total_expenditure || 0), 0)
}))

// Methods
const loadProjects = async () => {
  loading.value = true
  try {
    await projectStore.fetchProjects(filters)
  } catch (error) {
    ElMessage.error('載入專案列表失敗')
  } finally {
    loading.value = false
  }
}

const loadManagers = async () => {
  try {
    if (authStore.fetchManagers) {
      await authStore.fetchManagers()
    }
  } catch (error) {
    console.error('載入經理列表失敗:', error)
  }
}

const resetFilters = () => {
  Object.assign(filters, {
    status: '',
    manager_id: null,
    search: '',
    page: 1,
    page_size: 20
  })
  loadProjects()
}

const handlePageChange = (page: number) => {
  filters.page = page
  loadProjects()
}

const handleSortChange = (sort: any) => {
  // Handle sorting
  loadProjects()
}

const viewProject = (project: Project) => {
  selectedProject.value = project
  showDetailsDialog.value = true
}

const editProject = (project: Project) => {
  Object.assign(projectForm, {
    ...project,
    start_date: project.start_date ? new Date(project.start_date) : null,
    end_date: project.end_date ? new Date(project.end_date) : null
  })
  isEditing.value = true
  showCreateDialog.value = true
}

const viewExpenditure = (project: Project) => {
  selectedProject.value = project
  showExpenditureDialog.value = true
}

const handleSaveProject = async () => {
  if (!projectFormRef.value) return
  
  try {
    await projectFormRef.value.validate()
    
    const formData = {
      ...projectForm,
      start_date: projectForm.start_date ? formatDate(projectForm.start_date) : null,
      end_date: projectForm.end_date ? formatDate(projectForm.end_date) : null
    }
    
    if (isEditing.value) {
      await projectStore.updateProject(selectedProject.value!.id, formData)
      ElMessage.success('專案更新成功')
    } else {
      await projectStore.createProject(formData)
      ElMessage.success('專案建立成功')
    }
    
    showCreateDialog.value = false
    resetForm()
    loadProjects()
  } catch (error) {
    ElMessage.error(isEditing.value ? '專案更新失敗' : '專案建立失敗')
  }
}

const resetForm = () => {
  Object.assign(projectForm, {
    project_code: '',
    project_name: '',
    project_description: '',
    manager_id: null,
    budget: null,
    start_date: null,
    end_date: null,
    is_active: true
  })
  isEditing.value = false
  selectedProject.value = null
}

const getProjectStatus = (project: Project) => {
  if (!project.is_active) return { text: '非活躍', type: 'info' }
  if (project.end_date && new Date(project.end_date) < new Date()) {
    return { text: '已完成', type: 'success' }
  }
  return { text: '活躍', type: 'success' }
}

const getBudgetProgressStatus = (percentage: number) => {
  if (percentage >= 100) return 'exception'
  if (percentage >= 90) return 'warning'
  return 'success'
}

const formatCurrency = (amount: number | null | undefined) => {
  if (!amount) return 'NT$ 0'
  return `NT$ ${amount.toLocaleString()}`
}

const formatDate = (date: Date) => {
  return date.toISOString().split('T')[0]
}

// Lifecycle
onMounted(() => {
  loadProjects()
  loadManagers()
})
</script>

<style scoped>
.projects-container {
  padding: 20px;
}

.filter-card {
  margin: 20px 0;
}

.filter-form {
  margin-bottom: 0;
}

.stats-row {
  margin: 20px 0;
}

.table-card {
  margin-top: 20px;
}

.budget-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.budget-amount {
  font-weight: bold;
  color: #409EFF;
}

.budget-usage {
  display: flex;
  align-items: center;
  gap: 10px;
}

.usage-text {
  font-size: 12px;
  color: #666;
}

:deep(.el-progress-bar) {
  flex: 1;
}
</style>