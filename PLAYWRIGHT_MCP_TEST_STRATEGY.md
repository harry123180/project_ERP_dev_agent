# 🎭 PLAYWRIGHT MCP TESTING STRATEGY - CRITICAL BUG VALIDATION

## Overview

This document outlines the comprehensive Playwright MCP browser automation testing strategy to validate the critical requisition status update bug fix.

**Primary Objective**: Verify that requisition status changes from "已提交" to "已審核" when all items are approved through real UI interaction.

---

## Test Environment Setup

### Prerequisites
- ERP system running on localhost:5176 (frontend) and localhost:5000 (backend)
- Test user accounts with procurement approval permissions
- Sample requisitions in "submitted" status with pending items
- Playwright MCP browser automation configured

### Test Data Requirements
```json
{
  "test_requisitions": [
    {
      "id": "REQ20250908001",
      "status": "submitted",
      "items": [
        {"id": 1, "status": "pending_review", "name": "Office Chair"},
        {"id": 2, "status": "pending_review", "name": "Desk Lamp"}
      ]
    },
    {
      "id": "REQ20250908002", 
      "status": "submitted",
      "items": [
        {"id": 3, "status": "pending_review", "name": "Laptop"},
        {"id": 4, "status": "pending_review", "name": "Monitor"},
        {"id": 5, "status": "pending_review", "name": "Keyboard"}
      ]
    }
  ]
}
```

---

## Core Test Scenarios

### Scenario 1: Single Item Approval Status Update
**Test ID**: MCP-CRIT-001
**Priority**: CRITICAL
**Objective**: Verify status update when single item approved

#### Test Steps:
1. **Navigate to System**
   ```javascript
   await browser.navigate('http://localhost:5176/login')
   ```

2. **Login as Procurement User**
   ```javascript
   await browser.type('[data-testid="username"]', 'procurement_user')
   await browser.type('[data-testid="password"]', 'test123')
   await browser.click('[data-testid="login-button"]')
   ```

3. **Navigate to Requisitions List**
   ```javascript
   await browser.click('[data-testid="nav-requisitions"]')
   await browser.waitFor('[data-testid="requisitions-table"]')
   ```

4. **Find Submitted Requisition**
   ```javascript
   // Look for requisition with "已提交" status
   const submittedRow = await browser.snapshot()
   // Find row with status "已提交"
   ```

5. **Open Review Dialog**
   ```javascript
   await browser.click('[data-action="review"]')
   await browser.waitFor('[data-testid="review-dialog"]')
   ```

6. **Verify Initial Status**
   ```javascript
   // Take screenshot of current status
   await browser.screenshot('before_approval.png')
   // Verify status shows "已提交"
   ```

7. **Approve Single Item**
   ```javascript
   // Select supplier
   await browser.selectOption('[data-testid="supplier-select"]', ['SUP001'])
   // Enter price
   await browser.type('[data-testid="unit-price"]', '1500')
   // Click approve
   await browser.click('[data-testid="approve-item"]')
   ```

8. **Verify Status Change**
   ```javascript
   // Wait for status update (max 3 seconds)
   await browser.waitFor('[data-status="reviewed"]', { timeout: 3000 })
   // Take screenshot of updated status
   await browser.screenshot('after_approval.png')
   ```

9. **Close Dialog and Verify List**
   ```javascript
   await browser.click('[data-testid="close-dialog"]')
   // Verify status in list shows "已審核"
   const listStatus = await browser.getText('[data-status-cell="REQ20250908001"]')
   assert(listStatus === '已審核')
   ```

10. **Refresh Page Verification**
    ```javascript
    await browser.reload()
    await browser.waitFor('[data-testid="requisitions-table"]')
    // Verify status persists after refresh
    const persistentStatus = await browser.getText('[data-status-cell="REQ20250908001"]')
    assert(persistentStatus === '已審核')
    ```

### Scenario 2: Batch Approval Status Update  
**Test ID**: MCP-CRIT-002
**Priority**: CRITICAL
**Objective**: Verify status update with batch approval

#### Test Steps:
1. **Setup Multi-Item Requisition**
   - Navigate to requisition with multiple pending items
   - Open review dialog

2. **Batch Selection**
   ```javascript
   // Select all items
   await browser.click('[data-testid="select-all-checkbox"]')
   ```

3. **Set Batch Data**
   ```javascript
   // For each selected item, set supplier and price
   const items = await browser.findAll('[data-testid="item-row"]')
   for (let item of items) {
     await item.selectOption('[data-testid="supplier-select"]', ['SUP001'])
     await item.type('[data-testid="unit-price"]', '1000')
   }
   ```

4. **Execute Batch Approval**
   ```javascript
   await browser.click('[data-testid="batch-approve"]')
   // Wait for all items to show approved
   await browser.waitFor('[data-all-items="approved"]')
   ```

5. **Verify Status Update**
   ```javascript
   // Check requisition status changed to "已審核"
   await browser.waitFor('[data-requisition-status="reviewed"]')
   await browser.screenshot('batch_approval_success.png')
   ```

### Scenario 3: Mixed Actions Status Update
**Test ID**: MCP-CRIT-003  
**Priority**: HIGH
**Objective**: Verify status update with approve/reject/question mix

