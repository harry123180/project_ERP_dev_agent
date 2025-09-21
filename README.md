# ERP System - Enterprise Resource Planning

A comprehensive ERP (Enterprise Resource Planning) system built with modern web technologies, featuring complete workflows from requisition management to financial operations.

## 🏗️ System Architecture

### **Backend** - Flask + PostgreSQL
- **Framework**: Flask 3.0 with RESTful API design
- **Database**: PostgreSQL 17 with SQLAlchemy ORM
- **Authentication**: JWT with role-based access control (RBAC)
- **Architecture**: CQRS pattern with thin controllers, fat services

### **Frontend** - Vue.js 3 + TypeScript
- **Framework**: Vue.js 3 with Composition API
- **UI Library**: Element Plus with responsive design
- **State Management**: Pinia for reactive state
- **Build Tool**: Vite with TypeScript support

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+

### Backend Setup

1. **Install Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

2. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

3. **Database Setup**
```bash
# Create PostgreSQL database
createdb erp_system

# Initialize database and create sample data
flask init-db
flask seed-db
```

4. **Run Backend Server**
```bash
python app.py
# Server runs on http://localhost:5000
```

### Frontend Setup

1. **Install Dependencies**
```bash
cd frontend
npm install
```

2. **Development Server**
```bash
npm run dev
# Frontend runs on http://localhost:5173
```

3. **Production Build**
```bash
npm run build
```

## 🔄 系統重啟標準操作程序 (System Restart SOP)

### **服務重啟步驟 - Service Restart Procedure**

當需要重啟ERP系統服務時，請按以下順序執行：

#### **第1步：後端服務啟動 (Backend Service Startup)**
```bash
# 1. 導航到後端目錄
cd backend

# 2. 啟動Flask應用服務器
python app.py

# 3. 驗證服務狀態
# 瀏覽器訪問：http://172.20.10.10:5000/api/v1/health
# 預期回應：{"status": "healthy", "timestamp": "..."}
```
- **服務端口**：5000
- **健康檢查端點**：`/api/v1/health`
- **網絡地址**：172.20.10.10:5000

#### **第2步：前端服務啟動 (Frontend Service Startup)**
```bash
# 1. 導航到前端目錄
cd frontend

# 2. 啟動開發服務器
npm run dev

# 3. 驗證服務狀態
# 瀏覽器訪問：http://172.20.10.10:5174
# 預期：看到ERP登入界面
```
- **服務端口**：5174
- **訪問地址**：http://172.20.10.10:5174
- **登入頁面**：系統主要入口

#### **第3步：系統功能驗證 (System Function Verification)**

1. **登入驗證**
   - 使用測試帳號：`admin` / `admin123`
   - 確認JWT令牌正常發放

2. **採購界面測試**
   - 導航至請購管理模組
   - 開啟REQ20250908004請購單
   - **驗證重點**：供應商和單價欄位完全可見

3. **UI優化確認**
   - 對話框寬度應為95vw（最大1400px）
   - 供應商、單價、小計欄位正確顯示
   - 審核功能正常運作

#### **重要注意事項 (Critical Notes)**

1. **啟動順序**：必須先啟動後端，再啟動前端
2. **CORS配置**：確保包含172.20.10.10地址
3. **網絡配置**：系統配置為局域網IP 172.20.10.10
4. **背景執行**：建議使用背景執行讓服務持續運行

#### **已完成的系統優化**

- ✅ 採購Dialog寬度優化（95vw，最大1400px）
- ✅ 供應商欄位顯示問題修復
- ✅ 單價和小計欄位可見性改善
- ✅ 文件修改：List.vue, Detail.vue, Review.vue

#### **故障排除檢查清單**

1. **後端服務無法啟動**
   - 檢查Python虛擬環境
   - 確認PostgreSQL數據庫運行
   - 檢查端口5000是否被占用

2. **前端服務無法啟動**
   - 檢查Node.js版本（需16+）
   - 確認npm依賴已安裝
   - 檢查端口5174是否可用

3. **API連接失敗**
   - 驗證CORS設置包含正確IP
   - 確認防火牆設置允許通信
   - 檢查網絡連接性

### **快速重啟命令 (Quick Restart Commands)**

```bash
# 後端背景啟動
cd backend && python app.py &

# 前端背景啟動  
cd frontend && npm run dev &
```

此標準操作程序確保系統重啟的一致性和可靠性，為維運人員提供清晰的操作指引。

## 👥 Demo Accounts

| Role | Username | Password | Permissions |
|------|----------|----------|-------------|
| **管理員** | `admin` | `admin123` | Full system access |
| **採購專員** | `procurement` | `proc123` | Procurement operations |
| **工程師** | `engineer` | `eng123` | Requisition management |

