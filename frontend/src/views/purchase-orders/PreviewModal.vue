<template>
  <el-dialog
    v-model="dialogVisible"
    title="採購單預覽"
    width="1200px"
    :before-close="handleClose"
    class="po-preview-modal"
  >
    <div v-loading="loading" class="preview-container" :class="{ 'print-preview-mode': printPreviewMode }">
      <!-- Company Header with Logo -->
      <div class="company-header">
        <div class="logo-section">
          <img src="@/assets/TSIC_LOGO.png" alt="Company Logo" class="company-logo" />
        </div>
        <div class="header-center">
          <h1 class="title">採購單</h1>
          <h2 class="subtitle">PURCHASE ORDER</h2>
        </div>
        <div class="header-right">
          <!-- Status information -->
          <div class="status-info non-printable-section">
            <div class="status-badge" :class="{'outputted': poData.purchase_status === 'outputted', 'order-created': poData.purchase_status === 'order_created'}">
              {{ statusDisplay }}
            </div>
            <div v-if="exportHistoryDisplay" class="export-history">
              {{ exportHistoryDisplay }}
            </div>
          </div>
        </div>
      </div>

      <!-- Supplier and Order Info Table (4x4) -->
      <div class="info-table-section">
        <table class="info-table">
          <tr>
            <td class="label">廠商名稱</td>
            <td class="value">{{ poData.supplier_name }}</td>
            <td class="label">採購單號</td>
            <td class="value">{{ poData.purchase_order_no }}</td>
          </tr>
          <tr>
            <td class="label">廠商編號</td>
            <td class="value">{{ poData.supplier_id }}</td>
            <td class="label">訂購日期</td>
            <td class="value">{{ formatDate(poData.order_date) }}</td>
          </tr>
          <tr>
            <td class="label">廠商地址</td>
            <td class="value">{{ poData.supplier_address || '-' }}</td>
            <td class="label">報價單號</td>
            <td class="value">
              <el-input 
                v-model="poData.quotation_no" 
                size="small" 
                style="width: 150px"
                placeholder="請輸入"
                :disabled="isExporting"
              />
            </td>
          </tr>
          <tr>
            <td class="label">連絡電話</td>
            <td class="value">{{ poData.contact_phone || '-' }}</td>
            <td class="label">聯絡人</td>
            <td class="value">{{ poData.contact_person || '-' }}</td>
          </tr>
        </table>
      </div>

      <!-- Items Table -->
      <div class="section">
        <h3 class="section-title">採購明細 Purchase Items</h3>
        <el-table :data="itemsWithIndex" border style="width: 100%">
          <el-table-column prop="index" label="項次" width="60" align="center" />
          <el-table-column prop="item_name" label="品名" min-width="150" />
          <el-table-column prop="item_specification" label="規格" min-width="120">
            <template #default="scope">
              {{ scope.row.item_specification || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="item_model" label="型號" min-width="100">
            <template #default="scope">
              {{ scope.row.item_model || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="item_quantity" label="數量" width="80" align="right">
            <template #default="scope">
              {{ formatNumber(scope.row.item_quantity) }}
            </template>
          </el-table-column>
          <el-table-column prop="item_unit" label="單位" width="60" align="center" />
          <el-table-column prop="unit_price" label="單價" width="100" align="right">
            <template #default="scope">
              <span :class="{ 'print-currency': printPreviewMode }">
                {{ formatCurrency(scope.row.unit_price, !printPreviewMode) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="line_subtotal" label="小計" width="120" align="right">
            <template #default="scope">
              <span :class="{ 'print-currency': printPreviewMode }">
                {{ formatCurrency(scope.row.line_subtotal || scope.row.item_quantity * scope.row.unit_price, !printPreviewMode) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="備註" min-width="100">
            <template #default>
              -
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- Totals -->
      <div class="totals-section">
        <div class="total-row">
          <span class="label">小計 Subtotal：</span>
          <span class="value" :class="{ 'print-currency': printPreviewMode }">
            {{ formatCurrency(poData.subtotal_int, !printPreviewMode) }}
          </span>
        </div>
        <div class="total-row">
          <span class="label">稅額 Tax (5%)：</span>
          <span class="value" :class="{ 'print-currency': printPreviewMode }">
            {{ formatCurrency(poData.tax_decimal1, !printPreviewMode) }}
          </span>
        </div>
        <div class="total-row grand-total">
          <span class="label">總計 Total：</span>
          <span class="value" :class="{ 'print-currency': printPreviewMode }">
            {{ formatCurrency(poData.grand_total_int, !printPreviewMode) }}
          </span>
        </div>
      </div>

      <!-- Terms (Note) Section with Template Selection -->
      <div class="section terms-section">
        <h3 class="section-title">注意事項 Terms and Conditions</h3>
        <div class="terms-selector" v-if="!isExporting">
          <el-select 
            v-model="selectedTermsTemplate" 
            placeholder="選擇注意事項模板"
            size="small"
            style="width: 200px; margin-bottom: 10px"
            @change="loadTermsTemplate"
          >
            <el-option label="標準條款" value="standard" />
            <el-option label="急件條款" value="urgent" />
            <el-option label="自訂條款" value="custom" />
          </el-select>
        </div>
        <el-input
          v-model="termsContent"
          type="textarea"
          :rows="8"
          placeholder="請輸入注意事項內容"
          :disabled="isExporting"
        />
        <!-- Print-only terms content -->
        <div class="terms-print-content" style="display: none;">
          {{ termsContent }}
        </div>
      </div>

      <!-- Signature Area -->
      <div class="signature-section">
        <div class="signature-row">
          <div class="signature-item">
            <span class="label">採購人員：</span>
            <span class="signature-line"></span>
          </div>
          <div class="signature-item">
            <span class="label">核准主管：</span>
            <span class="signature-line"></span>
          </div>
        </div>
        <div class="signature-row">
          <div class="signature-item">
            <span class="label">日期：</span>
            <span class="signature-line"></span>
          </div>
          <div class="signature-item">
            <span class="label">日期：</span>
            <span class="signature-line"></span>
          </div>
        </div>
      </div>

      <!-- Below the Print/Export Area - Not included in export -->
      <div class="non-printable-section" v-if="!printPreviewMode">
        <div class="divider-line"></div>
        
        <!-- Delivery Information -->
        <div class="section">
          <h3 class="section-title">交貨資訊 Delivery Information</h3>
          <div class="delivery-info">
            <div class="info-row">
              <span class="label">交貨地址：</span>
              <span class="value">{{ poData.delivery_address || companyInfo.address }}</span>
            </div>
            <div class="info-row">
              <span class="label">預計交貨日期：</span>
              <span class="value">{{ poData.expected_delivery_date || '訂單確認後 14 個工作天' }}</span>
            </div>
          </div>
        </div>

        <!-- Full Supplier Information -->
        <div class="section supplier-section">
          <h3 class="section-title">供應商詳細資訊 Supplier Details</h3>
          <div class="supplier-info">
            <div class="supplier-row">
              <div class="info-item">
                <span class="label">廠商名稱：</span>
                <span class="value">{{ poData.supplier_name }}</span>
              </div>
              <div class="info-item">
                <span class="label">廠商編號：</span>
                <span class="value">{{ poData.supplier_id }}</span>
              </div>
            </div>
            <div class="supplier-row">
              <div class="info-item">
                <span class="label">廠商地址：</span>
                <span class="value">{{ poData.supplier_address || '-' }}</span>
              </div>
            </div>
            <div class="supplier-row">
              <div class="info-item">
                <span class="label">連絡電話：</span>
                <span class="value">{{ poData.contact_phone || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="label">聯絡人：</span>
                <span class="value">{{ poData.contact_person || '-' }}</span>
              </div>
            </div>
            <div class="supplier-row">
              <div class="info-item">
                <span class="label">統一編號：</span>
                <span class="value">{{ poData.supplier_tax_id || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="label">電子郵件：</span>
                <span class="value">{{ poData.supplier_email || '-' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">關閉</el-button>
        <el-button @click="togglePrintPreview" :type="printPreviewMode ? 'warning' : 'info'">
          {{ printPreviewMode ? '返回編輯模式' : '列印預覽模式' }}
        </el-button>
        <el-button 
          type="primary" 
          @click="handleExport('excel')" 
          :loading="exporting"
          :disabled="!canExport"
          :title="!canExport ? `採購單狀態為「${statusDisplay}」，無法輸出` : ''"
        >
          <el-icon><Download /></el-icon>
          輸出 Excel
        </el-button>
        <el-button 
          type="primary" 
          @click="handleExport('pdf')" 
          :loading="exporting"
          :disabled="!canExport"
          :title="!canExport ? `採購單狀態為「${statusDisplay}」，無法輸出` : ''"
        >
          <el-icon><Document /></el-icon>
          輸出 PDF
        </el-button>
        <el-button 
          type="primary" 
          @click="handlePrint" 
          :loading="printing"
          :disabled="!canExport"
          :title="!canExport ? `採購單狀態為「${statusDisplay}」，無法列印` : ''"
        >
          <el-icon><Printer /></el-icon>
          列印
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Document, Printer } from '@element-plus/icons-vue'
import { procurementApi } from '@/api/procurement'
import { downloadFromAPI } from '@/utils/download'

interface POPreviewData {
  purchase_order_no: string
  supplier_id: string
  supplier_name: string
  supplier_address?: string
  contact_person?: string
  contact_phone?: string
  supplier_tax_id?: string
  supplier_email?: string
  order_date?: string
  quotation_no?: string
  delivery_address?: string
  expected_delivery_date?: string
  notes?: string
  purchase_status?: string
  last_export_at?: string
  export_count?: number
  subtotal_int: number
  tax_decimal1: number
  grand_total_int: number
  items: Array<{
    item_name: string
    item_specification?: string
    item_model?: string
    item_quantity: number
    item_unit: string
    unit_price: number
    line_subtotal?: number
  }>
}

const props = defineProps<{
  visible: boolean
  poNo: string
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'exported': []
}>()

const dialogVisible = ref(false)
const loading = ref(false)
const exporting = ref(false)
const printing = ref(false)
const isExporting = ref(false)
const poData = ref<POPreviewData>({
  purchase_order_no: '',
  supplier_id: '',
  supplier_name: '',
  subtotal_int: 0,
  tax_decimal1: 0,
  grand_total_int: 0,
  items: []
})

const companyInfo = ref({
  name: 'Taiwan Semiconductor Innovation Company',
  address: '台北市信義區信義路五段7號',
  phone: '02-8101-2345'
})

const selectedTermsTemplate = ref('standard')
const termsContent = ref(`1. 付款條件：月結 30 天
2. 交貨期限：訂單確認後 14 個工作天
3. 品質要求：須符合國家標準規範
4. 驗收標準：貨到 7 日內完成驗收
5. 保固期限：自驗收合格日起算一年`)

// Add index to items for display
const itemsWithIndex = computed(() => {
  return poData.value.items.map((item, index) => ({
    ...item,
    index: index + 1
  }))
})

// Export eligibility computed property
const canExport = computed(() => {
  return true // 根據用戶需求，所有狀態的採購單都可以輸出
})

// Status display computed property
const statusDisplay = computed(() => {
  const statusMap: Record<string, string> = {
    'pending': '待處理',
    'confirmed': '已確認',
    'order_created': '已建立',
    'outputted': '已製單',
    'purchased': '已採購',
    'shipped': '已出貨'
  }
  return statusMap[poData.value.purchase_status || ''] || poData.value.purchase_status || '未知'
})

// Export history display
const exportHistoryDisplay = computed(() => {
  if (!poData.value.export_count || poData.value.export_count === 0) {
    return ''
  }
  const lastExportDate = poData.value.last_export_at 
    ? new Date(poData.value.last_export_at).toLocaleString('zh-TW')
    : ''
  return `已輸出 ${poData.value.export_count} 次${lastExportDate ? `，最後輸出：${lastExportDate}` : ''}`
})

watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
  if (newVal && props.poNo) {
    loadPreviewData()
  }
})

watch(dialogVisible, (newVal) => {
  emit('update:visible', newVal)
})

const loadPreviewData = async () => {
  loading.value = true
  try {
    const response = await procurementApi.getPurchaseOrder(props.poNo)
    const data = response
    
    poData.value = {
      purchase_order_no: data.purchase_order_no || '',
      supplier_id: data.supplier_id || '',
      supplier_name: data.supplier_name || '',
      supplier_address: data.supplier_address || '',
      contact_person: data.contact_person || '',
      contact_phone: data.contact_phone || '',
      supplier_tax_id: data.supplier_tax_id || '',
      supplier_email: data.supplier_email || '',
      order_date: data.order_date || data.creation_date,
      quotation_no: data.quotation_no || '',
      delivery_address: data.delivery_address || '',
      expected_delivery_date: data.expected_delivery_date || '',
      notes: data.notes || '',
      purchase_status: data.purchase_status || '',
      last_export_at: data.last_export_at || '',
      export_count: data.export_count || 0,
      subtotal_int: data.subtotal_int || 0,
      tax_decimal1: data.tax_decimal1 || 0,
      grand_total_int: data.grand_total_int || 0,
      items: data.items || []
    }
    
    // Load default terms template
    loadTermsTemplate('standard')
  } catch (error) {
    ElMessage.error('載入預覽資料失敗')
    console.error('Failed to load preview:', error)
  } finally {
    loading.value = false
  }
}

const loadTermsTemplate = (templateId: string) => {
  const templates: Record<string, string> = {
    standard: `1. 付款條件：月結 30 天
2. 交貨期限：訂單確認後 14 個工作天
3. 品質要求：須符合國家標準規範
4. 驗收標準：貨到 7 日內完成驗收
5. 保固期限：自驗收合格日起算一年`,
    urgent: `1. 付款條件：貨到付款
2. 交貨期限：訂單確認後 3 個工作天內
3. 品質要求：須符合國家標準規範
4. 驗收標準：貨到當日完成驗收
5. 保固期限：自驗收合格日起算一年
6. 急件處理：需優先處理並確保準時交貨`,
    custom: ''
  }
  
  if (templates[templateId] !== undefined) {
    termsContent.value = templates[templateId]
  }
}

const handleClose = () => {
  dialogVisible.value = false
}

const handleExport = async (format: 'excel' | 'pdf') => {
  exporting.value = true
  isExporting.value = true
  try {
    // Save quotation number if edited and PO can be edited
    if (poData.value.quotation_no && poData.value.purchase_status !== 'outputted') {
      await procurementApi.updatePurchaseOrder(props.poNo, {
        quotation_no: poData.value.quotation_no
      })
    }
    
    // Use the new download utility
    const token = localStorage.getItem('auth_token')
    const apiUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1'
    const filename = format === 'excel' 
      ? `PO_${props.poNo}.xlsx` 
      : `PO_${props.poNo}.pdf`
    
    // Download file using the utility function
    await downloadFromAPI(
      `${apiUrl}/po/${props.poNo}/export`,
      'POST',
      { format },
      filename,
      token
    )
    
    // 移除下載成功訊息，避免列印時出現
    // ElMessage.success(`採購單已成功下載為 ${format.toUpperCase()} 格式`)

    // Update status after export (call status API separately)
    await loadPreviewData()
    
    // Emit event to refresh parent list
    emit('exported')
    
  } catch (error: any) {
    if (error.response?.data?.error_code === 'EXPORT_NOT_ALLOWED') {
      ElMessage.error(`無法輸出：採購單狀態為「${error.response.data.details.current_status}」`)
    } else {
      ElMessage.error(`輸出 ${format.toUpperCase()} 失敗`)
    }
    console.error('Export failed:', error)
  } finally {
    exporting.value = false
    isExporting.value = false
  }
}

const printPreviewMode = ref(false)

const togglePrintPreview = () => {
  printPreviewMode.value = !printPreviewMode.value
}

const handlePrint = async () => {
  printing.value = true
  try {
    // Save quotation number if edited and PO can be edited
    if (poData.value.quotation_no && poData.value.purchase_status !== 'outputted') {
      await procurementApi.updatePurchaseOrder(props.poNo, {
        quotation_no: poData.value.quotation_no
      })
    }

    // Get the token for authorization
    const token = localStorage.getItem('auth_token') || localStorage.getItem('token')

    // Use correct API URL
    const apiUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1'
    const printUrl = `${apiUrl}/po/${props.poNo}/export`

    // Use fetch to get HTML with proper authorization
    const response = await fetch(printUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ format: 'print' })
    })

    if (response.ok) {
      const htmlContent = await response.text()

      // Open new window with the HTML content
      const printWindow = window.open('', '_blank')
      if (printWindow) {
        printWindow.document.write(htmlContent)
        printWindow.document.close()

        // Wait for content to load then print
        setTimeout(() => {
          printWindow.print()

          // Close window after print dialog
          printWindow.onafterprint = () => {
            printWindow.close()
          }
        }, 500)
      }

      // Emit event to refresh parent list
      emit('exported')
    } else {
      throw new Error('Failed to generate print document')
    }

  } catch (error: any) {
    if (error.response?.data?.error_code === 'EXPORT_NOT_ALLOWED') {
      ElMessage.error(`無法列印：採購單狀態為「${error.response.data.details.current_status}」`)
    } else {
      ElMessage.error('準備列印失敗')
    }
    console.error('Print preparation failed:', error)
  } finally {
    printing.value = false
  }
}

const formatDate = (date?: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-TW')
}

const formatNumber = (num: number) => {
  return num.toLocaleString('zh-TW')
}

// Import the robust formatCurrency from utils
import { formatCurrency as globalFormatCurrency } from '@/utils/format'

const formatCurrency = (amount: number | string | null | undefined, includePrefix: boolean = true) => {
  // Debug log to see the actual values
  console.log('formatCurrency received:', amount, typeof amount)
  
  if (includePrefix) {
    return globalFormatCurrency(amount)
  } else {
    // For non-prefixed format, use global function and remove the prefix
    const formatted = globalFormatCurrency(amount)
    return formatted.replace('NT$ ', '')
  }
}
</script>

<style scoped lang="scss">
.po-preview-modal {
  .preview-container {
    padding: 20px;
    background: white;
    min-height: 600px;
  }

  .company-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 2px solid #333;
    
    .logo-section {
      flex: 0 0 150px;
      
      .company-logo {
        max-width: 150px;
        max-height: 80px;
        object-fit: contain;
      }
    }
    
    .header-center {
      flex: 1;
      text-align: center;
      
      .title {
        font-size: 32px;
        font-weight: bold;
        margin: 0;
        color: #333;
      }
      
      .subtitle {
        font-size: 20px;
        margin: 5px 0 0 0;
        color: #666;
      }
    }
    
    .header-right {
      flex: 0 0 150px;
      display: flex;
      justify-content: flex-end;
      align-items: center;
      
      .status-info {
        text-align: right;
        
        .status-badge {
          padding: 6px 12px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
          margin-bottom: 4px;
          
          &.order-created {
            background: #e6f7ff;
            color: #1890ff;
            border: 1px solid #91d5ff;
          }
          
          &.outputted {
            background: #f6ffed;
            color: #52c41a;
            border: 1px solid #b7eb8f;
          }
        }
        
        .export-history {
          font-size: 10px;
          color: #666;
          max-width: 140px;
          line-height: 1.2;
        }
      }
    }
  }

  .info-table-section {
    margin-bottom: 30px;
    
    .info-table {
      width: 100%;
      border-collapse: collapse;
      border: 1px solid #ddd;
      
      tr {
        border-bottom: 1px solid #ddd;
        
        &:last-child {
          border-bottom: none;
        }
      }
      
      td {
        padding: 10px;
        border-right: 1px solid #ddd;
        
        &:last-child {
          border-right: none;
        }
        
        &.label {
          background: #f5f7fa;
          font-weight: 500;
          color: #666;
          width: 15%;
          white-space: nowrap;
        }
        
        &.value {
          color: #333;
          width: 35%;
        }
      }
    }
  }

  .section {
    margin-bottom: 25px;
    
    .section-title {
      font-size: 16px;
      font-weight: bold;
      margin-bottom: 10px;
      padding-bottom: 5px;
      border-bottom: 2px solid #409eff;
      color: #333;
    }
  }

  .totals-section {
    margin: 20px 0;
    text-align: right;
    padding-right: 20px;  // 減少右邊距，讓內容更靠右

    .total-row {
      margin-bottom: 8px;
      display: flex;
      justify-content: flex-end;  // 使用 flexbox 讓內容靠右對齊

      .label {
        font-weight: 500;
        margin-right: 20px;
        white-space: nowrap;  // 防止標籤換行
      }

      .value {
        display: inline-block;
        min-width: 120px;
        text-align: right;
        font-weight: bold;
      }
      
      &.grand-total {
        font-size: 18px;
        font-weight: bold;
        color: #409eff;
        padding-top: 10px;
        border-top: 2px solid #e4e7ed;
      }
    }
  }

  .signature-section {
    margin-top: 60px;  // 增加上方間距，給注意事項更多空間
    padding-top: 20px;
    
    .signature-row {
      display: flex;
      justify-content: space-between;
      margin-bottom: 30px;
      
      .signature-item {
        display: flex;
        align-items: center;
        flex: 0 0 45%;
        
        .label {
          margin-right: 10px;
        }
        
        .signature-line {
          flex: 1;
          border-bottom: 1px solid #333;
          height: 1px;
        }
      }
    }
  }

  .non-printable-section {
    margin-top: 50px;
    
    .divider-line {
      border-top: 3px dashed #ccc;
      margin: 30px 0;
      position: relative;
      
      &::after {
        content: '以下區域不包含在採購單輸出中';
        position: absolute;
        top: -12px;
        left: 50%;
        transform: translateX(-50%);
        background: white;
        padding: 0 20px;
        color: #999;
        font-size: 12px;
      }
    }
  }

  .delivery-info {
    padding: 15px;
    background: #f5f7fa;
    border-radius: 4px;
    
    .info-row {
      margin-bottom: 10px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .label {
        font-weight: 500;
        color: #666;
        margin-right: 10px;
      }
      
      .value {
        color: #333;
      }
    }
  }

  .supplier-section {
    .supplier-info {
      background: #f5f7fa;
      padding: 15px;
      border-radius: 4px;
      
      .supplier-row {
        display: flex;
        margin-bottom: 10px;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .info-item {
          flex: 1;
          display: flex;
          
          .label {
            font-weight: 500;
            color: #666;
            margin-right: 10px;
            min-width: 80px;
          }
          
          .value {
            color: #333;
          }
        }
      }
    }
  }
}

.dialog-footer {
  display: flex;
  gap: 10px;
}

/* Print Preview Mode (Screen) */
@media screen {
  .po-preview-modal .preview-container.print-preview-mode {
    width: 210mm !important;
    min-height: 297mm !important;
    margin: 0 auto 20px !important;
    background: white !important;
    box-shadow: 0 0 10px rgba(0,0,0,0.1) !important;
    padding: 10mm 10mm 15mm 25mm !important;  /* 減少上下內距，增加左內距減少右內距 */
    box-sizing: border-box !important;
    transform-origin: top center;
    overflow: visible !important;
    position: relative !important;
    
    /* Multiple page support */
    &.page-2 {
      min-height: 594mm !important;
    }
    
    /* Page boundary visualization */
    &::after {
      content: 'Page 1 boundary';
      position: absolute;
      top: 297mm;
      left: 0;
      right: 0;
      border-top: 2px dashed #ff0000;
      pointer-events: none;
      z-index: 1000;
      font-size: 10px;
      color: #ff0000;
      text-align: center;
      padding-top: 2px;
    }
    
    .company-header {
      max-height: 40mm !important;  /* 減少高度 */
      margin-bottom: 3mm !important;  /* 減少間距 */
      
      .title {
        font-size: 20pt !important;
      }
      
      .subtitle {
        font-size: 12pt !important;
      }
    }
    
    .info-table-section {
      margin-bottom: 5mm !important;
      
      .info-table td {
        padding: 1.5mm !important;
        font-size: 9pt !important;
      }
    }
    
    .section {
      margin-bottom: 5mm !important;
      
      .section-title {
        font-size: 10pt !important;
        margin-bottom: 2mm !important;
      }
    }
    
    .totals-section {
      margin: 3mm 0 3mm 0 !important;  /* 移除右邊距，避免內容被推向右側 */

      .total-row {
        font-size: 9pt !important;
        margin-bottom: 1mm !important;
      }
    }
    
    .terms-section {
      max-height: 45mm !important;  /* 適度增加高度 */
      overflow: hidden !important;  /* 保持 hidden 避免重複顯示 */

      .el-textarea__inner {
        font-size: 8pt !important;
        line-height: 1.2 !important;
      }
    }
    
    .signature-section {
      max-height: 25mm !important;
      margin-top: 8mm !important;  /* 增加簽名區域上方間距 */
      
      .signature-row {
        height: 10mm !important;
      }
    }
    
    /* Hide elements that would cause page overflow */
    .non-printable-section {
      display: none !important;
    }
    
    /* Table optimizations for print preview */
    .el-table {
      font-size: 7pt !important;
      table-layout: fixed !important;
      width: 100% !important;
      
      th, td {
        padding: 1mm 0.5mm !important;
        line-height: 1.1 !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
      }
      
      /* Optimized column widths */
      .el-table__column:nth-child(1) { width: 8% !important; }  /* 項次 */
      .el-table__column:nth-child(2) { width: 22% !important; } /* 品名 */
      .el-table__column:nth-child(3) { width: 18% !important; } /* 規格 */
      .el-table__column:nth-child(4) { width: 12% !important; } /* 型號 */
      .el-table__column:nth-child(5) { width: 8% !important; }  /* 數量 */
      .el-table__column:nth-child(6) { width: 6% !important; }  /* 單位 */
      .el-table__column:nth-child(7) { width: 10% !important; } /* 單價 */
      .el-table__column:nth-child(8) { width: 11% !important; } /* 小計 */
      .el-table__column:nth-child(9) { width: 5% !important; }  /* 備註 */
    }
    
    /* Currency display without NT$ */
    .print-currency::before {
      content: '$';
    }
  }
}

/* Complete Print Stylesheet */
@media print {
  /* Page Setup */
  @page {
    size: A4 portrait;
    margin: 20mm 10mm 20mm 25mm;  /* 調整邊距：上20mm 右10mm 下20mm 左25mm - 增加左邊距，減少右邊距讓內容居中 */

    /* Print optimization */
    -webkit-print-color-adjust: exact;
    color-adjust: exact;
    print-color-adjust: exact;
  }
  
  @page :first {
    margin-top: 20mm;  /* 保持與主要設定一致 */
  }

  @page :left {
    margin-left: 25mm;  /* 增加左邊距 */
    margin-right: 10mm;  /* 減少右邊距 */
  }

  @page :right {
    margin-left: 25mm;  /* 增加左邊距 */
    margin-right: 10mm;  /* 減少右邊距 */
  }
  
  /* Hide non-printable elements */
  .el-dialog__wrapper,
  .el-dialog__header,
  .dialog-footer,
  .terms-selector,
  .non-printable-section,
  .el-loading-mask,
  .el-input,
  .el-select,
  .status-info,
  .export-history {
    display: none !important;
  }
  
  /* Main container adjustments */
  .po-preview-modal .el-dialog,
  .po-preview-modal .el-dialog__body,
  .preview-container {
    width: 100% !important;
    max-width: 170mm !important;  /* 減少寬度使內容更居中 */
    height: auto !important;
    padding: 0 !important;
    margin: 0 auto !important;  /* 添加 auto 使內容水平置中 */
    box-shadow: none !important;
    border: none !important;
    border-radius: 0 !important;
    background: white !important;
    color: black !important;
  }
  
  /* Company Header */
  .company-header {
    max-height: 40mm !important;  /* 統一減少高度避免被截斷 */
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    border-bottom: 1.5pt solid #000 !important;
    margin-bottom: 5mm !important;
    page-break-inside: avoid !important;
    padding-bottom: 3mm !important;
  }
  
  .company-logo {
    max-width: 45mm !important;
    max-height: 30mm !important;
    object-fit: contain !important;
  }
  
  .title {
    font-size: 20pt !important;
    font-weight: bold !important;
    line-height: 1.1 !important;
    color: #000 !important;
  }
  
  .subtitle {
    font-size: 12pt !important;
    font-weight: normal !important;
    line-height: 1.1 !important;
    color: #333 !important;
  }
  
  /* Supplier Information Table */
  .info-table-section {
    margin-bottom: 8mm !important;
    page-break-inside: avoid !important;
  }
  
  .info-table {
    width: 100% !important;
    max-height: 35mm !important;
    border-collapse: collapse !important;
    page-break-inside: avoid !important;
  }
  
  .info-table td {
    padding: 2mm !important;
    border: 0.5pt solid #333 !important;
    vertical-align: middle !important;
    font-size: 10pt !important;
    line-height: 1.2 !important;
    color: #000 !important;
  }
  
  .info-table .label {
    width: 35mm !important;
    background: #f0f0f0 !important;
    font-weight: 600 !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  
  .info-table .value {
    width: 55mm !important;
  }
  
  /* Purchase Items Table */
  .el-table {
    font-size: 7.5pt !important;
    line-height: 1.1 !important;
    border-collapse: collapse !important;
    width: 100% !important;
    margin-bottom: 5mm !important;
    table-layout: fixed !important;
  }
  
  .el-table th {
    background: #f5f5f5 !important;
    font-size: 8pt !important;
    font-weight: 600 !important;
    padding: 1.5mm 1mm !important;
    border: 0.5pt solid #333 !important;
    color: #000 !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  
  .el-table td {
    padding: 1mm 0.5mm !important;
    border: 0.5pt solid #333 !important;
    font-size: 7.5pt !important;
    color: #000 !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
  }
  
  /* Special handling for text columns */
  .el-table td:nth-child(2),
  .el-table td:nth-child(3),
  .el-table td:nth-child(4) {
    white-space: normal !important;
    word-break: break-all !important;
    line-height: 1.1 !important;
  }
  
  .el-table .cell {
    line-height: 1.2 !important;
    word-break: break-word !important;
    overflow: hidden !important;
    padding: 0 !important;
  }
  
  /* Column-specific widths optimized for A4 */
  .el-table {
    table-layout: fixed !important;
    width: 100% !important;
  }
  
  .el-table .el-table__cell:nth-child(1) { width: 12mm !important; } /* 項次 */
  .el-table .el-table__cell:nth-child(2) { width: 38mm !important; } /* 品名 */
  .el-table .el-table__cell:nth-child(3) { width: 30mm !important; } /* 規格 */
  .el-table .el-table__cell:nth-child(4) { width: 20mm !important; } /* 型號 */
  .el-table .el-table__cell:nth-child(5) { width: 14mm !important; } /* 數量 */
  .el-table .el-table__cell:nth-child(6) { width: 11mm !important; } /* 單位 */
  .el-table .el-table__cell:nth-child(7) { width: 17mm !important; } /* 單價 */
  .el-table .el-table__cell:nth-child(8) { width: 19mm !important; } /* 小計 */
  .el-table .el-table__cell:nth-child(9) { width: 9mm !important; } /* 備註 */
  
  /* Totals Section */
  .totals-section {
    max-height: 20mm !important;
    margin: 5mm 0 5mm 0 !important;  /* 移除左右邊距，使用頁面邊距控制 */
    text-align: right !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-end !important;  /* 讓內容靠右對齊 */
    justify-content: center !important;
    page-break-inside: avoid !important;
  }

  .total-row {
    margin-bottom: 2mm !important;
    font-size: 11pt !important;
    line-height: 1.3 !important;
    color: #000 !important;
    display: flex !important;
    justify-content: flex-end !important;  /* 確保每一行都靠右對齊 */
  }
  
  .grand-total {
    font-size: 12pt !important;
    font-weight: bold !important;
    border-top: 1pt solid #333 !important;
    padding-top: 2mm !important;
    margin-top: 2mm !important;
  }
  
  /* Terms & Conditions */
  .section {
    margin-bottom: 5mm !important;
    page-break-inside: avoid !important;
  }
  
  .section-title {
    font-size: 11pt !important;
    font-weight: bold !important;
    margin-bottom: 2mm !important;
    color: #000 !important;
    border-bottom: 1pt solid #333 !important;
    padding-bottom: 1mm !important;
  }
  
  .terms-section {
    max-height: 40mm !important;  /* 減少高度避免超出頁面 */
    min-height: 25mm !important;  /* 減少最小高度 */
    overflow: hidden !important;  /* 保持 hidden 避免重複顯示 */
    page-break-inside: avoid !important;
  }
  
  /* Terms content handling for textarea */
  .el-textarea__inner {
    display: none !important;
  }
  
  /* Show print-only terms display */
  .terms-print-content {
    display: block !important;
    font-size: 8.5pt !important;  /* 稍微縮小字體 */
    line-height: 1.3 !important;  /* 調整行距 */
    white-space: pre-wrap !important;  /* 使用 pre-wrap 確保換行正確 */
    border: 0.5pt solid #ccc !important;
    padding: 2.5mm !important;  /* 減少內距 */
    min-height: 28mm !important;  /* 減少最小高度 */
    max-height: 38mm !important;  /* 減少最大高度 */
    height: auto !important;  /* 高度自動調整 */
    overflow: hidden !important;  /* 使用 hidden 避免超出 */
    color: #000 !important;
  }
  
  /* Signature Section */
  .signature-section {
    max-height: 20mm !important;  /* 減少高度 */
    margin-top: 5mm !important;  /* 減少上方間距 */
    page-break-inside: avoid !important;
    page-break-before: auto !important;
  }
  
  .signature-row {
    height: 10mm !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    margin-bottom: 5mm !important;
  }
  
  .signature-item {
    display: flex !important;
    align-items: center !important;
    width: 80mm !important;
    font-size: 10pt !important;
    color: #000 !important;
  }
  
  .signature-line {
    width: 60mm !important;
    border-bottom: 1pt solid #333 !important;
    height: 1pt !important;
    margin-left: 5mm !important;
  }
  
  /* Page break management */
  .company-header,
  .info-table-section {
    page-break-inside: avoid !important;
    page-break-after: auto !important;
  }
  
  .el-table {
    page-break-inside: auto !important;
  }
  
  .el-table tbody tr {
    page-break-inside: avoid !important;
    page-break-after: auto !important;
  }
  
  .totals-section,
  .terms-section,
  .signature-section {
    page-break-inside: avoid !important;
    page-break-before: auto !important;
  }
  
  /* Ensure proper page breaks */
  h3 {
    page-break-after: avoid !important;
    page-break-before: auto !important;
  }
  
  /* Currency formatting in print */
  .print-currency::before {
    content: '$';
  }
}

/* Browser-specific print adjustments */
@media print and (-webkit-min-device-pixel-ratio: 0) {
  .company-header {
    -webkit-print-color-adjust: exact;
  }
  
  .info-table .label {
    -webkit-print-color-adjust: exact;
  }
}

/* Firefox print adjustments */
@-moz-document url-prefix() {
  @media print {
    .el-table th {
      background: #f5f5f5 !important;
      color-adjust: exact;
    }
    
    .info-table .label {
      background: #f0f0f0 !important;
      color-adjust: exact;
    }
  }
}
</style>