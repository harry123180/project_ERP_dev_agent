#!/usr/bin/env python
"""
最終PostgreSQL驗證測試
"""
import os
import sys
import requests
import json

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
from app.models import User

print("="*70)
print("PostgreSQL最終驗證測試")
print("="*70)

# 創建Flask應用
app = create_app('development')

def test_database_connection():
    """測試資料庫連接"""
    print("\n1. 測試資料庫連接...")
    with app.app_context():
        try:
            # 執行簡單查詢
            result = db.session.execute("SELECT 1")
            print("   ✅ 資料庫連接成功")
            return True
        except Exception as e:
            print(f"   ❌ 資料庫連接失敗: {e}")
            return False

def test_user_authentication():
    """測試使用者認證"""
    print("\n2. 測試使用者認證...")
    with app.app_context():
        try:
            # 查詢管理員帳號
            admin = User.query.filter_by(username='admin').first()
            if admin:
                print(f"   ✅ 找到管理員帳號: {admin.chinese_name}")
                # 驗證密碼
                from werkzeug.security import check_password_hash
                if check_password_hash(admin.password, 'admin123'):
                    print("   ✅ 密碼驗證成功")
                    return True
                else:
                    print("   ⚠️ 密碼驗證失敗")
                    return False
            else:
                print("   ❌ 找不到管理員帳號")
                return False
        except Exception as e:
            print(f"   ❌ 認證測試失敗: {e}")
            return False

def test_data_statistics():
    """測試資料統計"""
    print("\n3. 資料統計...")
    with app.app_context():
        try:
            from app.models import User, Project, RequestOrder, PurchaseOrder

            stats = {
                '使用者': User.query.count(),
                '專案': Project.query.count(),
                '請購單': RequestOrder.query.count(),
                '採購單': PurchaseOrder.query.count()
            }

            total = 0
            for name, count in stats.items():
                if count > 0:
                    print(f"   ✅ {name}: {count} 筆")
                    total += count
                else:
                    print(f"   ⚠️ {name}: {count} 筆")

            return total > 0
        except Exception as e:
            print(f"   ❌ 統計失敗: {e}")
            return False

def test_api_login():
    """測試API登入"""
    print("\n4. 測試API登入...")

    # 啟動測試服務器
    with app.test_client() as client:
        try:
            # 發送登入請求
            response = client.post('/api/v1/auth/login',
                                 json={'username': 'admin', 'password': 'admin123'})

            if response.status_code == 200:
                data = response.get_json()
                if 'access_token' in data:
                    print("   ✅ API登入成功")
                    print(f"   Token: {data['access_token'][:50]}...")
                    return True
                else:
                    print(f"   ⚠️ 登入成功但沒有返回token")
                    return False
            else:
                print(f"   ❌ 登入失敗: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ API測試失敗: {e}")
            return False

def test_create_sample_data():
    """創建測試資料"""
    print("\n5. 創建測試資料...")
    with app.app_context():
        try:
            from app.models import Project
            from datetime import datetime

            # 檢查是否已有測試專案
            test_project = Project.query.filter_by(project_code='TEST001').first()
            if not test_project:
                test_project = Project(
                    project_name='PostgreSQL測試專案',
                    project_code='TEST001',
                    budget=1000000.0,
                    project_manager='admin',
                    start_date=datetime.now().date(),
                    status='進行中'
                )
                db.session.add(test_project)
                db.session.commit()
                print("   ✅ 創建測試專案成功")
            else:
                print("   ✅ 測試專案已存在")

            return True
        except Exception as e:
            print(f"   ❌ 創建測試資料失敗: {e}")
            db.session.rollback()
            return False

def main():
    print("\n開始執行測試...")

    results = []

    # 執行各項測試
    results.append(("資料庫連接", test_database_connection()))
    results.append(("使用者認證", test_user_authentication()))
    results.append(("資料統計", test_data_statistics()))
    results.append(("API登入", test_api_login()))
    results.append(("創建測試資料", test_create_sample_data()))

    # 總結
    print("\n" + "="*70)
    print("測試結果總結：")
    print("-"*70)

    success_count = 0
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {test_name:15} {status}")
        if result:
            success_count += 1

    print("-"*70)
    print(f"總計: {success_count}/{len(results)} 測試通過")

    if success_count == len(results):
        print("\n🎉 恭喜！PostgreSQL遷移完全成功！")
        print("\n使用以下資訊運行應用程式：")
        print("  資料庫: PostgreSQL")
        print("  主機: localhost:5432")
        print("  資料庫名: erp_database")
        print("  使用者: erp_user")
        print("  密碼: 271828")
        print("\n管理員帳號：")
        print("  使用者名: admin")
        print("  密碼: admin123")
    elif success_count > 0:
        print("\n⚠️ PostgreSQL部分功能正常，但仍有問題需要解決")
    else:
        print("\n❌ PostgreSQL配置有嚴重問題，請檢查設定")

    print("="*70)

    return success_count == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)