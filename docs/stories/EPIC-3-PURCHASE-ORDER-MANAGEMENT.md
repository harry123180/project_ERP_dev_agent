# Epic 3: Purchase Order Management
**Epic ID**: ERP-E03  
**Priority**: P0 (Critical)  
**Story Points**: 131  
**Status**: Draft  

## Epic Description
Implement a comprehensive purchase order management system that automatically generates POs from approved requisitions, manages supplier relationships, tracks order status through delivery, and provides complete lifecycle management with professional document generation and supplier communication.

## Business Value
- **Automation**: Automatically group approved requisitions by supplier into optimal purchase orders
- **Efficiency**: Reduce PO creation time by 70% through automation
- **Accuracy**: Eliminate manual transcription errors in PO generation
- **Supplier Relations**: Streamline supplier communication with professional PO documents
- **Cost Control**: Enable better spend tracking and supplier performance monitoring

## User Personas
- **Primary**: Procurement Specialists (PO creation/management), Procurement Managers (PO approval)
- **Secondary**: Engineers (PO status tracking), Warehouse (delivery confirmation), Accountants (financial tracking)

---

## Story 3.1: Automated Purchase Order Generation
**Story ID**: ERP-E03-S01  
**Title**: Generate Purchase Orders from Approved Requisitions  
**Priority**: P0  
**Story Points**: 25  

### User Story
**As a** Procurement Specialist  
**I want to** automatically generate purchase orders from approved requisitions  
**So that** I can efficiently convert approved requests into supplier orders with accurate pricing and delivery information  

### Background & Context
When requisitions are approved, the system must intelligently group items by supplier to create optimal purchase orders. Each PO must include accurate pricing, delivery terms, tax calculations, and professional formatting for supplier communication.

### Acceptance Criteria
**AC1**: Given approved requisitions exist, when I access the PO generation interface, then I can see all approved items grouped by supplier with options to customize grouping

**AC2**: Given I select items for PO generation, when I create the PO, then the system generates a unique PO number (PO-YYYYMMDD-XXX format) and populates all supplier information

**AC3**: Given I am creating a PO, when I review the order details, then I can see accurate calculations for subtotal, tax rate (5% default), tax amount, and total amount with ability to adjust pricing

**AC4**: Given I generate a PO, when the creation completes, then the system creates a professional PDF document with company branding and all order details

**AC5**: Given a PO is created, when I save it, then all related requisition items are marked as "PO Created" and linked to the purchase order

**AC6**: Given a PO is generated, when I review it, then I can set delivery address, expected delivery date, and special terms before finalizing

### Technical Implementation Notes

#### API Endpoints Required
```
GET /api/v1/purchase-orders/generate-candidates    # Get approved items ready for PO
POST /api/v1/purchase-orders                       # Create new PO
PUT /api/v1/purchase-orders/{id}                   # Update PO details
GET /api/v1/purchase-orders/{id}                   # Get PO details
POST /api/v1/purchase-orders/{id}/finalize         # Finalize and send PO
GET /api/v1/purchase-orders/{id}/pdf               # Generate PO PDF
```

#### Database Changes
```sql
-- Purchase Orders table
CREATE TABLE purchase_orders (
    id SERIAL PRIMARY KEY,
    po_number VARCHAR(20) UNIQUE NOT NULL,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (
        status IN ('Draft', 'Sent', 'Acknowledged', 'Shipped', 'Partially Received', 'Completed', 'Cancelled')
    ),
    subtotal DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    tax_rate DECIMAL(5,4) DEFAULT 0.05,
    tax_amount DECIMAL(12,2) DEFAULT 0.00,
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'USD',
    delivery_address TEXT,
    delivery_contact_name VARCHAR(255),
    delivery_contact_phone VARCHAR(50),
    expected_delivery_date DATE,
    special_terms TEXT,
    payment_terms VARCHAR(100),
    created_by INTEGER NOT NULL REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    sent_at TIMESTAMP,
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Purchase Order Items table
CREATE TABLE purchase_order_items (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    requisition_item_id INTEGER NOT NULL REFERENCES requisition_items(id),
    item_sequence INTEGER NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    description TEXT,
    specifications TEXT,
    quantity DECIMAL(10,3) NOT NULL CHECK (quantity > 0),
    unit VARCHAR(50) DEFAULT 'pcs',
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
    total_price DECIMAL(12,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    expected_delivery_date DATE,
    status VARCHAR(20) DEFAULT 'Ordered' CHECK (
        status IN ('Ordered', 'Acknowledged', 'Shipped', 'Partially Received', 'Received', 'Cancelled')
    ),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Link requisition items to POs
ALTER TABLE requisition_items ADD COLUMN purchase_order_id INTEGER REFERENCES purchase_orders(id);
ALTER TABLE requisition_items ADD COLUMN po_created_at TIMESTAMP;

-- Indexes for performance
CREATE INDEX idx_po_supplier_status ON purchase_orders(supplier_id, status);
CREATE INDEX idx_po_created_date ON purchase_orders(created_at DESC);
CREATE INDEX idx_po_items_po_id ON purchase_order_items(purchase_order_id);
CREATE INDEX idx_po_items_req_item ON purchase_order_items(requisition_item_id);
```

#### PO Generation Algorithm
```python
class PurchaseOrderGenerationService:
    def get_po_candidates(self, user_id: int):
        """Get approved requisition items ready for PO creation"""
        approved_items = db.session.query(RequisitionItem)\
            .join(Requisition)\
            .filter(
                Requisition.status == 'Approved',
                RequisitionItem.purchase_order_id.is_(None)
            )\
            .all()
        
        # Group by supplier based on item mapping
        grouped_items = self.group_items_by_supplier(approved_items)
        
        return {
            'candidates': grouped_items,
            'total_suppliers': len(grouped_items),
            'total_items': len(approved_items),
            'estimated_total': sum(item.estimated_total_price for item in approved_items)
        }
    
    def generate_po(self, supplier_id: int, item_ids: List[int], po_details: dict):
        """Generate a new purchase order"""
        # Create PO number
        po_number = self.generate_po_number()
        
        # Get supplier details
        supplier = Supplier.query.get_or_404(supplier_id)
        
        # Calculate totals
        items = RequisitionItem.query.filter(RequisitionItem.id.in_(item_ids)).all()
        subtotal = sum(item.estimated_total_price for item in items)
        tax_rate = po_details.get('tax_rate', 0.05)
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount
        
        # Create purchase order
        po = PurchaseOrder(
            po_number=po_number,
            supplier_id=supplier_id,
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_amount=total_amount,
            delivery_address=po_details.get('delivery_address'),
            expected_delivery_date=po_details.get('expected_delivery_date'),
            special_terms=po_details.get('special_terms'),
            payment_terms=supplier.payment_terms,
            created_by=current_user.id
        )
        
        db.session.add(po)
        db.session.flush()  # Get PO ID
        
        # Create PO items and link requisition items
        for sequence, item in enumerate(items, 1):
            po_item = PurchaseOrderItem(
                purchase_order_id=po.id,
                requisition_item_id=item.id,
                item_sequence=sequence,
                item_name=item.item_name,
                description=item.description,
                specifications=item.specifications,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=item.estimated_unit_price
            )
            db.session.add(po_item)
            
            # Link requisition item to PO
            item.purchase_order_id = po.id
            item.po_created_at = datetime.utcnow()
        
        db.session.commit()
        
        # Generate PDF document
        self.generate_po_pdf(po.id)
        
        return po
    
    def generate_po_number(self):
        """Generate unique PO number in format PO-YYYYMMDD-XXX"""
        today = datetime.now().strftime('%Y%m%d')
        count = PurchaseOrder.query.filter(
            PurchaseOrder.po_number.like(f'PO-{today}-%')
        ).count()
        return f'PO-{today}-{count + 1:03d}'
```

