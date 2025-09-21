
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
        query = db.session.query(PurchaseOrder)\
            .join(Supplier, PurchaseOrder.supplier_id == Supplier.supplier_id)\
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
