# Epic 4: Inventory & Warehouse Management
**Epic ID**: ERP-E04  
**Priority**: P0 (Critical)  
**Story Points**: 118  
**Status**: Draft  

## Epic Description
Implement a comprehensive inventory and warehouse management system that handles goods receipt, storage location management, inventory tracking, and item acceptance workflows. This system provides real-time inventory visibility, efficient space utilization, and seamless integration with purchase orders and requisitions.

## Business Value
- **Accuracy**: Eliminate manual inventory errors through digital tracking
- **Efficiency**: Reduce time to locate items by 80% with structured storage system
- **Visibility**: Provide real-time inventory status across all locations
- **Space Optimization**: Maximize warehouse space utilization through systematic location management
- **Process Integration**: Seamlessly connect purchase orders to inventory receipt and requisition fulfillment

## User Personas
- **Primary**: Warehouse Managers (goods receipt, location management), Engineers (item search and acceptance)
- **Secondary**: Procurement Staff (delivery tracking), Accountants (inventory valuation)

---

## Story 4.1: Flexible Goods Receipt Process
**Story ID**: ERP-E04-S01  
**Title**: Implement Comprehensive Goods Receipt Workflow  
**Priority**: P0  
**Story Points**: 25  

### User Story
**As a** Warehouse Manager  
**I want to** receive goods against purchase orders with flexible assignment options  
**So that** any authorized staff can handle deliveries efficiently and accurately track received items  

### Background & Context
The goods receipt process must accommodate various delivery scenarios: complete deliveries, partial deliveries, over-deliveries, and damaged items. The system should be flexible enough for any warehouse staff member to process receipts while maintaining accuracy and audit trails.

### Acceptance Criteria
**AC1**: Given a delivery arrives, when I start the receipt process, then I can scan or manually enter the PO number to retrieve expected items with quantities and specifications

**AC2**: Given I am receiving items, when I process each item, then I can confirm received quantity against ordered quantity with variance handling (under/over delivery)

**AC3**: Given items are damaged or defective, when I identify issues, then I can mark items as damaged, capture photos, and record detailed quality notes

**AC4**: Given I complete a receipt, when I finalize it, then I can assign storage locations and generate a receipt confirmation with timestamp and receiver identification

**AC5**: Given multiple staff can receive goods, when anyone processes a receipt, then the system validates their warehouse permissions and logs their identity

**AC6**: Given receipt variances exist, when quantities don't match, then the system alerts me and provides options to: accept variance, create discrepancy report, or contact supplier

### Technical Implementation Notes

#### API Endpoints Required
```
GET /api/v1/goods-receipt/po/{po_number}      # Get PO details for receipt
POST /api/v1/goods-receipt                    # Create new receipt
PUT /api/v1/goods-receipt/{id}/items          # Update received quantities
POST /api/v1/goods-receipt/{id}/finalize      # Finalize receipt
GET /api/v1/goods-receipt/{id}                # Get receipt details
POST /api/v1/goods-receipt/{id}/photos        # Upload item photos
GET /api/v1/goods-receipt/dashboard           # Receipt dashboard
```

#### Database Changes
```sql
-- Goods receipt header
CREATE TABLE goods_receipts (
    id SERIAL PRIMARY KEY,
    receipt_number VARCHAR(20) UNIQUE NOT NULL,
    purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id),
    receipt_date DATE NOT NULL DEFAULT CURRENT_DATE,
    received_by INTEGER NOT NULL REFERENCES users(id),
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    delivery_reference VARCHAR(100), -- Supplier delivery note number
    carrier_name VARCHAR(100),
    tracking_number VARCHAR(100),
    receipt_type VARCHAR(20) DEFAULT 'Full' CHECK (receipt_type IN ('Full', 'Partial', 'Over', 'Damaged')),
    total_items_expected INTEGER NOT NULL DEFAULT 0,
    total_items_received INTEGER NOT NULL DEFAULT 0,
    has_variances BOOLEAN DEFAULT FALSE,
    has_damages BOOLEAN DEFAULT FALSE,
    receipt_notes TEXT,
    status VARCHAR(20) DEFAULT 'Draft' CHECK (status IN ('Draft', 'Finalized', 'Discrepancy')),
    finalized_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Goods receipt items
CREATE TABLE goods_receipt_items (
    id SERIAL PRIMARY KEY,
    goods_receipt_id INTEGER NOT NULL REFERENCES goods_receipts(id) ON DELETE CASCADE,
    purchase_order_item_id INTEGER NOT NULL REFERENCES purchase_order_items(id),
    item_name VARCHAR(255) NOT NULL,
    item_description TEXT,
    expected_quantity DECIMAL(10,3) NOT NULL,
    received_quantity DECIMAL(10,3) NOT NULL DEFAULT 0,
    accepted_quantity DECIMAL(10,3) NOT NULL DEFAULT 0,
    damaged_quantity DECIMAL(10,3) NOT NULL DEFAULT 0,
    unit VARCHAR(50) DEFAULT 'pcs',
    unit_price DECIMAL(10,2),
    storage_location VARCHAR(50), -- Format: Zone-Shelf-Level-Position
    lot_batch_number VARCHAR(100),
    expiry_date DATE,
    condition_status VARCHAR(20) DEFAULT 'Good' CHECK (
        condition_status IN ('Good', 'Damaged', 'Defective', 'Expired')
    ),
    quality_notes TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_by INTEGER REFERENCES users(id), -- Original requester acceptance
    accepted_at TIMESTAMP
);

-- Item photos and documents
CREATE TABLE receipt_item_photos (
    id SERIAL PRIMARY KEY,
    receipt_item_id INTEGER NOT NULL REFERENCES goods_receipt_items(id) ON DELETE CASCADE,
    photo_filename VARCHAR(255) NOT NULL,
    photo_path VARCHAR(500) NOT NULL,
    photo_type VARCHAR(50) DEFAULT 'condition', -- 'condition', 'damage', 'packaging'
    description TEXT,
    uploaded_by INTEGER NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Storage locations master data
CREATE TABLE storage_locations (
    id SERIAL PRIMARY KEY,
    location_code VARCHAR(50) UNIQUE NOT NULL, -- A-01-2-B format
    zone VARCHAR(10) NOT NULL, -- A, B, C
    shelf VARCHAR(10) NOT NULL, -- 01, 02, 03
    level VARCHAR(10) NOT NULL, -- 1, 2, 3
    position VARCHAR(10) NOT NULL, -- A, B, C
    location_type VARCHAR(50) DEFAULT 'General', -- 'General', 'Hazardous', 'Climate-Controlled'
    capacity_limit DECIMAL(10,3), -- Maximum quantity capacity
    current_utilization DECIMAL(10,3) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Generate receipt numbers sequence
CREATE SEQUENCE receipt_number_seq START 1;

-- Indexes for performance
CREATE INDEX idx_goods_receipts_po ON goods_receipts(purchase_order_id);
CREATE INDEX idx_goods_receipts_date ON goods_receipts(receipt_date DESC);
CREATE INDEX idx_receipt_items_receipt ON goods_receipt_items(goods_receipt_id);
CREATE INDEX idx_storage_locations_code ON storage_locations(location_code);
CREATE INDEX idx_storage_locations_zone ON storage_locations(zone, shelf, level, position);
```