#### PDF Generation
```python
class POPDFGenerator:
    def generate_po_pdf(self, po_id: int):
        """Generate professional PO PDF document"""
        po = PurchaseOrder.query.get_or_404(po_id)
        
        # Use ReportLab or similar for PDF generation
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Header with company logo
        story.append(self.create_header())
        
        # PO details section
        story.append(self.create_po_details_section(po))
        
        # Supplier information
        story.append(self.create_supplier_section(po.supplier))
        
        # Items table
        story.append(self.create_items_table(po.items))
        
        # Totals section
        story.append(self.create_totals_section(po))
        
        # Terms and conditions
        story.append(self.create_terms_section(po))
        
        doc.build(story)
        
        # Save PDF to file system
        pdf_path = f"po_documents/{po.po_number}.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(buffer.getvalue())
        
        return pdf_path
```

### Test Scenarios
1. **Candidate Generation**: Test grouping approved items by supplier
2. **PO Creation**: Test complete PO generation workflow
3. **Pricing Calculations**: Test subtotal, tax, and total calculations
4. **PDF Generation**: Test professional PDF document creation
5. **Item Linking**: Test proper linking of requisition items to POs
6. **Number Generation**: Test unique PO number generation
7. **Validation**: Test data validation and error handling
8. **Concurrent Creation**: Test handling of simultaneous PO creation

### Dependencies
- Approved requisitions from Epic 2
- Supplier management system
- PDF generation library (ReportLab)
- File storage system for PO documents

**Story Points Breakdown**: Backend (15) + PDF Generation (5) + Frontend (3) + Testing (2) = 25

---

## Story 3.2: Supplier Management Integration
**Story ID**: ERP-E03-S02  
**Title**: Comprehensive Supplier Database Management  
**Priority**: P0  
**Story Points**: 21  

### User Story
**As a** Procurement Specialist  
**I want to** manage supplier information and performance data  
**So that** I can make informed decisions when creating purchase orders and maintain good supplier relationships  

### Background & Context
The supplier database is critical for PO generation and supplier performance tracking. It must store complete supplier profiles including contact information, payment terms, performance ratings, and communication history.

### Acceptance Criteria
**AC1**: Given I need to add a new supplier, when I create a supplier profile, then I can enter complete information: company name, contact person, phone, email, address, tax ID, and banking details

**AC2**: Given I am managing suppliers, when I view the supplier list, then I can see supplier classification (domestic/international), payment terms, active status, and performance ratings

**AC3**: Given I am creating a PO, when I select a supplier, then the system auto-populates payment terms, delivery address preferences, and contact information

**AC4**: Given I need to track supplier performance, when I view a supplier's profile, then I can see order history, delivery performance, quality ratings, and communication notes

**AC5**: Given I want to maintain supplier relationships, when I access supplier details, then I can add notes, update contact information, and set preferred supplier status

**AC6**: Given suppliers need to be organized, when I search suppliers, then I can filter by status (active/inactive), classification, location, and performance rating

### Technical Implementation Notes

#### API Endpoints Required
```
GET /api/v1/suppliers                        # List suppliers with filtering
POST /api/v1/suppliers                       # Create new supplier
PUT /api/v1/suppliers/{id}                   # Update supplier details
DELETE /api/v1/suppliers/{id}                # Deactivate supplier
GET /api/v1/suppliers/{id}/performance       # Get supplier performance metrics
POST /api/v1/suppliers/{id}/notes           # Add supplier note
GET /api/v1/suppliers/search                # Search suppliers with autocomplete
```

#### Database Changes
```sql
-- Main suppliers table
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    supplier_code VARCHAR(20) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(255),
    
    -- Address information
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state_province VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    
    -- Business details
    tax_id VARCHAR(50),
    business_registration VARCHAR(50),
    classification VARCHAR(20) CHECK (classification IN ('Domestic', 'International')),
    
    -- Financial information
    payment_terms VARCHAR(100) DEFAULT '30 days',
    currency VARCHAR(3) DEFAULT 'USD',
    bank_name VARCHAR(255),
    bank_account VARCHAR(100),
    bank_routing VARCHAR(50),
    
    -- Status and preferences
    is_active BOOLEAN DEFAULT TRUE,
    is_preferred BOOLEAN DEFAULT FALSE,
    credit_limit DECIMAL(15,2),
    
    -- Performance tracking
    performance_rating DECIMAL(3,2) CHECK (performance_rating >= 0 AND performance_rating <= 5),
    total_orders INTEGER DEFAULT 0,
    total_order_value DECIMAL(15,2) DEFAULT 0.00,
    average_delivery_days DECIMAL(5,2),
    on_time_delivery_rate DECIMAL(5,4), -- Percentage as decimal (0.95 = 95%)
    
    -- Metadata
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supplier notes and communication history
CREATE TABLE supplier_notes (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    note_type VARCHAR(50) DEFAULT 'General' CHECK (
        note_type IN ('General', 'Quality Issue', 'Delivery Issue', 'Price Change', 'Contact Update')
    ),
    note_title VARCHAR(255),
    note_content TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT TRUE,
    priority VARCHAR(20) DEFAULT 'Normal' CHECK (priority IN ('Low', 'Normal', 'High', 'Urgent')),
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supplier categories for better organization
CREATE TABLE supplier_categories (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE supplier_category_mapping (
    supplier_id INTEGER REFERENCES suppliers(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES supplier_categories(id) ON DELETE CASCADE,
    PRIMARY KEY (supplier_id, category_id)
);

-- Indexes for performance
CREATE INDEX idx_suppliers_active ON suppliers(is_active);
CREATE INDEX idx_suppliers_classification ON suppliers(classification);
CREATE INDEX idx_suppliers_performance ON suppliers(performance_rating DESC) WHERE is_active = TRUE;
CREATE INDEX idx_suppliers_name ON suppliers(company_name);
CREATE INDEX idx_supplier_notes_supplier ON supplier_notes(supplier_id, created_at DESC);

-- Generate supplier codes automatically
CREATE SEQUENCE supplier_code_seq START 1;
```

#### Supplier Performance Calculation
```python
class SupplierPerformanceService:
    def calculate_performance_metrics(self, supplier_id: int):
        """Calculate and update supplier performance metrics"""
        supplier = Supplier.query.get_or_404(supplier_id)
        
        # Get all completed POs for this supplier
        completed_pos = PurchaseOrder.query.filter(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.status == 'Completed'
        ).all()
        
        if not completed_pos:
            return None
        
        # Calculate metrics
        total_orders = len(completed_pos)
        total_value = sum(po.total_amount for po in completed_pos)
        
        # Delivery performance
        on_time_deliveries = 0
        total_delivery_days = 0
        
        for po in completed_pos:
            delivery_items = PurchaseOrderItem.query.filter(
                PurchaseOrderItem.purchase_order_id == po.id,
                PurchaseOrderItem.status == 'Received'
            ).all()
            
            for item in delivery_items:
                if item.expected_delivery_date and item.received_date:
                    delivery_delay = (item.received_date - item.expected_delivery_date).days
                    total_delivery_days += max(0, delivery_delay)
                    
                    if delivery_delay <= 0:  # On time or early
                        on_time_deliveries += 1
        
        on_time_rate = on_time_deliveries / len([item for po in completed_pos for item in po.items]) if completed_pos else 0
        avg_delivery_days = total_delivery_days / len([item for po in completed_pos for item in po.items]) if completed_pos else 0
        
        # Update supplier metrics
        supplier.total_orders = total_orders
        supplier.total_order_value = total_value
        supplier.on_time_delivery_rate = on_time_rate
        supplier.average_delivery_days = avg_delivery_days
        
        # Calculate overall performance rating (1-5 scale)
        performance_score = self.calculate_performance_score(
            on_time_rate, avg_delivery_days, total_orders
        )
        supplier.performance_rating = performance_score
        
        db.session.commit()
        
        return {
            'total_orders': total_orders,
            'total_value': total_value,
            'on_time_rate': on_time_rate,
            'avg_delivery_days': avg_delivery_days,
            'performance_rating': performance_score
        }
    
    def calculate_performance_score(self, on_time_rate: float, avg_delay: float, order_count: int) -> float:
        """Calculate 1-5 performance score"""
        score = 5.0  # Start with perfect score
        
        # Penalize for late deliveries
        if on_time_rate < 0.95:  # Less than 95% on-time
            score -= (0.95 - on_time_rate) * 10  # Up to -0.5 points
        
        # Penalize for average delays
        if avg_delay > 2:  # More than 2 days average delay
            score -= min(avg_delay - 2, 1.0)  # Up to -1 point
        
        # Bonus for high order volume (reliability indicator)
        if order_count > 50:
            score += 0.1
        elif order_count > 100:
            score += 0.2
        
        return max(1.0, min(5.0, round(score, 2)))
```

