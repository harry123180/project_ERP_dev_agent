#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
提交請購單，使其可以被審核
"""

import requests
import json

def get_auth_token():
    """獲取認證token"""
    login_url = "http://localhost:5000/api/v1/auth/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            print(f"登入失敗: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"登入錯誤: {str(e)}")
        return None

def submit_requisition(token, req_no):
    """提交請購單"""
    url = f"http://localhost:5000/api/v1/requisitions/{req_no}/submit"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers)
        if response.status_code in [200, 204]:
            return True
        else:
            print(f"提交請購單 {req_no} 失敗: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"API調用錯誤: {str(e)}")
        return False

def main():
    """主函數"""
    print("正在獲取認證token...")
    token = get_auth_token()
    if not token:
        print("❌ 無法獲取認證token")
        return
    
    print("✅ 成功獲取認證token")
    
    # 需要提交的請購單編號（從API回應中獲取的draft狀態請購單）
    draft_requisitions = [
        "REQ20250908009",
        "REQ20250908008", 
        "REQ20250908007",
        "REQ20250908006",
        "REQ20250908005"
    ]
    
    submitted_count = 0
    for req_no in draft_requisitions:
        print(f"\n正在提交請購單: {req_no}")
        if submit_requisition(token, req_no):
            print(f"✅ 成功提交請購單: {req_no}")
            submitted_count += 1
        else:
            print(f"❌ 提交請購單失敗: {req_no}")
    
    print("\n" + "="*50)
    print(f"🎉 完成！成功提交了 {submitted_count}/{len(draft_requisitions)} 張請購單")
    print("="*50)
    
    if submitted_count > 0:
        print(f"\n現在有 {submitted_count + 1} 張請購單可以審核了！")  # +1 因為原來就有REQ20250908004
        print("請到 請購管理 > 請購單列表 查看和審核")
    else:
        print("\n請檢查請購單狀態或聯繫系統管理員")

if __name__ == "__main__":
    main()