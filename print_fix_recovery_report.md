# 列印功能修復回復報告

## 錯誤檢討

### 問題症狀
1. 公司 logo 消失
2. 注意事項內容重複顯示兩次
3. 版面配置混亂

### 根本原因分析

#### 錯誤 1：誤解 overflow 的作用
- **錯誤做法**：將 `overflow: hidden` 改為 `overflow: visible`
- **後果**：導致隱藏的 `.terms-print-content` 也顯示出來，造成內容重複
- **正確理解**：
  - `overflow: hidden` 是為了隱藏超出容器的內容
  - 列印時透過 JavaScript 動態顯示 `.terms-print-content`

#### 錯誤 2：過度調整高度
- **錯誤做法**：將 `max-height` 增加到 50mm
- **後果**：影響整體版面配置，可能導致其他元素（如 logo）被推出可視區域

#### 錯誤 3：沒有測試就大幅修改
- **問題**：沒有逐步測試每個改動的影響
- **教訓**：應該小步修改，每次改動後測試

## 修復方案

### 1. 恢復 overflow 設定
```scss
// 所有 .terms-section 的 overflow 改回 hidden
overflow: hidden !important;  /* 避免內容重複顯示 */
```

### 2. 適度調整高度
```scss
// 從原本的 35mm 適度增加到 45mm（而非 50mm）
.terms-section {
  max-height: 45mm !important;
  min-height: 30mm !important;
}

// .terms-print-content 調整為合理範圍
.terms-print-content {
  min-height: 35mm !important;
  max-height: 42mm !important;
}
```

### 3. 保持列印機制完整性
- 維持 `.el-textarea__inner` 在列印時隱藏
- 維持 `.terms-print-content` 在列印時顯示
- 不破壞原有的顯示/隱藏邏輯

## 修復後狀態

### ✅ 已解決
1. 注意事項不再重複顯示
2. 公司 logo 正常顯示
3. 版面配置恢復正常

### ✅ 保留改善
1. 注意事項有更多空間（45mm vs 35mm）
2. 行距適度增加（1.35）
3. 最小高度確保內容不被截斷（35mm）

## 深刻教訓

1. **理解再修改**：必須完全理解現有機制再進行修改
2. **小步前進**：每次只改一個地方，測試後再繼續
3. **保守原則**：能不改就不改，特別是 overflow 這種關鍵屬性
4. **測試優先**：修改前後都要仔細測試
5. **版本控制**：隨時準備回復到穩定版本

## 總結

這次失敗提醒我：
- 不要輕易改變關鍵的 CSS 屬性（如 overflow）
- 要理解列印樣式的特殊性（display 切換機制）
- 修改要謹慎、測試要充分

現已回復到穩定版本，同時保留了合理的高度調整。