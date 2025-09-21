<template>
  <div class="dashboard">
    <PageHeader
      title="我的儀表板"
      :subtitle="`歡迎回來，${authStore.user?.chinese_name || authStore.user?.username}`"
      :show-refresh="true"
      @refresh="handleRefresh"
    >
      <template #extra>
        <el-select
          v-model="selectedPeriod"
          placeholder="選擇時間範圍"
          style="width: 120px"
          @change="handlePeriodChange"
        >
          <el-option label="本週" value="week" />
          <el-option label="本月" value="month" />
          <el-option label="本季" value="quarter" />
        </el-select>
      </template>
    </PageHeader>

    <!-- My Items Overview -->
    <div class="dashboard-stats">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="疑問項目"
            :value="myItems.questioned"
            icon="QuestionFilled"
            color="warning"
            :loading="loading"
            description="需要您回覆"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="被拒絕項目"
            :value="myItems.rejected"
            icon="CircleClose"
            color="danger"
            :loading="loading"
            description="需要修改"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="未到貨項目"
            :value="myItems.notArrived"
            icon="Van"
            color="info"
            :loading="loading"
            description="運送中"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="已到貨項目"
            :value="myItems.arrived"
            icon="CircleCheck"
            color="success"
            :loading="loading"
            description="待領取"
          />
        </el-col>
      </el-row>
    </div>

    <!-- My Items Lists and Quick Actions -->
    <div class="dashboard-content">
      <el-row :gutter="20">
        <!-- Left side - My Items Lists -->
        <el-col :xs="24" :lg="16">
          <div class="dashboard-charts">
            <!-- Questioned Items -->
            <el-card class="items-card">
              <template #header>
                <div class="card-header">
                  <span><el-icon><QuestionFilled /></el-icon> 疑問項目列表</span>
                  <el-button link type="primary" @click="viewAllQuestioned">查看全部</el-button>
                </div>
              </template>
              <div class="items-list">
                <div v-if="questionedItems.length === 0" class="empty-state">
                  <el-empty description="暫無疑問項目" :image-size="60" />
                </div>
                <div v-else>
                  <div v-for="item in questionedItems.slice(0, 5)" :key="item.id" class="item-row">
                    <div class="item-info">
                      <div class="item-title">{{ item.item_name }}</div>
                      <div class="item-meta">
                        <span>請購單: {{ item.request_order_no }}</span>
                        <span class="separator">|</span>
                        <span>{{ item.submit_date }}</span>
                      </div>
                    </div>
                    <div class="item-action">
                      <el-button size="small" type="warning" @click="handleReply(item)">回覆</el-button>
                    </div>
                  </div>
                </div>
              </div>
            </el-card>

            <!-- Rejected Items -->
            <el-card class="items-card" style="margin-top: 20px;">
              <template #header>
                <div class="card-header">
                  <span><el-icon><CircleClose /></el-icon> 被拒絕項目列表</span>
                  <el-button link type="primary" @click="viewAllRejected">查看全部</el-button>
                </div>
              </template>
              <div class="items-list">
                <div v-if="rejectedItems.length === 0" class="empty-state">
                  <el-empty description="暫無被拒絕項目" :image-size="60" />
                </div>
                <div v-else>
                  <div v-for="item in rejectedItems.slice(0, 5)" :key="item.id" class="item-row">
                    <div class="item-info">
                      <div class="item-title">{{ item.item_name }}</div>
                      <div class="item-meta">
                        <span>拒絕原因: {{ item.status_note }}</span>
                      </div>
                    </div>
                    <div class="item-action">
                      <el-button size="small" type="danger" @click="handleEdit(item)">修改</el-button>
                    </div>
                  </div>
                </div>
              </div>
            </el-card>

            <!-- Status Distribution -->
            <el-card class="chart-card" header="請購單狀態分布" style="margin-top: 20px;">
              <div class="status-stats">
                <div
                  v-for="item in statusDistribution"
                  :key="item.status"
                  class="status-item"
                >
                  <div class="status-info">
                    <StatusTag :status="item.status" size="small" />
                    <span class="status-name">{{ item.name }}</span>
                  </div>
                  <div class="status-count">{{ item.count }}</div>
                </div>
              </div>
            </el-card>
          </div>
        </el-col>

        <!-- Right side - Quick Actions & Recent Activities -->
        <el-col :xs="24" :lg="8">
          <div class="dashboard-sidebar">
            <!-- Quick Actions -->
            <el-card header="快速操作">
              <div class="quick-actions">
                <el-button
                  type="primary"
                  :icon="Plus"
                  @click="createRequisition"
                >
                  新增請購單
                </el-button>
                <el-button
                  type="success"
                  :icon="ShoppingCart"
                  @click="buildPO"
                >
                  建立採購單
                </el-button>
                <el-button
                  type="info"
                  :icon="Search"
                  @click="queryInventory"
                >
                  庫存查詢
                </el-button>
                <el-button
                  type="warning"
                  :icon="Van"
                  @click="manageReceiving"
                >
                  收貨管理
                </el-button>
              </div>
            </el-card>

            <!-- Recent Activities -->
            <el-card header="最近活動" style="margin-top: 20px;">
              <el-timeline>
                <el-timeline-item
                  v-for="activity in recentActivities"
                  :key="activity.id"
                  :timestamp="activity.timestamp"
                  size="small"
                >
                  <div class="activity-content">
                    <div class="activity-title">{{ activity.title }}</div>
                    <div class="activity-description">{{ activity.description }}</div>
                  </div>
                </el-timeline-item>
              </el-timeline>
              
              <div v-if="recentActivities.length === 0" class="no-activities">
                <el-empty description="暫無活動記錄" :image-size="60" />
              </div>
            </el-card>

            <!-- Notifications -->
            <el-card header="系統通知" style="margin-top: 20px;">
              <div class="notifications">
                <div
                  v-for="notification in notifications"
                  :key="notification.id"
                  class="notification-item"
                  :class="`notification-${notification.type}`"
                >
                  <el-icon>
                    <Warning v-if="notification.type === 'warning'" />
                    <InfoFilled v-else-if="notification.type === 'info'" />
                    <CircleCheckFilled v-else-if="notification.type === 'success'" />
                    <CircleCloseFilled v-else />
                  </el-icon>
                  <div class="notification-content">
                    <div class="notification-title">{{ notification.title }}</div>
                    <div class="notification-time">{{ notification.time }}</div>
                  </div>
                </div>
              </div>
              
              <div v-if="notifications.length === 0" class="no-notifications">
                暫無系統通知
              </div>
            </el-card>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  Plus,
  ShoppingCart,
  Search,
  Warning,
  InfoFilled,
  CircleCheckFilled,
  CircleCloseFilled,
  Van,
  QuestionFilled,
  CircleClose,
  CircleCheck
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { PageHeader, StatCard, StatusTag } from '@/components'
import { useRequisitionStore, useInventoryStore, useProcurementStore, useAccountingStore, useAuthStore } from '@/stores'
import api from '@/api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const requisitionStore = useRequisitionStore()
const inventoryStore = useInventoryStore()
const procurementStore = useProcurementStore()
const accountingStore = useAccountingStore()
const authStore = useAuthStore()

