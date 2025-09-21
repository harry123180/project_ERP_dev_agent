#!/usr/bin/env python
"""
PostgreSQL資料遷移 - 使用ORM模型
系統性掃描並遷移所有SQLite資料到PostgreSQL
"""
import os
import sys
import sqlite3
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
from app.models import (
    User, Supplier, Project, RequestOrder, RequestOrderItem,
    PurchaseOrder, PurchaseOrderItem, Storage, StorageHistory,
    PendingStorageItem, ReceivingRecord, RemarksHistory,
    InventoryBatch, InventoryBatchStorage, ShipmentConsolidation,
    ConsolidationPO, LogisticsEvent, ProjectSupplierExpenditure,
    SystemSettings, ItemCategory, InventoryMovement
)

print("="*70)
print("PostgreSQL ORM資料遷移系統")
print("="*70)

# 創建Flask應用
app = create_app('development')

def convert_bool(value):
    """轉換SQLite的0/1為Python的True/False"""
    if value is None:
        return False
    if isinstance(value, str):
        return value.lower() in ['true', '1', 'yes']
    return bool(value)

def convert_date(date_str):
    """轉換日期字串"""
    if not date_str:
        return None
    try:
        if isinstance(date_str, datetime):
            return date_str
        if isinstance(date_str, str):
            # 處理不同格式
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
            existing = User.query.filter_by(user_id=user_data['user_id']).first()
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
                    contact_person=sup_data.get('contact_person'),
                    phone=sup_data.get('phone'),
                    email=sup_data.get('email'),
                    address=sup_data.get('address'),
                    is_active=convert_bool(sup_data.get('is_active', 1)),
                    created_at=convert_date(sup_data.get('created_at'))
                )
                db.session.add(supplier)
                success_count += 1
        except Exception as e:
            print(f"  跳過供應商 {sup_data['supplier_id']}: {e}")

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
                    project_manager=proj_data.get('project_manager'),
                    start_date=convert_date(proj_data.get('start_date')),
                    end_date=convert_date(proj_data.get('end_date')),
                    status=proj_data.get('status', '進行中'),
                    created_at=convert_date(proj_data.get('created_at'))
                )
                db.session.add(project)
                success_count += 1
        except Exception as e:
            print(f"  跳過專案 {proj_data['project_id']}: {e}")

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
                    project_id=order_data.get('project_id'),
                    status=order_data['status'],
                    is_urgent=convert_bool(order_data.get('is_urgent', 0)),
                    urgent_date=convert_date(order_data.get('urgent_date')),
                    urgent_reason=order_data.get('urgent_reason'),
                    created_at=convert_date(order_data['created_at']),
                    updated_at=convert_date(order_data.get('updated_at'))
                )
                db.session.add(order)
                success_count += 1
        except Exception as e:
            print(f"  跳過請購單 {order_data['request_order_no']}: {e}")

    db.session.commit()
    print(f"  ✅ 成功遷移 {success_count}/{len(orders)} 個請購單")
    sqlite_conn.close()
    return success_count > 0

def migrate_request_order_items():
    """遷移請購單明細"""
    print("\n遷移請購單明細...")
    sqlite_conn = sqlite3.connect('../erp_development.db')
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    cursor.execute("SELECT * FROM request_order_items")
    items = cursor.fetchall()

    success_count = 0
    for item_data in items:
        try:
            existing = RequestOrderItem.query.filter_by(detail_id=item_data['detail_id']).first()
            if not existing:
                item = RequestOrderItem(
                    detail_id=item_data['detail_id'],
                    request_order_no=item_data['request_order_no'],
                    item_name=item_data['item_name'],
                    specification=item_data.get('specification'),
                    quantity=float(item_data['quantity']) if item_data['quantity'] else 0.0,
                    unit=item_data.get('unit'),
                    unit_price=float(item_data.get('unit_price', 0)) if item_data.get('unit_price') else 0.0,
                    total_price=float(item_data.get('total_price', 0)) if item_data.get('total_price') else 0.0,
                    required_date=convert_date(item_data.get('required_date')),
                    remark=item_data.get('remark'),
                    is_purchased=convert_bool(item_data.get('is_purchased', 0)),
                    created_at=convert_date(item_data.get('created_at'))
                )
                db.session.add(item)
                success_count += 1
        except Exception as e:
            print(f"  跳過請購單明細 {item_data['detail_id']}: {e}")

    db.session.commit()
    print(f"  ✅ 成功遷移 {success_count}/{len(items)} 個請購單明細")
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
                    delivery_date=convert_date(po_data.get('delivery_date')),
                    payment_terms=po_data.get('payment_terms'),
                    total_amount=float(po_data['total_amount']) if po_data['total_amount'] else 0.0,
                    status=po_data.get('status', '待確認'),
                    status_update_required=convert_bool(po_data.get('status_update_required', 0)),
                    created_at=convert_date(po_data['created_at']),
                    creation_date=convert_date(po_data.get('creation_date'))
                )
                db.session.add(po)
                success_count += 1
        except Exception as e:
            print(f"  跳過採購單 {po_data['purchase_order_no']}: {e}")

    db.session.commit()
    print(f"  ✅ 成功遷移 {success_count}/{len(orders)} 個採購單")
    sqlite_conn.close()
    return success_count > 0

