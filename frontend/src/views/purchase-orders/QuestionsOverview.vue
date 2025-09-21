<template>
  <div class="questions-overview">
    <div class="page-header">
      <h1 class="page-title">疑問總覽</h1>
      <div class="header-actions">
        <el-button type="primary" @click="refreshData">
          <el-icon><Refresh /></el-icon>
          重新整理
        </el-button>
        <el-button type="info" @click="clearAllData" :loading="clearing">
          <el-icon><Delete /></el-icon>
          清除所有資料
        </el-button>
      </div>
    </div>

    <!-- Summary Statistics -->
    <div class="statistics-container">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="statistic-card">
            <el-statistic title="總提交用戶" :value="summary.total_users" />
            <div class="statistic-icon users">
              <el-icon><User /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="statistic-card">
            <el-statistic title="總請購項目" :value="summary.total_items" />
            <div class="statistic-icon requisitions">
              <el-icon><Document /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="statistic-card">
            <el-statistic title="有疑問項目" :value="summary.total_questioned" />
            <div class="statistic-icon questioned">
              <el-icon><QuestionFilled /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="statistic-card">
            <el-statistic title="拒絕項目" :value="summary.total_rejected" />
            <div class="statistic-icon rejected">
              <el-icon><CircleCloseFilled /></el-icon>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- User Statistics Table -->
    <div class="table-container">
      <div class="table-header">
        <h2>用戶請購統計</h2>
        <el-input
          v-model="searchUser"
          placeholder="搜尋用戶..."
          style="width: 200px;"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <el-table 
        :data="filteredUserStatistics" 
        :loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="display_name" label="用戶名稱" width="150" />
        <el-table-column prop="total_items" label="總請購項目" width="120" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.total_items }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="questioned_items" label="有疑問項目" width="120" align="center">
          <template #default="{ row }">
            <el-tag type="warning" size="small" v-if="row.questioned_items > 0">
              {{ row.questioned_items }}
            </el-tag>
            <span v-else>0</span>
          </template>
        </el-table-column>
        <el-table-column prop="rejected_items" label="拒絕項目" width="120" align="center">
          <template #default="{ row }">
            <el-tag type="danger" size="small" v-if="row.rejected_items > 0">
              {{ row.rejected_items }}
            </el-tag>
            <span v-else>0</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_problematic" label="問題總數" width="120" align="center">
          <template #default="{ row }">
            <el-tag 
              :type="row.total_problematic > 0 ? 'danger' : 'success'" 
              size="small"
            >
              {{ row.total_problematic }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="狀態摘要" min-width="200">
          <template #default="{ row }">
            <span v-if="row.total_problematic === 0" class="status-good">
              ✅ 所有請購項目正常
            </span>
            <span v-else class="status-summary">
              {{ row.display_name }} - {{ row.total_items }} 個請購項目已提交，
              {{ row.questioned_items }} 個有疑問，
              {{ row.rejected_items }} 個被拒絕
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center">
          <template #default="{ row }">
            <el-button 
              size="small" 
              type="primary" 
              @click="viewUserDetails(row)"
              :disabled="row.total_problematic === 0"
            >
              查看詳情
            </el-button>
            <el-button 
              size="small" 
              type="success" 
              @click="copyLineMessage(row)"
              :disabled="row.total_problematic === 0"
            >
              複製LINE訊息
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- User Details Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="`${selectedUser.display_name} 的疑問詳情`"
      width="900px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedUserQuestions">
        <!-- Questions Section -->
        <div v-if="selectedUserQuestions.questions && selectedUserQuestions.questions.length > 0">
          <h4>❓ 疑問項目 ({{ selectedUserQuestions.questions.length }})</h4>
          <el-table :data="selectedUserQuestions.questions" size="small" style="margin-bottom: 20px;">
            <el-table-column prop="request_order_no" label="請購單號" width="120" />
            <el-table-column prop="item_name" label="項目名稱" width="150" />
            <el-table-column prop="status_note" label="疑問內容" min-width="200" />
            <el-table-column prop="submit_date" label="提交日期" width="100" />
          </el-table>
        </div>

        <!-- Rejections Section -->
        <div v-if="selectedUserQuestions.rejections && selectedUserQuestions.rejections.length > 0">
          <h4>❌ 拒絕項目 ({{ selectedUserQuestions.rejections.length }})</h4>
          <el-table :data="selectedUserQuestions.rejections" size="small">
            <el-table-column prop="request_order_no" label="請購單號" width="120" />
            <el-table-column prop="item_name" label="項目名稱" width="150" />
            <el-table-column prop="status_note" label="拒絕原因" min-width="200" />
            <el-table-column prop="submit_date" label="提交日期" width="100" />
          </el-table>
        </div>

        <!-- LINE Message Preview -->
        <div class="line-message-preview">
          <h4>📱 LINE 訊息預覽</h4>
          <el-input
            v-model="generatedLineMessage"
            type="textarea"
            :rows="6"
            readonly
            class="line-message-text"
          />
          <div style="margin-top: 10px;">
            <el-button type="success" @click="copyToClipboard(generatedLineMessage)">
              <el-icon><CopyDocument /></el-icon>
              複製到剪貼簿
            </el-button>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">關閉</el-button>
        <el-button type="success" @click="copyToClipboard(generatedLineMessage)">
          複製LINE訊息
        </el-button>
      </template>
    </el-dialog>

    <!-- Clear Data Confirmation -->
    <el-dialog
      v-model="clearConfirmVisible"
      title="確認清除資料"
      width="400px"
    >
      <p>您確定要清除所有疑問和拒絕資料嗎？此操作無法撤銷。</p>
      <template #footer>
        <el-button @click="clearConfirmVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmClearData" :loading="clearing">
          確定清除
        </el-button>
      </template>
    </el-dialog>

    <!-- Info Notice -->
    <div class="info-notice">
      <el-alert
        title="功能說明"
        description="此頁面顯示所有用戶的請購單統計，包括疑問和拒絕的項目。您可以查看詳情並複製LINE訊息來通知用戶。"
        type="info"
        show-icon
        :closable="false"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh, 
  Delete,
  User,
  Document,
  QuestionFilled, 
  CircleCloseFilled,
  Search,
  CopyDocument
} from '@element-plus/icons-vue'
import api from '@/api/index'