#### Goods Receipt Service
```python
class GoodsReceiptService:
    def initiate_receipt(self, po_number: str, user_id: int):
        """Initialize goods receipt process"""
        # Get purchase order
        po = PurchaseOrder.query.filter_by(po_number=po_number).first()
        if not po:
            raise ValidationError(f"Purchase order {po_number} not found")
        
        if po.status not in ['Shipped', 'Partially Received']:
            raise ValidationError(f"Cannot receive goods for PO with status: {po.status}")
        
        # Check if user has warehouse permissions
        if not self.has_warehouse_permission(user_id):
            raise PermissionError("User not authorized for goods receipt")
        
        # Check for existing draft receipt
        existing_receipt = GoodsReceipt.query.filter_by(
            purchase_order_id=po.id,
            status='Draft'
        ).first()
        
        if existing_receipt:
            return existing_receipt
        
        # Create new receipt
        receipt_number = self.generate_receipt_number()
        
        receipt = GoodsReceipt(
            receipt_number=receipt_number,
            purchase_order_id=po.id,
            received_by=user_id,
            supplier_id=po.supplier_id,
            total_items_expected=len(po.items)
        )
        
        db.session.add(receipt)
        db.session.flush()
        
        # Create receipt items from PO items
        for po_item in po.items:
            receipt_item = GoodsReceiptItem(
                goods_receipt_id=receipt.id,
                purchase_order_item_id=po_item.id,
                item_name=po_item.item_name,
                item_description=po_item.description,
                expected_quantity=po_item.quantity - po_item.received_quantity,
                unit=po_item.unit,
                unit_price=po_item.unit_price
            )
            db.session.add(receipt_item)
        
        db.session.commit()
        return receipt
    
    def update_received_quantities(self, receipt_id: int, items_data: List[dict], user_id: int):
        """Update received quantities for items"""
        receipt = GoodsReceipt.query.get_or_404(receipt_id)
        
        if receipt.status != 'Draft':
            raise ValidationError("Cannot modify finalized receipt")
        
        total_received = 0
        has_variances = False
        has_damages = False
        
        for item_data in items_data:
            item_id = item_data['item_id']
            received_qty = item_data['received_quantity']
            damaged_qty = item_data.get('damaged_quantity', 0)
            condition = item_data.get('condition_status', 'Good')
            quality_notes = item_data.get('quality_notes')
            
            receipt_item = GoodsReceiptItem.query.get(item_id)
            if receipt_item and receipt_item.goods_receipt_id == receipt_id:
                receipt_item.received_quantity = received_qty
                receipt_item.damaged_quantity = damaged_qty
                receipt_item.accepted_quantity = received_qty - damaged_qty
                receipt_item.condition_status = condition
                receipt_item.quality_notes = quality_notes
                
                # Check for variances
                if abs(received_qty - receipt_item.expected_quantity) > 0.01:
                    has_variances = True
                
                if damaged_qty > 0 or condition != 'Good':
                    has_damages = True
                
                total_received += received_qty
        
        # Update receipt summary
        receipt.total_items_received = total_received
        receipt.has_variances = has_variances
        receipt.has_damages = has_damages
        receipt.updated_at = datetime.utcnow()
        
        db.session.commit()
        return receipt
    
    def assign_storage_locations(self, receipt_id: int, location_assignments: List[dict], user_id: int):
        """Assign storage locations to received items"""
        receipt = GoodsReceipt.query.get_or_404(receipt_id)
        
        for assignment in location_assignments:
            item_id = assignment['item_id']
            location_code = assignment['location_code']
            quantity = assignment.get('quantity')
            
            # Validate location exists and has capacity
            location = StorageLocation.query.filter_by(location_code=location_code).first()
            if not location or not location.is_active:
                raise ValidationError(f"Invalid storage location: {location_code}")
            
            # Update receipt item
            receipt_item = GoodsReceiptItem.query.get(item_id)
            if receipt_item and receipt_item.goods_receipt_id == receipt_id:
                receipt_item.storage_location = location_code
                
                # Update location utilization
                location.current_utilization += quantity or receipt_item.accepted_quantity
        
        db.session.commit()
        return receipt
    
    def finalize_receipt(self, receipt_id: int, user_id: int):
        """Finalize goods receipt and update inventory"""
        receipt = GoodsReceipt.query.get_or_404(receipt_id)
        
        if receipt.status != 'Draft':
            raise ValidationError("Receipt already finalized")
        
        # Validate all items have received quantities
        items_without_quantities = [
            item for item in receipt.items 
            if item.received_quantity == 0 and item.expected_quantity > 0
        ]
        
        if items_without_quantities:
            raise ValidationError("All expected items must have received quantities")
        
        # Update receipt status
        receipt.status = 'Finalized'
        receipt.finalized_at = datetime.utcnow()
        
        # Update purchase order item quantities
        for receipt_item in receipt.items:
            po_item = receipt_item.purchase_order_item
            po_item.received_quantity += receipt_item.received_quantity
            
            # Update item status
            if po_item.received_quantity >= po_item.quantity:
                po_item.status = 'Received'
            else:
                po_item.status = 'Partially Received'
        
        # Update purchase order status
        po = receipt.purchase_order
        all_items_received = all(
            item.received_quantity >= item.quantity 
            for item in po.items
        )
        
        if all_items_received:
            po.status = 'Completed'
        else:
            po.status = 'Partially Received'
        
        # Create inventory items
        self.create_inventory_items(receipt)
        
        # Notify original requesters
        self.notify_item_recipients(receipt)
        
        db.session.commit()
        return receipt
    
    def generate_receipt_number(self):
        """Generate unique receipt number"""
        today = datetime.now().strftime('%Y%m%d')
        sequence = db.session.execute(text("SELECT nextval('receipt_number_seq')")).scalar()
        return f'GR-{today}-{sequence:04d}'
```

### Test Scenarios
1. **PO Retrieval**: Test PO lookup by number and validation
2. **Quantity Recording**: Test various quantity scenarios (full, partial, over)
3. **Damage Recording**: Test damaged item processing with photos
4. **Location Assignment**: Test storage location assignment and validation
5. **Receipt Finalization**: Test complete receipt workflow
6. **Variance Handling**: Test over/under delivery processing
7. **Permissions**: Test warehouse staff authorization
8. **Integration**: Test PO status updates after receipt

### Dependencies
- Purchase order management (Epic 3)
- User authentication and authorization (Epic 1)
- File storage for photos
- Storage location master data setup

**Story Points Breakdown**: Backend (15) + Frontend (7) + Database (2) + Testing (1) = 25

---

## Story 4.2: Hierarchical Storage Location Management
**Story ID**: ERP-E04-S02  
**Title**: Implement Zone-Based Storage Location System  
**Priority**: P0  
**Story Points**: 21  

### User Story
**As a** Warehouse Manager  
**I want to** organize inventory using a hierarchical storage location system  
**So that** items can be easily located and warehouse space is optimally utilized  

### Background & Context
The storage system uses a hierarchical structure: Zone → Shelf → Level → Position (e.g., A-01-2-B). This allows for logical organization, easy navigation, and scalable warehouse management as operations grow.

### Acceptance Criteria
**AC1**: Given I need to set up storage locations, when I create locations, then I can define zones (A, B, C), shelves (01, 02, 03), levels (1, 2, 3), and positions (A, B, C) in format Zone-Shelf-Level-Position

**AC2**: Given I manage warehouse layout, when I view storage locations, then I can see capacity limits, current utilization, location type, and status for each location

**AC3**: Given I assign items to storage, when I select a location, then the system validates capacity and suggests optimal locations based on item type and proximity

**AC4**: Given I search for items, when I use location-based search, then I can find items by zone, shelf, or complete location code with visual warehouse map

**AC5**: Given I optimize space usage, when I view utilization reports, then I can see capacity utilization by zone, identify underutilized areas, and plan layout improvements

**AC6**: Given items are moved, when I relocate inventory, then I can update storage locations with full audit trail of movement history

### Technical Implementation Notes

#### API Endpoints Required
```
GET /api/v1/storage-locations                 # List all locations with filters
POST /api/v1/storage-locations                # Create new location
PUT /api/v1/storage-locations/{id}            # Update location details
DELETE /api/v1/storage-locations/{id}         # Deactivate location
GET /api/v1/storage-locations/suggest         # Suggest optimal location
GET /api/v1/storage-locations/utilization     # Get utilization reports
POST /api/v1/storage-locations/relocate       # Move items between locations
```

#### Database Changes (Additional)
```sql
-- Enhanced storage location structure
ALTER TABLE storage_locations ADD COLUMN zone_description VARCHAR(255);
ALTER TABLE storage_locations ADD COLUMN temperature_controlled BOOLEAN DEFAULT FALSE;
ALTER TABLE storage_locations ADD COLUMN hazmat_approved BOOLEAN DEFAULT FALSE;
ALTER TABLE storage_locations ADD COLUMN weight_limit DECIMAL(10,3);
ALTER TABLE storage_locations ADD COLUMN dimension_length DECIMAL(8,2);
ALTER TABLE storage_locations ADD COLUMN dimension_width DECIMAL(8,2);
ALTER TABLE storage_locations ADD COLUMN dimension_height DECIMAL(8,2);

-- Location movement history
CREATE TABLE inventory_movements (
    id SERIAL PRIMARY KEY,
    inventory_item_id INTEGER NOT NULL REFERENCES inventory_items(id),
    from_location VARCHAR(50),
    to_location VARCHAR(50) NOT NULL,
    movement_type VARCHAR(20) NOT NULL CHECK (
        movement_type IN ('Receipt', 'Transfer', 'Adjustment', 'Pick', 'Return')
    ),
    quantity DECIMAL(10,3) NOT NULL,
    movement_reason TEXT,
    moved_by INTEGER NOT NULL REFERENCES users(id),
    reference_number VARCHAR(100), -- Receipt number, transfer order, etc.
    movement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory items table (main inventory tracking)
CREATE TABLE inventory_items (
    id SERIAL PRIMARY KEY,
    item_code VARCHAR(50) UNIQUE NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    item_description TEXT,
    category VARCHAR(100),
    unit VARCHAR(50) DEFAULT 'pcs',
    current_quantity DECIMAL(10,3) NOT NULL DEFAULT 0,
    reserved_quantity DECIMAL(10,3) NOT NULL DEFAULT 0,
    available_quantity DECIMAL(10,3) GENERATED ALWAYS AS (current_quantity - reserved_quantity) STORED,
    unit_cost DECIMAL(10,2),
    storage_location VARCHAR(50) REFERENCES storage_locations(location_code),
    lot_batch_number VARCHAR(100),
    expiry_date DATE,
    condition_status VARCHAR(20) DEFAULT 'Good',
    item_status VARCHAR(20) DEFAULT 'Available' CHECK (
        item_status IN ('Available', 'Reserved', 'Damaged', 'On Hold', 'Expired')
    ),
    supplier_id INTEGER REFERENCES suppliers(id),
    purchase_order_item_id INTEGER REFERENCES purchase_order_items(id),
    requisition_item_id INTEGER REFERENCES requisition_items(id), -- Original request
    received_date DATE,
    received_by INTEGER REFERENCES users(id),
    last_movement_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Location capacity tracking view
CREATE VIEW location_capacity_summary AS
SELECT 
    sl.location_code,
    sl.zone,
    sl.shelf,
    sl.level,
    sl.position,
    sl.capacity_limit,
    sl.current_utilization,
    CASE 
        WHEN sl.capacity_limit > 0 THEN (sl.current_utilization / sl.capacity_limit) * 100
        ELSE 0
    END as utilization_percentage,
    COUNT(ii.id) as item_count,
    SUM(ii.current_quantity * ii.unit_cost) as total_value
FROM storage_locations sl
LEFT JOIN inventory_items ii ON sl.location_code = ii.storage_location
WHERE sl.is_active = TRUE
GROUP BY sl.location_code, sl.zone, sl.shelf, sl.level, sl.position, 
         sl.capacity_limit, sl.current_utilization
ORDER BY sl.location_code;

-- Indexes
CREATE INDEX idx_inventory_items_location ON inventory_items(storage_location);
CREATE INDEX idx_inventory_items_status ON inventory_items(item_status);
CREATE INDEX idx_inventory_movements_item ON inventory_movements(inventory_item_id, movement_date DESC);
```

