# 🚨 CRITICAL BUG REPORT: 採購單建立失敗

**Date:** 2025-09-09  
**Reporter:** Claude QA Automation  
**Severity:** CRITICAL  
**Priority:** HIGH  

## 🔍 Executive Summary

採購單建立功能完全失效。用戶可以成功選擇採購項目並看到預覽，但點擊"建立採購單"後系統返回HTTP 400 Bad Request錯誤，導致採購單無法成功建立。這嚴重影響了采購流程的正常運作。

## 🧪 Test Scenario Executed

### Test Steps:
1. ✅ 導航到採購管理頁面 (http://localhost:5174/purchase-orders)
2. ✅ 點擊"建立採購單"按鈕
3. ✅ 成功加載建立採購單頁面 (http://localhost:5174/purchase-orders/build-candidates)
4. ✅ 選擇供應商：台積電 (顯示56項可採購項目)
5. ✅ 點擊"全選"按鈕，選擇8個採購項目
6. ✅ 確認採購單預覽正確顯示：
   - 項目總計：$19,600
   - 稅額 (5%)：$980.0
   - 總金額：$20,580
7. ✅ 點擊"建立採購單"按鈕
8. ❌ **FAILED:** 確認對話框顯示供應商名稱為"undefined"
9. ❌ **FAILED:** 點擊"確定建立"後返回400 Bad Request錯誤

## 🐛 Bug Details

### Primary Issues:

#### 1. 供應商名稱顯示為 undefined
**問題**: 確認對話框中顯示"確定要為 undefined 建立採購單嗎？"
- **Expected**: 顯示實際供應商名稱 (如"台積電")
- **Actual**: 顯示"undefined"

#### 2. 採購單建立API調用失敗
**問題**: POST 請求返回 HTTP 400 Bad Request
- **API Endpoint**: `POST /api/v1/po`
- **Response**: 400 Bad Request
- **Frontend Error**: "Create PO failed: AxiosError"

### Evidence Captured:

#### Frontend Console Errors:
```javascript
[ERROR] Failed to load resource: the server responded with a status of 400 (BAD REQUEST) @ http://localhost:5000/api/v1/po:0
[ERROR] Create PO failed: AxiosError @ http://localhost:5174/src/views/purchase-orders/BuildCandidates.vue:145
```

#### Backend Log Evidence:
```
127.0.0.1 - - [09/Sep/2025 18:43:37] "OPTIONS /api/v1/po HTTP/1.1" 200 -
127.0.0.1 - - [09/Sep/2025 18:43:37] "POST /api/v1/po HTTP/1.1" 400 -
127.0.0.1 - - [09/Sep/2025 18:48:21] "OPTIONS /api/v1/po HTTP/1.1" 200 -
127.0.0.1 - - [09/Sep/2025 18:48:22] "POST /api/v1/po HTTP/1.1" 400 -
```

#### UI State:
- Frontend successfully displays alert: "建立採購單失敗" (Purchase Order Creation Failed)
- User remains on build-candidates page
- All selected items remain selected
- No navigation occurs

## 🔧 Technical Analysis

### Root Cause Hypotheses:

#### 1. Frontend Data Issues:
- **Supplier Information Missing**: 供應商名稱為undefined表示前端沒有正確獲取或傳遞供應商信息
- **Request Payload Issue**: 可能發送到後端的數據格式不正確或缺少必填字段

#### 2. Backend Validation Failures:
- **Missing Required Fields**: 後端API可能要求某些字段但前端沒有提供
- **Data Type Validation**: 發送的數據類型可能與後端期望的不匹配
- **Business Logic Validation**: 可能觸發了後端的業務邏輯驗證錯誤

#### 3. API Integration Problems:
- **Payload Structure**: 前端發送的JSON結構可能與後端API期望的不同
- **Authentication Issues**: 雖然OPTIONS請求成功，但POST可能有權限問題

### Files to Investigate:

#### Frontend:
- **BuildCandidates.vue:145** - 錯誤發生的具體位置
- 採購單建立的API調用邏輯
- 供應商信息的數據綁定
- 請求payload的構建邏輯

#### Backend:
- **POST /api/v1/po** API endpoint實現
- 採購單創建的驗證邏輯
- 錯誤響應處理
- 數據模型驗證規則

## 📊 Impact Assessment

### Business Impact:
- **CRITICAL**: 採購單完全無法建立
- **BLOCKING**: 整個採購流程被阻斷
- **WORKFLOW**: 從請購單到採購單的轉換無法完成
- **OPERATIONS**: 影響日常採購作業流程

### User Experience Impact:
- 用戶看到功能正常但實際無法使用
- 錯誤信息不夠詳細，難以理解問題
- 供應商名稱顯示為undefined造成困惑

## 🔨 Recommended Development Actions

### Priority 1 (CRITICAL - Fix Immediately):

1. **Backend API Debug**
   - 檢查 POST /api/v1/po endpoint的實現
   - 添加詳細的錯誤日誌，記錄接收到的request payload
   - 驗證API的參數驗證邏輯
   - 確認數據庫模型的必填字段要求

2. **Frontend Request Debug**
   - 檢查BuildCandidates.vue中採購單建立的API調用
   - 驗證發送的payload結構和內容
   - 確認供應商信息的數據綁定是否正確
   - 添加請求攔截器記錄發送的數據

3. **Supply Chain Data Validation**
   - 驗證供應商選擇邏輯
   - 確認供應商ID和名稱的正確傳遞
   - 檢查台積電供應商數據的完整性

### Priority 2 (HIGH - Fix Within 4 Hours):

4. **Error Handling Enhancement**
   - 改善錯誤信息的顯示
   - 提供更詳細的失敗原因
   - 添加用戶友好的錯誤提示

5. **Data Consistency Check**
   - 驗證建立採購單候選頁面的數據完整性
   - 確認項目選擇和供應商關聯的正確性
   - 檢查金額計算邏輯

### Priority 3 (MEDIUM - Testing & Validation):

6. **Comprehensive Testing**
   - 添加採購單建立的單元測試
   - 集成測試覆蓋完整流程
   - API端點的測試用例

## 🧑‍💻 Developer Investigation Steps

### Immediate Actions:
1. **檢查 BuildCandidates.vue:145** 的具體實現
2. **審查 POST /api/v1/po** API的路由處理
3. **驗證採購單數據模型**的必填字段
4. **檢查供應商數據**的獲取和綁定邏輯

### Debug Commands:
```bash
# 檢查後端API實現
grep -r "POST.*\/po" backend/app/routes/
grep -r "def.*create.*po" backend/app/routes/

# 檢查前端API調用
grep -r "api\/v1\/po" frontend/src/
grep -r "Create PO failed" frontend/src/
```

### Test Data Verification:
- 驗證台積電供應商的數據完整性
- 確認選擇的8個採購項目數據正確性
- 檢查計算的金額 $20,580 是否正確

## 📞 Test Environment Details

**Frontend URL**: http://localhost:5174/purchase-orders/build-candidates  
**Backend API**: http://localhost:5000/api/v1/po  
**User**: 系統管理員 (admin)  
**Supplier**: 台積電 (56項可採購項目)  
**Selected Items**: 8項，總計$20,580  
**Timestamp**: 2025-09-09 18:43:37 & 18:48:22  

## ⏰ Timeline Expectations

- **Immediate (0-1 hour)**: 確認並重現bug，識別根本原因
- **Within 2 hours**: 實施修復並進行初步測試
- **Within 4 hours**: 完成全面測試和驗證
- **Within 6 hours**: 部署修復版本到測試環境
- **Within 8 hours**: 生產環境部署和最終驗證

## 🚨 Urgency Level: CRITICAL

此bug完全阻斷了採購流程，需要立即修復。建議：
1. 立即分配給後端和前端開發人員
2. 設置專門的debug session
3. 優先處理此問題，暫停其他非緊急功能開發

---
*This comprehensive bug report was generated by automated QA testing using Playwright MCP browser automation on 2025-09-09.*