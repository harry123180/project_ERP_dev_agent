<template>
  <div class="page-header">
    <div class="page-header-content">
      <!-- Left side -->
      <div class="page-header-left">
        <div class="page-title">
          <el-button
            v-if="showBack"
            type="text"
            :icon="ArrowLeft"
            @click="handleBack"
          />
          <h2>{{ title }}</h2>
          <el-tag
            v-if="badge"
            :type="badgeType"
            size="small"
          >
            {{ badge }}
          </el-tag>
        </div>
        <div v-if="subtitle" class="page-subtitle">
          {{ subtitle }}
        </div>
      </div>
      
      <!-- Right side -->
      <div v-if="$slots.extra || showRefresh" class="page-header-right">
        <slot name="extra" />
        <el-button
          v-if="showRefresh"
          :icon="Refresh"
          @click="handleRefresh"
        />
      </div>
    </div>
    
    <!-- Tabs -->
    <div v-if="tabs && tabs.length > 0" class="page-tabs">
      <el-tabs
        :model-value="activeTab"
        @tab-click="handleTabClick"
      >
        <el-tab-pane
          v-for="tab in tabs"
          :key="tab.name"
          :name="tab.name"
          :disabled="tab.disabled"
        >
          <template #label>
            <span class="tab-label">
              {{ tab.label }}
              <el-badge
                v-if="tab.count !== undefined"
                :value="tab.count"
                :max="99"
                :show-zero="false"
                class="tab-badge"
              />
            </span>
          </template>
        </el-tab-pane>
      </el-tabs>
    </div>
    
    <!-- Breadcrumb -->
    <div v-if="breadcrumb && breadcrumb.length > 0" class="page-breadcrumb">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item
          v-for="(item, index) in breadcrumb"
          :key="index"
          :to="item.to"
        >
          {{ item.text }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    
    <!-- Description -->
    <div v-if="description" class="page-description">
      <p>{{ description }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowLeft, Refresh } from '@element-plus/icons-vue'
import type { TabsPaneContext } from 'element-plus'
import type { BreadcrumbItem, TabItem, StatusType } from '@/types'

interface Props {
  title: string
  subtitle?: string
  description?: string
  badge?: string | number
  badgeType?: StatusType
  showBack?: boolean
  showRefresh?: boolean
  breadcrumb?: BreadcrumbItem[]
  tabs?: TabItem[]
  activeTab?: string
}

const props = withDefaults(defineProps<Props>(), {
  badgeType: 'info',
  showBack: false,
  showRefresh: false
})

interface Emits {
  (e: 'back'): void
  (e: 'refresh'): void
  (e: 'tab-change', tab: string): void
}

const emit = defineEmits<Emits>()

const handleBack = () => {
  emit('back')
}

const handleRefresh = () => {
  emit('refresh')
}

const handleTabClick = (tab: TabsPaneContext) => {
  emit('tab-change', tab.paneName as string)
}
</script>

<style scoped>
.page-header {
  background: white;
  padding: 16px 24px;
  margin-bottom: 16px;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.page-header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.page-header-left {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.page-title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.page-subtitle {
  color: #909399;
  font-size: 14px;
  margin-bottom: 8px;
}

.page-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-breadcrumb {
  margin-bottom: 12px;
}

.page-tabs {
  margin-top: 16px;
  border-top: 1px solid #ebeef5;
  padding-top: 0;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-description {
  margin-top: 8px;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.page-description p {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

:deep(.el-tabs__header) {
  margin-bottom: 0;
}

:deep(.el-tabs__nav-wrap::after) {
  display: none;
}

:deep(.el-badge) {
  .el-badge__content {
    font-size: 10px;
    height: 16px;
    line-height: 16px;
    padding: 0 4px;
    min-width: 16px;
  }
}
</style>