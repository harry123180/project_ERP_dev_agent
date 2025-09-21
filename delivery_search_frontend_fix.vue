<!-- 
修復版本的交期維護搜尋功能
主要修復點:
1. 優化搜尋參數處理
2. 添加錯誤處理和用戶反饋
3. 改善API調用邏輯
4. 增加搜尋結果驗證
-->

<!-- 在 DeliveryMaintenance.vue 中需要修復的部分 -->

<script setup lang="ts">
// ... 其他導入保持不變

// 修復後的載入國內資料函數
const loadData = async () => {
  loading.value = true
  try {
    // 清理和驗證搜尋參數
    const searchParams = {
      page: pagination.page,
      page_size: pagination.size,
      status: filters.deliveryStatus?.trim() || '',
      supplier_region: 'domestic',
      po_number: filters.poNumber?.trim() || ''
    }
    
    // 添加搜尋日誌
    console.log('🔍 國內搜尋參數:', searchParams)
    
    // 顯示搜尋指示
    if (searchParams.po_number) {
      ElMessage.info(`正在搜尋採購單號: ${searchParams.po_number}`)
    }
    
    const response = await deliveryApi.getMaintenanceList(searchParams)
    
    console.log('📋 API回應:', response)
    
    if (response.success) {
      deliveryData.value = response.data || []
      pagination.total = response.data?.length || 0
      
      // 更新統計
      updateSummary()
      
      // 搜尋結果反饋
      if (searchParams.po_number) {
        if (response.data.length === 0) {
          ElMessage.warning(`沒有找到採購單號包含 "${searchParams.po_number}" 的國內採購單`)
        } else {
          ElMessage.success(`找到 ${response.data.length} 筆匹配的國內採購單`)
        }
      }
      
      console.log(`✅ 載入成功: ${response.data.length} 筆國內採購單`)
    } else {
      ElMessage.error(response.error || '載入國內資料失敗')
      deliveryData.value = []
      pagination.total = 0
    }
  } catch (error) {
    console.error('❌ 載入國內資料錯誤:', error)
    ElMessage.error('載入國內資料時發生錯誤，請稍後再試')
    deliveryData.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

// 修復後的載入國外資料函數
const loadInternationalData = async () => {
  loadingInt.value = true
  try {
    // 清理和驗證搜尋參數
    const searchParams = {
      page: paginationInt.page,
      page_size: paginationInt.size,
      status: filtersInt.deliveryStatus?.trim() || '',
      supplier_region: 'international',
      po_number: filtersInt.poNumber?.trim() || ''
    }
    
    // 添加搜尋日誌
    console.log('🔍 國外搜尋參數:', searchParams)
    
    // 顯示搜尋指示
    if (searchParams.po_number) {
      ElMessage.info(`正在搜尋採購單號: ${searchParams.po_number}`)
    }
    
    const response = await deliveryApi.getMaintenanceList(searchParams)
    
    console.log('📋 API回應:', response)
    
    if (response.success) {
      internationalData.value = response.data || []
      paginationInt.total = response.data?.length || 0
      
      // 更新統計
      updateSummary()
      
      // 搜尋結果反饋
      if (searchParams.po_number) {
        if (response.data.length === 0) {
          ElMessage.warning(`沒有找到採購單號包含 "${searchParams.po_number}" 的國外採購單`)
        } else {
          ElMessage.success(`找到 ${response.data.length} 筆匹配的國外採購單`)
        }
      }
      
      console.log(`✅ 載入成功: ${response.data.length} 筆國外採購單`)
    } else {
      ElMessage.error(response.error || '載入國外資料失敗')
      internationalData.value = []
      paginationInt.total = 0
    }
  } catch (error) {
    console.error('❌ 載入國外資料錯誤:', error)
    ElMessage.error('載入國外資料時發生錯誤，請稍後再試')
    internationalData.value = []
    paginationInt.total = 0
  } finally {
    loadingInt.value = false
  }
}

// 新增：搜尋輸入框處理函數
const handleSearchInput = (type: 'domestic' | 'international') => {
  // 防抖動處理
  if (type === 'domestic') {
    // 清理輸入
    filters.poNumber = filters.poNumber?.trim() || ''
  } else {
    filtersInt.poNumber = filtersInt.poNumber?.trim() || ''
  }
}

// 新增：搜尋按鈕增強處理
const handleSearch = async (type: 'domestic' | 'international') => {
  try {
    if (type === 'domestic') {
      // 驗證搜尋條件
      if (filters.poNumber && filters.poNumber.length < 2) {
        ElMessage.warning('採購單號至少需要輸入2個字元')
        return
      }
      await loadData()
    } else {
      // 驗證搜尋條件
      if (filtersInt.poNumber && filtersInt.poNumber.length < 2) {
        ElMessage.warning('採購單號至少需要輸入2個字元')
        return
      }
      await loadInternationalData()
    }
  } catch (error) {
    console.error('搜尋處理錯誤:', error)
    ElMessage.error('搜尋處理失敗')
  }
}

// 修復後的重設篩選函數
const resetFilters = async () => {
  // 重設所有篩選條件
  filters.poNumber = ''
  filters.deliveryStatus = ''
  
  // 顯示重設提示
  ElMessage.info('已重設國內篩選條件')
  
  // 重新載入資料
  await loadData()
}

// 修復後的重設國外篩選函數
const resetInternationalFilters = async () => {
  // 重設所有篩選條件
  filtersInt.poNumber = ''
  filtersInt.deliveryStatus = ''
  
  // 顯示重設提示
  ElMessage.info('已重設國外篩選條件')
  
  // 重新載入資料
  await loadInternationalData()
}

// 新增：即時搜尋功能
const enableRealTimeSearch = ref(false)

const handleRealTimeSearch = useDebounceFn((type: 'domestic' | 'international') => {
  if (enableRealTimeSearch.value) {
    if (type === 'domestic') {
      loadData()
    } else {
      loadInternationalData()
    }
  }
}, 500)

// 監聽搜尋輸入的變化
watch(() => filters.poNumber, () => {
  handleRealTimeSearch('domestic')
})

watch(() => filtersInt.poNumber, () => {
  handleRealTimeSearch('international')
})

// 新增：搜尋歷史記錄
const searchHistory = ref<string[]>([])

const addToSearchHistory = (searchTerm: string) => {
  if (searchTerm && !searchHistory.value.includes(searchTerm)) {
    searchHistory.value.unshift(searchTerm)
    // 限制歷史記錄數量
    if (searchHistory.value.length > 10) {
      searchHistory.value = searchHistory.value.slice(0, 10)
    }
  }
}

// 修復後的載入所有資料函數
const loadAllData = async () => {
  try {
    ElMessage.info('正在重新整理所有資料...')
    
    // 並行載入資料
    await Promise.all([
      loadData(),
      loadInternationalData(),
      loadConsolidations()
    ])
    
    ElMessage.success('資料重新整理完成')
  } catch (error) {
    console.error('載入所有資料錯誤:', error)
    ElMessage.error('資料重新整理失敗')
  }
}

// ... 其他函數保持不變

</script>

<!-- 修復後的模板部分 -->
<template>
  <!-- ... 其他部分保持不變 -->
  
  <!-- 國內採購列表篩選條件 - 修復版本 -->
  <div class="filters">
    <el-form :model="filters" inline>
      <el-form-item label="採購單號">
        <el-input 
          v-model="filters.poNumber" 
          placeholder="輸入採購單號搜尋"
          clearable
          @input="handleSearchInput('domestic')"
          @clear="resetFilters"
          @keyup.enter="handleSearch('domestic')"
          style="width: 200px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </el-form-item>
      <el-form-item label="交貨狀態">
        <el-select 
          v-model="filters.deliveryStatus" 
          placeholder="選擇狀態" 
          clearable 
          style="width: 200px"
          @change="loadData"
        >
          <el-option label="全部" value="" />
          <el-option label="未發貨" value="not_shipped" />
          <el-option label="已發貨" value="shipped" />
          <el-option label="已到貨" value="delivered" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button 
          type="primary" 
          @click="handleSearch('domestic')"
          :loading="loading"
        >
          <el-icon><Search /></el-icon>
          搜尋
        </el-button>
        <el-button 
          @click="resetFilters"
          :disabled="loading"
        >
          <el-icon><Refresh /></el-icon>
          重設
        </el-button>
      </el-form-item>
      
      <!-- 新增：搜尋選項 -->
      <el-form-item>
        <el-checkbox 
          v-model="enableRealTimeSearch"
          size="small"
        >
          即時搜尋
        </el-checkbox>
      </el-form-item>
    </el-form>
    
    <!-- 搜尋結果提示 -->
    <div v-if="filters.poNumber" class="search-info">
      <el-tag type="info" size="small">
        搜尋: {{ filters.poNumber }} (找到 {{ deliveryData.length }} 筆)
      </el-tag>
    </div>
  </div>

  <!-- 國外採購列表篩選條件 - 修復版本 -->
  <div class="filters">
    <el-form :model="filtersInt" inline>
      <el-form-item label="採購單號">
        <el-input 
          v-model="filtersInt.poNumber" 
          placeholder="輸入採購單號搜尋"
          clearable
          @input="handleSearchInput('international')"
          @clear="resetInternationalFilters"
          @keyup.enter="handleSearch('international')"
          style="width: 200px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </el-form-item>
      <el-form-item label="交貨狀態">
        <el-select 
          v-model="filtersInt.deliveryStatus" 
          placeholder="選擇狀態" 
          clearable 
          style="width: 200px"
          @change="loadInternationalData"
        >
          <el-option label="全部" value="" />
          <el-option label="未發貨" value="not_shipped" />
          <el-option label="已發貨" value="shipped" />
          <el-option label="物流中" value="in_transit" />
          <el-option label="對方海關" value="foreign_customs" />
          <el-option label="台灣海關" value="taiwan_customs" />
          <el-option label="已到貨" value="delivered" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button 
          type="primary" 
          @click="handleSearch('international')"
          :loading="loadingInt"
        >
          <el-icon><Search /></el-icon>
          搜尋
        </el-button>
        <el-button 
          @click="resetInternationalFilters"
          :disabled="loadingInt"
        >
          <el-icon><Refresh /></el-icon>
          重設
        </el-button>
      </el-form-item>
      
      <!-- 新增：搜尋選項 -->
      <el-form-item>
        <el-checkbox 
          v-model="enableRealTimeSearch"
          size="small"
        >
          即時搜尋
        </el-checkbox>
      </el-form-item>
    </el-form>
    
    <!-- 搜尋結果提示 -->
    <div v-if="filtersInt.poNumber" class="search-info">
      <el-tag type="info" size="small">
        搜尋: {{ filtersInt.poNumber }} (找到 {{ internationalData.length }} 筆)
      </el-tag>
    </div>
  </div>

  <!-- ... 其他部分保持不變 -->
</template>

<style scoped>
.search-info {
  margin-top: 8px;
  margin-bottom: 16px;
}

.filters {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 16px;
}

.filters .el-form-item {
  margin-bottom: 0;
}
</style>