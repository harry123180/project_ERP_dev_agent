#!/usr/bin/env python
"""快速檢查 API 健康狀態"""
import requests
import time

base_url = "http://localhost:5000"

print("檢查 API 健康狀態...")
print(f"目標: {base_url}")

# 1. 檢查服務是否運行
try:
    print("\n1. 檢查服務連線...")
    start_time = time.time()
    response = requests.get(base_url, timeout=5)
    elapsed = time.time() - start_time
    print(f"   ✓ 服務回應 (耗時: {elapsed:.2f}秒)")
    print(f"   狀態碼: {response.status_code}")
except requests.exceptions.Timeout:
    print("   ❌ 連線逾時 (5秒)")
    print("   請確認後端服務是否運行: python app.py")
    exit(1)
except requests.exceptions.ConnectionError as e:
    print(f"   ❌ 無法連線: {e}")
    print("   請確認後端服務是否運行: python app.py")
    exit(1)

# 2. 測試登入端點
try:
    print("\n2. 測試登入端點...")
    login_url = f"{base_url}/api/v1/auth/login"
    login_data = {
        "username": "harry123180",
        "password": "password123"
    }

    start_time = time.time()
    response = requests.post(login_url, json=login_data, timeout=10)
    elapsed = time.time() - start_time

    print(f"   ✓ 登入回應 (耗時: {elapsed:.2f}秒)")
    print(f"   狀態碼: {response.status_code}")

    if response.status_code == 200:
        print("   ✓ 登入成功")
    else:
        print(f"   ❌ 登入失敗: {response.text[:200]}")

except requests.exceptions.Timeout:
    print("   ❌ 登入請求逾時 (10秒)")
except Exception as e:
    print(f"   ❌ 登入錯誤: {e}")

print("\n完成健康檢查")