#!/usr/bin/env python
"""
啟動 ERP 系統 (使用 PostgreSQL)
"""
import os
import sys

# 設定 PostgreSQL 環境變數
os.environ['USE_POSTGRESQL'] = 'true'
os.environ['POSTGRES_USER'] = 'erp_user'
os.environ['POSTGRES_PASSWORD'] = '271828'
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5432'
os.environ['POSTGRES_DB'] = 'erp_database'

print("="*60)
print("啟動 ERP 系統 (PostgreSQL)")
print("="*60)
print(f"資料庫: PostgreSQL")
print(f"主機: {os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}")
print(f"資料庫名: {os.environ['POSTGRES_DB']}")
print(f"使用者: {os.environ['POSTGRES_USER']}")
print("="*60)

# 切換到 backend 目錄
os.chdir('backend')

# 啟動應用程式
from app import create_app

app = create_app('development')

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )