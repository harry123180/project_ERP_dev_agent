#!/usr/bin/env python
"""修復 item_categories 表缺少的類別"""
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
    print("=== 修復 item_categories 表 ===\n")

    # 1. 檢查現有類別
    print("1. 檢查現有類別：")
    result = db.session.execute(text("""
        SELECT category_code, category_name
        FROM item_categories
        ORDER BY category_code
    """))
    existing = result.fetchall()

    if existing:
        for row in existing:
            print(f"   - {row[0]}: {row[1]}")
    else:
        print("   沒有找到任何類別")

    # 2. 新增缺少的類別
    print("\n2. 新增標準類別：")
    categories_to_add = [
        ('tool', '工具'),
        ('material', '材料'),
        ('equipment', '設備'),
        ('consumable', '消耗品'),
        ('spare_part', '備品'),
        ('software', '軟體'),
        ('service', '服務'),
        ('other', '其他')
    ]

    for code, name in categories_to_add:
        try:
            # 檢查是否已存在
            check_result = db.session.execute(
                text("SELECT 1 FROM item_categories WHERE category_code = :code"),
                {'code': code}
            )

            if not check_result.fetchone():
                # 新增類別
                db.session.execute(text("""
                    INSERT INTO item_categories (category_code, category_name, is_active, created_at, updated_at)
                    VALUES (:code, :name, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """), {'code': code, 'name': name})
                print(f"   ✓ 新增類別: {code} ({name})")
            else:
                print(f"   - 類別已存在: {code}")

        except Exception as e:
            print(f"   ✗ 新增類別 {code} 失敗: {str(e)}")

    # 提交變更
    try:
        db.session.commit()
        print("\n✓ 所有變更已提交")
    except Exception as e:
        db.session.rollback()
        print(f"\n✗ 提交失敗: {str(e)}")

    # 3. 驗證結果
    print("\n3. 驗證最終類別列表：")
    result = db.session.execute(text("""
        SELECT category_code, category_name
        FROM item_categories
        ORDER BY category_code
    """))

    for row in result:
        print(f"   - {row[0]}: {row[1]}")