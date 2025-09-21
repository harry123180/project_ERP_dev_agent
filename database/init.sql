-- PostgreSQL Database Schema for ERP System
-- Created from SQLite migration

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if they exist (for clean installation)
DROP TABLE IF EXISTS storage_history CASCADE;
DROP TABLE IF EXISTS inventory_movements CASCADE;
DROP TABLE IF EXISTS inventory_batches CASCADE;
DROP TABLE IF EXISTS logistics_events CASCADE;
DROP TABLE IF EXISTS request_order_items CASCADE;
DROP TABLE IF EXISTS request_orders CASCADE;
DROP TABLE IF EXISTS purchase_order_items CASCADE;
DROP TABLE IF EXISTS purchase_orders CASCADE;
DROP TABLE IF EXISTS item_categories CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS storages CASCADE;

-- Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    chinese_name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    job_title VARCHAR(100),
    role VARCHAR(50) NOT NULL DEFAULT 'Everyone',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Projects table
CREATE TABLE projects (
    project_id VARCHAR(50) PRIMARY KEY,
    project_name VARCHAR(200) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    budget DECIMAL(15, 2),
    actual_cost DECIMAL(15, 2) DEFAULT 0,
    manager_id INTEGER REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers table
CREATE TABLE suppliers (
    supplier_id VARCHAR(50) PRIMARY KEY,
    supplier_name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(50),
    email VARCHAR(100),
    address TEXT,
    supplier_type VARCHAR(20) DEFAULT 'domestic',
    tax_id VARCHAR(20),
    payment_terms VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Item categories table
CREATE TABLE item_categories (
    category_code VARCHAR(10) PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_category VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Request orders (requisitions) table
CREATE TABLE request_orders (
    request_order_no VARCHAR(50) PRIMARY KEY,
    requester_id INTEGER NOT NULL REFERENCES users(user_id),
    requester_name VARCHAR(100) NOT NULL,
    usage_type VARCHAR(20) NOT NULL,
    project_id VARCHAR(50) REFERENCES projects(project_id),
    submit_date DATE DEFAULT CURRENT_DATE,
    order_status VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Request order items table
CREATE TABLE request_order_items (
    detail_id SERIAL PRIMARY KEY,
    request_order_no VARCHAR(50) NOT NULL REFERENCES request_orders(request_order_no) ON DELETE CASCADE,
    item_name VARCHAR(200) NOT NULL,
    item_quantity DECIMAL(10, 2) NOT NULL,
    item_unit VARCHAR(20) NOT NULL,
    item_specification TEXT,
    item_description TEXT,
    item_category VARCHAR(10) REFERENCES item_categories(category_code),
    item_status VARCHAR(20) NOT NULL DEFAULT 'draft',
    acceptance_status VARCHAR(20) DEFAULT 'pending_acceptance',
    supplier_id VARCHAR(50) REFERENCES suppliers(supplier_id),
    unit_price DECIMAL(10, 2),
    material_serial_no VARCHAR(50),
    status_note TEXT,
    needs_acceptance BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Purchase orders table
CREATE TABLE purchase_orders (
    purchase_order_no VARCHAR(50) PRIMARY KEY,
    supplier_id VARCHAR(50) NOT NULL REFERENCES suppliers(supplier_id),
    creator_id INTEGER NOT NULL REFERENCES users(user_id),
    create_date DATE DEFAULT CURRENT_DATE,
    purchase_date DATE,
    payment_status VARCHAR(20) DEFAULT 'pending',
    purchase_status VARCHAR(20) DEFAULT 'draft',
    delivery_status VARCHAR(20) DEFAULT 'not_shipped',
    output_person_id INTEGER REFERENCES users(user_id),
    output_datetime TIMESTAMP,
    confirm_purchaser_id INTEGER REFERENCES users(user_id),
    confirm_purchase_datetime TIMESTAMP,
    total_amount DECIMAL(12, 2) DEFAULT 0,
    tax_amount DECIMAL(10, 2) DEFAULT 0,
    grand_total_int INTEGER DEFAULT 0,
    payment_date DATE,
    payment_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Purchase order items table
CREATE TABLE purchase_order_items (
    po_item_id SERIAL PRIMARY KEY,
    purchase_order_no VARCHAR(50) NOT NULL REFERENCES purchase_orders(purchase_order_no) ON DELETE CASCADE,
    request_item_id INTEGER REFERENCES request_order_items(detail_id),
    item_name VARCHAR(200) NOT NULL,
    item_specification TEXT,
    item_quantity DECIMAL(10, 2) NOT NULL,
    item_unit VARCHAR(20) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(12, 2),
    acceptance_quantity DECIMAL(10, 2) DEFAULT 0,
    acceptance_status VARCHAR(20) DEFAULT 'pending',
    shipped_quantity DECIMAL(10, 2) DEFAULT 0,
    shipping_status VARCHAR(20) DEFAULT 'pending',
    storage_location VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Logistics events table
CREATE TABLE logistics_events (
    event_id SERIAL PRIMARY KEY,
    purchase_order_no VARCHAR(50) NOT NULL REFERENCES purchase_orders(purchase_order_no),
    event_type VARCHAR(50) NOT NULL,
    event_date DATE NOT NULL,
    description TEXT,
    status VARCHAR(20),
    created_by INTEGER REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Storage locations table
CREATE TABLE storages (
    storage_id VARCHAR(50) PRIMARY KEY,
    storage_name VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    capacity DECIMAL(10, 2),
    current_usage DECIMAL(10, 2) DEFAULT 0,
    storage_type VARCHAR(50),
    manager VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Inventory batches table
CREATE TABLE inventory_batches (
    batch_id SERIAL PRIMARY KEY,
    batch_no VARCHAR(50) UNIQUE NOT NULL,
    po_item_id INTEGER REFERENCES purchase_order_items(po_item_id),
    item_name VARCHAR(200) NOT NULL,
    item_specification TEXT,
    quantity DECIMAL(10, 2) NOT NULL,
    remaining_quantity DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    unit_price DECIMAL(10, 2),
    storage_id VARCHAR(50) REFERENCES storages(storage_id),
    supplier_id VARCHAR(50) REFERENCES suppliers(supplier_id),
    received_date DATE NOT NULL,
    expiry_date DATE,
    batch_status VARCHAR(20) DEFAULT 'available',
    receiver_id INTEGER REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory movements table
CREATE TABLE inventory_movements (
    movement_id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES inventory_batches(batch_id),
    movement_type VARCHAR(20) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    reference_no VARCHAR(50),
    reference_type VARCHAR(50),
    from_storage_id VARCHAR(50) REFERENCES storages(storage_id),
    to_storage_id VARCHAR(50) REFERENCES storages(storage_id),
    movement_date DATE NOT NULL,
    reason TEXT,
    operator_id INTEGER REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Storage history table
CREATE TABLE storage_history (
    history_id SERIAL PRIMARY KEY,
    storage_id VARCHAR(50) NOT NULL REFERENCES storages(storage_id),
    request_item_id INTEGER REFERENCES request_order_items(detail_id),
    po_item_id INTEGER REFERENCES purchase_order_items(po_item_id),
    operation_type VARCHAR(10) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    operation_date DATE NOT NULL,
    operator_id INTEGER REFERENCES users(user_id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_request_orders_requester ON request_orders(requester_id);
CREATE INDEX idx_request_orders_status ON request_orders(order_status);
CREATE INDEX idx_request_order_items_status ON request_order_items(item_status);
CREATE INDEX idx_purchase_orders_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_purchase_orders_status ON purchase_orders(purchase_status);
CREATE INDEX idx_purchase_order_items_po ON purchase_order_items(purchase_order_no);
CREATE INDEX idx_inventory_batches_storage ON inventory_batches(storage_id);
CREATE INDEX idx_inventory_movements_batch ON inventory_movements(batch_id);
CREATE INDEX idx_storage_history_storage ON storage_history(storage_id);

-- Create update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_suppliers_updated_at BEFORE UPDATE ON suppliers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_request_orders_updated_at BEFORE UPDATE ON request_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_request_order_items_updated_at BEFORE UPDATE ON request_order_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_purchase_orders_updated_at BEFORE UPDATE ON purchase_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_purchase_order_items_updated_at BEFORE UPDATE ON purchase_order_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_storages_updated_at BEFORE UPDATE ON storages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_inventory_batches_updated_at BEFORE UPDATE ON inventory_batches FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default admin user (password: admin123)
INSERT INTO users (chinese_name, username, password, role)
VALUES ('系統管理員', 'admin', 'pbkdf2:sha256:600000$8vFLVxXp2J3LWHhL$1e0e7b9f8d0c9f9e8b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6', 'Admin');

-- Insert default item categories
INSERT INTO item_categories (category_code, category_name, description) VALUES
('IT', '資訊設備', '電腦、週邊設備、軟體等'),
('OF', '辦公用品', '文具、紙張、辦公耗材等'),
('FM', '廠務設備', '生產設備、工具、維修零件等'),
('EL', '電子零件', '電子元件、電路板、線材等'),
('CH', '化學材料', '化學品、溶劑、清潔用品等'),
('SF', '安全設備', '防護用品、安全設備、消防器材等'),
('OT', '其他', '其他未分類項目');

-- Insert default storage locations
INSERT INTO storages (storage_id, storage_name, location, storage_type, manager) VALUES
('WH-001', '主倉庫', '一樓倉儲區', 'main', '倉管員'),
('WH-002', '備品倉', '二樓備品區', 'spare', '倉管員'),
('WH-003', '化學品倉', '特殊倉儲區', 'chemical', '安全管理員');

COMMENT ON DATABASE postgres IS 'ERP System Database - PostgreSQL Version';