"""
Pagination utilities for ERP system
Provides consistent pagination across all API endpoints
Architecture Lead: Winston
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Query
from sqlalchemy import func


def paginate_query(query: Query, page: int = 1, page_size: int = 20, max_page_size: int = 100) -> Dict[str, Any]:
    """
    Paginate a SQLAlchemy query with performance optimization
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-based)
        page_size: Number of items per page
        max_page_size: Maximum allowed page size
        
    Returns:
        Dictionary containing paginated results and metadata
    """
    # Validate and constrain inputs
    page = max(1, int(page))
    page_size = min(max(1, int(page_size)), max_page_size)
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get total count efficiently
    total = query.count()
    
    # Get paginated items
    items = query.offset(offset).limit(page_size).all()
    
    # Calculate pagination metadata
    total_pages = (total + page_size - 1) // page_size  # Ceiling division
    has_more = page < total_pages
    has_prev = page > 1
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'has_more': has_more,
        'has_prev': has_prev,
        'offset': offset
    }


def paginate_list(items: List[Any], page: int = 1, page_size: int = 20, max_page_size: int = 100) -> Dict[str, Any]:
    """
    Paginate a list of items (for in-memory pagination)
    
    Args:
        items: List of items to paginate
        page: Page number (1-based)
        page_size: Number of items per page
        max_page_size: Maximum allowed page size
        
    Returns:
        Dictionary containing paginated results and metadata
    """
    # Validate and constrain inputs
    page = max(1, int(page))
    page_size = min(max(1, int(page_size)), max_page_size)
    
    # Calculate pagination
    total = len(items)
    offset = (page - 1) * page_size
    end_index = offset + page_size
    
    # Get paginated items
    paginated_items = items[offset:end_index]
    
    # Calculate pagination metadata
    total_pages = (total + page_size - 1) // page_size
    has_more = page < total_pages
    has_prev = page > 1
    
    return {
        'items': paginated_items,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'has_more': has_more,
        'has_prev': has_prev,
        'offset': offset
    }


def get_pagination_params(request_args: Dict[str, Any], default_page_size: int = 20) -> Dict[str, int]:
    """
    Extract and validate pagination parameters from request arguments
    
    Args:
        request_args: Request arguments dictionary (e.g., request.args)
        default_page_size: Default page size if not specified
        
    Returns:
        Dictionary with validated page and page_size values
    """
    try:
        page = max(1, int(request_args.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    
    try:
        page_size = max(1, min(int(request_args.get('page_size', default_page_size)), 100))
    except (ValueError, TypeError):
        page_size = default_page_size
    
    return {
        'page': page,
        'page_size': page_size
    }


def format_pagination_response(paginated_result: Dict[str, Any], data_formatter=None) -> Dict[str, Any]:
    """
    Format paginated response in a consistent format
    
    Args:
        paginated_result: Result from paginate_query or paginate_list
        data_formatter: Optional function to format each item in the results
        
    Returns:
        Formatted response dictionary
    """
    items = paginated_result['items']
    
    # Apply formatter if provided
    if data_formatter and callable(data_formatter):
        items = [data_formatter(item) for item in items]
    
    return {
        'data': items,
        'pagination': {
            'page': paginated_result['page'],
            'page_size': paginated_result['page_size'],
            'total': paginated_result['total'],
            'total_pages': paginated_result['total_pages'],
            'has_more': paginated_result['has_more'],
            'has_prev': paginated_result['has_prev']
        }
    }


def create_pagination_links(base_url: str, paginated_result: Dict[str, Any], 
                          additional_params: Dict[str, Any] = None) -> Dict[str, str]:
    """
    Create pagination navigation links
    
    Args:
        base_url: Base URL for the API endpoint
        paginated_result: Result from paginate_query or paginate_list
        additional_params: Additional query parameters to include in links
        
    Returns:
        Dictionary containing pagination navigation links
    """
    page = paginated_result['page']
    page_size = paginated_result['page_size']
    total_pages = paginated_result['total_pages']
    
    # Build query parameters
    params = {'page_size': page_size}
    if additional_params:
        params.update(additional_params)
    
    # Create parameter string helper
    def build_url(page_num):
        params['page'] = page_num
        param_string = '&'.join([f"{k}={v}" for k, v in params.items() if v is not None])
        return f"{base_url}?{param_string}"
    
    links = {
        'self': build_url(page),
        'first': build_url(1),
        'last': build_url(total_pages) if total_pages > 0 else build_url(1)
    }
    
    if paginated_result['has_prev']:
        links['prev'] = build_url(page - 1)
    
    if paginated_result['has_more']:
        links['next'] = build_url(page + 1)
    
    return links


def optimize_count_query(query: Query) -> int:
    """
    Optimize count query for better performance on large datasets
    
    Args:
        query: SQLAlchemy query object
        
    Returns:
        Total count of records
    """
    # For simple queries, use the standard count
    try:
        # Try to get the count without loading all objects
        count_query = query.statement.with_only_columns([func.count()]).order_by(None)
        return query.session.execute(count_query).scalar()
    except Exception:
        # Fallback to standard count if optimization fails
        return query.count()


class PaginationHelper:
    """Helper class for consistent pagination handling"""
    
    def __init__(self, default_page_size: int = 20, max_page_size: int = 100):
        self.default_page_size = default_page_size
        self.max_page_size = max_page_size
    
    def paginate(self, query: Query, page: int = None, page_size: int = None) -> Dict[str, Any]:
        """Paginate query with instance defaults"""
        page = page or 1
        page_size = page_size or self.default_page_size
        return paginate_query(query, page, page_size, self.max_page_size)
    
    def get_params(self, request_args: Dict[str, Any]) -> Dict[str, int]:
        """Get pagination parameters with instance defaults"""
        return get_pagination_params(request_args, self.default_page_size)
    
    def format_response(self, paginated_result: Dict[str, Any], data_formatter=None) -> Dict[str, Any]:
        """Format response with consistent structure"""
        return format_pagination_response(paginated_result, data_formatter)


# Create default pagination helper instance
default_paginator = PaginationHelper()


def quick_paginate(query: Query, request_args: Dict[str, Any], data_formatter=None) -> Dict[str, Any]:
    """
    Quick pagination function for common use cases
    
    Args:
        query: SQLAlchemy query object
        request_args: Request arguments dictionary
        data_formatter: Optional function to format each item
        
    Returns:
        Formatted paginated response
    """
    params = get_pagination_params(request_args)
    paginated_result = paginate_query(query, params['page'], params['page_size'])
    return format_pagination_response(paginated_result, data_formatter)