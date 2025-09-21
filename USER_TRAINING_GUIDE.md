# ERP System User Training Guide

**Version:** 1.0  
**Training Effective Date:** September 7, 2025  
**System Version:** ERP Management System v1.0  

---

## 🎯 Training Overview

This comprehensive training guide prepares users for effective operation of the ERP Management System across all business functions from requisition creation to financial processing. The system supports complete workflows in both English and Chinese languages.

### **Learning Objectives**
After completing this training, users will be able to:
- Navigate the ERP system interface effectively
- Execute role-specific workflows efficiently  
- Understand the complete business process flow
- Handle common scenarios and troubleshooting
- Maintain data accuracy and security compliance

### **Training Structure**
- **Module 1**: System Overview & Navigation
- **Module 2**: Authentication & Security
- **Module 3**: Role-Specific Workflows
- **Module 4**: Business Process Integration
- **Module 5**: Troubleshooting & Support

---

## 📚 Module 1: System Overview & Navigation

### **System Access Information**
- **Application URL**: `http://localhost:5177`
- **Supported Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **System Availability**: 24/7 with scheduled maintenance windows
- **Mobile Support**: Responsive design for tablet access

### **User Interface Overview**

#### **Main Navigation Structure**
```
┌─────────────────────────────────────────────────┐
│ ERP Management System        [User] [Logout]    │
├─────────────────────────────────────────────────┤
│ 📊 Dashboard  │  Main Content Area              │
│ 📝 請購管理   │                                 │
│ 🛒 採購管理   │  [Current Module Content]       │
│ 📦 庫存管理   │                                 │
│ 💰 會計管理   │                                 │
│ 🏢 供應商管理 │                                 │
│ ⚙️ 系統管理   │                                 │
└─────────────────────────────────────────────────┘
```

#### **Common Interface Elements**
- **Search Bars**: Global search functionality across modules
- **Filter Controls**: Advanced filtering for data tables
- **Action Buttons**: Primary (blue), Secondary (gray), Danger (red)
- **Status Indicators**: Color-coded status badges
- **Pagination**: Navigate through large datasets
- **Export Functions**: Excel/PDF export capabilities

### **Language Support**
The system supports bilingual operation:
- **English**: Complete interface and documentation
- **中文**: Native Chinese support for business terms
  - 請購 (Requisition)
  - 採購 (Procurement)  
  - 庫存 (Inventory)
  - 會計 (Accounting)
  - 消耗品 (Consumables)
  - 固定資產 (Fixed Assets)

---

## 🔐 Module 2: Authentication & Security

### **Login Process**
1. Navigate to `http://localhost:5177`
2. Enter username and password
3. Click "登入" (Login) button
4. System redirects to appropriate dashboard based on role

### **User Roles & Permissions**

| Role | Username | Password | Access Level | Key Responsibilities |
|------|----------|----------|-------------|-------------------|
| **管理員 (Admin)** | `admin` | `admin123` | Full system access | User management, system configuration, all module access |
| **採購專員 (Procurement)** | `procurement` | `proc123` | Procurement operations | Requisition approval, PO management, supplier relations |
| **工程師 (Engineer)** | `engineer` | `eng123` | Request creation | Requisition creation, status monitoring, inventory queries |

### **Security Best Practices**
- **Password Security**: Change default passwords immediately in production
- **Session Management**: System automatically logs out after 1 hour of inactivity
- **Token Refresh**: Authentication tokens refresh automatically during active sessions
- **Access Control**: Each role has specific permissions - attempting unauthorized access returns error messages
- **Audit Trail**: All user actions are logged for security and compliance

### **Multi-Factor Authentication (Future Enhancement)**
- Currently single-factor authentication with secure password policies
- Future releases will include 2FA/MFA options
- Integration with enterprise identity providers planned

---

## 👥 Module 3: Role-Specific Workflows

## 🔧 Engineer (工程師) Workflows

### **Primary Responsibilities**
- Create and submit purchase requisitions
- Monitor requisition approval status
- Query inventory availability  
- Track project material requirements

### **Workflow 1: Creating a Purchase Requisition**

