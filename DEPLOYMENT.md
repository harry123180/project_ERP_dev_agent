# ERP 系統部署指南

## 在遠端電腦上部署步驟

### 1. 前置需求
- Windows 10/11
- Git
- Python 3.9+
- Node.js 18+
- PostgreSQL 或使用 SQLite（開發模式）

### 2. 獲取程式碼

```bash
# 克隆 repository
git clone https://github.com/harry123180/project_ERP_dev_agent.git
cd project_ERP_dev_agent

# 或者如果已經克隆過，更新到最新版本
git pull origin main
```

### 3. 設定後端

#### 3.1 建立 Python 虛擬環境
```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

#### 3.2 安裝依賴
```bash
pip install -r requirements.txt
```

#### 3.3 設定環境變數
創建 `.env` 檔案：
```bash
copy .env.example .env
```

編輯 `.env` 檔案，設定以下內容：
```env
# 資料庫設定 (SQLite 開發模式)
DATABASE_URL=sqlite:///./erp_development.db

# 或 PostgreSQL 生產模式
# DATABASE_URL=postgresql://username:password@localhost:5432/erp_production

# JWT 密鑰
JWT_SECRET_KEY=your-secret-key-here

# Flask 設定
FLASK_ENV=development
FLASK_APP=app.py
```

#### 3.4 初始化資料庫
```bash
# 執行資料庫遷移
flask db upgrade

# 初始化物品種類
python fix_item_categories.py
```

### 4. 設定前端

#### 4.1 安裝依賴
```bash
cd ../frontend
npm install
```

#### 4.2 設定環境變數
編輯 `.env.development` 檔案（開發模式）：
```env
# 使用相對路徑以支援遠端訪問
VITE_API_BASE_URL=/api/v1
```

### 5. 啟動系統

#### 5.1 啟動後端
```bash
cd backend
venv\Scripts\activate
python app.py
```
後端會在 http://localhost:5000 運行

#### 5.2 啟動前端
新開一個終端視窗：
```bash
cd frontend
npm run dev
```
前端會在 http://localhost:5174 運行（如果被佔用會自動選擇其他端口）

### 6. 防火牆設定（允許遠端訪問）

#### 6.1 開啟 Windows 防火牆端口
以管理員身份執行 PowerShell：
```powershell
# 開啟前端端口
New-NetFirewallRule -DisplayName "ERP Frontend" -Direction Inbound -Protocol TCP -LocalPort 5174 -Action Allow

# 開啟後端端口
New-NetFirewallRule -DisplayName "ERP Backend" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

#### 6.2 修改前端配置以允許遠端訪問
編輯 `frontend/vite.config.ts`，確保有以下設定：
```javascript
export default defineConfig({
  server: {
    host: '0.0.0.0',  // 允許外部訪問
    port: 5174
  }
})
```

### 7. 訪問系統

- **本機訪問**：http://localhost:5174
- **遠端訪問**：http://[遠端電腦IP]:5174

預設管理員帳號：
- 用戶名：admin
- 密碼：admin123

### 8. 自動啟動腳本

創建 `start_erp.bat` 檔案：
```batch
@echo off
echo Starting ERP System...

:: 啟動後端
start "ERP Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && python app.py"

:: 等待後端啟動
timeout /t 5

:: 啟動前端
start "ERP Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo ERP System is starting...
echo Backend: http://localhost:5000
echo Frontend: http://localhost:5174
pause
```

### 9. 停止系統

創建 `stop_erp.bat` 檔案：
```batch
@echo off
echo Stopping ERP System...
taskkill /FI "WindowTitle eq ERP Backend*" /T /F
taskkill /FI "WindowTitle eq ERP Frontend*" /T /F
echo ERP System stopped.
pause
```

## 故障排除

### 問題 1：git pull 衝突
```bash
# 保留本地變更
git stash
git pull
git stash pop

# 或放棄本地變更
git reset --hard HEAD
git pull
```

### 問題 2：端口被佔用
```bash
# 查看端口佔用
netstat -ano | findstr :5174
netstat -ano | findstr :5000

# 結束佔用進程
taskkill /PID [進程ID] /F
```

### 問題 3：資料庫連線錯誤
- 確認 PostgreSQL 服務已啟動（如使用 PostgreSQL）
- 檢查 `.env` 中的資料庫連線字串
- 確認資料庫已創建且權限正確

### 問題 4：無法遠端訪問
- 確認防火牆規則已添加
- 確認前端 host 設定為 '0.0.0.0'
- 確認遠端電腦網路可達

## 更新系統

```bash
# 停止運行中的系統
# 執行 stop_erp.bat 或手動關閉

# 更新程式碼
git pull origin main

# 更新後端依賴（如需要）
cd backend
venv\Scripts\activate
pip install -r requirements.txt
flask db upgrade

# 更新前端依賴（如需要）
cd ../frontend
npm install

# 重新啟動系統
# 執行 start_erp.bat
```

## 生產環境建議

1. 使用 PostgreSQL 而非 SQLite
2. 設定 HTTPS（使用 nginx 反向代理）
3. 使用 PM2 或 Windows Service 管理進程
4. 定期備份資料庫
5. 設定日誌記錄和監控