#### Frontend Components
```vue
<!-- SupplierManagement.vue -->
<template>
  <div class="supplier-management">
    <el-row :gutter="20">
      <el-col :span="16">
        <el-table :data="suppliers" @row-click="selectSupplier">
          <el-table-column prop="supplier_code" label="Code" width="100" />
          <el-table-column prop="company_name" label="Company Name" />
          <el-table-column prop="classification" label="Type" width="120" />
          <el-table-column prop="payment_terms" label="Payment Terms" width="120" />
          <el-table-column label="Performance" width="120">
            <template #default="{ row }">
              <el-rate 
                v-model="row.performance_rating" 
                disabled 
                show-score 
                text-color="#ff9900"
              />
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="Status" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'">
                {{ row.is_active ? 'Active' : 'Inactive' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-col>
      
      <el-col :span="8">
        <el-card title="Supplier Details" v-if="selectedSupplier">
          <SupplierProfile :supplier="selectedSupplier" @update="refreshSuppliers" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
```

### Test Scenarios
1. **Supplier CRUD**: Test creating, reading, updating, deleting suppliers
2. **Performance Calculation**: Test automatic performance metric updates
3. **Search and Filter**: Test supplier search by various criteria
4. **Integration**: Test supplier selection during PO creation
5. **Notes Management**: Test adding and managing supplier notes
6. **Data Validation**: Test supplier information validation rules

### Dependencies
- User authentication system (Epic 1)
- Purchase order integration (Story 3.1)
- Address and contact validation services

**Story Points Breakdown**: Backend (12) + Frontend (6) + Database (2) + Testing (1) = 21

---

## Story 3.3: Purchase Order Lifecycle Management
**Story ID**: ERP-E03-S03  
**Title**: Track Purchase Orders Through Complete Lifecycle  
**Priority**: P0  
**Story Points**: 29  

### User Story
**As a** Procurement Specialist  
**I want to** track purchase orders through their complete lifecycle from creation to delivery  
**So that** I can monitor order progress, manage supplier communications, and ensure timely delivery  

### Background & Context
Purchase orders go through multiple stages: Draft → Sent → Acknowledged → Shipped → Delivered → Completed. Each stage requires specific actions, notifications, and status tracking with full audit trails.

### Acceptance Criteria
**AC1**: Given a purchase order exists, when I view its status, then I can see current stage, expected actions, and progress through the complete lifecycle

**AC2**: Given I need to send a PO to supplier, when I finalize it, then the system sends the PO document via email and updates status to "Sent"

**AC3**: Given a supplier acknowledges a PO, when I receive confirmation, then I can update the status to "Acknowledged" and record acknowledgment details

**AC4**: Given items are shipped, when I receive shipping notification, then I can update item status to "Shipped" with tracking information and expected delivery date

**AC5**: Given I need to modify a PO, when I make changes, then the system tracks all modifications with timestamps and sends updated PO to supplier if needed

**AC6**: Given a PO is partially received, when some items are delivered, then I can mark individual items as received while keeping others in shipped status

**AC7**: Given all items are received, when I confirm completion, then the PO status updates to "Completed" and triggers financial processing

### Technical Implementation Notes

#### API Endpoints Required
```
PUT /api/v1/purchase-orders/{id}/status       # Update PO status
POST /api/v1/purchase-orders/{id}/send        # Send PO to supplier
PUT /api/v1/purchase-orders/{id}/acknowledge  # Record supplier acknowledgment
PUT /api/v1/purchase-orders/{id}/items/{item_id}/ship  # Update item shipping status
PUT /api/v1/purchase-orders/{id}/items/{item_id}/receive # Mark item as received
GET /api/v1/purchase-orders/{id}/history      # Get PO status history
POST /api/v1/purchase-orders/{id}/modify      # Modify PO and track changes
GET /api/v1/purchase-orders/dashboard         # PO dashboard with status summary
```

#### Database Changes
```sql
-- PO status history tracking
CREATE TABLE po_status_history (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    previous_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_by INTEGER NOT NULL REFERENCES users(id),
    change_reason TEXT,
    notes TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PO modifications tracking
CREATE TABLE po_modifications (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    modification_type VARCHAR(50) NOT NULL, -- 'price_change', 'quantity_change', 'item_added', 'item_removed'
    old_values JSONB,
    new_values JSONB,
    reason TEXT,
    modified_by INTEGER NOT NULL REFERENCES users(id),
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supplier acknowledgments
CREATE TABLE po_acknowledgments (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    acknowledged_by VARCHAR(255), -- Supplier contact name
    acknowledgment_method VARCHAR(50), -- 'email', 'phone', 'portal', 'fax'
    confirmed_delivery_date DATE,
    special_notes TEXT,
    acknowledgment_document VARCHAR(500), -- Path to uploaded confirmation document
    recorded_by INTEGER NOT NULL REFERENCES users(id),
    acknowledged_at TIMESTAMP NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shipping information
CREATE TABLE po_shipments (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    shipment_reference VARCHAR(100), -- Supplier's shipment/tracking number
    carrier VARCHAR(100),
    tracking_number VARCHAR(100),
    shipped_date DATE NOT NULL,
    estimated_delivery_date DATE,
    actual_delivery_date DATE,
    shipping_notes TEXT,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Item-level receiving
ALTER TABLE purchase_order_items ADD COLUMN shipped_quantity DECIMAL(10,3) DEFAULT 0;
ALTER TABLE purchase_order_items ADD COLUMN received_quantity DECIMAL(10,3) DEFAULT 0;
ALTER TABLE purchase_order_items ADD COLUMN received_date DATE;
ALTER TABLE purchase_order_items ADD COLUMN received_by INTEGER REFERENCES users(id);
ALTER TABLE purchase_order_items ADD COLUMN shipment_id INTEGER REFERENCES po_shipments(id);
ALTER TABLE purchase_order_items ADD COLUMN quality_notes TEXT;

-- Indexes
CREATE INDEX idx_po_status_history_po ON po_status_history(purchase_order_id, changed_at DESC);
CREATE INDEX idx_po_modifications_po ON po_modifications(purchase_order_id, modified_at DESC);
CREATE INDEX idx_po_acknowledgments_po ON po_acknowledgments(purchase_order_id);
CREATE INDEX idx_po_shipments_po ON po_shipments(purchase_order_id, shipped_date DESC);
```