#### **Step-by-Step Process:**

**Step 1: Access Requisition Module**
```
1. Login with engineer/eng123
2. Click "請購管理" (Requisition Management) in left navigation
3. Click "新增請購單" (New Requisition) button
```

**Step 2: Fill Basic Information**
```
請購單基本資訊 (Requisition Basic Information):
- 專案代碼 (Project Code): Select from dropdown
- 請購人 (Requester): Auto-filled with your name  
- 申請日期 (Request Date): Auto-filled with current date
- 預計交期 (Expected Delivery): Select target delivery date
- 優先等級 (Priority): 一般/緊急/特急 (Normal/Urgent/Critical)
- 請購事由 (Requisition Reason): Detailed explanation
```

**Step 3: Add Line Items**
```
For each item needed:
1. Click "新增項目" (Add Item)
2. Fill item details:
   - 項目描述 (Item Description): Detailed specifications
   - 數量 (Quantity): Required amount
   - 單位 (Unit): 個/組/套/公斤/米 etc.
   - 預估單價 (Estimated Unit Price): Budget estimate
   - 使用性質 (Usage Type): 
     * 消耗品 (Consumables)
     * 固定資產 (Fixed Assets)
     * 維修耗材 (Maintenance Materials)
     * 辦公用品 (Office Supplies)
   - 技術規格 (Technical Specs): Detailed requirements
   - 建議供應商 (Suggested Supplier): Optional recommendation
```

**Step 4: Review and Submit**
```
1. Review all information for accuracy
2. Check calculated total amount
3. Add any additional notes in 備註 (Remarks)
4. Click "提交審核" (Submit for Review)
5. System generates unique requisition number
6. Email notification sent to procurement team
```

#### **Example Requisition Creation:**
```
Project Code: PRJ-2025-001
Requester: John Engineer
Expected Delivery: 2025-09-15
Priority: 一般 (Normal)
Reason: 新產品開發所需電子元件 (Electronic components for new product development)

Line Items:
1. 描述: ARM微處理器 STM32F407VGT6
   數量: 10
   單位: 個
   預估單價: $15.00
   使用性質: 消耗品
   規格: 168MHz, 1MB Flash, 192KB SRAM
   
2. 描述: 工業級電阻器包 (1% 精度)
   數量: 5
   單位: 組  
   預估單價: $25.00
   使用性質: 消耗品
   規格: E24系列, 0.25W, 1Ω-10MΩ
```

### **Workflow 2: Monitoring Requisition Status**

#### **Status Tracking Process:**
```
1. Navigate to "請購管理" → "我的請購單" (My Requisitions)
2. View status dashboard with color-coded indicators:
   - 🟡 待審核 (Pending Review)
   - 🔵 審核中 (Under Review)  
   - 🟢 已核准 (Approved)
   - 🔴 已拒絕 (Rejected)
   - 🟣 部分核准 (Partially Approved)

3. Click requisition number for detailed status
4. View line-by-line approval status
5. Read approver comments and feedback
6. Monitor purchase order generation
7. Track delivery milestones
```

#### **Status Details View:**
```
請購單號: REQ-2025-001234
當前狀態: 審核中 (Under Review)
提交時間: 2025-09-07 09:15:23
審核進度:
  ✅ 初審通過 (Initial Review Passed)
  🔄 採購審核中 (Procurement Review In Progress)
  ⏸️ 待主管核准 (Pending Supervisor Approval)
  ⏸️ 待採購執行 (Pending Procurement Execution)

項目審核狀態:
1. ARM微處理器: ✅ 核准 (Approved) - 建議供應商: TechCorp
2. 電阻器包: 🔄 審核中 (Under Review) - 等待技術確認
```

### **Workflow 3: Inventory Query and Availability Check**

#### **Inventory Search Process:**
```
1. Navigate to "庫存管理" → "庫存查詢" (Inventory Query)
2. Use search filters:
   - 項目名稱 (Item Name): Text search
   - 項目編號 (Item Code): Exact code match
   - 類別 (Category): Dropdown selection
   - 庫存狀態 (Stock Status): 有庫存/缺貨/預警 (In Stock/Out of Stock/Low Stock)
   - 儲存位置 (Storage Location): Zone/Shelf filtering
   
3. Review search results:
   - 當前庫存量 (Current Stock Level)
   - 最小庫存量 (Minimum Stock Level)  
   - 最後更新時間 (Last Updated)
   - 儲存位置 (Storage Location)
   - 預留數量 (Reserved Quantity)
```

