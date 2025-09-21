<template>
  <el-card
    class="stat-card"
    :class="[
      `stat-card--${color}`,
      { 'stat-card--loading': loading }
    ]"
    :body-style="{ padding: '20px' }"
  >
    <div class="stat-card-content">
      <!-- Icon -->
      <div v-if="icon" class="stat-icon">
        <el-icon :size="iconSize">
          <component :is="icon" />
        </el-icon>
      </div>
      
      <!-- Main content -->
      <div class="stat-main">
        <div class="stat-value">
          <el-skeleton v-if="loading" :rows="1" animated />
          <template v-else>
            <span class="stat-number">{{ formattedValue }}</span>
            <span v-if="unit" class="stat-unit">{{ unit }}</span>
          </template>
        </div>
        
        <div class="stat-title">
          <el-skeleton v-if="loading" :rows="1" animated />
          <template v-else>
            {{ title }}
          </template>
        </div>
        
        <!-- Trend -->
        <div v-if="trend && !loading" class="stat-trend">
          <el-icon
            :class="[
              'trend-icon',
              trend.isUp ? 'trend-up' : 'trend-down'
            ]"
            :size="12"
          >
            <ArrowUp v-if="trend.isUp" />
            <ArrowDown v-else />
          </el-icon>
          <span class="trend-value">
            {{ Math.abs(trend.value) }}%
          </span>
          <span class="trend-text">較上期</span>
        </div>
      </div>
      
      <!-- Extra content -->
      <div v-if="$slots.extra" class="stat-extra">
        <slot name="extra" />
      </div>
    </div>
    
    <!-- Footer -->
    <div v-if="$slots.footer" class="stat-footer">
      <slot name="footer" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowUp, ArrowDown } from '@element-plus/icons-vue'

interface Props {
  title: string
  value: string | number
  unit?: string
  icon?: string
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  loading?: boolean
  trend?: {
    value: number
    isUp: boolean
  }
  precision?: number
  formatter?: (value: string | number) => string
}

const props = withDefaults(defineProps<Props>(), {
  color: 'primary',
  loading: false,
  precision: 0
})

const formattedValue = computed(() => {
  if (props.loading) return ''
  
  if (props.formatter) {
    return props.formatter(props.value)
  }
  
  if (typeof props.value === 'number') {
    return props.value.toLocaleString('zh-TW', {
      minimumFractionDigits: props.precision,
      maximumFractionDigits: props.precision
    })
  }
  
  return props.value
})

const iconSize = computed(() => {
  return 24
})
</script>

<style scoped>
.stat-card {
  height: 100%;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-card--loading {
  opacity: 0.8;
}

.stat-card-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.stat-icon {
  padding: 12px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  height: 48px;
}

.stat-card--primary .stat-icon {
  background: rgba(64, 158, 255, 0.1);
  color: #409eff;
}

.stat-card--success .stat-icon {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
}

.stat-card--warning .stat-icon {
  background: rgba(230, 162, 60, 0.1);
  color: #e6a23c;
}

.stat-card--danger .stat-icon {
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
}

.stat-card--info .stat-icon {
  background: rgba(144, 147, 153, 0.1);
  color: #909399;
}

.stat-main {
  flex: 1;
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 8px;
}

.stat-number {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
}

.stat-unit {
  font-size: 14px;
  color: #909399;
  font-weight: normal;
}

.stat-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.trend-icon {
  border-radius: 50%;
  padding: 2px;
}

.trend-up {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
}

.trend-down {
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
}

.trend-value {
  font-weight: 600;
}

.trend-up .trend-value {
  color: #67c23a;
}

.trend-down .trend-value {
  color: #f56c6c;
}

.trend-text {
  color: #909399;
}

.stat-extra {
  min-width: max-content;
}

.stat-footer {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
  font-size: 12px;
  color: #909399;
}

/* Responsive */
@media (max-width: 768px) {
  .stat-card-content {
    flex-direction: column;
    gap: 12px;
  }
  
  .stat-icon {
    align-self: flex-start;
  }
  
  .stat-number {
    font-size: 24px;
  }
}
</style>