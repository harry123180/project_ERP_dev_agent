#!/usr/bin/env python3
"""
Find which table contains the delivery_status column
"""

import sqlite3

# Connect to the database
conn = sqlite3.connect('backend/erp_development.db')
cursor = conn.cursor()

# Get list of all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("All tables in database:")
for table in tables:
    table_name = table[0]
    print(f"  {table_name}")
    
    # Check if this table has a delivery_status column
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'delivery_status' in column_names:
            print(f"    ✅ Has delivery_status column!")
            print(f"    Schema:")
            for col in columns:
                print(f"      {col}")
    except Exception as e:
        print(f"    Error checking table: {e}")

conn.close()