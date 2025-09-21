from datetime import datetime, date
from app import db
from decimal import Decimal
import uuid
from app.utils.datetime_type import CustomDateTime

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'
    
    purchase_order_no = db.Column(db.String(50), primary_key=True)
    supplier_id = db.Column(db.String(50), db.ForeignKey('suppliers.supplier_id'), nullable=False)
    supplier_name = db.Column(db.String(200), nullable=False)
    supplier_address = db.Column(db.Text)
    contact_phone = db.Column(db.String(50))
    contact_person = db.Column(db.String(100))
    supplier_tax_id = db.Column(db.String(20))
    order_date = db.Column(db.Date, default=date.today)
    quotation_no = db.Column(db.String(50))
    delivery_address = db.Column(db.Text)
    creation_date = db.Column(db.Date, default=date.today)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    output_person_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    notes = db.Column(db.Text)
    confirm_purchaser_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    purchase_status = db.Column(
        db.Enum('pending', 'confirmed', 'order_created', 'outputted', 'purchased', 'shipped', 'cancelled', name='purchase_status_enum'),
        nullable=False,
        default='order_created'
    )
    shipping_status = db.Column(
        db.Enum('none', 'not_shipped', 'shipped', 'in_transit', 'customs_clearance', 'expected_arrival', 'arrived', name='shipping_status_enum'),
        default='none'
    )
    shipped_at = db.Column(CustomDateTime)
    eta_date = db.Column(db.Date)
    arrival_date = db.Column(db.Date)
    carrier = db.Column(db.String(100))
    tracking_no = db.Column(db.String(100))
    logistics_note = db.Column(db.Text)
    
    # Enhanced delivery management fields per PRD requirements
    delivery_status = db.Column(
        db.String(20),
        default='not_shipped'
    )
    expected_delivery_date = db.Column(db.Date)
    actual_delivery_date = db.Column(db.Date)
    consolidation_id = db.Column(db.String(50), db.ForeignKey('shipment_consolidations.consolidation_id'))
    remarks = db.Column(db.Text, comment='Logistics tracking numbers and notes')
    status_update_required = db.Column(db.Boolean, default=True, comment='Indicates if mandatory status update is required')
    
    subtotal_int = db.Column(db.Integer, default=0)  # 未稅總額（整數）
    tax_decimal1 = db.Column(db.Numeric(12, 1), default=0)  # 稅額（一位小數）
    grand_total_int = db.Column(db.Integer, default=0)  # 含稅總額（整數）
    
    # Additional fields for billing
    billing_status = db.Column(
        db.Enum('none', 'pending', 'billed', 'paid', name='billing_status_enum'),
        default='none'
    )
    payment_method = db.Column(
        db.Enum('remittance', 'check', 'cash', 'monthly', 'net60', name='payment_method_enum')
    )
    due_date = db.Column(db.Date)
    billed_month = db.Column(db.String(7))  # YYYY-MM
    payment_date = db.Column(db.Date)  # Date when payment was made
    payment_note = db.Column(db.Text)  # Notes about the payment

    created_at = db.Column(CustomDateTime, default=datetime.utcnow)
    updated_at = db.Column(CustomDateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy='dynamic', cascade='all, delete-orphan')
    logistics_events = db.relationship('LogisticsEvent', backref='purchase_order', lazy='dynamic')
    consolidation_pos = db.relationship('ConsolidationPO', backref='purchase_order', lazy='dynamic')
    # Note: creator relationship is defined in User model with backref='creator'
    # output_person and confirm_purchaser relationships are defined here without backrefs to avoid conflicts
    
    def __repr__(self):
        return f'<PurchaseOrder {self.purchase_order_no}>'
    
    @staticmethod
    def generate_po_number():
        """Generate a unique PO number"""
        today = date.today()
        prefix = f"PO{today.strftime('%Y%m%d')}"
        
        # Find the next sequence number for today
        existing = db.session.query(PurchaseOrder).filter(
            PurchaseOrder.purchase_order_no.like(f"{prefix}%")
        ).count()
        
        sequence = existing + 1
        return f"{prefix}{sequence:03d}"
    
    def can_edit(self):
        """Check if the PO can be edited"""
        return self.purchase_status in ('pending', 'order_created')
    
    def can_confirm(self):
        """Check if the PO can be confirmed for purchase"""
        return self.purchase_status in ('pending', 'order_created') and self.items.count() > 0
    
    def confirm_purchase(self, confirmer_id, idempotency_key=None):
        """Confirm the purchase order"""
        if not self.can_confirm():
            raise ValueError("Purchase order cannot be confirmed")
        
        self.purchase_status = 'purchased'
        self.confirm_purchaser_id = confirmer_id
        self.status_update_required = True  # Require mandatory status update after purchase confirmation
        
        # Update all items to purchased status
        for item in self.items:
            if item.line_status == 'order_created':
                item.line_status = 'purchased'
        
        # Update project costs when purchase is confirmed
        self._update_project_costs()
    
    def withdraw(self, reason, withdrawn_by_id):
        """Withdraw the purchase order"""
        if self.purchase_status == 'cancelled':
            raise ValueError("Purchase order is already cancelled")
        
        self.purchase_status = 'cancelled'
        self.notes = f"CANCELLED: {reason}"
        
        # Update all items to cancelled status
        for item in self.items:
            item.line_status = 'cancelled'
            item.updated_at = datetime.utcnow()
    
    def recalculate_totals(self, tax_rate=5.0):
        """Recalculate totals based on current line items"""
        subtotal = sum(item.get_line_subtotal() for item in self.items)
        
        # Convert to integer (rounded)
        self.subtotal_int = int(round(subtotal))
        
        # Calculate tax (1 decimal place)
        tax_amount = subtotal * Decimal(str(tax_rate)) / 100
        self.tax_decimal1 = round(tax_amount, 1)
        
        # Grand total (integer, rounded)
        grand_total = subtotal + tax_amount
        self.grand_total_int = int(round(grand_total))
    
    def update_milestone(self, status, **kwargs):
        """Update shipping milestone"""
        if status not in ['not_shipped', 'shipped', 'in_transit', 'customs_clearance', 'expected_arrival', 'arrived']:
            raise ValueError("Invalid shipping status")
        
        self.shipping_status = status
        
        # Update relevant fields based on status
        if status == 'shipped' and 'shipped_at' in kwargs:
            self.shipped_at = kwargs['shipped_at']
        elif status == 'expected_arrival' and 'eta_date' in kwargs:
            self.eta_date = kwargs['eta_date']
        elif status == 'arrived' and 'arrival_date' in kwargs:
            self.arrival_date = kwargs['arrival_date']
            # Also update all line items
            for item in self.items:
                if item.line_status in ['purchased', 'shipped']:
                    item.line_status = 'arrived'
        
        # Update tracking info if provided
        if 'carrier' in kwargs:
            self.carrier = kwargs['carrier']
        if 'tracking_no' in kwargs:
            self.tracking_no = kwargs['tracking_no']
        if 'note' in kwargs:
            self.logistics_note = kwargs['note']
    
    def is_ready_for_receiving(self):
        """Check if PO is ready for receiving"""
        return self.purchase_status == 'purchased' and self.shipping_status in ['expected_arrival', 'arrived']
    
    # Delivery Management Methods per PRD requirements
    def is_in_delivery_maintenance_list(self):
        """Check if PO belongs in Delivery Maintenance List"""
        # Domestic POs or international POs not in consolidation
        if not hasattr(self, 'supplier') or not self.supplier:
            return False
        
        from app.models.supplier import Supplier
        supplier = Supplier.query.get(self.supplier_id)
        if not supplier:
            return False
            
        # All domestic POs go to delivery maintenance list
        if supplier.supplier_region == 'domestic':
            return True
        
        # International POs only if not in consolidation
        if supplier.supplier_region == 'international':
            return self.consolidation_id is None
        
        return False
    
    def is_in_consolidation_list(self):
        """Check if PO belongs in Consolidation List"""
        # Only international POs in consolidation
        if not hasattr(self, 'supplier') or not self.supplier:
            return False
        
        from app.models.supplier import Supplier
        supplier = Supplier.query.get(self.supplier_id)
        if not supplier:
            return False
            
        return (supplier.supplier_region == 'international' and 
                self.consolidation_id is not None)
    
    def can_update_delivery_status(self):
        """Check if delivery status can be updated"""
        return self.purchase_status == 'purchased'
    
    def update_delivery_status(self, new_status, updated_by_id, expected_date=None, remarks=None):
        """Update delivery status with cascading to items"""
        if not self.can_update_delivery_status():
            raise ValueError("Cannot update delivery status - PO not in purchased state")
        
        # Validate status transitions based on supplier region
        from app.models.supplier import Supplier
        supplier = Supplier.query.get(self.supplier_id)
        
        if supplier and supplier.supplier_region == 'domestic':
            # Domestic: 3-stage flow (not_shipped -> shipped -> delivered)
            valid_statuses = ['not_shipped', 'shipped', 'delivered']
        else:
            # International: 6-stage flow
            valid_statuses = ['not_shipped', 'shipped', 'foreign_customs', 'taiwan_customs', 'in_transit', 'delivered']
        
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid delivery status for {supplier.supplier_region if supplier else 'unknown'} supplier")
        
        # Update delivery status
        old_status = self.delivery_status
        self.delivery_status = new_status
        
        # Update expected delivery date if provided
        if expected_date:
            self.expected_delivery_date = expected_date
        
        # Update actual delivery date when delivered
        if new_status == 'delivered':
            self.actual_delivery_date = date.today()
        
        # Update remarks and cascade to items
        if remarks is not None:
            self.update_remarks(remarks, updated_by_id)
        
        # Mark status update as completed
        if old_status == 'not_shipped' and new_status == 'shipped':
            self.status_update_required = False
        
        # Cascade status to items
        for item in self.items:
            item.delivery_status = new_status
            if remarks is not None:
                item.remarks = remarks
    
    def can_be_consolidated(self):
        """Check if PO can be added to consolidation"""
        from app.models.supplier import Supplier
        supplier = Supplier.query.get(self.supplier_id)
        
        return (supplier and 
                supplier.supplier_region == 'international' and
                self.delivery_status == 'shipped' and
                self.consolidation_id is None)
    
    def update_remarks(self, new_remarks, updated_by_id):
        """Update remarks and cascade to items"""
        old_remarks = self.remarks
        self.remarks = new_remarks
        
        # Cascade to items
        for item in self.items:
            item.remarks = new_remarks
        
        # Create audit trail
        from app.models.logistics import RemarksHistory
        history = RemarksHistory(
            purchase_order_no=self.purchase_order_no,
            consolidation_id=self.consolidation_id,
            previous_remarks=old_remarks,
            new_remarks=new_remarks,
            updated_by=updated_by_id
        )
        db.session.add(history)
    
    def can_export(self):
        """Check if the PO can be exported"""
        # Allow export for all statuses per user requirement
        return True
    
    def record_export(self, export_person_id):
        """Record export operation and handle status transitions"""
        if not self.can_export():
            raise ValueError(f"Purchase order with status '{self.purchase_status}' cannot be exported")
        
        from datetime import datetime
        
        # Handle status transitions based on current status
        previous_status = self.purchase_status
        if self.purchase_status == 'pending':
            # First export from pending -> order_created
            self.purchase_status = 'order_created'
            self.output_person_id = export_person_id
        elif self.purchase_status == 'order_created':
            # Second export from order_created -> outputted
            self.purchase_status = 'outputted'
            self.output_person_id = export_person_id
        
        return {
            'previous_status': previous_status,
            'current_status': self.purchase_status,
            'export_person_id': export_person_id,
            'export_timestamp': datetime.utcnow().isoformat()
        }
    
    def to_dict(self, include_user_details=False):
        def safe_isoformat(value):
            """Safely convert datetime/date to ISO format string"""
            if value is None:
                return None
            if isinstance(value, str):
                return value  # Already a string, return as-is
            if hasattr(value, 'isoformat'):
                return value.isoformat()
            return str(value)  # Fallback to string conversion

        result = {
            'purchase_order_no': self.purchase_order_no,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'supplier_address': self.supplier_address,
            'contact_phone': self.contact_phone,
            'contact_person': self.contact_person,
            'supplier_tax_id': self.supplier_tax_id,
            'order_date': safe_isoformat(self.order_date),
            'quotation_no': self.quotation_no,
            'delivery_address': self.delivery_address,
            'creation_date': safe_isoformat(self.creation_date),
            'creator_id': self.creator_id,
            'output_person_id': self.output_person_id,
            'notes': self.notes,
            'confirm_purchaser_id': self.confirm_purchaser_id,
            'purchase_status': self.purchase_status,
            'shipping_status': self.shipping_status,
            'shipped_at': safe_isoformat(self.shipped_at),
            'eta_date': safe_isoformat(self.eta_date),
            'arrival_date': safe_isoformat(self.arrival_date),
            'carrier': self.carrier,
            'tracking_no': self.tracking_no,
            'logistics_note': self.logistics_note,
            'delivery_status': self.delivery_status,
            'expected_delivery_date': safe_isoformat(self.expected_delivery_date),
            'actual_delivery_date': safe_isoformat(self.actual_delivery_date),
            'consolidation_id': self.consolidation_id,
            'remarks': self.remarks,
            'status_update_required': self.status_update_required,
            'subtotal_int': self.subtotal_int,
            'tax_decimal1': float(self.tax_decimal1) if self.tax_decimal1 else 0.0,
            'grand_total_int': self.grand_total_int,
            'billing_status': self.billing_status,
            'payment_method': self.payment_method,
            'due_date': safe_isoformat(self.due_date),
            'billed_month': self.billed_month,
            'payment_date': safe_isoformat(self.payment_date),
            'payment_note': self.payment_note,
            'created_at': safe_isoformat(self.created_at),
            'updated_at': safe_isoformat(self.updated_at),
        }
        
        # Include user details if requested
        if include_user_details:
            if self.creator:
                result['creator_name'] = self.creator.chinese_name
                result['creator_username'] = self.creator.username
            if self.output_person:
                result['output_person_name'] = self.output_person.chinese_name
                result['output_person_username'] = self.output_person.username
                result['output_timestamp'] = safe_isoformat(self.updated_at) if self.purchase_status in ['outputted', 'purchased'] and self.updated_at else None
            if self.confirm_purchaser:
                result['confirm_purchaser_name'] = self.confirm_purchaser.chinese_name
                result['confirm_purchaser_username'] = self.confirm_purchaser.username
                # Look for confirmed_at attribute (added in confirm purchase endpoint)
                confirmed_value = getattr(self, 'confirmed_at', self.updated_at)
                result['confirm_timestamp'] = safe_isoformat(confirmed_value) if hasattr(self, 'confirmed_at') or (self.purchase_status == 'purchased' and self.updated_at) else None
        
        return result

