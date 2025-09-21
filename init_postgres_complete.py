#!/usr/bin/env python
"""
完整的PostgreSQL資料庫初始化腳本
處理表結構創建和資料遷移
"""
import os
import sys
import sqlite3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime

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
from werkzeug.security import generate_password_hash

print("="*60)
print("PostgreSQL完整初始化")
print("="*60)

# 創建Flask應用
app = create_app('development')

def create_all_tables():
    """使用SQLAlchemy創建所有表"""
    with app.app_context():
        try:
            print("\n步驟1: 創建所有表結構...")

            # 刪除所有表（重新開始）
            print("  清理舊表...")
            db.drop_all()

            # 創建所有表
            print("  創建新表...")
            db.create_all()

            print("  ✅ 表結構創建成功")
            return True
        except Exception as e:
            print(f"  ❌ 創建表失敗: {e}")
            return False

def migrate_data_from_sqlite():
    """從SQLite遷移資料到PostgreSQL"""

    # SQLite連接
    sqlite_conn = sqlite3.connect('../erp_development.db')
    sqlite_conn.row_factory = sqlite3.Row

    with app.app_context():
        try:
            print("\n步驟2: 遷移資料...")

            # 1. 遷移使用者
            print("\n  遷移使用者...")
            cursor = sqlite_conn.cursor()
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()

            for user in users:
                # 處理Boolean轉換（SQLite的0/1轉為Python的True/False）
                is_active = bool(user['is_active']) if user['is_active'] is not None else True

                sql = """
                    INSERT INTO users (user_id, chinese_name, username, password,
                                     department, role, is_active, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO NOTHING
                """

                try:
                    db.session.execute(sql, (
                        user['user_id'],
                        user['chinese_name'],
                        user['username'],
                        user['password'],
                        user['department'],
                        user['role'],
                        is_active,
                        user['created_at']
                    ))
                except Exception as e:
                    print(f"    跳過使用者 {user['username']}: {e}")

            db.session.commit()
            print(f"    ✅ 遷移了 {len(users)} 個使用者")

            # 2. 遷移供應商
            print("\n  遷移供應商...")
            cursor.execute("SELECT * FROM suppliers")
            suppliers = cursor.fetchall()

            for supplier in suppliers:
                # 處理Boolean轉換
                is_active = bool(supplier['is_active']) if supplier['is_active'] is not None else True

                sql = """
                    INSERT INTO suppliers (supplier_id, supplier_name, contact_person,
                                         phone, email, address, is_active, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (supplier_id) DO NOTHING
                """

                try:
                    db.session.execute(sql, (
                        supplier['supplier_id'],
                        supplier['supplier_name'],
                        supplier['contact_person'],
                        supplier['phone'],
                        supplier['email'],
                        supplier['address'],
                        is_active,
                        supplier['created_at']
                    ))
                except Exception as e:
                    print(f"    跳過供應商 {supplier['supplier_name']}: {e}")

            db.session.commit()
            print(f"    ✅ 遷移了 {len(suppliers)} 個供應商")

            # 3. 遷移專案
            print("\n  遷移專案...")
            cursor.execute("SELECT * FROM projects")
            projects = cursor.fetchall()

            for project in projects:
                sql = """
                    INSERT INTO projects (project_id, project_name, project_code,
                                        budget, project_manager, start_date,
                                        end_date, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (project_id) DO NOTHING
                """

                try:
                    db.session.execute(sql, (
                        project['project_id'],
                        project['project_name'],
                        project['project_code'],
                        project['budget'],
                        project['project_manager'],
                        project['start_date'],
                        project['end_date'],
                        project['status'],
                        project['created_at']
                    ))
                except Exception as e:
                    print(f"    跳過專案 {project['project_name']}: {e}")

            db.session.commit()
            print(f"    ✅ 遷移了 {len(projects)} 個專案")

            # 4. 遷移請購單
            print("\n  遷移請購單...")
            cursor.execute("SELECT * FROM request_orders")
            request_orders = cursor.fetchall()

            for order in request_orders:
                # 處理Boolean轉換
                is_urgent = bool(order['is_urgent']) if order['is_urgent'] is not None else False

                sql = """
                    INSERT INTO request_orders (request_order_no, request_date,
                                              applicant_id, project_id, status,
                                              created_at, updated_at, is_urgent,
                                              urgent_date, urgent_reason)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (request_order_no) DO NOTHING
                """

                try:
                    db.session.execute(sql, (
                        order['request_order_no'],
                        order['request_date'],
                        order['applicant_id'],
                        order['project_id'],
                        order['status'],
                        order['created_at'],
                        order['updated_at'],
                        is_urgent,
                        order['urgent_date'],
                        order['urgent_reason']
                    ))
                except Exception as e:
                    print(f"    跳過請購單 {order['request_order_no']}: {e}")

            db.session.commit()
            print(f"    ✅ 遷移了 {len(request_orders)} 個請購單")

            # 5. 遷移採購單
            print("\n  遷移採購單...")
            cursor.execute("SELECT * FROM purchase_orders")
            purchase_orders = cursor.fetchall()

            for po in purchase_orders:
                # 處理Boolean轉換
                status_update_required = bool(po['status_update_required']) if po['status_update_required'] is not None else False

                sql = """
                    INSERT INTO purchase_orders (purchase_order_no, supplier_id,
                                               order_date, delivery_date, payment_terms,
                                               total_amount, status, created_at,
                                               creation_date, status_update_required)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (purchase_order_no) DO NOTHING
                """

                try:
                    db.session.execute(sql, (
                        po['purchase_order_no'],
                        po['supplier_id'],
                        po['order_date'],
                        po['delivery_date'],
                        po['payment_terms'],
                        po['total_amount'],
                        po['status'],
                        po['created_at'],
                        po['creation_date'],
                        status_update_required
                    ))
                except Exception as e:
                    print(f"    跳過採購單 {po['purchase_order_no']}: {e}")

            db.session.commit()
            print(f"    ✅ 遷移了 {len(purchase_orders)} 個採購單")

            # 6. 創建預設管理員帳號（如果不存在）
            print("\n  檢查管理員帳號...")
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
                print("    ✅ 創建了預設管理員帳號")
            else:
                print("    ✅ 管理員帳號已存在")

            print("\n  ✅ 資料遷移完成")
            return True

        except Exception as e:
            print(f"\n  ❌ 資料遷移失敗: {e}")
            db.session.rollback()
            return False
        finally:
            sqlite_conn.close()

