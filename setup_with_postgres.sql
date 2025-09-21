-- 使用 postgres 使用者密碼 271828 執行此腳本
-- 在 pgAdmin 4 中連接到 postgres 資料庫後執行

-- 步驟 1: 建立使用者
CREATE USER erp_user WITH PASSWORD '271828';

-- 步驟 2: 建立資料庫
CREATE DATABASE erp_database OWNER erp_user;

-- 步驟 3: 授予權限
GRANT ALL PRIVILEGES ON DATABASE erp_database TO erp_user;

-- 顯示成功訊息
-- 資料庫: erp_database
-- 使用者: erp_user
-- 密碼: 271828