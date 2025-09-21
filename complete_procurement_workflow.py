import requests
import json
import time

base_url = "http://localhost:5000/api/v1"

# Login first
login_data = {"username": "admin", "password": "admin123"}
response = requests.post(f"{base_url}/auth/login", json=login_data)
if response.status_code != 200:
    print(f"Login failed: {response.text}")
    exit(1)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

requisition_no = "REQ20250913002"
print(f"Working with requisition: {requisition_no}")

# Step 1: Submit requisition for approval
print("\n1. Submitting requisition for approval...")
response = requests.put(f"{base_url}/requisitions/{requisition_no}/submit", headers=headers)
if response.status_code == 200:
    print("✅ Requisition submitted for approval")
else:
    print(f"❌ Failed to submit: {response.text}")

# Step 2: Approve all items
print("\n2. Approving requisition items...")
response = requests.get(f"{base_url}/requisitions/{requisition_no}", headers=headers)
if response.status_code == 200:
    requisition = response.json()
    items = requisition.get("items", [])

    for item in items:
        item_id = item.get("detail_id")
        approve_data = {
            "item_status": "approved",
            "unit_price": 50000 if "筆記型電腦" in item["item_name"] else 5000 if "辦公椅" in item["item_name"] else 30000
        }
        response = requests.put(f"{base_url}/requisitions/{requisition_no}/items/{item_id}", json=approve_data, headers=headers)
        if response.status_code == 200:
            print(f"  ✅ Approved item: {item['item_name']}")
        else:
            print(f"  ❌ Failed to approve {item['item_name']}: {response.text}")

# Step 3: Convert to purchase order
print("\n3. Converting to purchase order...")
po_data = {
    "supplier_id": "S001",  # Use default supplier
    "items": "all"
}
response = requests.post(f"{base_url}/requisitions/{requisition_no}/convert-to-po", json=po_data, headers=headers)
if response.status_code == 201:
    po_data = response.json()
    po_number = po_data.get("purchase_order_no")
    print(f"✅ Created purchase order: {po_number}")
else:
    print(f"❌ Failed to create PO: {response.text}")
    po_number = None

if po_number:
    # Step 4: Update delivery dates
    print("\n4. Updating delivery dates...")
    delivery_data = {
        "estimated_delivery_date": "2025-09-20",
        "actual_delivery_date": "2025-09-19"
    }
    response = requests.put(f"{base_url}/purchase-orders/{po_number}/delivery", json=delivery_data, headers=headers)
    if response.status_code == 200:
        print("✅ Delivery dates updated")
    else:
        print(f"❌ Failed to update delivery: {response.text}")

    # Step 5: Mark items as received
    print("\n5. Marking items as received...")
    response = requests.post(f"{base_url}/purchase-orders/{po_number}/receive", headers=headers)
    if response.status_code == 200:
        print("✅ Items marked as received")
    else:
        print(f"❌ Failed to mark as received: {response.text}")

    # Step 6: Process warehousing
    print("\n6. Processing warehousing...")
    warehouse_data = {
        "warehouse_location": "A1-B2-C3",
        "received_by": "admin"
    }
    response = requests.post(f"{base_url}/purchase-orders/{po_number}/warehouse", json=warehouse_data, headers=headers)
    if response.status_code == 200:
        print("✅ Items warehoused")
    else:
        print(f"❌ Failed to warehouse: {response.text}")

    # Step 7: Process acceptance
    print("\n7. Processing acceptance...")
    acceptance_data = {
        "acceptance_status": "accepted",
        "acceptance_notes": "All items meet quality standards"
    }
    response = requests.post(f"{base_url}/purchase-orders/{po_number}/accept", json=acceptance_data, headers=headers)
    if response.status_code == 200:
        print("✅ Items accepted")
    else:
        print(f"❌ Failed to accept: {response.text}")

# Step 8: Verify project expenses
print("\n8. Verifying project expenses...")
response = requests.get(f"{base_url}/projects/PROJ65813667", headers=headers)
if response.status_code == 200:
    project = response.json()
    print(f"✅ Project budget: {project.get('budget', 0):,.2f}")
    print(f"✅ Project expenses: {project.get('total_expenditure', 0):,.2f}")

    expected_total = (3 * 50000) + (10 * 5000) + (2 * 30000)  # 150000 + 50000 + 60000 = 260000
    actual_total = project.get('total_expenditure', 0)

    if actual_total == expected_total:
        print(f"✅ Expenses match expected total: {expected_total:,.2f}")
    else:
        print(f"⚠️ Expenses mismatch - Expected: {expected_total:,.2f}, Actual: {actual_total:,.2f}")
else:
    print(f"❌ Failed to get project info: {response.text}")

print("\n✅ Procurement workflow completed!")