#### Status Management Service
```python
class PurchaseOrderLifecycleService:
    STATUS_TRANSITIONS = {
        'Draft': ['Sent', 'Cancelled'],
        'Sent': ['Acknowledged', 'Cancelled'],
        'Acknowledged': ['Shipped', 'Cancelled'],
        'Shipped': ['Partially Received', 'Completed', 'Cancelled'],
        'Partially Received': ['Completed', 'Cancelled'],
        'Completed': [],
        'Cancelled': []
    }
    
    def update_po_status(self, po_id: int, new_status: str, user_id: int, reason: str = None, notes: str = None):
        """Update PO status with validation and history tracking"""
        po = PurchaseOrder.query.get_or_404(po_id)
        
        # Validate status transition
        if new_status not in self.STATUS_TRANSITIONS.get(po.status, []):
            raise ValidationError(f"Cannot transition from {po.status} to {new_status}")
        
        # Record status change
        status_history = POStatusHistory(
            purchase_order_id=po_id,
            previous_status=po.status,
            new_status=new_status,
            changed_by=user_id,
            change_reason=reason,
            notes=notes
        )
        
        # Update PO status
        old_status = po.status
        po.status = new_status
        po.updated_at = datetime.utcnow()
        
        # Handle status-specific actions
        if new_status == 'Sent':
            po.sent_at = datetime.utcnow()
            self.send_po_to_supplier(po)
        elif new_status == 'Acknowledged':
            po.acknowledged_at = datetime.utcnow()
        elif new_status == 'Completed':
            self.complete_po_processing(po)
        
        db.session.add(status_history)
        db.session.commit()
        
        # Send notifications
        self.send_status_notification(po, old_status, new_status)
        
        return po
    
    def send_po_to_supplier(self, po: PurchaseOrder):
        """Send PO document to supplier via email"""
        # Generate PDF if not exists
        pdf_path = self.ensure_po_pdf_exists(po.id)
        
        # Send email to supplier
        email_service = EmailService()
        email_service.send_po_to_supplier(
            supplier=po.supplier,
            po=po,
            pdf_path=pdf_path
        )
        
        # Log the communication
        self.log_supplier_communication(po.id, 'email_sent', f'PO sent to {po.supplier.email}')
    
    def acknowledge_po(self, po_id: int, acknowledgment_data: dict, user_id: int):
        """Record supplier acknowledgment"""
        acknowledgment = POAcknowledgment(
            purchase_order_id=po_id,
            acknowledged_by=acknowledgment_data.get('acknowledged_by'),
            acknowledgment_method=acknowledgment_data.get('method', 'email'),
            confirmed_delivery_date=acknowledgment_data.get('delivery_date'),
            special_notes=acknowledgment_data.get('notes'),
            recorded_by=user_id,
            acknowledged_at=acknowledgment_data.get('acknowledged_at', datetime.utcnow())
        )
        
        db.session.add(acknowledgment)
        
        # Update PO status
        self.update_po_status(po_id, 'Acknowledged', user_id, 'Supplier acknowledgment received')
        
        return acknowledgment
    
    def record_shipment(self, po_id: int, shipment_data: dict, user_id: int):
        """Record shipment information"""
        shipment = POShipment(
            purchase_order_id=po_id,
            shipment_reference=shipment_data.get('reference'),
            carrier=shipment_data.get('carrier'),
            tracking_number=shipment_data.get('tracking'),
            shipped_date=shipment_data.get('shipped_date'),
            estimated_delivery_date=shipment_data.get('estimated_delivery'),
            shipping_notes=shipment_data.get('notes'),
            created_by=user_id
        )
        
        db.session.add(shipment)
        db.session.flush()
        
        # Update item statuses
        item_ids = shipment_data.get('item_ids', [])
        if item_ids:
            items = PurchaseOrderItem.query.filter(
                PurchaseOrderItem.id.in_(item_ids)
            ).all()
            
            for item in items:
                item.status = 'Shipped'
                item.shipment_id = shipment.id
                item.shipped_quantity = shipment_data.get('quantities', {}).get(str(item.id), item.quantity)
        
        # Update PO status
        self.update_po_status(po_id, 'Shipped', user_id, f'Items shipped via {shipment.carrier}')
        
        db.session.commit()
        return shipment
    
    def receive_items(self, po_id: int, received_items: List[dict], user_id: int):
        """Record item receipts"""
        po = PurchaseOrder.query.get_or_404(po_id)
        
        for item_data in received_items:
            item_id = item_data['item_id']
            received_qty = item_data['quantity']
            
            po_item = PurchaseOrderItem.query.get(item_id)
            if po_item and po_item.purchase_order_id == po_id:
                po_item.received_quantity += received_qty
                po_item.received_date = item_data.get('received_date', datetime.utcnow().date())
                po_item.received_by = user_id
                po_item.quality_notes = item_data.get('quality_notes')
                
                # Update item status based on received quantity
                if po_item.received_quantity >= po_item.quantity:
                    po_item.status = 'Received'
                else:
                    po_item.status = 'Partially Received'
        
        # Check if all items are fully received
        all_items_received = all(
            item.received_quantity >= item.quantity 
            for item in po.items
        )
        
        if all_items_received:
            new_status = 'Completed'
        else:
            new_status = 'Partially Received'
        
        self.update_po_status(po_id, new_status, user_id, 'Items received')
        
        db.session.commit()
        
        return po
```

#### Email Templates
```html
<!-- PO Email Template -->
<h2>Purchase Order: {{po_number}}</h2>
<p>Dear {{supplier_contact}},</p>

<p>Please find attached our purchase order {{po_number}} dated {{po_date}}.</p>

<p><strong>Order Summary:</strong></p>
<ul>
    <li>Total Items: {{item_count}}</li>
    <li>Total Amount: {{currency}} {{total_amount}}</li>
    <li>Expected Delivery: {{expected_delivery_date}}</li>
</ul>

<p><strong>Delivery Address:</strong><br>
{{delivery_address}}</p>

<p>Please confirm receipt and acknowledge the delivery date at your earliest convenience.</p>

<p>For any questions, please contact {{contact_person}} at {{contact_email}}.</p>

<p>Thank you for your business.</p>

<p>Best regards,<br>
{{company_name}} Procurement Team</p>
```

### Test Scenarios
1. **Status Transitions**: Test all valid status transitions and validations
2. **Email Integration**: Test PO email sending to suppliers
3. **Acknowledgment Recording**: Test supplier acknowledgment workflow
4. **Shipment Tracking**: Test shipment information recording
5. **Item Receiving**: Test partial and complete item receipt processing
6. **History Tracking**: Test complete audit trail functionality
7. **Concurrent Updates**: Test handling of simultaneous status updates
8. **Error Handling**: Test validation and error scenarios

### Dependencies
- Email service integration
- PDF generation system (Story 3.1)
- Supplier management (Story 3.2)
- Notification system

**Story Points Breakdown**: Backend (18) + Frontend (7) + Email Integration (2) + Testing (2) = 29

---

## Story 3.4: Purchase Order Modifications and Version Control
**Story ID**: ERP-E03-S04  
**Title**: Handle Purchase Order Changes and Amendments  
**Priority**: P1  
**Story Points**: 17  

### User Story
**As a** Procurement Specialist  
**I want to** modify purchase orders after they've been sent and track all changes  
**So that** I can handle supplier negotiations, price changes, and quantity adjustments while maintaining audit compliance  

### Background & Context
Purchase orders often need modifications after being sent to suppliers due to price negotiations, quantity changes, specification updates, or delivery date adjustments. All changes must be tracked and communicated to suppliers.

### Acceptance Criteria
**AC1**: Given a sent PO needs modification, when I request changes, then I can modify quantities, prices, delivery dates, or specifications with change tracking

**AC2**: Given I modify a PO, when I save changes, then the system creates a new version, tracks all differences, and requires approval for significant changes

**AC3**: Given a PO is modified, when changes are approved, then the system generates an amendment document and sends it to the supplier

**AC4**: Given I view a PO, when I check its history, then I can see all versions, what changed between versions, who made changes, and when

**AC5**: Given a PO has multiple versions, when I compare versions, then I can see a side-by-side comparison highlighting differences

**AC6**: Given significant changes require approval, when modifications exceed thresholds, then the system routes the amendment for manager approval

### Technical Implementation Notes

