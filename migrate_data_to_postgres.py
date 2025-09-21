#!/usr/bin/env python
"""
使用ORM模型遷移資料到PostgreSQL
"""
import os
import sys
import sqlite3
from datetime import datetime
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
from app.models import User, Supplier, Project, RequestOrder, PurchaseOrder, RequestOrderItem, PurchaseOrderItem

print("="*60)
print("PostgreSQL資料遷移（使用ORM）")
print("="*60)

# 創建Flask應用
app = create_app('development')

def convert_bool(value):
    """轉換SQLite的0/1為Python的True/False"""
    if value is None:
        return False
    return bool(value)

def convert_date(date_str):
    """轉換日期字串"""
    if not date_str:
        return None
    try:
        # 處理不同的日期格式
        if 'T' in date_str:
            date_str = date_str.replace('T', ' ')
        if '.' in date_str:
            date_str = date_str.split('.')[0]

        if len(date_str) == 10:  # YYYY-MM-DD
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        else:  # YYYY-MM-DD HH:MM:SS
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except:
        return None

def migrate_users():
    """遷移使用者"""
    print("\n遷移使用者...")
    sqlite_conn = sqlite3.connect('../erp_development.db')
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    success_count = 0
    for user_data in users:
        try:
            # 檢查是否已存在
            existing = User.query.filter_by(username=user_data['username']).first()
            if not existing:
                user = User(
                    user_id=user_data['user_id'],
                    chinese_name=user_data['chinese_name'],
                    username=user_data['username'],
                    password=user_data['password'],
                    department=user_data['department'],
                    role=user_data['role'],
                    is_active=convert_bool(user_data['is_active']),
                    created_at=convert_date(user_data['created_at'])
                )
                db.session.add(user)
                success_count += 1
        except Exception as e:
            print(f"  跳過使用者 {user_data['username']}: {e}")

    db.session.commit()
    print(f"  ✅ 成功遷移 {success_count}/{len(users)} 個使用者")
    sqlite_conn.close()
    return success_count > 0

def migrate_suppliers():
    """遷移供應商"""
    print("\n遷移供應商...")
    sqlite_conn = sqlite3.connect('../erp_development.db')
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    cursor.execute("SELECT * FROM suppliers")
    suppliers = cursor.fetchall()

    success_count = 0
    for sup_data in suppliers:
        try:
            existing = Supplier.query.filter_by(supplier_id=sup_data['supplier_id']).first()
            if not existing:
                supplier = Supplier(
                    supplier_id=sup_data['supplier_id'],
                    supplier_name=sup_data['supplier_name'],
                    contact_person=sup_data['contact_person'],
                    phone=sup_data['phone'],
                    email=sup_data['email'],
                    address=sup_data['address'],
                    is_active=convert_bool(sup_data['is_active']),
                    created_at=convert_date(sup_data['created_at'])
                )
                db.session.add(supplier)
                success_count += 1
        except Exception as e:
            print(f"  跳過供應商 {sup_data['supplier_name']}: {e}")

    db.session.commit()
    print(f"  ✅ 成功遷移 {success_count}/{len(suppliers)} 個供應商")
    sqlite_conn.close()
    return success_count > 0

def migrate_projects():
    """遷移專案"""
    print("\n遷移專案...")
    sqlite_conn = sqlite3.connect('../erp_development.db')
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()

    success_count = 0
    for proj_data in projects:
        try:
            existing = Project.query.filter_by(project_id=proj_data['project_id']).first()
            if not existing:
                project = Project(
                    project_id=proj_data['project_id'],
                    project_name=proj_data['project_name'],
                    project_code=proj_data['project_code'],
                    budget=float(proj_data['budget']) if proj_data['budget'] else 0.0,
                    project_manager=proj_data['project_manager'],
                    start_date=convert_date(proj_data['start_date']),
                    end_date=convert_date(proj_data['end_date']),
                    status=proj_data['status'],
                    created_at=convert_date(proj_data['created_at'])
                )
                db.session.add(project)
                success_count += 1
        except Exception as e:
            print(f"  跳過專案 {proj_data['project_name']}: {e}")

    db.session.commit()
    print(f"  ✅ 成功遷移 {success_count}/{len(projects)} 個專案")
    sqlite_conn.close()
    return success_count > 0