#### **Example Inventory Query:**
```
Search: "ARM微處理器"
Results:
┌──────────────────┬─────────┬─────────┬──────────┬─────────────┐
│ 項目描述          │ 現有庫存 │ 最小庫存 │ 可用數量  │ 儲存位置     │
├──────────────────┼─────────┼─────────┼──────────┼─────────────┤
│ STM32F407VGT6    │ 25      │ 10      │ 20       │ A1-B3-F2    │
│ STM32F103C8T6    │ 15      │ 5       │ 12       │ A1-B2-F1    │
│ STM32H743VIT6    │ 8       │ 5       │ 8        │ A2-B1-F3    │
└──────────────────┴─────────┴─────────┴──────────┴─────────────┘
```

---

## 🛒 Procurement Specialist (採購專員) Workflows  

### **Primary Responsibilities**
- Review and approve/reject requisitions
- Manage supplier relationships
- Generate and process purchase orders
- Coordinate shipping and delivery
- Process receiving confirmations

### **Workflow 1: Requisition Review and Approval**

#### **Daily Approval Process:**
```
1. Login with procurement/proc123
2. Navigate to "請購管理" → "待審核請購單" (Pending Requisitions)
3. Review dashboard showing:
   - 新提交 (Newly Submitted)
   - 審核中 (Under Review)
   - 逾期待處理 (Overdue)
   - 優先處理 (High Priority)
```

#### **Individual Requisition Review:**
```
1. Click requisition number to open detailed view
2. Review requisition information:
   - 請購人資訊 (Requester Information)
   - 專案詳情 (Project Details)  
   - 預算核實 (Budget Verification)
   - 技術規格確認 (Technical Specification Review)
   
3. For each line item, evaluate:
   - 技術可行性 (Technical Feasibility)
   - 預算合理性 (Budget Reasonableness)
   - 供應商可用性 (Supplier Availability)
   - 交期可達成性 (Delivery Timeline Feasibility)
   
4. Make approval decisions:
   - ✅ 核准 (Approve): Item meets all criteria
   - 🔄 條件核准 (Conditional Approval): Approve with modifications  
   - 🔴 拒絕 (Reject): Specify rejection reason
   - 💬 需要澄清 (Needs Clarification): Request additional information
```

#### **Approval Decision Examples:**
```
項目: ARM微處理器 STM32F407VGT6
決策: ✅ 核准 (Approved)
採購建議:
- 建議供應商: TechCorp (最優價格)
- 建議數量: 15個 (含10%安全庫存)
- 預計交期: 14個工作天
- 核准金額: $225.00 (15 × $15.00)
審核備註: 規格符合需求，供應商可靠，價格合理

項目: 特殊感測器
決策: 🔄 條件核准 (Conditional Approval)  
修改建議:
- 原始數量: 5個 → 建議數量: 3個 (考慮預算限制)
- 替代規格: 建議使用標準型號替代客製化版本
審核備註: 預算超標，建議採用替代方案
```

### **Workflow 2: Purchase Order Generation and Management**

#### **Purchase Order Creation Process:**
```
1. Navigate to "採購管理" → "採購訂單" (Purchase Orders)
2. Click "從請購單生成" (Generate from Requisitions)
3. Select approved requisition items
4. Group items by supplier for optimal efficiency
5. Create purchase orders:
   - 供應商選擇 (Supplier Selection)
   - 付款條件 (Payment Terms)
   - 交貨條件 (Delivery Terms)
   - 特殊要求 (Special Requirements)
```

