#!/usr/bin/env python
"""
建立簡單的採購單供查看歷史記錄
"""

from app import create_app, db
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from datetime import datetime, timedelta
import random

def create_simple_purchase_orders():
    """為SUP001供應商建立多筆採購單"""
    app = create_app()
    
    with app.app_context():
        try:
            # 使用台積電材料供應商
            supplier_id = 'SUP001'
            supplier_name = '台積電材料供應商'
            
            print(f'\n📋 為 {supplier_name} ({supplier_id}) 建立採購單歷史記錄')
            print('=' * 70)
            
            created_orders = []
            
            # 建立5筆不同時間和狀態的採購單
            order_configs = [
                {'days_ago': 60, 'status': 'shipped', 'items': 3, 'total': 850000},
                {'days_ago': 45, 'status': 'shipped', 'items': 2, 'total': 620000},
                {'days_ago': 30, 'status': 'purchased', 'items': 4, 'total': 1200000},
                {'days_ago': 15, 'status': 'purchased', 'items': 3, 'total': 980000},
                {'days_ago': 5, 'status': 'order_created', 'items': 2, 'total': 450000},
            ]
            
            for idx, config in enumerate(order_configs, 1):
                po_no = f'PO{datetime.now().strftime("%Y%m%d%H%M%S")}SUP001{idx:03d}'
                order_date = datetime.now() - timedelta(days=config['days_ago'])
                
                # 建立採購單
                po = PurchaseOrder(
                    purchase_order_no=po_no,
                    supplier_id=supplier_id,
                    supplier_name=supplier_name,
                    supplier_address='新竹科學園區創新路1號',
                    contact_phone='03-5678900',
                    contact_person='王經理',
                    order_date=order_date.date(),
                    expected_delivery_date=(order_date + timedelta(days=14)).date(),
                    purchase_status=config['status'],
                    subtotal_int=config['total'],
                    tax_decimal1=0.05,
                    grand_total_int=int(config['total'] * 1.05),
                    payment_method='monthly',
                    creator_id='admin',
                    created_at=order_date,
                    updated_at=datetime.now()
                )
                
                # 設定交貨狀態
                if config['status'] == 'shipped':
                    po.delivery_status = 'delivered'
                    po.shipping_status = 'arrived'
                elif config['status'] == 'purchased':
                    po.delivery_status = 'in_transit'
                    po.shipping_status = 'expected_arrival'
                else:
                    po.delivery_status = 'pending'
                    po.shipping_status = 'none'
                
                db.session.add(po)
                
                # 建立採購明細
                item_names = [
                    '晶圓材料', '光阻材料', '清洗液', '蝕刻液', 
                    '封裝材料', '測試探針', '化學品', '耗材'
                ]
                
                for j in range(config['items']):
                    item = PurchaseOrderItem(
                        purchase_order_no=po_no,
                        item_name=random.choice(item_names) + f'-{j+1}',
                        item_quantity=random.randint(10, 100),
                        item_unit=random.choice(['片', '公升', '個', '盒']),
                        unit_price=random.randint(1000, 10000),
                        item_specification=f'規格{j+1}',
                        item_model=f'MODEL-{random.randint(1000, 9999)}',
                        line_status=config['status'] if config['status'] != 'order_created' else 'order_created'
                    )
                    db.session.add(item)
                
                created_orders.append({
                    'po_no': po_no,
                    'date': order_date.strftime('%Y-%m-%d'),
                    'status': config['status'],
                    'amount': config['total']
                })
                
                print(f'✅ 建立採購單 {po_no} - {order_date.strftime("%Y-%m-%d")} - {config["status"]}')
            
            db.session.commit()
            
            print('\n' + '=' * 70)
            print('📊 採購單建立完成！')
            print(f'\n供應商: {supplier_name} ({supplier_id})')
            print(f'建立採購單數: {len(created_orders)}')
            print('\n採購單列表:')
            for order in created_orders:
                print(f'  • {order["po_no"]} | {order["date"]} | {order["status"]} | NT$ {order["amount"]:,}')
            
            print('\n🔍 現在您可以:')
            print(f'  1. 前往供應商列表頁面: http://localhost:5174/suppliers')
            print(f'  2. 找到 "{supplier_name}" 並點擊 "採購單" 按鈕')
            print(f'  3. 查看該供應商的所有歷史採購記錄')
            print(f'\n  或直接訪問: http://localhost:5174/suppliers/{supplier_id}/purchase-orders')
            
        except Exception as e:
            db.session.rollback()
            print(f'\n❌ 錯誤: {str(e)}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    create_simple_purchase_orders()