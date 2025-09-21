<template>
  <div class="projects-list">
    <div class="page-header">
      <h1>專案管理</h1>
      <el-button type="primary" icon="Plus" @click="handleCreate">新增專案</el-button>
    </div>

    <div class="filter-section">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="專案狀態">
          <el-select 
            v-model="filters.status" 
            placeholder="全部狀態" 
            clearable
            style="width: 150px"
          >
            <el-option label="進行中" value="ongoing" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜尋">
          <el-input 
            v-model="filters.search" 
            placeholder="專案名稱/客戶名稱"
            clearable
            style="width: 250px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="handleSearch">查詢</el-button>
          <el-button icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-card>
      <el-table :data="projects" v-loading="loading" stripe>
        <el-table-column prop="project_code" label="專案代碼" width="120" />
        <el-table-column prop="project_name" label="專案名稱" min-width="200">
          <template #default="scope">
            <el-link type="primary" @click="viewDetail(scope.row)">
              {{ scope.row.project_name }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="project_status" label="狀態" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.project_status === 'ongoing' ? 'success' : 'info'">
              {{ scope.row.project_status === 'ongoing' ? '進行中' : '已完成' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="budget" label="預算" width="150" align="right">
          <template #default="scope">
            <span v-if="scope.row.budget">NT$ {{ formatAmount(scope.row.budget) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_expenditure" label="已花費" width="150" align="right">
          <template #default="scope">
            NT$ {{ formatAmount(scope.row.total_expenditure || 0) }}
          </template>
        </el-table-column>
        <el-table-column label="預算使用率" width="150">
          <template #default="scope">
            <el-progress 
              v-if="scope.row.budget && scope.row.budget > 0"
              :percentage="Math.min(100, Math.round((scope.row.total_expenditure || 0) / scope.row.budget * 100))"
              :status="getProgressStatus(scope.row)"
            />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="start_date" label="開始日期" width="120">
          <template #default="scope">
            {{ formatDate(scope.row.start_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="manager" label="負責人" width="100">
          <template #default="scope">
            {{ scope.row.manager?.chinese_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="viewDetail(scope.row)">查看</el-button>
            <el-button size="small" @click="handleEdit(scope.row)">編輯</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="fetchProjects"
          @current-change="fetchProjects"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { projectsApi } from '@/api/projects'

const router = useRouter()
const loading = ref(false)
const projects = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const filters = reactive({
  status: '',
  search: ''
})

const fetchProjects = async () => {
  loading.value = true
  try {
    const response = await projectsApi.getProjects({
      page: currentPage.value,
      page_size: pageSize.value,
      status: filters.status as any,
      search: filters.search
    })
    
    const data = response.data || response
    projects.value = data.data || data.items || []
    total.value = data.pagination?.total || data.total || 0
  } catch (error) {
    console.error('Failed to fetch projects:', error)
    ElMessage.error('載入專案列表失敗')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchProjects()
}

const handleReset = () => {
  filters.status = ''
  filters.search = ''
  currentPage.value = 1
  fetchProjects()
}

const handleCreate = () => {
  router.push('/projects/create')
}

const viewDetail = (project: any) => {
  router.push(`/projects/${project.project_id}`)
}

const handleEdit = (project: any) => {
  router.push(`/projects/${project.project_id}/edit`)
}

const formatAmount = (amount: number) => {
  return amount.toLocaleString('zh-TW')
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-TW')
}

const getProgressStatus = (project: any) => {
  const usage = (project.total_expenditure || 0) / project.budget * 100
  if (usage >= 90) return 'exception'
  if (usage >= 70) return 'warning'
  return 'success'
}

onMounted(() => {
  fetchProjects()
})
</script>

<style scoped>
.projects-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 24px;
  margin: 0;
  color: #303133;
}

.filter-section {
  background: white;
  padding: 20px;
  margin-bottom: 20px;
  border-radius: 8px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>