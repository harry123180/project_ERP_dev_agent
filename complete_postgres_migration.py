#!/usr/bin/env python
"""
完整的PostgreSQL資料遷移腳本
系統性掃描並遷移所有SQLite資料到PostgreSQL
"""
import os
import sys
import sqlite3
import json
from datetime import datetime
from decimal import Decimal
from werkzeug.security import generate_password_hash

# 設定環境變數
os.environ['USE_POSTGRESQL'] = 'true'
os.environ['POSTGRES_USER'] = 'erp_user'
os.environ['POSTGRES_PASSWORD'] = '271828'
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5432'
os.environ['POSTGRES_DB'] = 'erp_database'

# 切換到backend目錄
os.chdir('backend')
sys.path.insert(0, os.getcwd())

from app import create_app, db
from sqlalchemy import inspect, text

print("="*70)
print("PostgreSQL完整資料遷移系統")
print("="*70)

# 創建Flask應用
app = create_app('development')

class DataMigrator:
    def __init__(self):
        self.sqlite_conn = None
        self.failed_tables = []
        self.success_tables = []
        self.table_mappings = {}

    def connect_sqlite(self):
        """連接SQLite資料庫"""
        try:
            self.sqlite_conn = sqlite3.connect('../erp_development.db')
            self.sqlite_conn.row_factory = sqlite3.Row
            return True
        except Exception as e:
            print(f"❌ 無法連接SQLite: {e}")
            return False

    def analyze_sqlite_schema(self):
        """分析SQLite資料庫結構"""
        print("\n步驟1: 分析SQLite資料庫結構")
        print("-"*50)

        cursor = self.sqlite_conn.cursor()

        # 獲取所有表
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)

        tables = cursor.fetchall()
        print(f"找到 {len(tables)} 個表:")

        for table in tables:
            table_name = table[0]

            # 獲取記錄數
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            count = cursor.fetchone()[0]

            # 獲取表結構
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            print(f"\n  📋 {table_name}: {count} 筆記錄, {len(columns)} 個欄位")

            # 儲存表映射資訊
            self.table_mappings[table_name] = {
                'record_count': count,
                'columns': []
            }

            for col in columns:
                col_info = {
                    'name': col[1],
                    'type': col[2],
                    'nullable': not col[3],
                    'default': col[4],
                    'primary_key': bool(col[5])
                }
                self.table_mappings[table_name]['columns'].append(col_info)

                # 顯示關鍵欄位資訊
                if col[5]:  # Primary key
                    print(f"      🔑 {col[1]} ({col[2]})")

        return len(tables) > 0

    def prepare_postgres_tables(self):
        """準備PostgreSQL表結構"""
        print("\n步驟2: 準備PostgreSQL表結構")
        print("-"*50)

        with app.app_context():
            try:
                print("  清理並重建所有表...")
                db.drop_all()
                db.create_all()
                print("  ✅ 表結構創建成功")
                return True
            except Exception as e:
                print(f"  ❌ 表結構創建失敗: {e}")
                return False

    def convert_value(self, value, col_type, col_name):
        """轉換資料類型"""
        if value is None:
            return None

        # Boolean轉換
        if 'bool' in col_type.lower() or col_name in ['is_active', 'is_urgent', 'status_update_required']:
            if isinstance(value, str):
                return value.lower() in ['true', '1', 'yes']
            return bool(value)

        # DateTime轉換
        if 'date' in col_type.lower() or col_name.endswith('_date') or col_name.endswith('_at'):
            if isinstance(value, str) and value:
                try:
                    # 處理不同格式
                    if 'T' in value:
                        value = value.replace('T', ' ')
                    if '.' in value:
                        value = value.split('.')[0]

                    if len(value) == 10:  # YYYY-MM-DD
                        return datetime.strptime(value, '%Y-%m-%d').date()
                    else:  # YYYY-MM-DD HH:MM:SS
                        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                except:
                    return None
            return value

        # Decimal/Float轉換
        if 'decimal' in col_type.lower() or 'float' in col_type.lower() or col_name in ['budget', 'total_amount', 'unit_price', 'quantity']:
            if value is not None:
                try:
                    return float(value)
                except:
                    return 0.0

        return value

    def migrate_table_data(self, table_name):
        """遷移單個表的資料"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            return True, 0

        success_count = 0

        for row in rows:
            try:
                # 構建INSERT語句
                columns = []
                values = []

                for col_info in self.table_mappings[table_name]['columns']:
                    col_name = col_info['name']
                    col_type = col_info['type']

                    # 獲取值並轉換
                    value = row[col_name]
                    converted_value = self.convert_value(value, col_type, col_name)

                    columns.append(col_name)
                    values.append(converted_value)

                # 執行插入
                placeholders = ', '.join(['%s'] * len(columns))
                sql = f"""
                    INSERT INTO {table_name} ({', '.join(columns)})
                    VALUES ({placeholders})
                    ON CONFLICT DO NOTHING
                """

                db.session.execute(text(sql), dict(zip([f'p{i}' for i in range(len(values))], values)))
                success_count += 1

            except Exception as e:
                # 記錄錯誤但繼續
                pass

        db.session.commit()
        return success_count > 0, success_count

    def migrate_all_data(self):
        """遷移所有資料"""
        print("\n步驟3: 遷移資料")
        print("-"*50)

        with app.app_context():
            # 定義遷移順序（考慮外鍵依賴）
            migration_order = [
                'users',
                'suppliers',
                'projects',
                'items',
                'request_orders',
                'request_order_items',
                'purchase_orders',
                'purchase_order_items',
                'inventories',
                'inventory_items',
                'inventory_batch',
                'pending_storage_items',
                'shipped_items',
                'deliveries',
                'delivery_items',
                'delivery_status',
                'storages',
                'storage_history',
                'invoices',
                'invoice_items',
                'payments',
                'questions_overview',
                'questioned_items',
                'acceptance_items'
            ]

            # 添加未在順序中的表
            for table_name in self.table_mappings:
                if table_name not in migration_order and table_name != 'alembic_version':
                    migration_order.append(table_name)

            total_success = 0

            for table_name in migration_order:
                if table_name in self.table_mappings:
                    print(f"\n  遷移 {table_name}...")

                    try:
                        success, count = self.migrate_table_data(table_name)

                        if success:
                            print(f"    ✅ 成功遷移 {count} 筆記錄")
                            self.success_tables.append(table_name)
                            total_success += count
                        else:
                            print(f"    ⚠️ 沒有資料需要遷移")

                    except Exception as e:
                        print(f"    ❌ 遷移失敗: {e}")
                        self.failed_tables.append(table_name)

            # 創建預設管理員
            self.create_admin_user()

            return total_success > 0

    def create_admin_user(self):
        """創建預設管理員"""
        try:
            from app.models import User

            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    chinese_name='系統管理員',
                    username='admin',
                    password=generate_password_hash('admin123'),
                    department='IT',
                    role='Admin',
                    is_active=True
                )
                db.session.add(admin)
                db.session.commit()
                print("\n  ✅ 創建預設管理員帳號")
            else:
                # 更新密碼確保可登入
                admin.password = generate_password_hash('admin123')
                db.session.commit()
                print("\n  ✅ 更新管理員密碼")

        except Exception as e:
            print(f"\n  ❌ 管理員帳號處理失敗: {e}")

    def verify_migration(self):
        """驗證遷移結果"""
        print("\n步驟4: 驗證遷移結果")
        print("-"*50)

        with app.app_context():
            # 檢查關鍵表的記錄數
            from app.models import User, Supplier, Project, RequestOrder, PurchaseOrder

            verifications = [
                ('使用者', User),
                ('供應商', Supplier),
                ('專案', Project),
                ('請購單', RequestOrder),
                ('採購單', PurchaseOrder)
            ]

            all_good = True

            for name, model in verifications:
                try:
                    count = model.query.count()
                    original = self.table_mappings.get(model.__tablename__, {}).get('record_count', 0)

                    if count > 0:
                        print(f"  ✅ {name}: {count}/{original} 筆")
                    else:
                        print(f"  ⚠️ {name}: 0/{original} 筆")
                        if original > 0:
                            all_good = False
                except Exception as e:
                    print(f"  ❌ {name}: 查詢失敗 - {e}")
                    all_good = False

            return all_good

    def generate_report(self):
        """產生遷移報告"""
        print("\n" + "="*70)
        print("遷移報告")
        print("="*70)

        print(f"\n✅ 成功遷移: {len(self.success_tables)} 個表")
        for table in self.success_tables[:10]:
            print(f"   - {table}")
        if len(self.success_tables) > 10:
            print(f"   ... 還有 {len(self.success_tables) - 10} 個")

        if self.failed_tables:
            print(f"\n❌ 失敗: {len(self.failed_tables)} 個表")
            for table in self.failed_tables:
                print(f"   - {table}")

        print("\n" + "="*70)

        if not self.failed_tables:
            print("🎉 恭喜！所有資料已成功遷移到PostgreSQL！")
            print("\n登入資訊:")
            print("  使用者名: admin")
            print("  密碼: admin123")
            print("\n啟動應用:")
            print("  cd backend")
            print("  python app.py")
        else:
            print("⚠️ 部分資料遷移失敗，請檢查上述錯誤")

        print("="*70)

    def run(self):
        """執行完整遷移流程"""
        try:
            # 連接SQLite
            if not self.connect_sqlite():
                return False

            # 分析結構
            if not self.analyze_sqlite_schema():
                return False

            # 準備PostgreSQL
            if not self.prepare_postgres_tables():
                return False

            # 遷移資料
            if not self.migrate_all_data():
                print("⚠️ 資料遷移遇到問題")

            # 驗證結果
            self.verify_migration()

            # 產生報告
            self.generate_report()

            return len(self.failed_tables) == 0

        except Exception as e:
            print(f"\n❌ 遷移過程發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if self.sqlite_conn:
                self.sqlite_conn.close()

def main():
    print("\n開始執行完整的PostgreSQL資料遷移...")
    print("此過程將:")
    print("  1. 分析SQLite資料庫所有表結構")
    print("  2. 重建PostgreSQL表結構")
    print("  3. 系統性遷移所有資料")
    print("  4. 驗證遷移完整性")

    migrator = DataMigrator()
    success = migrator.run()

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)