#### Storage Location Service
```python
class StorageLocationService:
    def create_location_hierarchy(self, zone_config: dict):
        """Create complete zone with all locations"""
        zone = zone_config['zone']
        shelves = zone_config.get('shelves', 10)
        levels = zone_config.get('levels', 3)
        positions = zone_config.get('positions', ['A', 'B', 'C'])
        capacity_per_location = zone_config.get('default_capacity', 100)
        
        locations = []
        
        for shelf in range(1, shelves + 1):
            for level in range(1, levels + 1):
                for position in positions:
                    location_code = f"{zone}-{shelf:02d}-{level}-{position}"
                    
                    location = StorageLocation(
                        location_code=location_code,
                        zone=zone,
                        shelf=f"{shelf:02d}",
                        level=str(level),
                        position=position,
                        capacity_limit=capacity_per_location,
                        location_type=zone_config.get('type', 'General'),
                        temperature_controlled=zone_config.get('temperature_controlled', False),
                        hazmat_approved=zone_config.get('hazmat_approved', False)
                    )
                    
                    locations.append(location)
        
        db.session.add_all(locations)
        db.session.commit()
        
        return locations
    
    def suggest_optimal_location(self, item_requirements: dict):
        """Suggest best storage location for item"""
        required_capacity = item_requirements.get('quantity', 1)
        item_type = item_requirements.get('type', 'general')
        temperature_controlled = item_requirements.get('temperature_controlled', False)
        hazmat = item_requirements.get('hazmat', False)
        
        query = StorageLocation.query.filter(
            StorageLocation.is_active == True,
            StorageLocation.capacity_limit >= StorageLocation.current_utilization + required_capacity
        )
        
        # Add special requirements
        if temperature_controlled:
            query = query.filter(StorageLocation.temperature_controlled == True)
        
        if hazmat:
            query = query.filter(StorageLocation.hazmat_approved == True)
        
        # Order by utilization (prefer less utilized locations)
        # but also consider proximity to similar items
        locations = query.order_by(
            StorageLocation.current_utilization.asc(),
            StorageLocation.location_code.asc()
        ).limit(5).all()
        
        suggestions = []
        for location in locations:
            utilization_after = location.current_utilization + required_capacity
            utilization_percentage = (utilization_after / location.capacity_limit) * 100 if location.capacity_limit > 0 else 0
            
            suggestions.append({
                'location_code': location.location_code,
                'zone': location.zone,
                'current_utilization': float(location.current_utilization),
                'capacity_limit': float(location.capacity_limit),
                'utilization_after': float(utilization_after),
                'utilization_percentage': round(utilization_percentage, 1),
                'location_type': location.location_type,
                'recommendation_score': self.calculate_recommendation_score(location, item_requirements)
            })
        
        return sorted(suggestions, key=lambda x: x['recommendation_score'], reverse=True)
    
    def calculate_recommendation_score(self, location: StorageLocation, requirements: dict) -> float:
        """Calculate location recommendation score (0-100)"""
        score = 100.0
        
        # Penalize high utilization
        if location.capacity_limit > 0:
            utilization_rate = location.current_utilization / location.capacity_limit
            if utilization_rate > 0.8:  # Over 80% utilized
                score -= (utilization_rate - 0.8) * 100  # Penalty up to 20 points
        
        # Bonus for matching special requirements
        if requirements.get('temperature_controlled') and location.temperature_controlled:
            score += 10
        
        if requirements.get('hazmat') and location.hazmat_approved:
            score += 10
        
        # Bonus for zone preference (if specified)
        preferred_zone = requirements.get('preferred_zone')
        if preferred_zone and location.zone == preferred_zone:
            score += 15
        
        return max(0, min(100, score))
    
    def relocate_inventory(self, relocation_requests: List[dict], user_id: int):
        """Move inventory items between locations"""
        movements = []
        
        for request in relocation_requests:
            item_id = request['item_id']
            to_location = request['to_location']
            quantity = request.get('quantity')
            reason = request.get('reason', 'Manual relocation')
            
            # Get inventory item
            inventory_item = InventoryItem.query.get_or_404(item_id)
            from_location = inventory_item.storage_location
            
            # Validate destination location
            dest_location = StorageLocation.query.filter_by(location_code=to_location).first()
            if not dest_location or not dest_location.is_active:
                raise ValidationError(f"Invalid destination location: {to_location}")
            
            # Determine quantity to move
            move_quantity = quantity or inventory_item.current_quantity
            
            if move_quantity > inventory_item.current_quantity:
                raise ValidationError("Cannot move more quantity than available")
            
            # Update location utilization
            if from_location:
                from_loc = StorageLocation.query.filter_by(location_code=from_location).first()
                if from_loc:
                    from_loc.current_utilization -= move_quantity
            
            dest_location.current_utilization += move_quantity
            
            # Update inventory item location
            if move_quantity == inventory_item.current_quantity:
                # Moving entire quantity
                inventory_item.storage_location = to_location
            else:
                # Split inventory - create new item for moved quantity
                new_item = InventoryItem(
                    item_code=f"{inventory_item.item_code}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    item_name=inventory_item.item_name,
                    item_description=inventory_item.item_description,
                    category=inventory_item.category,
                    unit=inventory_item.unit,
                    current_quantity=move_quantity,
                    unit_cost=inventory_item.unit_cost,
                    storage_location=to_location,
                    lot_batch_number=inventory_item.lot_batch_number,
                    expiry_date=inventory_item.expiry_date,
                    condition_status=inventory_item.condition_status,
                    item_status=inventory_item.item_status
                )
                db.session.add(new_item)
                
                # Update original item quantity
                inventory_item.current_quantity -= move_quantity
            
            # Create movement record
            movement = InventoryMovement(
                inventory_item_id=inventory_item.id,
                from_location=from_location,
                to_location=to_location,
                movement_type='Transfer',
                quantity=move_quantity,
                movement_reason=reason,
                moved_by=user_id
            )
            movements.append(movement)
            db.session.add(movement)
        
        db.session.commit()
        return movements
```

### Test Scenarios
1. **Location Creation**: Test hierarchical location setup
2. **Capacity Management**: Test capacity tracking and validation
3. **Location Suggestions**: Test optimal location recommendation algorithm
4. **Inventory Relocation**: Test moving items between locations
5. **Utilization Reporting**: Test capacity utilization calculations
6. **Search Functionality**: Test location-based inventory search
7. **Audit Trail**: Test movement history tracking

### Dependencies
- Goods receipt process (Story 4.1)
- Basic warehouse setup and configuration
- User permission system for warehouse operations

**Story Points Breakdown**: Backend (12) + Frontend (6) + Database (2) + Testing (1) = 21

---

## Story 4.3: Advanced Inventory Search and Management
**Story ID**: ERP-E04-S03  
**Title**: Comprehensive Inventory Search and Filtering System  
**Priority**: P1  
**Story Points**: 17  

### User Story
**As an** Engineer or Warehouse staff member  
**I want to** search and filter inventory by multiple criteria with real-time availability  
**So that** I can quickly find needed items and make informed decisions about inventory usage  

### Background & Context
Users need to efficiently locate items among potentially thousands of inventory records. The search system must support text search, location filtering, status filtering, and availability checks while maintaining high performance.

### Acceptance Criteria
**AC1**: Given I need to find items, when I use the search interface, then I can search by item name, description, SKU, or location code with auto-complete suggestions

**AC2**: Given I want to filter inventory, when I apply filters, then I can filter by: status, location (zone/shelf), category, supplier, date ranges, and quantity ranges

**AC3**: Given I search for items, when results are displayed, then I can see: item details, current location, available quantity, condition status, and last movement date

**AC4**: Given I need detailed item information, when I select an item, then I can view: complete history, related purchase orders, original requisitions, and movement trail

**AC5**: Given I manage inventory, when I view item details, then I can update item status, add notes, mark as damaged, or initiate transfers

**AC6**: Given I need reports, when I export search results, then I can generate Excel reports with all visible data and applied filters

### Technical Implementation Notes

#### API Endpoints Required
```
GET /api/v1/inventory/search                  # Advanced search with filters
GET /api/v1/inventory/autocomplete            # Search suggestions
GET /api/v1/inventory/{id}/details            # Get item details with history
PUT /api/v1/inventory/{id}/status             # Update item status
POST /api/v1/inventory/{id}/notes             # Add item notes
POST /api/v1/inventory/export                 # Export search results
GET /api/v1/inventory/categories              # Get available categories
```

