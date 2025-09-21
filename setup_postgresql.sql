-- PostgreSQL 設定腳本
-- 在 pgAdmin 4 中執行此腳本來設定資料庫

-- 1. 建立使用者（如果不存在）
DO
$$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_user
      WHERE usename = 'erp_user') THEN
      CREATE USER erp_user WITH PASSWORD 'erp2024secure';
   END IF;
END
$$;

-- 2. 建立資料庫（如果不存在）
SELECT 'CREATE DATABASE erp_database OWNER erp_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'erp_database')\gexec

-- 3. 授予權限
GRANT ALL PRIVILEGES ON DATABASE erp_database TO erp_user;

-- 4. 連接到 erp_database 來建立表格
\c erp_database

-- 5. 授予 schema 權限
GRANT ALL ON SCHEMA public TO erp_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO erp_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO erp_user;

-- 6. 設定預設權限（未來建立的表格）
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL PRIVILEGES ON TABLES TO erp_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL PRIVILEGES ON SEQUENCES TO erp_user;

-- 顯示成功訊息
DO $$
BEGIN
   RAISE NOTICE '✅ 資料庫設定完成！';
   RAISE NOTICE '資料庫: erp_database';
   RAISE NOTICE '使用者: erp_user';
   RAISE NOTICE '密碼: erp2024secure';
END $$;