#### **Purchase Order Details:**
```
採購訂單號: PO-2025-001234
供應商: TechCorp Electronics Ltd.
訂單日期: 2025-09-07
預計交期: 2025-09-21
付款條件: NET 30
貨運方式: 標準配送 (Standard Delivery)

訂單項目:
1. STM32F407VGT6 × 15個 @ $15.00 = $225.00
2. 工業電阻器包 × 3組 @ $25.00 = $75.00

小計: $300.00
稅額 (8%): $24.00
運費: $15.00
總計: $339.00

特殊說明:
- 所有IC需提供原廠證明書
- 包裝需防靜電保護
- 收貨地址: 公司研發部門
```

### **Workflow 3: Supplier Management**

#### **Supplier Database Management:**
```
1. Navigate to "供應商管理" (Supplier Management)
2. Supplier information includes:
   - 基本資訊 (Basic Information)
   - 聯絡方式 (Contact Information)
   - 財務條件 (Financial Terms)
   - 品質評等 (Quality Rating)
   - 交期表現 (Delivery Performance)
   - 認證狀態 (Certification Status)
```

#### **Supplier Performance Tracking:**
```
供應商: TechCorp Electronics
評等: A級 (4.8/5.0)
合作年期: 3年

績效指標:
- 準時交貨率: 96% (優秀)
- 品質合格率: 99.2% (優秀)  
- 價格競爭力: 良好 (行業前25%)
- 技術支援: 優秀 (快速響應)
- 財務穩定性: 穩定 (定期評估)

最近交易:
- 2025-09-01: PO-001230 ($1,250) - 準時交貨
- 2025-08-15: PO-001225 ($890) - 準時交貨  
- 2025-07-28: PO-001220 ($2,150) - 延遲1天
```

---

## 👨‍💼 Administrator (管理員) Workflows

### **Primary Responsibilities**
- System configuration and maintenance
- User account management
- Role and permission assignment
- System monitoring and audit trail review
- Master data maintenance

### **Workflow 1: User Management**

#### **Creating New Users:**
```
1. Navigate to "系統管理" → "用戶管理" (User Management)
2. Click "新增用戶" (Add User)
3. Fill user information:
   - 用戶名 (Username): Unique identifier
   - 全名 (Full Name): Display name  
   - 電子郵件 (Email): Contact email
   - 角色 (Role): Select from available roles
   - 部門 (Department): User's department
   - 職位 (Position): Job title
   - 電話 (Phone): Contact number
   - 狀態 (Status): 啟用/停用 (Active/Inactive)
```

#### **Role Assignment and Permissions:**
```
Available Roles:
1. 系統管理員 (System Administrator)
   - Full system access
   - User management
   - System configuration
   - All module access
   
2. 採購專員 (Procurement Specialist)  
   - Requisition approval
   - Purchase order management
   - Supplier management
   - Inventory viewing
   
3. 工程師 (Engineer)
   - Requisition creation
   - Status monitoring  
   - Inventory query
   - Limited reporting
   
4. 會計人員 (Accounting Staff)
   - Financial processing
   - Billing management
   - Payment processing
   - Financial reporting
   
5. 倉庫管理員 (Warehouse Manager)
   - Inventory management
   - Receiving processing
   - Storage assignment
   - Stock level monitoring
```

### **Workflow 2: System Configuration**

#### **System Settings Management:**
```
1. Navigate to "系統管理" → "系統設定" (System Settings)
2. Configuration categories:
   
   基本設定 (Basic Settings):
   - 公司資訊 (Company Information)
   - 預設幣別 (Default Currency)
   - 時區設定 (Timezone Configuration)
   - 語言設定 (Language Settings)
   
   安全設定 (Security Settings):
   - 密碼政策 (Password Policy)
   - 登入嘗試限制 (Login Attempt Limits)
   - 會話逾時 (Session Timeout)
   - 雙重驗證 (Two-Factor Authentication)
   
   工作流程設定 (Workflow Settings):
   - 審核流程 (Approval Workflows)
   - 通知規則 (Notification Rules)
   - 自動化規則 (Automation Rules)
   - 文件範本 (Document Templates)
```

### **Workflow 3: Audit Trail and Monitoring**