#### API Endpoints Required
```
POST /api/v1/purchase-orders/{id}/modify      # Request PO modification
GET /api/v1/purchase-orders/{id}/versions     # Get all PO versions
GET /api/v1/purchase-orders/{id}/compare/{v1}/{v2}  # Compare PO versions
POST /api/v1/purchase-orders/{id}/approve-changes   # Approve modifications
POST /api/v1/purchase-orders/{id}/send-amendment    # Send amendment to supplier
```

#### Database Changes
```sql
-- PO versions table
CREATE TABLE po_versions (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    version_data JSONB NOT NULL, -- Complete PO data snapshot
    change_summary TEXT,
    change_reason VARCHAR(500),
    requires_approval BOOLEAN DEFAULT FALSE,
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(purchase_order_id, version_number)
);

-- Change approval workflow
CREATE TABLE po_change_approvals (
    id SERIAL PRIMARY KEY,
    po_version_id INTEGER NOT NULL REFERENCES po_versions(id) ON DELETE CASCADE,
    approver_id INTEGER NOT NULL REFERENCES users(id),
    approval_status VARCHAR(20) DEFAULT 'Pending' CHECK (
        approval_status IN ('Pending', 'Approved', 'Rejected')
    ),
    approval_comments TEXT,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Amendment documents
CREATE TABLE po_amendments (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    amendment_number INTEGER NOT NULL,
    from_version INTEGER NOT NULL,
    to_version INTEGER NOT NULL,
    amendment_document_path VARCHAR(500),
    sent_to_supplier_at TIMESTAMP,
    supplier_acknowledged_at TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(purchase_order_id, amendment_number)
);

-- Add versioning to main PO table
ALTER TABLE purchase_orders ADD COLUMN current_version INTEGER DEFAULT 1;
ALTER TABLE purchase_orders ADD COLUMN has_amendments BOOLEAN DEFAULT FALSE;

-- Indexes
CREATE INDEX idx_po_versions_po ON po_versions(purchase_order_id, version_number DESC);
CREATE INDEX idx_change_approvals_version ON po_change_approvals(po_version_id, approval_status);
```

#### Version Control Service
```python
class POVersionControlService:
    CHANGE_THRESHOLDS = {
        'price_increase_percent': 0.10,  # 10% price increase requires approval
        'quantity_increase_percent': 0.20,  # 20% quantity increase requires approval
        'total_value_increase': 10000.00,  # $10K total increase requires approval
        'delivery_delay_days': 14  # 14+ day delay requires approval
    }
    
    def create_modification(self, po_id: int, changes: dict, user_id: int, reason: str):
        """Create a new version with modifications"""
        po = PurchaseOrder.query.get_or_404(po_id)
        
        # Create snapshot of current state
        current_snapshot = self.create_po_snapshot(po)
        
        # Apply changes to get new state
        new_po_data = self.apply_changes(current_snapshot, changes)
        
        # Determine if approval is required
        requires_approval = self.requires_approval(current_snapshot, new_po_data)
        
        # Create new version
        new_version = POVersion(
            purchase_order_id=po_id,
            version_number=po.current_version + 1,
            version_data=new_po_data,
            change_summary=self.generate_change_summary(current_snapshot, new_po_data),
            change_reason=reason,
            requires_approval=requires_approval,
            created_by=user_id
        )
        
        db.session.add(new_version)
        
        if requires_approval:
            # Create approval request
            approval = POChangeApproval(
                po_version_id=new_version.id,
                approver_id=self.get_approver_for_po(po_id)
            )
            db.session.add(approval)
            
            # Send notification to approver
            self.notify_approver(approval)
        else:
            # Auto-apply changes
            self.apply_version(po_id, new_version.version_number, user_id)
        
        db.session.commit()
        return new_version
    
    def requires_approval(self, old_data: dict, new_data: dict) -> bool:
        """Determine if changes require approval"""
        old_total = old_data.get('total_amount', 0)
        new_total = new_data.get('total_amount', 0)
        
        # Check total value increase
        if new_total - old_total > self.CHANGE_THRESHOLDS['total_value_increase']:
            return True
        
        # Check percentage increase
        if old_total > 0:
            increase_percent = (new_total - old_total) / old_total
            if increase_percent > self.CHANGE_THRESHOLDS['price_increase_percent']:
                return True
        
        # Check delivery date changes
        old_delivery = old_data.get('expected_delivery_date')
        new_delivery = new_data.get('expected_delivery_date')
        
        if old_delivery and new_delivery:
            delay_days = (datetime.strptime(new_delivery, '%Y-%m-%d') - 
                         datetime.strptime(old_delivery, '%Y-%m-%d')).days
            if delay_days > self.CHANGE_THRESHOLDS['delivery_delay_days']:
                return True
        
        # Check item quantity increases
        old_items = {item['id']: item for item in old_data.get('items', [])}
        new_items = {item['id']: item for item in new_data.get('items', [])}
        
        for item_id, new_item in new_items.items():
            if item_id in old_items:
                old_qty = old_items[item_id].get('quantity', 0)
                new_qty = new_item.get('quantity', 0)
                
                if old_qty > 0:
                    qty_increase = (new_qty - old_qty) / old_qty
                    if qty_increase > self.CHANGE_THRESHOLDS['quantity_increase_percent']:
                        return True
        
        return False
    
    def generate_change_summary(self, old_data: dict, new_data: dict) -> str:
        """Generate human-readable change summary"""
        changes = []
        
        # Price changes
        old_total = old_data.get('total_amount', 0)
        new_total = new_data.get('total_amount', 0)
        if old_total != new_total:
            diff = new_total - old_total
            changes.append(f"Total amount changed by ${diff:,.2f} (${old_total:,.2f} → ${new_total:,.2f})")
        
        # Delivery date changes
        old_delivery = old_data.get('expected_delivery_date')
        new_delivery = new_data.get('expected_delivery_date')
        if old_delivery != new_delivery:
            changes.append(f"Delivery date changed from {old_delivery} to {new_delivery}")
        
        # Item changes
        old_items = {item['id']: item for item in old_data.get('items', [])}
        new_items = {item['id']: item for item in new_data.get('items', [])}
        
        for item_id, new_item in new_items.items():
            if item_id in old_items:
                old_item = old_items[item_id]
                if old_item['quantity'] != new_item['quantity']:
                    changes.append(f"Item {new_item['name']} quantity: {old_item['quantity']} → {new_item['quantity']}")
                if old_item['unit_price'] != new_item['unit_price']:
                    changes.append(f"Item {new_item['name']} price: ${old_item['unit_price']} → ${new_item['unit_price']}")
        
        return '; '.join(changes) if changes else 'Minor changes'
    
    def approve_changes(self, po_version_id: int, approver_id: int, comments: str = None):
        """Approve pending changes"""
        version = POVersion.query.get_or_404(po_version_id)
        
        # Find pending approval
        approval = POChangeApproval.query.filter(
            POChangeApproval.po_version_id == po_version_id,
            POChangeApproval.approval_status == 'Pending'
        ).first()
        
        if not approval:
            raise ValidationError("No pending approval found")
        
        # Update approval
        approval.approval_status = 'Approved'
        approval.approval_comments = comments
        approval.approved_at = datetime.utcnow()
        
        # Update version
        version.approved_by = approver_id
        version.approved_at = datetime.utcnow()
        
        # Apply the version
        self.apply_version(version.purchase_order_id, version.version_number, approver_id)
        
        db.session.commit()
        return approval
```

### Test Scenarios
1. **Version Creation**: Test creating new versions with modifications
2. **Approval Workflow**: Test approval routing for significant changes
3. **Change Detection**: Test automatic detection of change thresholds
4. **Version Comparison**: Test side-by-side version comparisons
5. **Amendment Generation**: Test amendment document creation
6. **History Tracking**: Test complete modification history
7. **Concurrent Modifications**: Test handling of simultaneous changes

### Dependencies
- Purchase order management (Story 3.3)
- Approval workflow system
- Document generation for amendments
- Change notification system

**Story Points Breakdown**: Backend (12) + Frontend (3) + Testing (2) = 17