## 📋 Core Features

### 1. **請購管理 (Requisition Management)**
- ✅ Create and edit purchase requisitions
- ✅ Submit for approval workflow
- ✅ Line-by-line approval/rejection
- ✅ Status tracking and history

### 2. **採購管理 (Procurement Management)**
- ✅ Generate purchase orders from approved requisitions
- ✅ Supplier management and selection
- ✅ Purchase order confirmation and tracking
- ✅ Shipping milestone updates

### 3. **庫存管理 (Inventory Management)**
- ✅ Receiving management with validation
- ✅ Storage location assignment (Zone/Shelf/Floor)
- ✅ Inventory query and search
- ✅ Item issuance and tracking

### 4. **會計管理 (Accounting Management)**
- ✅ Billing batch generation
- ✅ Payment processing and tracking
- ✅ Supplier payment terms management
- ✅ Financial reporting

### 5. **系統管理 (System Management)**
- ✅ User management with role-based access
- ✅ Supplier master data management
- ✅ System settings configuration
- ✅ Audit trail tracking

## 🔐 Security Features

### **Authentication & Authorization**
- JWT token-based authentication
- Automatic token refresh mechanism
- Role-based access control (RBAC)
- Route-level permission guards

### **API Security**
- Input validation and sanitization
- SQL injection prevention
- CORS configuration
- Request rate limiting ready

## 🎨 UI/UX Features

### **Professional Interface**
- Modern, responsive design
- Dark mode support
- Mobile-friendly layouts
- Accessibility compliant

### **User Experience**
- Real-time data updates
- Comprehensive error handling
- Loading states and feedback
- Intuitive navigation

## 📊 Business Process Flow

```mermaid
graph LR
    A[Requisition] --> B[Approval]
    B --> C[Purchase Order]
    C --> D[Shipping]
    D --> E[Receiving]
    E --> F[Storage]
    F --> G[Acceptance]
    G --> H[Inventory]
    H --> I[Accounting]
```

### **Complete Workflow Support**
1. **Requisition Creation** - Engineers create purchase requests
2. **Approval Process** - Procurement team reviews and approves
3. **Purchase Orders** - Generate POs from approved items
4. **Shipping Tracking** - Monitor delivery status
5. **Receiving Management** - Confirm item receipt
6. **Storage Assignment** - Assign warehouse locations
7. **Acceptance Validation** - Final quality approval
8. **Inventory Management** - Track and issue items
9. **Financial Processing** - Generate bills and process payments

## 🛠️ Development

### **Backend Structure**
```
backend/
├── app/
│   ├── models/          # Database models
│   ├── routes/          # API endpoints
│   ├── services/        # Business logic
│   └── auth.py          # Authentication utilities
├── config.py            # Application configuration
└── app.py              # Application entry point
```

### **Frontend Structure**
```
frontend/
├── src/
│   ├── api/            # API service layer
│   ├── components/     # Reusable components
│   ├── stores/         # Pinia state management
│   ├── types/          # TypeScript definitions
│   ├── views/          # Page components
│   └── router/         # Route configuration
└── public/             # Static assets
```

## 📈 Performance & Scalability

### **Backend Optimizations**
- Database connection pooling
- Query optimization with proper indexing
- Pagination for large datasets
- Caching strategies ready

### **Frontend Optimizations**
- Component lazy loading
- Bundle optimization with Vite
- Image lazy loading
- Progressive Web App ready

## 🧪 Testing

### **Automated Testing**
- Comprehensive test coverage
- API endpoint validation
- Frontend unit tests
- Integration testing suite

### **Quality Assurance**
- Code quality standards
- Security vulnerability scanning
- Performance monitoring
- Accessibility compliance

## 📦 Production Deployment

### **Backend Deployment**
```bash
# Using Gunicorn
gunicorn --bind 0.0.0.0:5000 app:app
```

### **Frontend Deployment**
```bash
# Build for production
npm run build

# Serve static files with nginx or similar
```

### **Environment Variables**
- `FLASK_ENV=production`
- `SECRET_KEY=your-production-secret`
- `DATABASE_URL=postgresql://user:pass@host/db`
- `JWT_SECRET_KEY=your-jwt-secret`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation in the `/docs` folder
- Review the API specifications in `/artifacts`

## 🎯 Roadmap

### **Upcoming Features**
- [ ] Advanced reporting and analytics
- [ ] Mobile application
- [ ] Integration with external systems
- [ ] Workflow automation
- [ ] Real-time notifications
- [ ] Multi-language support

---

Built with ❤️ using modern web technologies for enterprise resource planning. 
