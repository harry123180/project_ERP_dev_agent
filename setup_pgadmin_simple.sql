-- 簡化版 PostgreSQL 設定腳本
-- 在 pgAdmin 4 Query Tool 中執行

-- 步驟 1: 建立使用者
CREATE USER erp_user WITH PASSWORD 'erp2024secure';

-- 步驟 2: 建立資料庫
CREATE DATABASE erp_database OWNER erp_user;

-- 步驟 3: 授予所有權限
GRANT ALL PRIVILEGES ON DATABASE erp_database TO erp_user;