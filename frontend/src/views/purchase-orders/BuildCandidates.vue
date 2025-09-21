<template>
  <div class="build-candidates">
    <PageHeader
      title="建立採購單"
      subtitle="從已核准請購項目建立採購單"
      :show-back="true"
      :show-refresh="true"
      @back="handleBack"
      @refresh="handleRefresh"
    />

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="candidateGroups.length === 0" class="empty-state">
      <el-empty description="暫無可用的請購項目">
        <template #image>
          <el-icon size="60"><DocumentCopy /></el-icon>
        </template>
        <el-button type="primary" @click="handleBack">返回列表</el-button>
      </el-empty>
    </div>

    <div v-else class="candidates-content">
      <!-- 供應商選擇器 -->
      <div class="supplier-selector">
        <el-select 
          v-model="selectedSupplierId" 
          placeholder="選擇供應商建立採購單（可輸入供應商名稱搜尋）"
          size="large"
          class="supplier-select"
          filterable
          remote
          :remote-method="handleSupplierSearch"
          :loading="supplierSearchLoading"
          clearable
          @change="handleSupplierChange"
          @clear="handleSupplierClear"
        >
          <el-option
            v-for="group in filteredCandidateGroups"
            :key="group.supplier_id"
            :value="group.supplier_id"
            :label="`${group.supplier?.supplier_name_zh || group.supplier_id || '未知供應商'} (${group.items.length}項)`"
          >
            <div class="supplier-option">
              <span class="supplier-name" :class="{ 'urgent-text': group.has_urgent_items }">
                <el-icon v-if="group.has_urgent_items" color="#cf1322"><Warning /></el-icon>
                {{ group.supplier?.supplier_name_zh || group.supplier_id || '未知供應商' }}
                <el-tag v-if="group.has_urgent_items" type="danger" size="small" class="urgent-tag">加急</el-tag>
              </span>
              <span class="supplier-meta">
                {{ group.items.length }}項 · {{ formatMoney(calculateGroupTotal(group.items)) }}
              </span>
            </div>
          </el-option>
        </el-select>
      </div>

      <!-- 提示選擇供應商 -->
      <div v-if="!currentSupplierGroup" class="no-supplier-selected">
        <el-empty description="請選擇供應商以查看可採購項目">
          <template #image>
            <el-icon size="60"><Select /></el-icon>
          </template>
          <div class="empty-hint">
            <p>請從上方下拉選單中選擇一個供應商</p>
            <p class="hint-secondary">選擇後即可查看該供應商的可採購項目</p>
          </div>
        </el-empty>
      </div>

      <!-- 左右分欄編輯界面 -->
      <div v-else class="po-builder">
        <!-- 左側 40%：待採購項目清單 -->
        <div class="left-panel">
          <div class="panel-header">
            <h3>待採購項目</h3>
            <div class="panel-actions">
              <el-button size="small" @click="selectAll" :disabled="allSelected">全選</el-button>
              <el-button size="small" @click="clearSelection" :disabled="!hasSelection">清空</el-button>
            </div>
          </div>
          
          <div class="items-list">
            <el-checkbox-group v-model="selectedItems">
              <div 
                v-for="item in currentSupplierGroup.items" 
                :key="item.detail_id"
                class="item-row"
                :class="{ selected: selectedItems.includes(item.detail_id) }"
              >
                <el-checkbox :label="item.detail_id" class="item-checkbox">
                  <div class="item-content">
                    <div class="item-header">
                      <span class="item-name">{{ item.item_name }}</span>
                      <span class="item-price">{{ formatMoney(item.unit_price) }}</span>
                    </div>
                    <div class="item-details">
                      <span class="item-spec">{{ item.item_specification }}</span>
                      <span class="item-qty">{{ item.item_quantity }} {{ item.item_unit }}</span>
                    </div>
                    <div class="item-meta">
                      <span class="source-no">{{ item.source_request_order_no }}</span>
                      <span class="item-subtotal">小計: {{ formatMoney(item.item_quantity * item.unit_price) }}</span>
                    </div>
                  </div>
                </el-checkbox>
              </div>
            </el-checkbox-group>
          </div>
        </div>

        <!-- 右側 60%：採購單即時預覽 -->
        <div class="right-panel">
          <div class="panel-header">
            <h3>採購單預覽</h3>
            <div class="panel-actions">
              <el-button 
                type="primary" 
                @click="createPurchaseOrder"
                :disabled="!hasSelection"
                :loading="creating"
              >
                建立採購單
              </el-button>
            </div>
          </div>

          <div class="po-preview">
            <div v-if="!hasSelection" class="preview-empty">
              <el-empty description="請選擇要採購的項目" />
            </div>

            <div v-else class="preview-content">
              <!-- 供應商資訊 -->
              <el-card class="supplier-info" shadow="never">
                <h4>供應商資訊</h4>
                <div class="supplier-details">
                  <div class="detail-row">
                    <label>供應商名稱：</label>
                    <span>{{ currentSupplierGroup.supplier?.supplier_name_zh || currentSupplierGroup.supplier_id || '未知供應商' }}</span>
                  </div>
                  <div class="detail-row">
                    <label>聯絡電話：</label>
                    <span>{{ currentSupplierGroup.supplier?.supplier_phone || '-' }}</span>
                  </div>
                  <div class="detail-row">
                    <label>聯絡人：</label>
                    <span>{{ currentSupplierGroup.supplier?.supplier_contact_person || '-' }}</span>
                  </div>
                </div>
              </el-card>

              <!-- 採購項目清單 -->
              <el-card class="items-preview" shadow="never">
                <h4>採購項目 ({{ selectedItemsDetails.length }}項)</h4>
                <el-table :data="selectedItemsDetails" border size="small">
                  <el-table-column type="index" label="序號" width="50" align="center" />
                  <el-table-column label="項目名稱" prop="item_name" min-width="120" show-overflow-tooltip />
                  <el-table-column label="規格" prop="item_specification" width="100" show-overflow-tooltip />
                  <el-table-column label="數量" prop="item_quantity" width="60" align="center" />
                  <el-table-column label="單位" prop="item_unit" width="60" align="center" />
                  <el-table-column label="單價" width="90" align="right">
                    <template #default="{ row }">
                      <span class="money">{{ formatMoney(row.unit_price) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="小計" width="100" align="right">
                    <template #default="{ row }">
                      <span class="money">{{ formatMoney(calculateSubtotal(row)) }}</span>
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>

              <!-- 金額計算 -->
              <el-card class="amount-summary" shadow="never">
                <h4>金額計算</h4>
                <div class="amount-details">
                  <div class="amount-row">
                    <label>項目總計：</label>
                    <span class="money">{{ formatMoney(subtotalAmount) }}</span>
                  </div>
                  <div class="amount-row">
                    <label>稅額 (5%)：</label>
                    <span class="money">{{ formatTax(taxAmount) }}</span>
                  </div>
                  <div class="amount-row total">
                    <label>總金額：</label>
                    <span class="money total-amount">{{ formatMoney(totalAmount) }}</span>
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DocumentCopy, Select, Warning } from '@element-plus/icons-vue'
import { PageHeader } from '@/components'
import { procurementApi } from '@/api/procurement'
import { suppliersApi } from '@/api/suppliers'
import type { BuildCandidate } from '@/api/procurement'

const router = useRouter()

// State
const loading = ref(false)
const creating = ref(false)
const candidateGroups = ref<BuildCandidate[]>([])
const currentSupplierGroup = ref<BuildCandidate | null>(null)
const selectedSupplierId = ref<string | null>(null)
const selectedItems = ref<number[]>([])
const supplierSearchLoading = ref(false)
const supplierSearchQuery = ref('')

// Computed
const validCandidateGroups = computed(() => {
  return candidateGroups.value.filter(group => 
    group.supplier_id && group.supplier_id !== 'null' && group.supplier_id !== null
  )
})

// Fuzzy search function
const fuzzyMatch = (text: string, search: string): boolean => {
  if (!search) return true
  
  const searchLower = search.toLowerCase()
  const textLower = text.toLowerCase()
  
  // Direct substring match
  if (textLower.includes(searchLower)) return true
  
  // Fuzzy match - allows for some typos and character variations
  let searchIndex = 0
  for (let i = 0; i < textLower.length && searchIndex < searchLower.length; i++) {
    if (textLower[i] === searchLower[searchIndex]) {
      searchIndex++
    }
  }
  
  return searchIndex === searchLower.length
}

const filteredCandidateGroups = computed(() => {
  if (!supplierSearchQuery.value) {
    return validCandidateGroups.value
  }
  
  return validCandidateGroups.value.filter(group => {
    const supplierName = group.supplier?.supplier_name_zh || group.supplier_id || ''
    const supplierNameEn = group.supplier?.supplier_name_en || ''
    const supplierId = group.supplier_id || ''
    
    return fuzzyMatch(supplierName, supplierSearchQuery.value) ||
           fuzzyMatch(supplierNameEn, supplierSearchQuery.value) ||
           fuzzyMatch(supplierId, supplierSearchQuery.value)
  })
})

const hasSelection = computed(() => selectedItems.value.length > 0)

const allSelected = computed(() => {
  if (!currentSupplierGroup.value) return false
  return selectedItems.value.length === currentSupplierGroup.value.items.length
})

const selectedItemsDetails = computed(() => {
  if (!currentSupplierGroup.value) return []
  return currentSupplierGroup.value.items.filter(item => 
    selectedItems.value.includes(item.detail_id)
  )
})

const subtotalAmount = computed(() => {
  return selectedItemsDetails.value.reduce((total, item) => 
    total + calculateSubtotal(item), 0
  )
})

const taxAmount = computed(() => {
  return subtotalAmount.value * 0.05
})

const totalAmount = computed(() => {
  return Math.round(subtotalAmount.value + taxAmount.value)
})

// Methods
const formatMoney = (amount: number) => {
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: 'TWD',
    minimumFractionDigits: 0
  }).format(Math.round(amount))
}

