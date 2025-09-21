# ERP System Docker Deployment Guide
## BMad Method™ Docker化部署文檔

### 📋 Executive Summary
本文檔提供完整的Docker化部署指南，將ERP系統的前端和後端容器化，而PostgreSQL數據庫保留在本地主機。

---

## 🎯 系統架構概述

### 目標架構
```
┌─────────────────────────────────────────────────────┐
│                   Docker Host                        │
│                                                      │
│  ┌─────────────────┐     ┌─────────────────┐       │
│  │  Frontend       │     │  Backend        │       │
│  │  Container      │────>│  Container      │       │
│  │  (Vue.js)       │     │  (Flask API)    │       │
│  │  Port: 80       │     │  Port: 5000     │       │
│  └─────────────────┘     └─────────────────┘       │
│                                │                    │
│                                │                    │
│                                ▼                    │
│                    ┌─────────────────────┐          │
│                    │  PostgreSQL         │          │
│                    │  (Host Machine)     │          │
│                    │  localhost:5432     │          │
│                    └─────────────────────┘          │
└─────────────────────────────────────────────────────┘
```

### 網絡配置
- **Frontend**: 80 (對外) → 80 (容器內)
- **Backend API**: 5000 (對外) → 5000 (容器內)
- **PostgreSQL**: localhost:5432 (本地主機)

---

## 📦 Prerequisites 前置需求

### 必需軟體
1. **Docker Engine** >= 20.10
2. **Docker Compose** >= 2.0
3. **PostgreSQL** 14+ (本地安裝)
4. **Git** (用於克隆repository)

### PostgreSQL本地配置
```bash
# PostgreSQL連接參數
Host: localhost (或 host.docker.internal 從容器訪問)
Port: 5432
Database: erp_database
Username: erp_user
Password: 271828
```

---

## 🔧 Docker配置文件

### 1. Backend Dockerfile (`backend/Dockerfile`)
```dockerfile
# Backend Dockerfile
FROM python:3.9-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 複製requirements文件
COPY requirements.txt .

# 安裝Python依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用代碼
COPY . .

# 設置環境變量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV USE_POSTGRESQL=true
ENV POSTGRES_HOST=host.docker.internal
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=erp_database
ENV POSTGRES_USER=erp_user
ENV POSTGRES_PASSWORD=271828

# 暴露端口
EXPOSE 5000

# 啟動命令
CMD ["python", "app.py"]
```

### 2. Frontend Dockerfile (`frontend/Dockerfile`)
```dockerfile
# Frontend Dockerfile
# Build stage
FROM node:18-alpine as build-stage

WORKDIR /app

# 複製package文件
COPY package*.json ./

# 安裝依賴
RUN npm ci

# 複製源代碼
COPY . .

# 設置API URL環境變量
ARG VITE_API_URL=http://localhost:5000/api/v1
ENV VITE_API_URL=$VITE_API_URL

# 構建應用
RUN npm run build

# Production stage
FROM nginx:alpine

# 複製構建輸出到nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 複製nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 3. Nginx配置 (`frontend/nginx.conf`)
```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        # Vue.js路由支持
        location / {
            try_files $uri $uri/ /index.html;
        }

        # API代理
        location /api/ {
            proxy_pass http://host.docker.internal:5000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### 4. Docker Compose (`docker-compose.yml`)
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: erp-backend
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - USE_POSTGRESQL=true
      - POSTGRES_HOST=host.docker.internal
      - POSTGRES_PORT=5432
      - POSTGRES_DB=erp_database
      - POSTGRES_USER=erp_user
      - POSTGRES_PASSWORD=271828
      - JWT_SECRET_KEY=your-secret-key-here
      - SECRET_KEY=your-flask-secret-key
    networks:
      - erp-network
    extra_hosts:
      - "host.docker.internal:host-gateway"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_URL: http://localhost:5000/api/v1
    container_name: erp-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - erp-network
    extra_hosts:
      - "host.docker.internal:host-gateway"

networks:
  erp-network:
    driver: bridge
```

---

## 🚀 部署步驟

### Step 1: 準備環境
```bash
# 1. 克隆repository
git clone <your-repository-url>
cd project_ERP_dev_agent

# 2. 創建環境文件
cat > .env << EOF
POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=5432
POSTGRES_DB=erp_database
POSTGRES_USER=erp_user
POSTGRES_PASSWORD=271828
JWT_SECRET_KEY=$(openssl rand -hex 32)
SECRET_KEY=$(openssl rand -hex 32)
EOF
```

### Step 2: 配置PostgreSQL (本地主機)
```bash
# 1. 編輯PostgreSQL配置允許Docker容器連接
# 編輯 postgresql.conf
listen_addresses = '*'

# 編輯 pg_hba.conf，添加:
host    all             all             172.0.0.0/8            md5
host    all             all             192.168.0.0/16         md5

# 2. 重啟PostgreSQL
sudo systemctl restart postgresql

# 3. 創建數據庫和用戶
psql -U postgres
CREATE DATABASE erp_database;
CREATE USER erp_user WITH PASSWORD '271828';
GRANT ALL PRIVILEGES ON DATABASE erp_database TO erp_user;
\q
```

### Step 3: 構建Docker鏡像
```bash
# 構建所有服務
docker-compose build

# 或分別構建
docker-compose build backend
docker-compose build frontend
```

### Step 4: 啟動服務
```bash
# 啟動所有服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 檢查服務狀態
docker-compose ps
```

### Step 5: 初始化數據庫
```bash
# 執行數據庫遷移
docker exec -it erp-backend python migrate_database.py

# 創建初始管理員用戶
docker exec -it erp-backend python create_admin.py
```

---

## 🔄 遷移到新服務器

### 在源服務器上
```bash
# 1. 備份數據庫
pg_dump -U erp_user -h localhost erp_database > erp_backup.sql

# 2. 打包Docker鏡像
docker save erp-backend:latest > erp-backend.tar
docker save erp-frontend:latest > erp-frontend.tar

# 3. 打包項目文件
tar -czf erp-project.tar.gz \
  docker-compose.yml \
  .env \
  backend/ \
  frontend/
```

### 在目標服務器上
```bash
# 1. 傳輸文件到新服務器
scp erp-*.tar* user@new-server:/path/to/deployment/
scp erp_backup.sql user@new-server:/path/to/deployment/

# 2. 在新服務器上解壓
tar -xzf erp-project.tar.gz

# 3. 加載Docker鏡像
docker load < erp-backend.tar
docker load < erp-frontend.tar

# 4. 恢復數據庫
psql -U erp_user -h localhost erp_database < erp_backup.sql

# 5. 更新配置（如需要）
# 編輯 .env 文件，更新IP地址和端口

# 6. 啟動服務
docker-compose up -d
```

---

## 🌐 網絡和IP配置

### 不同部署場景的IP配置

#### 場景1: 同一局域網內訪問
```yaml
# docker-compose.yml
services:
  frontend:
    build:
      args:
        VITE_API_URL: http://192.168.1.100:5000/api/v1
```

#### 場景2: 公網訪問
```yaml
# docker-compose.yml
services:
  frontend:
    build:
      args:
        VITE_API_URL: https://your-domain.com/api/v1
```

#### 場景3: 使用反向代理
```nginx
# nginx反向代理配置
upstream backend {
    server localhost:5000;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://backend;
    }

    location / {
        proxy_pass http://localhost:80;
    }
}
```

---

## 🔍 健康檢查和監控

### 健康檢查端點
```python
# backend/app.py 添加健康檢查
@app.route('/health')
def health_check():
    try:
        # 檢查數據庫連接
        db.session.execute('SELECT 1')
        return jsonify({'status': 'healthy'}), 200
    except:
        return jsonify({'status': 'unhealthy'}), 500
