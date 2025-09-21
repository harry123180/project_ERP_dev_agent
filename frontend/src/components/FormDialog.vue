<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    :width="width"
    :fullscreen="fullscreen"
    :center="center"
    :close-on-click-modal="closeOnClickModal"
    :close-on-press-escape="closeOnPressEscape"
    :show-close="showClose"
    :before-close="handleBeforeClose"
    destroy-on-close
    @closed="handleClosed"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      :label-width="labelWidth"
      :label-position="labelPosition"
      :size="size"
      @submit.prevent="handleSubmit"
    >
      <el-row :gutter="20">
        <el-col
          v-for="field in visibleFields"
          :key="field.prop"
          :span="field.span || 24"
          :offset="field.offset"
        >
          <el-form-item
            :label="field.label"
            :prop="field.prop"
            :required="field.required"
          >
            <!-- Input -->
            <el-input
              v-if="field.type === 'input'"
              v-model="formData[field.prop]"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              :readonly="field.readonly"
              :clearable="field.clearable !== false"
              :maxlength="field.maxlength"
              :show-word-limit="field.showWordLimit"
              v-bind="field.props"
            />

            <!-- Textarea -->
            <el-input
              v-else-if="field.type === 'textarea'"
              v-model="formData[field.prop]"
              type="textarea"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              :readonly="field.readonly"
              :rows="field.rows || 3"
              :maxlength="field.maxlength"
              :show-word-limit="field.showWordLimit"
              v-bind="field.props"
            />

            <!-- Number -->
            <el-input-number
              v-else-if="field.type === 'number'"
              v-model="formData[field.prop]"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              :min="field.props?.min"
              :max="field.props?.max"
              :precision="field.props?.precision"
              :step="field.props?.step || 1"
              :controls-position="field.props?.controlsPosition"
              style="width: 100%"
              v-bind="field.props"
            />

            <!-- Select -->
            <el-select
              v-else-if="field.type === 'select'"
              v-model="formData[field.prop]"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              :clearable="field.clearable !== false"
              :filterable="field.filterable"
              :multiple="field.multiple"
              :loading="field.props?.loading"
              style="width: 100%"
              v-bind="field.props"
            >
              <el-option
                v-for="option in field.options"
                :key="option.value"
                :label="option.label"
                :value="option.value"
                :disabled="option.disabled"
              />
            </el-select>

            <!-- Cascader -->
            <el-cascader
              v-else-if="field.type === 'cascader'"
              v-model="formData[field.prop]"
              :options="field.options"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              :clearable="field.clearable !== false"
              :filterable="field.filterable"
              style="width: 100%"
              v-bind="field.props"
            />

            <!-- Date -->
            <el-date-picker
              v-else-if="field.type === 'date'"
              v-model="formData[field.prop]"
              type="date"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              :clearable="field.clearable !== false"
              :format="field.props?.format || 'YYYY-MM-DD'"
              :value-format="field.props?.valueFormat || 'YYYY-MM-DD'"
              style="width: 100%"
              v-bind="field.props"
            />

            <!-- DateTime -->
            <el-date-picker
              v-else-if="field.type === 'datetime'"
              v-model="formData[field.prop]"
              type="datetime"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              :clearable="field.clearable !== false"
              :format="field.props?.format || 'YYYY-MM-DD HH:mm:ss'"
              :value-format="field.props?.valueFormat || 'YYYY-MM-DD HH:mm:ss'"
              style="width: 100%"
              v-bind="field.props"
            />

            <!-- Switch -->
            <el-switch
              v-else-if="field.type === 'switch'"
              v-model="formData[field.prop]"
              :disabled="field.disabled"
              v-bind="field.props"
            />

            <!-- Checkbox -->
            <el-checkbox-group
              v-else-if="field.type === 'checkbox'"
              v-model="formData[field.prop]"
              :disabled="field.disabled"
              v-bind="field.props"
            >
              <el-checkbox
                v-for="option in field.options"
                :key="option.value"
                :label="option.value"
                :disabled="option.disabled"
              >
                {{ option.label }}
              </el-checkbox>
            </el-checkbox-group>

            <!-- Radio -->
            <el-radio-group
              v-else-if="field.type === 'radio'"
              v-model="formData[field.prop]"
              :disabled="field.disabled"
              v-bind="field.props"
            >
              <el-radio
                v-for="option in field.options"
                :key="option.value"
                :label="option.value"
                :disabled="option.disabled"
              >
                {{ option.label }}
              </el-radio>
            </el-radio-group>

            <!-- Custom slot -->
            <slot
              v-else-if="field.type === 'slot'"
              :name="field.prop"
              :field="field"
              :value="formData[field.prop]"
              :setValue="(value: any) => formData[field.prop] = value"
            />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <slot name="footer" :submit="handleSubmit" :cancel="handleCancel">
          <el-button @click="handleCancel">
            {{ cancelText }}
          </el-button>
          <el-button
            type="primary"
            :loading="submitting"
            @click="handleSubmit"
          >
            {{ confirmText }}
          </el-button>
        </slot>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import type { FormInstance } from 'element-plus'