#### Enhanced Inventory Search
```python
class InventorySearchService:
    def advanced_search(self, search_params: dict, user_id: int):
        """Perform advanced inventory search with filters"""
        query = db.session.query(InventoryItem)
        
        # Text search across multiple fields
        search_text = search_params.get('q')
        if search_text:
            search_pattern = f'%{search_text}%'
            query = query.filter(
                or_(
                    InventoryItem.item_name.ilike(search_pattern),
                    InventoryItem.item_description.ilike(search_pattern),
                    InventoryItem.item_code.ilike(search_pattern),
                    InventoryItem.lot_batch_number.ilike(search_pattern)
                )
            )
        
        # Status filter
        status = search_params.get('status')
        if status:
            if isinstance(status, str):
                status = [status]
            query = query.filter(InventoryItem.item_status.in_(status))
        
        # Location filters
        location_code = search_params.get('location_code')
        if location_code:
            query = query.filter(InventoryItem.storage_location == location_code)
        
        zone = search_params.get('zone')
        if zone:
            query = query.join(StorageLocation).filter(StorageLocation.zone == zone)
        
        # Category filter
        category = search_params.get('category')
        if category:
            query = query.filter(InventoryItem.category == category)
        
        # Supplier filter
        supplier_id = search_params.get('supplier_id')
        if supplier_id:
            query = query.filter(InventoryItem.supplier_id == supplier_id)
        
        # Quantity range filters
        min_quantity = search_params.get('min_quantity')
        if min_quantity is not None:
            query = query.filter(InventoryItem.available_quantity >= min_quantity)
        
        max_quantity = search_params.get('max_quantity')
        if max_quantity is not None:
            query = query.filter(InventoryItem.available_quantity <= max_quantity)
        
        # Date range filters
        received_from = search_params.get('received_from')
        if received_from:
            query = query.filter(InventoryItem.received_date >= received_from)
        
        received_to = search_params.get('received_to')
        if received_to:
            query = query.filter(InventoryItem.received_date <= received_to)
        
        # Expiry date filters
        expires_within_days = search_params.get('expires_within_days')
        if expires_within_days:
            expiry_threshold = datetime.now().date() + timedelta(days=expires_within_days)
            query = query.filter(
                InventoryItem.expiry_date.isnot(None),
                InventoryItem.expiry_date <= expiry_threshold
            )
        
        # Condition filter
        condition = search_params.get('condition')
        if condition:
            query = query.filter(InventoryItem.condition_status == condition)
        
        # Role-based filtering
        user_role = self.get_user_role(user_id)
        if user_role == 'Engineer':
            # Engineers can only see available items
            query = query.filter(InventoryItem.item_status == 'Available')
        
        # Sorting
        sort_by = search_params.get('sort_by', 'item_name')
        sort_order = search_params.get('sort_order', 'asc')
        
        sort_column = getattr(InventoryItem, sort_by, InventoryItem.item_name)
        if sort_order == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Pagination
        page = search_params.get('page', 1)
        per_page = search_params.get('per_page', 20)
        
        result = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'items': [self.serialize_inventory_item(item) for item in result.items],
            'pagination': {
                'page': result.page,
                'per_page': result.per_page,
                'total': result.total,
                'pages': result.pages,
                'has_next': result.has_next,
                'has_prev': result.has_prev
            }
        }
    
    def get_autocomplete_suggestions(self, query_text: str, limit: int = 10):
        """Get autocomplete suggestions for search"""
        if len(query_text) < 2:
            return []
        
        pattern = f'{query_text}%'
        
        # Search in item names
        name_suggestions = db.session.query(InventoryItem.item_name)\
            .filter(InventoryItem.item_name.ilike(pattern))\
            .distinct()\
            .limit(limit//2)\
            .all()
        
        # Search in item codes
        code_suggestions = db.session.query(InventoryItem.item_code)\
            .filter(InventoryItem.item_code.ilike(pattern))\
            .distinct()\
            .limit(limit//2)\
            .all()
        
        suggestions = []
        suggestions.extend([{'value': name[0], 'type': 'name'} for name in name_suggestions])
        suggestions.extend([{'value': code[0], 'type': 'code'} for code in code_suggestions])
        
        return suggestions[:limit]
    
    def get_item_details_with_history(self, item_id: int):
        """Get comprehensive item details including history"""
        item = InventoryItem.query.get_or_404(item_id)
        
        # Get movement history
        movements = InventoryMovement.query\
            .filter_by(inventory_item_id=item_id)\
            .order_by(InventoryMovement.movement_date.desc())\
            .all()
        
        # Get related purchase order information
        po_info = None
        if item.purchase_order_item_id:
            po_item = PurchaseOrderItem.query.get(item.purchase_order_item_id)
            if po_item:
                po_info = {
                    'po_number': po_item.purchase_order.po_number,
                    'supplier': po_item.purchase_order.supplier.company_name,
                    'po_date': po_item.purchase_order.created_at.isoformat(),
                    'unit_price': float(po_item.unit_price)
                }
        
        # Get original requisition information
        req_info = None
        if item.requisition_item_id:
            req_item = RequisitionItem.query.get(item.requisition_item_id)
            if req_item:
                req_info = {
                    'req_number': req_item.requisition.req_number,
                    'requester': req_item.requisition.user.username,
                    'purpose': req_item.requisition.purpose,
                    'req_date': req_item.requisition.created_at.isoformat()
                }
        
        return {
            'item': self.serialize_inventory_item(item),
            'movements': [self.serialize_movement(movement) for movement in movements],
            'purchase_order': po_info,
            'original_requisition': req_info,
            'current_reservations': self.get_item_reservations(item_id)
        }
    
    def serialize_inventory_item(self, item: InventoryItem):
        """Serialize inventory item for API response"""
        return {
            'id': item.id,
            'item_code': item.item_code,
            'item_name': item.item_name,
            'description': item.item_description,
            'category': item.category,
            'unit': item.unit,
            'current_quantity': float(item.current_quantity),
            'reserved_quantity': float(item.reserved_quantity),
            'available_quantity': float(item.available_quantity),
            'unit_cost': float(item.unit_cost) if item.unit_cost else None,
            'storage_location': item.storage_location,
            'lot_batch_number': item.lot_batch_number,
            'expiry_date': item.expiry_date.isoformat() if item.expiry_date else None,
            'condition_status': item.condition_status,
            'item_status': item.item_status,
            'received_date': item.received_date.isoformat() if item.received_date else None,
            'last_movement_date': item.last_movement_date.isoformat() if item.last_movement_date else None,
            'days_since_received': (datetime.now().date() - item.received_date).days if item.received_date else None,
            'expires_in_days': (item.expiry_date - datetime.now().date()).days if item.expiry_date else None
        }
```

#### Frontend Search Interface
```vue
<!-- InventorySearch.vue -->
<template>
  <div class="inventory-search">
    <!-- Search Bar -->
    <el-row :gutter="20">
      <el-col :span="18">
        <el-autocomplete
          v-model="searchQuery"
          :fetch-suggestions="fetchSuggestions"
          placeholder="Search by item name, code, or description"
          @select="onSuggestionSelect"
          @keyup.enter="performSearch"
          clearable
          style="width: 100%"
        >
          <template #suffix>
            <el-button @click="performSearch" :icon="Search" />
          </template>
        </el-autocomplete>
      </el-col>
      
      <el-col :span="6">
        <el-button-group style="width: 100%">
          <el-button @click="showAdvancedFilters = !showAdvancedFilters">
            <el-icon><Filter /></el-icon> Filters
          </el-button>
          <el-button @click="exportResults" :disabled="!hasResults">
            <el-icon><Download /></el-icon> Export
          </el-button>
        </el-button-group>
      </el-col>
    </el-row>
    
    <!-- Advanced Filters -->
    <el-collapse-transition>
      <el-card v-show="showAdvancedFilters" style="margin-top: 15px;">
        <template #header>
          <span>Advanced Filters</span>
          <el-button 
            style="float: right; margin-top: -5px;" 
            type="text" 
            @click="clearAllFilters"
          >
            Clear All
          </el-button>
        </template>
        
        <el-form :model="filters" label-width="120px">
          <el-row :gutter="20">
            <el-col :span="6">
              <el-form-item label="Status">
                <el-select v-model="filters.status" multiple placeholder="Select status">
                  <el-option label="Available" value="Available" />
                  <el-option label="Reserved" value="Reserved" />
                  <el-option label="Damaged" value="Damaged" />
                  <el-option label="On Hold" value="On Hold" />
                  <el-option label="Expired" value="Expired" />
                </el-select>
              </el-form-item>
            </el-col>
            
            <el-col :span="6">
              <el-form-item label="Zone">
                <el-select v-model="filters.zone" placeholder="Select zone">
                  <el-option label="Zone A" value="A" />
                  <el-option label="Zone B" value="B" />
                  <el-option label="Zone C" value="C" />
                </el-select>
              </el-form-item>
            </el-col>
            
            <el-col :span="6">
              <el-form-item label="Category">
                <el-select v-model="filters.category" filterable placeholder="Select category">
                  <el-option 
                    v-for="category in categories" 
                    :key="category" 
                    :label="category" 
                    :value="category" 
                  />
                </el-select>
              </el-form-item>
            </el-col>
            
            <el-col :span="6">
              <el-form-item label="Quantity Range">
                <el-input-number v-model="filters.minQuantity" placeholder="Min" style="width: 45%" />
                <span style="margin: 0 5px;">-</span>
                <el-input-number v-model="filters.maxQuantity" placeholder="Max" style="width: 45%" />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="Received Date">
                <el-date-picker
                  v-model="filters.receivedDateRange"
                  type="daterange"
                  range-separator="To"
                  start-placeholder="Start date"
                  end-placeholder="End date"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            
            <el-col :span="6">
              <el-form-item label="Expires Within">
                <el-input-number 
                  v-model="filters.expiresWithinDays" 
                  placeholder="Days"
                  :min="0"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            
            <el-col :span="6">
              <el-form-item>
                <el-button type="primary" @click="applyFilters">Apply Filters</el-button>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>
    </el-collapse-transition>
    
    <!-- Results Table -->
    <el-table 
      :data="searchResults.items" 
      v-loading="loading"
      @row-click="viewItemDetails"
      style="margin-top: 20px;"
    >
      <el-table-column prop="item_code" label="Item Code" width="120" />
      <el-table-column prop="item_name" label="Item Name" min-width="200" />
      <el-table-column prop="storage_location" label="Location" width="120" />
      <el-table-column prop="available_quantity" label="Available" width="100" align="right">
        <template #default="{ row }">
          {{ row.available_quantity }} {{ row.unit }}
        </template>
      </el-table-column>
      <el-table-column prop="condition_status" label="Condition" width="100">
        <template #default="{ row }">
          <el-tag :type="getConditionTagType(row.condition_status)">
            {{ row.condition_status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="item_status" label="Status" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusTagType(row.item_status)">
            {{ row.item_status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="received_date" label="Received" width="120">
        <template #default="{ row }">
          {{ formatDate(row.received_date) }}
        </template>
      </el-table-column>
      <el-table-column label="Actions" width="150">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetails(row)">Details</el-button>
          <el-button size="small" type="primary" @click="reserveItem(row)">Reserve</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- Pagination -->
    <el-pagination
      v-if="searchResults.pagination"
      background
      layout="total, sizes, prev, pager, next, jumper"
      :current-page="searchResults.pagination.page"
      :page-sizes="[10, 20, 50, 100]"
      :page-size="searchResults.pagination.per_page"
      :total="searchResults.pagination.total"
      @size-change="onPageSizeChange"
      @current-change="onCurrentPageChange"
      style="margin-top: 20px; text-align: center;"
    />
  </div>
</template>
```