#### **System Activity Monitoring:**
```
1. Navigate to "系統管理" → "稽核記錄" (Audit Trail)
2. Filter options:
   - 日期範圍 (Date Range)
   - 用戶 (User)
   - 操作類型 (Action Type)
   - 模組 (Module)
   - IP位址 (IP Address)
   
3. Review logged activities:
   - 登入/登出 (Login/Logout)
   - 資料修改 (Data Changes)
   - 權限變更 (Permission Changes)
   - 系統設定修改 (System Configuration Changes)
```

---

## 🔄 Module 4: Business Process Integration

### **Complete ERP Workflow: End-to-End Process**

#### **Phase 1: Requisition Creation (請購建立)**
```
Engineer Actions:
1. Identify material needs for project
2. Create requisition with detailed specifications
3. Add multiple line items as needed
4. Submit for procurement review
5. Monitor approval status

System Actions:
- Generate unique requisition number
- Send notification to procurement team
- Log all actions in audit trail
- Update requisition status automatically
```

#### **Phase 2: Approval Process (審批流程)**  
```
Procurement Actions:
1. Review requisition for technical feasibility
2. Verify budget availability
3. Evaluate supplier options
4. Make line-by-line approval decisions
5. Add procurement recommendations

System Actions:
- Update approval status in real-time
- Send notifications to requester
- Generate approval workflow tracking
- Prepare for purchase order creation
```

#### **Phase 3: Purchase Order Generation (採購訂單生成)**
```
Procurement Actions:
1. Group approved items by supplier
2. Generate purchase orders with terms
3. Send POs to suppliers
4. Track confirmation responses
5. Monitor delivery commitments

System Actions:
- Create PO numbers automatically
- Calculate totals including tax/shipping
- Update inventory reservations
- Schedule delivery tracking
```

#### **Phase 4: Shipping and Receiving (物流收貨)**
```
Procurement/Warehouse Actions:
1. Monitor supplier shipping notifications
2. Update delivery status milestones
3. Prepare receiving area for delivery
4. Perform quality inspection upon receipt
5. Confirm quantities and specifications

System Actions:
- Update shipping status automatically
- Generate receiving documents
- Update inventory levels upon confirmation
- Trigger payment processing workflows
```

#### **Phase 5: Financial Processing (財務處理)**
```
Accounting Actions:
1. Generate invoices from confirmed receipts
2. Verify invoice accuracy against POs
3. Process supplier payments
4. Update financial records
5. Generate financial reports

System Actions:
- Create billing batches automatically
- Calculate payment amounts with terms
- Update supplier account balances
- Generate audit trail for all transactions
```

### **Cross-Module Data Integration**

#### **Data Flow Between Modules:**
```
請購管理 → 採購管理:
- Approved requisitions become purchase orders
- Requester information transfers to PO
- Technical specifications carry forward
- Budget allocations link to financial tracking

採購管理 → 庫存管理:
- Purchase orders create inventory reservations
- Receiving confirmations update stock levels
- Storage assignments track item locations
- Quality status affects availability

庫存管理 → 會計管理:
- Received items trigger billing processes
- Inventory valuations affect financial reports
- Cost allocations update project budgets
- Asset classifications determine depreciation
```

### **Real-Time Status Synchronization**

#### **Status Updates Across Modules:**
```
When Engineer submits requisition:
- 請購管理: Status = "待審核" (Pending Review)
- Dashboard: New notification for procurement
- 稽核記錄: Log requisition creation

When Procurement approves items:
- 請購管理: Status = "已核准" (Approved)  
- 採購管理: Ready for PO generation
- Notification: Email to original requester

When PO is confirmed:
- 採購管理: Status = "已確認" (Confirmed)
- 庫存管理: Items reserved for delivery
- 會計管理: Financial commitment recorded

When items are received:
- 庫存管理: Stock levels updated
- 採購管理: PO status = "已完成" (Completed)
- 會計管理: Invoice generation triggered
```

---

## 🔧 Module 5: Troubleshooting & Support

### **Common Issues and Solutions**

#### **Login and Authentication Issues**