class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_items'
    
    detail_id = db.Column(db.Integer, primary_key=True)
    purchase_order_no = db.Column(db.String(50), db.ForeignKey('purchase_orders.purchase_order_no'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    item_quantity = db.Column(db.Numeric(10, 2), nullable=False)
    item_unit = db.Column(db.String(20), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    item_specification = db.Column(db.Text)
    item_model = db.Column(db.String(100))
    line_status = db.Column(
        db.Enum('active', 'cancelled', 'completed', name='line_status_enum'),
        nullable=False,
        default='active'
    )
    line_subtotal_int = db.Column(db.Integer, default=0)  # 小計（整數）
    source_request_order_no = db.Column(db.String(50))
    source_detail_id = db.Column(db.Integer, db.ForeignKey('request_order_items.detail_id'))
    
    # Delivery management fields for items
    delivery_status = db.Column(
        db.String(20),
        default='not_shipped'
    )
    remarks = db.Column(db.Text, comment='Cascaded logistics tracking information from PO or consolidation')
    
    created_at = db.Column(CustomDateTime, default=datetime.utcnow)
    updated_at = db.Column(CustomDateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PurchaseOrderItem {self.detail_id}: {self.item_name}>'
    
    def get_line_subtotal(self):
        """Calculate line subtotal"""
        if self.unit_price and self.item_quantity:
            return self.unit_price * self.item_quantity
        return Decimal('0')
    
    def update_line_subtotal(self):
        """Update the line subtotal (integer)"""
        subtotal = self.get_line_subtotal()
        self.line_subtotal_int = int(round(subtotal))
    
    def mark_purchased(self):
        """Mark item as purchased"""
        if self.line_status == 'order_created':
            self.line_status = 'purchased'
    
    def mark_shipped(self):
        """Mark item as shipped"""
        if self.line_status == 'purchased':
            self.line_status = 'shipped'
    
    def mark_arrived(self):
        """Mark item as arrived"""
        if self.line_status in ['purchased', 'shipped']:
            self.line_status = 'arrived'
    
    def to_dict(self):
        result = {
            'detail_id': self.detail_id,
            'purchase_order_no': self.purchase_order_no,
            'item_name': self.item_name,
            'item_quantity': float(self.item_quantity),
            'item_unit': self.item_unit,
            'unit_price': float(self.unit_price),
            'item_specification': self.item_specification,
            'item_model': self.item_model,
            'line_status': self.line_status,
            'delivery_status': self.delivery_status,
            'remarks': self.remarks,
            'line_subtotal_int': self.line_subtotal_int,
            'line_subtotal': float(self.get_line_subtotal()),
            'source_request_order_no': self.source_request_order_no,
            'source_detail_id': self.source_detail_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Add request_info if source requisition exists
        if self.source_request_item:
            request_order = self.source_request_item.request_order
            if request_order:
                result['request_info'] = {
                    'request_number': request_order.request_order_no,
                    'requester': request_order.requester.chinese_name if request_order.requester else 'N/A'
                }
        else:
            result['request_info'] = {
                'request_number': self.source_request_order_no or 'N/A',
                'requester': 'N/A'
            }
        
        return result

    def to_detailed_dict(self):
        """Detailed dictionary with item details for accounting invoice management"""
        result = self.to_dict(include_user_details=True)

        # Add detailed items information
        result['items'] = [item.to_dict() for item in self.items]

        # Calculate items summary
        result['item_count'] = self.items.count()
        result['total_quantity'] = sum(float(item.item_quantity) for item in self.items)

        # Add supplier payment terms if available
        if hasattr(self, 'supplier') and self.supplier:
            result['supplier_payment_terms'] = self.supplier.payment_terms
            result['supplier_region'] = self.supplier.supplier_region

        return result

    def _update_project_costs(self):
        """Update project costs when purchase order is confirmed"""
        try:
            from app.models.request_order import RequestOrder
            from app.models.project import Project, ProjectSupplierExpenditure
            
            # Find all request orders linked to items in this purchase order
            affected_projects = set()
            
            for item in self.items:
                if item.source_request_order_no:
                    request_order = RequestOrder.query.filter_by(
                        request_order_no=item.source_request_order_no
                    ).first()
                    
                    if request_order and request_order.project_id:
                        affected_projects.add(request_order.project_id)
            
            # Update costs for each affected project
            for project_id in affected_projects:
                project = Project.query.get(project_id)
                if project:
                    # Calculate total expenditure for this supplier in this project
                    total_amount = db.session.query(
                        db.func.sum(PurchaseOrderItem.unit_price * PurchaseOrderItem.item_quantity)
                    ).join(PurchaseOrder, PurchaseOrderItem.purchase_order_no == PurchaseOrder.purchase_order_no)\
                     .join(RequestOrder, PurchaseOrderItem.source_request_order_no == RequestOrder.request_order_no)\
                     .filter(
                         RequestOrder.project_id == project_id,
                         PurchaseOrder.supplier_id == self.supplier_id,
                         PurchaseOrder.purchase_status == 'purchased'
                     ).scalar() or 0
                    
                    # Update or create supplier expenditure record
                    expenditure = ProjectSupplierExpenditure.query.filter_by(
                        project_id=project_id,
                        supplier_id=self.supplier_id
                    ).first()
                    
                    if expenditure:
                        expenditure.expenditure_amount = total_amount
                        expenditure.updated_at = datetime.utcnow()
                    else:
                        expenditure = ProjectSupplierExpenditure(
                            project_id=project_id,
                            supplier_id=self.supplier_id,
                            expenditure_amount=total_amount
                        )
                        db.session.add(expenditure)
                    
                    # Recalculate project total expenditure
                    project.calculate_total_expenditure()
                    db.session.commit()
                    
        except Exception as e:
            # Log error but don't break the purchase confirmation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating project costs for PO {self.purchase_order_no}: {str(e)}")
            # Re-raise in development, but catch in production
            if db.app and db.app.config.get('DEBUG', False):
                raise