### Test Scenarios
1. **Text Search**: Test search across item names, codes, descriptions
2. **Advanced Filtering**: Test all filter combinations and performance
3. **Auto-complete**: Test search suggestions functionality
4. **Item Details**: Test comprehensive item detail views
5. **Export Functionality**: Test Excel export with filters applied
6. **Performance**: Test search performance with large datasets
7. **Permissions**: Test role-based search result filtering

### Dependencies
- Inventory data from goods receipt (Story 4.1)
- Storage location system (Story 4.2)
- User role and permission system
- Export functionality integration

**Story Points Breakdown**: Backend (8) + Frontend (7) + Testing (2) = 17

---

## Story 4.4: Inventory Item Acceptance Workflow
**Story ID**: ERP-E04-S04  
**Title**: Enable Original Requesters to Accept Delivered Items  
**Priority**: P0  
**Story Points**: 21  

### User Story
**As an** Engineer (original requester)  
**I want to** accept delivered items and confirm they meet my requirements  
**So that** I can ensure item quality and trigger the release of items to available inventory  

### Background & Context
When items are received in the warehouse, the original requesters must inspect and accept them before they become available for general use. This ensures quality control and provides final approval from the end users who will use the items.

### Acceptance Criteria
**AC1**: Given items I requested have been received, when they arrive, then I receive notification with item details and location information for inspection

**AC2**: Given I need to inspect items, when I access the acceptance interface, then I can see all my pending acceptances with item details, quantities, and photos from receipt

**AC3**: Given I inspect items, when I evaluate them, then I can accept all quantities, accept partial quantities, or reject items with detailed reasons

**AC4**: Given I accept items, when I confirm acceptance, then I can add quality notes and the items status changes to "Available" for general use

**AC5**: Given I reject items, when I provide rejection reasons, then the items are marked as "On Hold" and notifications are sent to procurement and warehouse teams

**AC6**: Given I have accepted or rejected items, when the process completes, then I receive confirmation and the inventory system is automatically updated

### Technical Implementation Notes

#### API Endpoints Required
```
GET /api/v1/inventory/pending-acceptance       # Get items awaiting user acceptance
PUT /api/v1/inventory/{id}/accept              # Accept inventory item
PUT /api/v1/inventory/{id}/reject              # Reject inventory item
POST /api/v1/inventory/{id}/quality-notes      # Add quality inspection notes
GET /api/v1/inventory/my-accepted              # Get user's accepted items history
GET /api/v1/inventory/acceptance-dashboard     # Acceptance dashboard data
```

#### Database Changes
```sql
-- Item acceptance tracking
CREATE TABLE inventory_acceptances (
    id SERIAL PRIMARY KEY,
    inventory_item_id INTEGER NOT NULL REFERENCES inventory_items(id) ON DELETE CASCADE,
    original_requester_id INTEGER NOT NULL REFERENCES users(id), -- From original requisition
    acceptance_status VARCHAR(20) NOT NULL DEFAULT 'Pending' CHECK (
        acceptance_status IN ('Pending', 'Accepted', 'Partially Accepted', 'Rejected')
    ),
    inspected_quantity DECIMAL(10,3),
    accepted_quantity DECIMAL(10,3) DEFAULT 0,
    rejected_quantity DECIMAL(10,3) DEFAULT 0,
    quality_rating INTEGER CHECK (quality_rating BETWEEN 1 AND 5),
    quality_notes TEXT,
    rejection_reason TEXT,
    acceptance_photos JSONB, -- Array of photo paths
    inspection_date TIMESTAMP,
    acceptance_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quality inspection checklist (configurable)
CREATE TABLE quality_inspection_criteria (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    criterion_name VARCHAR(255) NOT NULL,
    description TEXT,
    is_mandatory BOOLEAN DEFAULT FALSE,
    rating_scale INTEGER DEFAULT 5, -- 1-5 scale
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inspection results
CREATE TABLE inspection_results (
    id SERIAL PRIMARY KEY,
    acceptance_id INTEGER NOT NULL REFERENCES inventory_acceptances(id) ON DELETE CASCADE,
    criterion_id INTEGER NOT NULL REFERENCES quality_inspection_criteria(id),
    rating INTEGER NOT NULL,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notification tracking for acceptances
CREATE TABLE acceptance_notifications (
    id SERIAL PRIMARY KEY,
    inventory_item_id INTEGER NOT NULL REFERENCES inventory_items(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    notification_type VARCHAR(50) NOT NULL, -- 'acceptance_required', 'acceptance_reminder', 'acceptance_overdue'
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    acknowledged_at TIMESTAMP
);

-- Add acceptance fields to inventory_items
ALTER TABLE inventory_items ADD COLUMN requires_acceptance BOOLEAN DEFAULT FALSE;
ALTER TABLE inventory_items ADD COLUMN acceptance_status VARCHAR(20) DEFAULT 'Not Required';
ALTER TABLE inventory_items ADD COLUMN accepted_by INTEGER REFERENCES users(id);
ALTER TABLE inventory_items ADD COLUMN accepted_at TIMESTAMP;
ALTER TABLE inventory_items ADD COLUMN acceptance_notes TEXT;

-- Indexes
CREATE INDEX idx_acceptances_requester ON inventory_acceptances(original_requester_id, acceptance_status);
CREATE INDEX idx_acceptances_item ON inventory_acceptances(inventory_item_id);
CREATE INDEX idx_acceptance_notifications_user ON acceptance_notifications(user_id, sent_at DESC);
```

