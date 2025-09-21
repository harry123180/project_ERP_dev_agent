<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    width="400px"
    center
    :show-close="showClose"
    :close-on-click-modal="closeOnClickModal"
    :close-on-press-escape="closeOnPressEscape"
    destroy-on-close
  >
    <div class="confirm-content">
      <!-- Icon -->
      <div class="confirm-icon">
        <el-icon :size="48" :color="iconColor">
          <component :is="iconType" />
        </el-icon>
      </div>
      
      <!-- Message -->
      <div class="confirm-message">
        <div class="message-title">{{ message }}</div>
        <div v-if="description" class="message-description">
          {{ description }}
        </div>
      </div>
    </div>
    
    <!-- Input for reason (if required) -->
    <div v-if="requireReason" class="confirm-input">
      <el-input
        v-model="reason"
        type="textarea"
        :placeholder="reasonPlaceholder"
        :rows="3"
        maxlength="200"
        show-word-limit
      />
    </div>
    
    <template #footer>
      <div class="confirm-footer">
        <el-button @click="handleCancel">
          {{ cancelText }}
        </el-button>
        <el-button
          :type="confirmButtonType"
          :loading="loading"
          :disabled="requireReason && !reason.trim()"
          @click="handleConfirm"
        >
          {{ confirmText }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  QuestionFilled,
  InfoFilled,
  WarningFilled,
  CircleCheckFilled,
  CircleCloseFilled
} from '@element-plus/icons-vue'

interface Props {
  visible?: boolean
  type?: 'info' | 'success' | 'warning' | 'error' | 'confirm'
  title?: string
  message: string
  description?: string
  confirmText?: string
  cancelText?: string
  showClose?: boolean
  closeOnClickModal?: boolean
  closeOnPressEscape?: boolean
  loading?: boolean
  requireReason?: boolean
  reasonPlaceholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  type: 'confirm',
  title: '確認',
  confirmText: '確認',
  cancelText: '取消',
  showClose: true,
  closeOnClickModal: false,
  closeOnPressEscape: true,
  loading: false,
  requireReason: false,
  reasonPlaceholder: '請輸入原因...'
})

interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'confirm', reason?: string): void
  (e: 'cancel'): void
}

const emit = defineEmits<Emits>()

// Reason input
const reason = ref('')

// Dialog visibility
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// Icon configuration
const iconConfig = computed(() => {
  const configs = {
    info: {
      icon: InfoFilled,
      color: '#409eff'
    },
    success: {
      icon: CircleCheckFilled,
      color: '#67c23a'
    },
    warning: {
      icon: WarningFilled,
      color: '#e6a23c'
    },
    error: {
      icon: CircleCloseFilled,
      color: '#f56c6c'
    },
    confirm: {
      icon: QuestionFilled,
      color: '#e6a23c'
    }
  }
  
  return configs[props.type]
})

const iconType = computed(() => iconConfig.value.icon)
const iconColor = computed(() => iconConfig.value.color)

// Button type
const confirmButtonType = computed(() => {
  const typeMap = {
    info: 'primary',
    success: 'success',
    warning: 'warning',
    error: 'danger',
    confirm: 'primary'
  }
  
  return typeMap[props.type] as 'primary' | 'success' | 'warning' | 'danger'
})

// Handlers
const handleConfirm = () => {
  const reasonValue = props.requireReason ? reason.value.trim() : undefined
  emit('confirm', reasonValue)
  
  if (!props.loading) {
    dialogVisible.value = false
    reason.value = ''
  }
}

const handleCancel = () => {
  dialogVisible.value = false
  reason.value = ''
  emit('cancel')
}
</script>

<style scoped>
.confirm-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 20px 0;
}

.confirm-icon {
  margin-bottom: 20px;
}

.confirm-message {
  max-width: 300px;
}

.message-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
  line-height: 1.4;
}

.message-description {
  font-size: 14px;
  color: #606266;
  line-height: 1.4;
}

.confirm-input {
  margin-top: 20px;
}

.confirm-footer {
  display: flex;
  justify-content: center;
  gap: 12px;
}

:deep(.el-dialog) {
  border-radius: 8px;
}

:deep(.el-dialog__body) {
  padding: 20px 24px;
}

:deep(.el-dialog__footer) {
  padding: 0 24px 24px;
}
</style>