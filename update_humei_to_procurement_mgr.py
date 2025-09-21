#!/usr/bin/env python
"""
Update humei account role to ProcurementMgr (採購主管)
"""
import os
import psycopg2
from psycopg2 import sql

# PostgreSQL connection
conn_params = {
    'host': 'localhost',
    'port': 5432,
    'database': 'erp_database',
    'user': 'erp_user',
    'password': '271828'
}

def update_humei_role():
    """Update humei role to ProcurementMgr"""
    conn = None
    cursor = None

    try:
        # Connect to PostgreSQL
        print("Connecting to PostgreSQL...")
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()

        # Check current status
        print("\n檢查 humei 帳號當前狀態...")
        cursor.execute("""
            SELECT user_id, username, chinese_name, role, is_active
            FROM users
            WHERE username = 'humei'
        """)
        user = cursor.fetchone()

        if user:
            user_id, username, chinese_name, role, is_active = user
            print(f"找到帳號: {username} ({chinese_name})")
            print(f"當前角色: {role}")
            print(f"啟用狀態: {is_active}")

            # Update to ProcurementMgr role
            print("\n更新角色為 'ProcurementMgr' (採購主管)...")
            cursor.execute("""
                UPDATE users
                SET role = 'ProcurementMgr'
                WHERE username = 'humei'
            """)

            # Verify the change
            cursor.execute("""
                SELECT username, chinese_name, role
                FROM users
                WHERE username = 'humei'
            """)
            updated = cursor.fetchone()

            # Commit changes
            conn.commit()

            print(f"✅ 更新成功！")
            print(f"   帳號: {updated[0]}")
            print(f"   中文姓名: {updated[1]}")
            print(f"   新角色: {updated[2]}")

            print("\n📋 採購主管 (ProcurementMgr) 權限:")
            print("   - 審核請購單 ✅")
            print("   - 管理採購流程 ✅")
            print("   - 核准採購訂單 ✅")
            print("   - 會計採購管理 ✅")
            print("   - 查看所有採購相關報表 ✅")
            print("   - 管理供應商資料 ✅")

            print("\n⚠️  重要提醒: humei 必須重新登入系統")
            print("   新的角色權限才會生效！")

        else:
            print("❌ 找不到 humei 帳號！")
            print("需要先建立該帳號。")

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    update_humei_role()