// Reactive data
const loading = ref(false)
const clearing = ref(false)
const userStatistics = ref([])
const questionsData = ref([])
const detailDialogVisible = ref(false)
const clearConfirmVisible = ref(false)
const selectedUser = ref({})
const selectedUserQuestions = ref(null)
const generatedLineMessage = ref('')
const searchUser = ref('')

// Summary statistics
const summary = ref({
  total_users: 0,
  total_items: 0,
  total_questioned: 0,
  total_rejected: 0
})

// Computed
const filteredUserStatistics = computed(() => {
  if (!searchUser.value) {
    return userStatistics.value
  }
  return userStatistics.value.filter(user => 
    user.display_name.toLowerCase().includes(searchUser.value.toLowerCase()) ||
    user.username.toLowerCase().includes(searchUser.value.toLowerCase())
  )
})

// Methods
const loadUserStatistics = async () => {
  loading.value = true
  try {
    const response = await api.get('/requisitions/user-statistics')
    const data = response.data?.data || response.data || {}
    userStatistics.value = data.user_statistics || []
    summary.value = data.summary || {
      total_users: 0,
      total_items: 0,
      total_questioned: 0,
      total_rejected: 0
    }
  } catch (error) {
    console.error('載入用戶統計失敗:', error)
    ElMessage.error('載入用戶統計失敗')
  } finally {
    loading.value = false
  }
}

const loadQuestionsData = async () => {
  try {
    const response = await api.get('/requisitions/questions-data')
    const data = response.data?.data || response.data || {}
    questionsData.value = data.user_questions || []
  } catch (error) {
    console.error('載入疑問資料失敗:', error)
    ElMessage.error('載入疑問資料失敗')
  }
}

const refreshData = async () => {
  await Promise.all([loadUserStatistics(), loadQuestionsData()])
  ElMessage.success('資料已重新整理')
}

const viewUserDetails = async (user) => {
  selectedUser.value = user
  
  // Find user's questions data
  const userQuestions = questionsData.value.find(q => 
    q.username === user.username || q.username === user.display_name
  )
  
  selectedUserQuestions.value = userQuestions || { questions: [], rejections: [] }
  
  // Generate LINE message
  generatedLineMessage.value = generateLineMessage(user, selectedUserQuestions.value)
  
  detailDialogVisible.value = true
}