// Reactive data
const loading = ref(false)
const selectedPeriod = ref('month')

// My Items Statistics
const myItems = reactive({
  questioned: 0,
  rejected: 0,
  notArrived: 0,
  arrived: 0
})

// Item Lists
const questionedItems = ref([])
const rejectedItems = ref([])
const notArrivedItems = ref([])
const arrivedItems = ref([])

// Trends
const trends = reactive({
  requisitions: { value: 5.2, isUp: true },
  purchase: { value: -2.1, isUp: false },
  receiving: { value: 8.7, isUp: true },
  inventory: { value: 3.4, isUp: true }
})

// Status distribution
const statusDistribution = ref([
  { status: 'draft', name: '草稿', count: 8 },
  { status: 'submitted', name: '已提交', count: 15 },
  { status: 'reviewed', name: '已審核', count: 23 },
  { status: 'approved', name: '已核准', count: 45 }
])

// Recent activities
const recentActivities = ref([
  {
    id: 1,
    title: '新請購單已提交',
    description: '用戶張三提交了請購單 REQ-2024-001',
    timestamp: '2小時前'
  },
  {
    id: 2,
    title: '採購單已確認',
    description: '採購單 PO-2024-005 已確認採購',
    timestamp: '4小時前'
  },
  {
    id: 3,
    title: '物品已到貨',
    description: '供應商A的貨品已到貨，待收貨確認',
    timestamp: '6小時前'
  },
  {
    id: 4,
    title: '庫存預警',
    description: '辦公用品類庫存不足，請及時補充',
    timestamp: '1天前'
  }
])

