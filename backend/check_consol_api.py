#!/usr/bin/env python
"""測試集運單 API 回傳資料"""
import requests
import json
from datetime import datetime

# API endpoint
base_url = "http://localhost:5000"
login_url = f"{base_url}/api/v1/auth/login"

# Login first to get token
login_data = {
    "username": "harry123180",
    "password": "password123"
}

print("1. 登入系統...")
login_response = requests.post(login_url, json=login_data)
if login_response.status_code != 200:
    print(f"登入失敗: {login_response.text}")
    exit(1)

response_json = login_response.json()
if 'data' in response_json:
    token = response_json['data']['access_token']
else:
    token = response_json.get('access_token', response_json.get('token', None))

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
print("✓ 登入成功")

# 測試集運單列表 API
print("\n2. 取得集運單列表...")
response = requests.get(
    f"{base_url}/api/v1/delivery/consolidation-list",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    consolidations = data.get('data', [])
    print(f"找到 {len(consolidations)} 個集運單")

    for consol in consolidations:
        print(f"\n=== 集運單: {consol['consolidation_id']} ===")
        print(f"名稱: {consol['consolidation_name']}")
        print(f"狀態: {consol['logistics_status']}")
        print(f"PO數量: {consol.get('po_count', 0)}")
        print(f"採購單列表: {len(consol.get('purchase_orders', []))} 筆")

        if consol.get('purchase_orders'):
            print("關聯的採購單:")
            for po in consol['purchase_orders']:
                print(f"  - {po['purchase_order_no']}: {po['supplier_name']}")
        else:
            print("  ❌ purchase_orders 欄位是空的!")

        # 測試詳情 API
        print(f"\n3. 取得集運單詳情 ({consol['consolidation_id']})...")
        detail_response = requests.get(
            f"{base_url}/api/v1/delivery/consolidation/{consol['consolidation_id']}",
            headers=headers
        )

        if detail_response.status_code == 200:
            details = detail_response.json()['data']
            print(f"詳情 API 回傳:")
            print(f"  PO數量: {details.get('po_count', 0)}")
            print(f"  總項目: {details.get('total_items', 0)}")
            print(f"  採購單數: {len(details.get('purchase_orders', []))}")

            if details.get('purchase_orders'):
                print("  採購單:")
                for po in details['purchase_orders']:
                    print(f"    - {po['purchase_order_no']}: {po['supplier_name']}")
                    print(f"      項目數: {po.get('item_count', 0)}")
            else:
                print("    ❌ 詳情 API 也沒有採購單!")
        else:
            print(f"取得詳情失敗: {detail_response.status_code}")
            print(detail_response.text)
else:
    print(f"取得列表失敗: {response.status_code}")
    print(response.text)