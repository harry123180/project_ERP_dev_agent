# PostgreSQL 遷移指南 - 從 SQLite 到 PostgreSQL

## 目錄
1. [環境準備](#環境準備)
2. [安裝 PostgreSQL](#安裝-postgresql)
3. [Python 依賴更新](#python-依賴更新)
4. [配置檔案更新](#配置檔案更新)
5. [資料庫遷移](#資料庫遷移)
6. [測試與驗證](#測試與驗證)

---

## 環境準備

### 系統需求
- PostgreSQL 14+ (建議使用最新穩定版)
- Python 3.8+
- psycopg2-binary (PostgreSQL Python 驅動)

---

## 安裝 PostgreSQL

### Windows 安裝
1. 下載 PostgreSQL 安裝程式：https://www.postgresql.org/download/windows/
2. 執行安裝程式，記住設定的密碼
3. 預設埠號：5432

### Linux (Ubuntu/Debian) 安裝
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### macOS 安裝
```bash
brew install postgresql
brew services start postgresql
```

---

## Python 依賴更新

### 1. 更新 requirements.txt
```txt
# 移除或註解 SQLite 相關依賴
# 新增 PostgreSQL 相關依賴
psycopg2-binary==2.9.9
SQLAlchemy==2.0.23
alembic==1.13.0
```

### 2. 安裝新依賴
```bash
pip install psycopg2-binary
pip install --upgrade SQLAlchemy
```

---

## 配置檔案更新

### 1. 更新 config.py
```python
import os
from datetime import timedelta

class Config:
    """基礎配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # PostgreSQL 配置
    POSTGRES_USER = os.environ.get('POSTGRES_USER', 'erp_user')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'your_secure_password')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.environ.get('POSTGRES_DB', 'erp_database')

    # SQLAlchemy 配置
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'echo': False  # 設為 True 可看到 SQL 語句 (調試用)
    }

class DevelopmentConfig(Config):
    """開發環境配置"""
    DEBUG = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        'echo': True  # 開發環境顯示 SQL
    }

class ProductionConfig(Config):
    """生產環境配置"""
    DEBUG = False
    # 使用環境變數中的資料庫 URL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        # Heroku 使用 postgres://，但 SQLAlchemy 需要 postgresql://
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)

class TestConfig(Config):
    """測試環境配置"""
    TESTING = True
    POSTGRES_DB = 'erp_test_database'
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}@"
        f"{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{POSTGRES_DB}"
    )

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestConfig,
    'default': DevelopmentConfig
}
```

### 2. 建立 .env 檔案
```env
# PostgreSQL Configuration
POSTGRES_USER=erp_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=erp_database

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

---

## 資料庫遷移

### 1. 建立 PostgreSQL 資料庫和使用者
```sql
-- 以 postgres 使用者登入
sudo -u postgres psql

-- 建立資料庫使用者
CREATE USER erp_user WITH PASSWORD 'your_secure_password';

-- 建立資料庫
CREATE DATABASE erp_database OWNER erp_user;

-- 授予權限
GRANT ALL PRIVILEGES ON DATABASE erp_database TO erp_user;

-- 退出
\q
```

### 2. 資料遷移腳本 (migrate_to_postgresql.py)
```python
#!/usr/bin/env python
"""
SQLite 到 PostgreSQL 資料遷移腳本
"""
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import sys

class DatabaseMigrator:
    def __init__(self, sqlite_path, pg_config):
        self.sqlite_path = sqlite_path
        self.pg_config = pg_config
        self.sqlite_conn = None
        self.pg_conn = None

    def connect(self):
        """建立資料庫連接"""
        # SQLite 連接
        self.sqlite_conn = sqlite3.connect(self.sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row

        # PostgreSQL 連接
        self.pg_conn = psycopg2.connect(
            host=self.pg_config['host'],
            port=self.pg_config['port'],
            database=self.pg_config['database'],
            user=self.pg_config['user'],
            password=self.pg_config['password']
        )

    def get_sqlite_tables(self):
        """獲取 SQLite 中的所有表"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        return [row[0] for row in cursor.fetchall()]

    def migrate_table(self, table_name):
        """遷移單個表的資料"""
        print(f"正在遷移表: {table_name}")

        # 讀取 SQLite 資料
        sqlite_cursor = self.sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()

        if not rows:
            print(f"  表 {table_name} 沒有資料")
            return

        # 獲取欄位名稱
        columns = [description[0] for description in sqlite_cursor.description]

        # 準備 PostgreSQL 插入語句
        pg_cursor = self.pg_conn.cursor()

        # 建立插入語句
        placeholders = ','.join(['%s'] * len(columns))
        columns_str = ','.join([f'"{col}"' for col in columns])
        insert_sql = f"""
            INSERT INTO {table_name} ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """

        # 批量插入資料
        batch_size = 1000
        total_rows = len(rows)

        for i in range(0, total_rows, batch_size):
            batch = rows[i:i+batch_size]
            batch_data = []

            for row in batch:
                # 轉換資料類型
                row_data = []
                for j, value in enumerate(row):
                    # 處理特殊類型
                    if value is None:
                        row_data.append(None)
                    elif isinstance(value, bytes):
                        # 二進制資料轉換
                        row_data.append(value)
                    elif columns[j].endswith('_date') or columns[j].endswith('_at'):
                        # 日期時間處理
                        if isinstance(value, str):
                            try:
                                # 嘗試解析日期
                                if 'T' in value or ' ' in value:
                                    row_data.append(datetime.fromisoformat(value.replace('T', ' ')))
                                else:
                                    row_data.append(datetime.strptime(value, '%Y-%m-%d').date())
                            except:
                                row_data.append(value)
                        else:
                            row_data.append(value)
                    else:
                        row_data.append(value)

                batch_data.append(tuple(row_data))

            # 執行批量插入
            try:
                pg_cursor.executemany(insert_sql, batch_data)
                self.pg_conn.commit()
                print(f"  已遷移 {min(i+batch_size, total_rows)}/{total_rows} 筆資料")
            except Exception as e:
                print(f"  錯誤: {e}")
                self.pg_conn.rollback()
                # 嘗試單筆插入以找出問題資料
                for data in batch_data:
                    try:
                        pg_cursor.execute(insert_sql, data)
                        self.pg_conn.commit()
                    except Exception as e2:
                        print(f"    單筆插入失敗: {e2}")
                        self.pg_conn.rollback()

        print(f"  表 {table_name} 遷移完成")

    def migrate_all(self):
        """執行完整遷移"""
        try:
            self.connect()
            tables = self.get_sqlite_tables()

            print(f"發現 {len(tables)} 個表需要遷移")
            print("="*50)

            # 遷移順序（考慮外鍵依賴）
            ordered_tables = [
                'users',
                'suppliers',
                'projects',
                'item_categories',
                'request_orders',
                'request_order_items',
                'purchase_orders',
                'purchase_order_items',
                'inventory_items',
                'inventory_batches',
                # ... 其他表按依賴順序排列
            ]

            # 先遷移有序表
            for table in ordered_tables:
                if table in tables:
                    self.migrate_table(table)
                    tables.remove(table)

            # 遷移剩餘的表
            for table in tables:
                self.migrate_table(table)

            print("="*50)
            print("遷移完成！")

        except Exception as e:
            print(f"遷移失敗: {e}")
            if self.pg_conn:
                self.pg_conn.rollback()
        finally:
            if self.sqlite_conn:
                self.sqlite_conn.close()
            if self.pg_conn:
                self.pg_conn.close()

if __name__ == "__main__":
    # 配置
    SQLITE_DB_PATH = "erp_development.db"

    PG_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'erp_database',
        'user': 'erp_user',
        'password': 'your_secure_password'
    }

    # 執行遷移
    migrator = DatabaseMigrator(SQLITE_DB_PATH, PG_CONFIG)
    migrator.migrate_all()
```

### 3. 使用 Flask-Migrate 管理資料庫版本
```bash
# 初始化遷移
flask db init

# 建立遷移腳本
flask db migrate -m "Initial PostgreSQL migration"

# 執行遷移
flask db upgrade
```

---

## 測試與驗證

### 1. 建立測試腳本 (test_postgresql.py)
```python
#!/usr/bin/env python
"""PostgreSQL 連接測試腳本"""

import psycopg2
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

def test_direct_connection():
    """測試直接 PostgreSQL 連接"""
    print("測試直接 PostgreSQL 連接...")
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', 5432),
            database=os.getenv('POSTGRES_DB', 'erp_database'),
            user=os.getenv('POSTGRES_USER', 'erp_user'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✓ PostgreSQL 版本: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 連接失敗: {e}")
        return False

def test_sqlalchemy_connection():
    """測試 SQLAlchemy 連接"""
    print("\n測試 SQLAlchemy 連接...")
    try:
        db_url = (
            f"postgresql://{os.getenv('POSTGRES_USER')}:"
            f"{os.getenv('POSTGRES_PASSWORD')}@"
            f"{os.getenv('POSTGRES_HOST')}:"
            f"{os.getenv('POSTGRES_PORT')}/"
            f"{os.getenv('POSTGRES_DB')}"
        )
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"✓ SQLAlchemy 連接成功")
        return True
    except Exception as e:
        print(f"✗ SQLAlchemy 連接失敗: {e}")
        return False

def test_tables():
    """測試資料表"""
    print("\n檢查資料表...")
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', 5432),
            database=os.getenv('POSTGRES_DB', 'erp_database'),
            user=os.getenv('POSTGRES_USER', 'erp_user'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print(f"✓ 找到 {len(tables)} 個資料表:")
        for table in tables:
            print(f"  - {table[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 查詢資料表失敗: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("PostgreSQL 連接測試")
    print("=" * 50)

    all_passed = True
    all_passed = test_direct_connection() and all_passed
    all_passed = test_sqlalchemy_connection() and all_passed
    all_passed = test_tables() and all_passed

    print("\n" + "=" * 50)
    if all_passed:
        print("✓ 所有測試通過！")
    else:
        print("✗ 部分測試失敗，請檢查配置")
```

---

## Docker Compose 配置（可選）

### docker-compose.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: erp_postgres
    environment:
      POSTGRES_USER: erp_user
      POSTGRES_PASSWORD: your_secure_password
      POSTGRES_DB: erp_database
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - erp_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U erp_user -d erp_database"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    container_name: erp_backend
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_USER: erp_user
      POSTGRES_PASSWORD: your_secure_password
      POSTGRES_DB: erp_database
      FLASK_ENV: development
    ports:
      - "5000:5000"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - erp_network
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    container_name: erp_frontend
    ports:
      - "5173:5173"
    networks:
      - erp_network
    volumes:
      - ./frontend:/app
      - /app/node_modules

volumes:
  postgres_data:

networks:
  erp_network:
    driver: bridge
```

---

## 注意事項

### 1. 資料類型差異
- SQLite 的 `INTEGER` → PostgreSQL 的 `INTEGER` 或 `BIGINT`
- SQLite 的 `TEXT` → PostgreSQL 的 `TEXT` 或 `VARCHAR`
- SQLite 的 `REAL` → PostgreSQL 的 `DOUBLE PRECISION`
- SQLite 的 `BLOB` → PostgreSQL 的 `BYTEA`

### 2. 日期時間處理
- PostgreSQL 有嚴格的日期時間格式要求
- 需要確保所有日期時間欄位都是正確的格式

### 3. 自動遞增主鍵
- SQLite: `AUTOINCREMENT`
- PostgreSQL: `SERIAL` 或 `IDENTITY`

### 4. 效能優化
- 建立適當的索引
- 設定連接池參數
- 考慮使用分區表（大資料量時）

### 5. 備份策略
```bash
# 備份 PostgreSQL
pg_dump -U erp_user -h localhost erp_database > backup.sql

# 還原 PostgreSQL
psql -U erp_user -h localhost erp_database < backup.sql
```

---

## 故障排除

### 常見問題

1. **連接被拒絕**
   - 檢查 PostgreSQL 是否運行中
   - 檢查 pg_hba.conf 配置
   - 確認防火牆設定

2. **權限問題**
   - 確保使用者有適當的權限
   - 檢查資料庫擁有者

3. **編碼問題**
   - 設定資料庫編碼為 UTF-8
   - 處理特殊字符

4. **效能問題**
   - 調整 PostgreSQL 配置
   - 優化查詢
   - 添加適當的索引

---

## 完成檢查清單

- [ ] PostgreSQL 已安裝並運行
- [ ] Python 依賴已更新
- [ ] 配置檔案已更新
- [ ] 資料庫和使用者已建立
- [ ] 資料遷移完成
- [ ] 測試通過
- [ ] 應用程式正常運行
- [ ] 備份策略已設定