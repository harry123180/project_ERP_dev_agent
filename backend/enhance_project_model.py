#!/usr/bin/env python
"""
增強Project模型 - 添加預算和描述欄位
"""

from app import create_app, db
from sqlalchemy import text

def enhance_project_model():
    """為projects表新增預算和描述欄位"""
    app = create_app()
    
    with app.app_context():
        try:
            # 檢查budget欄位是否已存在
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM pragma_table_info('projects') WHERE name='budget'"
            )).scalar()
            
            if result == 0:
                # 新增budget欄位
                db.session.execute(text(
                    "ALTER TABLE projects ADD COLUMN budget DECIMAL(15, 2) DEFAULT 0"
                ))
                print("✅ 成功新增budget欄位")
            else:
                print("✅ budget欄位已存在")
            
            # 檢查description欄位是否已存在
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM pragma_table_info('projects') WHERE name='description'"
            )).scalar()
            
            if result == 0:
                # 新增description欄位
                db.session.execute(text(
                    "ALTER TABLE projects ADD COLUMN description TEXT"
                ))
                print("✅ 成功新增description欄位")
            else:
                print("✅ description欄位已存在")
            
            # 檢查project_code欄位是否已存在
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM pragma_table_info('projects') WHERE name='project_code'"
            )).scalar()
            
            if result == 0:
                # 新增project_code欄位（用於簡短代碼）
                db.session.execute(text(
                    "ALTER TABLE projects ADD COLUMN project_code VARCHAR(20)"
                ))
                print("✅ 成功新增project_code欄位")
            else:
                print("✅ project_code欄位已存在")
            
            db.session.commit()
            print("✅ 專案模型增強完成")
            
        except Exception as e:
            print(f"❌ 錯誤: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    enhance_project_model()