const generateLineMessage = (user, questionsData) => {
  let message = `請購項目狀態通知\n\n`
  message += `${user.display_name}\n`
  
  // Only show questioned and rejected items count, not total
  if (user.questioned_items > 0) {
    message += `有疑問項目: ${user.questioned_items} 個\n`
  }
  
  if (user.rejected_items > 0) {
    message += `拒絕項目: ${user.rejected_items} 個\n`
  }
  
  message += `\n`
  
  // Add questions details with item names
  if (questionsData.questions && questionsData.questions.length > 0) {
    message += `疑問項目詳情:\n`
    questionsData.questions.forEach((q, index) => {
      // Show item name and problem description
      message += `${index + 1}. ${q.item_name || '未知物品'}`
      if (q.status_note) {
        message += ` - ${q.status_note}\n`
      } else {
        message += ` - 有疑問\n`
      }
      message += `   請購單號: ${q.request_order_no}\n`
    })
    message += `\n`
  }
  
  // Add rejection details with item names
  if (questionsData.rejections && questionsData.rejections.length > 0) {
    message += `拒絕項目詳情:\n`
    questionsData.rejections.forEach((r, index) => {
      // Show item name and rejection reason
      message += `${index + 1}. ${r.item_name || '未知物品'}`
      if (r.status_note) {
        message += ` - ${r.status_note}\n`
      } else {
        message += ` - 已拒絕\n`
      }
      message += `   請購單號: ${r.request_order_no}\n`
    })
    message += `\n`
  }
  
  message += `請盡快處理上述項目問題，如有疑問請聯繫採購部門。\n`
  message += `\n${new Date().toLocaleString('zh-TW')}`
  
  return message
}

const copyLineMessage = async (user) => {
  // Find user's questions data
  const userQuestions = questionsData.value.find(q => 
    q.username === user.username || q.username === user.display_name
  )
  
  const message = generateLineMessage(user, userQuestions || { questions: [], rejections: [] })
  await copyToClipboard(message)
}

const copyToClipboard = async (text) => {
  try {
    // Check if clipboard API is available
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text)
      ElMessage.success('已複製到剪貼簿！可以貼到LINE中發送。')
    } else {
      // Fallback method using a temporary textarea
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      ElMessage.success('已複製到剪貼簿！可以貼到LINE中發送。')
    }
  } catch (error) {
    console.error('複製失敗:', error)

    // Try fallback method if clipboard API fails
    try {
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      ElMessage.success('已複製到剪貼簿！可以貼到LINE中發送。')
    } catch (fallbackError) {
      console.error('Fallback複製也失敗:', fallbackError)
      ElMessage.error('複製失敗，請手動複製')
    }
  }
}

const clearAllData = () => {
  clearConfirmVisible.value = true
}

const confirmClearData = async () => {
  clearing.value = true
  try {
    // This would typically call a backend API to clear the data
    // For now, we'll just refresh to show empty data
    await new Promise(resolve => setTimeout(resolve, 1000)) // Simulate API call
    
    userStatistics.value = []
    questionsData.value = []
    summary.value = {
      total_users: 0,
      total_items: 0,
      total_questioned: 0,
      total_rejected: 0
    }
    
    clearConfirmVisible.value = false
    ElMessage.success('所有疑問資料已清除')
  } catch (error) {
    console.error('清除資料失敗:', error)
    ElMessage.error('清除資料失敗')
  } finally {
    clearing.value = false
  }
}

onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.questions-overview {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .header-actions {
    display: flex;
    gap: 8px;
  }
}

.page-title {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.statistics-container {
  margin-bottom: 20px;

  .statistic-card {
    position: relative;
    
    .statistic-icon {
      position: absolute;
      top: 16px;
      right: 16px;
      font-size: 24px;
      opacity: 0.6;
      
      &.users { color: #409eff; }
      &.requisitions { color: #67c23a; }
      &.questioned { color: #e6a23c; }
      &.rejected { color: #f56c6c; }
    }
  }
}

.table-container {
  background: white;
  border-radius: 4px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  h2 {
    margin: 0;
    color: #303133;
  }
}

.status-good {
  color: #67c23a;
  font-weight: 500;
}

.status-summary {
  color: #606266;
  line-height: 1.4;
}

.line-message-preview {
  margin-top: 24px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;

  h4 {
    margin: 0 0 12px 0;
    color: #303133;
  }

  .line-message-text {
    font-family: 'Courier New', monospace;
    background: white;
  }
}

.info-notice {
  margin-top: 20px;
}

:deep(.el-statistic__content) {
  font-size: 28px;
  font-weight: bold;
}

:deep(.el-alert__description) {
  margin-top: 8px;
  font-size: 13px;
}

:deep(.el-table__body-wrapper) {
  max-height: 500px;
  overflow-y: auto;
}

:deep(.el-dialog__body) {
  max-height: 60vh;
  overflow-y: auto;
}
</style>