"""
修復版本的 Delivery Management API Routes
修復搜尋功能的問題
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import logging

from app import db
from app.models import PurchaseOrder, Supplier

# Create blueprint
delivery_bp = Blueprint('delivery', __name__, url_prefix='/api/v1/delivery')
logger = logging.getLogger(__name__)

@delivery_bp.route('/maintenance-list', methods=['GET'])
@jwt_required()
def get_delivery_maintenance_list():
    """Get Delivery Maintenance List - 修復版本"""
    try:
        # Get query parameters and strip whitespace
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        status_filter = request.args.get('status', '').strip()
        supplier_region_filter = request.args.get('supplier_region', '').strip()
        po_number_filter = request.args.get('po_number', '').strip()
        
        # Add comprehensive logging for debugging
        logger.info(f"🔍 搜尋參數接收:")
        logger.info(f"  - po_number: '{po_number_filter}' (length: {len(po_number_filter)})")
        logger.info(f"  - supplier_region: '{supplier_region_filter}'")
        logger.info(f"  - status: '{status_filter}'")
        logger.info(f"  - page: {page}, page_size: {page_size}")
        
        # Start with base query
        query = db.session.query(PurchaseOrder)\
            .join(Supplier, PurchaseOrder.supplier_id == Supplier.supplier_id)\
            .filter(PurchaseOrder.purchase_status == 'purchased')
        
        logger.info("✅ 基礎查詢建立完成")
        
        # Apply filters with detailed logging
        filter_applied = False
        
        if supplier_region_filter:
            query = query.filter(Supplier.supplier_region == supplier_region_filter)
            logger.info(f"📍 應用供應商地區篩選: {supplier_region_filter}")
            filter_applied = True
        
        if status_filter:
            query = query.filter(PurchaseOrder.delivery_status == status_filter)
            logger.info(f"📊 應用狀態篩選: {status_filter}")
            filter_applied = True
            
        if po_number_filter:
            # Enhanced search logic - support multiple search patterns
            search_patterns = [
                PurchaseOrder.purchase_order_no.ilike(f'%{po_number_filter}%'),
                PurchaseOrder.purchase_order_no == po_number_filter,
                PurchaseOrder.purchase_order_no.ilike(f'{po_number_filter}%'),
                PurchaseOrder.purchase_order_no.ilike(f'%{po_number_filter}')
            ]
            
            query = query.filter(db.or_(*search_patterns))
            logger.info(f"🔎 應用採購單號篩選: '{po_number_filter}' (多模式匹配)")
            filter_applied = True
        
        if not filter_applied:
            logger.info("ℹ️  無篩選條件，返回所有已採購的採購單")
        
        # Execute query with error handling
        try:
            pos = query.all()
            logger.info(f"📋 SQL查詢執行成功，找到 {len(pos)} 筆採購單")
        except Exception as query_error:
            logger.error(f"❌ SQL查詢執行失敗: {str(query_error)}")
            return jsonify({
                'success': False,
                'error': f'Database query failed: {str(query_error)}'
            }), 500
        
        # Process results
        maintenance_list = []
        processed_count = 0
        
        for po in pos:
            try:
                # Get supplier information
                supplier = Supplier.query.get(po.supplier_id)
                if not supplier:
                    logger.warning(f"⚠️  採購單 {po.purchase_order_no} 找不到供應商資訊")
                    continue
                
                # Check if PO qualifies for maintenance list
                # (domestic or international not in consolidation)
                if supplier.supplier_region == 'domestic' or \
                   (supplier.supplier_region == 'international' and not po.consolidation_id):
                    
                    # Get item count safely
                    item_count = 0
                    try:
                        if hasattr(po, 'items') and po.items:
                            item_count = po.items.count()
                    except:
                        item_count = 0
                    
                    po_data = {
                        'po_number': po.purchase_order_no,
                        'supplier_id': po.supplier_id,
                        'supplier_name': po.supplier_name or supplier.supplier_name_zh,
                        'supplier_region': supplier.supplier_region,
                        'delivery_status': po.delivery_status or 'not_shipped',
                        'expected_delivery_date': po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
                        'actual_delivery_date': po.actual_delivery_date.isoformat() if po.actual_delivery_date else None,
                        'remarks': po.remarks or '',
                        'status_update_required': bool(po.status_update_required),
                        'consolidation_id': po.consolidation_id,
                        'item_count': item_count,
                        'can_create_consolidation': (
                            supplier.supplier_region == 'international' and 
                            po.delivery_status == 'shipped' and 
                            not po.consolidation_id
                        )
                    }
                    
                    maintenance_list.append(po_data)
                    processed_count += 1
                    
            except Exception as po_error:
                logger.error(f"❌ 處理採購單 {po.purchase_order_no} 時發生錯誤: {str(po_error)}")
                continue
        
        logger.info(f"✅ 成功處理 {processed_count} 筆採購單")
        
        # Apply search result logging
        if po_number_filter and len(maintenance_list) == 0:
            logger.warning(f"⚠️  搜尋 '{po_number_filter}' 沒有找到匹配的採購單")
        elif po_number_filter:
            logger.info(f"🎯 搜尋 '{po_number_filter}' 找到 {len(maintenance_list)} 筆匹配的採購單")
            for item in maintenance_list[:3]:  # Log first 3 matches
                logger.info(f"  - {item['po_number']} ({item['supplier_region']})")
        
        # Calculate summary statistics
        total_pos = len(maintenance_list)
        need_update = sum(1 for po in maintenance_list if po['status_update_required'])
        can_consolidate = sum(1 for po in maintenance_list if po['can_create_consolidation'])
        domestic_count = sum(1 for po in maintenance_list if po['supplier_region'] == 'domestic')
        international_count = sum(1 for po in maintenance_list if po['supplier_region'] == 'international')
        
        summary = {
            'total_pos': total_pos,
            'need_status_update': need_update,
            'can_create_consolidation': can_consolidate,
            'domestic_count': domestic_count,
            'international_count': international_count
        }
        
        logger.info(f"📊 統計結果: {summary}")
        
        # Return successful response
        response = {
            'success': True,
            'data': maintenance_list,
            'summary': summary,
            'debug_info': {
                'filters_applied': filter_applied,
                'search_term': po_number_filter,
                'total_found': total_pos
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ 取得交期維護列表失敗: {str(e)}")
        import traceback
        logger.error(f"詳細錯誤: {traceback.format_exc()}")
        
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}',
            'debug_info': {
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
        }), 500

@delivery_bp.route('/orders/<po_number>/status', methods=['PUT'])
@jwt_required()
def update_delivery_status(po_number):
    """Update delivery status (mandatory workflow)"""
    try:
        data = request.get_json()
        new_status = data.get('new_status') or data.get('status')  # Support both parameter names
        remarks = data.get('remarks', '')
        expected_date = data.get('expected_date')
        
        logger.info(f"🔄 更新交貨狀態請求 - PO: {po_number}, 新狀態: {new_status}")
        
        # Validate status
        valid_statuses = ['not_shipped', 'shipped', 'foreign_customs', 'taiwan_customs', 'in_transit', 'delivered']
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400
        
        # Find the PO
        po = PurchaseOrder.query.filter_by(purchase_order_no=po_number).first()
        if not po:
            logger.error(f"❌ 找不到採購單: {po_number}")
            return jsonify({
                'success': False,
                'error': 'Purchase order not found'
            }), 404
        
        # Update status
        old_status = po.delivery_status
        po.delivery_status = new_status
        po.status_update_required = False  # Clear the mandatory update flag
        
        # Update expected delivery date if provided
        if expected_date:
            try:
                po.expected_delivery_date = datetime.strptime(expected_date, '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"⚠️  無效的預期交貨日期格式: {expected_date}")
        
        # Update remarks if provided
        if remarks:
            po.remarks = remarks
            # Also update all items with the same remarks
            try:
                for item in po.items:
                    item.remarks = remarks
                    item.delivery_status = new_status
            except:
                logger.warning(f"⚠️  更新採購單項目備註失敗")
        
        # Set dates based on status
        if new_status == 'shipped' and old_status != 'shipped':
            po.shipped_at = datetime.now()
            logger.info(f"📦 設定發貨時間: {po.shipped_at}")
        elif new_status == 'delivered' and old_status != 'delivered':
            po.actual_delivery_date = datetime.now().date()
            logger.info(f"📋 設定實際到貨日期: {po.actual_delivery_date}")
        
        po.updated_at = datetime.now()
        db.session.commit()
        
        logger.info(f"✅ 成功更新狀態 {po_number}: {old_status} -> {new_status}")
        
        return jsonify({
            'success': True,
            'message': f'Status updated from {old_status} to {new_status}',
            'data': {
                'po_number': po_number,
                'old_status': old_status,
                'new_status': new_status,
                'remarks': remarks,
                'status_update_required': False
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 更新交貨狀態失敗 {po_number}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@delivery_bp.route('/orders/<po_number>/remarks', methods=['PUT'])
@jwt_required()
def update_remarks(po_number):
    """Update remarks/tracking number"""
    try:
        data = request.get_json()
        remarks = data.get('remarks', '')
        
        logger.info(f"📝 更新備註請求 - PO: {po_number}")
        
        # Find the PO
        po = PurchaseOrder.query.filter_by(purchase_order_no=po_number).first()
        if not po:
            return jsonify({
                'success': False,
                'error': 'Purchase order not found'
            }), 404
        
        # Update remarks
        old_remarks = po.remarks
        po.remarks = remarks
        
        # Cascade to items
        try:
            for item in po.items:
                item.remarks = remarks
        except:
            logger.warning(f"⚠️  更新項目備註失敗")
        
        po.updated_at = datetime.now()
        db.session.commit()
        
        logger.info(f"✅ 成功更新備註 {po_number}: '{old_remarks}' -> '{remarks}'")
        
        return jsonify({
            'success': True,
            'message': 'Remarks updated successfully',
            'data': {
                'po_number': po_number,
                'old_remarks': old_remarks,
                'new_remarks': remarks
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 更新備註失敗 {po_number}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ... 其他函數保持原樣 ...