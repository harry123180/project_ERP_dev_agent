#!/usr/bin/env python3
"""
Project cost calculation utility function
"""

from datetime import datetime


def update_project_cost_on_purchase(purchase_order_no, db_connection):
    """
    Update project costs when a purchase order is confirmed/purchased
    This should be called whenever a purchase order status changes to 'purchased'
    """
    cursor = db_connection.cursor()
    
    # Find all request orders linked to this purchase order
    cursor.execute("""
        SELECT DISTINCT ro.project_id
        FROM request_orders ro
        JOIN purchase_order_items poi ON ro.request_order_no = poi.source_request_order_no
        WHERE poi.purchase_order_no = ?
    """, (purchase_order_no,))
    
    affected_projects = cursor.fetchall()
    
    for (project_id,) in affected_projects:
        if project_id:  # Only process if project_id is not None
            # Recalculate project cost
            cursor.execute("""
                SELECT 
                    po.supplier_id,
                    SUM(poi.unit_price * poi.item_quantity) as total_amount
                FROM purchase_order_items poi
                JOIN purchase_orders po ON poi.purchase_order_no = po.purchase_order_no
                JOIN request_orders ro ON poi.source_request_order_no = ro.request_order_no
                WHERE ro.project_id = ? 
                    AND po.purchase_status = 'purchased'
                GROUP BY po.supplier_id
            """, (project_id,))
            
            supplier_expenditures = cursor.fetchall()
            total_project_cost = 0
            
            for supplier_id, amount in supplier_expenditures:
                total_project_cost += amount or 0
                
                # Update supplier expenditure
                cursor.execute("""
                    INSERT OR REPLACE INTO project_supplier_expenditures (
                        project_id, supplier_id, expenditure_amount, updated_at
                    ) VALUES (?, ?, ?, ?)
                """, (project_id, supplier_id, amount, datetime.now()))
            
            # Update project total
            cursor.execute("""
                UPDATE projects 
                SET total_expenditure = ?, updated_at = ?
                WHERE project_id = ?
            """, (total_project_cost, datetime.now(), project_id))
    
    db_connection.commit()