const formatTax = (amount: number) => {
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: 'TWD',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  }).format(amount)
}

const calculateSubtotal = (item: any) => {
  return Math.round(item.item_quantity * item.unit_price)
}

const calculateGroupTotal = (items: any[]) => {
  return items.reduce((total, item) => total + calculateSubtotal(item), 0)
}

const handleBack = () => {
  router.push('/purchase-orders')
}

const handleRefresh = async () => {
  await loadCandidates()
}

const handleSupplierChange = (supplierId: string | null) => {
  if (supplierId) {
    currentSupplierGroup.value = candidateGroups.value.find(group => group.supplier_id === supplierId) || null
  } else {
    currentSupplierGroup.value = null
  }
  selectedItems.value = []
}

const handleSupplierSearch = (query: string) => {
  supplierSearchQuery.value = query
}

const handleSupplierClear = () => {
  supplierSearchQuery.value = ''
  selectedSupplierId.value = null
  currentSupplierGroup.value = null
  selectedItems.value = []
}

const selectAll = () => {
  if (currentSupplierGroup.value) {
    selectedItems.value = currentSupplierGroup.value.items.map(item => item.detail_id)
  }
}

const clearSelection = () => {
  selectedItems.value = []
}

const loadCandidates = async () => {
  try {
    loading.value = true
    const response = await procurementApi.getBuildCandidates()
    const candidatesArray = Array.isArray(response) ? response : Object.values(response.candidates || response.data || [])
    candidateGroups.value = candidatesArray.filter(group => group && group.items && group.items.length > 0)
    
    // 不再自動選擇第一個供應商，讓用戶主動選擇
    // 清空當前選擇以確保用戶重新選擇
    currentSupplierGroup.value = null
    selectedSupplierId.value = null
  } catch (error) {
    console.error('Failed to load candidates:', error)
    ElMessage.error('載入採購候選項目失敗')
  } finally {
    loading.value = false
  }
}

