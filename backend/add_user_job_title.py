#!/usr/bin/env python
"""
為users表新增job_title欄位
"""

from app import create_app, db
from sqlalchemy import text

def add_job_title_column():
    """新增job_title欄位到users表"""
    app = create_app()
    
    with app.app_context():
        try:
            # 檢查欄位是否已存在
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM pragma_table_info('users') WHERE name='job_title'"
            )).scalar()
            
            if result > 0:
                print("✅ job_title欄位已存在，無需新增")
                return
            
            # 新增job_title欄位
            db.session.execute(text(
                "ALTER TABLE users ADD COLUMN job_title VARCHAR(100)"
            ))
            
            # 設定預設值
            db.session.execute(text(
                "UPDATE users SET job_title = '員工' WHERE job_title IS NULL"
            ))
            
            db.session.commit()
            print("✅ 成功新增job_title欄位到users表")
            
            # 更新現有用戶的職稱
            db.session.execute(text("""
                UPDATE users 
                SET job_title = CASE 
                    WHEN role = 'Admin' THEN '系統管理員'
                    WHEN role = 'Procurement' THEN '採購專員'
                    WHEN role = 'ProcurementMgr' THEN '採購經理'
                    WHEN role = 'Manager' THEN '部門經理'
                    WHEN role = 'IT' THEN 'IT專員'
                    ELSE '員工'
                END
                WHERE job_title = '員工' OR job_title IS NULL
            """))
            
            db.session.commit()
            print("✅ 已根據角色更新職稱預設值")
            
        except Exception as e:
            print(f"❌ 錯誤: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    add_job_title_column()