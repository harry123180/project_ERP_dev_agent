#!/usr/bin/env python
"""檢查集運單中的物品數量計算"""
import requests
import json

# 登入
login_url = 'http://localhost:5000/api/v1/auth/login'
login_data = {'username': 'harry123180', 'password': 'password123'}
login_resp = requests.post(login_url, json=login_data)

if login_resp.status_code != 200:
    print(f"登入失敗: {login_resp.status_code}")
    print(login_resp.text)
    exit(1)

token = login_resp.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

# 獲取集運單列表
consol_url = 'http://localhost:5000/api/v1/delivery/consolidation-list'
resp = requests.get(consol_url, headers=headers)

print(f"API 狀態碼: {resp.status_code}")
print(f"API 回應內容前500字: {resp.text[:500]}")

try:
    data = resp.json()
except json.JSONDecodeError:
    print("無法解析 JSON 回應")
    exit(1)

print('=== API 返回的集運單資料結構 ===')
if data.get('success') and data.get('data'):
    for consol in data['data'][:2]:  # 只顯示前2個
        print(f"\n集運單: {consol.get('consolidation_id')}")
        print(f"  po_count: {consol.get('po_count')}")
        print(f"  total_items: {consol.get('total_items')}")
        print(f"  purchase_orders 結構:")
        if consol.get('purchase_orders'):
            for po in consol['purchase_orders']:
                print(f"    - PO: {po.get('purchase_order_no')}")
                print(f"      item_count: {po.get('item_count')}")
                print(f"      items_count: {po.get('items_count')}")
                print(f"      所有欄位: {list(po.keys())}")
        else:
            print("    無採購單資料")