const createPurchaseOrder = async () => {
  if (!currentSupplierGroup.value || !hasSelection.value) return
  
  // Validate supplier_id before proceeding
  if (!currentSupplierGroup.value.supplier_id || currentSupplierGroup.value.supplier_id === 'null') {
    ElMessage.error('無法為此供應商創建採購單：供應商信息不完整')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `確定要為 ${currentSupplierGroup.value.supplier?.supplier_name_zh || currentSupplierGroup.value.supplier_id || '未知供應商'} 建立採購單嗎？\n將包含 ${selectedItems.value.length} 個項目，總金額 ${formatMoney(totalAmount.value)}`,
      '建立採購單確認',
      {
        confirmButtonText: '確定建立',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    creating.value = true

    // Debug logging
    console.log('Creating PO with:')
    console.log('  selectedItems.value:', selectedItems.value)
    console.log('  selectedItemsDetails.value:', selectedItemsDetails.value)
    console.log('  currentSupplierGroup.value:', currentSupplierGroup.value)

    // Check if items are selected
    if (!selectedItemsDetails.value || selectedItemsDetails.value.length === 0) {
      ElMessage.error('請至少選擇一個項目來建立採購單')
      creating.value = false
      return
    }

    const createData = {
      supplier_id: currentSupplierGroup.value.supplier_id,
      lines: selectedItemsDetails.value.map(item => ({
        detail_id: item.detail_id,
        quantity: item.item_quantity,
        unit_price: item.unit_price
      }))
    }

    console.log('Sending createData:', JSON.stringify(createData, null, 2))

    const newPO = await procurementApi.createPO(createData)
    
    ElMessage.success(`採購單建立成功！`)
    
    // Refresh candidates to remove items that were used
    await loadCandidates()
    
    // Clear selection
    selectedItems.value = []
    
    // Always navigate back to the purchase orders list after creation
    router.push('/purchase-orders')
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Create PO failed:', error)
      
      // Handle specific error types
      if (error.response?.status === 400) {
        const errorData = error.response.data?.error
        const errorCode = errorData?.code
        const errorMessage = errorData?.message
        
        if (errorCode === 'NO_ITEMS') {
          ElMessage.error('請至少選擇一個項目來建立採購單')
        } else if (errorCode === 'SUPPLIER_NOT_FOUND') {
          ElMessage.error('供應商不存在，無法建立採購單')
        } else if (errorCode === 'INVALID_REQUISITION_ITEM') {
          ElMessage.error('選擇的項目不可用或已被使用')
        } else {
          ElMessage.error(`建立採購單失敗：${errorMessage || '未知錯誤'}`)
        }
      } else if (error.response?.status === 500) {
        ElMessage.error('系統內部錯誤，請聯繫管理員')
      } else {
        ElMessage.error('建立採購單失敗')
      }
    }
  } finally {
    creating.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadCandidates()
})
</script>

