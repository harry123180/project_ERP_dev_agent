from datetime import datetime
from app import db

class LogisticsEvent(db.Model):
    __tablename__ = 'logistics_events'
    
    event_id = db.Column(db.Integer, primary_key=True)
    scope_type = db.Column(db.Enum('PO', 'CONSOLIDATION', name='scope_type_enum'), nullable=False)
    scope_id = db.Column(db.String(50), nullable=False)  # PO number or consolidation ID
    status = db.Column(
        db.Enum('shipped', 'in_transit', 'customs_clearance', 'expected_arrival', 'arrived', name='logistics_status_enum'),
        nullable=False
    )
    happened_at = db.Column(db.DateTime, nullable=False)
    note = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add foreign keys for proper relationships
    purchase_order_no = db.Column(db.String(50), db.ForeignKey('purchase_orders.purchase_order_no'))
    consolidation_id = db.Column(db.String(50), db.ForeignKey('shipment_consolidations.consolidation_id'))
    
    def __repr__(self):
        return f'<LogisticsEvent {self.event_id}: {self.scope_type} {self.scope_id} - {self.status}>'
    
    @staticmethod
    def create_po_event(purchase_order_no, status, happened_at, note, created_by):
        """Create a logistics event for a PO"""
        event = LogisticsEvent(
            scope_type='PO',
            scope_id=purchase_order_no,
            purchase_order_no=purchase_order_no,
            status=status,
            happened_at=happened_at,
            note=note,
            created_by=created_by
        )
        return event
    
    @staticmethod
    def create_consolidation_event(consolidation_id, status, happened_at, note, created_by):
        """Create a logistics event for a consolidation"""
        event = LogisticsEvent(
            scope_type='CONSOLIDATION',
            scope_id=consolidation_id,
            consolidation_id=consolidation_id,
            status=status,
            happened_at=happened_at,
            note=note,
            created_by=created_by
        )
        return event
    
    def to_dict(self):
        return {
            'event_id': self.event_id,
            'scope_type': self.scope_type,
            'scope_id': self.scope_id,
            'status': self.status,
            'happened_at': self.happened_at.isoformat() if self.happened_at else None,
            'note': self.note,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by_user': self.created_by_user.to_dict() if self.created_by_user else None
        }

class RemarksHistory(db.Model):
    """Tracks history of remarks changes for audit purposes"""
    __tablename__ = 'remarks_history'
    
    history_id = db.Column(db.Integer, primary_key=True)
    purchase_order_no = db.Column(db.String(50), db.ForeignKey('purchase_orders.purchase_order_no'))
    consolidation_id = db.Column(db.String(50), db.ForeignKey('shipment_consolidations.consolidation_id'))
    item_id = db.Column(db.Integer, db.ForeignKey('purchase_order_items.detail_id'))
    previous_remarks = db.Column(db.Text)
    new_remarks = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RemarksHistory {self.history_id}>'
    
    def to_dict(self):
        return {
            'history_id': self.history_id,
            'purchase_order_no': self.purchase_order_no,
            'consolidation_id': self.consolidation_id,
            'item_id': self.item_id,
            'previous_remarks': self.previous_remarks,
            'new_remarks': self.new_remarks,
            'updated_by': self.updated_by,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }