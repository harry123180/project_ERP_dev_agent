# ERP System Project Brief
## 企業資源規劃系統專案簡報

---

## Executive Summary | 執行摘要

### Project Overview
This is a comprehensive Enterprise Resource Planning (ERP) system designed to streamline procurement, inventory, and accounting processes for a mid-sized manufacturing company. The system manages the complete lifecycle from requisition to payment, providing role-based access control and real-time status tracking.

### 專案概述
本專案為一個完整的企業資源規劃（ERP）系統，專為中型製造業公司設計，旨在簡化採購、庫存和會計流程。系統管理從請購到付款的完整生命週期，提供基於角色的存取控制和即時狀態追蹤。

---

## Business Objectives | 商業目標

### Primary Goals
1. **Digital Transformation** - Replace manual paper-based processes with digital workflows
2. **Process Automation** - Reduce manual data entry and automate approval workflows
3. **Real-time Visibility** - Provide instant access to procurement and inventory status
4. **Cost Control** - Better manage procurement costs through systematic tracking
5. **Compliance** - Ensure proper approval chains and audit trails

### 主要目標
1. **數位轉型** - 以數位工作流程取代手動紙本流程
2. **流程自動化** - 減少手動資料輸入並自動化審批工作流程
3. **即時可見性** - 提供採購和庫存狀態的即時存取
4. **成本控制** - 通過系統化追蹤更好地管理採購成本
5. **合規性** - 確保適當的審批鏈和審計軌跡

---

## Core Business Processes | 核心業務流程

### 1. Requisition Process | 請購流程
**Purpose**: Enable engineers to request items needed for daily operations or projects

**Key Features**:
- Multi-item requisition creation
- Draft save capability
- Auto-generated requisition numbers
- Purpose classification (daily/project-specific)
- Status tracking (draft/submitted/reviewed/approved)

**Workflow**:
```
Engineer → Create Requisition → Save Draft/Submit → Procurement Review → Approve/Question/Reject
```

### 2. Procurement Process | 採購流程
**Purpose**: Convert approved requisitions into purchase orders for suppliers

**Key Features**:
- Supplier-grouped item consolidation
- Purchase order generation with unique PO numbers
- Real-time price calculation (subtotal, tax, total)
- Multiple supplier management
- Status management (drafted/purchased/shipped)

**Workflow**:
```
Approved Items → Group by Supplier → Create PO → Manual Send → Confirm Purchase → Track Delivery
```

### 3. Receiving & Warehousing | 收貨入庫流程
**Purpose**: Manage goods receipt, warehouse storage, and inventory tracking

**Key Features**:
- Role-agnostic receiving (any authorized user)
- Zone-based warehouse location system
- Multi-tier storage structure (Zone/Shelf/Level/Position)
- Quick inventory addition for non-system purchases
- Acceptance workflow for requesters

**Workflow**:
```
Receive Goods → Confirm Items → Assign Storage Location → User Acceptance → Available in Inventory
```

### 4. Accounting & Payment | 會計請款流程
**Purpose**: Manage supplier invoicing and payment processing

**Key Features**:
- Monthly payment cycle management
- Payment terms handling (30/60 days)
- Automatic invoice generation
- Check payment slip creation
- Discount and deduction management

**Workflow**:
```
Monthly Invoice Review → Generate Payment Request → Issue Check/Transfer → Mark as Paid
```

---

## System Architecture | 系統架構

### Technology Stack | 技術棧

#### Frontend 前端
- **Framework**: Vue.js 3 with Composition API
- **UI Library**: Element Plus
- **State Management**: Pinia
- **Build Tool**: Vite
- **HTTP Client**: Axios

#### Backend 後端
- **Framework**: Flask (Python)
- **ORM**: SQLAlchemy
- **Authentication**: JWT (Flask-JWT-Extended)
- **API Design**: RESTful with CQRS pattern
- **Database**: PostgreSQL 17

#### Security & Infrastructure
- **Authentication**: JWT tokens with refresh mechanism
- **Authorization**: Role-Based Access Control (RBAC)
- **CORS**: Configured for cross-origin requests
- **Data Validation**: Server-side validation with client-side pre-validation

---

## User Roles & Permissions | 使用者角色與權限

### Role Matrix

| Role | Chinese | Key Permissions |
|------|---------|-----------------|
| **Engineer** | 工程師 | Create requisitions, view own items, accept deliveries |
| **Procurement** | 採購員 | Review requisitions, create POs, manage suppliers |
| **ProcurementMgr** | 採購主管 | All procurement permissions + approval authority |
| **Warehouse** | 倉管員 | Receive goods, manage storage, handle inventory |
| **Accountant** | 會計 | Generate invoices, process payments, financial reports |
| **Admin** | 系統管理員 | Full system access, user management, system configuration |

