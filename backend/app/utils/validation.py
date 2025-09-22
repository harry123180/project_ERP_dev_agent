"""
Validation utilities for ERP system
Provides data validation functions for all API endpoints
Architecture Lead: Winston
"""

import re
from datetime import datetime, date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Any, Optional


def validate_project_data(data: Dict[str, Any], required_fields: List[str] = None) -> List[str]:
    """
    Validate project data for creation and updates
    
    Args:
        data: Dictionary containing project data
        required_fields: List of required field names
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    if required_fields:
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Required field '{field}' is missing or empty")
    
    # Validate project_name
    if 'project_name' in data:
        if len(data['project_name']) < 2:
            errors.append("Project name must be at least 2 characters long")
        if len(data['project_name']) > 200:
            errors.append("Project name cannot exceed 200 characters")
    
    # Validate project_code
    if 'project_code' in data:
        if not re.match(r'^[A-Z0-9-_]{2,20}$', data['project_code']):
            errors.append("Project code must be 2-20 characters, alphanumeric, hyphens and underscores only")

    # Validate project_status (PostgreSQL ENUM constraint)
    if 'project_status' in data and data['project_status']:
        valid_statuses = ['ongoing', 'completed']
        if data['project_status'] not in valid_statuses:
            errors.append(f"Project status must be one of: {', '.join(valid_statuses)}")

    # Validate budget
    if 'budget' in data and data['budget'] is not None:
        try:
            budget = Decimal(str(data['budget']))
            if budget < 0:
                errors.append("Budget cannot be negative")
            if budget > Decimal('999999999.99'):
                errors.append("Budget cannot exceed 999,999,999.99")
        except (InvalidOperation, ValueError):
            errors.append("Budget must be a valid number")
    
    # Validate dates
    if 'start_date' in data and data['start_date']:
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        except ValueError:
            errors.append("Start date must be in YYYY-MM-DD format")
        else:
            if start_date > date.today() + timedelta(days=365):
                errors.append("Start date cannot be more than 1 year in the future")
    
    if 'end_date' in data and data['end_date']:
        try:
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            errors.append("End date must be in YYYY-MM-DD format")
        else:
            if 'start_date' in data and data['start_date']:
                try:
                    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                    if end_date <= start_date:
                        errors.append("End date must be after start date")
                except ValueError:
                    pass
    
    # Validate manager_id
    if 'manager_id' in data and data['manager_id'] is not None:
        try:
            manager_id = int(data['manager_id'])
            if manager_id <= 0:
                errors.append("Manager ID must be a positive integer")
        except (ValueError, TypeError):
            errors.append("Manager ID must be a valid integer")
    
    return errors


def validate_storage_data(data: Dict[str, Any], required_fields: List[str] = None) -> List[str]:
    """
    Validate storage location data for creation and updates
    
    Args:
        data: Dictionary containing storage data
        required_fields: List of required field names
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    if required_fields:
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Required field '{field}' is missing or empty")
    
    # Validate zone
    if 'zone' in data and data['zone']:
        if len(data['zone']) > 50:
            errors.append("Zone name cannot exceed 50 characters")
        if not re.match(r'^[A-Za-z0-9\s\-_]+$', data['zone']):
            errors.append("Zone name can only contain letters, numbers, spaces, hyphens, and underscores")
    
    # Validate shelf
    if 'shelf' in data and data['shelf']:
        if len(data['shelf']) > 50:
            errors.append("Shelf name cannot exceed 50 characters")
        if not re.match(r'^[A-Za-z0-9\s\-_]+$', data['shelf']):
            errors.append("Shelf name can only contain letters, numbers, spaces, hyphens, and underscores")
    
    # Validate floor
    if 'floor' in data and data['floor']:
        if len(data['floor']) > 20:
            errors.append("Floor name cannot exceed 20 characters")
        if not re.match(r'^[A-Za-z0-9\-_]+$', data['floor']):
            errors.append("Floor name can only contain letters, numbers, hyphens, and underscores")
    
    # Validate position
    if 'position' in data and data['position']:
        if len(data['position']) > 20:
            errors.append("Position name cannot exceed 20 characters")
        if not re.match(r'^[A-Za-z0-9\-_]+$', data['position']):
            errors.append("Position name can only contain letters, numbers, hyphens, and underscores")
    
    # Validate storage_type
    if 'storage_type' in data and data['storage_type']:
        valid_types = ['zone', 'shelf', 'floor', 'position', 'bin', 'rack', 'pallet']
        if data['storage_type'] not in valid_types:
            errors.append(f"Storage type must be one of: {', '.join(valid_types)}")
    
    # Validate capacities
    if 'max_capacity' in data and data['max_capacity'] is not None:
        try:
            max_cap = int(data['max_capacity'])
            if max_cap <= 0:
                errors.append("Maximum capacity must be a positive integer")
            if max_cap > 100000:
                errors.append("Maximum capacity cannot exceed 100,000")
        except (ValueError, TypeError):
            errors.append("Maximum capacity must be a valid integer")
    
    if 'current_capacity' in data and data['current_capacity'] is not None:
        try:
            current_cap = int(data['current_capacity'])
            if current_cap < 0:
                errors.append("Current capacity cannot be negative")
        except (ValueError, TypeError):
            errors.append("Current capacity must be a valid integer")
        
        # Check current vs max capacity if both provided
        if 'max_capacity' in data and data['max_capacity'] is not None:
            try:
                max_cap = int(data['max_capacity'])
                if current_cap > max_cap:
                    errors.append("Current capacity cannot exceed maximum capacity")
            except (ValueError, TypeError):
                pass
    
    return errors