```

### 監控命令
```bash
# 查看容器狀態
docker-compose ps

# 查看容器日誌
docker-compose logs backend
docker-compose logs frontend

# 實時日誌
docker-compose logs -f --tail=100

# 資源使用情況
docker stats
```

---

## 🛠 故障排除

### 常見問題

#### 1. 無法連接到PostgreSQL
```bash
# 檢查PostgreSQL是否允許外部連接
netstat -an | grep 5432

# 檢查防火牆
sudo ufw status
sudo ufw allow 5432/tcp

# 測試連接
docker exec -it erp-backend psql -h host.docker.internal -U erp_user -d erp_database
```

#### 2. Frontend無法訪問Backend API
```bash
# 檢查backend服務
curl http://localhost:5000/health

# 檢查網絡
docker network ls
docker network inspect project_erp_dev_agent_erp-network
```

#### 3. 容器啟動失敗
```bash
# 查看詳細錯誤
docker-compose logs backend
docker-compose logs frontend

# 重新構建
docker-compose down
docker-compose build --no-cache
docker-compose up
```

---

## 📝 維護操作

### 更新代碼
```bash
# 1. 停止服務
docker-compose down

# 2. 更新代碼
git pull origin main

# 3. 重新構建
docker-compose build

# 4. 啟動服務
docker-compose up -d
```

### 備份和恢復
```bash
# 備份
docker exec erp-backend python backup_database.py
docker cp erp-backend:/app/backup.sql ./

# 恢復
docker cp ./backup.sql erp-backend:/app/
docker exec erp-backend python restore_database.py
```

### 日誌管理
```bash
# 清理日誌
docker-compose logs --no-color > logs_$(date +%Y%m%d).txt
docker-compose down
docker-compose up -d
```

---

## 🔐 安全建議

1. **環境變量管理**
   - 使用`.env`文件管理敏感信息
   - 不要將`.env`提交到Git

2. **網絡隔離**
   - 使用Docker網絡隔離服務
   - 限制不必要的端口暴露

3. **定期更新**
   - 定期更新Docker鏡像
   - 保持依賴包最新

4. **訪問控制**
   - 配置防火牆規則
   - 使用HTTPS加密傳輸

---

## 📞 支持信息

### 技術支持
- 項目維護者: BMad Development Team
- 文檔版本: 1.0.0
- 最後更新: 2024-01-09

### 相關文檔
- [系統架構文檔](./ERP_SYSTEM_ARCHITECTURE.md)
- [API文檔](./docs/API_DOCUMENTATION.md)
- [用戶手冊](./USER_TRAINING_GUIDE.md)

---

## ✅ 部署檢查清單

- [ ] PostgreSQL已安裝並配置
- [ ] Docker和Docker Compose已安裝
- [ ] 環境變量已配置
- [ ] 防火牆規則已設置
- [ ] 數據庫已初始化
- [ ] 健康檢查通過
- [ ] 前端可以訪問
- [ ] API響應正常
- [ ] 數據持久化測試
- [ ] 備份策略已實施

---

**END OF DOCUMENT**