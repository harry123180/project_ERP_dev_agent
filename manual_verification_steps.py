#!/usr/bin/env python3
"""
手動驗證 REQ20250909018 狀態修復成功
================================

這個腳本示範如何驗證請購單狀態已正確修復
"""

import requests
import json

BASE_URL = 'http://localhost:5000'
API_BASE = f'{BASE_URL}/api/v1'

def verify_req_status(req_no='REQ20250909018'):
    """驗證特定請購單的狀態"""
    
    # 1. 獲取登入 token
    print(f"=== 驗證 {req_no} 狀態修復 ===")
    
    login_response = requests.post(f'{API_BASE}/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    
    if login_response.status_code != 200:
        print(f"❌ 登入失敗: {login_response.text}")
        return False
    
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # 2. 檢查請購單狀態
    req_response = requests.get(f'{API_BASE}/requisitions/{req_no}', headers=headers)
    
    if req_response.status_code != 200:
        print(f"❌ 無法獲取請購單資料: {req_response.text}")
        return False
    
    req_data = req_response.json()
    status = req_data['order_status']
    summary = req_data.get('summary', {})
    
    print(f"請購單編號: {req_no}")
    print(f"當前狀態: {status}")
    print(f"項目摘要: {summary}")
    
    # 3. 驗證狀態是否正確
    if status == 'reviewed' and summary.get('pending_items', -1) == 0:
        print("✅ 狀態修復成功！請購單現在正確顯示為 '已審核'")
        return True
    else:
        print(f"❌ 狀態仍然不正確 - 狀態: {status}, 待審核項目: {summary.get('pending_items', 'N/A')}")
        return False

def check_all_fixed_requisitions():
    """檢查所有修復的請購單狀態"""
    
    fixed_reqs = [
        'REQ20250909018',
        'REQ20250909022', 
        'REQ20250909024',
        'REQ20250909025',
        'REQ20250909026'
    ]
    
    print("=" * 60)
    print("檢查所有已修復的請購單狀態")
    print("=" * 60)
    
    success_count = 0
    for req_no in fixed_reqs:
        if verify_req_status(req_no):
            success_count += 1
        print()
    
    print(f"修復結果: {success_count}/{len(fixed_reqs)} 請購單狀態正確")
    
    if success_count == len(fixed_reqs):
        print("🎉 所有請購單都已成功修復！")
    else:
        print("⚠️ 部分請購單可能需要進一步檢查")

if __name__ == '__main__':
    # 首先檢查特定的 REQ20250909018
    verify_req_status('REQ20250909018')
    
    print("\n" + "=" * 60)
    
    # 然後檢查所有修復的請購單
    check_all_fixed_requisitions()