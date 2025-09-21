from datetime import datetime, date
from app import db
from decimal import Decimal

class RequestOrder(db.Model):
    __tablename__ = 'request_orders'
    
    # Valid enum values for validation
    VALID_USAGE_TYPES = ['daily', 'project', '消耗品']
    VALID_ORDER_STATUSES = ['draft', 'submitted', 'reviewed', 'cancelled']
    
    request_order_no = db.Column(db.String(50), primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    requester_name = db.Column(db.String(100), nullable=False)
    usage_type = db.Column(db.String(20), nullable=False)  # Changed from Enum to String for SQLite compatibility
    project_id = db.Column(db.String(50), db.ForeignKey('projects.project_id'))
    submit_date = db.Column(db.Date, default=date.today)
    order_status = db.Column(db.String(20), nullable=False, default='draft')  # Changed from Enum to String for SQLite compatibility
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('RequestOrderItem', backref='request_order', lazy='dynamic', cascade='all, delete-orphan')
    project = db.relationship('Project', backref='request_orders')
    # Note: requester relationship is defined in User model with backref='requester'
    
    def __repr__(self):
        return f'<RequestOrder {self.request_order_no}>'
    
    def can_edit(self):
        """Check if the request order can be edited"""
        return self.order_status == 'draft'
    
    def can_submit(self):
        """Check if the request order can be submitted"""
        return self.order_status == 'draft' and self.items.count() > 0
    
    def submit(self):
        """Submit the request order for review"""
        if not self.can_submit():
            raise ValueError("Request order cannot be submitted")
        self.order_status = 'submitted'
        self.submit_date = date.today()
        
        # Update all items to pending_review
        for item in self.items:
            if item.item_status == 'draft':
                item.item_status = 'pending_review'
    
    def reject(self, reason=''):
        """Reject the entire request order"""
        if self.order_status not in ['submitted', 'reviewed']:
            raise ValueError("Request order cannot be rejected")
        
        self.order_status = 'draft'
        # Reset all items to draft
        for item in self.items:
            if item.item_status in ['pending_review', 'approved', 'questioned']:
                item.item_status = 'draft'
                item.status_note = reason
    
    def get_summary(self):
        """Get summary statistics of the request order"""
        items = self.items.all()
        total_items = len(items)
        # CRITICAL FIX: Count 'reviewed' items as approved items
        approved_items = len([i for i in items if i.item_status in ['approved', 'reviewed']])
        rejected_items = len([i for i in items if i.item_status == 'rejected'])
        questioned_items = len([i for i in items if i.item_status == 'questioned'])
        # CRITICAL FIX: Include 'submitted' status as pending
        pending_items = len([i for i in items if i.item_status in ['pending_review', 'submitted']])
        
        return {
            'total_items': total_items,
            'approved_items': approved_items,
            'rejected_items': rejected_items,
            'questioned_items': questioned_items,
            'pending_items': pending_items
        }
    
    def update_status_after_review(self):
        """Update order status based on item review status - CRITICAL FIX VERSION"""
        print(f"[STATUS_UPDATE] Checking status for {self.request_order_no}")
        print(f"[STATUS_UPDATE] Current status: {self.order_status}")
        
        if self.order_status != 'submitted':
            print(f"[STATUS_UPDATE] Skipping - order not in submitted status")
            return  # Only update if currently submitted
            
        summary = self.get_summary()
        total_items = summary['total_items']
        pending_items = summary['pending_items']
        approved_items = summary['approved_items']
        rejected_items = summary['rejected_items']
        questioned_items = summary['questioned_items']
        
        print(f"[STATUS_UPDATE] Summary: total={total_items}, pending={pending_items}, approved={approved_items}, rejected={rejected_items}, questioned={questioned_items}")
        
        # If all items have been reviewed (no pending items), update to reviewed
        if total_items > 0 and pending_items == 0:
            print(f"[STATUS_UPDATE] All items reviewed, updating to 'reviewed'")
            old_status = self.order_status
            self.order_status = 'reviewed'
            self.updated_at = datetime.utcnow()
            print(f"[STATUS_UPDATE] Status updated from '{old_status}' to '{self.order_status}'")
            
            # CRITICAL FIX: Remove the db.session.commit() call to let the API endpoint handle transactions
            # The calling API endpoint will handle the database commit
            print(f"[STATUS_UPDATE] Status change prepared, letting API endpoint handle database commit")
        else:
            print(f"[STATUS_UPDATE] Not all items reviewed yet - keeping current status")
    
    def cancel(self, reason, cancelled_by_id):
        """Cancel the request order"""
        if self.order_status == 'cancelled':
            raise ValueError("Request order is already cancelled")
        
        if self.order_status == 'draft':
            # For draft status, we call it "delete" in UI, but it's actually cancel
            self.order_status = 'cancelled'
        else:
            # For submitted/reviewed status, it's withdrawal
            self.order_status = 'cancelled'
        
        # Cancel all items
        for item in self.items:
            item.item_status = 'cancelled'
            item.status_note = f"CANCELLED: {reason}"
            item.updated_at = datetime.utcnow()
    
    def to_dict(self):
        # Get the latest chinese_name from the user relationship if available
        display_name = self.requester_name  # Fallback to stored name
        if self.requester:
            # Use the latest chinese_name from the User model
            display_name = self.requester.chinese_name or self.requester.username or self.requester_name

        return {
            'request_order_no': self.request_order_no,
            'requester_id': self.requester_id,
            'requester_name': display_name,  # Use the latest chinese_name
            'usage_type': self.usage_type,
            'project_id': self.project_id,
            'submit_date': self.submit_date.isoformat() if self.submit_date else None,
            'order_status': self.order_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'summary': self.get_summary()
        }

class RequestOrderItem(db.Model):
    __tablename__ = 'request_order_items'
    
    # Valid enum values for validation
    VALID_ITEM_STATUSES = [
        'draft', 'pending_review', 'approved', 'rejected', 'questioned', 
        'unavailable', 'order_created', 'purchased', 'shipped', 'arrived', 
        'warehoused', 'issued', 'cancelled'
    ]
    VALID_ACCEPTANCE_STATUSES = ['pending_acceptance', 'accepted']
    
    detail_id = db.Column(db.Integer, primary_key=True)
    request_order_no = db.Column(db.String(50), db.ForeignKey('request_orders.request_order_no'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    item_quantity = db.Column(db.Numeric(10, 2), nullable=False)
    item_unit = db.Column(db.String(20), nullable=False)
    item_specification = db.Column(db.Text)
    item_description = db.Column(db.Text)
    item_category = db.Column(db.String(10), db.ForeignKey('item_categories.category_code'))
    item_status = db.Column(db.String(20), nullable=False, default='draft')  # Changed from Enum to String
    acceptance_status = db.Column(db.String(20), default='pending_acceptance')  # Changed from Enum to String
    supplier_id = db.Column(db.String(50), db.ForeignKey('suppliers.supplier_id'))
    unit_price = db.Column(db.Numeric(10, 2))
    material_serial_no = db.Column(db.String(50))
    status_note = db.Column(db.Text)
    needs_acceptance = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    purchase_order_items = db.relationship('PurchaseOrderItem', backref='source_request_item', lazy='dynamic')
    storage_history = db.relationship('StorageHistory', backref='request_item', lazy='dynamic')
    
    def __repr__(self):
        return f'<RequestOrderItem {self.detail_id}: {self.item_name}>'
    
    def can_approve(self):
        """Check if the item can be approved"""
        # CRITICAL FIX: Allow approval of 'submitted' status items
        return self.item_status in ['pending_review', 'questioned', 'submitted']
    
    def approve(self, supplier_id, unit_price, approver_note=''):
        """Approve the request order item"""
        if not self.can_approve():
            raise ValueError("Item cannot be approved")
        
        self.item_status = 'approved'
        self.supplier_id = supplier_id
        self.unit_price = Decimal(str(unit_price))
        self.status_note = approver_note
        
    def question(self, reason):
        """Mark the item as questioned"""
        # CRITICAL FIX: Handle already-processed items gracefully
        if self.item_status == 'questioned':
            # Item is already questioned - just update the reason
            self.status_note = reason
            return
        elif self.item_status in ['approved', 'rejected']:
            raise ValueError(f"Item is already {self.item_status} and cannot be questioned")
        elif self.item_status not in ['pending_review']:
            raise ValueError(f"Item with status '{self.item_status}' cannot be questioned")
        
        self.item_status = 'questioned'
        self.status_note = reason
    
    def reject(self, reason):
        """Reject the item"""
        # CRITICAL FIX: Handle already-processed items gracefully
        if self.item_status == 'rejected':
            # Item is already rejected - just update the reason
            self.status_note = reason
            return
        elif self.item_status == 'approved':
            raise ValueError("Item is already approved and cannot be rejected")
        elif self.item_status not in ['pending_review', 'questioned']:
            raise ValueError(f"Item with status '{self.item_status}' cannot be rejected")
        
        self.item_status = 'rejected'
        self.status_note = reason
    
    def mark_unavailable(self, reason):
        """Mark the item as unavailable"""
        if self.item_status not in ['pending_review', 'approved']:
            raise ValueError("Item cannot be marked as unavailable")
        
        self.item_status = 'unavailable'
        self.status_note = reason
    
    def get_subtotal(self):
        """Calculate subtotal for the item"""
        if self.unit_price and self.item_quantity:
            return self.unit_price * self.item_quantity
        return Decimal('0')
    
    def get_storage_location(self):
        """Get current storage location for this item"""
        # Get the latest storage 'in' record for this item
        from app.models.storage import StorageHistory
        latest_storage = StorageHistory.query.filter_by(
            request_item_id=self.detail_id,
            operation_type='in'
        ).order_by(StorageHistory.operation_date.desc()).first()
        
        if latest_storage and latest_storage.storage:
            return latest_storage.storage.storage_id
        return None
    
    def is_warehoused(self):
        """Check if the item has been warehoused (has storage location)"""
        return self.get_storage_location() is not None
    
    def to_dict(self):
        return {
            'detail_id': self.detail_id,
            'request_order_no': self.request_order_no,
            'item_name': self.item_name,
            'item_quantity': float(self.item_quantity),
            'item_unit': self.item_unit,
            'item_specification': self.item_specification,
            'item_description': self.item_description,
            'item_category': self.item_category,
            'item_status': self.item_status,
            'acceptance_status': self.acceptance_status,
            'supplier_id': self.supplier_id,
            'unit_price': float(self.unit_price) if self.unit_price else None,
            'material_serial_no': self.material_serial_no,
            'status_note': self.status_note,
            'needs_acceptance': self.needs_acceptance,
            'subtotal': float(self.get_subtotal()),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'supplier': self.supplier.to_summary_dict() if self.supplier else None,
            'category_info': self.category.to_dict() if self.category else None,
            'storage_location': self.get_storage_location(),
            'is_warehoused': self.is_warehoused()
        }