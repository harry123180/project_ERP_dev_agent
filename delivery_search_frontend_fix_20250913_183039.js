
// 前端修復建議 - DeliveryMaintenance.vue

// 在搜尋方法中添加日誌和錯誤處理：

const loadData = async () => {
  loading.value = true
  try {
    console.log('搜尋參數:', {
      page: pagination.page,
      page_size: pagination.size,
      status: filters.deliveryStatus,
      supplier_region: 'domestic',
      po_number: filters.poNumber
    })
    
    const response = await deliveryApi.getMaintenanceList({
      page: pagination.page,
      page_size: pagination.size,
      status: filters.deliveryStatus,
      supplier_region: 'domestic',
      po_number: filters.poNumber.trim() // 清除空白字元
    })
    
    console.log('API回應:', response)
    
    if (response.success) {
      deliveryData.value = response.data
      pagination.total = response.data.length
      updateSummary()
      
      if (filters.poNumber && response.data.length === 0) {
        ElMessage.warning('沒有找到符合條件的採購單')
      }
    } else {
      ElMessage.error(response.error || '搜尋失敗')
    }
  } catch (error) {
    console.error('搜尋錯誤:', error)
    ElMessage.error('搜尋功能異常，請稍後再試')
  } finally {
    loading.value = false
  }
}

// 添加輸入驗證
const handleSearchInput = () => {
  // 自動觸發搜尋或添加防抖動
  if (filters.poNumber.length >= 2 || filters.poNumber.length === 0) {
    loadData()
  }
}