def migrate_request_orders():
    """遷移請購單"""
    print("\n遷移請購單...")
    sqlite_conn = sqlite3.connect('../erp_development.db')
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    cursor.execute("SELECT * FROM request_orders")
    orders = cursor.fetchall()

    success_count = 0
    for order_data in orders:
        try:
            existing = RequestOrder.query.filter_by(request_order_no=order_data['request_order_no']).first()
            if not existing:
                order = RequestOrder(
                    request_order_no=order_data['request_order_no'],
                    request_date=convert_date(order_data['request_date']),
                    applicant_id=order_data['applicant_id'],
                    project_id=order_data['project_id'],
                    status=order_data['status'],
                    is_urgent=convert_bool(order_data['is_urgent']),
                    urgent_date=convert_date(order_data['urgent_date']),
                    urgent_reason=order_data['urgent_reason'],
                    created_at=convert_date(order_data['created_at']),
                    updated_at=convert_date(order_data['updated_at'])
                )
                db.session.add(order)
                success_count += 1
        except Exception as e:
            print(f"  跳過請購單 {order_data['request_order_no']}: {e}")

    db.session.commit()
    print(f"  ✅ 成功遷移 {success_count}/{len(orders)} 個請購單")
    sqlite_conn.close()
    return success_count > 0

def migrate_purchase_orders():
    """遷移採購單"""
    print("\n遷移採購單...")
    sqlite_conn = sqlite3.connect('../erp_development.db')
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    cursor.execute("SELECT * FROM purchase_orders")
    orders = cursor.fetchall()

    success_count = 0
    for po_data in orders:
        try:
            existing = PurchaseOrder.query.filter_by(purchase_order_no=po_data['purchase_order_no']).first()
            if not existing:
                po = PurchaseOrder(
                    purchase_order_no=po_data['purchase_order_no'],
                    supplier_id=po_data['supplier_id'],
                    order_date=convert_date(po_data['order_date']),
                    delivery_date=convert_date(po_data['delivery_date']),
                    payment_terms=po_data['payment_terms'],
                    total_amount=float(po_data['total_amount']) if po_data['total_amount'] else 0.0,
                    status=po_data['status'],
                    status_update_required=convert_bool(po_data.get('status_update_required', 0)),
                    created_at=convert_date(po_data['created_at']),
                    creation_date=convert_date(po_data['creation_date'])
                )
                db.session.add(po)
                success_count += 1
        except Exception as e:
            print(f"  跳過採購單 {po_data['purchase_order_no']}: {e}")

    db.session.commit()
    print(f"  ✅ 成功遷移 {success_count}/{len(orders)} 個採購單")
    sqlite_conn.close()
    return success_count > 0

def create_default_admin():
    """創建預設管理員"""
    print("\n檢查管理員帳號...")
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
        print("  ✅ 創建了預設管理員帳號 (admin/admin123)")
    else:
        print("  ✅ 管理員帳號已存在")
    return True

def verify_migration():
    """驗證遷移結果"""
    print("\n驗證遷移結果...")

    stats = {
        '使用者': User.query.count(),
        '供應商': Supplier.query.count(),
        '專案': Project.query.count(),
        '請購單': RequestOrder.query.count(),
        '採購單': PurchaseOrder.query.count()
    }

    print("\n資料統計:")
    total_count = 0
    for table, count in stats.items():
        status = "✅" if count > 0 else "⚠️"
        print(f"  {status} {table}: {count} 筆")
        total_count += count

    return total_count > 0

def main():
    with app.app_context():
        try:
            success = True

            # 遷移各表
            if not migrate_users():
                print("  ⚠️ 使用者遷移失敗")

            if not migrate_suppliers():
                print("  ⚠️ 供應商遷移失敗")

            if not migrate_projects():
                print("  ⚠️ 專案遷移失敗")

            if not migrate_request_orders():
                print("  ⚠️ 請購單遷移失敗")

            if not migrate_purchase_orders():
                print("  ⚠️ 採購單遷移失敗")

            # 創建管理員
            create_default_admin()

            # 驗證結果
            if verify_migration():
                print("\n" + "="*60)
                print("✅ PostgreSQL資料遷移成功！")
                print("\n現在可以使用PostgreSQL運行應用程式：")
                print("  cd backend")
                print("  python app.py")
                print("="*60)
            else:
                print("\n" + "="*60)
                print("⚠️ 資料遷移部分成功，請檢查上述警告訊息")
                print("="*60)
                success = False

            return success

        except Exception as e:
            print(f"\n❌ 遷移失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)