#### Acceptance Service
```python
class InventoryAcceptanceService:
    def create_acceptance_requirements(self, goods_receipt_id: int):
        """Create acceptance requirements when goods are received"""
        receipt = GoodsReceipt.query.get_or_404(goods_receipt_id)
        
        acceptances_created = []
        
        for receipt_item in receipt.items:
            # Get original requisition item to find requester
            po_item = receipt_item.purchase_order_item
            if not po_item or not po_item.requisition_item_id:
                continue
            
            req_item = RequisitionItem.query.get(po_item.requisition_item_id)
            if not req_item:
                continue
            
            # Create inventory item from receipt
            inventory_item = InventoryItem(
                item_code=self.generate_item_code(receipt_item),
                item_name=receipt_item.item_name,
                item_description=receipt_item.item_description,
                category=self.determine_category(receipt_item.item_name),
                unit=receipt_item.unit,
                current_quantity=receipt_item.accepted_quantity,
                unit_cost=receipt_item.unit_price,
                storage_location=receipt_item.storage_location,
                lot_batch_number=receipt_item.lot_batch_number,
                expiry_date=receipt_item.expiry_date,
                condition_status=receipt_item.condition_status,
                item_status='Pending Acceptance',
                requires_acceptance=True,
                acceptance_status='Pending',
                supplier_id=receipt.supplier_id,
                purchase_order_item_id=po_item.id,
                requisition_item_id=req_item.id,
                received_date=receipt.receipt_date,
                received_by=receipt.received_by
            )
            
            db.session.add(inventory_item)
            db.session.flush()  # Get inventory item ID
            
            # Create acceptance requirement
            acceptance = InventoryAcceptance(
                inventory_item_id=inventory_item.id,
                original_requester_id=req_item.requisition.user_id,
                inspected_quantity=receipt_item.accepted_quantity
            )
            
            db.session.add(acceptance)
            acceptances_created.append(acceptance)
            
            # Send notification to original requester
            self.send_acceptance_notification(
                inventory_item.id,
                req_item.requisition.user_id,
                'acceptance_required'
            )
        
        db.session.commit()
        return acceptances_created
    
    def get_pending_acceptances(self, user_id: int):
        """Get items waiting for user acceptance"""
        acceptances = db.session.query(InventoryAcceptance)\
            .join(InventoryItem)\
            .filter(
                InventoryAcceptance.original_requester_id == user_id,
                InventoryAcceptance.acceptance_status == 'Pending'
            )\
            .order_by(InventoryAcceptance.created_at.desc())\
            .all()
        
        result = []
        for acceptance in acceptances:
            item = acceptance.inventory_item
            
            # Get receipt photos
            receipt_photos = []
            receipt_item = GoodsReceiptItem.query\
                .filter_by(purchase_order_item_id=item.purchase_order_item_id)\
                .first()
            
            if receipt_item:
                photos = ReceiptItemPhoto.query\
                    .filter_by(receipt_item_id=receipt_item.id)\
                    .all()
                receipt_photos = [
                    {
                        'id': photo.id,
                        'filename': photo.photo_filename,
                        'path': photo.photo_path,
                        'type': photo.photo_type,
                        'description': photo.description
                    } for photo in photos
                ]
            
            result.append({
                'acceptance_id': acceptance.id,
                'item': self.serialize_inventory_item(item),
                'inspected_quantity': float(acceptance.inspected_quantity),
                'days_pending': (datetime.now() - acceptance.created_at).days,
                'receipt_photos': receipt_photos,
                'quality_criteria': self.get_quality_criteria(item.category)
            })
        
        return result
    
    def process_acceptance(self, acceptance_id: int, acceptance_data: dict, user_id: int):
        """Process item acceptance or rejection"""
        acceptance = InventoryAcceptance.query.get_or_404(acceptance_id)
        
        if acceptance.original_requester_id != user_id:
            raise PermissionError("Only the original requester can accept this item")
        
        if acceptance.acceptance_status != 'Pending':
            raise ValidationError("Item has already been processed")
        
        action = acceptance_data.get('action')  # 'accept', 'partial', 'reject'
        accepted_quantity = acceptance_data.get('accepted_quantity', 0)
        rejected_quantity = acceptance_data.get('rejected_quantity', 0)
        quality_rating = acceptance_data.get('quality_rating')
        quality_notes = acceptance_data.get('quality_notes')
        rejection_reason = acceptance_data.get('rejection_reason')
        
        # Update acceptance record
        acceptance.accepted_quantity = accepted_quantity
        acceptance.rejected_quantity = rejected_quantity
        acceptance.quality_rating = quality_rating
        acceptance.quality_notes = quality_notes
        acceptance.rejection_reason = rejection_reason
        acceptance.inspection_date = datetime.utcnow()
        
        if action == 'accept':
            acceptance.acceptance_status = 'Accepted'
            acceptance.accepted_quantity = acceptance.inspected_quantity
            acceptance.acceptance_date = datetime.utcnow()
            
            # Update inventory item
            inventory_item = acceptance.inventory_item
            inventory_item.item_status = 'Available'
            inventory_item.acceptance_status = 'Accepted'
            inventory_item.accepted_by = user_id
            inventory_item.accepted_at = datetime.utcnow()
            inventory_item.acceptance_notes = quality_notes
            
        elif action == 'partial':
            if accepted_quantity + rejected_quantity != acceptance.inspected_quantity:
                raise ValidationError("Accepted and rejected quantities must equal inspected quantity")
            
            acceptance.acceptance_status = 'Partially Accepted'
            acceptance.acceptance_date = datetime.utcnow()
            
            # Split inventory item
            inventory_item = acceptance.inventory_item
            
            if accepted_quantity > 0:
                # Update original item for accepted portion
                inventory_item.current_quantity = accepted_quantity
                inventory_item.item_status = 'Available'
                inventory_item.acceptance_status = 'Accepted'
                inventory_item.accepted_by = user_id
                inventory_item.accepted_at = datetime.utcnow()
            
            if rejected_quantity > 0:
                # Create new item for rejected portion
                rejected_item = InventoryItem(
                    item_code=f"{inventory_item.item_code}-REJ",
                    item_name=inventory_item.item_name,
                    item_description=inventory_item.item_description,
                    category=inventory_item.category,
                    unit=inventory_item.unit,
                    current_quantity=rejected_quantity,
                    unit_cost=inventory_item.unit_cost,
                    storage_location=inventory_item.storage_location,
                    lot_batch_number=inventory_item.lot_batch_number,
                    expiry_date=inventory_item.expiry_date,
                    condition_status='Rejected',
                    item_status='On Hold',
                    acceptance_status='Rejected',
                    requires_acceptance=False
                )
                db.session.add(rejected_item)
                
        elif action == 'reject':
            acceptance.acceptance_status = 'Rejected'
            acceptance.rejected_quantity = acceptance.inspected_quantity
            
            # Update inventory item
            inventory_item = acceptance.inventory_item
            inventory_item.item_status = 'On Hold'
            inventory_item.acceptance_status = 'Rejected'
            inventory_item.condition_status = 'Rejected'
            inventory_item.acceptance_notes = rejection_reason
        
        # Process quality inspection results
        inspection_results = acceptance_data.get('inspection_results', [])
        for result in inspection_results:
            inspection = InspectionResult(
                acceptance_id=acceptance.id,
                criterion_id=result['criterion_id'],
                rating=result['rating'],
                comments=result.get('comments')
            )
            db.session.add(inspection)
        
        # Send notifications
        if action in ['partial', 'reject']:
            self.send_rejection_notifications(acceptance)
        
        db.session.commit()
        return acceptance
    
    def send_acceptance_notification(self, inventory_item_id: int, user_id: int, notification_type: str):
        """Send acceptance notification to user"""
        notification = AcceptanceNotification(
            inventory_item_id=inventory_item_id,
            user_id=user_id,
            notification_type=notification_type
        )
        db.session.add(notification)
        
        # Send email notification
        item = InventoryItem.query.get(inventory_item_id)
        user = User.query.get(user_id)
        
        if item and user:
            self.email_service.send_acceptance_notification(
                user.email,
                {
                    'item_name': item.item_name,
                    'quantity': item.current_quantity,
                    'location': item.storage_location,
                    'acceptance_url': f"{current_app.config['BASE_URL']}/inventory/accept/{item.id}"
                }
            )
    
    def send_rejection_notifications(self, acceptance: InventoryAcceptance):
        """Send notifications when items are rejected"""
        item = acceptance.inventory_item
        
        # Notify procurement team
        procurement_users = User.query.filter_by(role='Procurement').all()
        for user in procurement_users:
            self.email_service.send_rejection_notification(
                user.email,
                {
                    'item_name': item.item_name,
                    'quantity': acceptance.rejected_quantity,
                    'reason': acceptance.rejection_reason,
                    'requester': acceptance.original_requester.username
                }
            )
    
    def get_quality_criteria(self, category: str):
        """Get quality inspection criteria for category"""
        criteria = QualityInspectionCriterion.query\
            .filter_by(category=category, is_active=True)\
            .order_by(QualityInspectionCriterion.criterion_name)\
            .all()
        
        return [
            {
                'id': criterion.id,
                'name': criterion.criterion_name,
                'description': criterion.description,
                'is_mandatory': criterion.is_mandatory,
                'rating_scale': criterion.rating_scale
            } for criterion in criteria
        ]
```

### Test Scenarios
1. **Notification System**: Test acceptance notification delivery
2. **Acceptance Processing**: Test full acceptance workflow
3. **Partial Acceptance**: Test partial acceptance with item splitting
4. **Rejection Handling**: Test rejection workflow and notifications
5. **Quality Inspection**: Test quality criteria evaluation
6. **Permission Validation**: Test that only requesters can accept their items
7. **Status Updates**: Test inventory status changes after acceptance
8. **Dashboard Integration**: Test acceptance dashboard functionality

### Dependencies
- Goods receipt process (Story 4.1)
- Inventory item creation
- User notification system
- Email service integration
- Purchase order and requisition linking

**Story Points Breakdown**: Backend (12) + Frontend (6) + Notifications (2) + Testing (1) = 21

---

## Story 4.5: Inventory Reservations and Allocation
**Story ID**: ERP-E04-S05  
**Title**: Implement Inventory Reservation System  
**Priority**: P1  
**Story Points**: 17  

### User Story
**As an** Engineer  
**I want to** reserve inventory items for my projects  
**So that** I can ensure item availability and prevent others from using items I need  

### Background & Context
Users need to reserve items for upcoming projects or activities to prevent shortages and ensure availability when needed. The reservation system must track reserved quantities, expiration times, and provide release mechanisms.

### Acceptance Criteria
**AC1**: Given I find an item I need, when I reserve it, then I can specify quantity, purpose, expected usage date, and reservation duration

**AC2**: Given I have reserved items, when I view my reservations, then I can see all active reservations with expiration dates and release options

**AC3**: Given reservations expire, when the expiration time passes, then items are automatically released back to available inventory with notifications

**AC4**: Given I no longer need reserved items, when I release them manually, then they become immediately available for others

**AC5**: Given items are reserved, when others search inventory, then they can see available quantity (excluding reserved) and reservation information

**AC6**: Given I am a manager, when I review reservations, then I can see team reservations and override/release reservations if needed

### Technical Implementation Notes

#### API Endpoints Required
```
POST /api/v1/inventory/{id}/reserve            # Reserve inventory item
GET /api/v1/inventory/reservations/my          # Get user's reservations
PUT /api/v1/inventory/reservations/{id}/release # Release reservation
PUT /api/v1/inventory/reservations/{id}/extend  # Extend reservation
GET /api/v1/inventory/reservations/team        # Manager view of team reservations
POST /api/v1/inventory/reservations/cleanup    # Cleanup expired reservations
```

#### Database Changes
```sql
-- Inventory reservations
CREATE TABLE inventory_reservations (
    id SERIAL PRIMARY KEY,
    inventory_item_id INTEGER NOT NULL REFERENCES inventory_items(id) ON DELETE CASCADE,
    reserved_by INTEGER NOT NULL REFERENCES users(id),
    reserved_quantity DECIMAL(10,3) NOT NULL CHECK (reserved_quantity > 0),
    reservation_purpose TEXT NOT NULL,
    project_id INTEGER REFERENCES projects(id),
    expected_usage_date DATE,
    reservation_expires_at TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'Active' CHECK (
        status IN ('Active', 'Released', 'Expired', 'Used')
    ),
    release_reason TEXT,
    released_by INTEGER REFERENCES users(id),
    released_at TIMESTAMP,
    auto_released BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reservation history for auditing
CREATE TABLE reservation_history (
    id SERIAL PRIMARY KEY,
    reservation_id INTEGER NOT NULL REFERENCES inventory_reservations(id),
    action VARCHAR(50) NOT NULL, -- 'created', 'extended', 'released', 'expired', 'used'
    old_values JSONB,
    new_values JSONB,
    performed_by INTEGER REFERENCES users(id),
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Update inventory_items to track total reserved quantity
-- (This was already added in the previous story)

-- Indexes
CREATE INDEX idx_reservations_user ON inventory_reservations(reserved_by, status);
CREATE INDEX idx_reservations_item ON inventory_reservations(inventory_item_id, status);
CREATE INDEX idx_reservations_expiry ON inventory_reservations(reservation_expires_at) WHERE status = 'Active';
CREATE INDEX idx_reservations_project ON inventory_reservations(project_id) WHERE project_id IS NOT NULL;
```