**Issue: Cannot login with correct credentials**
```
Possible Causes:
- Account may be disabled
- Password may have expired
- Browser cache issues
- Server connection problems

Solutions:
1. Clear browser cache and cookies
2. Try different browser or incognito mode  
3. Contact system administrator to check account status
4. Verify system is accessible (check with other users)
5. Check network connection and firewall settings
```

**Issue: Session expires frequently**
```
Cause: System security settings
Solution: 
- Normal session timeout is 1 hour for security
- Save work frequently to prevent data loss
- System will warn 5 minutes before timeout
- Activity refreshes session automatically
```

#### **Data Entry and Validation Issues**

**Issue: Cannot save requisition - validation errors**
```
Common Validation Rules:
- 項目描述 (Item Description): Required, minimum 10 characters
- 數量 (Quantity): Must be positive number
- 預估單價 (Estimated Price): Must be positive number
- 預計交期 (Expected Date): Must be future date
- 使用性質 (Usage Type): Must select from dropdown

Solution: Check all required fields marked with red asterisk (*)
```

**Issue: Supplier not found in dropdown**
```
Possible Causes:
- Supplier not activated in system
- Supplier record incomplete
- User lacks permission to view supplier

Solutions:
1. Contact procurement team to activate supplier
2. Use "建議新供應商" (Suggest New Supplier) field
3. Contact administrator for permission review
```

#### **Performance and Loading Issues**

**Issue: System loading slowly**
```
Troubleshooting Steps:
1. Check internet connection speed
2. Clear browser cache
3. Close unnecessary browser tabs
4. Try different browser
5. Check system status with IT team

Optimization Tips:
- Use search filters to limit data displayed
- Export large datasets instead of viewing online
- Avoid opening multiple browser windows to same system
```

**Issue: Export/Print functions not working**
```
Solutions:
1. Allow pop-ups in browser settings
2. Check PDF viewer is installed and updated
3. Try exporting to Excel format instead
4. Ensure adequate disk space for downloads
5. Contact IT if organizational firewall blocks downloads
```

### **System Limitations and Workarounds**

#### **Known Limitations**
```
1. Maximum Upload File Size: 100MB per document
   Workaround: Compress large files or use cloud sharing links

2. Concurrent User Limit: 50 simultaneous users
   Workaround: System queues additional users with estimated wait time

3. Report Generation Time: Large reports may take 2-5 minutes
   Workaround: Schedule reports during off-peak hours

4. Browser Compatibility: Internet Explorer not supported
   Workaround: Use Chrome, Firefox, Safari, or Edge browsers
```

#### **Data Backup and Recovery**
```
System automatically backs up data:
- Real-time: All transactions saved immediately
- Hourly: Incremental backups of changed data
- Daily: Full system backup at 2:00 AM
- Weekly: Complete database backup retained for 3 months

User Responsibilities:
- Save work frequently using Save buttons
- Export important reports for local storage
- Do not rely on browser bookmark for unsaved work
- Contact IT immediately if data appears incorrect
```

### **Getting Help and Support**

#### **Support Levels**

**Level 1: Self-Service (First Try)**
```
Available Resources:
- This User Training Guide
- Online Help tooltips (? icons)  
- System Status page
- FAQ section in system Help menu
- Video tutorials (when available)
```

**Level 2: Peer Support (Department Level)**
```
Department Contacts:
- Engineering: Senior Engineer (requisition questions)
- Procurement: Procurement Manager (approval processes)
- IT: Help Desk (technical issues)
- Accounting: Finance Manager (financial workflows)
```

**Level 3: System Administrator**
```
Contact for:
- User account issues
- Permission problems
- System configuration questions
- Data integrity concerns
- Security incidents

Response Time: Within 4 business hours
```

**Level 4: Technical Support**
```
Escalation for:
- System outages
- Data corruption
- Performance degradation
- Security vulnerabilities

Contact: IT Department Emergency Line
Response Time: Within 1 hour for critical issues
```

#### **Reporting Issues Effectively**

**Include This Information:**
```
1. User Information:
   - Username (never include password)
   - Role/Department
   - Browser and version
   
2. Issue Details:
   - What you were trying to do
   - What happened instead  
   - Error messages (exact text or screenshot)
   - Time when issue occurred
   
3. Steps to Reproduce:
   - List specific steps taken
   - Include any specific data used
   - Note if issue happens consistently
   
4. Business Impact:
   - How urgent is the issue
   - How many users affected
   - Workaround being used (if any)
```