// Notifications
const notifications = ref([
  {
    id: 1,
    type: 'warning',
    title: '3張請購單待審核',
    time: '10分鐘前'
  },
  {
    id: 2,
    type: 'info',
    title: '系統將於今晚維護',
    time: '2小時前'
  }
])

// Chart instance
let chartInstance: echarts.ECharts | null = null

// Methods
const handleRefresh = async () => {
  await fetchDashboardData()
}

const handlePeriodChange = () => {
  fetchDashboardData()
}

const fetchDashboardData = async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchMyItems(),
      fetchStatusDistribution(),
      fetchRecentActivities(),
      fetchNotifications()
    ])
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  } finally {
    loading.value = false
  }
}

const fetchMyItems = async () => {
  try {
    const userId = authStore.user?.id
    if (!userId) return

    // 獲取我的請購單項目
    const response = await api.get('/api/v1/requisitions/my-items', {
      params: {
        user_id: userId,
        period: selectedPeriod.value
      }
    })

    if (response.data.success) {
      const items = response.data.data || []

      // 分類項目
      questionedItems.value = items.filter(item => item.item_status === 'questioned')
      rejectedItems.value = items.filter(item => item.item_status === 'rejected')

      // 統計數量
      myItems.questioned = questionedItems.value.length
      myItems.rejected = rejectedItems.value.length
    }

    // 獲取採購單項目狀態
    const poResponse = await api.get('/api/v1/purchase-orders/my-items', {
      params: {
        user_id: userId,
        period: selectedPeriod.value
      }
    })

    if (poResponse.data.success) {
      const poItems = poResponse.data.data || []

      // 分類採購項目
      notArrivedItems.value = poItems.filter(item =>
        item.shipping_status !== 'arrived' && item.shipping_status !== 'completed'
      )
      arrivedItems.value = poItems.filter(item =>
        item.shipping_status === 'arrived' && item.acceptance_status !== 'accepted'
      )

      // 統計數量
      myItems.notArrived = notArrivedItems.value.length
      myItems.arrived = arrivedItems.value.length
    }
  } catch (error) {
    console.error('Failed to fetch my items:', error)
    // 使用模擬數據
    myItems.questioned = 3
    myItems.rejected = 2
    myItems.notArrived = 5
    myItems.arrived = 4

    // 模擬項目列表
    questionedItems.value = [
      { id: 1, item_name: '筆記型電腦', request_order_no: 'REQ-2024-001', submit_date: '2024-01-15', status_note: '規格需要確認' },
      { id: 2, item_name: '辦公椅', request_order_no: 'REQ-2024-002', submit_date: '2024-01-16', status_note: '數量是否正確？' },
      { id: 3, item_name: '投影機', request_order_no: 'REQ-2024-003', submit_date: '2024-01-17', status_note: '品牌偏好？' }
    ]

    rejectedItems.value = [
      { id: 4, item_name: '印表機', request_order_no: 'REQ-2024-004', submit_date: '2024-01-14', status_note: '預算超支' },
      { id: 5, item_name: '會議桌', request_order_no: 'REQ-2024-005', submit_date: '2024-01-13', status_note: '規格不符' }
    ]
  }
}

const fetchStatusDistribution = async () => {
  try {
    const userId = authStore.user?.id
    if (!userId) return

    const response = await api.get('/api/v1/requisitions/status-distribution', {
      params: {
        user_id: userId,
        period: selectedPeriod.value
      }
    })

    if (response.data.success) {
      statusDistribution.value = response.data.data || []
    }
  } catch (error) {
    // 使用預設數據
    statusDistribution.value = [
      { status: 'draft', name: '草稿', count: 2 },
      { status: 'submitted', name: '已提交', count: 5 },
      { status: 'reviewed', name: '已審核', count: 8 },
      { status: 'approved', name: '已核准', count: 12 }
    ]
  }
}

const fetchRecentActivities = async () => {
  try {
    const userId = authStore.user?.id
    if (!userId) return

    const response = await api.get('/api/v1/activities/recent', {
      params: {
        user_id: userId,
        limit: 5
      }
    })

    if (response.data.success) {
      recentActivities.value = response.data.data || []
    }
  } catch (error) {
    // 使用預設數據
    recentActivities.value = [
      { id: 1, title: '請購單已提交', description: '您的請購單 REQ-2024-001 已提交', timestamp: '2小時前' },
      { id: 2, title: '項目已審核', description: '您的筆記型電腦申請已通過審核', timestamp: '5小時前' },
      { id: 3, title: '貨品已到貨', description: '您申請的辦公用品已到貨', timestamp: '1天前' }
    ]
  }
}