#### Reservation Service
```python
class InventoryReservationService:
    DEFAULT_RESERVATION_HOURS = 72  # 3 days default
    MAX_RESERVATION_DAYS = 30      # Maximum reservation period
    
    def create_reservation(self, item_id: int, reservation_data: dict, user_id: int):
        """Create inventory reservation"""
        item = InventoryItem.query.get_or_404(item_id)
        
        requested_quantity = reservation_data.get('quantity')
        purpose = reservation_data.get('purpose')
        expected_usage_date = reservation_data.get('expected_usage_date')
        reservation_hours = reservation_data.get('reservation_hours', self.DEFAULT_RESERVATION_HOURS)
        project_id = reservation_data.get('project_id')
        
        # Validate reservation hours
        max_hours = self.MAX_RESERVATION_DAYS * 24
        if reservation_hours > max_hours:
            raise ValidationError(f"Maximum reservation period is {self.MAX_RESERVATION_DAYS} days")
        
        # Check if enough quantity is available
        if requested_quantity > item.available_quantity:
            raise ValidationError(f"Only {item.available_quantity} {item.unit} available for reservation")
        
        # Check user permissions (engineers can only reserve for their projects)
        user_role = self.get_user_role(user_id)
        if user_role == 'Engineer' and project_id:
            project = Project.query.get(project_id)
            if not project or not self.user_can_access_project(user_id, project_id):
                raise PermissionError("Cannot reserve items for this project")
        
        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(hours=reservation_hours)
        
        # Create reservation
        reservation = InventoryReservation(
            inventory_item_id=item_id,
            reserved_by=user_id,
            reserved_quantity=requested_quantity,
            reservation_purpose=purpose,
            project_id=project_id,
            expected_usage_date=expected_usage_date,
            reservation_expires_at=expires_at
        )
        
        # Update item reserved quantity
        item.reserved_quantity += requested_quantity
        
        db.session.add(reservation)
        
        # Log reservation creation
        self.log_reservation_action(reservation, 'created', user_id)
        
        # Send confirmation notification
        self.send_reservation_confirmation(reservation)
        
        db.session.commit()
        return reservation
    
    def release_reservation(self, reservation_id: int, user_id: int, reason: str = None):
        """Release inventory reservation"""
        reservation = InventoryReservation.query.get_or_404(reservation_id)
        
        # Check permissions
        if reservation.reserved_by != user_id:
            user_role = self.get_user_role(user_id)
            if user_role not in ['ProcurementMgr', 'Warehouse']:
                raise PermissionError("Cannot release another user's reservation")
        
        if reservation.status != 'Active':
            raise ValidationError("Reservation is not active")
        
        # Update reservation
        old_values = {
            'status': reservation.status,
            'reserved_quantity': float(reservation.reserved_quantity)
        }
        
        reservation.status = 'Released'
        reservation.release_reason = reason
        reservation.released_by = user_id
        reservation.released_at = datetime.utcnow()
        
        # Update item reserved quantity
        item = reservation.inventory_item
        item.reserved_quantity -= reservation.reserved_quantity
        
        # Log the action
        self.log_reservation_action(
            reservation, 
            'released', 
            user_id, 
            old_values=old_values,
            new_values={'status': 'Released'}
        )
        
        # Notify user if released by someone else
        if reservation.reserved_by != user_id:
            self.send_reservation_release_notification(reservation, reason)
        
        db.session.commit()
        return reservation
    
    def extend_reservation(self, reservation_id: int, additional_hours: int, user_id: int):
        """Extend reservation duration"""
        reservation = InventoryReservation.query.get_or_404(reservation_id)
        
        if reservation.reserved_by != user_id:
            raise PermissionError("Cannot extend another user's reservation")
        
        if reservation.status != 'Active':
            raise ValidationError("Cannot extend inactive reservation")
        
        # Check maximum extension limit
        total_hours = (reservation.reservation_expires_at - reservation.created_at).total_seconds() / 3600
        if total_hours + additional_hours > (self.MAX_RESERVATION_DAYS * 24):
            raise ValidationError(f"Maximum total reservation period is {self.MAX_RESERVATION_DAYS} days")
        
        # Update expiration
        old_expiry = reservation.reservation_expires_at
        reservation.reservation_expires_at += timedelta(hours=additional_hours)
        reservation.updated_at = datetime.utcnow()
        
        # Log the extension
        self.log_reservation_action(
            reservation,
            'extended',
            user_id,
            old_values={'expires_at': old_expiry.isoformat()},
            new_values={'expires_at': reservation.reservation_expires_at.isoformat()}
        )
        
        db.session.commit()
        return reservation
    
    def cleanup_expired_reservations(self):
        """Cleanup expired reservations (run as background task)"""
        expired_reservations = InventoryReservation.query.filter(
            InventoryReservation.status == 'Active',
            InventoryReservation.reservation_expires_at < datetime.utcnow()
        ).all()
        
        released_count = 0
        
        for reservation in expired_reservations:
            # Update reservation status
            reservation.status = 'Expired'
            reservation.auto_released = True
            reservation.released_at = datetime.utcnow()
            
            # Update item reserved quantity
            item = reservation.inventory_item
            item.reserved_quantity -= reservation.reserved_quantity
            
            # Log auto-release
            self.log_reservation_action(reservation, 'expired', None)
            
            # Send expiration notification
            self.send_reservation_expiry_notification(reservation)
            
            released_count += 1
        
        if released_count > 0:
            db.session.commit()
            logger.info(f"Auto-released {released_count} expired reservations")
        
        return released_count
    
    def get_user_reservations(self, user_id: int, include_inactive: bool = False):
        """Get user's reservations"""
        query = InventoryReservation.query.filter_by(reserved_by=user_id)
        
        if not include_inactive:
            query = query.filter_by(status='Active')
        
        reservations = query.order_by(InventoryReservation.created_at.desc()).all()
        
        result = []
        for reservation in reservations:
            item = reservation.inventory_item
            
            # Calculate time remaining
            time_remaining = None
            if reservation.status == 'Active':
                remaining_seconds = (reservation.reservation_expires_at - datetime.utcnow()).total_seconds()
                time_remaining = max(0, remaining_seconds / 3600)  # Hours remaining
            
            result.append({
                'id': reservation.id,
                'item': {
                    'id': item.id,
                    'name': item.item_name,
                    'code': item.item_code,
                    'location': item.storage_location,
                    'unit': item.unit
                },
                'reserved_quantity': float(reservation.reserved_quantity),
                'purpose': reservation.reservation_purpose,
                'project_id': reservation.project_id,
                'expected_usage_date': reservation.expected_usage_date.isoformat() if reservation.expected_usage_date else None,
                'expires_at': reservation.reservation_expires_at.isoformat(),
                'time_remaining_hours': round(time_remaining, 1) if time_remaining is not None else None,
                'status': reservation.status,
                'created_at': reservation.created_at.isoformat()
            })
        
        return result
    
    def log_reservation_action(self, reservation: InventoryReservation, action: str, user_id: int, 
                              old_values: dict = None, new_values: dict = None):
        """Log reservation action for audit trail"""
        history = ReservationHistory(
            reservation_id=reservation.id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            performed_by=user_id
        )
        db.session.add(history)
    
    def send_reservation_confirmation(self, reservation: InventoryReservation):
        """Send reservation confirmation email"""
        user = User.query.get(reservation.reserved_by)
        item = reservation.inventory_item
        
        self.email_service.send_reservation_confirmation(
            user.email,
            {
                'item_name': item.item_name,
                'quantity': reservation.reserved_quantity,
                'unit': item.unit,
                'location': item.storage_location,
                'expires_at': reservation.reservation_expires_at.strftime('%Y-%m-%d %H:%M'),
                'purpose': reservation.reservation_purpose
            }
        )
```

### Test Scenarios
1. **Reservation Creation**: Test creating reservations with various parameters
2. **Availability Checking**: Test available quantity calculations with reservations
3. **Expiration Processing**: Test automatic expiration cleanup
4. **Manual Release**: Test user-initiated reservation releases
5. **Extension Functionality**: Test reservation duration extensions
6. **Permission Validation**: Test reservation access controls
7. **Manager Override**: Test manager ability to release team reservations
8. **Notification System**: Test all reservation-related notifications

### Dependencies
- Inventory search and management (Story 4.3)
- User permissions and project management
- Email notification service
- Background job processing for cleanup

**Story Points Breakdown**: Backend (10) + Frontend (5) + Testing (2) = 17

---

## Story 4.6: Inventory Reporting and Analytics
**Story ID**: ERP-E04-S06  
**Title**: Comprehensive Inventory Reports and Analytics  
**Priority**: P1  
**Story Points**: 13  

### User Story
**As a** Warehouse Manager and Procurement Manager  
**I want to** generate comprehensive inventory reports and analytics  
**So that** I can optimize inventory levels, track utilization, and make data-driven decisions  

### Background & Context
Management needs visibility into inventory performance, utilization rates, aging analysis, and cost tracking to optimize warehouse operations and procurement strategies.

### Acceptance Criteria
**AC1**: Given I need inventory insights, when I access the inventory dashboard, then I can see key metrics: total inventory value, item count, location utilization, and turnover rates

**AC2**: Given I want to analyze inventory, when I generate reports, then I can create reports for: aging analysis, slow-moving items, location utilization, and cost analysis

**AC3**: Given I track performance, when I view analytics, then I can see trends: receipt patterns, acceptance rates, reservation utilization, and space optimization

**AC4**: Given I need compliance reports, when I generate audit reports, then I can export inventory movements, acceptance history, and current stock positions

**AC5**: Given I optimize operations, when I view recommendations, then the system suggests reorder points, space reallocation, and process improvements

### Technical Implementation Notes

#### API Endpoints Required
```
GET /api/v1/inventory/analytics/dashboard      # Dashboard metrics
GET /api/v1/inventory/analytics/aging          # Aging analysis
GET /api/v1/inventory/analytics/utilization    # Location utilization
POST /api/v1/inventory/reports/generate        # Generate custom reports
GET /api/v1/inventory/analytics/recommendations # Optimization recommendations
```

