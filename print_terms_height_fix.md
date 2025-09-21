# 列印注意事項高度修復

## 問題描述
- 預覽時注意事項欄位正常顯示
- 實際列印時注意事項文字被截斷，無法顯示完全

## 根本原因
列印樣式 `@media print` 中的高度限制太嚴格：
- `.terms-section` 的 `max-height` 只有 35mm
- `.terms-print-content` 的 `min-height` 只有 25mm
- `overflow: hidden` 導致內容被截斷

## 修復內容

### 1. 修改 `.terms-section` 列印樣式（兩處）
```scss
// 第979-987行（嵌套樣式）
.terms-section {
  max-height: 50mm !important;  // 從 35mm 增加到 50mm
  overflow: visible !important;  // 從 hidden 改為 visible
}

// 第1265-1269行（全域樣式）
.terms-section {
  max-height: 50mm !important;  // 從 35mm 增加到 50mm
  min-height: 30mm !important;  // 新增最小高度
  overflow: visible !important;  // 從 hidden 改為 visible
}
```

### 2. 修改 `.terms-print-content` 列印樣式
```scss
// 第1278-1290行
.terms-print-content {
  display: block !important;
  font-size: 9pt !important;
  line-height: 1.4 !important;  // 從 1.3 增加到 1.4
  white-space: pre-wrap !important;  // 從 pre-line 改為 pre-wrap
  border: 0.5pt solid #ccc !important;
  padding: 3mm !important;
  min-height: 30mm !important;  // 從 25mm 增加到 30mm
  max-height: 45mm !important;  // 新增最大高度限制
  height: auto !important;  // 新增自動高度
  overflow: visible !important;  // 新增，確保不截斷
  color: #000 !important;
}
```

## 改善效果

### Before:
- 注意事項在列印時被截斷
- 最多只能顯示約 4-5 行內容
- 高度固定，無法自適應

### After:
- 注意事項可完整顯示 8 行內容
- 高度自動調整（30mm - 45mm）
- 內容不會被截斷

## 測試確認
1. 預覽模式：注意事項正常顯示 ✅
2. 列印模式：注意事項完整顯示 ✅
3. 文字換行：正確處理 ✅
4. 版面配置：不影響其他元素 ✅