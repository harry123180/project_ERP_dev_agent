<template>
  <el-tag
    :type="tagType"
    :size="size"
    :effect="effect"
    :closable="closable"
    :disable-transitions="disableTransitions"
    :hit="hit"
    :color="customColor"
    :round="round"
    @close="$emit('close')"
    @click="$emit('click')"
  >
    <el-icon v-if="icon" :size="iconSize">
      <component :is="icon" />
    </el-icon>
    {{ displayText }}
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { StatusType } from '@/types/ui'
import { STATUS_LABELS, STATUS_TYPES } from '@/types/common'

interface Props {
  status: string
  size?: 'large' | 'default' | 'small'
  effect?: 'dark' | 'light' | 'plain'
  closable?: boolean
  disableTransitions?: boolean
  hit?: boolean
  color?: string
  round?: boolean
  icon?: string
  showText?: boolean
  customLabels?: Record<string, string>
  customTypes?: Record<string, StatusType>
}

const props = withDefaults(defineProps<Props>(), {
  size: 'default',
  effect: 'light',
  closable: false,
  disableTransitions: false,
  hit: false,
  round: false,
  showText: true
})

interface Emits {
  (e: 'close'): void
  (e: 'click'): void
}

const emit = defineEmits<Emits>()

// Computed properties
const tagType = computed((): StatusType => {
  if (props.customTypes && props.customTypes[props.status]) {
    return props.customTypes[props.status]
  }
  return STATUS_TYPES[props.status] || ''
})

const displayText = computed(() => {
  if (!props.showText) return ''
  
  if (props.customLabels && props.customLabels[props.status]) {
    return props.customLabels[props.status]
  }
  
  return STATUS_LABELS[props.status] || props.status
})

const customColor = computed(() => {
  return props.color || undefined
})

const iconSize = computed(() => {
  const sizeMap = {
    large: 16,
    default: 14,
    small: 12
  }
  return sizeMap[props.size]
})
</script>

<style scoped>
.el-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.el-tag:hover {
  opacity: 0.8;
}

.el-tag .el-icon {
  margin-right: 4px;
}
</style>