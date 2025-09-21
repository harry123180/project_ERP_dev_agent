"""
Project Management API Routes
Handles project creation, tracking, and expenditure management
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
    Project, ProjectSupplierExpenditure, PurchaseOrder,
    Supplier, User
)
from app.auth import require_roles
from app.utils.validation import validate_project_data, validate_expenditure_data
from app.utils.pagination import paginate_query
from app.utils.cache import cache_result, invalidate_cache

# Create blueprint
projects_bp = Blueprint('projects', __name__, url_prefix='/api/v1/projects')
logger = logging.getLogger(__name__)

@projects_bp.route('', methods=['GET'])
@jwt_required()
def list_projects():
    """
    List all projects with filtering and pagination
    Query Parameters:
    - page: int (default: 1)
    - page_size: int (default: 20, max: 100)
    - status: string ('active', 'inactive', 'completed') 
    - manager_id: int (filter by project manager)
    - search: string (search in project name/description)
    - start_date: date (projects started after this date)
    - end_date: date (projects ending before this date)
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 20, type=int), 100)
        status_filter = request.args.get('status')
        manager_id = request.args.get('manager_id', type=int)
        search = request.args.get('search')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build base query with eager loading
        query = db.session.query(Project)\
                .options(selectinload(Project.manager))
        
        # Apply filters
        if status_filter == 'ongoing':
            query = query.filter(Project.project_status == 'ongoing')
        elif status_filter == 'completed':
            query = query.filter(Project.project_status == 'completed')
        elif status_filter == 'completed_by_date':
            query = query.filter(Project.end_date <= datetime.now().date())
            
        if manager_id:
            query = query.filter(Project.manager_id == manager_id)
            
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Project.project_name.ilike(search_term),
                    Project.customer_name.ilike(search_term),
                    Project.customer_department.ilike(search_term)
                )
            )
            
        if start_date:
            query = query.filter(Project.start_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
            
        if end_date:
            query = query.filter(Project.end_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        # Order by most recent first
        query = query.order_by(desc(Project.created_at))
        
        # Paginate results
        paginated_result = paginate_query(query, page, page_size)
        
        # Format response with expenditure summaries
        projects_data = []
        for project in paginated_result['items']:
            # Use the existing total_expenditure field from the project
            total_expenditure = float(project.total_expenditure) if project.total_expenditure else 0
            
            project_data = {
                'project_id': project.project_id,
                'project_code': getattr(project, 'project_code', None),
                'project_name': project.project_name,
                'project_status': project.project_status,
                'budget': float(getattr(project, 'budget', 0)) if getattr(project, 'budget', None) is not None else None,
                'manager': {
                    'user_id': project.manager.user_id,
                    'chinese_name': project.manager.chinese_name,
                    'name': project.manager.chinese_name,
                    'username': project.manager.username
                } if project.manager else None,
                'total_expenditure': float(total_expenditure),
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'end_date': project.end_date.isoformat() if project.end_date else None,
                'customer_name': project.customer_name,
                'customer_contact': project.customer_contact,
                'customer_department': project.customer_department,
                'customer_address': getattr(project, 'customer_address', None),
                'customer_phone': getattr(project, 'customer_phone', None),
                'description': getattr(project, 'description', None),
                'created_at': project.created_at.isoformat(),
                'updated_at': project.updated_at.isoformat() if project.updated_at else None
            }
            projects_data.append(project_data)
        
        return jsonify({
            'items': projects_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': paginated_result['total'],
                'has_more': paginated_result['has_more'],
                'pages': (paginated_result['total'] + page_size - 1) // page_size
            },
            'success': True,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'LIST_PROJECTS_ERROR',
                'message': 'Failed to retrieve projects',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@projects_bp.route('', methods=['POST'])
@jwt_required()
def create_project():
    """
    Create a new project
    Required fields: project_name
    Optional fields: project_code, description, manager_id, budget, start_date, end_date
    """
    try:
        data = request.get_json()
        
        # Clean up empty strings - convert to None for optional fields
        for key in ['description', 'end_date', 'customer_name', 'customer_department', 
                    'customer_contact', 'customer_phone', 'customer_address', 'project_code']:
            if key in data and data[key] == '':
                data.pop(key)  # Remove empty string fields entirely
        
        # Convert budget to None if empty or 0
        if 'budget' in data and (data['budget'] == '' or data['budget'] == 0):
            data['budget'] = None
            
        # Validate input data - only project_name is required
        validation_errors = validate_project_data(data, required_fields=['project_name'])
        if validation_errors:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid project data',
                    'details': validation_errors
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 422
        
        # Generate project_code if not provided
        if not data.get('project_code'):
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            data['project_code'] = f"PROJ{timestamp}"
        
        # Check for duplicate project code
        existing_project = Project.query.filter_by(project_code=data['project_code']).first()
        if existing_project:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'DUPLICATE_PROJECT_CODE',
                    'message': 'Project code already exists',
                    'details': {'project_code': data['project_code']}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 409
        
        # Validate manager exists if provided
        if data.get('manager_id'):
            manager = User.query.get(data['manager_id'])
            if not manager:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_MANAGER',
                        'message': 'Specified manager does not exist',
                        'details': {'manager_id': data['manager_id']}
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }), 422
        
        # Create new project
        project = Project(
            project_id=data.get('project_id', f"PROJ{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            project_code=data.get('project_code'),
            project_name=data['project_name'],
            description=data.get('description'),
            project_status=data.get('project_status', 'ongoing'),
            manager_id=data.get('manager_id'),
            budget=data.get('budget', 0),
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') and data['start_date'] else None,
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') and data['end_date'] else None,
            customer_name=data.get('customer_name'),
            customer_contact=data.get('customer_contact'),
            customer_address=data.get('customer_address'),
            customer_phone=data.get('customer_phone'),
            customer_department=data.get('customer_department'),
            created_at=datetime.utcnow()
        )
        
        db.session.add(project)
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache('projects:*')
        
        # Log creation
        logger.info(f"Project created: {project.project_code} by user {get_jwt_identity()}")
        
        # Return created project
        return jsonify({
            'success': True,
            'data': {
                'project_id': project.project_id,
                'project_code': project.project_code,
                'project_name': project.project_name,
                'description': project.description,
                'project_status': project.project_status,
                'manager_id': project.manager_id,
                'budget': float(project.budget) if project.budget else None,
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'end_date': project.end_date.isoformat() if project.end_date else None,
                'customer_name': project.customer_name,
                'customer_contact': project.customer_contact,
                'created_at': project.created_at.isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating project: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'CREATE_PROJECT_ERROR',
                'message': 'Failed to create project',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@projects_bp.route('/<project_identifier>', methods=['GET', 'OPTIONS'])
@jwt_required(optional=True)
def get_project_by_identifier(project_identifier):
    """
    Get project information by project ID or project code
    Handles both integer IDs and string project codes
    """
    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response, 200

    try:
        # First try to find by project_id (can be string or integer)
        project = db.session.query(Project)\
                    .options(selectinload(Project.manager))\
                    .filter(Project.project_id == project_identifier)\
                    .first()

        # If not found, try to find by project_code
        if not project:
            project = db.session.query(Project)\
                        .options(selectinload(Project.manager))\
                        .filter(Project.project_code == project_identifier)\
                        .first()

        if not project:
            return jsonify({
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Resource not found',
                    'details': {}
                }
            }), 404

        # Build response data
        response_data = {
            'project_id': project.project_id,
            'project_code': project.project_code,
            'project_name': project.project_name,
            'description': project.description,
            'project_status': project.project_status,
            'start_date': project.start_date.isoformat() if project.start_date else None,
            'end_date': project.end_date.isoformat() if project.end_date else None,
            'budget': float(project.budget) if project.budget else 0,
            'total_expenditure': float(project.total_expenditure) if project.total_expenditure else 0,
            'customer_name': project.customer_name,
            'customer_contact': project.customer_contact,
            'customer_address': project.customer_address,
            'customer_phone': project.customer_phone,
            'customer_department': project.customer_department,
            'manager_id': project.manager_id,
            'manager_name': project.manager.chinese_name if project.manager else None,
            'created_at': project.created_at.isoformat() if project.created_at else None,
            'updated_at': project.updated_at.isoformat() if project.updated_at else None
        }

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error getting project: {str(e)}")
        return jsonify({
            'error': {
                'code': 'PROJECT_ERROR',
                'message': 'Failed to get project',
                'details': {'error': str(e)}
            }
        }), 500


# @projects_bp.route('/<int:project_id>', methods=['GET'])
# @jwt_required()
# def get_project_details(project_id):
    """
    Get detailed project information including expenditure breakdown
    """
    try:
        # Get project with relationships
        project = db.session.query(Project)\
                    .options(selectinload(Project.manager))\
                    .get(project_id)
        
        if not project:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'PROJECT_NOT_FOUND',
                    'message': 'Project not found',
                    'details': {'project_id': project_id}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 404
        
        # Get expenditure breakdown by supplier
        expenditure_query = db.session.query(
            ProjectSupplierExpenditure.supplier_id,
            Supplier.supplier_name_zh,
            func.sum(ProjectSupplierExpenditure.amount).label('total_amount'),
            func.count(ProjectSupplierExpenditure.id).label('transaction_count')
        ).join(Supplier, ProjectSupplierExpenditure.supplier_id == Supplier.id)\
         .filter(ProjectSupplierExpenditure.project_id == project_id)\
         .group_by(ProjectSupplierExpenditure.supplier_id, Supplier.supplier_name_zh)\
         .all()
        
        expenditure_breakdown = [
            {
                'supplier_id': exp.supplier_id,
                'supplier_name': exp.supplier_name_zh,
                'total_amount': float(exp.total_amount),
                'transaction_count': exp.transaction_count
            }
            for exp in expenditure_query
        ]
        
        # Calculate totals
        total_expenditure = sum(exp['total_amount'] for exp in expenditure_breakdown)
        remaining_budget = float(project.budget - total_expenditure) if project.budget else None
        
        # Get recent purchase orders related to this project
        recent_pos = db.session.query(PurchaseOrder)\
                     .join(ProjectSupplierExpenditure, PurchaseOrder.id == ProjectSupplierExpenditure.po_id)\
                     .filter(ProjectSupplierExpenditure.project_id == project_id)\
                     .order_by(desc(PurchaseOrder.created_at))\
                     .limit(10)\
                     .all()
        
        recent_po_data = [
            {
                'id': po.id,
                'po_no': po.po_no,
                'supplier_name': po.supplier.supplier_name_zh if po.supplier else None,
                'total_amount': float(po.total_amount) if po.total_amount else 0,
                'status': po.status,
                'created_at': po.created_at.isoformat()
            }
            for po in recent_pos
        ]
        
        project_data = {
            'id': project.id,
            'project_code': project.project_code,
            'project_name': project.project_name,
            'project_description': project.project_description,
            'manager': {
                'id': project.manager.id,
                'name': project.manager.chinese_name,
                'username': project.manager.username,
                'department': project.manager.department
            } if project.manager else None,
            'budget': float(project.budget) if project.budget else None,
            'total_expenditure': total_expenditure,
            'remaining_budget': remaining_budget,
            'budget_utilization_percent': round((total_expenditure / float(project.budget)) * 100, 2) if project.budget and project.budget > 0 else 0,
            'start_date': project.start_date.isoformat() if project.start_date else None,
            'end_date': project.end_date.isoformat() if project.end_date else None,
            'is_active': project.is_active,
            'expenditure_breakdown': expenditure_breakdown,
            'recent_purchase_orders': recent_po_data,
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat() if project.updated_at else None
        }
        
        return jsonify({
            'success': True,
            'data': project_data,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving project {project_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'GET_PROJECT_ERROR',
                'message': 'Failed to retrieve project details',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@projects_bp.route('/<int:project_id>', methods=['PUT'])
@jwt_required()
@require_roles(['Admin', 'ProcurementMgr'])
def update_project(project_id):
    """
    Update project information
    Updatable fields: project_name, project_description, manager_id, budget, start_date, end_date, is_active
    """
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'PROJECT_NOT_FOUND',
                    'message': 'Project not found',
                    'details': {'project_id': project_id}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 404
        
        data = request.get_json()
        
        # Validate input data
        validation_errors = validate_project_data(data, required_fields=[])
        if validation_errors:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid project data',
                    'details': validation_errors
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 422
        
        # Update fields
        if 'project_name' in data:
            project.project_name = data['project_name']
        if 'project_description' in data:
            project.project_description = data['project_description']
        if 'manager_id' in data:
            if data['manager_id']:
                manager = User.query.get(data['manager_id'])
                if not manager:
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'INVALID_MANAGER',
                            'message': 'Specified manager does not exist',
                            'details': {'manager_id': data['manager_id']}
                        },
                        'timestamp': datetime.utcnow().isoformat()
                    }), 422
            project.manager_id = data['manager_id']
        if 'budget' in data:
            project.budget = data['budget']
        if 'start_date' in data:
            project.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data['start_date'] else None
        if 'end_date' in data:
            project.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data['end_date'] else None
        if 'is_active' in data:
            project.is_active = data['is_active']
        
        project.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache('projects:*')
        
        # Log update
        logger.info(f"Project updated: {project.project_code} by user {get_jwt_identity()}")
        
        return jsonify({
            'success': True,
            'data': {
                'id': project.id,
                'project_code': project.project_code,
                'project_name': project.project_name,
                'project_description': project.project_description,
                'manager_id': project.manager_id,
                'budget': float(project.budget) if project.budget else None,
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'end_date': project.end_date.isoformat() if project.end_date else None,
                'is_active': project.is_active,
                'updated_at': project.updated_at.isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating project {project_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'UPDATE_PROJECT_ERROR',
                'message': 'Failed to update project',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@projects_bp.route('/<int:project_id>/expenditure', methods=['GET'])
@jwt_required()
@cache_result('projects', lambda project_id: f'expenditure:{project_id}')
def get_project_expenditure(project_id):
    """
    Get detailed expenditure history for a project
    Query Parameters:
    - start_date: date (expenditures after this date)
    - end_date: date (expenditures before this date)
    - supplier_id: int (filter by supplier)
    - page: int (default: 1)
    - page_size: int (default: 50)
    """
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'PROJECT_NOT_FOUND',
                    'message': 'Project not found',
                    'details': {'project_id': project_id}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 404
        
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        supplier_id = request.args.get('supplier_id', type=int)
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 50, type=int), 100)
        
        # Build query
        query = db.session.query(ProjectSupplierExpenditure)\
                .join(Supplier, ProjectSupplierExpenditure.supplier_id == Supplier.id)\
                .join(PurchaseOrder, ProjectSupplierExpenditure.po_id == PurchaseOrder.id)\
                .filter(ProjectSupplierExpenditure.project_id == project_id)
        
        # Apply filters
        if start_date:
            query = query.filter(ProjectSupplierExpenditure.expenditure_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(ProjectSupplierExpenditure.expenditure_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        if supplier_id:
            query = query.filter(ProjectSupplierExpenditure.supplier_id == supplier_id)
        
        # Order by most recent first
        query = query.order_by(desc(ProjectSupplierExpenditure.expenditure_date))
        
        # Paginate
        paginated_result = paginate_query(query, page, page_size)
        
        # Format expenditure data
        expenditure_data = []
        for expenditure in paginated_result['items']:
            exp_data = {
                'id': expenditure.id,
                'amount': float(expenditure.amount),
                'expenditure_date': expenditure.expenditure_date.isoformat(),
                'supplier': {
                    'id': expenditure.supplier.id,
                    'name': expenditure.supplier.supplier_name_zh,
                    'supplier_id': expenditure.supplier.supplier_id
                },
                'purchase_order': {
                    'id': expenditure.po_id,
                    'po_no': expenditure.purchase_order.po_no,
                    'status': expenditure.purchase_order.status
                },
                'created_at': expenditure.created_at.isoformat()
            }
            expenditure_data.append(exp_data)
        
        return jsonify({
            'success': True,
            'data': {
                'project': {
                    'id': project.id,
                    'project_code': project.project_code,
                    'project_name': project.project_name
                },
                'expenditures': expenditure_data,
                'summary': {
                    'total_amount': sum(float(exp.amount) for exp in paginated_result['items']),
                    'count': len(expenditure_data)
                }
            },
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': paginated_result['total'],
                'has_more': paginated_result['has_more']
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving project expenditure {project_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'GET_EXPENDITURE_ERROR',
                'message': 'Failed to retrieve project expenditure',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@projects_bp.route('/<project_identifier>/requisitions', methods=['GET'])
@jwt_required()
def get_project_requisitions(project_identifier):
    """
    Get all requisitions for a specific project
    Args:
        project_identifier: Can be either project_id (string) or id (integer)
    Returns:
        List of requisitions associated with the project
    """
    try:
        # Use raw SQL to query requisitions by project_id
        from sqlalchemy import text

        query = text("""
            SELECT
                ro.request_order_no,
                ro.project_id,
                ro.submit_date,
                ro.requester_name,
                ro.usage_type,
                ro.order_status,
                ro.created_at,
                ro.updated_at,
                COALESCE(SUM(roi.item_quantity * roi.unit_price), 0) as total_amount
            FROM request_orders ro
            LEFT JOIN request_order_items roi ON ro.request_order_no = roi.request_order_no
            WHERE ro.project_id = :project_id
            GROUP BY ro.request_order_no, ro.project_id, ro.submit_date,
                     ro.requester_name, ro.usage_type, ro.order_status,
                     ro.created_at, ro.updated_at
        """)

        result = db.session.execute(query, {'project_id': project_identifier})
        rows = result.fetchall()

        # Convert rows to dictionaries
        requisitions_data = []
        for row in rows:
            req_dict = {
                'requisition_no': row[0],  # request_order_no
                'project_id': row[1],
                'requisition_date': row[2],  # submit_date
                'applicant_name': row[3],  # requester_name
                'department': row[4],  # usage_type
                'status': row[5],  # order_status
                'created_at': row[6],
                'updated_at': row[7],
                'total_amount': float(row[8]) if row[8] else 0,
                # These fields are compatible with frontend expectations
                'approval_status': row[5],  # Use order_status as approval_status
                'usage_type': row[4]
            }
            requisitions_data.append(req_dict)

        logger.info(f"Retrieved {len(requisitions_data)} requisitions for project {project_identifier}")

        return jsonify(requisitions_data), 200

    except Exception as e:
        logger.error(f"Error retrieving requisitions for project {project_identifier}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'GET_REQUISITIONS_ERROR',
                'message': 'Failed to retrieve project requisitions',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500