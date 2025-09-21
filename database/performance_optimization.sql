-- ERP System Database Performance Optimization
-- Architecture Lead: Winston
-- Date: September 7, 2025
-- Purpose: Optimize database performance for production workloads

-- =====================================================
-- PERFORMANCE INDEXES FOR CRITICAL QUERIES
-- =====================================================

-- 1. REQUISITION PERFORMANCE INDEXES
-- Primary lookup patterns: user_id + status, created_at DESC
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_request_order_user_status_date
    ON request_orders(user_id, status, created_at DESC) 
    WHERE status != 'draft';

-- Status-based queries (procurement team views)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_request_order_status_priority
    ON request_orders(status, created_at DESC, priority)
    WHERE status IN ('submitted', 'in_review', 'approved');

-- 2. REQUISITION ITEMS PERFORMANCE INDEXES  
-- Full-text search on item names and specifications
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_request_items_fulltext_search
    ON request_order_items 
    USING gin(to_tsvector('english', coalesce(item_name, '') || ' ' || coalesce(item_spec, '')));

-- Item approval workflow queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_request_items_approval_status
    ON request_order_items(request_id, approval_status, created_at)
    WHERE approval_status IS NOT NULL;

-- Supplier assignment queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_request_items_supplier_assignment
    ON request_order_items(supplier_id, approval_status)
    WHERE supplier_id IS NOT NULL;

-- 3. PURCHASE ORDER PERFORMANCE INDEXES
-- Supplier-based PO queries (most common lookup)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_purchase_order_supplier_status_date
    ON purchase_orders(supplier_id, status, created_at DESC);

-- PO number lookup (exact match queries)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_purchase_order_po_no_unique
    ON purchase_orders(po_no) WHERE po_no IS NOT NULL;

-- Financial queries (accounting module)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_purchase_order_financial
    ON purchase_orders(supplier_id, status, total_amount, created_at)
    WHERE status IN ('confirmed', 'delivered', 'billed');

-- 4. PURCHASE ORDER ITEMS PERFORMANCE INDEXES
-- Link between requisitions and purchase orders
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_items_requisition_link
    ON purchase_order_items(request_item_id, po_id)
    WHERE request_item_id IS NOT NULL;

-- Receiving workflow queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_items_receiving_status
    ON purchase_order_items(po_id, receiving_status, item_reference)
    WHERE receiving_status IS NOT NULL;

-- 5. LOGISTICS & SHIPPING INDEXES
-- Shipment tracking by PO
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_logistics_events_po_tracking
    ON logistics_events(po_no, milestone_type, event_date DESC);

-- Consolidation management
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_consolidation_po_mapping
    ON consolidation_po(consolidation_id, po_id);

-- Active shipments (dashboard queries)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_logistics_active_shipments
    ON logistics_events(milestone_type, event_date DESC)
    WHERE milestone_type IN ('shipped', 'in_transit', 'customs', 'arrived');

-- 6. STORAGE & INVENTORY INDEXES
-- Hierarchical storage queries (Zone -> Shelf -> Floor)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_storage_hierarchy
    ON storage(parent_id, storage_type, zone, shelf, floor)
    WHERE parent_id IS NOT NULL;

-- Available storage locations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_storage_availability
    ON storage(storage_type, is_available, zone)
    WHERE is_available = true;

-- 7. STORAGE HISTORY & MOVEMENT TRACKING
-- Item movement tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_storage_history_item_tracking
    ON storage_history(item_reference, movement_type, movement_date DESC);

-- Location-based inventory queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_storage_history_location_inventory
    ON storage_history(storage_id, movement_type, movement_date DESC)
    WHERE movement_type IN ('in', 'issue');

-- Current inventory status (latest movement per item)
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_storage_history_current_status
    ON storage_history(item_reference, movement_date DESC, id DESC);

-- 8. USER & AUTHENTICATION INDEXES
-- Username lookup (login queries)
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username_lower
    ON users(lower(username)) WHERE username IS NOT NULL;

-- Role-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role_department
    ON users(role, department) WHERE role IS NOT NULL;

-- 9. SUPPLIER MANAGEMENT INDEXES
-- Supplier ID lookup (very frequent)
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_suppliers_supplier_id
    ON suppliers(supplier_id) WHERE supplier_id IS NOT NULL;

-- Regional supplier queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_suppliers_region_status
    ON suppliers(supplier_region, is_active)
    WHERE is_active = true;

-- 10. PROJECT MANAGEMENT INDEXES
-- Project expenditure tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_project_expenditure_tracking
    ON project_supplier_expenditure(project_id, supplier_id, expenditure_date DESC);

-- Active projects
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_active_status
    ON projects(is_active, start_date, end_date)
    WHERE is_active = true;

-- =====================================================
-- DATABASE PERFORMANCE CONFIGURATION
-- =====================================================

-- Update table statistics for better query planning
ANALYZE request_orders;
ANALYZE request_order_items;
ANALYZE purchase_orders; 
ANALYZE purchase_order_items;
ANALYZE logistics_events;
ANALYZE storage;
ANALYZE storage_history;
ANALYZE suppliers;
ANALYZE users;
ANALYZE projects;

