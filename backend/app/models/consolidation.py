from datetime import datetime, date
from app import db

class ShipmentConsolidation(db.Model):
    __tablename__ = 'shipment_consolidations'
    
    consolidation_id = db.Column(db.String(50), primary_key=True)
    consolidation_name = db.Column(db.String(200), nullable=False)
    # Only international consolidations per PRD
    logistics_status = db.Column(
        db.Enum('shipped', 'foreign_customs', 'taiwan_customs', 'in_transit', 'delivered', name='consolidation_logistics_status_enum'),
        nullable=False,
        default='shipped'
    )
    expected_delivery_date = db.Column(db.Date)
    actual_delivery_date = db.Column(db.Date)
    total_weight = db.Column(db.Numeric(10,2))
    total_volume = db.Column(db.Numeric(10,2))
    carrier = db.Column(db.String(100))
    tracking_number = db.Column(db.String(100))
    customs_declaration_no = db.Column(db.String(100))
    logistics_notes = db.Column(db.Text)
    remarks = db.Column(db.Text, comment='Logistics tracking numbers and notes')
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    consolidation_pos = db.relationship('ConsolidationPO', backref='consolidation', lazy='dynamic', cascade='all, delete-orphan')
    logistics_events = db.relationship('LogisticsEvent', backref='consolidation', lazy='dynamic')
    
    def __repr__(self):
        return f'<ShipmentConsolidation {self.consolidation_id}: {self.consolidation_name}>'
    
    @staticmethod
    def generate_consolidation_id():
        """Generate a unique consolidation ID"""
        today = date.today()
        prefix = f"CONS{today.strftime('%Y%m%d')}"
        
        existing = db.session.query(ShipmentConsolidation).filter(
            ShipmentConsolidation.consolidation_id.like(f"{prefix}%")
        ).count()
        
        sequence = existing + 1
        return f"{prefix}{sequence:03d}"
    
    @staticmethod
    def generate_consolidation_name():
        """Generate a unique consolidation name"""
        today = date.today()
        return f"Consolidation_{today.strftime('%Y%m%d')}_001"
    
    def can_add_po(self):
        """Check if POs can be added to this consolidation"""
        # Only allow adding POs when consolidation is in shipped status (per PRD)
        return self.logistics_status == 'shipped'
    
    def add_po(self, purchase_order_no):
        """Add a PO to this consolidation and move from Delivery Maintenance to Consolidation List"""
        if not self.can_add_po():
            raise ValueError("Cannot add PO to this consolidation")
        
        # Check if PO is already in another consolidation
        existing = ConsolidationPO.query.filter_by(purchase_order_no=purchase_order_no).first()
        if existing:
            raise ValueError("PO is already in a consolidation")
        
        # Validate PO can be consolidated
        from app.models.purchase_order import PurchaseOrder
        po = PurchaseOrder.query.get(purchase_order_no)
        if not po:
            raise ValueError("Purchase order not found")
        
        if not po.can_be_consolidated():
            raise ValueError("Purchase order cannot be consolidated")
        
        # Add to consolidation
        consolidation_po = ConsolidationPO(
            consolidation_id=self.consolidation_id,
            purchase_order_no=purchase_order_no
        )
        db.session.add(consolidation_po)
        
        # Update PO consolidation reference
        po.consolidation_id = self.consolidation_id
    
    def remove_po(self, purchase_order_no):
        """Remove a PO from this consolidation - per PRD, once consolidated, POs cannot be removed"""
        raise ValueError("POs cannot be removed from consolidation once added per business rules")
    
    def update_logistics_status(self, new_status, updated_by_id, expected_date=None, remarks=None, **kwargs):
        """Update consolidation logistics status and cascade to all POs and items"""
        # Validate 5-stage international flow
        valid_statuses = ['shipped', 'foreign_customs', 'taiwan_customs', 'in_transit', 'delivered']
        
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid logistics status: {new_status}")
        
        old_status = self.logistics_status
        self.logistics_status = new_status
        
        # Update expected delivery date if provided
        if expected_date:
            self.expected_delivery_date = expected_date
        
        # Update actual delivery date when delivered
        if new_status == 'delivered':
            self.actual_delivery_date = date.today()
        
        # Update carrier and tracking info if provided
        if 'carrier' in kwargs:
            self.carrier = kwargs['carrier']
        if 'tracking_number' in kwargs:
            self.tracking_number = kwargs['tracking_number']
        if 'customs_declaration_no' in kwargs:
            self.customs_declaration_no = kwargs['customs_declaration_no']
        if 'logistics_notes' in kwargs:
            self.logistics_notes = kwargs['logistics_notes']
        
        # Update remarks and cascade
        if remarks is not None:
            self.update_remarks(remarks, updated_by_id)
        
        # Cascade status to all POs and their items
        for consolidation_po in self.consolidation_pos:
            po = consolidation_po.purchase_order
            if po:
                po.delivery_status = new_status
                if remarks is not None:
                    po.remarks = remarks
                
                # Cascade to items
                for item in po.items:
                    item.delivery_status = new_status
                    if remarks is not None:
                        item.remarks = remarks
    
    def update_remarks(self, new_remarks, updated_by_id):
        """Update remarks and cascade to all POs and items"""
        old_remarks = self.remarks
        self.remarks = new_remarks
        
        # Cascade to all POs and their items
        for consolidation_po in self.consolidation_pos:
            po = consolidation_po.purchase_order
            if po:
                po.remarks = new_remarks
                for item in po.items:
                    item.remarks = new_remarks
        
        # Create audit trail
        from app.models.logistics import RemarksHistory
        history = RemarksHistory(
            consolidation_id=self.consolidation_id,
            previous_remarks=old_remarks,
            new_remarks=new_remarks,
            updated_by=updated_by_id
        )
        db.session.add(history)
    
    def get_po_count(self):
        """Get number of POs in this consolidation"""
        return self.consolidation_pos.count()
    
    def to_dict(self):
        return {
            'consolidation_id': self.consolidation_id,
            'consolidation_name': self.consolidation_name,
            'logistics_status': self.logistics_status,
            'expected_delivery_date': self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            'actual_delivery_date': self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            'total_weight': float(self.total_weight) if self.total_weight else None,
            'total_volume': float(self.total_volume) if self.total_volume else None,
            'carrier': self.carrier,
            'tracking_number': self.tracking_number,
            'customs_declaration_no': self.customs_declaration_no,
            'logistics_notes': self.logistics_notes,
            'remarks': self.remarks,
            'created_by': self.created_by,
            'po_count': self.get_po_count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ConsolidationPO(db.Model):
    __tablename__ = 'consolidation_pos'
    
    id = db.Column(db.Integer, primary_key=True)
    consolidation_id = db.Column(db.String(50), db.ForeignKey('shipment_consolidations.consolidation_id'), nullable=False)
    purchase_order_no = db.Column(db.String(50), db.ForeignKey('purchase_orders.purchase_order_no'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure unique combination
    __table_args__ = (db.UniqueConstraint('consolidation_id', 'purchase_order_no'),)
    
    def __repr__(self):
        return f'<ConsolidationPO {self.consolidation_id} - {self.purchase_order_no}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'consolidation_id': self.consolidation_id,
            'purchase_order_no': self.purchase_order_no,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'purchase_order': self.purchase_order.to_dict() if self.purchase_order else None
        }