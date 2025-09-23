#!/usr/bin/env python
"""為 PostgreSQL 創建集運測試數據"""
import os
from datetime import datetime
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 強制使用 PostgreSQL
os.environ['DATABASE_URL'] = 'postgresql://postgres:64946849@localhost:5432/erp_production'
os.environ['FLASK_ENV'] = 'production'

from app import create_app, db
from sqlalchemy import text

app = create_app('production')

with app.app_context():
    print("=== 創建 PostgreSQL 集運測試數據 ===\n")

    try:
        # 1. 確認有國際供應商
        result = db.session.execute(text("""
            SELECT supplier_id, supplier_name_en
            FROM suppliers
            WHERE supplier_region = 'international'
            LIMIT 2
        """))
        suppliers = result.fetchall()

        if len(suppliers) < 2:
            print("創建國際供應商...")
            # 創建測試供應商
            import uuid
            for name in ['Samsung Electronics', 'Apple Inc']:
                supplier_id = f"SUP-{uuid.uuid4().hex[:8].upper()}"
                db.session.execute(text("""
                    INSERT INTO suppliers (
                        supplier_id, supplier_name_zh, supplier_name_en,
                        supplier_region, is_active
                    ) VALUES (:id, :name, :name, 'international', true)
                """), {'id': supplier_id, 'name': name})
            db.session.commit()

            # 重新取得供應商
            result = db.session.execute(text("""
                SELECT supplier_id, supplier_name_en
                FROM suppliers
                WHERE supplier_region = 'international'
                LIMIT 2
            """))
            suppliers = result.fetchall()

        print(f"找到 {len(suppliers)} 個國際供應商")

        # 2. 創建測試採購單
        user_id = 1  # 使用 harry123180 的 user_id
        current_time = datetime.now()

        po_numbers = []
        for i, supplier in enumerate(suppliers):
            po_no = f"PO{current_time.strftime('%Y%m%d')}PSQL{str(i+1).zfill(3)}"
            po_numbers.append(po_no)

            # 檢查採購單是否已存在
            existing = db.session.execute(text(
                "SELECT 1 FROM purchase_orders WHERE purchase_order_no = :po_no"
            ), {'po_no': po_no}).fetchone()

            if not existing:
                print(f"創建採購單: {po_no}")
                db.session.execute(text("""
                    INSERT INTO purchase_orders (
                        purchase_order_no, supplier_id, supplier_name,
                        order_date, purchase_status, shipping_status,
                        delivery_status, expected_delivery_date,
                        subtotal_int, grand_total_int,
                        creator_id, status_update_required,
                        created_at, updated_at
                    ) VALUES (
                        :po_no, :supplier_id, :supplier_name,
                        :order_date, 'purchased', 'shipped',
                        'shipped', :expected_date,
                        50000, 55000,
                        :user_id, false,
                        :created_at, :updated_at
                    )
                """), {
                    'po_no': po_no,
                    'supplier_id': supplier[0],
                    'supplier_name': supplier[1],
                    'order_date': current_time,
                    'expected_date': '2025-10-15',
                    'user_id': user_id,
                    'created_at': current_time,
                    'updated_at': current_time
                })

                # 創建採購單項目
                for j in range(2):
                    db.session.execute(text("""
                        INSERT INTO purchase_order_items (
                            purchase_order_no, item_name, item_specification,
                            item_quantity, item_unit, unit_price,
                            line_subtotal_int, delivery_status, line_status
                        ) VALUES (
                            :po_no, :item_name, :spec,
                            :qty, 'pcs', 1000,
                            :subtotal, 'not_shipped', 'active'
                        )
                    """), {
                        'po_no': po_no,
                        'item_name': f'測試產品 {j+1}',
                        'spec': f'規格 {j+1}',
                        'qty': 10 + j * 5,
                        'subtotal': (10 + j * 5) * 1000
                    })

                print(f"  ✓ 創建 {po_no} 包含 2 個項目")

        db.session.commit()

        # 3. 驗證數據
        print("\n=== 驗證可集運採購單 ===")
        result = db.session.execute(text("""
            SELECT po.purchase_order_no, po.supplier_name, s.supplier_region
            FROM purchase_orders po
            JOIN suppliers s ON po.supplier_id = s.supplier_id
            WHERE s.supplier_region = 'international'
            AND po.delivery_status = 'shipped'
            AND po.consolidation_id IS NULL
        """))

        eligible_pos = result.fetchall()
        print(f"找到 {len(eligible_pos)} 個可集運的採購單:")
        for po in eligible_pos:
            print(f"  - {po[0]}: {po[1]} (地區: {po[2]})")

        print("\n✓ 測試數據創建成功")
        print("\n現在可以在前端創建集運單了！")

    except Exception as e:
        print(f"錯誤: {e}")
        db.session.rollback()
        import traceback
        traceback.print_exc()