def verify_migration():
    """驗證遷移結果"""
    with app.app_context():
        try:
            print("\n步驟3: 驗證遷移結果...")

            from app.models import User, Supplier, Project, RequestOrder, PurchaseOrder

            # 統計各表記錄數
            stats = {
                '使用者': User.query.count(),
                '供應商': Supplier.query.count(),
                '專案': Project.query.count(),
                '請購單': RequestOrder.query.count(),
                '採購單': PurchaseOrder.query.count()
            }

            print("\n  資料統計:")
            for table, count in stats.items():
                status = "✅" if count > 0 else "⚠️"
                print(f"    {status} {table}: {count} 筆")

            # 測試查詢
            print("\n  測試查詢:")
            admin = User.query.filter_by(username='admin').first()
            if admin:
                print(f"    ✅ 管理員帳號: {admin.chinese_name} ({admin.username})")

            return True

        except Exception as e:
            print(f"\n  ❌ 驗證失敗: {e}")
            return False

if __name__ == "__main__":
    success = True

    # 步驟1: 創建表
    if not create_all_tables():
        success = False

    # 步驟2: 遷移資料
    if success:
        if not migrate_data_from_sqlite():
            success = False

    # 步驟3: 驗證
    if success:
        if not verify_migration():
            success = False

    print("\n" + "="*60)
    if success:
        print("✅ PostgreSQL初始化成功！")
        print("\n使用以下命令啟動應用：")
        print("  cd backend")
        print("  set USE_POSTGRESQL=true")
        print("  python app.py")
    else:
        print("❌ PostgreSQL初始化失敗，請檢查錯誤訊息")
    print("="*60)

    sys.exit(0 if success else 1)