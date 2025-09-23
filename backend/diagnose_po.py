#!/usr/bin/env python
"""
診斷採購單物流狀態腳本
用於檢查特定採購單的完整狀態和相關資訊
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
import json

def diagnose_po(po_number):
    """診斷特定採購單的狀態"""
    app = create_app()

    with app.app_context():
        print(f"{'='*80}")
        print(f"診斷採購單: {po_number}")
        print(f"診斷時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")

        # 1. 檢查採購單基本資訊
        print("【1. 採購單基本資訊】")

        # 先檢查資料庫中有哪些欄位
        check_columns = text("""
            SELECT sql FROM sqlite_master
            WHERE type='table' AND name='purchase_orders'
        """)

        table_info = db.session.execute(check_columns).fetchone()
        has_supplier_region = False
        if table_info and 'supplier_region' in str(table_info[0]):
            has_supplier_region = True

        # 根據欄位存在與否建構查詢
        if has_supplier_region:
            po_query = text("""
                SELECT
                    po.purchase_order_no,
                    po.supplier_id,
                    po.supplier_name,
                    po.supplier_region,
                    po.delivery_status,
                    po.shipping_status,
                    po.consolidation_id,
                    po.expected_delivery_date,
                    po.actual_delivery_date,
                    po.shipped_at,
                    po.remarks,
                    po.created_at,
                    po.updated_at,
                    s.supplier_region as supplier_actual_region
                FROM purchase_orders po
                LEFT JOIN suppliers s ON po.supplier_id = s.supplier_id
                WHERE po.purchase_order_no = :po_number
            """)
        else:
            po_query = text("""
                SELECT
                    po.purchase_order_no,
                    po.supplier_id,
                    po.supplier_name,
                    NULL as supplier_region,
                    po.delivery_status,
                    po.shipping_status,
                    po.consolidation_id,
                    po.expected_delivery_date,
                    po.actual_delivery_date,
                    po.shipped_at,
                    po.remarks,
                    po.created_at,
                    po.updated_at,
                    s.supplier_region as supplier_actual_region
                FROM purchase_orders po
                LEFT JOIN suppliers s ON po.supplier_id = s.supplier_id
                WHERE po.purchase_order_no = :po_number
            """)

        result = db.session.execute(po_query, {'po_number': po_number}).fetchone()

        if not result:
            print(f"❌ 找不到採購單: {po_number}")
            return

        print(f"  採購單號: {result.purchase_order_no}")
        print(f"  供應商ID: {result.supplier_id}")
        print(f"  供應商名稱: {result.supplier_name}")
        print(f"  供應商地區(PO): {result.supplier_region}")
        print(f"  供應商地區(實際): {result.supplier_actual_region}")
        print(f"  交貨狀態: {result.delivery_status}")
        print(f"  出貨狀態: {result.shipping_status}")
        print(f"  集運單ID: {result.consolidation_id or '無'}")
        print(f"  預計交貨日: {result.expected_delivery_date}")
        print(f"  實際交貨日: {result.actual_delivery_date}")
        print(f"  出貨時間: {result.shipped_at}")
        print(f"  備註: {result.remarks or '無'}")
        print(f"  建立時間: {result.created_at}")
        print(f"  更新時間: {result.updated_at}")
        print()

        # 2. 檢查集運單資訊（如果有）
        if result.consolidation_id:
            print("【2. 集運單資訊】")
            consol_query = text("""
                SELECT
                    consolidation_id,
                    consolidation_name,
                    logistics_status,
                    expected_delivery_date,
                    actual_delivery_date,
                    carrier,
                    tracking_number,
                    created_at,
                    updated_at
                FROM shipment_consolidations
                WHERE consolidation_id = :consolidation_id
            """)

            consol = db.session.execute(consol_query, {
                'consolidation_id': result.consolidation_id
            }).fetchone()

            if consol:
                print(f"  集運單ID: {consol.consolidation_id}")
                print(f"  集運單名稱: {consol.consolidation_name}")
                print(f"  物流狀態: {consol.logistics_status}")
                print(f"  預計交貨: {consol.expected_delivery_date}")
                print(f"  實際交貨: {consol.actual_delivery_date}")
                print(f"  承運商: {consol.carrier or '無'}")
                print(f"  追蹤號碼: {consol.tracking_number or '無'}")
                print(f"  建立時間: {consol.created_at}")
                print(f"  更新時間: {consol.updated_at}")
            else:
                print(f"  ⚠️ 找不到集運單: {result.consolidation_id}")
            print()

        # 3. 檢查採購單項目
        print("【3. 採購單項目】")
        items_query = text("""
            SELECT
                detail_id,
                item_name,
                item_specification,
                item_quantity,
                item_unit,
                line_status,
                delivery_status,
                remarks
            FROM purchase_order_items
            WHERE purchase_order_no = :po_number
        """)

        items = db.session.execute(items_query, {'po_number': po_number}).fetchall()

        if items:
            for idx, item in enumerate(items, 1):
                print(f"  項目 {idx}:")
                print(f"    ID: {item.detail_id}")
                print(f"    品名: {item.item_name}")
                print(f"    規格: {item.item_specification or '無'}")
                print(f"    數量: {item.item_quantity} {item.item_unit}")
                print(f"    行狀態: {item.line_status}")
                print(f"    交貨狀態: {item.delivery_status}")
                print(f"    備註: {item.remarks or '無'}")
        else:
            print("  ⚠️ 沒有找到採購單項目")
        print()

        # 4. 檢查是否應該出現在待收貨列表
        print("【4. 待收貨列表檢查】")
        print(f"  供應商地區: {result.supplier_actual_region or result.supplier_region}")
        print(f"  交貨狀態: {result.delivery_status}")
        print(f"  是否為國外單: {'是' if result.supplier_actual_region == 'foreign' or result.supplier_region == 'foreign' else '否'}")

        should_appear = False
        reason = ""

        if result.delivery_status == 'shipped':
            should_appear = True
            reason = "交貨狀態為 'shipped'"
        elif result.delivery_status == 'arrived':
            should_appear = False
            reason = "交貨狀態為 'arrived' (已到貨)"
        elif result.delivery_status == 'delivered':
            should_appear = False
            reason = "交貨狀態為 'delivered' (已交付)"
        else:
            should_appear = False
            reason = f"交貨狀態為 '{result.delivery_status}' (未出貨)"

        print(f"  應該出現在待收貨列表: {'✅ 是' if should_appear else '❌ 否'}")
        print(f"  原因: {reason}")
        print()

        # 5. 模擬 API 查詢
        print("【5. 模擬待收貨 API 查詢】")
        api_query = text("""
            SELECT
                po.purchase_order_no,
                po.supplier_name,
                po.supplier_region,
                po.delivery_status,
                po.shipped_at,
                poi.detail_id,
                poi.item_name,
                poi.item_specification,
                poi.item_quantity,
                poi.item_unit,
                poi.line_status,
                poi.remarks
            FROM purchase_orders po
            JOIN purchase_order_items poi ON po.purchase_order_no = poi.purchase_order_no
            WHERE po.delivery_status = 'shipped'
            AND po.purchase_order_no = :po_number
            AND poi.line_status = 'active'
        """)

        api_items = db.session.execute(api_query, {'po_number': po_number}).fetchall()

        if api_items:
            print(f"  ✅ API 查詢會返回 {len(api_items)} 個項目:")
            for item in api_items:
                print(f"    - {item.item_name} ({item.item_quantity} {item.item_unit})")
        else:
            print(f"  ❌ API 查詢不會返回此採購單")
            print(f"     可能原因:")
            if result.delivery_status != 'shipped':
                print(f"     - delivery_status 不是 'shipped' (當前: {result.delivery_status})")

            # 檢查是否所有項目都已收貨
            active_items = [i for i in items if i.line_status == 'active']
            if not active_items:
                print(f"     - 沒有 line_status='active' 的項目 (所有項目可能已收貨)")

        print()

        # 6. 建議
        print("【6. 診斷建議】")
        if result.delivery_status != 'shipped' and should_appear:
            if result.consolidation_id:
                print("  📌 此採購單屬於集運單，請檢查集運單狀態")
                print("     建議: 在交期維護中將集運單狀態設為 'shipped'")
            else:
                print("  📌 此採購單沒有集運單，請直接更新採購單狀態")
                print("     建議: 在交期維護中將採購單狀態設為 'shipped'")
        elif result.delivery_status == 'shipped' and not api_items:
            print("  📌 採購單狀態正確但沒有可收貨項目")
            print("     可能所有項目的 line_status 都不是 'active'")
            print("     建議: 檢查項目狀態是否正確")
        elif result.delivery_status == 'shipped' and api_items:
            print("  ✅ 採購單狀態正確，應該出現在待收貨列表")
            print("     如果前端沒顯示，可能是前端顯示問題")
        else:
            print("  ℹ️ 採購單狀態正常")

if __name__ == '__main__':
    # 可以從命令列參數獲取採購單號
    if len(sys.argv) > 1:
        po_number = sys.argv[1]
    else:
        po_number = 'PO20250923008'  # 預設診斷此單號

    diagnose_po(po_number)