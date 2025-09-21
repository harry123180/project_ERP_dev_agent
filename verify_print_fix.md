# 採購單列印功能修復驗證

## 修復內容

### 1. 移除列印成功訊息
- **檔案**: `frontend/src/views/purchase-orders/PreviewModal.vue`
- **行號**: 572-581
- **修改內容**: 註解掉列印後顯示的成功訊息，避免訊息出現在列印內容中

### 2. 調整金額區塊靠右對齊

#### 一般顯示樣式
- **行號**: 758-779
- **修改內容**:
  - `padding-right`: 從 120px 改為 20px
  - 新增 `display: flex` 和 `justify-content: flex-end`
  - 新增 `white-space: nowrap` 防止標籤換行

#### 列印樣式
- **行號**: 1221-1239
- **修改內容**:
  - `margin`: 從 `5mm 30mm 5mm 0` 改為 `5mm 5mm 5mm 0`（右邊距從 30mm 減少到 5mm）
  - 新增 `align-items: flex-end` 讓內容靠右對齊
  - 在 `.total-row` 新增 `display: flex` 和 `justify-content: flex-end`

## 測試方法

1. 登入採購專員帳號（procurement/proc123）
2. 進入「採購管理」→「採購單管理」
3. 選擇任一採購單，點擊「檢視」按鈕
4. 在預覽視窗中點擊「列印」按鈕
5. 檢查：
   - ✅ 列印預覽中不應顯示「採購單已準備列印」的成功訊息
   - ✅ 小計、稅額、總計應該靠頁面右邊對齊
   - ✅ 金額欄位應該整齊排列

## 改善效果

### Before:
- 列印時會顯示「採購單已成功輸出」的訊息在列印內容中
- 金額區塊距離右邊較遠（padding-right: 120px, margin-right: 30mm）

### After:
- 列印時不再顯示成功訊息
- 金額區塊更靠右對齊，視覺效果更佳
- 使用 flexbox 確保對齊一致性