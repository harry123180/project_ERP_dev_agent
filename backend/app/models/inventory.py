from datetime import datetime
from app import db
from decimal import Decimal
from sqlalchemy import func


class InventoryBatch(db.Model):
    """
    Represents a batch of inventory items from a specific source (PO).
    Supports PM's requirement for batch management by source PO number.
    """
    __tablename__ = 'inventory_batches'
    
    batch_id = db.Column(db.Integer, primary_key=True)
    
    # Item identification
    item_name = db.Column(db.String(200), nullable=False, index=True)
    item_specification = db.Column(db.Text)
    unit = db.Column(db.String(20), nullable=False)
    # usage_type = db.Column(db.String(20), default='general')  # general, daily, project, production, maintenance, office, it
    
    # Batch source tracking (PM requirement: track by source PO)
    source_type = db.Column(db.String(20), nullable=False)  # 'PO', 'MANUAL', 'TRANSFER'
    source_po_number = db.Column(db.String(50), nullable=False, index=True)
    source_line_number = db.Column(db.Integer)
    
    # Batch quantities
    original_quantity = db.Column(db.Numeric(10, 2), nullable=False)
    current_quantity = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Batch status and lifecycle
    batch_status = db.Column(db.String(20), default='active')  # active, depleted, transferred
    
    # Receiving information
    received_date = db.Column(db.Date, nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    receiver_name = db.Column(db.String(50))
    
    # Storage information
    primary_storage_id = db.Column(db.String(20), db.ForeignKey('storages.storage_id'))
    
    # Quality and compliance
    lot_number = db.Column(db.String(50))
    expiry_date = db.Column(db.Date)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    receiver = db.relationship('User', backref='received_batches')
    primary_storage = db.relationship('Storage', backref='inventory_batches')
    storage_distributions = db.relationship('InventoryBatchStorage', backref='batch', cascade='all, delete-orphan')
    movement_history = db.relationship('InventoryMovement', backref='batch', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<InventoryBatch {self.batch_id}: {self.item_name} from {self.source_po_number}>'
    
    @staticmethod
    def create_from_receiving(receiving_record):
        """Create inventory batch from receiving record"""
        batch = InventoryBatch(
            item_name=receiving_record.item_name,
            item_specification=receiving_record.item_specification,
            unit=receiving_record.unit,
            source_type='PO',
            source_po_number=receiving_record.purchase_order_no,
            source_line_number=receiving_record.po_item_detail_id,
            original_quantity=receiving_record.quantity_received,
            current_quantity=receiving_record.quantity_received,
            received_date=receiving_record.received_at.date(),
            receiver_id=receiving_record.receiver_id,
            receiver_name=receiving_record.receiver_name
        )
        return batch
    
    def allocate_to_storage(self, storage_id, quantity):
        """Allocate a portion of the batch to a storage location"""
        # Check if we're allocating more than what's unallocated
        allocated_quantity = db.session.query(func.sum(InventoryBatchStorage.quantity)).filter_by(
            batch_id=self.batch_id
        ).scalar() or 0
        unallocated_quantity = float(self.current_quantity) - float(allocated_quantity)
        
        if quantity > unallocated_quantity:
            raise ValueError(f"Cannot allocate {quantity}, only {unallocated_quantity} unallocated")
        
        # Find existing storage allocation or create new one
        storage_allocation = InventoryBatchStorage.query.filter_by(
            batch_id=self.batch_id,
            storage_id=storage_id
        ).first()
        
        if storage_allocation:
            storage_allocation.quantity += Decimal(str(quantity))
        else:
            storage_allocation = InventoryBatchStorage(
                batch_id=self.batch_id,
                storage_id=storage_id,
                quantity=Decimal(str(quantity))
            )
            db.session.add(storage_allocation)
        
        # Note: We don't reduce current_quantity here - it represents the total batch quantity
        # current_quantity should only be reduced when items are issued/consumed, not when allocated
        
        return storage_allocation
    
    def get_storage_distribution(self):
        """Get current storage distribution for this batch"""
        return db.session.query(
            InventoryBatchStorage.storage_id,
            InventoryBatchStorage.quantity
        ).filter_by(batch_id=self.batch_id).all()
    
    def to_dict(self):
        return {
            'batch_id': self.batch_id,
            'item_name': self.item_name,
            'item_specification': self.item_specification,
            'unit': self.unit,
            # 'usage_type': self.usage_type,
            'source_type': self.source_type,
            'source_po_number': self.source_po_number,
            'source_line_number': self.source_line_number,
            'original_quantity': float(self.original_quantity),
            'current_quantity': float(self.current_quantity),
            'batch_status': self.batch_status,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'receiver_id': self.receiver_id,
            'receiver_name': self.receiver_name,
            'primary_storage_id': self.primary_storage_id,
            'lot_number': self.lot_number,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class InventoryBatchStorage(db.Model):
    """
    Tracks how inventory batches are distributed across storage locations.
    Supports PM's requirement for storage distribution view.
    """
    __tablename__ = 'inventory_batch_storage'
    
    allocation_id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('inventory_batches.batch_id'), nullable=False)
    storage_id = db.Column(db.String(20), db.ForeignKey('storages.storage_id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    storage = db.relationship('Storage', backref='batch_allocations')
    
    def __repr__(self):
        return f'<InventoryBatchStorage {self.allocation_id}: {self.quantity} at {self.storage_id}>'
    
    def to_dict(self):
        return {
            'allocation_id': self.allocation_id,
            'batch_id': self.batch_id,
            'storage_id': self.storage_id,
            'quantity': float(self.quantity),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'storage': self.storage.to_dict() if self.storage else None
        }


class InventoryMovement(db.Model):
    """
    Enhanced inventory movement tracking with batch support.
    Supports PM's requirement for movement history timeline.
    """
    __tablename__ = 'inventory_movements'
    
    movement_id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('inventory_batches.batch_id'), nullable=False)
    
    # Movement details
    movement_type = db.Column(db.String(20), nullable=False)  # 'in', 'out', 'transfer', 'adjustment'
    movement_subtype = db.Column(db.String(30))  # 'receiving', 'issue', 'transfer_in', 'transfer_out', 'count_adjustment'
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Storage information
    from_storage_id = db.Column(db.String(20), db.ForeignKey('storages.storage_id'))
    to_storage_id = db.Column(db.String(20), db.ForeignKey('storages.storage_id'))
    
    # Transaction details
    operator_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    movement_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Reference information
    reference_type = db.Column(db.String(30))  # 'PO', 'REQUISITION', 'TRANSFER_ORDER', 'ADJUSTMENT'
    reference_number = db.Column(db.String(50))
    reference_line = db.Column(db.Integer)
    
    # Additional information
    reason_code = db.Column(db.String(20))  # 'normal', 'damage', 'expiry', 'count_adjustment'
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    operator = db.relationship('User', backref='inventory_movements')
    from_storage = db.relationship('Storage', foreign_keys=[from_storage_id])
    to_storage = db.relationship('Storage', foreign_keys=[to_storage_id])
    
    def __repr__(self):
        return f'<InventoryMovement {self.movement_id}: {self.movement_type} {self.quantity}>'
    
    @staticmethod
    def create_receiving_movement(batch_id, storage_id, quantity, operator_id, po_number, notes=None):
        """Create movement record for receiving"""
        movement = InventoryMovement(
            batch_id=batch_id,
            movement_type='in',
            movement_subtype='receiving',
            quantity=Decimal(str(quantity)),
            to_storage_id=storage_id,
            operator_id=operator_id,
            reference_type='PO',
            reference_number=po_number,
            reason_code='normal',
            notes=notes
        )
        return movement
    
    @staticmethod
    def create_issue_movement(batch_id, storage_id, quantity, operator_id, requisition_number=None, notes=None):
        """Create movement record for issuing"""
        movement = InventoryMovement(
            batch_id=batch_id,
            movement_type='out',
            movement_subtype='issue',
            quantity=Decimal(str(quantity)),
            from_storage_id=storage_id,
            operator_id=operator_id,
            reference_type='REQUISITION',
            reference_number=requisition_number,
            reason_code='normal',
            notes=notes
        )
        return movement
    
    @staticmethod
    def create_transfer_movement(batch_id, from_storage_id, to_storage_id, quantity, operator_id, transfer_number=None, notes=None):
        """Create movement record for storage transfer"""
        movement = InventoryMovement(
            batch_id=batch_id,
            movement_type='transfer',
            movement_subtype='transfer',
            quantity=Decimal(str(quantity)),
            from_storage_id=from_storage_id,
            to_storage_id=to_storage_id,
            operator_id=operator_id,
            reference_type='TRANSFER_ORDER',
            reference_number=transfer_number,
            reason_code='normal',
            notes=notes
        )
        return movement
    
    def to_dict(self):
        return {
            'movement_id': self.movement_id,
            'batch_id': self.batch_id,
            'movement_type': self.movement_type,
            'movement_subtype': self.movement_subtype,
            'quantity': float(self.quantity),
            'from_storage_id': self.from_storage_id,
            'to_storage_id': self.to_storage_id,
            'operator_id': self.operator_id,
            'movement_date': self.movement_date.isoformat() if self.movement_date else None,
            'reference_type': self.reference_type,
            'reference_number': self.reference_number,
            'reference_line': self.reference_line,
            'reason_code': self.reason_code,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'operator': self.operator.to_dict() if self.operator else None,
            'from_storage': self.from_storage.to_dict() if self.from_storage else None,
            'to_storage': self.to_storage.to_dict() if self.to_storage else None
        }


class InventoryItem(db.Model):
    """
    Inventory items model for PostgreSQL.
    Supports PM's requirement for item grouping and batch count display.
    """
    __tablename__ = 'inventory_items'

    # Match the actual PostgreSQL table structure
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50))
    item_name = db.Column(db.String(200), nullable=False)
    item_specification = db.Column(db.Text)
    item_category = db.Column(db.String(100))
    description = db.Column(db.Text)
    item_quantity = db.Column(db.Numeric(10, 2))
    item_unit = db.Column(db.String(20))
    quantity = db.Column(db.Numeric(10, 2))
    unit = db.Column(db.String(20))
    unit_price = db.Column(db.Numeric(10, 2))
    min_stock = db.Column(db.Numeric(10, 2))
    max_stock = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    
    @staticmethod
    def get_inventory_summary():
        """Get inventory summary with batch grouping (Phase 1 implementation)"""
        # For now, we'll use a query instead of a view
        return db.session.query(
            func.concat(InventoryBatch.item_name, '|', func.coalesce(InventoryBatch.item_specification, '')).label('item_key'),
            InventoryBatch.item_name,
            InventoryBatch.item_specification,
            InventoryBatch.unit,
            func.sum(InventoryBatch.current_quantity).label('total_quantity'),
            func.count(InventoryBatch.batch_id).label('batch_count'),
            func.count(func.distinct(InventoryBatchStorage.storage_id)).label('storage_location_count'),
            func.max(InventoryBatch.received_date).label('last_received_date')
        ).outerjoin(InventoryBatchStorage).filter(
            InventoryBatch.current_quantity > 0
        ).group_by(
            InventoryBatch.item_name,
            InventoryBatch.item_specification,
            InventoryBatch.unit
        ).all()
    
    def to_dict(self):
        return {
            'item_key': self.item_key,
            'item_name': self.item_name,
            'item_specification': self.item_specification,
            'unit': self.unit,
            'total_quantity': float(self.total_quantity) if self.total_quantity else 0,
            'batch_count': self.batch_count or 0,
            'storage_location_count': self.storage_location_count or 0,
            'last_received_date': self.last_received_date.isoformat() if self.last_received_date else None,
            'last_issued_date': self.last_issued_date.isoformat() if self.last_issued_date else None
        }