import type { FormField } from '@/types/ui'

interface Props {
  // Dialog props
  visible?: boolean
  title?: string
  width?: string | number
  fullscreen?: boolean
  center?: boolean
  closeOnClickModal?: boolean
  closeOnPressEscape?: boolean
  showClose?: boolean
  
  // Form props
  fields: FormField[]
  data?: Record<string, any>
  rules?: Record<string, any>
  labelWidth?: string
  labelPosition?: 'left' | 'right' | 'top'
  size?: 'large' | 'default' | 'small'
  
  // Button text
  confirmText?: string
  cancelText?: string
  
  // Loading state
  submitting?: boolean
  
  // Conditional fields
  when?: (data: Record<string, any>) => boolean
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  title: '表單',
  width: '600px',
  fullscreen: false,
  center: false,
  closeOnClickModal: false,
  closeOnPressEscape: true,
  showClose: true,
  data: () => ({}),
  rules: () => ({}),
  labelWidth: '100px',
  labelPosition: 'right',
  size: 'default',
  confirmText: '確認',
  cancelText: '取消',
  submitting: false
})

interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'submit', data: Record<string, any>): void
  (e: 'cancel'): void
  (e: 'closed'): void
}

const emit = defineEmits<Emits>()

// Form ref
const formRef = ref<FormInstance>()

// Dialog visibility
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// Form data - deep clone to avoid mutations
const formData = ref<Record<string, any>>({})

// Form rules - combine default rules with field rules
const formRules = computed(() => {
  const rules: Record<string, any> = { ...props.rules }
  
  props.fields.forEach(field => {
    if (field.rules) {
      rules[field.prop] = field.rules
    } else if (field.required) {
      rules[field.prop] = [
        { required: true, message: `請輸入${field.label}`, trigger: 'blur' }
      ]
    }
  })
  
  return rules
})

// Visible fields (filtered by when condition)
const visibleFields = computed(() => {
  return props.fields.filter(field => {
    return !field.when || field.when(formData.value)
  })
})

// Watch for data changes
watch(() => props.data, (newData) => {
  formData.value = { ...newData }
}, { deep: true, immediate: true })

// Watch for dialog visibility changes
watch(() => props.visible, (visible) => {
  if (visible) {
    // Reset form when dialog opens
    nextTick(() => {
      formRef.value?.clearValidate()
    })
  }
})

// Handlers
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    emit('submit', { ...formData.value })
  } catch (error) {
    console.error('Form validation failed:', error)
  }
}

const handleCancel = () => {
  dialogVisible.value = false
  emit('cancel')
}

const handleBeforeClose = (done: () => void) => {
  // Could add confirmation dialog here if form is dirty
  done()
}

const handleClosed = () => {
  // Reset form data when dialog is closed
  formData.value = {}
  emit('closed')
}

// Expose form methods
defineExpose({
  validate: () => formRef.value?.validate(),
  validateField: (props: string | string[]) => formRef.value?.validateField(props),
  resetFields: () => formRef.value?.resetFields(),
  clearValidate: (props?: string | string[]) => formRef.value?.clearValidate(props),
  scrollToField: (prop: string) => formRef.value?.scrollToField(prop),
  getFormData: () => formData.value,
  setFormData: (data: Record<string, any>) => {
    formData.value = { ...data }
  }
})
</script>

<style scoped>
.dialog-footer {
  text-align: right;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-dialog) {
  border-radius: 8px;
}

:deep(.el-dialog__header) {
  padding: 20px 20px 10px;
  border-bottom: 1px solid #ebeef5;
}

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-dialog__footer) {
  padding: 10px 20px 20px;
  border-top: 1px solid #ebeef5;
}
</style>