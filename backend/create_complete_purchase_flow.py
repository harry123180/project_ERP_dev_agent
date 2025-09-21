#!/usr/bin/env python
"""
建立完整的採購流程 - 從請購到驗收
"""

from app import create_app, db
from app.models.request_order import RequestOrder, RequestOrderItem
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.receiving import ReceivingRecord
from app.models.inventory import InventoryBatch, InventoryBatchStorage, InventoryMovement
from datetime import datetime, timedelta
import random

def create_complete_purchase_flow():
    """建立完整採購流程"""
    app = create_app()
    
    with app.app_context():
        try:
            # 1. 選擇供應商 - 使用台積電材料供應商
            supplier_id = 'SUP001'
            supplier_name = '台積電材料供應商'
            
            print(f'\n📋 開始建立完整採購流程 - 供應商: {supplier_name} ({supplier_id})')
            print('=' * 70)
            
            # 2. 建立請購單
            req_no = f'REQ{datetime.now().strftime("%Y%m%d%H%M%S")}'
            request_order = RequestOrder(
                request_order_no=req_no,
                requester_id=1,  # admin user
                requester_name='王經理',
                usage_type='project',  # 專案使用
                submit_date=datetime.now().date(),
                order_status='submitted',  # 已提交
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.session.add(request_order)
            
            # 建立請購明細
            items = [
                {'name': '晶圓材料A', 'spec': '12吋/300mm', 'quantity': 100, 'unit': '片', 'price': 5000},
                {'name': '光阻材料B', 'spec': 'ArF型/193nm', 'quantity': 50, 'unit': '公升', 'price': 8000},
                {'name': '清洗液C', 'spec': '電子級/高純度', 'quantity': 200, 'unit': '公升', 'price': 1500}
            ]
            
            for idx, item in enumerate(items, 1):
                detail = RequestOrderItem(
                    request_order_no=req_no,
                    item_name=item['name'],
                    item_specification=item['spec'],
                    item_quantity=item['quantity'],
                    item_unit=item['unit'],
                    item_description=f'{item["name"]} - 生產使用',
                    item_status='approved',  # 已核准
                    acceptance_status='pending_acceptance'
                )
                db.session.add(detail)
            
            db.session.flush()
            print(f'✅ 步驟 1: 建立請購單 {req_no}')
            
            # 3. 轉成採購單
            po_no = f'PO{datetime.now().strftime("%Y%m%d%H%M%S")}'
            purchase_order = PurchaseOrder(
                purchase_order_no=po_no,
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                supplier_address='新竹科學園區創新路1號',
                contact_phone='03-5678900',
                contact_person='王經理',
                order_date=datetime.now().date(),
                expected_delivery_date=(datetime.now() + timedelta(days=7)).date(),
                purchase_status='purchased',  # 已確認採購
                subtotal_int=sum(i['quantity'] * i['price'] for i in items),
                tax_decimal1=0.05,
                grand_total_int=int(sum(i['quantity'] * i['price'] for i in items) * 1.05),
                payment_method='monthly',
                creator_id='admin',
                confirm_purchaser_id='admin',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.session.add(purchase_order)
            
            # 建立採購單明細
            for item in items:
                po_item = PurchaseOrderItem(
                    purchase_order_no=po_no,
                    item_name=item['name'],
                    item_quantity=item['quantity'],
                    item_unit=item['unit'],
                    unit_price=item['price'],
                    item_specification=item['spec'],
                    item_model=f'MODEL-{random.randint(1000, 9999)}',
                    line_status='purchased'
                )
                db.session.add(po_item)
            
            db.session.flush()
            print(f'✅ 步驟 2: 建立採購單 {po_no}')
            
            # 4. 更新交期狀態 (模擬已出貨)
            purchase_order.purchase_status = 'shipped'
            purchase_order.delivery_status = 'in_transit'
            purchase_order.shipping_status = 'expected_arrival'
            purchase_order.eta_date = (datetime.now() + timedelta(days=3)).date()
            
            db.session.flush()
            print(f'✅ 步驟 3: 交期維護 - 狀態更新為已出貨')
            
            # 5. 執行收貨
            for item in items:
                receiving = ReceivingRecord(
                    purchase_order_no=po_no,
                    supplier_id=supplier_id,
                    item_name=item['name'],
                    item_specification=item['spec'],
                    ordered_quantity=item['quantity'],
                    receiving_quantity=item['quantity'],  # 全部收貨
                    unit=item['unit'],
                    receiving_date=datetime.now().date(),
                    receiver='倉管員',
                    receiving_status='completed',
                    inspection_status='pending',
                    storage_status='pending',
                    created_at=datetime.now()
                )
                db.session.add(receiving)
            
            db.session.flush()
            print(f'✅ 步驟 4: 收貨完成 - 收貨 {len(items)} 項物料')
            
            # 6. 建立庫存批次並入庫
            for item in items:
                # 建立庫存批次
                batch = InventoryBatch(
                    batch_no=f'BATCH{datetime.now().strftime("%Y%m%d%H%M%S")}{random.randint(100, 999)}',
                    item_name=item['name'],
                    item_specification=item['spec'],
                    quantity=item['quantity'],
                    unit=item['unit'],
                    source_type='purchase',
                    source_po_no=po_no,
                    supplier_id=supplier_id,
                    received_date=datetime.now().date(),
                    status='available',
                    created_at=datetime.now()
                )
                db.session.add(batch)
                db.session.flush()
                
                # 分配儲位
                storage = InventoryBatchStorage(
                    batch_id=batch.batch_id,
                    storage_code=f'A{random.randint(1, 9)}-{random.randint(1, 9)}-{random.randint(1, 9)}',
                    quantity=item['quantity'],
                    status='active',
                    stored_at=datetime.now()
                )
                db.session.add(storage)
                
                # 記錄入庫動作
                movement = InventoryMovement(
                    batch_id=batch.batch_id,
                    movement_type='in',
                    quantity=item['quantity'],
                    movement_date=datetime.now(),
                    from_location='收貨區',
                    to_location=storage.storage_code,
                    reason='採購入庫',
                    handler='倉管員',
                    reference_no=po_no
                )
                db.session.add(movement)
            
            db.session.flush()
            print(f'✅ 步驟 5: 入庫完成 - 建立 {len(items)} 個庫存批次')
            
            # 7. 執行驗收（這裡簡化處理，實際應有驗收記錄表）
            purchase_order.purchase_status = 'shipped'  # 保持已出貨狀態
            purchase_order.delivery_status = 'delivered'  # 更新為已交貨
            
            # 更新收貨記錄的檢驗狀態
            from sqlalchemy import text
            db.session.execute(text(
                f"UPDATE receiving_records SET inspection_status = 'passed', storage_status = 'completed' "
                f"WHERE purchase_order_no = '{po_no}'"
            ))
            
            db.session.commit()
            print(f'✅ 步驟 6: 驗收完成 - 所有物料驗收合格')
            
            print('\n' + '=' * 70)
            print('📊 完整採購流程建立成功！')
            print(f'\n詳細資訊:')
            print(f'  供應商: {supplier_name} ({supplier_id})')
            print(f'  請購單號: {req_no}')
            print(f'  採購單號: {po_no}')
            print(f'  採購金額: NT$ {purchase_order.grand_total_int:,}')
            print(f'  物料項目: {len(items)} 項')
            print(f'  當前狀態: 已完成驗收')
            
            print('\n🔍 您現在可以:')
            print(f'  1. 在供應商列表中查看 "{supplier_name}"')
            print(f'  2. 點擊供應商查看採購單歷史記錄')
            print(f'  3. 採購單號 {po_no} 包含完整流程記錄')
            
            return {
                'supplier_id': supplier_id,
                'supplier_name': supplier_name,
                'request_order_no': req_no,
                'purchase_order_no': po_no,
                'total_amount': purchase_order.grand_total_int
            }
            
        except Exception as e:
            db.session.rollback()
            print(f'\n❌ 錯誤: {str(e)}')
            import traceback
            traceback.print_exc()
            return None

if __name__ == '__main__':
    result = create_complete_purchase_flow()
    if result:
        print(f'\n✨ 流程建立完成！請前往供應商列表查看 {result["supplier_name"]} 的採購歷史')