const fetchNotifications = async () => {
  // 保持原有實現
}

// Item actions
const handleReply = (item: any) => {
  router.push(`/requisitions/reply/${item.request_order_no}/${item.id}`)
}

const handleEdit = (item: any) => {
  router.push(`/requisitions/edit/${item.request_order_no}`)
}

const viewAllQuestioned = () => {
  router.push('/requisitions?status=questioned')
}

const viewAllRejected = () => {
  router.push('/requisitions?status=rejected')
}

const formatMoney = (value: string | number) => {
  const num = typeof value === 'string' ? parseInt(value) : value
  return new Intl.NumberFormat('zh-TW').format(num)
}

// Quick actions
const createRequisition = () => {
  router.push('/requisitions/create')
}

const buildPO = () => {
  router.push('/purchase-orders/build-candidates')
}

const queryInventory = () => {
  router.push('/inventory')
}

const manageReceiving = () => {
  router.push('/receiving')
}

// Lifecycle
onMounted(async () => {
  await fetchDashboardData()

  // Auto refresh every 3 minutes for personalized data
  const refreshInterval = setInterval(fetchDashboardData, 3 * 60 * 1000)

  onUnmounted(() => {
    clearInterval(refreshInterval)
  })
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.dashboard-stats {
  margin-bottom: 20px;
}

.dashboard-content {
  min-height: 500px;
}

.dashboard-charts {
  .items-card {
    margin-bottom: 20px;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      span {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 500;
      }
    }

    .items-list {
      .empty-state {
        padding: 20px;
        text-align: center;
      }

      .item-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #f0f2f5;

        &:last-child {
          border-bottom: none;
        }

        .item-info {
          flex: 1;

          .item-title {
            font-size: 14px;
            font-weight: 500;
            color: #303133;
            margin-bottom: 4px;
          }

          .item-meta {
            font-size: 12px;
            color: #909399;

            .separator {
              margin: 0 8px;
              color: #dcdfe6;
            }
          }
        }

        .item-action {
          flex-shrink: 0;
        }
      }
    }
  }

  .chart-card {
    .chart-container {
      height: 300px;
    }
  }
}

.status-stats {
  .status-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #f0f2f5;
    
    &:last-child {
      border-bottom: none;
    }
    
    .status-info {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .status-name {
        font-size: 14px;
        color: #606266;
      }
    }
    
    .status-count {
      font-size: 18px;
      font-weight: 600;
      color: #303133;
    }
  }
}

.dashboard-sidebar {
  .quick-actions {
    display: flex;
    flex-direction: column;
    gap: 12px;
    
    .el-button {
      justify-content: flex-start;
    }
  }
}

.activity-content {
  .activity-title {
    font-size: 14px;
    font-weight: 500;
    color: #303133;
    margin-bottom: 4px;
  }
  
  .activity-description {
    font-size: 12px;
    color: #909399;
  }
}

.no-activities {
  text-align: center;
  padding: 20px;
}

.notifications {
  .notification-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid #f0f2f5;
    
    &:last-child {
      border-bottom: none;
    }
    
    .el-icon {
      margin-top: 2px;
    }
    
    &.notification-warning .el-icon {
      color: #e6a23c;
    }
    
    &.notification-info .el-icon {
      color: #409eff;
    }
    
    &.notification-success .el-icon {
      color: #67c23a;
    }
    
    &.notification-error .el-icon {
      color: #f56c6c;
    }
  }
  
  .notification-content {
    flex: 1;
    
    .notification-title {
      font-size: 14px;
      color: #303133;
      margin-bottom: 4px;
    }
    
    .notification-time {
      font-size: 12px;
      color: #909399;
    }
  }
}

.no-notifications {
  text-align: center;
  padding: 20px;
  color: #909399;
  font-size: 14px;
}

/* Responsive */
@media (max-width: 768px) {
  .dashboard-stats {
    .el-col {
      margin-bottom: 16px;
    }
  }
  
  .dashboard-sidebar {
    margin-top: 20px;
  }
}
</style>