<style scoped>
.build-candidates {
  .loading-container {
    background: white;
    padding: 24px;
    border-radius: 6px;
  }

  .empty-state {
    background: white;
    padding: 40px;
    border-radius: 6px;
    text-align: center;
  }

  .candidates-content {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .no-supplier-selected {
    background: white;
    padding: 60px 40px;
    border-radius: 6px;
    border: 1px solid #e4e7ed;
    text-align: center;

    .empty-hint {
      margin-top: 16px;

      p {
        margin: 8px 0;
        color: #606266;
        font-size: 14px;

        &.hint-secondary {
          color: #909399;
          font-size: 13px;
        }
      }
    }
  }

  .supplier-selector {
    background: white;
    padding: 20px;
    border-radius: 6px;
    border: 1px solid #e4e7ed;

    .supplier-select {
      width: 100%;
      max-width: 500px;
    }

    .supplier-option {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .supplier-name {
        font-weight: 600;
        color: #303133;
      }

      .supplier-meta {
        font-size: 12px;
        color: #909399;
      }
    }
  }

  .po-builder {
    display: flex;
    gap: 20px;
    height: calc(100vh - 300px);
    min-height: 600px;

    .left-panel {
      width: 40%;
      background: white;
      border-radius: 6px;
      border: 1px solid #e4e7ed;
      display: flex;
      flex-direction: column;

      .panel-header {
        padding: 16px 20px;
        border-bottom: 1px solid #e4e7ed;
        display: flex;
        justify-content: space-between;
        align-items: center;

        h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: #303133;
        }

        .panel-actions {
          display: flex;
          gap: 8px;
        }
      }

      .items-list {
        flex: 1;
        overflow-y: auto;
        padding: 16px 20px;

        .item-row {
          border: 1px solid #e4e7ed;
          border-radius: 4px;
          margin-bottom: 12px;
          padding: 12px;
          transition: all 0.2s;

          &:hover {
            border-color: #409eff;
            box-shadow: 0 2px 4px rgba(64, 158, 255, 0.1);
          }

          &.selected {
            border-color: #409eff;
            background-color: #f0f9ff;
          }

          .item-checkbox {
            width: 100%;

            :deep(.el-checkbox__label) {
              width: 100%;
              padding-left: 0;
            }
          }

          .item-content {
            .item-header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              margin-bottom: 8px;

              .item-name {
                font-weight: 600;
                color: #303133;
                flex: 1;
                margin-right: 12px;
              }

              .item-price {
                font-weight: 600;
                color: #409eff;
                font-family: Monaco, 'Courier New', monospace;
              }
            }

            .item-details {
              display: flex;
              justify-content: space-between;
              align-items: center;
              margin-bottom: 8px;
              font-size: 13px;
              color: #606266;

              .item-spec {
                flex: 1;
                margin-right: 12px;
              }

              .item-qty {
                font-weight: 500;
              }
            }

            .item-meta {
              display: flex;
              justify-content: space-between;
              align-items: center;
              font-size: 12px;
              color: #909399;

              .source-no {
                flex: 1;
                margin-right: 12px;
              }

              .item-subtotal {
                font-weight: 500;
                color: #67c23a;
                font-family: Monaco, 'Courier New', monospace;
              }
            }
          }
        }
      }
    }

    .right-panel {
      width: 60%;
      background: white;
      border-radius: 6px;
      border: 1px solid #e4e7ed;
      display: flex;
      flex-direction: column;

      .panel-header {
        padding: 16px 20px;
        border-bottom: 1px solid #e4e7ed;
        display: flex;
        justify-content: space-between;
        align-items: center;

        h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: #303133;
        }
      }

      .po-preview {
        flex: 1;
        overflow-y: auto;
        padding: 20px;

        .preview-empty {
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .preview-content {
          display: flex;
          flex-direction: column;
          gap: 20px;

          .supplier-info,
          .items-preview,
          .amount-summary {
            border: 1px solid #e4e7ed;

            h4 {
              margin: 0 0 16px 0;
              font-size: 14px;
              font-weight: 600;
              color: #303133;
            }

            .supplier-details {
              .detail-row {
                display: flex;
                margin-bottom: 8px;

                label {
                  width: 100px;
                  color: #606266;
                  font-weight: 500;
                }

                span {
                  color: #303133;
                }
              }
            }

            .amount-details {
              .amount-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
                
                label {
                  color: #606266;
                  font-weight: 500;
                }

                .money {
                  font-family: Monaco, 'Courier New', monospace;
                  font-weight: 600;
                  color: #409eff;
                }

                &.total {
                  padding-top: 8px;
                  border-top: 1px solid #e4e7ed;
                  margin-top: 8px;

                  label {
                    font-size: 16px;
                    font-weight: 600;
                    color: #303133;
                  }

                  .total-amount {
                    font-size: 18px;
                    color: #67c23a;
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  .money {
    font-family: Monaco, 'Courier New', monospace;
    font-weight: 500;
    color: #409eff;
  }

  /* 加急供應商樣式 */
  .urgent-supplier {
    background-color: #fff2f0 !important;

    &:hover {
      background-color: #ffe7e6 !important;
    }
  }

  .urgent-text {
    color: #cf1322 !important;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .urgent-tag {
    margin-left: 8px;
  }

  /* 加急項目樣式 */
  .urgent-item {
    background-color: #fff2f0 !important;
    border-color: #ff7875 !important;

    &:hover {
      border-color: #cf1322 !important;
      box-shadow: 0 2px 4px rgba(207, 19, 34, 0.15) !important;
    }

    &.selected {
      background-color: #ffe7e6 !important;
      border-color: #cf1322 !important;
    }
  }

  .urgent-item-tag {
    margin: 0 8px;
  }
}

/* Responsive */
@media (max-width: 1200px) {
  .build-candidates {
    .po-builder {
      flex-direction: column;
      height: auto;
      min-height: auto;

      .left-panel,
      .right-panel {
        width: 100%;
      }

      .left-panel {
        .items-list {
          max-height: 400px;
        }
      }

      .right-panel {
        .po-preview {
          max-height: 500px;
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .build-candidates {
    .po-builder {
      .left-panel,
      .right-panel {
        .panel-header {
          padding: 12px 16px;

          h3 {
            font-size: 14px;
          }

          .panel-actions {
            gap: 4px;

            .el-button {
              padding: 6px 12px;
              font-size: 12px;
            }
          }
        }
      }

      .left-panel {
        .items-list {
          padding: 12px 16px;

          .item-row {
            padding: 10px;

            .item-content {
              .item-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 4px;

                .item-name {
                  margin-right: 0;
                }
              }

              .item-details {
                flex-direction: column;
                align-items: flex-start;
                gap: 4px;

                .item-spec {
                  margin-right: 0;
                }
              }

              .item-meta {
                flex-direction: column;
                align-items: flex-start;
                gap: 4px;

                .source-no {
                  margin-right: 0;
                }
              }
            }
          }
        }
      }

      .right-panel {
        .po-preview {
          padding: 16px;

          .preview-content {
            gap: 16px;

            .supplier-info,
            .items-preview,
            .amount-summary {
              h4 {
                font-size: 13px;
              }
            }
          }
        }
      }
    }
  }
}
</style>