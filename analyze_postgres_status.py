#!/usr/bin/env python
"""
分析PostgreSQL資料庫狀態和問題
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

def analyze_database():
    """分析資料庫狀態"""

    # PostgreSQL連接配置
    pg_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'erp_database',
        'user': 'erp_user',
        'password': '271828'
    }

    print("="*60)
    print("PostgreSQL資料庫狀態分析")
    print("="*60)

    try:
        # 連接資料庫
        conn = psycopg2.connect(**pg_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 1. 檢查所有表
        print("\n1. 檢查現有表：")
        cursor.execute("""
            SELECT table_name,
                   pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()

        if tables:
            for table in tables:
                print(f"   ✓ {table['table_name']:30} 大小: {table['size']}")
        else:
            print("   ❌ 沒有找到任何表")

        # 2. 檢查每個表的記錄數
        print(f"\n2. 表記錄統計：")
        table_stats = []
        for table in tables:
            table_name = table['table_name']
            if table_name != 'alembic_version':
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                    count = cursor.fetchone()['count']
                    table_stats.append((table_name, count))
                    status = "✓ 有資料" if count > 0 else "⚠ 空表"
                    print(f"   {table_name:30} {count:6} 筆記錄 {status}")
                except:
                    print(f"   {table_name:30} 無法查詢")

        # 3. 檢查表結構中的Boolean欄位
        print(f"\n3. Boolean欄位分析：")
        cursor.execute("""
            SELECT table_name, column_name, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND data_type = 'boolean'
            ORDER BY table_name, column_name
        """)
        boolean_columns = cursor.fetchall()

        for col in boolean_columns:
            default = col['column_default'] or 'NULL'
            # 檢查默認值是否有問題
            if '0' in str(default) or '1' in str(default):
                print(f"   ⚠ {col['table_name']}.{col['column_name']} - 默認值問題: {default}")
            else:
                print(f"   ✓ {col['table_name']}.{col['column_name']} - 默認值: {default}")

        # 4. 分析需要修復的問題
        print(f"\n4. 問題總結：")

        # 統計空表
        empty_tables = [t for t, c in table_stats if c == 0]
        if empty_tables:
            print(f"   ⚠ {len(empty_tables)} 個空表需要資料遷移")
            for table in empty_tables[:5]:  # 只顯示前5個
                print(f"      - {table}")
            if len(empty_tables) > 5:
                print(f"      ... 還有 {len(empty_tables) - 5} 個")

        # Boolean默認值問題
        problematic_booleans = [col for col in boolean_columns
                                if '0' in str(col['column_default']) or '1' in str(col['column_default'])]
        if problematic_booleans:
            print(f"   ⚠ {len(problematic_booleans)} 個Boolean欄位有默認值問題")

        # 5. 驗證表結構完整性
        print(f"\n5. 關鍵表結構驗證：")
        key_tables = ['users', 'suppliers', 'projects', 'request_orders', 'purchase_orders']
        for table_name in key_tables:
            cursor.execute(f"""
                SELECT COUNT(*) as col_count
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = '{table_name}'
            """)
            col_count = cursor.fetchone()
            if col_count:
                print(f"   ✓ {table_name}: {col_count['col_count']} 個欄位")
            else:
                print(f"   ❌ {table_name}: 表不存在")

        cursor.close()
        conn.close()

        print("\n" + "="*60)
        print("分析完成！")
        return True

    except psycopg2.Error as e:
        print(f"\n❌ 資料庫錯誤: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 未預期錯誤: {e}")
        return False

if __name__ == "__main__":
    success = analyze_database()
    sys.exit(0 if success else 1)