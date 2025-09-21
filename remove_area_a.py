"""
Remove area 'A' from the database as it's causing confusion with shelf 'A'
"""
import sqlite3

# Connect to database
conn = sqlite3.connect('erp_development.db')
cursor = conn.cursor()

try:
    # Begin transaction
    conn.execute("BEGIN TRANSACTION")

    # First check if area A exists
    cursor.execute("""
        SELECT storage_id, area_code, shelf_code, floor_level
        FROM storages
        WHERE area_code = 'A'
    """)

    area_a_storages = cursor.fetchall()

    if area_a_storages:
        print(f"Found {len(area_a_storages)} storage locations in area 'A':")
        for storage in area_a_storages:
            print(f"  {storage[0]} - Shelf: {storage[2]}, Floor: {storage[3]}")

        # Check if there are any pending storage items referencing area A
        cursor.execute("""
            SELECT COUNT(*)
            FROM pending_storage_items
            WHERE assigned_storage_id IN (SELECT storage_id FROM storages WHERE area_code = 'A')
               OR suggested_storage_id IN (SELECT storage_id FROM storages WHERE area_code = 'A')
        """)
        pending_count = cursor.fetchone()[0]

        if pending_count > 0:
            print(f"\n⚠️ Warning: {pending_count} pending storage items reference area 'A'")
            print("Clearing these references...")
            cursor.execute("""
                UPDATE pending_storage_items
                SET assigned_storage_id = NULL
                WHERE assigned_storage_id IN (SELECT storage_id FROM storages WHERE area_code = 'A')
            """)
            cursor.execute("""
                UPDATE pending_storage_items
                SET suggested_storage_id = NULL
                WHERE suggested_storage_id IN (SELECT storage_id FROM storages WHERE area_code = 'A')
            """)

        # Delete storages in area 'A'
        cursor.execute("DELETE FROM storages WHERE area_code = 'A'")
        deleted_count = cursor.rowcount

        # Commit the transaction
        conn.commit()
        print(f"\n✅ Successfully removed {deleted_count} storage locations from area 'A'")

    else:
        print("No storage locations found in area 'A'")

    # Show remaining areas
    cursor.execute("""
        SELECT DISTINCT area_code, COUNT(*) as location_count
        FROM storages
        GROUP BY area_code
        ORDER BY area_code
    """)

    areas = cursor.fetchall()

    print("\n📦 Remaining storage areas:")
    for area in areas:
        print(f"  {area[0]}: {area[1]} locations")

    print("\n✅ Area 'A' has been removed. The frontend should now only show Z1 and Z2 as area options.")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    conn.close()

print("\n✨ Done!")