-- =====================================================
-- QUERY PERFORMANCE VIEWS
-- =====================================================

-- Materialized view for dashboard statistics (refreshed periodically)
CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_stats AS
SELECT 
    -- Requisition statistics
    COUNT(CASE WHEN ro.status = 'draft' THEN 1 END) as draft_requisitions,
    COUNT(CASE WHEN ro.status = 'submitted' THEN 1 END) as pending_requisitions,
    COUNT(CASE WHEN ro.status = 'approved' THEN 1 END) as approved_requisitions,
    
    -- Purchase order statistics  
    COUNT(CASE WHEN po.status = 'draft' THEN 1 END) as draft_pos,
    COUNT(CASE WHEN po.status = 'confirmed' THEN 1 END) as confirmed_pos,
    SUM(CASE WHEN po.status = 'confirmed' THEN po.total_amount ELSE 0 END) as total_po_value,
    
    -- Shipping statistics
    COUNT(CASE WHEN le.milestone_type = 'shipped' THEN 1 END) as shipped_orders,
    COUNT(CASE WHEN le.milestone_type = 'arrived' THEN 1 END) as arrived_orders,
    
    -- Current timestamp
    NOW() as last_updated
FROM request_orders ro
FULL OUTER JOIN purchase_orders po ON true
FULL OUTER JOIN logistics_events le ON le.po_no = po.po_no
WHERE ro.created_at >= CURRENT_DATE - INTERVAL '30 days'
   OR po.created_at >= CURRENT_DATE - INTERVAL '30 days'
   OR le.event_date >= CURRENT_DATE - INTERVAL '30 days';

-- Create index on materialized view
CREATE INDEX IF NOT EXISTS idx_dashboard_stats_last_updated ON dashboard_stats(last_updated);

-- =====================================================
-- PERFORMANCE MONITORING FUNCTIONS
-- =====================================================

-- Function to get slow queries
CREATE OR REPLACE FUNCTION get_slow_queries()
RETURNS TABLE(
    query_text TEXT,
    calls BIGINT,
    total_time DOUBLE PRECISION,
    mean_time DOUBLE PRECISION,
    rows_per_call BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pg_stat_statements.query,
        pg_stat_statements.calls,
        pg_stat_statements.total_exec_time,
        pg_stat_statements.mean_exec_time,
        pg_stat_statements.rows / pg_stat_statements.calls as rows_per_call
    FROM pg_stat_statements
    WHERE pg_stat_statements.calls > 100
    ORDER BY pg_stat_statements.mean_exec_time DESC
    LIMIT 20;
END;
$$ LANGUAGE plpgsql;

-- Function to check index usage
CREATE OR REPLACE FUNCTION check_unused_indexes()
RETURNS TABLE(
    schemaname TEXT,
    tablename TEXT, 
    indexname TEXT,
    idx_tup_read BIGINT,
    idx_tup_fetch BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pg_stat_user_indexes.schemaname,
        pg_stat_user_indexes.relname,
        pg_stat_user_indexes.indexrelname,
        pg_stat_user_indexes.idx_tup_read,
        pg_stat_user_indexes.idx_tup_fetch
    FROM pg_stat_user_indexes
    WHERE pg_stat_user_indexes.idx_tup_read < 100
       OR pg_stat_user_indexes.idx_tup_fetch < 100
    ORDER BY pg_stat_user_indexes.idx_tup_read ASC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- MAINTENANCE PROCEDURES
-- =====================================================

-- Procedure to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_dashboard_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY dashboard_stats;
    
    -- Log the refresh
    INSERT INTO system_logs (log_level, message, created_at)
    VALUES ('INFO', 'Dashboard stats materialized view refreshed', NOW());
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- PERFORMANCE OPTIMIZATION VALIDATIONS
-- =====================================================

-- Validate that all critical indexes exist
DO $$
DECLARE
    missing_indexes TEXT[] := ARRAY[]::TEXT[];
    index_name TEXT;
    critical_indexes TEXT[] := ARRAY[
        'idx_request_order_user_status_date',
        'idx_purchase_order_supplier_status_date', 
        'idx_storage_history_item_tracking',
        'idx_users_username_lower',
        'idx_suppliers_supplier_id'
    ];
BEGIN
    FOREACH index_name IN ARRAY critical_indexes
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE indexname = index_name
        ) THEN
            missing_indexes := array_append(missing_indexes, index_name);
        END IF;
    END LOOP;
    
    IF array_length(missing_indexes, 1) > 0 THEN
        RAISE NOTICE 'Missing critical indexes: %', array_to_string(missing_indexes, ', ');
    ELSE
        RAISE NOTICE 'All critical indexes are present and accounted for!';
    END IF;
END $$;

-- =====================================================
-- PRODUCTION MONITORING SETUP
-- =====================================================

-- Enable query statistics collection
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Create performance monitoring table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,2),
    measurement_time TIMESTAMP DEFAULT NOW(),
    
    INDEX(measurement_time),
    INDEX(metric_name, measurement_time)
);

-- Log performance optimization completion
INSERT INTO system_logs (log_level, message, created_at)
VALUES ('INFO', 'Database performance optimization completed successfully', NOW());

COMMIT;