---

## Story 3.5: Purchase Order Dashboard and Analytics
**Story ID**: ERP-E03-S05  
**Title**: Comprehensive Purchase Order Reporting and Analytics  
**Priority**: P1  
**Story Points**: 21  

### User Story
**As a** Procurement Manager  
**I want to** view comprehensive analytics and dashboards for purchase order activities  
**So that** I can monitor spending patterns, supplier performance, and make data-driven procurement decisions  

### Background & Context
Procurement managers need visibility into spending patterns, supplier performance, order cycle times, and budget compliance. The dashboard should provide both high-level KPIs and detailed drill-down capabilities.

### Acceptance Criteria
**AC1**: Given I access the PO dashboard, when I view the overview, then I can see key metrics: total orders, total spend, average order value, and cycle times for current month and year-to-date

**AC2**: Given I need supplier insights, when I view supplier analytics, then I can see performance ratings, spend by supplier, delivery performance, and order frequency

**AC3**: Given I want to track trends, when I view trend analysis, then I can see spending trends over time, seasonal patterns, and budget vs actual comparisons

**AC4**: Given I need detailed reports, when I generate reports, then I can filter by date range, supplier, category, status, and export to Excel or PDF

**AC5**: Given I manage budgets, when I view budget tracking, then I can see spend by department, category, and project with variance analysis

**AC6**: Given I need alerts, when thresholds are exceeded, then I receive notifications for budget overruns, delayed orders, or performance issues

### Technical Implementation Notes

#### API Endpoints Required
```
GET /api/v1/purchase-orders/dashboard         # Dashboard summary data
GET /api/v1/purchase-orders/analytics/spending # Spending analytics
GET /api/v1/purchase-orders/analytics/suppliers # Supplier performance
GET /api/v1/purchase-orders/analytics/trends   # Trend analysis
POST /api/v1/purchase-orders/reports          # Generate custom reports
GET /api/v1/purchase-orders/budget-tracking   # Budget vs actual tracking
```

#### Analytics Database Views
```sql
-- Monthly spending summary view
CREATE MATERIALIZED VIEW monthly_po_summary AS
SELECT 
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as total_orders,
    SUM(total_amount) as total_spend,
    AVG(total_amount) as avg_order_value,
    COUNT(DISTINCT supplier_id) as unique_suppliers
FROM purchase_orders 
WHERE status != 'Cancelled'
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month DESC;

-- Supplier performance view
CREATE MATERIALIZED VIEW supplier_performance_summary AS
SELECT 
    s.id,
    s.company_name,
    COUNT(po.id) as total_orders,
    SUM(po.total_amount) as total_spend,
    AVG(po.total_amount) as avg_order_value,
    s.performance_rating,
    s.on_time_delivery_rate,
    AVG(EXTRACT(days FROM (po.updated_at - po.created_at))) as avg_cycle_days,
    COUNT(CASE WHEN po.status = 'Completed' THEN 1 END) as completed_orders,
    COUNT(CASE WHEN po.expected_delivery_date < CURRENT_DATE AND po.status IN ('Sent', 'Acknowledged', 'Shipped') THEN 1 END) as overdue_orders
FROM suppliers s
LEFT JOIN purchase_orders po ON s.id = po.supplier_id
WHERE s.is_active = TRUE
GROUP BY s.id, s.company_name, s.performance_rating, s.on_time_delivery_rate
ORDER BY total_spend DESC;

-- Budget tracking view
CREATE MATERIALIZED VIEW budget_tracking AS
SELECT 
    r.purpose,
    p.project_name,
    u.department,
    DATE_TRUNC('month', po.created_at) as month,
    SUM(po.total_amount) as actual_spend,
    COUNT(po.id) as order_count
FROM purchase_orders po
JOIN purchase_order_items poi ON po.id = poi.purchase_order_id
JOIN requisition_items ri ON poi.requisition_item_id = ri.id
JOIN requisitions r ON ri.requisition_id = r.id
JOIN users u ON r.user_id = u.id
LEFT JOIN projects p ON r.project_id = p.id
WHERE po.status != 'Cancelled'
GROUP BY r.purpose, p.project_name, u.department, DATE_TRUNC('month', po.created_at)
ORDER BY month DESC, actual_spend DESC;

-- Refresh materialized views periodically
CREATE OR REPLACE FUNCTION refresh_po_analytics_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW monthly_po_summary;
    REFRESH MATERIALIZED VIEW supplier_performance_summary;
    REFRESH MATERIALIZED VIEW budget_tracking;
END;
$$ LANGUAGE plpgsql;
```

#### Analytics Service
```python
class POAnalyticsService:
    def get_dashboard_summary(self, date_range: dict = None):
        """Get high-level dashboard metrics"""
        if not date_range:
            # Default to current month and YTD
            current_month = datetime.now().replace(day=1)
            year_start = datetime.now().replace(month=1, day=1)
        
        # Current month metrics
        current_month_data = db.session.query(
            func.count(PurchaseOrder.id).label('total_orders'),
            func.sum(PurchaseOrder.total_amount).label('total_spend'),
            func.avg(PurchaseOrder.total_amount).label('avg_order_value'),
            func.count(func.distinct(PurchaseOrder.supplier_id)).label('unique_suppliers')
        ).filter(
            PurchaseOrder.created_at >= current_month,
            PurchaseOrder.status != 'Cancelled'
        ).first()
        
        # Year-to-date metrics
        ytd_data = db.session.query(
            func.count(PurchaseOrder.id).label('total_orders'),
            func.sum(PurchaseOrder.total_amount).label('total_spend'),
            func.avg(PurchaseOrder.total_amount).label('avg_order_value'),
            func.count(func.distinct(PurchaseOrder.supplier_id)).label('unique_suppliers')
        ).filter(
            PurchaseOrder.created_at >= year_start,
            PurchaseOrder.status != 'Cancelled'
        ).first()
        
        # Status distribution
        status_distribution = db.session.query(
            PurchaseOrder.status,
            func.count(PurchaseOrder.id).label('count'),
            func.sum(PurchaseOrder.total_amount).label('value')
        ).filter(
            PurchaseOrder.created_at >= current_month
        ).group_by(PurchaseOrder.status).all()
        
        # Top suppliers this month
        top_suppliers = db.session.query(
            Supplier.company_name,
            func.sum(PurchaseOrder.total_amount).label('spend'),
            func.count(PurchaseOrder.id).label('orders')
        ).join(PurchaseOrder)\
        .filter(
            PurchaseOrder.created_at >= current_month,
            PurchaseOrder.status != 'Cancelled'
        )\
        .group_by(Supplier.company_name)\
        .order_by(func.sum(PurchaseOrder.total_amount).desc())\
        .limit(10).all()
        
        return {
            'current_month': {
                'total_orders': current_month_data.total_orders or 0,
                'total_spend': float(current_month_data.total_spend or 0),
                'avg_order_value': float(current_month_data.avg_order_value or 0),
                'unique_suppliers': current_month_data.unique_suppliers or 0
            },
            'year_to_date': {
                'total_orders': ytd_data.total_orders or 0,
                'total_spend': float(ytd_data.total_spend or 0),
                'avg_order_value': float(ytd_data.avg_order_value or 0),
                'unique_suppliers': ytd_data.unique_suppliers or 0
            },
            'status_distribution': [
                {
                    'status': status.status,
                    'count': status.count,
                    'value': float(status.value or 0)
                } for status in status_distribution
            ],
            'top_suppliers': [
                {
                    'name': supplier.company_name,
                    'spend': float(supplier.spend),
                    'orders': supplier.orders
                } for supplier in top_suppliers
            ]
        }
    
    def get_spending_trends(self, months: int = 12):
        """Get spending trends over time"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        trends = db.session.query(
            func.date_trunc('month', PurchaseOrder.created_at).label('month'),
            func.sum(PurchaseOrder.total_amount).label('spend'),
            func.count(PurchaseOrder.id).label('orders'),
            func.avg(PurchaseOrder.total_amount).label('avg_value')
        ).filter(
            PurchaseOrder.created_at >= start_date,
            PurchaseOrder.status != 'Cancelled'
        ).group_by(
            func.date_trunc('month', PurchaseOrder.created_at)
        ).order_by('month').all()
        
        return [
            {
                'month': trend.month.strftime('%Y-%m'),
                'spend': float(trend.spend or 0),
                'orders': trend.orders,
                'avg_value': float(trend.avg_value or 0)
            } for trend in trends
        ]
    
    def get_supplier_analytics(self):
        """Get comprehensive supplier performance analytics"""
        # Use materialized view for performance
        suppliers = db.session.execute(
            text("SELECT * FROM supplier_performance_summary ORDER BY total_spend DESC")
        ).fetchall()
        
        return [
            {
                'supplier_name': supplier.company_name,
                'total_orders': supplier.total_orders,
                'total_spend': float(supplier.total_spend or 0),
                'avg_order_value': float(supplier.avg_order_value or 0),
                'performance_rating': float(supplier.performance_rating or 0),
                'on_time_rate': float(supplier.on_time_delivery_rate or 0),
                'avg_cycle_days': float(supplier.avg_cycle_days or 0),
                'completed_orders': supplier.completed_orders,
                'overdue_orders': supplier.overdue_orders
            } for supplier in suppliers
        ]
```

