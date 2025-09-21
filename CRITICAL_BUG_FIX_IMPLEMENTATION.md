# CRITICAL BUG FIX: Database Enum Mismatch

**Issue ID:** P0-001  
**Root Cause Identified:** Database enum schema mismatch  
**Fix Status:** READY FOR IMPLEMENTATION  

---

## 🔍 ROOT CAUSE ANALYSIS

### **Problem Identified**
```
Error: '消耗品' is not among the defined enum values. 
Enum name: usage_type_enum. 
Possible values: daily, project
```

### **Code Analysis**
In `backend/app/models/request_order.py` line 11:
```python
usage_type = db.Column(db.Enum('daily', 'project', '消耗品', name='usage_type_enum'), nullable=False)
```

### **Database Schema Issue**
The model defines the enum with 3 values: `['daily', 'project', '消耗品']`  
But the database enum only contains: `['daily', 'project']`

### **Impact Assessment**
- ✅ **Requisition Creation**: WORKS (confirmed via API test)
- ❌ **Requisition Listing**: FAILS when existing data contains '消耗品'
- ❌ **Complete Workflow**: BLOCKED due to listing failure

---

## 🔧 IMMEDIATE FIX STRATEGY

### **Option 1: Database Migration (RECOMMENDED)**
Update the database enum to match the model definition.

### **Option 2: Model Update**  
Update the model to match the database enum (removes functionality).

### **Option 3: Data Cleanup**
Update existing '消耗品' records to use 'daily' or 'project'.

---

## 🚀 IMPLEMENTATION PLAN

### **Step 1: Database Migration Script**
```sql
-- Add missing enum value to existing enum type
ALTER TYPE usage_type_enum ADD VALUE '消耗品';
```

### **Step 2: Verification Script**
```python
# Test script to verify fix
from app.models.request_order import RequestOrder
orders = RequestOrder.query.all()
print(f"Successfully loaded {len(orders)} requisitions")
```

### **Step 3: API Testing**
```bash
# Test both creation and listing
curl -X GET "http://localhost:5000/api/v1/requisitions" -H "Authorization: Bearer $TOKEN"
```

---

## 🎯 IMPLEMENTATION

Implementing the fix now...