---

## Key Functional Modules | 關鍵功能模組

### 1. Requisition Management | 請購管理
- Create multi-item requisitions
- Save drafts for later submission
- Track approval status
- View requisition history
- Comment and feedback system

### 2. Purchase Order Management | 採購單管理
- Consolidate items by supplier
- Generate professional PO documents
- Calculate pricing with tax
- Track PO lifecycle
- Handle order modifications/cancellations

### 3. Supplier Management | 供應商管理
- Maintain supplier database
- Categorize domestic/international suppliers
- Track payment terms
- Supplier performance metrics
- Contact information management

### 4. Inventory Management | 庫存管理
- Real-time stock levels
- Location-based tracking
- Storage assignment system
- Inventory search and filtering
- Usage tracking and reporting

### 5. Delivery Tracking | 交期維護
- Shipment status updates
- Consolidation warehouse for international orders
- Logistics tracking integration
- Expected arrival dates
- Multi-stage tracking (shipped/in-transit/customs/delivered)

### 6. Financial Management | 財務管理
- Invoice generation
- Payment processing
- Discount management
- Payment term enforcement
- Financial reporting

---

## Implementation Status | 實施狀態

### Completed Features ✅
- User authentication and authorization system
- Requisition creation and management
- Purchase order generation
- Supplier database management
- Basic inventory tracking
- Core API endpoints

### In Progress 🔄
- Frontend-backend integration optimization
- Performance improvements
- Bug fixes for critical workflows
- UI/UX enhancements

### Planned Features 📋
- Advanced reporting and analytics
- Mobile responsive design
- WebSocket for real-time updates
- Integration with external logistics APIs
- Advanced inventory forecasting

---

## Success Metrics | 成功指標

### Quantitative KPIs
- **Process Time Reduction**: 60% reduction in requisition-to-PO time
- **Error Rate**: <1% data entry errors
- **System Uptime**: 99.5% availability
- **User Adoption**: 100% of target users actively using system within 3 months

### Qualitative Goals
- Improved transparency in procurement process
- Better supplier relationship management
- Enhanced inventory visibility
- Streamlined financial reconciliation

---

## Risk Assessment | 風險評估

### Technical Risks
- **Data Migration**: Ensuring accurate transfer from legacy systems
- **Integration**: Compatibility with existing enterprise systems
- **Performance**: Handling peak load during month-end processing

### Business Risks
- **User Adoption**: Resistance to change from manual processes
- **Training**: Ensuring all users are properly trained
- **Process Changes**: Adapting existing workflows to system capabilities

### Mitigation Strategies
- Phased rollout approach
- Comprehensive training program
- Parallel run with existing systems
- Regular feedback and iteration cycles

---

## Project Timeline | 專案時程

### Phase 1: Foundation (Completed)
- System architecture design
- Database schema implementation
- Core API development
- Basic UI components

### Phase 2: Integration (Current)
- Frontend-backend integration
- Authentication and authorization
- Core workflow implementation
- Initial testing and bug fixes

### Phase 3: Optimization (Next)
- Performance tuning
- UI/UX improvements
- Advanced features
- User acceptance testing

### Phase 4: Deployment (Future)
- Production environment setup
- Data migration
- User training
- Go-live support

---

## Conclusion | 結論

This ERP system represents a significant step forward in digitalizing and optimizing business processes. By integrating requisition, procurement, inventory, and accounting functions into a unified platform, the organization can achieve greater efficiency, transparency, and control over its operations.

The system's modular architecture and comprehensive feature set provide a solid foundation for current needs while maintaining flexibility for future growth and enhancement.

本ERP系統代表了業務流程數位化和優化的重要一步。通過將請購、採購、庫存和會計功能整合到統一平台中，組織可以實現更高的效率、透明度和營運控制。

系統的模組化架構和全面的功能集為當前需求提供了堅實的基礎，同時保持了未來增長和增強的靈活性。

---

## Appendix | 附錄

### A. Technical Documentation
- API Documentation
- Database Schema
- Deployment Guide
- User Manual

### B. Business Process Flows
- Detailed workflow diagrams
- Status transition matrices
- Approval hierarchies

### C. Training Materials
- User guides by role
- Video tutorials
- Quick reference cards

---

*Document Version: 1.0*  
*Last Updated: September 2025*  
*Prepared by: Business Analyst - Mary*