#!/usr/bin/env python
"""
修復採購單項目狀態腳本
將已出貨但被錯誤標記為completed的項目重置為active
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def fix_po_item_status(po_number):
    """修復採購單項目狀態"""
    app = create_app()

    with app.app_context():
        print(f"{'='*80}")
        print(f"修復採購單項目狀態: {po_number}")
        print(f"修復時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")

        # 1. 檢查採購單狀態
        print("【1. 檢查採購單狀態】")
        po_query = text("""
            SELECT
                purchase_order_no,
                supplier_name,
                delivery_status,
                shipping_status
            FROM purchase_orders
            WHERE purchase_order_no = :po_number
        """)

        po = db.session.execute(po_query, {'po_number': po_number}).fetchone()

        if not po:
            print(f"❌ 找不到採購單: {po_number}")
            return

        print(f"  採購單號: {po.purchase_order_no}")
        print(f"  供應商: {po.supplier_name}")
        print(f"  交貨狀態: {po.delivery_status}")
        print(f"  出貨狀態: {po.shipping_status}")
        print()

        # 2. 檢查項目狀態
        print("【2. 檢查項目狀態】")
        items_query = text("""
            SELECT
                detail_id,
                item_name,
                line_status,
                delivery_status
            FROM purchase_order_items
            WHERE purchase_order_no = :po_number
        """)

        items = db.session.execute(items_query, {'po_number': po_number}).fetchall()

        needs_fix = False
        for item in items:
            print(f"  項目ID: {item.detail_id}")
            print(f"  品名: {item.item_name}")
            print(f"  行狀態: {item.line_status}")
            print(f"  交貨狀態: {item.delivery_status}")

            if po.delivery_status == 'shipped' and item.line_status != 'active':
                print(f"    ⚠️ 需要修復: 採購單已出貨但項目狀態為 {item.line_status}")
                needs_fix = True
            print()

        if not needs_fix:
            print("✅ 項目狀態正常，無需修復")
            return

        # 3. 執行修復
        print("【3. 執行修復】")

        # 如果採購單是shipped狀態，但項目不是active，則修復
        if po.delivery_status == 'shipped':
            fix_query = text("""
                UPDATE purchase_order_items
                SET line_status = 'active',
                    delivery_status = 'pending',
                    updated_at = :updated_at
                WHERE purchase_order_no = :po_number
                AND line_status != 'active'
            """)

            result = db.session.execute(fix_query, {
                'po_number': po_number,
                'updated_at': datetime.utcnow()
            })

            db.session.commit()

            print(f"  ✅ 已修復 {result.rowcount} 個項目的狀態")

            # 4. 驗證修復結果
            print("\n【4. 驗證修復結果】")
            verify_query = text("""
                SELECT
                    detail_id,
                    item_name,
                    line_status,
                    delivery_status
                FROM purchase_order_items
                WHERE purchase_order_no = :po_number
            """)

            verified_items = db.session.execute(verify_query, {'po_number': po_number}).fetchall()

            for item in verified_items:
                print(f"  項目ID: {item.detail_id}")
                print(f"  品名: {item.item_name}")
                print(f"  行狀態: {item.line_status} {'✅' if item.line_status == 'active' else '❌'}")
                print(f"  交貨狀態: {item.delivery_status}")
                print()

            print("✅ 修復完成！現在這個採購單的項目應該出現在待收貨列表中。")
        else:
            print("❌ 採購單狀態不是 'shipped'，請先在交期維護中將其設為已出貨")

if __name__ == '__main__':
    # 可以從命令列參數獲取採購單號
    if len(sys.argv) > 1:
        po_number = sys.argv[1]
    else:
        po_number = 'PO20250923008'  # 預設修復此單號

    fix_po_item_status(po_number)