#!/usr/bin/env python
"""檢查 PostgreSQL 集運單資料"""
import os
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
    print("=== 檢查 PostgreSQL 集運資料 ===\n")

    # 1. 檢查 consolidation_pos 表結構
    print("1. consolidation_pos 表結構：")
    result = db.session.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'consolidation_pos'
        ORDER BY ordinal_position
    """))
    for row in result:
        print(f"   - {row[0]}: {row[1]} (nullable: {row[2]})")

    # 2. 檢查所有集運單
    print("\n2. 所有集運單：")
    result = db.session.execute(text("""
        SELECT consolidation_id, consolidation_name, logistics_status, created_at
        FROM shipment_consolidations
        ORDER BY created_at DESC
    """))
    consolidations = result.fetchall()
    for consol in consolidations:
        print(f"   - {consol[0]}: {consol[1]} (狀態: {consol[2]})")

    # 3. 檢查 consolidation_pos 資料
    print("\n3. consolidation_pos 關聯資料：")
    result = db.session.execute(text("""
        SELECT consolidation_id, purchase_order_no
        FROM consolidation_pos
    """))
    links = result.fetchall()
    if links:
        for link in links:
            print(f"   - 集運單 {link[0]} -> 採購單 {link[1]}")
    else:
        print("   ❌ 沒有找到任何關聯資料！")

    # 4. 檢查最新集運單的詳細資訊
    if consolidations:
        latest_consol = consolidations[0]
        print(f"\n4. 最新集運單詳情 ({latest_consol[0]})：")

        # 檢查採購單關聯
        result = db.session.execute(text("""
            SELECT cp.purchase_order_no, po.supplier_name
            FROM consolidation_pos cp
            LEFT JOIN purchase_orders po ON cp.purchase_order_no = po.purchase_order_no
            WHERE cp.consolidation_id = :consol_id
        """), {'consol_id': latest_consol[0]})

        pos = result.fetchall()
        if pos:
            print(f"   關聯的採購單：")
            for po in pos:
                print(f"   - {po[0]}: {po[1]}")
        else:
            print("   ❌ 沒有關聯的採購單")

    # 5. 檢查可用的採購單
    print("\n5. 可集運的採購單（未被關聯）：")
    result = db.session.execute(text("""
        SELECT po.purchase_order_no, po.supplier_name, po.delivery_status
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.supplier_id
        WHERE s.supplier_region = 'international'
        AND po.delivery_status = 'shipped'
        AND po.consolidation_id IS NULL
        ORDER BY po.purchase_order_no
    """))
    available_pos = result.fetchall()
    if available_pos:
        for po in available_pos:
            print(f"   - {po[0]}: {po[1]} (狀態: {po[2]})")
    else:
        print("   沒有可用的採購單")

    # 6. 檢查所有國際採購單狀態
    print("\n6. 所有國際採購單狀態：")
    result = db.session.execute(text("""
        SELECT po.purchase_order_no, po.supplier_name, po.delivery_status, po.consolidation_id
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.supplier_id
        WHERE s.supplier_region = 'international'
        ORDER BY po.created_at DESC
        LIMIT 10
    """))
    all_pos = result.fetchall()
    for po in all_pos:
        consol_status = f"已關聯到 {po[3]}" if po[3] else "未關聯"
        print(f"   - {po[0]}: {po[1]} (狀態: {po[2]}, {consol_status})")