#### Frontend Dashboard Components
```vue
<!-- PODashboard.vue -->
<template>
  <div class="po-dashboard">
    <!-- KPI Cards -->
    <el-row :gutter="20" class="kpi-cards">
      <el-col :span="6">
        <el-card>
          <div class="kpi-card">
            <div class="kpi-value">${{ formatCurrency(summary.current_month.total_spend) }}</div>
            <div class="kpi-label">This Month Spend</div>
            <div class="kpi-change" :class="getChangeClass(monthlyGrowth)">
              {{ formatPercentage(monthlyGrowth) }}
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card>
          <div class="kpi-card">
            <div class="kpi-value">{{ summary.current_month.total_orders }}</div>
            <div class="kpi-label">Orders This Month</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card>
          <div class="kpi-card">
            <div class="kpi-value">${{ formatCurrency(summary.current_month.avg_order_value) }}</div>
            <div class="kpi-label">Avg Order Value</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card>
          <div class="kpi-card">
            <div class="kpi-value">{{ summary.current_month.unique_suppliers }}</div>
            <div class="kpi-label">Active Suppliers</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- Charts -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card title="Spending Trends">
          <SpendingTrendsChart :data="spendingTrends" />
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card title="Status Distribution">
          <StatusDistributionChart :data="summary.status_distribution" />
        </el-card>
      </el-col>
    </el-row>
    
    <!-- Supplier Performance -->
    <el-row style="margin-top: 20px;">
      <el-col :span="24">
        <el-card title="Supplier Performance">
          <SupplierPerformanceTable :data="supplierAnalytics" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { usePOAnalytics } from '@/stores/poAnalytics';

const analytics = usePOAnalytics();
const summary = ref({});
const spendingTrends = ref([]);
const supplierAnalytics = ref([]);

onMounted(async () => {
  await Promise.all([
    analytics.loadDashboardSummary(),
    analytics.loadSpendingTrends(),
    analytics.loadSupplierAnalytics()
  ]);
  
  summary.value = analytics.dashboardSummary;
  spendingTrends.value = analytics.spendingTrends;
  supplierAnalytics.value = analytics.supplierAnalytics;
});

const monthlyGrowth = computed(() => {
  // Calculate growth compared to previous month
  // Implementation depends on historical data structure
  return 0.15; // Placeholder
});
</script>
```

### Test Scenarios
1. **Dashboard Loading**: Test dashboard data loading and display
2. **Trend Analysis**: Test spending and performance trend calculations
3. **Supplier Analytics**: Test supplier performance metrics accuracy
4. **Budget Tracking**: Test budget vs actual calculations
5. **Report Generation**: Test custom report creation and export
6. **Performance**: Test dashboard performance with large datasets
7. **Real-time Updates**: Test dashboard updates with new orders

### Dependencies
- Purchase order data (Stories 3.1-3.4)
- Reporting and export services
- Chart visualization libraries
- Materialized view refresh scheduling

**Story Points Breakdown**: Backend (12) + Frontend (6) + Analytics (2) + Testing (1) = 21

---

## Story 3.6: Supplier Communication and Portal Integration
**Story ID**: ERP-E03-S06  
**Title**: Enhanced Supplier Communication and Future Portal Preparation  
**Priority**: P2  
**Story Points**: 13  

### User Story
**As a** Procurement Specialist  
**I want to** improve communication with suppliers and prepare for future supplier portal integration  
**So that** I can streamline supplier interactions and enable self-service capabilities  

### Background & Context
Current supplier communication is primarily via email. This story prepares the foundation for future supplier portal integration while improving current email-based communications with better templates, tracking, and automated notifications.

### Acceptance Criteria
**AC1**: Given I need to communicate with suppliers, when I send PO-related communications, then I can use customizable email templates for different scenarios (PO send, amendments, delivery reminders)

**AC2**: Given I track supplier communications, when any email is sent, then the system logs all communications with timestamps and content for audit purposes

**AC3**: Given suppliers need to respond, when I send communications, then I can include response tracking links and deadline reminders

**AC4**: Given I prepare for future portal integration, when I design the system, then I create API endpoints and data structures that can support future supplier self-service portal

**AC5**: Given I need supplier confirmations, when I send POs, then I can include electronic acknowledgment options and track response status

### Technical Implementation Notes

#### API Endpoints Required
```
POST /api/v1/suppliers/{id}/communications    # Send communication to supplier
GET /api/v1/suppliers/{id}/communications     # Get communication history
PUT /api/v1/suppliers/{id}/acknowledge/{token} # Supplier acknowledgment endpoint
GET /api/v1/suppliers/portal-preparation       # Future portal data endpoints
```

#### Database Changes
```sql
-- Supplier communications log
CREATE TABLE supplier_communications (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    communication_type VARCHAR(50) NOT NULL, -- 'po_sent', 'amendment', 'reminder', 'inquiry'
    subject VARCHAR(500) NOT NULL,
    message_content TEXT NOT NULL,
    template_used VARCHAR(100),
    related_po_id INTEGER REFERENCES purchase_orders(id),
    sent_by INTEGER NOT NULL REFERENCES users(id),
    sent_via VARCHAR(20) DEFAULT 'email', -- 'email', 'portal', 'phone', 'fax'
    delivery_status VARCHAR(20) DEFAULT 'sent', -- 'sent', 'delivered', 'read', 'responded', 'failed'
    response_required BOOLEAN DEFAULT FALSE,
    response_deadline TIMESTAMP,
    response_received_at TIMESTAMP,
    tracking_token VARCHAR(255) UNIQUE,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Email templates
CREATE TABLE communication_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) UNIQUE NOT NULL,
    template_type VARCHAR(50) NOT NULL,
    subject_template VARCHAR(500) NOT NULL,
    body_template TEXT NOT NULL,
    variables JSONB, -- Available template variables
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supplier portal preparation (future use)
CREATE TABLE supplier_portal_access (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    contact_email VARCHAR(255) NOT NULL,
    access_token VARCHAR(255) UNIQUE,
    token_expires_at TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE,
    permissions JSONB DEFAULT '{"view_pos": true, "acknowledge_pos": true, "update_delivery": false}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_communications_supplier ON supplier_communications(supplier_id, sent_at DESC);
CREATE INDEX idx_communications_tracking ON supplier_communications(tracking_token) WHERE tracking_token IS NOT NULL;
```