def validate_expenditure_data(data: Dict[str, Any], required_fields: List[str] = None) -> List[str]:
    """
    Validate project expenditure data
    
    Args:
        data: Dictionary containing expenditure data
        required_fields: List of required field names
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    if required_fields:
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Required field '{field}' is missing or empty")
    
    # Validate amount
    if 'amount' in data and data['amount'] is not None:
        try:
            amount = Decimal(str(data['amount']))
            if amount <= 0:
                errors.append("Expenditure amount must be positive")
            if amount > Decimal('9999999.99'):
                errors.append("Expenditure amount cannot exceed 9,999,999.99")
        except (InvalidOperation, ValueError):
            errors.append("Expenditure amount must be a valid number")
    
    # Validate expenditure_date
    if 'expenditure_date' in data and data['expenditure_date']:
        try:
            exp_date = datetime.strptime(data['expenditure_date'], '%Y-%m-%d').date()
            if exp_date > date.today():
                errors.append("Expenditure date cannot be in the future")
        except ValueError:
            errors.append("Expenditure date must be in YYYY-MM-DD format")
    
    # Validate project_id
    if 'project_id' in data and data['project_id'] is not None:
        try:
            project_id = int(data['project_id'])
            if project_id <= 0:
                errors.append("Project ID must be a positive integer")
        except (ValueError, TypeError):
            errors.append("Project ID must be a valid integer")
    
    # Validate supplier_id
    if 'supplier_id' in data and data['supplier_id'] is not None:
        try:
            supplier_id = int(data['supplier_id'])
            if supplier_id <= 0:
                errors.append("Supplier ID must be a positive integer")
        except (ValueError, TypeError):
            errors.append("Supplier ID must be a valid integer")
    
    # Validate po_id
    if 'po_id' in data and data['po_id'] is not None:
        try:
            po_id = int(data['po_id'])
            if po_id <= 0:
                errors.append("Purchase Order ID must be a positive integer")
        except (ValueError, TypeError):
            errors.append("Purchase Order ID must be a valid integer")
    
    return errors


def validate_movement_data(data: Dict[str, Any], required_fields: List[str] = None) -> List[str]:
    """
    Validate storage movement data
    
    Args:
        data: Dictionary containing movement data
        required_fields: List of required field names
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    if required_fields:
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Required field '{field}' is missing or empty")
    
    # Validate item_reference
    if 'item_reference' in data and data['item_reference']:
        if len(data['item_reference']) > 100:
            errors.append("Item reference cannot exceed 100 characters")
    
    # Validate movement_type
    if 'movement_type' in data and data['movement_type']:
        valid_types = ['in', 'out', 'transfer', 'adjustment']
        if data['movement_type'] not in valid_types:
            errors.append(f"Movement type must be one of: {', '.join(valid_types)}")
    
    # Validate quantity
    if 'quantity' in data and data['quantity'] is not None:
        try:
            quantity = int(data['quantity'])
            if quantity <= 0:
                errors.append("Quantity must be a positive integer")
            if quantity > 100000:
                errors.append("Quantity cannot exceed 100,000")
        except (ValueError, TypeError):
            errors.append("Quantity must be a valid integer")
    
    # Validate storage_id
    if 'storage_id' in data and data['storage_id'] is not None:
        try:
            storage_id = int(data['storage_id'])
            if storage_id <= 0:
                errors.append("Storage ID must be a positive integer")
        except (ValueError, TypeError):
            errors.append("Storage ID must be a valid integer")
    
    return errors


def validate_email(email: str) -> bool:
    """Validate email address format"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Validate phone number format (supports various formats)"""
    if not phone:
        return False
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (8-15 digits)
    return 8 <= len(digits) <= 15


def validate_positive_decimal(value: Any, max_value: Optional[Decimal] = None) -> bool:
    """Validate that a value is a positive decimal"""
    try:
        decimal_value = Decimal(str(value))
        if decimal_value <= 0:
            return False
        if max_value and decimal_value > max_value:
            return False
        return True
    except (InvalidOperation, ValueError, TypeError):
        return False


def validate_date_string(date_str: str, date_format: str = '%Y-%m-%d') -> bool:
    """Validate date string format"""
    try:
        datetime.strptime(date_str, date_format)
        return True
    except ValueError:
        return False


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize string input by stripping whitespace and limiting length"""
    if not value:
        return ''
    
    sanitized = value.strip()
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """Validate file extension against allowed list"""
    if not filename or '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in [ext.lower() for ext in allowed_extensions]