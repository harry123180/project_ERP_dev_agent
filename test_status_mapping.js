// 測試交期維護頁面的狀態映射功能
// 可在瀏覽器控制台中執行

console.log('🔧 交期維護狀態映射測試');
console.log('=' * 50);

// 模擬前端狀態映射函數
const getStatusLabel = (status) => {
  const statusMap = {
    'not_shipped': '未發貨',
    'shipped': '已發貨',
    'foreign_customs': '對方海關',
    'taiwan_customs': '台灣海關',
    'in_transit': '物流',
    'delivered': '已到貨'
  };
  return statusMap[status] || status;
};

const getDomesticStatusLabel = (status) => {
  const statusMap = {
    'not_shipped': '未發貨',
    'shipped': '已發貨',
    'delivered': '已到貨'
  };
  return statusMap[status] || status;
};

const getStatusType = (status) => {
  const typeMap = {
    'not_shipped': 'info',
    'shipped': '',
    'foreign_customs': 'danger',
    'taiwan_customs': 'danger',
    'in_transit': 'warning',
    'delivered': 'success'
  };
  return typeMap[status] || 'info';
};

// 測試狀態映射
const testStatuses = ['in_transit', 'delivered', 'shipped', 'not_shipped', 'foreign_customs', 'taiwan_customs'];

console.log('\n📋 國外採購狀態映射測試:');
testStatuses.forEach(status => {
  const label = getStatusLabel(status);
  const type = getStatusType(status);
  console.log(`${status.padEnd(15)} -> ${label.padEnd(10)} (${type})`);
});

console.log('\n📋 國內採購狀態映射測試:');
['not_shipped', 'shipped', 'delivered'].forEach(status => {
  const label = getDomesticStatusLabel(status);
  const type = getStatusType(status);
  console.log(`${status.padEnd(15)} -> ${label.padEnd(10)} (${type})`);
});

// 測試問題案例
console.log('\n🎯 問題案例測試:');
const problemData = [
  { po_number: 'PO20250913140045SUP001004', delivery_status: 'in_transit', supplier_name: '台積電材料供應商' },
  { po_number: 'PO20250913140045SUP001003', delivery_status: 'in_transit', supplier_name: '台積電材料供應商' }
];

problemData.forEach(row => {
  const statusLabel = getStatusLabel(row.delivery_status);
  const statusType = getStatusType(row.delivery_status);
  const deliveryLabel = row.delivery_status === 'delivered' ? '已到貨' : '未到貨';
  
  console.log(`採購單號: ${row.po_number}`);
  console.log(`供應商: ${row.supplier_name}`);
  console.log(`交貨狀態: ${deliveryLabel}`);
  console.log(`物流狀態: ${statusLabel} (${statusType})`);
  console.log('---');
});

console.log('\n✅ 測試完成！');
console.log('現在前端應該正確顯示：');
console.log('- "in_transit" -> "物流"');
console.log('- 狀態顯示為中文而非英文');