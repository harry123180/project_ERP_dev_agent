<template>
  <div class="po-settings">
    <div class="page-header">
      <h1 class="page-title">採購單資訊設定</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showAddTemplateDialog">
          <el-icon><Plus /></el-icon>
          新增模板
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="注意事項模板" name="terms">
        <div class="settings-section">
          <div class="section-header">
            <h3>注意事項模板管理</h3>
            <p class="section-desc">設定採購單輸出時可選擇的注意事項模板</p>
          </div>

          <el-table :data="termsTemplates" stripe style="width: 100%">
            <el-table-column prop="name" label="模板名稱" width="200" />
            <el-table-column prop="description" label="說明" min-width="200" />
            <el-table-column label="內容預覽" min-width="300">
              <template #default="scope">
                <div class="content-preview">{{ truncateContent(scope.row.content) }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="is_default" label="預設" width="80" align="center">
              <template #default="scope">
                <el-tag v-if="scope.row.is_default" type="success">預設</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="scope">
                <el-button size="small" @click="editTemplate(scope.row)">編輯</el-button>
                <el-button 
                  size="small" 
                  type="primary" 
                  @click="setAsDefault(scope.row)"
                  :disabled="scope.row.is_default"
                >
                  設為預設
                </el-button>
                <el-button 
                  size="small" 
                  type="danger" 
                  @click="deleteTemplate(scope.row)"
                  :disabled="scope.row.is_system"
                >
                  刪除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="公司資訊" name="company">
        <div class="settings-section">
          <div class="section-header">
            <h3>公司資訊設定</h3>
            <p class="section-desc">設定採購單上顯示的公司資訊</p>
          </div>

          <el-form 
            ref="companyFormRef"
            :model="companyInfo" 
            label-width="120px"
            style="max-width: 600px"
          >
            <el-form-item label="公司名稱" prop="name" required>
              <el-input v-model="companyInfo.name" placeholder="請輸入公司名稱" />
            </el-form-item>
            <el-form-item label="公司地址" prop="address" required>
              <el-input v-model="companyInfo.address" placeholder="請輸入公司地址" />
            </el-form-item>
            <el-form-item label="聯絡電話" prop="phone">
              <el-input v-model="companyInfo.phone" placeholder="請輸入聯絡電話" />
            </el-form-item>
            <el-form-item label="傳真號碼" prop="fax">
              <el-input v-model="companyInfo.fax" placeholder="請輸入傳真號碼" />
            </el-form-item>
            <el-form-item label="統一編號" prop="tax_id">
              <el-input v-model="companyInfo.tax_id" placeholder="請輸入統一編號" />
            </el-form-item>
            <el-form-item label="電子郵件" prop="email">
              <el-input v-model="companyInfo.email" placeholder="請輸入電子郵件" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveCompanyInfo">儲存公司資訊</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- Template Edit Dialog -->
    <el-dialog 
      v-model="templateDialogVisible" 
      :title="templateDialogTitle"
      width="800px"
    >
      <el-form 
        ref="templateFormRef"
        :model="currentTemplate" 
        label-width="100px"
      >
        <el-form-item label="模板名稱" prop="name" required>
          <el-input 
            v-model="currentTemplate.name" 
            placeholder="請輸入模板名稱"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="說明" prop="description">
          <el-input 
            v-model="currentTemplate.description" 
            placeholder="請輸入模板說明"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="模板內容" prop="content" required>
          <el-input
            v-model="currentTemplate.content"
            type="textarea"
            :rows="12"
            placeholder="請輸入注意事項內容，可使用以下變數：
{company_name} - 公司名稱
{order_date} - 訂購日期
{delivery_days} - 交貨天數"
          />
        </el-form-item>
        <el-form-item label="設為預設" prop="is_default">
          <el-switch v-model="currentTemplate.is_default" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="templateDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveTemplate">儲存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/api'

interface TermsTemplate {
  id?: number
  name: string
  description?: string
  content: string
  is_default?: boolean
  is_system?: boolean
}

interface CompanyInfo {
  name: string
  address: string
  phone?: string
  fax?: string
  tax_id?: string
  email?: string
}

const activeTab = ref('terms')
const termsTemplates = ref<TermsTemplate[]>([])
const templateDialogVisible = ref(false)
const templateDialogTitle = ref('新增模板')
const currentTemplate = ref<TermsTemplate>({
  name: '',
  content: '',
  is_default: false
})

const companyInfo = ref<CompanyInfo>({
  name: 'Taiwan Semiconductor Innovation Company',
  address: '台北市信義區信義路五段7號',
  phone: '02-8101-2345',
  fax: '',
  tax_id: '',
  email: ''
})

const companyFormRef = ref()
const templateFormRef = ref()

onMounted(() => {
  loadTermsTemplates()
  loadCompanyInfo()
})

const loadTermsTemplates = async () => {
  try {
    // Load from localStorage for now (later will use API)
    const saved = localStorage.getItem('po_terms_templates')
    if (saved) {
      termsTemplates.value = JSON.parse(saved)
    } else {
      // Default templates
      termsTemplates.value = [
        {
          id: 1,
          name: '標準條款',
          description: '一般採購單使用的標準注意事項',
          content: `1. 付款條件：月結 30 天
2. 交貨期限：訂單確認後 14 個工作天
3. 品質要求：須符合國家標準規範
4. 驗收標準：貨到 7 日內完成驗收
5. 保固期限：自驗收合格日起算一年
6. 退換貨規定：如有品質問題，可於驗收後 30 日內申請退換貨
7. 發票開立：請於出貨時一併開立統一發票`,
          is_default: true,
          is_system: true
        },
        {
          id: 2,
          name: '急件條款',
          description: '用於急件採購的注意事項',
          content: `1. 付款條件：貨到付款
2. 交貨期限：訂單確認後 3 個工作天內
3. 品質要求：須符合國家標準規範
4. 驗收標準：貨到當日完成驗收
5. 保固期限：自驗收合格日起算一年
6. 急件處理：需優先處理並確保準時交貨
7. 延遲罰則：每延遲一日扣款總金額 1%`,
          is_default: false,
          is_system: true
        }
      ]
      saveTemplatesLocal()
    }
  } catch (error) {
    console.error('Failed to load templates:', error)
  }
}

const loadCompanyInfo = async () => {
  try {
    // Load from localStorage for now (later will use API)
    const saved = localStorage.getItem('po_company_info')
    if (saved) {
      companyInfo.value = JSON.parse(saved)
    }
  } catch (error) {
    console.error('Failed to load company info:', error)
  }
}

const saveTemplatesLocal = () => {
  localStorage.setItem('po_terms_templates', JSON.stringify(termsTemplates.value))
}

const showAddTemplateDialog = () => {
  currentTemplate.value = {
    name: '',
    content: '',
    is_default: false
  }
  templateDialogTitle.value = '新增模板'
  templateDialogVisible.value = true
}

const editTemplate = (template: TermsTemplate) => {
  currentTemplate.value = { ...template }
  templateDialogTitle.value = '編輯模板'
  templateDialogVisible.value = true
}

const saveTemplate = async () => {
  if (!currentTemplate.value.name || !currentTemplate.value.content) {
    ElMessage.warning('請填寫必要欄位')
    return
  }

  try {
    if (currentTemplate.value.id) {
      // Update existing
      const index = termsTemplates.value.findIndex(t => t.id === currentTemplate.value.id)
      if (index !== -1) {
        termsTemplates.value[index] = { ...currentTemplate.value }
      }
    } else {
      // Add new
      currentTemplate.value.id = Date.now()
      termsTemplates.value.push({ ...currentTemplate.value })
    }

    // If set as default, unset others
    if (currentTemplate.value.is_default) {
      termsTemplates.value.forEach(t => {
        if (t.id !== currentTemplate.value.id) {
          t.is_default = false
        }
      })
    }

    saveTemplatesLocal()
    ElMessage.success('模板儲存成功')
    templateDialogVisible.value = false
  } catch (error) {
    ElMessage.error('儲存模板失敗')
  }
}

const setAsDefault = async (template: TermsTemplate) => {
  try {
    termsTemplates.value.forEach(t => {
      t.is_default = t.id === template.id
    })
    saveTemplatesLocal()
    ElMessage.success('已設為預設模板')
  } catch (error) {
    ElMessage.error('設定失敗')
  }
}

const deleteTemplate = async (template: TermsTemplate) => {
  try {
    await ElMessageBox.confirm(
      `確定要刪除模板「${template.name}」嗎？`,
      '確認刪除',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const index = termsTemplates.value.findIndex(t => t.id === template.id)
    if (index !== -1) {
      termsTemplates.value.splice(index, 1)
      saveTemplatesLocal()
      ElMessage.success('模板已刪除')
    }
  } catch (error) {
    // User cancelled
  }
}

const saveCompanyInfo = async () => {
  try {
    // Save to localStorage for now (later will use API)
    localStorage.setItem('po_company_info', JSON.stringify(companyInfo.value))
    ElMessage.success('公司資訊已儲存')
  } catch (error) {
    ElMessage.error('儲存失敗')
  }
}

const truncateContent = (content: string) => {
  const lines = content.split('\n')
  const preview = lines.slice(0, 2).join(' | ')
  return preview.length > 100 ? preview.substring(0, 100) + '...' : preview
}
</script>

<style scoped lang="scss">
.po-settings {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .page-title {
    margin: 0;
    font-size: 24px;
    color: #303133;
  }

  .header-actions {
    display: flex;
    gap: 10px;
  }
}

.settings-section {
  background: white;
  padding: 20px;
  border-radius: 4px;

  .section-header {
    margin-bottom: 20px;
    
    h3 {
      margin: 0 0 5px 0;
      font-size: 18px;
      color: #303133;
    }
    
    .section-desc {
      margin: 0;
      color: #909399;
      font-size: 14px;
    }
  }
}

.content-preview {
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dialog-footer {
  display: flex;
  gap: 10px;
}
</style>