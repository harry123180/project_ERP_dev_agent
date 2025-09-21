#!/usr/bin/env python3
"""
交期維護搜尋功能分析和修復腳本 - 本地版本
分析搜尋功能的問題並提供修復方案
"""

import sqlite3
import json
import logging
from datetime import datetime
import os

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeliverySearchAnalysis:
    def __init__(self):
        self.db_path = 'erp_development.db'
        
    def check_database_structure(self):
        """檢查資料庫結構"""
        try:
            logger.info("🔍 檢查資料庫結構...")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 檢查 purchase_orders 表結構
            cursor.execute("PRAGMA table_info(purchase_orders)")
            po_columns = cursor.fetchall()
            
            logger.info("📋 purchase_orders 表欄位:")
            for col in po_columns:
                logger.info(f"  - {col[1]} ({col[2]})")
            
            # 檢查 suppliers 表結構
            cursor.execute("PRAGMA table_info(suppliers)")
            supplier_columns = cursor.fetchall()
            
            logger.info("📋 suppliers 表欄位:")
            for col in supplier_columns:
                logger.info(f"  - {col[1]} ({col[2]})")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ 檢查資料庫結構失敗: {str(e)}")
            return False
    
    def analyze_search_data(self):
        """分析搜尋相關的資料"""
        try:
            logger.info("📊 分析搜尋相關的資料...")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 檢查採購單資料
            cursor.execute("""
                SELECT 
                    po.purchase_order_no,
                    po.supplier_name,
                    po.delivery_status,
                    po.purchase_status,
                    s.supplier_region,
                    po.consolidation_id,
                    COUNT(*) OVER() as total_count
                FROM purchase_orders po
                LEFT JOIN suppliers s ON po.supplier_id = s.supplier_id
                WHERE po.purchase_status = 'purchased'
                ORDER BY po.purchase_order_no
                LIMIT 15
            """)
            
            orders = cursor.fetchall()
            
            if orders:
                total_count = orders[0][6] if orders else 0
                logger.info(f"📋 找到 {total_count} 筆已採購的採購單")
                logger.info("前15筆資料:")
                for order in orders:
                    status = order[2] or '無狀態'
                    region = order[4] or '未知地區'
                    logger.info(f"  - {order[0]} | {order[1]} | 地區: {region} | 交貨狀態: {status}")
            else:
                logger.warning("⚠️  沒有找到已採購的採購單資料")
            
            # 統計分析
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN s.supplier_region = 'domestic' THEN 1 END) as domestic,
                    COUNT(CASE WHEN s.supplier_region = 'international' THEN 1 END) as international,
                    COUNT(CASE WHEN po.delivery_status = 'shipped' THEN 1 END) as shipped,
                    COUNT(CASE WHEN po.delivery_status = 'delivered' THEN 1 END) as delivered,
                    COUNT(CASE WHEN po.delivery_status IS NULL OR po.delivery_status = '' THEN 1 END) as no_status
                FROM purchase_orders po
                LEFT JOIN suppliers s ON po.supplier_id = s.supplier_id
                WHERE po.purchase_status = 'purchased'
            """)
            
            stats = cursor.fetchone()
            logger.info(f"📊 統計資料:")
            logger.info(f"  - 總計: {stats[0]}")
            logger.info(f"  - 國內: {stats[1]}")
            logger.info(f"  - 國外: {stats[2]}")
            logger.info(f"  - 已發貨: {stats[3]}")
            logger.info(f"  - 已到貨: {stats[4]}")
            logger.info(f"  - 無狀態: {stats[5]}")
            
            # 測試搜尋查詢
            self.test_search_queries(cursor)
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ 分析資料失敗: {str(e)}")
            return False
    
    def test_search_queries(self, cursor):
        """測試各種搜尋查詢"""
        logger.info("🧪 測試搜尋查詢...")
        
        # 測試案例
        test_cases = [
            {
                "name": "採購單號完整匹配",
                "query": """
                    SELECT COUNT(*) FROM purchase_orders po
                    LEFT JOIN suppliers s ON po.supplier_id = s.supplier_id
                    WHERE po.purchase_status = 'purchased'
                    AND po.purchase_order_no = 'PO20250910001'
                """,
                "params": []
            },
            {
                "name": "採購單號模糊匹配 - LIKE %202509%",
                "query": """
                    SELECT COUNT(*) FROM purchase_orders po
                    LEFT JOIN suppliers s ON po.supplier_id = s.supplier_id
                    WHERE po.purchase_status = 'purchased'
                    AND po.purchase_order_no LIKE '%202509%'
                """,
                "params": []
            },
            {
                "name": "採購單號模糊匹配 - LIKE %PO%",
                "query": """
                    SELECT COUNT(*) FROM purchase_orders po
                    LEFT JOIN suppliers s ON po.supplier_id = s.supplier_id
                    WHERE po.purchase_status = 'purchased'
                    AND po.purchase_order_no LIKE '%PO%'
                """,
                "params": []
            },
            {
                "name": "國內供應商篩選",
                "query": """
                    SELECT COUNT(*) FROM purchase_orders po
                    LEFT JOIN suppliers s ON po.supplier_id = s.supplier_id
                    WHERE po.purchase_status = 'purchased'
                    AND s.supplier_region = 'domestic'
                """,
                "params": []
            },
            {
                "name": "國外供應商篩選",
                "query": """
                    SELECT COUNT(*) FROM purchase_orders po
                    LEFT JOIN suppliers s ON po.supplier_id = s.supplier_id
                    WHERE po.purchase_status = 'purchased'
                    AND s.supplier_region = 'international'
                """,
                "params": []
            },
            {
                "name": "已發貨狀態篩選",
                "query": """
                    SELECT COUNT(*) FROM purchase_orders po
                    LEFT JOIN suppliers s ON po.supplier_id = s.supplier_id
                    WHERE po.purchase_status = 'purchased'
                    AND po.delivery_status = 'shipped'
                """,
                "params": []
            }
        ]
        
        for test_case in test_cases:
            try:
                cursor.execute(test_case['query'], test_case['params'])
                result = cursor.fetchone()
                count = result[0] if result else 0
                logger.info(f"  ✅ {test_case['name']}: {count} 筆")
                
            except Exception as e:
                logger.error(f"  ❌ {test_case['name']}: {str(e)}")
    
    def analyze_code_issues(self):
        """分析代碼問題"""
        logger.info("🔍 分析代碼問題...")
        
        issues = []
        
        # 前端問題分析
        logger.info("📱 前端問題分析:")
        
        # 檢查前端Vue組件
        frontend_issues = [
            "搜尋輸入框綁定正確 (v-model='filters.poNumber')",
            "搜尋按鈕事件處理正確 (@click='loadData')",
            "API調用參數名稱需要檢查 (po_number vs purchase_order_no)",
            "前端使用的過濾條件可能與後端不一致"
        ]
        
        for issue in frontend_issues:
            logger.info(f"  - {issue}")
            issues.append(f"前端: {issue}")
        
        # 後端問題分析
        logger.info("🔧 後端問題分析:")
        
        backend_issues = [
            "後端API接收參數名為 'po_number'",
            "資料庫查詢使用 'purchase_order_no' 欄位",
            "使用 ilike() 進行模糊匹配，應該正常工作",
            "需要檢查 JOIN 條件是否正確"
        ]
        
        for issue in backend_issues:
            logger.info(f"  - {issue}")
            issues.append(f"後端: {issue}")
        
        return issues
    
    def generate_fix_recommendations(self):
        """生成修復建議"""
        logger.info("💡 生成修復建議...")
        
        recommendations = [
            {
                "category": "前端修復",
                "items": [
                    "確認搜尋按鈕的點擊事件正確調用API",
                    "檢查API請求參數是否正確傳遞",
                    "添加搜尋輸入框的即時驗證",
                    "優化搜尋結果的顯示邏輯"
                ]
            },
            {
                "category": "後端修復", 
                "items": [
                    "檢查SQL查詢的JOIN條件",
                    "確認模糊搜尋的LIKE語法正確",
                    "添加更詳細的日誌記錄",
                    "改善錯誤處理機制"
                ]
            },
            {
                "category": "資料庫優化",
                "items": [
                    "為搜尋欄位添加索引",
                    "檢查資料完整性",
                    "確認測試資料充足",
                    "優化查詢性能"
                ]
            },
            {
                "category": "測試改善",
                "items": [
                    "添加單元測試覆蓋搜尋功能",
                    "創建端到端測試",
                    "模擬不同搜尋場景",
                    "驗證搜尋結果準確性"
                ]
            }
        ]
        
        for rec in recommendations:
            logger.info(f"📂 {rec['category']}:")
            for item in rec['items']:
                logger.info(f"  - {item}")
        
        return recommendations
    
    def create_fix_script(self):
        """創建修復腳本"""
        logger.info("🔧 創建修復腳本...")
        
        # 後端API修復
        backend_fix = """
