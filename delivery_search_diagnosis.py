#!/usr/bin/env python3
"""
交期維護頁面搜尋功能診斷和修復腳本

診斷問題：
1. 檢查前端搜尋輸入框的綁定和事件處理
2. 分析搜尋功能的篩選邏輯
3. 檢查API請求參數是否正確傳遞
4. 驗證後端API是否正確處理搜尋參數
5. 修復搜尋功能，確保能正確過濾採購單
"""

import requests
import json
import sqlite3
import logging
from datetime import datetime
import os

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeliverySearchDiagnosis:
    def __init__(self):
        self.base_url = "http://localhost:8002"
        self.token = None
        self.headers = {}
        
    def login(self):
        """登入並獲取token"""
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = requests.post(f"{self.base_url}/api/v1/auth/login", json=login_data)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.token = result.get('token')
                    self.headers = {
                        'Authorization': f'Bearer {self.token}',
                        'Content-Type': 'application/json'
                    }
                    logger.info("✅ 登入成功")
                    return True
            
            logger.error(f"❌ 登入失敗: {response.status_code} - {response.text}")
            return False
            
        except Exception as e:
            logger.error(f"❌ 登入異常: {str(e)}")
            return False
    
    def test_search_functionality(self):
        """測試搜尋功能"""
        logger.info("🔍 開始測試搜尋功能...")
        
        # 測試案例
        test_cases = [
            {
                "name": "無參數查詢",
                "params": {}
            },
            {
                "name": "採購單號搜尋 - 完整匹配",
                "params": {"po_number": "PO202509"}
            },
            {
                "name": "採購單號搜尋 - 部分匹配",
                "params": {"po_number": "202509"}
            },
            {
                "name": "國內供應商篩選",
                "params": {"supplier_region": "domestic"}
            },
            {
                "name": "國外供應商篩選",
                "params": {"supplier_region": "international"}
            },
            {
                "name": "已發貨狀態篩選",
                "params": {"status": "shipped"}
            },
            {
                "name": "綜合篩選",
                "params": {
                    "po_number": "PO",
                    "supplier_region": "domestic",
                    "status": "shipped"
                }
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            try:
                logger.info(f"🧪 測試: {test_case['name']}")
                
                response = requests.get(
                    f"{self.base_url}/api/v1/delivery/maintenance-list",
                    params=test_case['params'],
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        result_count = len(data.get('data', []))
                        logger.info(f"  ✅ 成功 - 找到 {result_count} 筆資料")
                        
                        results.append({
                            "test": test_case['name'],
                            "status": "success",
                            "count": result_count,
                            "data": data.get('data', [])[:3]  # 只取前3筆作為範例
                        })
                    else:
                        logger.error(f"  ❌ API返回錯誤: {data.get('error', 'Unknown error')}")
                        results.append({
                            "test": test_case['name'],
                            "status": "api_error",
                            "error": data.get('error', 'Unknown error')
                        })
                else:
                    logger.error(f"  ❌ HTTP錯誤: {response.status_code} - {response.text}")
                    results.append({
                        "test": test_case['name'],
                        "status": "http_error",
                        "status_code": response.status_code,
                        "response": response.text
                    })
                    
            except Exception as e:
                logger.error(f"  ❌ 測試異常: {str(e)}")
                results.append({
                    "test": test_case['name'],
                    "status": "exception",
                    "error": str(e)
                })
        
        return results
    
    def check_database_data(self):
        """檢查資料庫中的資料"""
        try:
            logger.info("📊 檢查資料庫資料...")
            
            conn = sqlite3.connect('erp_development.db')
            cursor = conn.cursor()
            
            # 檢查採購單資料
            cursor.execute("""
                SELECT 
                    po.purchase_order_no,
                    po.supplier_name,
                    po.delivery_status,
                    po.purchase_status,
                    s.supplier_region,
                    po.consolidation_id
                FROM purchase_orders po
                LEFT JOIN suppliers s ON po.supplier_id = s.supplier_id
                WHERE po.purchase_status = 'purchased'
                ORDER BY po.purchase_order_no
                LIMIT 10
            """)
            
            orders = cursor.fetchall()
            
            logger.info(f"📋 找到 {len(orders)} 筆採購單資料")
            for order in orders:
                logger.info(f"  - {order[0]} | {order[1]} | 地區: {order[4]} | 狀態: {order[2]}")
            
            # 檢查搜尋相關的統計
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN s.supplier_region = 'domestic' THEN 1 END) as domestic,
                    COUNT(CASE WHEN s.supplier_region = 'international' THEN 1 END) as international,
                    COUNT(CASE WHEN po.delivery_status = 'shipped' THEN 1 END) as shipped,
                    COUNT(CASE WHEN po.delivery_status IS NULL OR po.delivery_status = '' THEN 1 END) as no_status
                FROM purchase_orders po
                LEFT JOIN suppliers s ON po.supplier_id = s.supplier_id
                WHERE po.purchase_status = 'purchased'
            """)
            
            stats = cursor.fetchone()
            logger.info(f"📊 統計資料: 總計={stats[0]}, 國內={stats[1]}, 國外={stats[2]}, 已發貨={stats[3]}, 無狀態={stats[4]}")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ 檢查資料庫失敗: {str(e)}")
            return False
    
    def test_frontend_api_call(self):
        """模擬前端API調用"""
        logger.info("🎯 模擬前端API調用...")
        
        # 模擬前端的實際參數
        frontend_params = [
            {
                "name": "國內採購單搜尋 - 空值",
                "params": {
                    "page": 1,
                    "page_size": 20,
                    "status": "",
                    "supplier_region": "domestic",
                    "po_number": ""
                }
            },
            {
                "name": "國內採購單搜尋 - 有搜尋值",
                "params": {
                    "page": 1,
                    "page_size": 20,
                    "status": "",
                    "supplier_region": "domestic",
                    "po_number": "PO202509"
                }
            },
            {
                "name": "國外採購單搜尋",
                "params": {
                    "page": 1,
                    "page_size": 20,
                    "status": "",
                    "supplier_region": "international",
                    "po_number": ""
                }
            }
        ]
        
        for test in frontend_params:
            try:
                logger.info(f"🧪 {test['name']}")
                
                response = requests.get(
                    f"{self.base_url}/api/v1/delivery/maintenance-list",
                    params=test['params'],
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        count = len(data.get('data', []))
                        logger.info(f"  ✅ 成功 - {count} 筆資料")
                        
                        # 顯示前幾筆資料
                        for i, item in enumerate(data.get('data', [])[:3]):
                            logger.info(f"    {i+1}. {item['po_number']} - {item['supplier_name']} ({item['supplier_region']})")
                    else:
                        logger.error(f"  ❌ API錯誤: {data.get('error')}")
                else:
                    logger.error(f"  ❌ HTTP錯誤: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"  ❌ 異常: {str(e)}")
    
    def diagnose_and_fix(self):
        """診斷並嘗試修復問題"""
        logger.info("🔧 開始診斷和修復...")
        
        # 1. 登入
        if not self.login():
            return False
        
        # 2. 檢查資料庫資料
        self.check_database_data()
        
        # 3. 測試搜尋功能
        search_results = self.test_search_functionality()
        
        # 4. 模擬前端API調用
        self.test_frontend_api_call()
        
        # 5. 分析結果並提供修復建議
        self.analyze_results(search_results)
        
        return True
    
    def analyze_results(self, results):
        """分析測試結果並提供修復建議"""
        logger.info("📋 分析測試結果...")
        
        successful_tests = [r for r in results if r.get('status') == 'success']
        failed_tests = [r for r in results if r.get('status') != 'success']
        
        logger.info(f"✅ 成功測試: {len(successful_tests)}")
        logger.info(f"❌ 失敗測試: {len(failed_tests)}")
        
        if failed_tests:
            logger.info("🔍 問題分析:")
            for test in failed_tests:
                logger.info(f"  - {test['test']}: {test.get('error', test.get('status'))}")
        
        # 生成修復建議
        recommendations = self.generate_fix_recommendations(results)
        
        logger.info("💡 修復建議:")
        for rec in recommendations:
            logger.info(f"  {rec}")
        
        return recommendations
    
    def generate_fix_recommendations(self, results):
        """生成修復建議"""
        recommendations = []
        
        # 檢查是否有API連接問題
        http_errors = [r for r in results if r.get('status') == 'http_error']
        if http_errors:
            recommendations.append("🔧 檢查後端伺服器是否正常運行 (http://localhost:8002)")
        
        # 檢查是否有認證問題
        auth_errors = [r for r in results if r.get('status_code') == 401]
        if auth_errors:
            recommendations.append("🔧 檢查JWT token認證是否正確")
        
        # 檢查搜尋功能
        search_tests = [r for r in results if 'po_number' in r.get('test', '').lower()]
        if any(r.get('status') != 'success' for r in search_tests):
            recommendations.append("🔧 檢查後端API中的po_number過濾邏輯")
            recommendations.append("🔧 確認前端傳遞的參數名稱與後端期望的參數名稱一致")
        
        # 檢查資料問題
        zero_results = [r for r in results if r.get('count') == 0]
        if len(zero_results) > len(results) / 2:
            recommendations.append("🔧 檢查資料庫中是否有足夠的測試資料")
            recommendations.append("🔧 確認purchase_status = 'purchased'的條件是否正確")
        
        return recommendations

def main():
    """主函數"""
    logger.info("🚀 開始交期維護搜尋功能診斷...")
    
    diagnosis = DeliverySearchDiagnosis()
    success = diagnosis.diagnose_and_fix()
    
    if success:
        logger.info("✅ 診斷完成")
    else:
        logger.error("❌ 診斷失敗")
    
    # 保存診斷報告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"delivery_search_diagnosis_report_{timestamp}.json"
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "diagnosis_completed": success,
                "recommendations": [
                    "檢查前端Vue組件中的搜尋參數綁定",
                    "驗證API調用時的參數傳遞",
                    "檢查後端API的po_number過濾邏輯",
                    "確認資料庫查詢條件",
                    "測試前端搜尋按鈕的事件處理"
                ]
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📋 診斷報告已保存至: {report_file}")
        
    except Exception as e:
        logger.error(f"❌ 保存報告失敗: {str(e)}")

if __name__ == "__main__":
    main()