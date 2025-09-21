from datetime import datetime
from app import db
from decimal import Decimal

class Storage(db.Model):
    __tablename__ = 'storages'
    
    storage_id = db.Column(db.String(20), primary_key=True)  # e.g., "Z1-A-3-F-Left"
    area_code = db.Column(db.String(10), nullable=False)     # e.g., "Z1"
    shelf_code = db.Column(db.String(1), nullable=False)     # e.g., "A"
    floor_level = db.Column(db.Integer, nullable=False)      # e.g., 3
    front_back_position = db.Column(db.Integer, nullable=False)  # 1=Front, 2=Back
    left_middle_right_position = db.Column(db.Integer, nullable=False)  # 1=Left, 2=Middle, 3=Right
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    storage_history = db.relationship('StorageHistory', backref='storage', lazy='dynamic')
    
    def __repr__(self):
        return f'<Storage {self.storage_id}>'
    
    @staticmethod
    def generate_storage_id(area_code, shelf_code, floor_level, front_back_position, left_middle_right_position):
        """Generate storage ID based on location components"""
        fb_map = {1: 'F', 2: 'B'}
        lmr_map = {1: 'Left', 2: 'Middle', 3: 'Right'}
        
        fb_str = fb_map.get(front_back_position, 'F')
        lmr_str = lmr_map.get(left_middle_right_position, 'Left')
        
        return f"{area_code}-{shelf_code}-{floor_level}-{fb_str}-{lmr_str}"
    
    @staticmethod
    def create_storage_location(area_code, shelf_code, floor_level, front_back_position, left_middle_right_position):
        """Create a new storage location"""
        storage_id = Storage.generate_storage_id(area_code, shelf_code, floor_level, front_back_position, left_middle_right_position)
        
        # Check if already exists
        existing = Storage.query.get(storage_id)
        if existing:
            return existing
        
        storage = Storage(
            storage_id=storage_id,
            area_code=area_code,
            shelf_code=shelf_code,
            floor_level=floor_level,
            front_back_position=front_back_position,
            left_middle_right_position=left_middle_right_position
        )
        return storage
    
    def get_current_inventory(self):
        """Get current inventory at this storage location"""
        # Calculate in - out for each item
        inventory = db.session.query(
            StorageHistory.item_id,
            StorageHistory.source_no,
            StorageHistory.source_line,
            db.func.sum(
                db.case(
                    (StorageHistory.operation_type == 'in', StorageHistory.quantity),
                    else_=-StorageHistory.quantity
                )
            ).label('current_quantity')
        ).filter(
            StorageHistory.storage_id == self.storage_id
        ).group_by(
            StorageHistory.item_id,
            StorageHistory.source_no,
            StorageHistory.source_line
        ).having(
            db.func.sum(
                db.case(
                    (StorageHistory.operation_type == 'in', StorageHistory.quantity),
                    else_=-StorageHistory.quantity
                )
            ) > 0
        ).all()
        
        return inventory
    
    def to_dict(self):
        return {
            'storage_id': self.storage_id,
            'area_code': self.area_code,
            'shelf_code': self.shelf_code,
            'floor_level': self.floor_level,
            'front_back_position': self.front_back_position,
            'left_middle_right_position': self.left_middle_right_position,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'current_inventory': len(self.get_current_inventory())
        }

class StorageHistory(db.Model):
    __tablename__ = 'storage_history'
    
    history_id = db.Column(db.Integer, primary_key=True)
    storage_id = db.Column(db.String(20), db.ForeignKey('storages.storage_id'), nullable=False)
    item_id = db.Column(db.String(50), nullable=False)  # Could be item name or unique identifier
    operation_type = db.Column(db.Enum('in', 'out', name='operation_type_enum'), nullable=False)
    operation_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    source_type = db.Column(db.String(30))  # 'PO', 'REQUISITION', 'MANUAL', etc.
    source_no = db.Column(db.String(50))    # PO number, requisition number, etc.
    source_line = db.Column(db.Integer)     # Line number in source document
    note = db.Column(db.Text)
    
    # Add foreign key to request order item for traceability
    request_item_id = db.Column(db.Integer, db.ForeignKey('request_order_items.detail_id'))
    
    def __repr__(self):
        return f'<StorageHistory {self.history_id}: {self.operation_type} {self.quantity} {self.item_id}>'
    
    @staticmethod
    def create_in_record(storage_id, item_id, quantity, operator_id, source_type=None, source_no=None, source_line=None, note=None):
        """Create an 'in' operation record"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive for 'in' operations")
        
        record = StorageHistory(
            storage_id=storage_id,
            item_id=item_id,
            operation_type='in',
            quantity=Decimal(str(quantity)),
            operator_id=operator_id,
            source_type=source_type,
            source_no=source_no,
            source_line=source_line,
            note=note
        )
        return record
    
    @staticmethod
    def create_out_record(storage_id, item_id, quantity, operator_id, source_type=None, source_no=None, source_line=None, note=None):
        """Create an 'out' operation record"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive for 'out' operations")
        
        # Check if there's sufficient inventory
        current_qty = StorageHistory.get_current_quantity(storage_id, item_id, source_no, source_line)
        if current_qty < quantity:
            raise ValueError(f"Insufficient inventory. Available: {current_qty}, Requested: {quantity}")
        
        record = StorageHistory(
            storage_id=storage_id,
            item_id=item_id,
            operation_type='out',
            quantity=Decimal(str(quantity)),
            operator_id=operator_id,
            source_type=source_type,
            source_no=source_no,
            source_line=source_line,
            note=note
        )
        return record
    
    @staticmethod
    def get_current_quantity(storage_id, item_id, source_no=None, source_line=None):
        """Get current quantity for a specific item at a storage location"""
        query = db.session.query(
            db.func.sum(
                db.case(
                    (StorageHistory.operation_type == 'in', StorageHistory.quantity),
                    else_=-StorageHistory.quantity
                )
            )
        ).filter(
            StorageHistory.storage_id == storage_id,
            StorageHistory.item_id == item_id
        )
        
        if source_no:
            query = query.filter(StorageHistory.source_no == source_no)
        if source_line is not None:
            query = query.filter(StorageHistory.source_line == source_line)
        
        result = query.scalar()
        return float(result) if result else 0.0
    
    def to_dict(self):
        return {
            'history_id': self.history_id,
            'storage_id': self.storage_id,
            'item_id': self.item_id,
            'operation_type': self.operation_type,
            'operation_date': self.operation_date.isoformat() if self.operation_date else None,
            'operator_id': self.operator_id,
            'quantity': float(self.quantity),
            'source_type': self.source_type,
            'source_no': self.source_no,
            'source_line': self.source_line,
            'note': self.note,
            'request_item_id': self.request_item_id,
            'storage': self.storage.to_dict() if self.storage else None,
            'operator': self.operator.to_dict() if self.operator else None,
            'request_item': self.request_item.to_dict() if self.request_item else None
        }