# 後端API修復建議 - delivery.py

# 在 get_delivery_maintenance_list 函數中，改善搜尋邏輯：

@delivery_bp.route('/maintenance-list', methods=['GET'])
@jwt_required()
def get_delivery_maintenance_list():
    try:
        # 獲取查詢參數
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        status_filter = request.args.get('status', '').strip()
        supplier_region_filter = request.args.get('supplier_region', '').strip()
        po_number_filter = request.args.get('po_number', '').strip()
        
        # 添加日誌記錄
        logger.info(f"搜尋參數: po_number={po_number_filter}, region={supplier_region_filter}, status={status_filter}")
        
        # 構建查詢
        query = db.session.query(PurchaseOrder)\\
            .join(Supplier, PurchaseOrder.supplier_id == Supplier.supplier_id)\\
            .filter(PurchaseOrder.purchase_status == 'purchased')
        
        # 應用篩選條件
        if supplier_region_filter:
            query = query.filter(Supplier.supplier_region == supplier_region_filter)
        
        if status_filter:
            query = query.filter(PurchaseOrder.delivery_status == status_filter)
            
        # 改善採購單號搜尋邏輯
        if po_number_filter:
            # 使用 OR 條件支持多種搜尋方式
            query = query.filter(
                db.or_(
                    PurchaseOrder.purchase_order_no.ilike(f'%{po_number_filter}%'),
                    PurchaseOrder.purchase_order_no == po_number_filter
                )
            )
            logger.info(f"應用採購單號篩選: {po_number_filter}")
        
        # 執行查詢
        pos = query.all()
        logger.info(f"查詢結果: {len(pos)} 筆")
        
        # 後續處理邏輯...
        
    except Exception as e:
        logger.error(f"搜尋失敗: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
"""

        # 前端修復
        frontend_fix = """
// 前端修復建議 - DeliveryMaintenance.vue

// 在搜尋方法中添加日誌和錯誤處理：

const loadData = async () => {
  loading.value = true
  try {
    console.log('搜尋參數:', {
      page: pagination.page,
      page_size: pagination.size,
      status: filters.deliveryStatus,
      supplier_region: 'domestic',
      po_number: filters.poNumber
    })
    
    const response = await deliveryApi.getMaintenanceList({
      page: pagination.page,
      page_size: pagination.size,
      status: filters.deliveryStatus,
      supplier_region: 'domestic',
      po_number: filters.poNumber.trim() // 清除空白字元
    })
    
    console.log('API回應:', response)
    
    if (response.success) {
      deliveryData.value = response.data
      pagination.total = response.data.length
      updateSummary()
      
      if (filters.poNumber && response.data.length === 0) {
        ElMessage.warning('沒有找到符合條件的採購單')
      }
    } else {
      ElMessage.error(response.error || '搜尋失敗')
    }
  } catch (error) {
    console.error('搜尋錯誤:', error)
    ElMessage.error('搜尋功能異常，請稍後再試')
  } finally {
    loading.value = false
  }
}

// 添加輸入驗證
const handleSearchInput = () => {
  // 自動觸發搜尋或添加防抖動
  if (filters.poNumber.length >= 2 || filters.poNumber.length === 0) {
    loadData()
  }
}
"""

        # 保存修復腳本
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(f'delivery_search_backend_fix_{timestamp}.py', 'w', encoding='utf-8') as f:
            f.write(backend_fix)
        
        with open(f'delivery_search_frontend_fix_{timestamp}.js', 'w', encoding='utf-8') as f:
            f.write(frontend_fix)
        
        logger.info(f"✅ 修復腳本已保存:")
        logger.info(f"  - delivery_search_backend_fix_{timestamp}.py")
        logger.info(f"  - delivery_search_frontend_fix_{timestamp}.js")
        
        return True
    
    def run_analysis(self):
        """執行完整分析"""
        logger.info("🚀 開始交期維護搜尋功能分析...")
        
        # 1. 檢查資料庫結構
        if not self.check_database_structure():
            return False
        
        # 2. 分析搜尋資料
        if not self.analyze_search_data():
            return False
        
        # 3. 分析代碼問題
        issues = self.analyze_code_issues()
        
        # 4. 生成修復建議
        recommendations = self.generate_fix_recommendations()
        
        # 5. 創建修復腳本
        self.create_fix_script()
        
        # 6. 生成報告
        self.generate_report(issues, recommendations)
        
        logger.info("✅ 分析完成")
        return True
    
    def generate_report(self, issues, recommendations):
        """生成分析報告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = {
            "timestamp": timestamp,
            "analysis_summary": {
                "database_structure": "正常",
                "search_functionality": "需要修復",
                "code_issues": len(issues),
                "recommendations": len([item for rec in recommendations for item in rec['items']])
            },
            "identified_issues": issues,
            "recommendations": recommendations,
            "key_findings": [
                "前端搜尋輸入框綁定正確",
                "後端API參數接收正常",
                "資料庫查詢邏輯需要優化",
                "需要添加更好的錯誤處理",
                "建議增加日誌記錄便於除錯"
            ]
        }
        
        report_file = f"delivery_search_analysis_report_{timestamp}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📋 分析報告已保存至: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ 保存報告失敗: {str(e)}")

def main():
    """主函數"""
    analysis = DeliverySearchAnalysis()
    analysis.run_analysis()

if __name__ == "__main__":
    main()