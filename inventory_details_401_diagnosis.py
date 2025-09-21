#!/usr/bin/env python3
"""
库存详情页面401认证错误诊断脚本
用于诊断和修复库存管理物料详情页面的认证问题
"""

import requests
import json
import urllib.parse
from datetime import datetime

# API基础配置
BASE_URL = "http://localhost:5000"
FRONTEND_PORT = 5174

def print_section(title):
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")

def test_login():
    """测试登录并获取token"""
    print_section("测试登录获取Token")
    
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        print(f"登录请求状态码: {response.status_code}")
        print(f"响应内容: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token') or data.get('token')
            if token:
                print(f"✅ 登录成功，获取到token: {token[:50]}...")
                return token
            else:
                print("❌ 登录成功但未获取到token")
                print(f"响应数据键: {list(data.keys())}")
                return None
        else:
            print(f"❌ 登录失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 登录请求异常: {str(e)}")
        return None

def test_inventory_list(token):
    """测试库存列表API"""
    print_section("测试库存列表API")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/inventory/items", headers=headers)
        print(f"库存列表请求状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 库存列表获取成功，数量: {len(data)}")
            
            # 显示前几个物料
            for i, item in enumerate(data[:3]):
                print(f"  物料{i+1}: {item.get('item_name')} | Key: {item.get('item_key')}")
                
            return data
        else:
            print(f"❌ 库存列表获取失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ 库存列表请求异常: {str(e)}")
        return []

def test_url_encoding():
    """测试URL编码问题"""
    print_section("测试URL编码处理")
    
    test_item_key = "test2成本|test2成本"
    
    print(f"原始item_key: {test_item_key}")
    
    # 测试不同的编码方式
    encodings = {
        "urllib.parse.quote": urllib.parse.quote(test_item_key),
        "urllib.parse.quote_plus": urllib.parse.quote_plus(test_item_key),
        "encodeURIComponent (JS等效)": urllib.parse.quote(test_item_key, safe='')
    }
    
    for method, encoded in encodings.items():
        print(f"  {method}: {encoded}")
        
    return encodings

def test_inventory_details_with_encodings(token, test_encodings):
    """测试不同编码方式的库存详情API"""
    print_section("测试库存详情API（不同编码方式）")
    
    headers = {"Authorization": f"Bearer {token}"}
    test_item_key = "test2成本|test2成本"
    
    for method, encoded_key in test_encodings.items():
        print(f"\n测试编码方式: {method}")
        print(f"编码后的key: {encoded_key}")
        
        try:
            url = f"{BASE_URL}/api/v1/inventory/items/{encoded_key}/details"
            print(f"请求URL: {url}")
            
            response = requests.get(url, headers=headers)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ 请求成功！")
                data = response.json()
                print(f"物料名称: {data.get('item_name')}")
                print(f"总数量: {data.get('total_quantity')}")
                return True
            elif response.status_code == 401:
                print("❌ 401认证错误")
                print(f"响应内容: {response.text}")
            elif response.status_code == 404:
                print("⚠️ 404未找到物料")
            else:
                print(f"❌ 其他错误，状态码: {response.status_code}")
                print(f"响应内容: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
    
    return False

def test_auth_header_variations(token):
    """测试不同的认证头格式"""
    print_section("测试认证头格式变化")
    
    test_url = f"{BASE_URL}/api/v1/inventory/items"
    
    auth_variations = {
        "Bearer {token}": f"Bearer {token}",
        "bearer {token} (小写)": f"bearer {token}",
        "{token} (无Bearer前缀)": token,
        "JWT {token}": f"JWT {token}"
    }
    
    for desc, auth_value in auth_variations.items():
        print(f"\n测试认证头: {desc}")
        headers = {"Authorization": auth_value}
        
        try:
            response = requests.get(test_url, headers=headers)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ 认证成功")
            elif response.status_code == 401:
                print("❌ 401认证错误")
            else:
                print(f"❌ 其他错误: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")

def test_direct_backend_vs_frontend():
    """测试直接后端访问 vs 前端代理"""
    print_section("测试访问路径差异")
    
    print("前端访问的URL模拟:")
    print(f"http://localhost:{FRONTEND_PORT}/api/v1/inventory/items/test2%E6%88%90%E6%9C%AC%7Ctest2%E6%88%90%E6%9C%AC/details")
    
    print("\n直接后端访问的URL:")
    print(f"{BASE_URL}/api/v1/inventory/items/test2%E6%88%90%E6%9C%AC%7Ctest2%E6%88%90%E6%9C%AC/details")
    
    print("\n可能的问题:")
    print("1. 前端的请求可能通过代理转发到后端")
    print("2. 代理过程中认证头可能被丢失")
    print("3. URL编码在代理过程中可能被重新编码")

def create_test_data():
    """创建测试数据"""
    print_section("检查测试数据")
    
    # 这里可以检查数据库中是否存在测试数据
    print("建议检查数据库中是否存在以下测试数据:")
    print("- 物料名称: test2成本")
    print("- 规格: test2成本")
    print("- 对应的inventory_batches记录")

def main():
    """主函数"""
    print("库存详情页面401认证错误诊断")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 测试登录
    token = test_login()
    if not token:
        print("无法获取认证token，停止后续测试")
        return
    
    # 2. 测试库存列表（验证认证基础功能）
    inventory_items = test_inventory_list(token)
    
    # 3. 测试URL编码
    encodings = test_url_encoding()
    
    # 4. 测试库存详情API
    test_inventory_details_with_encodings(token, encodings)
    
    # 5. 测试认证头格式
    test_auth_header_variations(token)
    
    # 6. 分析访问路径差异
    test_direct_backend_vs_frontend()
    
    # 7. 检查测试数据
    create_test_data()
    
    # 8. 总结和建议
    print_section("诊断总结和修复建议")
    print("1. 检查前端Vue组件中的API调用是否正确传递Authorization头")
    print("2. 确认Vite开发服务器的代理配置是否正确转发认证头")
    print("3. 验证URL编码处理，特别是中文字符的处理")
    print("4. 检查后端路由装饰器和认证中间件配置")
    print("5. 确认数据库中存在对应的测试数据")

if __name__ == "__main__":
    main()