#!/usr/bin/env python3
"""
Update Form.vue to add urgent functionality
"""

def update_form_vue():
    file_path = "/d/AWORKSPACE/Github/project_ERP_dev_agent/frontend/src/views/requisitions/Form.vue"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find where to insert urgent section - after the project selection row
    project_row_end = '</el-row>'
    first_end_row = content.find(project_row_end)
    if first_end_row != -1:
        # Add urgent settings section after the first </el-row>
        urgent_section = '''

        <!-- 加急設定區塊 -->
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="加急設定">
              <el-checkbox
                v-model="formData.is_urgent"
                @change="onUrgentChange"
                class="urgent-checkbox"
              >
                <span class="urgent-label">此為加急請購單</span>
              </el-checkbox>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 加急詳細資訊區塊 -->
        <div v-if="formData.is_urgent" class="urgent-details">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item
                label="期望到貨日期"
                prop="expected_delivery_date"
                required
              >
                <el-date-picker
                  v-model="formData.expected_delivery_date"
                  type="date"
                  placeholder="選擇期望到貨日期"
                  format="YYYY/MM/DD"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                  :disabled-date="disabledDate"
                  class="urgent-date-picker"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item
                label="加急原因"
                prop="urgent_reason"
                required
              >
                <el-input
                  v-model="formData.urgent_reason"
                  type="textarea"
                  :rows="3"
                  placeholder="請詳細說明加急原因"
                  maxlength="200"
                  show-word-limit
                  class="urgent-reason-input"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>'''

        content = content[:first_end_row + len(project_row_end)] + urgent_section + content[first_end_row + len(project_row_end):]

    # Add urgent fields to formData interface in the script section
    script_start = content.find('<script setup lang="ts">')
    if script_start != -1:
        # Find formData reactive definition
        formdata_start = content.find('const formData = reactive({')
        if formdata_start != -1:
            # Find the closing brace of formData
            formdata_end = content.find('})', formdata_start)
            if formdata_end != -1:
                # Insert urgent fields before the closing brace
                urgent_fields = '''  // 加急相關欄位
  is_urgent: false,
  expected_delivery_date: '',
  urgent_reason: '',
'''
                content = content[:formdata_end] + urgent_fields + content[formdata_end:]

    # Add methods for urgent functionality
    methods_to_add = '''

// 加急功能相關方法
const onUrgentChange = (isUrgent: boolean) => {
  if (!isUrgent) {
    // 取消加急時清空相關欄位
    formData.expected_delivery_date = ''
    formData.urgent_reason = ''
  }
}

const disabledDate = (time: Date) => {
  // 禁用今天之前的日期
  return time.getTime() < Date.now() - 8.64e7
}'''

    # Find a good place to insert methods (before the last export or at the end of script)
    last_function_end = content.rfind('}')
    if last_function_end != -1 and last_function_end > script_start:
        content = content[:last_function_end] + methods_to_add + '\n' + content[last_function_end:]

    # Add styles for urgent elements
    style_section = '''

/* 加急設定樣式 */
.urgent-details {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 6px;
  padding: 16px;
  margin-top: 16px;
}

.urgent-details .el-form-item__label {
  color: #cf1322;
  font-weight: 600;
}

.urgent-checkbox .urgent-label {
  color: #cf1322;
  font-weight: 600;
}

.urgent-date-picker :deep(.el-input__inner) {
  border-color: #ff7875;
}

.urgent-date-picker :deep(.el-input__inner:focus) {
  border-color: #cf1322;
  box-shadow: 0 0 0 2px rgba(207, 19, 34, 0.2);
}

.urgent-reason-input :deep(.el-textarea__inner) {
  border-color: #ff7875;
}

.urgent-reason-input :deep(.el-textarea__inner:focus) {
  border-color: #cf1322;
  box-shadow: 0 0 0 2px rgba(207, 19, 34, 0.2);
}'''

    # Find the style section and add urgent styles
    style_start = content.rfind('<style scoped>')
    if style_start != -1:
        style_end = content.find('</style>', style_start)
        if style_end != -1:
            content = content[:style_end] + style_section + '\n' + content[style_end:]

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✓ Updated Form.vue with urgent functionality")

if __name__ == "__main__":
    update_form_vue()