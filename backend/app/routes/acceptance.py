"""
Acceptance & Quality Control API Routes
Handles item acceptance, validation, and quality check operations
Architecture Lead: Winston
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import and_, func, desc, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import logging

from app import db
from app.models import (
    RequestOrderItem, PurchaseOrderItem, PurchaseOrder, RequestOrder,
    User, Supplier
)
from app.auth import require_roles
from app.utils.validation import validate_date_string
from app.utils.pagination import paginate_query
from app.utils.cache import cache_result, invalidate_cache

# Create blueprint
acceptance_bp = Blueprint('acceptance', __name__, url_prefix='/api/v1/acceptance')
logger = logging.getLogger(__name__)

@acceptance_bp.route('/pending', methods=['GET'])
@jwt_required()
def list_pending_acceptance():
    """
    List all items pending acceptance/validation
    Query Parameters:
    - user_id: filter by assigned user (Admin only)
    - priority: filter by priority (high, medium, low)
    - item_type: filter by item type (po_item, request_item)
    - overdue_only: boolean (show only overdue items)
    - page: int (default: 1)
    - page_size: int (default: 50)
    """
    try:
        # Get query parameters
        user_id = request.args.get('user_id', type=int)
        priority = request.args.get('priority')
        item_type = request.args.get('item_type')
        overdue_only = request.args.get('overdue_only', 'false').lower() == 'true'
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 50, type=int), 100)
        
        current_user_id = get_jwt_identity()
        user_roles = get_jwt().get('roles', [])
        
        # Admin can see all, others see only their own
        if user_id and 'Admin' not in user_roles:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INSUFFICIENT_PERMISSIONS',
                    'message': 'Only admins can filter by user',
                    'details': {}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 403
        
        target_user_id = user_id if user_id and 'Admin' in user_roles else current_user_id
        
        pending_items = []
        
        # Get pending request order items if not filtered to po_item only
        if item_type != 'po_item':
            ro_query = db.session.query(RequestOrderItem)\
                      .join(RequestOrder, RequestOrderItem.request_order_no == RequestOrder.request_order_no)\
                      .join(User, RequestOrder.requester_id == User.user_id)\
                      .filter(and_(
                          RequestOrderItem.acceptance_status == 'pending_acceptance',
                          RequestOrderItem.needs_acceptance == True
                      ))
            
            if not ('Admin' in user_roles or 'ProcurementMgr' in user_roles):
                ro_query = ro_query.filter(RequestOrder.requester_id == target_user_id)
            
            ro_items = ro_query.all()
            
            for item in ro_items:
                # Calculate priority based on various factors
                priority_score = _calculate_acceptance_priority(item, 'request_item')
                priority_level = 'high' if priority_score >= 8 else 'medium' if priority_score >= 5 else 'low'
                
                if priority and priority != priority_level:
                    continue
                
                # Check if overdue
                is_overdue = False
                days_pending = None
                if item.request_order.submit_date:
                    days_pending = (datetime.utcnow().date() - item.request_order.submit_date).days
                    is_overdue = days_pending > 5  # More than 5 days pending
                
                if overdue_only and not is_overdue:
                    continue
                
                item_data = {
                    'id': item.detail_id,
                    'type': 'request_item',
                    'item_reference': getattr(item, 'material_serial_no', ''),
                    'item_name': item.item_name,
                    'item_spec': item.item_specification,
                    'quantity': float(item.item_quantity),
                    'unit': item.item_unit,
                    'request_order': {
                        'id': item.request_order.request_order_no,
                        'ro_no': item.request_order.request_order_no,
                        'ro_date': item.request_order.submit_date.isoformat() if item.request_order.submit_date else None,
                        'requested_by': item.request_order.requester_name,
                        'status': item.request_order.order_status
                    },
                    'acceptance_status': item.acceptance_status,
                    'needs_acceptance': item.needs_acceptance,
                    'priority': priority_level,
                    'priority_score': priority_score,
                    'is_overdue': is_overdue,
                    'days_pending': days_pending if item.request_order.submit_date else None,
                    'created_at': item.created_at.isoformat() if item.created_at else None,
                    'notes': item.status_note
                }
                pending_items.append(item_data)
        
        # Get pending purchase order items if not filtered to request_item only
        if False and item_type != 'request_item':  # Temporarily disabled
            po_query = db.session.query(PurchaseOrderItem)\
                      .join(PurchaseOrder, PurchaseOrderItem.po_id == PurchaseOrder.id)\
                      .join(Supplier, PurchaseOrder.supplier_id == Supplier.id)\
                      .filter(and_(
                          PurchaseOrderItem.receiving_status == 'received',
                          PurchaseOrderItem.acceptance_status.in_(['pending_acceptance', None])
                      ))
            
            po_items = po_query.all()
            
            for item in po_items:
                # Calculate priority
                priority_score = _calculate_acceptance_priority(item, 'po_item')
                priority_level = 'high' if priority_score >= 8 else 'medium' if priority_score >= 5 else 'low'
                
                if priority and priority != priority_level:
                    continue
                
                # Check if overdue
                is_overdue = False
                days_pending = None
                if item.received_date:
                    days_pending = (datetime.utcnow().date() - item.received_date.date()).days
                    is_overdue = days_pending > 3  # More than 3 days since received
                
                if overdue_only and not is_overdue:
                    continue
                
                item_data = {
                    'id': item.id,
                    'type': 'po_item',
                    'item_reference': item.item_reference,
                    'item_name': item.item_name,
                    'item_spec': item.item_spec,
                    'quantity': item.quantity,
                    'received_quantity': item.received_quantity,
                    'unit': item.unit,
                    'purchase_order': {
                        'id': item.purchase_order.id,
                        'po_no': item.purchase_order.po_no,
                        'po_date': item.purchase_order.po_date.isoformat(),
                        'supplier': item.purchase_order.supplier.supplier_name_zh,
                        'status': item.purchase_order.status
                    },
                    'receiving_status': item.receiving_status,
                    'acceptance_status': item.acceptance_status,
                    'received_date': item.received_date.isoformat() if item.received_date else None,
                    'priority': priority_level,
                    'priority_score': priority_score,
                    'is_overdue': is_overdue,
                    'days_pending': days_pending,
                    'created_at': item.created_at.isoformat(),
                    'notes': item.notes
                }
                pending_items.append(item_data)
        
        # Sort by priority score (highest first), then by days pending
        pending_items.sort(key=lambda x: (x['priority_score'], x['days_pending'] or 0), reverse=True)
        
        # Manual pagination since we combined two queries
        total_items = len(pending_items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = pending_items[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'data': paginated_items,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total_items,
                'has_more': end_idx < total_items
            },
            'summary': {
                'total_pending': total_items,
                'overdue_count': len([item for item in pending_items if item['is_overdue']]),
                'high_priority': len([item for item in pending_items if item['priority'] == 'high']),
                'medium_priority': len([item for item in pending_items if item['priority'] == 'medium']),
                'low_priority': len([item for item in pending_items if item['priority'] == 'low'])
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing pending acceptance items: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'ACCEPTANCE_LIST_ERROR',
                'message': 'Failed to retrieve pending acceptance items',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@acceptance_bp.route('/validation', methods=['POST'])
@jwt_required()
@require_roles(['Admin', 'ProcurementMgr', 'QualityCtrl'])
def perform_validation():
    """
    Perform validation/quality check on an item
    Required fields: item_id, item_type (request_item/po_item), validation_result
    Optional fields: quality_notes, defect_description, photos
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['item_id', 'item_type', 'validation_result']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_REQUIRED_FIELD',
                        'message': f'Required field missing: {field}',
                        'details': {'field': field}
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }), 422
        
        # Validate item_type
        if data['item_type'] not in ['request_item', 'po_item']:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_ITEM_TYPE',
                    'message': 'Invalid item type. Must be request_item or po_item',
                    'details': {'valid_types': ['request_item', 'po_item']}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 422
        
        # Validate validation_result
        valid_results = ['passed', 'failed', 'needs_review']
        if data['validation_result'] not in valid_results:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_VALIDATION_RESULT',
                    'message': 'Invalid validation result',
                    'details': {'valid_results': valid_results}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 422
        
        # Get the item based on type
        if data['item_type'] == 'request_item':
            item = RequestOrderItem.query.get(data['item_id'])
            if not item:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'REQUEST_ITEM_NOT_FOUND',
                        'message': 'Request order item not found',
                        'details': {'item_id': data['item_id']}
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }), 404
        else:
            item = PurchaseOrderItem.query.get(data['item_id'])
            if not item:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'PO_ITEM_NOT_FOUND',
                        'message': 'Purchase order item not found',
                        'details': {'item_id': data['item_id']}
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }), 404
        
        # Update validation status based on result
        validation_result = data['validation_result']
        current_time = datetime.utcnow()
        
        if validation_result == 'passed':
            item.acceptance_status = 'accepted'
        elif validation_result == 'failed':
            item.acceptance_status = 'rejected'
        else:  # needs_review
            item.acceptance_status = 'needs_review'
        
        # Add quality notes and validation details
        validation_notes = []
        if data.get('quality_notes'):
            validation_notes.append(f"Quality Notes: {data['quality_notes']}")
        if data.get('defect_description'):
            validation_notes.append(f"Defects: {data['defect_description']}")
        
        validation_log = f"[{current_time.strftime('%Y-%m-%d %H:%M')}] Validation: {validation_result.upper()}"
        if validation_notes:
            validation_log += f" - {'; '.join(validation_notes)}"
        validation_log += f" (by user {get_jwt_identity()})"
        
        # Append to existing notes
        if item.notes:
            item.notes += f"\n{validation_log}"
        else:
            item.notes = validation_log
        
        # Update timestamps
        item.updated_at = current_time
        if hasattr(item, 'validation_date'):
            item.validation_date = current_time
        
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache('acceptance:*')
        
        logger.info(f"Validation completed: {data['item_type']} {item.id} - {validation_result} by user {get_jwt_identity()}")
        
        return jsonify({
            'success': True,
            'data': {
                'item_id': item.id,
                'item_type': data['item_type'],
                'item_reference': item.item_reference,
                'validation_result': validation_result,
                'acceptance_status': item.acceptance_status,
                'validation_date': current_time.isoformat(),
                'quality_notes': data.get('quality_notes', ''),
                'defect_description': data.get('defect_description', '')
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error performing validation: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Failed to perform validation',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@acceptance_bp.route('/quality-check', methods=['POST'])
@jwt_required()
@require_roles(['Admin', 'ProcurementMgr', 'QualityCtrl'])
def quality_check():
    """
    Perform detailed quality check on an item
    Required fields: item_id, item_type, check_results
    Optional fields: photos, measurements, compliance_notes
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['item_id', 'item_type', 'check_results']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_REQUIRED_FIELD',
                        'message': f'Required field missing: {field}',
                        'details': {'field': field}
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }), 422
        
        # Get the item
        if data['item_type'] == 'request_item':
            item = RequestOrderItem.query.get(data['item_id'])
        else:
            item = PurchaseOrderItem.query.get(data['item_id'])
        
        if not item:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'ITEM_NOT_FOUND',
                    'message': f'{data["item_type"]} not found',
                    'details': {'item_id': data['item_id']}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 404
        
        # Process quality check results
        check_results = data['check_results']
        
        # Validate check_results structure
        if not isinstance(check_results, dict):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_CHECK_RESULTS',
                    'message': 'check_results must be an object',
                    'details': {'expected_structure': 'Object with check criteria and results'}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 422
        
        # Calculate overall quality score
        total_checks = len(check_results)
        passed_checks = sum(1 for result in check_results.values() if result.get('status') == 'pass')
        quality_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        # Determine quality status
        if quality_score >= 95:
            quality_status = 'excellent'
        elif quality_score >= 80:
            quality_status = 'good'
        elif quality_score >= 60:
            quality_status = 'acceptable'
        else:
            quality_status = 'poor'
        
        # Create quality check log
        current_time = datetime.utcnow()
        quality_log = f"[{current_time.strftime('%Y-%m-%d %H:%M')}] Quality Check: {quality_status.upper()} (Score: {quality_score:.1f}%)"
        
        # Add detailed results
        failed_checks = [check for check, result in check_results.items() if result.get('status') == 'fail']
        if failed_checks:
            quality_log += f" - Failed checks: {', '.join(failed_checks)}"
        
        # Add measurements if provided
        if data.get('measurements'):
            quality_log += f" - Measurements: {data['measurements']}"
        
        # Add compliance notes if provided
        if data.get('compliance_notes'):
            quality_log += f" - Compliance: {data['compliance_notes']}"
        
        quality_log += f" (by user {get_jwt_identity()})"
        
        # Update item with quality check results
        if item.notes:
            item.notes += f"\n{quality_log}"
        else:
            item.notes = quality_log
        
        # Update acceptance status based on quality
        if quality_score >= 60:  # Acceptable threshold
            item.acceptance_status = 'accepted'
        else:
            item.acceptance_status = 'rejected'
        
        item.updated_at = current_time
        
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache('acceptance:*')
        
        logger.info(f"Quality check completed: {data['item_type']} {item.id} - {quality_status} ({quality_score:.1f}%) by user {get_jwt_identity()}")
        
        return jsonify({
            'success': True,
            'data': {
                'item_id': item.id,
                'item_type': data['item_type'],
                'item_reference': item.item_reference,
                'quality_status': quality_status,
                'quality_score': round(quality_score, 1),
                'total_checks': total_checks,
                'passed_checks': passed_checks,
                'failed_checks': len(failed_checks),
                'check_results': check_results,
                'acceptance_status': item.acceptance_status,
                'check_date': current_time.isoformat(),
                'measurements': data.get('measurements', ''),
                'compliance_notes': data.get('compliance_notes', '')
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error performing quality check: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'QUALITY_CHECK_ERROR',
                'message': 'Failed to perform quality check',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@acceptance_bp.route('/reports/summary', methods=['GET'])
@jwt_required()
def acceptance_summary_report():
    """
    Generate acceptance summary report
    Query Parameters:
    - date_from: filter from date (YYYY-MM-DD)
    - date_to: filter to date (YYYY-MM-DD)
    - user_id: filter by user (Admin only)
    """
    try:
        # Get query parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        user_id = request.args.get('user_id', type=int)
        
        current_user_id = get_jwt_identity()
        user_roles = get_jwt().get('roles', [])
        
        # Date filters
        filters = []
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                filters.append(('date', '>=', from_date))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_DATE_FORMAT',
                        'message': 'Invalid date format. Use YYYY-MM-DD'
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }), 422
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                filters.append(('date', '<=', to_date))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_DATE_FORMAT',
                        'message': 'Invalid date format. Use YYYY-MM-DD'
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }), 422
        
        # Count acceptance statuses for request items
        ro_stats = {}
        ro_query = db.session.query(RequestOrderItem.acceptance_status, func.count(RequestOrderItem.id))\
                   .filter(RequestOrderItem.acceptance_status.isnot(None))\
                   .group_by(RequestOrderItem.acceptance_status)
        
        for status, count in ro_query.all():
            ro_stats[status] = count
        
        # Count acceptance statuses for purchase order items
        po_stats = {}
        po_query = db.session.query(PurchaseOrderItem.acceptance_status, func.count(PurchaseOrderItem.id))\
                   .filter(PurchaseOrderItem.acceptance_status.isnot(None))\
                   .group_by(PurchaseOrderItem.acceptance_status)
        
        for status, count in po_query.all():
            po_stats[status] = count
        
        # Calculate totals
        total_ro_items = sum(ro_stats.values())
        total_po_items = sum(po_stats.values())
        total_items = total_ro_items + total_po_items
        
        # Calculate acceptance rates
        ro_accepted = ro_stats.get('accepted', 0)
        po_accepted = po_stats.get('accepted', 0)
        total_accepted = ro_accepted + po_accepted
        
        acceptance_rate = (total_accepted / total_items * 100) if total_items > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_items': total_items,
                    'total_accepted': total_accepted,
                    'total_rejected': ro_stats.get('rejected', 0) + po_stats.get('rejected', 0),
                    'total_pending': ro_stats.get('pending_acceptance', 0) + po_stats.get('pending_acceptance', 0),
                    'needs_review': ro_stats.get('needs_review', 0) + po_stats.get('needs_review', 0),
                    'acceptance_rate': round(acceptance_rate, 2)
                },
                'request_items': {
                    'total': total_ro_items,
                    'stats': ro_stats
                },
                'purchase_items': {
                    'total': total_po_items,
                    'stats': po_stats
                },
                'filters': {
                    'date_from': date_from,
                    'date_to': date_to,
                    'user_id': user_id
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating acceptance report: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'ACCEPTANCE_REPORT_ERROR',
                'message': 'Failed to generate acceptance report',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Helper function
def _calculate_acceptance_priority(item, item_type):
    """Calculate acceptance priority based on various factors"""
    priority = 5  # Base priority
    
    if item_type == 'request_item':
        # Higher priority for older requests
        if item.request_order and item.request_order.submit_date:
            days_old = (datetime.utcnow().date() - item.request_order.submit_date).days
            if days_old > 7:
                priority += 3
            elif days_old > 3:
                priority += 2
            elif days_old > 1:
                priority += 1
        
        # Higher priority for urgent requests
        if item.request_order and hasattr(item.request_order, 'urgency_level') and item.request_order.urgency_level == 'high':
            priority += 3
            
    elif item_type == 'po_item':
        # Higher priority for items received longer ago
        if item.received_date:
            days_since_received = (datetime.utcnow().date() - item.received_date.date()).days
            if days_since_received > 5:
                priority += 3
            elif days_since_received > 2:
                priority += 2
            elif days_since_received > 0:
                priority += 1
        
        # Higher priority for high-value items
        if hasattr(item, 'unit_price') and item.unit_price and item.unit_price > 1000:
            priority += 2
    
    # Priority keywords in item name
    urgent_keywords = ['urgent', 'critical', 'emergency', 'asap']
    if any(keyword in item.item_name.lower() for keyword in urgent_keywords):
        priority += 2
    
    return min(priority, 10)  # Cap at 10