#### Communication Service
```python
class SupplierCommunicationService:
    def send_po_to_supplier(self, po_id: int, template_name: str = 'po_standard', custom_message: str = None):
        """Send PO to supplier with tracking"""
        po = PurchaseOrder.query.get_or_404(po_id)
        template = self.get_template(template_name)
        
        # Generate tracking token
        tracking_token = self.generate_tracking_token()
        
        # Prepare template variables
        template_vars = {
            'po_number': po.po_number,
            'po_date': po.created_at.strftime('%Y-%m-%d'),
            'supplier_name': po.supplier.company_name,
            'supplier_contact': po.supplier.contact_person,
            'total_amount': po.total_amount,
            'currency': po.currency,
            'expected_delivery': po.expected_delivery_date,
            'delivery_address': po.delivery_address,
            'item_count': len(po.items),
            'tracking_url': f"{current_app.config['BASE_URL']}/supplier/track/{tracking_token}",
            'acknowledge_url': f"{current_app.config['BASE_URL']}/supplier/acknowledge/{tracking_token}"
        }
        
        # Render email content
        subject = self.render_template(template.subject_template, template_vars)
        body = self.render_template(template.body_template, template_vars)
        
        if custom_message:
            body += f"\n\nAdditional Notes:\n{custom_message}"
        
        # Send email
        email_result = self.email_service.send_email(
            to=po.supplier.email,
            cc=po.supplier.additional_contacts,
            subject=subject,
            body=body,
            attachments=[self.get_po_pdf_path(po_id)]
        )
        
        # Log communication
        communication = SupplierCommunication(
            supplier_id=po.supplier_id,
            communication_type='po_sent',
            subject=subject,
            message_content=body,
            template_used=template_name,
            related_po_id=po_id,
            sent_by=current_user.id,
            response_required=True,
            response_deadline=datetime.utcnow() + timedelta(days=3),
            tracking_token=tracking_token,
            delivery_status='sent' if email_result.success else 'failed'
        )
        
        db.session.add(communication)
        db.session.commit()
        
        return communication
    
    def track_email_interaction(self, tracking_token: str, interaction_type: str):
        """Track email interactions (open, click, etc.)"""
        communication = SupplierCommunication.query.filter_by(
            tracking_token=tracking_token
        ).first()
        
        if communication:
            if interaction_type == 'opened' and communication.delivery_status == 'sent':
                communication.delivery_status = 'read'
            elif interaction_type == 'acknowledged':
                communication.delivery_status = 'responded'
                communication.response_received_at = datetime.utcnow()
            
            db.session.commit()
        
        return communication
    
    def supplier_acknowledge_po(self, tracking_token: str, acknowledgment_data: dict):
        """Handle supplier PO acknowledgment via link"""
        communication = SupplierCommunication.query.filter_by(
            tracking_token=tracking_token
        ).first()
        
        if not communication or not communication.related_po_id:
            raise ValidationError("Invalid acknowledgment link")
        
        # Update communication
        communication.delivery_status = 'responded'
        communication.response_received_at = datetime.utcnow()
        
        # Process PO acknowledgment
        po_service = PurchaseOrderLifecycleService()
        po_service.acknowledge_po(
            communication.related_po_id,
            {
                'acknowledged_by': acknowledgment_data.get('contact_name', communication.supplier.contact_person),
                'method': 'email_link',
                'delivery_date': acknowledgment_data.get('confirmed_delivery_date'),
                'notes': acknowledgment_data.get('notes'),
                'acknowledged_at': datetime.utcnow()
            },
            user_id=1  # System user for supplier acknowledgments
        )
        
        db.session.commit()
        return communication
```

#### Email Templates
```html
<!-- PO Standard Template -->
<h2>Purchase Order: {{po_number}}</h2>
<p>Dear {{supplier_contact}},</p>

<p>We are pleased to send you our Purchase Order {{po_number}} dated {{po_date}}.</p>

<table style="border-collapse: collapse; width: 100%;">
  <tr style="background-color: #f5f5f5;">
    <td style="padding: 10px; border: 1px solid #ddd;"><strong>PO Number:</strong></td>
    <td style="padding: 10px; border: 1px solid #ddd;">{{po_number}}</td>
  </tr>
  <tr>
    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Total Amount:</strong></td>
    <td style="padding: 10px; border: 1px solid #ddd;">{{currency}} {{total_amount}}</td>
  </tr>
  <tr style="background-color: #f5f5f5;">
    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Expected Delivery:</strong></td>
    <td style="padding: 10px; border: 1px solid #ddd;">{{expected_delivery}}</td>
  </tr>
  <tr>
    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Total Items:</strong></td>
    <td style="padding: 10px; border: 1px solid #ddd;">{{item_count}}</td>
  </tr>
</table>

<p><strong>Delivery Address:</strong><br>{{delivery_address}}</p>

<div style="margin: 20px 0; padding: 15px; background-color: #e7f3ff; border-left: 5px solid #2196f3;">
  <p><strong>Action Required:</strong> Please acknowledge receipt of this PO and confirm the delivery date.</p>
  <p>
    <a href="{{acknowledge_url}}" style="background-color: #2196f3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
      Acknowledge PO Online
    </a>
  </p>
  <p><small>Or reply to this email with your confirmation.</small></p>
</div>

<p>Please find the detailed PO document attached. If you have any questions, please don't hesitate to contact us.</p>

<p>Thank you for your continued partnership.</p>

<p>Best regards,<br>
Procurement Team<br>
{{company_name}}</p>

<hr>
<p><small>
  This email was sent regarding PO {{po_number}}. 
  <a href="{{tracking_url}}">Track this communication</a>
</small></p>
```

### Test Scenarios
1. **Email Templates**: Test various email template rendering
2. **Communication Logging**: Test communication history tracking
3. **Supplier Acknowledgment**: Test acknowledgment workflow via email links
4. **Portal Preparation**: Test API endpoints for future portal integration
5. **Email Tracking**: Test email delivery and interaction tracking
6. **Template Management**: Test template creation and customization

### Dependencies
- Email service integration
- PO management system (Story 3.3)
- PDF generation for attachments
- Future portal development planning

**Story Points Breakdown**: Backend (8) + Email Templates (3) + Testing (2) = 13

---

## Epic Summary

### Total Story Points: 131
- Story 3.1: Automated Purchase Order Generation (25 points)
- Story 3.2: Supplier Management Integration (21 points)
- Story 3.3: Purchase Order Lifecycle Management (29 points)
- Story 3.4: PO Modifications and Version Control (17 points)
- Story 3.5: PO Dashboard and Analytics (21 points)
- Story 3.6: Supplier Communication and Portal Integration (13 points)

### Epic Dependencies
1. **Core Systems**: Authentication (Epic 1), Requisition Management (Epic 2)
2. **Infrastructure**: Email service, PDF generation, file storage
3. **External Services**: Materialized view refresh scheduling, background jobs
4. **Data**: Supplier database, project management integration

### Epic Risks & Mitigations
- **Risk**: Complex PO lifecycle causing workflow confusion
  - **Mitigation**: Clear UI status indicators, comprehensive user training
- **Risk**: Supplier communication failures affecting order processing
  - **Mitigation**: Multiple communication channels, automated retries, fallback procedures
- **Risk**: Performance issues with large PO datasets and complex analytics
  - **Mitigation**: Database optimization, materialized views, caching strategies
- **Risk**: Version control complexity leading to data inconsistencies
  - **Mitigation**: Robust validation, approval workflows, comprehensive testing

### Success Criteria
- PO generation time reduced by 70% through automation
- 100% of PO status changes tracked and communicated
- Supplier acknowledgment rate >90% within 48 hours
- Dashboard analytics refresh within 5 seconds for standard queries
- Zero data loss during PO modifications and version control
- User satisfaction score >4.3/5.0 for PO management workflows

This epic provides comprehensive purchase order management that transforms approved requisitions into managed supplier relationships with complete lifecycle tracking, performance analytics, and communication management.