#### Test Steps:
1. **Process Items Differently**
   ```javascript
   // Approve first item
   await browser.click('[data-row="0"] [data-action="approve"]')
   
   // Reject second item  
   await browser.click('[data-row="1"] [data-action="reject"]')
   await browser.type('[data-testid="reason-input"]', 'Not needed')
   await browser.click('[data-testid="confirm-reason"]')
   
   // Question third item
   await browser.click('[data-row="2"] [data-action="question"]') 
   await browser.type('[data-testid="reason-input"]', 'Clarify specs')
   await browser.click('[data-testid="confirm-reason"]')
   ```

2. **Verify Final Status**
   ```javascript
   // All items processed, status should be "已審核"
   await browser.waitFor('[data-requisition-status="reviewed"]')
   ```

---

## Edge Case Testing

### Edge Case 1: Network Interruption
**Test ID**: MCP-EDGE-001

```javascript
// Simulate network delay during approval
await browser.setNetworkConditions({ 
  downloadThroughput: 1000, // Very slow
  uploadThroughput: 1000 
})

// Perform approval
await browser.click('[data-testid="approve-item"]')

// Verify status still updates correctly despite network issues
await browser.waitFor('[data-status="reviewed"]', { timeout: 10000 })
```

### Edge Case 2: Concurrent Approvals
**Test ID**: MCP-EDGE-002

```javascript
// Open same requisition in two browser tabs
const tab1 = await browser.newTab()
const tab2 = await browser.newTab()

// Both tabs approve different items simultaneously
await Promise.all([
  tab1.click('[data-row="0"] [data-action="approve"]'),
  tab2.click('[data-row="1"] [data-action="approve"]')
])

// Verify status updates correctly
await tab1.waitFor('[data-status="reviewed"]')
await tab2.waitFor('[data-status="reviewed"]')
```

### Edge Case 3: Large Requisition Performance
**Test ID**: MCP-EDGE-003

```javascript
// Test with 50+ item requisition
const largeRequisition = await browser.findByTestId('large-requisition')
await largeRequisition.click('[data-action="review"]')

// Batch approve all items
await browser.click('[data-testid="select-all"]')
await browser.click('[data-testid="batch-approve"]')

// Verify performance - should complete within 5 seconds
const startTime = Date.now()
await browser.waitFor('[data-status="reviewed"]')
const duration = Date.now() - startTime
assert(duration < 5000, 'Status update took too long')
```

---

## Browser Compatibility Matrix

### Desktop Browsers
| Browser | Version | Status Update | Batch Approval | Network Resilience |
|---------|---------|---------------|----------------|-------------------|
| Chrome  | Latest  | ✅ Test        | ✅ Test         | ✅ Test            |
| Firefox | Latest  | ✅ Test        | ✅ Test         | ✅ Test            |
| Edge    | Latest  | ✅ Test        | ✅ Test         | ✅ Test            |

### Mobile Browsers  
| Browser | Platform | Touch Approval | Status Display |
|---------|----------|----------------|----------------|
| Chrome Mobile | Android | ✅ Test | ✅ Test |
| Safari Mobile | iOS | ✅ Test | ✅ Test |

---

## Test Execution Framework

### Test Runner Configuration
```javascript
// playwright.config.js for MCP
export default {
  testDir: './tests',
  timeout: 30000,
  retries: 2,
  use: {
    baseURL: 'http://localhost:5176',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  projects: [
    { name: 'chrome', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'edge', use: { ...devices['Desktop Edge'] } }
  ]
}
```

### Evidence Capture
```javascript
// Enhanced screenshot and logging
await browser.screenshot(`step_${stepNumber}_${testId}.png`)
await browser.evaluate(() => {
  console.log('DOM State:', document.documentElement.outerHTML)
  console.log('Network Requests:', performance.getEntriesByType('resource'))
})
```

---

## Reporting and Validation

### Success Criteria Checklist
- [ ] Single item approval updates status within 2 seconds
- [ ] Batch approval handles all items correctly  
- [ ] Mixed actions result in proper status
- [ ] Status persists after page refresh
- [ ] Works across all target browsers
- [ ] Performance meets requirements (<3 seconds)
- [ ] Network resilience validated
- [ ] No regression in existing flows

### Test Report Format
```json
{
  "test_execution": {
    "timestamp": "2025-01-08T12:00:00Z",
    "environment": "localhost:5176",
    "total_tests": 15,
    "passed": 15,
    "failed": 0,
    "duration_ms": 45000
  },
  "critical_tests": {
    "MCP-CRIT-001": "PASS - Status updated in 1.2s",
    "MCP-CRIT-002": "PASS - Batch approval successful", 
    "MCP-CRIT-003": "PASS - Mixed actions handled correctly"
  },
  "evidence": {
    "screenshots": ["before_approval.png", "after_approval.png"],
    "videos": ["full_test_run.webm"],
    "network_logs": ["api_calls.har"]
  }
}
```

---

## Continuous Validation

### Regression Test Suite
After the critical bug fix, add these tests to the permanent regression suite:

1. **Daily Status Update Validation**: Run MCP-CRIT-001 daily
2. **Weekly Comprehensive**: Run all critical scenarios weekly  
3. **Pre-deployment**: Run full suite before any deployment

### Monitoring Integration
```javascript
// Add status update performance monitoring
await browser.evaluate(() => {
  window.statusUpdateMonitor = {
    start: Date.now(),
    track: (event) => {
      console.log(`Status Update Event: ${event} at ${Date.now() - this.start}ms`)
    }
  }
})
```

---

**REMEMBER**: This is a CRITICAL bug affecting CEO visibility. All tests must PASS at 100% success rate before marking the fix as complete. Any failures require immediate escalation and investigation.