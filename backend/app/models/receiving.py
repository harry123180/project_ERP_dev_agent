from datetime import datetime
from app import db
from decimal import Decimal


class ReceivingRecord(db.Model):
    __tablename__ = 'receiving_records'
    
    receiving_id = db.Column(db.Integer, primary_key=True)
    purchase_order_no = db.Column(db.String(50), db.ForeignKey('purchase_orders.purchase_order_no'), nullable=False)
    po_item_detail_id = db.Column(db.Integer, db.ForeignKey('purchase_order_items.detail_id'), nullable=False)
    requisition_number = db.Column(db.String(50), nullable=False)
    consolidation_number = db.Column(db.String(50))
    
    # Item information
    item_name = db.Column(db.String(200), nullable=False)
    item_specification = db.Column(db.Text)
    quantity_shipped = db.Column(db.Numeric(10, 2), nullable=False)
    quantity_received = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    
    # Receiving information
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    receiver_name = db.Column(db.String(50), nullable=False)  # Store name for history
    received_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # Status tracking
    receiving_status = db.Column(db.String(20), default='received_pending_storage')  # received_pending_storage, stored
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    purchase_order = db.relationship('PurchaseOrder', backref='receiving_records')
    purchase_order_item = db.relationship('PurchaseOrderItem', backref='receiving_record')
    receiver = db.relationship('User', backref='received_items')
    
    def __repr__(self):
        return f'<ReceivingRecord {self.receiving_id}: {self.item_name} from {self.purchase_order_no}>'
    
    @staticmethod
    def create_receiving_record(po_no, po_item_detail_id, requisition_number, item_name,
                               quantity_received, unit, receiver_id, receiver_name,
                               consolidation_number=None, notes=None, item_specification=None,
                               received_at=None):
        """Create a new receiving record"""
        from datetime import datetime

        # Create and return a new ReceivingRecord instance
        record = ReceivingRecord(
            purchase_order_no=po_no,
            po_item_detail_id=po_item_detail_id,
            requisition_number=requisition_number,
            consolidation_number=consolidation_number,
            item_name=item_name,
            item_specification=item_specification,
            quantity_shipped=quantity_received,  # Assuming shipped quantity equals received for now
            quantity_received=quantity_received,
            unit=unit,
            receiver_id=receiver_id,
            receiver_name=receiver_name,
            received_at=received_at or datetime.utcnow(),
            notes=notes,
            receiving_status='received'
        )
        return record
    
    def to_dict(self):
        return {
            'receiving_id': self.receiving_id,
            'purchase_order_no': self.purchase_order_no,
            'po_item_detail_id': self.po_item_detail_id,
            'requisition_number': self.requisition_number,
            'consolidation_number': self.consolidation_number,
            'item_name': self.item_name,
            'item_specification': self.item_specification,
            'quantity_shipped': float(self.quantity_shipped),
            'quantity_received': float(self.quantity_received),
            'unit': self.unit,
            'receiver_id': self.receiver_id,
            'receiver_name': self.receiver_name,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'notes': self.notes,
            'receiving_status': self.receiving_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_pending_storage_item(self):
        """Convert receiving record to pending storage item format"""
        return {
            'id': self.receiving_id,
            'item_name': self.item_name,
            'quantity': float(self.quantity_received),
            'unit': self.unit,
            'source_po_number': self.purchase_order_no,
            'arrival_date': self.received_at.strftime('%Y-%m-%d') if self.received_at else None,
            'receiver': self.receiver_name,
            'suggested_location': None,  # Will be determined later
            'requisition_number': self.requisition_number,
            'consolidation_number': self.consolidation_number,
            'specification': self.item_specification or ''
        }


class PendingStorageItem(db.Model):
    __tablename__ = 'pending_storage_items'
    
    pending_id = db.Column(db.Integer, primary_key=True)
    receiving_record_id = db.Column(db.Integer, db.ForeignKey('receiving_records.receiving_id'), nullable=False)
    
    # Item information (denormalized for easy querying)
    item_name = db.Column(db.String(200), nullable=False)
    item_specification = db.Column(db.Text)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    
    # Source tracking
    source_po_number = db.Column(db.String(50), nullable=False)
    requisition_number = db.Column(db.String(50), nullable=False)
    consolidation_number = db.Column(db.String(50))
    
    # Storage information
    suggested_storage_id = db.Column(db.String(20), db.ForeignKey('storages.storage_id'))
    assigned_storage_id = db.Column(db.String(20), db.ForeignKey('storages.storage_id'))
    
    # Status and timing
    storage_status = db.Column(db.String(20), default='pending')  # pending, assigned, stored
    arrival_date = db.Column(db.Date, nullable=False)
    receiver = db.Column(db.String(50), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_at = db.Column(db.DateTime)
    stored_at = db.Column(db.DateTime)
    
    # Relationships
    receiving_record = db.relationship('ReceivingRecord', backref='pending_storage_item')
    suggested_storage = db.relationship('Storage', foreign_keys=[suggested_storage_id])
    assigned_storage = db.relationship('Storage', foreign_keys=[assigned_storage_id])
    
    def __repr__(self):
        return f'<PendingStorageItem {self.pending_id}: {self.item_name} from {self.source_po_number}>'
    
    @staticmethod
    def create_from_receiving_record(receiving_record):
        """Create pending storage item from receiving record"""
        item = PendingStorageItem(
            receiving_record_id=receiving_record.receiving_id,
            item_name=receiving_record.item_name,
            item_specification=receiving_record.item_specification,
            quantity=receiving_record.quantity_received,
            unit=receiving_record.unit,
            source_po_number=receiving_record.purchase_order_no,
            requisition_number=receiving_record.requisition_number,
            consolidation_number=receiving_record.consolidation_number,
            arrival_date=receiving_record.received_at.date() if receiving_record.received_at else None,
            receiver=receiving_record.receiver_name
        )
        return item
    
    def assign_storage(self, storage_id):
        """Assign storage location to pending item"""
        self.assigned_storage_id = storage_id
        self.storage_status = 'assigned'
        self.assigned_at = datetime.utcnow()
        
    def mark_as_stored(self):
        """Mark item as successfully stored"""
        self.storage_status = 'stored'
        self.stored_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.pending_id,
            'receiving_record_id': self.receiving_record_id,
            'item_name': self.item_name,
            'item_specification': self.item_specification,
            'quantity': float(self.quantity),
            'unit': self.unit,
            'source_po_number': self.source_po_number,
            'requisition_number': self.requisition_number,
            'consolidation_number': self.consolidation_number,
            'suggested_storage_id': self.suggested_storage_id,
            'assigned_storage_id': self.assigned_storage_id,
            'storage_status': self.storage_status,
            'arrival_date': self.arrival_date.isoformat() if self.arrival_date else None,
            'receiver': self.receiver,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'stored_at': self.stored_at.isoformat() if self.stored_at else None
        }