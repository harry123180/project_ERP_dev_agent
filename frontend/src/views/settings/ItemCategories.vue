<template>
  <div class="item-categories-management">
    <div class="page-header">
      <h1>物品種類管理</h1>
      <div class="actions">
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          新增種類
        </el-button>
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          重新整理
        </el-button>
      </div>
    </div>

    <!-- 統計卡片 -->
    <div class="stats-cards">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-card>
            <el-statistic title="總種類數" :value="totalCategories" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card>
            <el-statistic title="啟用中" :value="activeCategories" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card>
            <el-statistic title="停用中" :value="inactiveCategories" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card>
            <el-statistic title="使用中" :value="usedCategories" />
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 資料表格 -->
    <el-card class="table-card">
      <el-table
        :data="categories"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="category_code" label="種類代碼" width="120" />
        <el-table-column prop="category_name" label="種類名稱" width="200" />
        <el-table-column prop="is_active" label="狀態" width="100">
          <template #default="scope">
            <el-tag
              :type="scope.row.is_active ? 'success' : 'danger'"
              disable-transitions
            >
              {{ scope.row.is_active ? '啟用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="建立時間" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新時間" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="scope">
            <el-button
              link
              type="primary"
              size="small"
              @click="showEditDialog(scope.row)"
            >
              編輯
            </el-button>
            <el-button
              link
              :type="scope.row.is_active ? 'warning' : 'success'"
              size="small"
              @click="toggleStatus(scope.row)"
            >
              {{ scope.row.is_active ? '停用' : '啟用' }}
            </el-button>
            <el-button
              link
              type="danger"
              size="small"
              @click="deleteCategory(scope.row)"
            >
              刪除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/編輯對話框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '編輯物品種類' : '新增物品種類'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="種類代碼" prop="category_code">
          <el-input
            v-model="form.category_code"
            placeholder="請輸入種類代碼"
            :disabled="isEdit"
          />
        </el-form-item>
        <el-form-item label="種類名稱" prop="category_name">
          <el-input
            v-model="form.category_name"
            placeholder="請輸入種類名稱"
          />
        </el-form-item>
        <el-form-item label="啟用狀態">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">確定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import request from '@/api'

interface ItemCategory {
  category_code: string
  category_name: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// 響應式變數
const loading = ref(false)
const categories = ref<ItemCategory[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()

// 表單資料
const form = ref({
  category_code: '',
  category_name: '',
  is_active: true
})

// 表單驗證規則
const rules = {
  category_code: [
    { required: true, message: '請輸入種類代碼', trigger: 'blur' },
    { min: 1, max: 20, message: '長度在 1 到 20 個字元', trigger: 'blur' }
  ],
  category_name: [
    { required: true, message: '請輸入種類名稱', trigger: 'blur' },
    { min: 1, max: 50, message: '長度在 1 到 50 個字元', trigger: 'blur' }
  ]
}

// 計算屬性
const totalCategories = computed(() => categories.value.length)
const activeCategories = computed(() => categories.value.filter(c => c.is_active).length)
const inactiveCategories = computed(() => categories.value.filter(c => !c.is_active).length)
const usedCategories = computed(() => 0) // 可以根據實際使用情況更新

// 獲取種類列表
const fetchCategories = async () => {
  loading.value = true
  try {
    const response = await request.get('/item-categories')
    if (response.data.success) {
      categories.value = response.data.data
    }
  } catch (error) {
    console.error('獲取種類列表失敗:', error)
    ElMessage.error('獲取種類列表失敗')
  } finally {
    loading.value = false
  }
}

// 顯示新增對話框
const showAddDialog = () => {
  isEdit.value = false
  form.value = {
    category_code: '',
    category_name: '',
    is_active: true
  }
  dialogVisible.value = true
}

// 顯示編輯對話框
const showEditDialog = (row: ItemCategory) => {
  isEdit.value = true
  form.value = {
    category_code: row.category_code,
    category_name: row.category_name,
    is_active: row.is_active
  }
  dialogVisible.value = true
}

// 保存（新增或編輯）
const handleSave = async () => {
  try {
    await formRef.value.validate()

    if (isEdit.value) {
      // 編輯
      const response = await request.put(
        `/item-categories/${form.value.category_code}`,
        form.value
      )
      if (response.data.success) {
        ElMessage.success('更新成功')
        dialogVisible.value = false
        await fetchCategories()
      }
    } else {
      // 新增
      const response = await request.post('/item-categories', form.value)
      if (response.data.success) {
        ElMessage.success('新增成功')
        dialogVisible.value = false
        await fetchCategories()
      }
    }
  } catch (error: any) {
    if (error.response?.data?.error) {
      ElMessage.error(error.response.data.error)
    } else {
      ElMessage.error('操作失敗')
    }
  }
}

// 切換狀態
const toggleStatus = async (row: ItemCategory) => {
  try {
    const response = await request.patch(
      `/item-categories/${row.category_code}/toggle-active`
    )
    if (response.data.success) {
      ElMessage.success(response.data.message)
      await fetchCategories()
    }
  } catch (error) {
    ElMessage.error('切換狀態失敗')
  }
}

// 刪除種類
const deleteCategory = async (row: ItemCategory) => {
  try {
    await ElMessageBox.confirm(
      `確定要刪除種類「${row.category_name}」嗎？`,
      '刪除確認',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await request.delete(`/item-categories/${row.category_code}`)
    if (response.data.success) {
      ElMessage.success('刪除成功')
      await fetchCategories()
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      if (error.response?.data?.error) {
        ElMessage.error(error.response.data.error)
      } else {
        ElMessage.error('刪除失敗')
      }
    }
  }
}

// 重新整理
const refreshData = () => {
  fetchCategories()
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-TW')
}

onMounted(() => {
  fetchCategories()
})
</script>

<style scoped>
.item-categories-management {
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
}

.actions {
  display: flex;
  gap: 10px;
}

.stats-cards {
  margin-bottom: 20px;
}

.table-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}
</style>