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
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseMigrator:
    def __init__(self, sqlite_path, pg_config):
        self.sqlite_path = sqlite_path
        self.pg_config = pg_config
        self.sqlite_conn = None
        self.pg_conn = None

    def connect(self):
        """建立資料庫連接"""
        print("連接到 SQLite 資料庫...")
        # SQLite 連接
        self.sqlite_conn = sqlite3.connect(self.sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row

        print("連接到 PostgreSQL 資料庫...")
        # PostgreSQL 連接
        self.pg_conn = psycopg2.connect(
            host=self.pg_config['host'],
            port=self.pg_config['port'],
            database=self.pg_config['database'],
            user=self.pg_config['user'],
            password=self.pg_config['password']
        )
        print("資料庫連接成功！")

    def get_sqlite_tables(self):
        """獲取 SQLite 中的所有表"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
            AND name NOT LIKE 'alembic%'
            ORDER BY name
        """)
        return [row[0] for row in cursor.fetchall()]

    def create_table_if_not_exists(self, table_name):
        """在 PostgreSQL 中建立表結構（如果不存在）"""
        sqlite_cursor = self.sqlite_conn.cursor()

        # 獲取 SQLite 表結構
        sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = sqlite_cursor.fetchall()

        if not columns_info:
            return

        # 建立 PostgreSQL CREATE TABLE 語句
        pg_cursor = self.pg_conn.cursor()

        # 檢查表是否已存在
        pg_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %s
            )
        """, (table_name,))

        if pg_cursor.fetchone()[0]:
            print(f"  表 {table_name} 已存在")
            return

        # 構建 CREATE TABLE 語句
        columns_def = []
        for col in columns_info:
            col_name = col[1]
            col_type = col[2].upper()
            not_null = col[3] == 1
            default_val = col[4]
            is_pk = col[5] == 1

            # SQLite 到 PostgreSQL 類型映射
            pg_type = self.map_sqlite_to_pg_type(col_type)

            col_def = f'"{col_name}" {pg_type}'

            if is_pk:
                col_def += " PRIMARY KEY"
            elif not_null:
                col_def += " NOT NULL"

            if default_val is not None:
                col_def += f" DEFAULT {default_val}"

            columns_def.append(col_def)

        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join(columns_def)}
            )
        """

        try:
            pg_cursor.execute(create_sql)
            self.pg_conn.commit()
            print(f"  建立表 {table_name}")
        except Exception as e:
            print(f"  建立表 {table_name} 失敗: {e}")
            self.pg_conn.rollback()

    def map_sqlite_to_pg_type(self, sqlite_type):
        """SQLite 類型映射到 PostgreSQL 類型"""
        type_mapping = {
            'INTEGER': 'INTEGER',
            'TEXT': 'TEXT',
            'REAL': 'DOUBLE PRECISION',
            'BLOB': 'BYTEA',
            'VARCHAR': 'VARCHAR(255)',
            'DATE': 'DATE',
            'DATETIME': 'TIMESTAMP',
            'BOOLEAN': 'BOOLEAN',
            'DECIMAL': 'DECIMAL',
            'FLOAT': 'FLOAT'
        }

        # 處理帶參數的類型，如 VARCHAR(50)
        base_type = sqlite_type.split('(')[0]
        if base_type in type_mapping:
            if '(' in sqlite_type:
                # 保留參數
                return sqlite_type.replace(base_type, type_mapping[base_type].split('(')[0])
            return type_mapping[base_type]
        return sqlite_type

    def migrate_table(self, table_name):
        """遷移單個表的資料"""
        print(f"正在遷移表: {table_name}")

        # 建立表結構（如果需要）
        self.create_table_if_not_exists(table_name)

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

        # 清空目標表（可選）
        try:
            pg_cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE")
            self.pg_conn.commit()
        except:
            self.pg_conn.rollback()

        # 建立插入語句
        placeholders = ','.join(['%s'] * len(columns))
        columns_str = ','.join([f'"{col}"' for col in columns])
        insert_sql = f"""
            INSERT INTO {table_name} ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """

        # 批量插入資料
        batch_size = 100
        total_rows = len(rows)
        success_count = 0

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
                        if value and isinstance(value, str):
                            try:
                                # 處理各種日期格式
                                if 'T' in value:
                                    value = value.replace('T', ' ')
                                if '.' in value:
                                    # 移除毫秒
                                    value = value.split('.')[0]

                                if len(value) == 10:  # YYYY-MM-DD
                                    row_data.append(datetime.strptime(value, '%Y-%m-%d').date())
                                else:  # YYYY-MM-DD HH:MM:SS
                                    row_data.append(datetime.strptime(value, '%Y-%m-%d %H:%M:%S'))
                            except:
                                row_data.append(None)
                        else:
                            row_data.append(value)
                    else:
                        row_data.append(value)

                batch_data.append(tuple(row_data))

            # 執行批量插入
            for data in batch_data:
                try:
                    pg_cursor.execute(insert_sql, data)
                    success_count += 1
                except Exception as e:
                    print(f"    插入失敗: {e}")
                    self.pg_conn.rollback()
                    continue

            self.pg_conn.commit()
            print(f"  已遷移 {min(i+batch_size, total_rows)}/{total_rows} 筆資料")

        print(f"  表 {table_name} 遷移完成，成功 {success_count}/{total_rows} 筆")

    def migrate_all(self):
        """執行完整遷移"""
        try:
            self.connect()
            tables = self.get_sqlite_tables()

            print(f"\n發現 {len(tables)} 個表需要遷移")
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
                'storages',
                'storage_items',
                'consolidations',
                'consolidation_items',
                'project_expenditures',
                'system_settings',
                'pending_storage_items',
                'storage_history',
                'acceptance_items'
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

            # 顯示統計
            self.show_statistics()

        except Exception as e:
            print(f"遷移失敗: {e}")
            if self.pg_conn:
                self.pg_conn.rollback()
        finally:
            if self.sqlite_conn:
                self.sqlite_conn.close()
            if self.pg_conn:
                self.pg_conn.close()

    def show_statistics(self):
        """顯示遷移統計"""
        print("\n遷移統計:")
        print("-"*30)

        pg_cursor = self.pg_conn.cursor()
        pg_cursor.execute("""
            SELECT table_name,
                   (SELECT COUNT(*)
                    FROM information_schema.columns
                    WHERE table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        tables = pg_cursor.fetchall()
        for table, col_count in tables:
            # 獲取記錄數
            try:
                pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = pg_cursor.fetchone()[0]
                print(f"  {table}: {row_count} 筆資料, {col_count} 個欄位")
            except:
                print(f"  {table}: 無法獲取統計")

if __name__ == "__main__":
    # 配置
    SQLITE_DB_PATH = "erp_development.db"

    PG_CONFIG = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', 5432),
        'database': os.getenv('POSTGRES_DB', 'erp_database'),
        'user': os.getenv('POSTGRES_USER', 'erp_user'),
        'password': os.getenv('POSTGRES_PASSWORD', '271828')
    }

    print("PostgreSQL 資料遷移工具")
    print("="*50)
    print(f"來源: SQLite ({SQLITE_DB_PATH})")
    print(f"目標: PostgreSQL ({PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']})")
    print("="*50)

    # 自動執行遷移
    print("開始自動遷移...")

    # 執行遷移
    migrator = DatabaseMigrator(SQLITE_DB_PATH, PG_CONFIG)
    migrator.migrate_all()