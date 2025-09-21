<template>
  <div class="users-management">
    <!-- Header with actions -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">用戶管理</h1>
        <div class="stats-cards" v-if="statistics">
          <div class="stat-card">
            <div class="stat-number">{{ statistics.total_users }}</div>
            <div class="stat-label">總用戶數</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ statistics.active_users }}</div>
            <div class="stat-label">活躍用戶</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ statistics.inactive_users }}</div>
            <div class="stat-label">停用用戶</div>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn btn-primary" @click="showCreateModal">
          <i class="icon-plus"></i>
          新增用戶
        </button>
      </div>
    </div>

    <!-- Search and Filters -->
    <div class="search-panel">
      <div class="search-row">
        <div class="search-field">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜尋用戶名稱、姓名、部門..."
            class="search-input"
            @keyup.enter="handleSearch"
          />
          <button class="search-btn" @click="handleSearch">
            <i class="icon-search"></i>
          </button>
        </div>

        <div class="filter-group">
          <select v-model="filters.role" class="filter-select" @change="handleSearch">
            <option value="">全部角色</option>
            <option v-for="role in roles" :key="role.value" :value="role.value">
              {{ role.label }}
            </option>
          </select>

          <select v-model="filters.is_active" class="filter-select" @change="handleSearch">
            <option value="">全部狀態</option>
            <option value="true">活躍</option>
            <option value="false">停用</option>
          </select>

          <input
            v-model="filters.department"
            type="text"
            placeholder="部門"
            class="filter-input"
            @keyup.enter="handleSearch"
          />

          <button class="btn btn-outline" @click="clearFilters">清除篩選</button>
        </div>
      </div>
    </div>

    <!-- Users Table -->
    <div class="data-table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>用戶ID</th>
            <th>中文姓名</th>
            <th>用戶名稱</th>
            <th>部門</th>
            <th>職稱</th>
            <th>角色</th>
            <th>狀態</th>
            <th>創建時間</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.user_id" class="table-row">
            <td>{{ user.user_id }}</td>
            <td>{{ user.chinese_name }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.department || '-' }}</td>
            <td>{{ user.job_title || '-' }}</td>
            <td>
              <span class="role-badge" :class="`role-${user.role.toLowerCase()}`">
                {{ getRoleLabel(user.role) }}
              </span>
            </td>
            <td>
              <span class="status-badge" :class="user.is_active ? 'status-active' : 'status-inactive'">
                {{ user.is_active ? '活躍' : '停用' }}
              </span>
            </td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td>
              <div class="action-buttons">
                <button class="btn-icon" @click="editUser(user)" title="編輯">
                  <i class="icon-edit"></i>
                </button>
                <button class="btn-icon" @click="showResetPasswordModal(user)" title="重置密碼">
                  <i class="icon-key"></i>
                </button>
                <button
                  v-if="user.is_active"
                  class="btn-icon btn-danger"
                  @click="deactivateUser(user)"
                  title="停用"
                  :disabled="user.user_id === currentUser?.user_id"
                >
                  <i class="icon-ban"></i>
                </button>
                <button
                  v-else
                  class="btn-icon btn-success"
                  @click="activateUser(user)"
                  title="啟用"
                >
                  <i class="icon-check"></i>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="loading" class="loading-spinner">載入中...</div>
      <div v-if="!loading && users.length === 0" class="no-data">沒有找到用戶</div>
    </div>

    <!-- Pagination -->
    <div v-if="pagination.pages > 1" class="pagination">
      <button
        class="pagination-btn"
        :disabled="pagination.page <= 1"
        @click="changePage(pagination.page - 1)"
      >
        上一頁
      </button>

      <span class="pagination-info">
        第 {{ pagination.page }} 頁，共 {{ pagination.pages }} 頁
        (總計 {{ pagination.total }} 筆)
      </span>

      <button
        class="pagination-btn"
        :disabled="pagination.page >= pagination.pages"
        @click="changePage(pagination.page + 1)"
      >
        下一頁
      </button>
    </div>

    <!-- Create/Edit User Modal -->
    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ editingUser ? '編輯用戶' : '新增用戶' }}</h3>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>

        <form @submit.prevent="saveUser" class="user-form">
          <div class="form-row">
            <div class="form-field">
              <label>用戶名稱 *</label>
              <input
                v-model="userForm.username"
                type="text"
                required
                :disabled="!!editingUser"
                class="form-input"
              />
            </div>
            <div class="form-field">
              <label>中文姓名 *</label>
              <input
                v-model="userForm.chinese_name"
                type="text"
                required
                class="form-input"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-field">
              <label>部門</label>
              <input
                v-model="userForm.department"
                type="text"
                class="form-input"
              />
            </div>
            <div class="form-field">
              <label>職稱</label>
              <input
                v-model="userForm.job_title"
                type="text"
                class="form-input"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-field">
              <label>角色 *</label>
              <select v-model="userForm.role" required class="form-select">
                <option value="">請選擇角色</option>
                <option v-for="role in roles" :key="role.value" :value="role.value">
                  {{ role.label }}
                </option>
              </select>
            </div>
            <div class="form-field">
              <label>
                <input
                  v-model="userForm.is_active"
                  type="checkbox"
                  class="form-checkbox"
                />
                啟用帳號
              </label>
            </div>
          </div>

          <div v-if="!editingUser" class="form-row">
            <div class="form-field">
              <label>密碼 *</label>
              <input
                v-model="userForm.password"
                type="password"
                required
                class="form-input"
                placeholder="至少8字符，包含大小寫字母、數字和特殊字符"
              />
            </div>
            <div class="form-field">
              <label>確認密碼 *</label>
              <input
                v-model="confirmPassword"
                type="password"
                required
                class="form-input"
              />
            </div>
          </div>

          <div class="form-actions">
            <button type="button" class="btn btn-outline" @click="closeModal">取消</button>
            <button type="submit" class="btn btn-primary" :disabled="saving">
              {{ saving ? '儲存中...' : '儲存' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Reset Password Modal -->
    <div v-if="showPasswordModal" class="modal-overlay" @click="closePasswordModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>重置密碼 - {{ passwordUser?.chinese_name }}</h3>
          <button class="close-btn" @click="closePasswordModal">&times;</button>
        </div>

        <form @submit.prevent="resetPassword" class="password-form">
          <div class="form-field">
            <label>新密碼 *</label>
            <input
              v-model="newPassword"
              type="password"
              required
              class="form-input"
              placeholder="至少8字符，包含大小寫字母、數字和特殊字符"
            />
          </div>
          <div class="form-field">
            <label>確認新密碼 *</label>
            <input
              v-model="confirmNewPassword"
              type="password"
              required
              class="form-input"
            />
          </div>

          <div class="form-actions">
            <button type="button" class="btn btn-outline" @click="closePasswordModal">取消</button>
            <button type="submit" class="btn btn-primary" :disabled="resetting">
              {{ resetting ? '重置中...' : '重置密碼' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Confirm Dialog -->
    <div v-if="showConfirmDialog" class="modal-overlay" @click="cancelConfirm">
      <div class="modal-content confirm-dialog" @click.stop>
        <div class="modal-header">
          <h3>確認操作</h3>
        </div>
        <div class="confirm-content">
          <p>{{ confirmMessage }}</p>
        </div>
        <div class="form-actions">
          <button class="btn btn-outline" @click="cancelConfirm">取消</button>
          <button class="btn btn-danger" @click="confirmAction">確認</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { usersApi, type UserSearchFilters, type CreateUserRequest, type UpdateUserRequest } from '@/api/users'
import type { User, UserRoleType } from '@/types/auth'
import { useAuthStore } from '@/stores/auth'

// Store
const authStore = useAuthStore()
const currentUser = computed(() => authStore.currentUser)

// Data
const users = ref<User[]>([])
const roles = ref<Array<{value: UserRoleType, label: string}>>([])
const statistics = ref<any>(null)
const loading = ref(false)
const saving = ref(false)
const resetting = ref(false)

// Search and filters
const searchQuery = ref('')
const filters = reactive<UserSearchFilters>({
  q: '',
  role: undefined,
  department: '',
  is_active: undefined,
  page: 1,
  page_size: 20
})

// Pagination
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
  pages: 0
})

// Modals
const showModal = ref(false)
const showPasswordModal = ref(false)
const showConfirmDialog = ref(false)
const editingUser = ref<User | null>(null)
const passwordUser = ref<User | null>(null)

// Forms
const userForm = reactive<CreateUserRequest & UpdateUserRequest>({
  username: '',
  chinese_name: '',
  password: '',
  department: '',
  job_title: '',
  role: 'Everyone' as UserRoleType,
  is_active: true
})

const confirmPassword = ref('')
const newPassword = ref('')
const confirmNewPassword = ref('')

// Confirm dialog
const confirmMessage = ref('')
const confirmCallback = ref<(() => void) | null>(null)

// Methods
const loadUsers = async () => {
  loading.value = true
  try {
    const response = await usersApi.searchUsers(filters)
    users.value = response.items
    pagination.page = response.pagination.page
    pagination.page_size = response.pagination.page_size
    pagination.total = response.pagination.total
    pagination.pages = response.pagination.pages
  } catch (error) {
    console.error('Failed to load users:', error)
  } finally {
    loading.value = false
  }
}

const loadRoles = async () => {
  try {
    roles.value = await usersApi.getRoles()
  } catch (error) {
    console.error('Failed to load roles:', error)
  }
}

const loadStatistics = async () => {
  try {
    statistics.value = await usersApi.getUserStatistics()
  } catch (error) {
    console.error('Failed to load statistics:', error)
  }
}

const handleSearch = () => {
  filters.q = searchQuery.value
  filters.page = 1
  loadUsers()
}

const clearFilters = () => {
  searchQuery.value = ''
  filters.q = ''
  filters.role = undefined
  filters.department = ''
  filters.is_active = undefined
  filters.page = 1
  loadUsers()
}

const changePage = (page: number) => {
  filters.page = page
  loadUsers()
}

const showCreateModal = () => {
  editingUser.value = null
  resetUserForm()
  showModal.value = true
}

const editUser = (user: User) => {
  editingUser.value = user
  userForm.username = user.username
  userForm.chinese_name = user.chinese_name
  userForm.department = user.department || ''
  userForm.job_title = user.job_title || ''
  userForm.role = user.role as UserRoleType
  userForm.is_active = user.is_active
  userForm.password = ''
  confirmPassword.value = ''
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editingUser.value = null
  resetUserForm()
}

const resetUserForm = () => {
  userForm.username = ''
  userForm.chinese_name = ''
  userForm.password = ''
  userForm.department = ''
  userForm.job_title = ''
  userForm.role = 'Everyone' as UserRoleType
  userForm.is_active = true
  confirmPassword.value = ''
}

const saveUser = async () => {
  if (!editingUser.value && userForm.password !== confirmPassword.value) {
    alert('密碼確認不符')
    return
  }

  saving.value = true
  try {
    if (editingUser.value) {
      // Update user
      const updateData: UpdateUserRequest = {
        chinese_name: userForm.chinese_name,
        department: userForm.department,
        job_title: userForm.job_title,
        role: userForm.role,
        is_active: userForm.is_active
      }
      await usersApi.updateUser(editingUser.value.user_id, updateData)
    } else {
      // Create user
      const createData: CreateUserRequest = {
        username: userForm.username,
        chinese_name: userForm.chinese_name,
        password: userForm.password,
        department: userForm.department,
        job_title: userForm.job_title,
        role: userForm.role,
        is_active: userForm.is_active
      }
      await usersApi.createUser(createData)
    }

    closeModal()
    loadUsers()
    loadStatistics()
  } catch (error: any) {
    alert(error.response?.data?.error?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const showResetPasswordModal = (user: User) => {
  passwordUser.value = user
  newPassword.value = ''
  confirmNewPassword.value = ''
  showPasswordModal.value = true
}

const closePasswordModal = () => {
  showPasswordModal.value = false
  passwordUser.value = null
  newPassword.value = ''
  confirmNewPassword.value = ''
}

const resetPassword = async () => {
  if (newPassword.value !== confirmNewPassword.value) {
    alert('密碼確認不符')
    return
  }

  if (!passwordUser.value) return

  resetting.value = true
  try {
    await usersApi.resetUserPassword(passwordUser.value.user_id, {
      new_password: newPassword.value
    })
    closePasswordModal()
    alert('密碼重置成功')
  } catch (error: any) {
    alert(error.response?.data?.error?.message || '密碼重置失败')
  } finally {
    resetting.value = false
  }
}

const deactivateUser = (user: User) => {
  confirmMessage.value = `確定要停用用戶 "${user.chinese_name}" 嗎？`
  confirmCallback.value = async () => {
    try {
      await usersApi.deleteUser(user.user_id)
      loadUsers()
      loadStatistics()
    } catch (error: any) {
      alert(error.response?.data?.error?.message || '停用失败')
    }
  }
  showConfirmDialog.value = true
}

const activateUser = async (user: User) => {
  try {
    await usersApi.activateUser(user.user_id)
    loadUsers()
    loadStatistics()
  } catch (error: any) {
    alert(error.response?.data?.error?.message || '啟用失败')
  }
}

const confirmAction = () => {
  if (confirmCallback.value) {
    confirmCallback.value()
  }
  cancelConfirm()
}

const cancelConfirm = () => {
  showConfirmDialog.value = false
  confirmCallback.value = null
  confirmMessage.value = ''
}

const getRoleLabel = (role: string): string => {
  const roleItem = roles.value.find(r => r.value === role)
  return roleItem?.label || role
}

const formatDate = (dateString?: string): string => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-TW')
}

// Initialize
onMounted(() => {
  loadUsers()
  loadRoles()
  loadStatistics()
})
</script>

<style scoped>
.users-management {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: #2c3e50;
}

.stats-cards {
  display: flex;
  gap: 16px;
}

.stat-card {
  background: white;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-width: 120px;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #3498db;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #7f8c8d;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.search-panel {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.search-row {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.search-field {
  display: flex;
  flex: 1;
  min-width: 300px;
}

.search-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-right: none;
  border-radius: 4px 0 0 4px;
  font-size: 14px;
}

.search-btn {
  padding: 8px 12px;
  background: #3498db;
  color: white;
  border: 1px solid #3498db;
  border-radius: 0 4px 4px 0;
  cursor: pointer;
}

.filter-group {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-select, .filter-input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  min-width: 120px;
}

.data-table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 24px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: #f8f9fa;
  padding: 16px 12px;
  text-align: left;
  font-weight: 600;
  color: #2c3e50;
  border-bottom: 1px solid #dee2e6;
}

.data-table td {
  padding: 12px;
  border-bottom: 1px solid #f1f3f4;
  color: #2c3e50;
}

.table-row:hover {
  background: #f8f9fa;
}

.role-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.role-admin { background: #e74c3c; color: white; }
.role-procurementmgr { background: #9b59b6; color: white; }
.role-procurement { background: #3498db; color: white; }
.role-accountant { background: #f39c12; color: white; }
.role-everyone { background: #95a5a6; color: white; }

.status-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-active { background: #2ecc71; color: white; }
.status-inactive { background: #e74c3c; color: white; }

.action-buttons {
  display: flex;
  gap: 8px;
}

.btn-icon {
  padding: 6px 8px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-icon:hover {
  background: #f8f9fa;
}

.btn-icon.btn-danger:hover {
  background: #e74c3c;
  color: white;
  border-color: #e74c3c;
}

.btn-icon.btn-success:hover {
  background: #2ecc71;
  color: white;
  border-color: #2ecc71;
}

.btn-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-spinner, .no-data {
  text-align: center;
  padding: 40px;
  color: #7f8c8d;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.pagination-btn {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-info {
  color: #7f8c8d;
  font-size: 14px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  padding: 0;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.user-form, .password-form {
  padding: 24px;
}

.form-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.form-field {
  flex: 1;
}

.form-field label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #2c3e50;
}

.form-input, .form-select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-checkbox {
  margin-right: 8px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.btn {
  padding: 10px 20px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.btn-primary {
  background: #3498db;
  color: white;
  border-color: #3498db;
}

.btn-primary:hover {
  background: #2980b9;
  border-color: #2980b9;
}

.btn-outline {
  background: white;
  color: #3498db;
  border-color: #3498db;
}

.btn-outline:hover {
  background: #3498db;
  color: white;
}

.btn-danger {
  background: #e74c3c;
  color: white;
  border-color: #e74c3c;
}

.btn-danger:hover {
  background: #c0392b;
  border-color: #c0392b;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.confirm-dialog {
  max-width: 400px;
}

.confirm-content {
  padding: 20px 24px;
}

.confirm-content p {
  margin: 0;
  color: #2c3e50;
  line-height: 1.5;
}

/* Icons using CSS (you might want to use a proper icon library) */
.icon-plus::before { content: '+'; }
.icon-search::before { content: '🔍'; }
.icon-edit::before { content: '✏️'; }
.icon-key::before { content: '🔑'; }
.icon-ban::before { content: '🚫'; }
.icon-check::before { content: '✅'; }
</style>