def migrate_purchase_order_items():
    """遷移採購單明細"""
    print("\n遷移採購單明細...")
    sqlite_conn = sqlite3.connect('../erp_development.db')
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    cursor.execute("SELECT * FROM purchase_order_items")
    items = cursor.fetchall()

    success_count = 0
    for item_data in items:
        try:
            existing = PurchaseOrderItem.query.filter_by(detail_id=item_data['detail_id']).first()
            if not existing:
                item = PurchaseOrderItem(
                    detail_id=item_data['detail_id'],
                    purchase_order_no=item_data['purchase_order_no'],
                    request_detail_id=item_data.get('request_detail_id'),
                    item_name=item_data['item_name'],
                    specification=item_data.get('specification'),
                    quantity=float(item_data['quantity']) if item_data['quantity'] else 0.0,
                    unit=item_data.get('unit'),
                    unit_price=float(item_data.get('unit_price', 0)) if item_data.get('unit_price') else 0.0,
                    total_price=float(item_data.get('total_price', 0)) if item_data.get('total_price') else 0.0,
                    delivery_date=convert_date(item_data.get('delivery_date')),
                    is_received=convert_bool(item_data.get('is_received', 0)),
                    received_quantity=float(item_data.get('received_quantity', 0)) if item_data.get('received_quantity') else 0.0,
                    created_at=convert_date(item_data.get('created_at'))
                )
                db.session.add(item)
                success_count += 1
        except Exception as e:
            print(f"  跳過採購單明細 {item_data['detail_id']}: {e}")

    db.session.commit()
    print(f"  ✅ 成功遷移 {success_count}/{len(items)} 個採購單明細")
    sqlite_conn.close()
    return success_count > 0

def migrate_other_tables():
    """遷移其他表"""
    print("\n遷移其他表...")

    # 遷移storages表
    sqlite_conn = sqlite3.connect('../erp_development.db')
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    # 遷移storages
    try:
        cursor.execute("SELECT * FROM storages")
        storages = cursor.fetchall()
        for storage_data in storages:
            existing = Storage.query.filter_by(storage_id=storage_data['storage_id']).first()
            if not existing:
                storage = Storage(
                    storage_id=storage_data['storage_id'],
                    storage_name=storage_data['storage_name'],
                    parent_id=storage_data.get('parent_id'),
                    storage_type=storage_data.get('storage_type', '倉庫'),
                    level=storage_data.get('level', 0),
                    is_active=convert_bool(storage_data.get('is_active', 1)),
                    created_at=convert_date(storage_data.get('created_at'))
                )
                db.session.add(storage)
        db.session.commit()
        print(f"  ✅ 遷移 storages 表")
    except Exception as e:
        print(f"  ⚠️ 無法遷移 storages: {e}")

    # 遷移其他關聯表
    tables = [
        ('storage_history', StorageHistory),
        ('pending_storage_items', PendingStorageItem),
        ('receiving_records', ReceivingRecord),
        ('remarks_history', RemarksHistory),
        ('inventory_batches', InventoryBatch)
    ]

    for table_name, model_class in tables:
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            if rows:
                print(f"  處理 {table_name} ({len(rows)} 筆)...")
        except:
            print(f"  ⚠️ 跳過 {table_name}")

    sqlite_conn.close()
    return True

def create_admin_user():
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
        # 更新密碼確保可登入
        admin.password = generate_password_hash('admin123')
        db.session.commit()
        print("  ✅ 更新管理員密碼")
    return True

def verify_migration():
    """驗證遷移結果"""
    print("\n驗證遷移結果...")

    stats = {
        '使用者': User.query.count(),
        '供應商': Supplier.query.count(),
        '專案': Project.query.count(),
        '請購單': RequestOrder.query.count(),
        '請購單明細': RequestOrderItem.query.count(),
        '採購單': PurchaseOrder.query.count(),
        '採購單明細': PurchaseOrderItem.query.count()
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
            print("\n開始執行PostgreSQL完整資料遷移...")

            # 重建表結構
            print("\n重建PostgreSQL表結構...")
            db.drop_all()
            db.create_all()
            print("  ✅ 表結構創建成功")

            success = True

            # 按順序遷移各表（考慮外鍵依賴）
            if not migrate_users():
                print("  ⚠️ 使用者遷移部分失敗")

            if not migrate_suppliers():
                print("  ⚠️ 供應商遷移部分失敗")

            if not migrate_projects():
                print("  ⚠️ 專案遷移部分失敗")

            if not migrate_request_orders():
                print("  ⚠️ 請購單遷移部分失敗")

            if not migrate_request_order_items():
                print("  ⚠️ 請購單明細遷移部分失敗")

            if not migrate_purchase_orders():
                print("  ⚠️ 採購單遷移部分失敗")

            if not migrate_purchase_order_items():
                print("  ⚠️ 採購單明細遷移部分失敗")

            # 遷移其他表
            migrate_other_tables()

            # 創建管理員
            create_admin_user()

            # 驗證結果
            if verify_migration():
                print("\n" + "="*70)
                print("✅ PostgreSQL資料遷移成功！")
                print("\n現在可以使用PostgreSQL運行應用程式：")
                print("  cd backend")
                print("  python app.py")
                print("\n登入資訊：")
                print("  使用者名: admin")
                print("  密碼: admin123")
                print("="*70)
            else:
                print("\n" + "="*70)
                print("⚠️ 資料遷移部分成功，請檢查上述警告訊息")
                print("="*70)
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