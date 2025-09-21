# ERP 系統狀態同步修復總結

## 問題描述
請購單項目的狀態在採購流程中沒有正確同步更新，導致請購單詳情頁面無法看到最新的狀態變化。

## 修復的問題

### 1. 交期維護狀態同步
**問題**: 在交期維護變更採購單狀態時，請購單項目狀態不會更新
**修復檔案**: `backend/app/routes/delivery.py`
**修復內容**:
- 修正 `po.items` 的迭代問題（加上 `.all()`）
- 新增請購單項目狀態同步邏輯
- 狀態映射：
  - `shipped` → `shipped`
  - `delivered` → `arrived`
  - 其他運輸狀態 → `shipped`

### 2. 收貨管理狀態同步
**問題**: 收貨確認後，請購單項目沒有更新為「已到貨」狀態
**修復檔案**: `backend/app/routes/receiving.py`
**修復內容**:
- 在批次收貨和單項收貨時都加入請購單項目狀態更新
- 收貨確認時將請購單項目狀態更新為 `arrived`

### 3. 驗收管理狀態同步
**問題**: 驗收完成後，請購單項目沒有更新為「已收貨」狀態
**修復檔案**: `backend/app/routes/inventory.py`
**修復內容**:
- 在驗收確認時將請購單項目狀態更新為 `received`
- 同時更新 `acceptance_status` 為 `accepted`

## 狀態流程圖

```
請購單創建 (pending)
    ↓
採購單建立 (purchased)
    ↓
交期維護-已發貨 (shipped)
    ↓
收貨管理-確認收貨 (arrived)
    ↓
驗收管理-驗收通過 (received + accepted)
```

## 測試腳本
- `test_delivery_status_sync.py` - 測試交期維護狀態同步
- `test_receiving_status_sync.py` - 測試收貨管理狀態同步
- `test_acceptance_sync.py` - 測試驗收管理狀態同步
- `test_complete_status_sync.py` - 測試完整流程狀態同步

## 資料庫關聯
- `PurchaseOrderItem.source_detail_id` → `RequestOrderItem.detail_id`
- 透過此外鍵關聯同步狀態更新

## 注意事項
1. 修改後需要重啟後端服務以使變更生效
2. 既有資料可能需要執行修復腳本來更新狀態
3. 前端會自動反映狀態變化，不需要額外修改

## 驗證方法
1. 在交期維護更改採購單狀態
2. 檢查請購單詳情中的項目狀態是否同步更新
3. 執行收貨和驗收流程，確認狀態正確傳遞