<template>
  <div class="purchase-order-form">
    <div class="page-header">
      <h1 class="page-title">{{ isEdit ? '編輯採購單' : '新增採購單' }}</h1>
      <div class="actions">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="savePO" :loading="saving">
          {{ isEdit ? '更新' : '儲存' }}
        </el-button>
      </div>
    </div>

    <div class="form-container">
      <el-form 
        :model="form" 
        :rules="rules" 
        ref="formRef"
        label-width="120px"
      >
        <el-card class="form-card">
          <template #header>
            <h3>基本資訊</h3>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="採購單號" prop="purchase_order_no">
                <el-input v-model="form.purchase_order_no" disabled />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="供應商" prop="supplier_id">
                <el-select 
                  v-model="form.supplier_id" 
                  placeholder="選擇供應商"
                  style="width: 100%"
                  @change="onSupplierChange"
                >
                  <el-option 
                    v-for="supplier in suppliers"
                    :key="supplier.supplier_id"
                    :label="`${supplier.supplier_id} - ${supplier.supplier_name_zh}`"
                    :value="supplier.supplier_id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="訂購日期" prop="order_date">
                <el-date-picker
                  v-model="form.order_date"
                  type="date"
                  placeholder="選擇日期"
                  format="YYYY/MM/DD"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="報價單號" prop="quotation_no">
                <el-input 
                  v-model="form.quotation_no" 
                  placeholder="請輸入報價單號"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="交貨天數" prop="delivery_days">
                <el-input-number 
                  v-model="form.delivery_days" 
                  :min="1"
                  :max="365"
                  placeholder="請輸入交貨天數"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="採購狀態" prop="purchase_status">
                <el-select 
                  v-model="form.purchase_status" 
                  placeholder="請選擇狀態"
                  style="width: 100%"
                >
                  <el-option label="已建立" value="order_created" />
                  <el-option label="已製單" value="outputted" />
                  <el-option label="已採購" value="purchased" />
                  <el-option label="已發貨" value="shipped" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="備註">
            <el-input 
              v-model="form.remarks"
              type="textarea"
              :rows="3"
              placeholder="請輸入備註"
            />
          </el-form-item>
        </el-card>

        <el-card class="form-card">
          <template #header>
            <div class="card-header">
              <h3>採購項目</h3>
              <el-button type="primary" size="small" @click="addItem">
                新增項目
              </el-button>
            </div>
          </template>
          
          <el-table :data="form.items" stripe>
            <el-table-column type="index" label="項次" width="60" />
            <el-table-column label="物料編號" width="120">
              <template #default="{ row }">
                <el-input v-model="row.material_no" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="品名規格" min-width="200">
              <template #default="{ row }">
                <el-input v-model="row.description" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="單位" width="100">
              <template #default="{ row }">
                <el-select v-model="row.unit" size="small">
                  <el-option label="個" value="個" />
                  <el-option label="件" value="件" />
                  <el-option label="箱" value="箱" />
                  <el-option label="台" value="台" />
                  <el-option label="組" value="組" />
                  <el-option label="批" value="批" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="數量" width="100">
              <template #default="{ row }">
                <el-input-number 
                  v-model="row.quantity" 
                  size="small" 
                  :min="1"
                  @change="calculateItemTotal(row)"
                />
              </template>
            </el-table-column>
            <el-table-column label="單價" width="120">
              <template #default="{ row }">
                <el-input-number 
                  v-model="row.unit_price" 
                  size="small" 
                  :min="0"
                  :precision="2"
                  @change="calculateItemTotal(row)"
                />
              </template>
            </el-table-column>
            <el-table-column label="小計" width="120">
              <template #default="{ row }">
                {{ formatCurrency(row.total_price || 0) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" fixed="right">
              <template #default="{ $index }">
                <el-button 
                  size="small" 
                  type="danger" 
                  @click="removeItem($index)"
                >
                  刪除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card class="form-card">
          <template #header>
            <h3>金額總計</h3>
          </template>
          
          <div class="summary">
            <el-row :gutter="20">
              <el-col :span="8">
                <div class="summary-item">
                  <label>小計：</label>
                  <span>{{ formatCurrency(subtotal) }}</span>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="summary-item">
                  <label>稅額：</label>
                  <span>{{ formatCurrency(taxAmount) }}</span>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="summary-item">
                  <label>總計：</label>
                  <span class="total">{{ formatCurrency(total) }}</span>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatCurrency } from '@/utils/format'
import { procurementApi } from '@/api/procurement'
import { suppliersApi } from '@/api/suppliers'

const route = useRoute()
const router = useRouter()

// Reactive data
const formRef = ref()
const saving = ref(false)
const suppliers = ref([])

const isEdit = computed(() => !!route.params.id)
const poNo = computed(() => route.params.id as string)

const form = ref({
  purchase_order_no: '',
  supplier_id: null,
  supplier_name: '',
  order_date: new Date().toISOString().split('T')[0],
  quotation_no: '',
  purchase_status: 'order_created',
  delivery_days: 14,
  remarks: '',
  items: []
})

const rules = {
  supplier_id: [
    { required: true, message: '請選擇供應商', trigger: 'change' }
  ],
  order_date: [
    { required: true, message: '請選擇訂購日期', trigger: 'change' }
  ]
}

// Computed
const subtotal = computed(() => {
  return form.value.items.reduce((sum, item: any) => sum + (item.total_price || 0), 0)
})

const taxAmount = computed(() => {
  return subtotal.value * 0.05
})

const total = computed(() => {
  return subtotal.value + taxAmount.value
})

// Methods
const loadSuppliers = async () => {
  try {
    const response = await suppliersApi.getActiveSuppliers()
    suppliers.value = response || []
  } catch (error) {
    console.error('載入供應商失敗:', error)
    ElMessage.error('載入供應商列表失敗')
  }
}

const loadPOData = async () => {
  if (!isEdit.value) {
    // Generate PO number for new PO
    const date = new Date()
    const dateStr = date.toISOString().slice(0, 10).replace(/-/g, '')
    const randomNum = Math.floor(Math.random() * 1000).toString().padStart(3, '0')
    form.value.purchase_order_no = `PO${dateStr}${randomNum}`
    return
  }
  
  try {
    const response = await procurementApi.getPurchaseOrder(poNo.value)
    
    // Map the response data to form data
    form.value = {
      purchase_order_no: response.purchase_order_no,
      supplier_id: response.supplier_id,
      supplier_name: response.supplier_name,
      order_date: response.order_date,
      quotation_no: response.quotation_no || '',
      purchase_status: response.purchase_status,
      delivery_days: response.delivery_days || 14,
      remarks: response.remarks || '',
      items: (response.items || []).map(item => ({
        material_no: item.material_no || '',
        description: item.item_name || '',
        unit: item.item_unit || '個',
        quantity: item.item_quantity || 1,
        unit_price: item.unit_price || 0,
        total_price: (item.item_quantity || 1) * (item.unit_price || 0)
      }))
    }
  } catch (error) {
    console.error('載入採購單資料失敗:', error)
    ElMessage.error('載入採購單資料失敗')
    router.push('/purchase-orders')
  }
}

const onSupplierChange = (supplierId: number) => {
  const supplier = suppliers.value.find(s => s.id === supplierId)
  if (supplier) {
    form.value.supplier_name = supplier.name
  }
}

const addItem = () => {
  form.value.items.push({
    material_no: '',
    description: '',
    unit: '個',
    quantity: 1,
    unit_price: 0,
    total_price: 0
  })
}

const calculateItemTotal = (item: any) => {
  item.total_price = (item.quantity || 0) * (item.unit_price || 0)
}

const savePO = async () => {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
    
    if (form.value.items.length === 0) {
      ElMessage.warning('請至少新增一個採購項目')
      return
    }

    saving.value = true
    
    const payload = {
      ...form.value,
      subtotal_int: subtotal.value,
      tax_int: taxAmount.value,
      grand_total_int: total.value
    }

    if (isEdit.value) {
      await procurementApi.updatePurchaseOrder(poNo.value, payload)
      ElMessage.success('採購單更新成功')
    } else {
      const response = await procurementApi.createPurchaseOrder(payload)
      ElMessage.success('採購單建立成功')
      router.push(`/purchase-orders/${response.purchase_order_no}`)
    }
  } catch (error) {
    console.error('儲存採購單失敗:', error)
    ElMessage.error(isEdit.value ? '更新採購單失敗' : '建立採購單失敗')
  } finally {
    saving.value = false
  }
}

const removeItem = (index: number) => {
  ElMessageBox.confirm('確定要刪除此項目？', '提示', {
    confirmButtonText: '確定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    form.value.items.splice(index, 1)
  }).catch(() => {
    // User cancelled
  })
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  loadSuppliers()
  loadPOData()
})
</script>

<style scoped>
.purchase-order-form {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.form-container {
  max-width: 1200px;
}

.form-card {
  margin-bottom: 20px;
}

.form-card :deep(.el-card__header h3) {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary {
  padding: 20px 0;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  font-size: 16px;
}

.summary-item .total {
  font-weight: bold;
  font-size: 18px;
  color: #409eff;
}
</style>