### **Emergency Procedures**

#### **System Outage Response**
```
If system is completely unavailable:
1. Check system status page for maintenance notifications
2. Try accessing from different browser/device
3. Contact other users to confirm outage scope
4. Contact IT Help Desk immediately
5. Document critical work that cannot wait
6. Use backup procedures if available

Expected Response:
- IT acknowledgment within 15 minutes
- Status updates every 30 minutes during outage
- Estimated restoration time provided when known
```

#### **Data Emergency Response**
```
If data appears missing or corrupted:
1. Do NOT continue working in affected area
2. Document exactly what data seems incorrect
3. Note the last time data appeared correct
4. Take screenshots of issue if possible
5. Contact system administrator immediately
6. Preserve any backup copies you may have

Critical: Do not attempt to "fix" data issues yourself
```

---

## ✅ Training Completion Checklist

### **Engineer (工程師) Competency**
- [ ] Can login successfully and navigate interface
- [ ] Can create complete requisition with multiple line items
- [ ] Understands usage types (消耗品, 固定資產, etc.)
- [ ] Can monitor requisition approval status
- [ ] Can perform inventory queries effectively
- [ ] Knows how to get help when needed

### **Procurement Specialist (採購專員) Competency**  
- [ ] Can review and approve/reject requisitions
- [ ] Understands supplier evaluation criteria
- [ ] Can generate purchase orders from approved requisitions
- [ ] Can manage supplier information effectively
- [ ] Understands complete procurement workflow
- [ ] Can coordinate with other departments

### **Administrator (管理員) Competency**
- [ ] Can create and manage user accounts
- [ ] Understands role-based permissions
- [ ] Can configure system settings
- [ ] Can review audit trails and system activity
- [ ] Knows emergency response procedures
- [ ] Can provide user support and training

### **All Users - General Competency**
- [ ] Understands system security requirements
- [ ] Can troubleshoot common issues independently
- [ ] Knows how to report problems effectively
- [ ] Understands data backup and recovery procedures
- [ ] Can work efficiently within role permissions
- [ ] Knows escalation procedures for critical issues

---

## 📊 Training Assessment

### **Practical Exercise: Complete Workflow Test**

**Scenario**: New product development requires electronic components
**Participants**: Engineer, Procurement Specialist, Administrator

**Exercise Steps:**
1. **Engineer**: Create requisition for development project components
2. **Procurement**: Review and approve requisition with supplier selection
3. **System**: Generate purchase order automatically
4. **Procurement**: Confirm PO and track delivery status
5. **Administrator**: Monitor process and review audit trail

**Success Criteria:**
- Requisition created with complete technical specifications
- Approval process completed with proper documentation  
- Purchase order generated with accurate supplier information
- All status updates reflected correctly across modules
- Audit trail captures all user actions accurately

**Time Allocation**: 90 minutes total
- Setup: 15 minutes
- Execution: 60 minutes  
- Review: 15 minutes

### **Knowledge Assessment Questions**

#### **For Engineers:**
1. What information is required when creating a requisition?
2. How do you check inventory availability before submitting requests?
3. What should you do if your requisition is partially rejected?
4. How can you track the status of purchase orders generated from your requisitions?

#### **For Procurement Specialists:**
1. What criteria should you evaluate when approving requisitions?
2. How do you select appropriate suppliers for approved items?
3. What information must be included in purchase orders?
4. How do you handle supplier delivery delays?

#### **For Administrators:**
1. How do you create user accounts with appropriate permissions?
2. What system settings require regular monitoring?
3. How do you investigate issues reported by users?
4. What procedures should be followed during system outages?

---

**Training Guide Version**: 1.0  
**Last Updated**: September 7, 2025  
**Next Review**: After 30 days of system operation  
**Training Coordinator**: Product Management Team

*This training guide provides comprehensive preparation for effective ERP system operation. Users should complete role-specific training modules and pass competency assessments before independent system operation.*