#### Analytics Views and Queries
```sql
-- Inventory aging analysis view
CREATE MATERIALIZED VIEW inventory_aging_analysis AS
SELECT 
    ii.id,
    ii.item_code,
    ii.item_name,
    ii.category,
    ii.current_quantity,
    ii.unit_cost,
    (ii.current_quantity * ii.unit_cost) as total_value,
    ii.received_date,
    ii.storage_location,
    EXTRACT(days FROM (CURRENT_DATE - ii.received_date)) as days_in_inventory,
    CASE 
        WHEN EXTRACT(days FROM (CURRENT_DATE - ii.received_date)) <= 30 THEN '0-30 days'
        WHEN EXTRACT(days FROM (CURRENT_DATE - ii.received_date)) <= 90 THEN '31-90 days'
        WHEN EXTRACT(days FROM (CURRENT_DATE - ii.received_date)) <= 180 THEN '91-180 days'
        WHEN EXTRACT(days FROM (CURRENT_DATE - ii.received_date)) <= 365 THEN '181-365 days'
        ELSE 'Over 1 year'
    END as aging_bucket
FROM inventory_items ii
WHERE ii.item_status = 'Available'
AND ii.current_quantity > 0;

-- Location utilization summary
CREATE MATERIALIZED VIEW location_utilization_summary AS
SELECT 
    sl.location_code,
    sl.zone,
    sl.capacity_limit,
    sl.current_utilization,
    CASE 
        WHEN sl.capacity_limit > 0 THEN (sl.current_utilization / sl.capacity_limit) * 100
        ELSE 0
    END as utilization_percentage,
    COUNT(ii.id) as item_types,
    SUM(ii.current_quantity * ii.unit_cost) as total_value,
    AVG(EXTRACT(days FROM (CURRENT_DATE - ii.received_date))) as avg_age_days
FROM storage_locations sl
LEFT JOIN inventory_items ii ON sl.location_code = ii.storage_location
WHERE sl.is_active = TRUE
GROUP BY sl.location_code, sl.zone, sl.capacity_limit, sl.current_utilization;

-- Refresh function for materialized views
CREATE OR REPLACE FUNCTION refresh_inventory_analytics_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW inventory_aging_analysis;
    REFRESH MATERIALIZED VIEW location_utilization_summary;
END;
$$ LANGUAGE plpgsql;
```

#### Analytics Service
```python
class InventoryAnalyticsService:
    def get_dashboard_metrics(self):
        """Get comprehensive inventory dashboard metrics"""
        # Total inventory metrics
        total_metrics = db.session.query(
            func.count(InventoryItem.id).label('total_items'),
            func.sum(InventoryItem.current_quantity * InventoryItem.unit_cost).label('total_value'),
            func.count(func.distinct(InventoryItem.storage_location)).label('locations_used'),
            func.count(func.distinct(InventoryItem.category)).label('categories')
        ).filter(
            InventoryItem.item_status == 'Available',
            InventoryItem.current_quantity > 0
        ).first()
        
        # Status distribution
        status_dist = db.session.query(
            InventoryItem.item_status,
            func.count(InventoryItem.id).label('count'),
            func.sum(InventoryItem.current_quantity * InventoryItem.unit_cost).label('value')
        ).filter(
            InventoryItem.current_quantity > 0
        ).group_by(InventoryItem.item_status).all()
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_receipts = db.session.query(func.count(InventoryItem.id)).filter(
            InventoryItem.received_date >= thirty_days_ago
        ).scalar()
        
        recent_movements = db.session.query(func.count(InventoryMovement.id)).filter(
            InventoryMovement.movement_date >= thirty_days_ago
        ).scalar()
        
        # Location utilization summary
        location_stats = db.session.query(
            func.avg(case([(StorageLocation.capacity_limit > 0, 
                           StorageLocation.current_utilization / StorageLocation.capacity_limit * 100)], 
                         else_=0)).label('avg_utilization'),
            func.count(StorageLocation.id).label('total_locations')
        ).filter(StorageLocation.is_active == True).first()
        
        return {
            'totals': {
                'items': total_metrics.total_items or 0,
                'value': float(total_metrics.total_value or 0),
                'locations_used': total_metrics.locations_used or 0,
                'categories': total_metrics.categories or 0
            },
            'status_distribution': [
                {
                    'status': status.item_status,
                    'count': status.count,
                    'value': float(status.value or 0)
                } for status in status_dist
            ],
            'recent_activity': {
                'receipts_30_days': recent_receipts or 0,
                'movements_30_days': recent_movements or 0
            },
            'location_utilization': {
                'average_utilization': float(location_stats.avg_utilization or 0),
                'total_locations': location_stats.total_locations or 0
            }
        }
    
    def get_aging_analysis(self, category: str = None):
        """Get inventory aging analysis"""
        query = text("""
            SELECT 
                aging_bucket,
                COUNT(*) as item_count,
                SUM(current_quantity) as total_quantity,
                SUM(total_value) as total_value,
                AVG(days_in_inventory) as avg_days
            FROM inventory_aging_analysis
            WHERE (:category IS NULL OR category = :category)
            GROUP BY aging_bucket
            ORDER BY 
                CASE aging_bucket
                    WHEN '0-30 days' THEN 1
                    WHEN '31-90 days' THEN 2
                    WHEN '91-180 days' THEN 3
                    WHEN '181-365 days' THEN 4
                    WHEN 'Over 1 year' THEN 5
                END
        """)
        
        result = db.session.execute(query, {'category': category}).fetchall()
        
        return [
            {
                'aging_bucket': row.aging_bucket,
                'item_count': row.item_count,
                'total_quantity': float(row.total_quantity),
                'total_value': float(row.total_value),
                'avg_days': round(float(row.avg_days), 1)
            } for row in result
        ]
    
    def get_slow_moving_items(self, days_threshold: int = 90, limit: int = 50):
        """Identify slow-moving inventory items"""
        threshold_date = datetime.now() - timedelta(days=days_threshold)
        
        # Items with no recent movements
        slow_items = db.session.query(
            InventoryItem.id,
            InventoryItem.item_code,
            InventoryItem.item_name,
            InventoryItem.category,
            InventoryItem.current_quantity,
            InventoryItem.unit_cost,
            (InventoryItem.current_quantity * InventoryItem.unit_cost).label('total_value'),
            InventoryItem.received_date,
            InventoryItem.storage_location,
            func.max(InventoryMovement.movement_date).label('last_movement')
        ).outerjoin(InventoryMovement)\
        .filter(
            InventoryItem.item_status == 'Available',
            InventoryItem.current_quantity > 0,
            InventoryItem.received_date < threshold_date
        ).group_by(
            InventoryItem.id
        ).having(
            or_(
                func.max(InventoryMovement.movement_date).is_(None),
                func.max(InventoryMovement.movement_date) < threshold_date
            )
        ).order_by(
            (InventoryItem.current_quantity * InventoryItem.unit_cost).desc()
        ).limit(limit).all()
        
        return [
            {
                'id': item.id,
                'item_code': item.item_code,
                'item_name': item.item_name,
                'category': item.category,
                'current_quantity': float(item.current_quantity),
                'unit_cost': float(item.unit_cost),
                'total_value': float(item.total_value),
                'received_date': item.received_date.isoformat(),
                'storage_location': item.storage_location,
                'days_since_movement': (datetime.now().date() - 
                    (item.last_movement.date() if item.last_movement else item.received_date)).days,
                'last_movement': item.last_movement.isoformat() if item.last_movement else None
            } for item in slow_items
        ]
```

### Test Scenarios
1. **Dashboard Metrics**: Test dashboard data accuracy and performance
2. **Aging Analysis**: Test inventory aging calculations and categorization
3. **Utilization Reports**: Test location utilization analytics
4. **Slow Moving Analysis**: Test identification of slow-moving items
5. **Report Generation**: Test custom report creation and export
6. **Performance**: Test analytics performance with large datasets

### Dependencies
- Inventory data from all previous stories
- Materialized view refresh scheduling
- Report generation and export services
- Dashboard visualization components

**Story Points Breakdown**: Backend (7) + Frontend (4) + Analytics (1) + Testing (1) = 13

---

## Epic Summary

### Total Story Points: 118
- Story 4.1: Flexible Goods Receipt Process (25 points)
- Story 4.2: Hierarchical Storage Location Management (21 points)
- Story 4.3: Advanced Inventory Search and Management (17 points)
- Story 4.4: Inventory Item Acceptance Workflow (21 points)
- Story 4.5: Inventory Reservations and Allocation (17 points)
- Story 4.6: Inventory Reporting and Analytics (13 points)

### Epic Dependencies
1. **Core Systems**: Authentication (Epic 1), Purchase Orders (Epic 3)
2. **Infrastructure**: File storage for photos, email notifications, background jobs
3. **Data Integration**: Purchase order linking, requisition traceability
4. **External Services**: Photo storage, email service, report generation

### Epic Risks & Mitigations
- **Risk**: Complex location hierarchy causing user confusion
  - **Mitigation**: Intuitive UI design, location suggestion system, comprehensive training
- **Risk**: Inventory accuracy issues affecting business operations
  - **Mitigation**: Robust validation, audit trails, regular reconciliation processes
- **Risk**: Performance issues with large inventory datasets
  - **Mitigation**: Database optimization, materialized views, efficient indexing
- **Risk**: Acceptance workflow delays affecting operations
  - **Mitigation**: Automated reminders, escalation procedures, manager override capabilities

### Success Criteria
- Item location time reduced by 80% through systematic organization
- 100% inventory movement tracking with complete audit trails
- Goods receipt processing time reduced by 60% through digital workflows
- Zero inventory discrepancies through acceptance validation
- Space utilization increased by 30% through optimization analytics
- User satisfaction score >4.2/5.0 for inventory management processes

This epic provides comprehensive inventory and warehouse management that bridges the gap between purchase order receipt and item availability, ensuring accurate tracking, optimal space utilization, and seamless integration with the broader ERP workflow.