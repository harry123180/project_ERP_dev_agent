#!/usr/bin/env python
"""
創建完整的庫存管理流程測試數據
包含：採購單 -> 發貨 -> 收貨 -> 入庫 -> 查詢
"""

from datetime import datetime, timedelta
from decimal import Decimal
from app import create_app, db
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem  
from app.models.delivery import DeliveryManagement
from app.models.receiving import ReceivingRecord
from app.models.inventory import InventoryBatch, InventoryBatchStorage, InventoryMovement
from app.models.storage import Storage
from app.models.user import User
from app.models.supplier import Supplier

def create_test_data():
    """創建完整的測試數據"""
    app = create_app()
    
    with app.app_context():
        try:
            # 獲取或創建測試用戶
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("Error: Admin user not found")
                return
                
            # 獲取或創建供應商
            supplier = Supplier.query.filter_by(supplier_code='S001').first()
            if not supplier:
                supplier = Supplier(
                    supplier_code='S001',
                    supplier_name='測試供應商',
                    supplier_region='domestic',
                    contact_person='張三',
                    contact_phone='0912345678',
                    email='test@example.com'
                )
                db.session.add(supplier)
                db.session.commit()
                print("Created test supplier S001")
            
            # 創建測試採購單
            test_pos = [
                {
                    'po_number': 'PO202501010',
                    'items': [
                        {'name': '筆記型電腦', 'spec': 'ThinkPad T14 Gen3', 'qty': 5, 'unit': '台', 'price': 45000},
                        {'name': '無線滑鼠', 'spec': 'Logitech MX Master 3', 'qty': 10, 'unit': '個', 'price': 2500}
                    ]
                },
                {
                    'po_number': 'PO202501011', 
                    'items': [
                        {'name': 'A4影印紙', 'spec': '80磅 500張/包', 'qty': 100, 'unit': '包', 'price': 120},
                        {'name': '原子筆', 'spec': '0.5mm 藍色', 'qty': 200, 'unit': '支', 'price': 15}
                    ]
                },
                {
                    'po_number': 'PO202501012',
                    'items': [
                        {'name': '辦公椅', 'spec': '人體工學椅 黑色', 'qty': 8, 'unit': '張', 'price': 8500},
                        {'name': '辦公桌', 'spec': '160x80cm 白色', 'qty': 8, 'unit': '張', 'price': 12000}
                    ]
                }
            ]
            
            for po_data in test_pos:
                # 檢查採購單是否已存在
                existing_po = PurchaseOrder.query.filter_by(purchase_order_no=po_data['po_number']).first()
                if existing_po:
                    print(f"PO {po_data['po_number']} already exists, skipping...")
                    continue
                    
                # 創建採購單
                po = PurchaseOrder(
                    purchase_order_no=po_data['po_number'],
                    supplier_id=supplier.supplier_id,
                    order_date=datetime.now() - timedelta(days=7),
                    expected_delivery_date=datetime.now() + timedelta(days=3),
                    po_status='confirmed',
                    created_by=admin_user.user_id,
                    created_at=datetime.now() - timedelta(days=7)
                )
                db.session.add(po)
                db.session.flush()
                
                total_amount = 0
                # 創建採購單明細
                for idx, item in enumerate(po_data['items'], 1):
                    detail = PurchaseOrderItem(
                        purchase_order_id=po.purchase_order_id,
                        item_name=item['name'],
                        item_specification=item['spec'],
                        item_quantity=item['qty'],
                        item_unit=item['unit'],
                        unit_price=Decimal(str(item['price'])),
                        subtotal=Decimal(str(item['qty'] * item['price'])),
                        line_number=idx
                    )
                    total_amount += item['qty'] * item['price']
                    db.session.add(detail)
                
                po.total_amount = Decimal(str(total_amount))
                print(f"Created PO: {po_data['po_number']} with {len(po_data['items'])} items")
                
                # 創建發貨記錄 (DeliveryManagement)
                for detail in po.details:
                    delivery = DeliveryManagement(
                        requisition_number=f"REQ{po_data['po_number'][2:]}",  # 虛擬請購單號
                        purchase_order_number=po.purchase_order_no,
                        item_name=detail.item_name,
                        specification=detail.item_specification,
                        quantity=detail.item_quantity,
                        unit=detail.item_unit,
                        supplier_name=supplier.supplier_name,
                        supplier_region=supplier.supplier_region,
                        remarks='測試發貨',
                        shipped_date=datetime.now() - timedelta(days=2),
                        delivery_status='shipped'
                    )
                    db.session.add(delivery)
                    print(f"  - Created delivery record for {detail.item_name}")
            
            db.session.commit()
            print("\n=== 第一步：採購單和發貨記錄創建完成 ===\n")
            
            # 步驟2：執行收貨確認，創建庫存批次
            print("=== 第二步：執行收貨確認 ===")
            
            # 獲取所有已發貨的項目
            shipped_items = DeliveryManagement.query.filter_by(delivery_status='shipped').all()
            
            for item in shipped_items:
                # 創建收貨記錄
                receiving = ReceivingRecord(
                    purchase_order_no=item.purchase_order_number,
                    po_item_detail_id=None,  # 簡化處理
                    item_name=item.item_name,
                    item_specification=item.specification,
                    quantity_ordered=item.quantity,
                    quantity_received=item.quantity,  # 假設全部收貨
                    unit=item.unit,
                    received_at=datetime.now() - timedelta(days=1),
                    receiver_id=admin_user.user_id,
                    receiver_name=admin_user.full_name or admin_user.username,
                    receiving_status='received',
                    notes='測試收貨確認'
                )
                db.session.add(receiving)
                db.session.flush()
                
                # 創建庫存批次
                batch = InventoryBatch(
                    item_name=item.item_name,
                    item_specification=item.specification,
                    unit=item.unit,
                    source_type='PO',
                    source_po_number=item.purchase_order_number,
                    source_line_number=None,
                    original_quantity=item.quantity,
                    current_quantity=item.quantity,
                    batch_status='active',
                    received_date=(datetime.now() - timedelta(days=1)).date(),
                    receiver_id=admin_user.user_id,
                    receiver_name=admin_user.full_name or admin_user.username
                )
                db.session.add(batch)
                
                # 更新發貨狀態為已收貨
                item.delivery_status = 'received'
                
                print(f"  - Received: {item.item_name} x {item.quantity} {item.unit}")
            
            db.session.commit()
            print("\n=== 第二步：收貨確認完成，庫存批次已創建 ===\n")
            
            # 步驟3：分配儲位
            print("=== 第三步：分配儲位 ===")
            
            # 獲取或創建儲位
            storage_locations = []
            zones = ['Z1', 'Z2']
            shelves = ['A', 'B', 'C']
            floors = [1, 2, 3]
            
            for zone in zones:
                for shelf in shelves:
                    for floor in floors:
                        storage_id = f"{zone}-{shelf}-{floor}"
                        storage = Storage.query.filter_by(storage_id=storage_id).first()
                        if not storage:
                            storage = Storage(
                                storage_id=storage_id,
                                area_code=zone,
                                shelf_code=shelf,
                                floor_level=floor,
                                front_back_position=1,
                                left_middle_right_position=1,
                                storage_status='available',
                                created_at=datetime.now()
                            )
                            db.session.add(storage)
                        storage_locations.append(storage_id)
            
            db.session.commit()
            
            # 為每個批次分配儲位
            batches = InventoryBatch.query.filter_by(batch_status='active').all()
            
            for idx, batch in enumerate(batches):
                # 選擇一個儲位
                storage_id = storage_locations[idx % len(storage_locations)]
                
                # 分配批次到儲位
                batch_storage = InventoryBatchStorage(
                    batch_id=batch.batch_id,
                    storage_id=storage_id,
                    quantity=batch.current_quantity
                )
                db.session.add(batch_storage)
                
                # 設置主要儲位
                batch.primary_storage_id = storage_id
                
                # 創建入庫移動記錄
                movement = InventoryMovement(
                    batch_id=batch.batch_id,
                    movement_type='in',
                    movement_subtype='receiving',
                    quantity=batch.current_quantity,
                    to_storage_id=storage_id,
                    operator_id=admin_user.user_id,
                    reference_type='PO',
                    reference_number=batch.source_po_number,
                    reason_code='normal',
                    notes='測試入庫'
                )
                db.session.add(movement)
                
                print(f"  - Stored: {batch.item_name} x {batch.current_quantity} {batch.unit} at {storage_id}")
            
            db.session.commit()
            print("\n=== 第三步：儲位分配完成 ===\n")
            
            # 步驟4：驗證數據
            print("=== 第四步：驗證庫存數據 ===")
            
            # 統計庫存批次
            batch_count = InventoryBatch.query.filter_by(batch_status='active').count()
            print(f"活躍庫存批次數量: {batch_count}")
            
            # 統計各物料的庫存
            from sqlalchemy import func
            inventory_summary = db.session.query(
                InventoryBatch.item_name,
                func.sum(InventoryBatch.current_quantity).label('total_qty'),
                func.count(InventoryBatch.batch_id).label('batch_count'),
                InventoryBatch.unit
            ).filter(
                InventoryBatch.batch_status == 'active',
                InventoryBatch.current_quantity > 0
            ).group_by(
                InventoryBatch.item_name,
                InventoryBatch.unit
            ).all()
            
            print("\n庫存匯總:")
            print("-" * 60)
            for item in inventory_summary:
                print(f"{item.item_name}: {item.total_qty} {item.unit} (分{item.batch_count}批)")
            
            print("\n=== 測試數據創建完成！===")
            print("\n您現在可以:")
            print("1. 訪問 http://172.20.10.10:5174/inventory/query 查詢庫存")
            print("2. 訪問 http://172.20.10.10:5174/receiving 查看收貨管理")
            print("3. 訪問 http://172.20.10.10:5174/inventory/storage 查看儲位管理")
            
        except Exception as e:
            print(f"Error creating test data: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    create_test_data()