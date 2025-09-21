# Epic 2: Requisition Management System
**Epic ID**: ERP-E02  
**Priority**: P0 (Critical)  
**Story Points**: 144  
**Status**: Draft  

## Epic Description
Implement a comprehensive requisition management system that allows users to create, submit, track, and approve requisitions with multiple items, file attachments, approval workflows, and real-time status updates. This system replaces the current manual paper-based process with a digital workflow.

## Business Value
- **Efficiency**: Reduce requisition-to-approval cycle time by 60%
- **Accuracy**: Eliminate manual transcription errors through digital forms
- **Transparency**: Provide real-time status visibility to all stakeholders
- **Compliance**: Maintain complete audit trail for all requisition activities
- **Workflow**: Streamline approval processes with automated routing

## User Personas
- **Primary**: Engineers (requisition creators), Procurement Managers (approvers)
- **Secondary**: Procurement Staff (reviewers), System Administrators

---

## Story 2.1: Multi-Item Requisition Creation
**Story ID**: ERP-E02-S01  
**Title**: Create Multi-Item Requisitions with Specifications  
**Priority**: P0  
**Story Points**: 21  

### User Story
**As an** Engineer  
**I want to** create requisitions with multiple items and detailed specifications  
**So that** I can request everything needed for my project in one submission and provide clear requirements  

### Background & Context
Engineers need to create requisitions for various items ranging from raw materials to equipment. Each requisition can contain multiple items with detailed specifications, estimated prices, and justifications. The system must support both "Daily Operations" and "Project-Specific" purposes with appropriate validation and routing.

### Acceptance Criteria
**AC1**: Given I am on the requisition creation form, when I add items, then I can add multiple items with fields: name, description, quantity, estimated unit price, justification, and optional file attachments

**AC2**: Given I am creating a requisition, when I select purpose type, then I can choose between "Daily Operations" and "Project-Specific" with appropriate project selection for project-specific items

**AC3**: Given I am filling out requisition items, when I enter data, then the system should validate: quantity > 0, estimated price >= 0, required fields are not empty

**AC4**: Given I am working on a requisition, when I need to save my progress, then I can save as draft with auto-save every 30 seconds and return to complete it later

**AC5**: Given I complete a requisition form, when I click submit, then the system generates a unique requisition number (REQ-YYYYMMDD-XXX format) and changes status to "Submitted"

**AC6**: Given I submit a requisition, when the submission completes, then I receive confirmation with the requisition number and an email notification is sent to the appropriate approver

### Technical Implementation Notes

#### API Endpoints Required
```
POST /api/v1/requisitions                    # Create new requisition
PUT /api/v1/requisitions/{id}                # Update draft requisition
POST /api/v1/requisitions/{id}/submit        # Submit requisition for approval
GET /api/v1/requisitions/{id}                # Get requisition details
DELETE /api/v1/requisitions/{id}             # Delete draft requisition
POST /api/v1/requisitions/{id}/attachments   # Upload attachments
```

#### Database Changes
```sql
-- Main requisitions table
CREATE TABLE requisitions (
    id SERIAL PRIMARY KEY,
    req_number VARCHAR(20) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    purpose VARCHAR(20) NOT NULL CHECK (purpose IN ('Daily Operations', 'Project-Specific')),
    project_id INTEGER REFERENCES projects(id),
    status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Submitted', 'Under Review', 'Approved', 'Questioned', 'Rejected')),
    total_estimated_amount DECIMAL(12,2) DEFAULT 0.00,
    justification TEXT,
    submitted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Requisition items table
CREATE TABLE requisition_items (
    id SERIAL PRIMARY KEY,
    requisition_id INTEGER NOT NULL REFERENCES requisitions(id) ON DELETE CASCADE,
    item_sequence INTEGER NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    description TEXT,
    quantity DECIMAL(10,3) NOT NULL CHECK (quantity > 0),
    unit VARCHAR(50) DEFAULT 'pcs',
    estimated_unit_price DECIMAL(10,2) NOT NULL CHECK (estimated_unit_price >= 0),
    estimated_total_price DECIMAL(12,2) GENERATED ALWAYS AS (quantity * estimated_unit_price) STORED,
    justification TEXT,
    specifications TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- File attachments table
CREATE TABLE requisition_attachments (
    id SERIAL PRIMARY KEY,
    requisition_id INTEGER NOT NULL REFERENCES requisitions(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    uploaded_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects table (if not exists)
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    project_code VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Completed', 'On Hold', 'Cancelled')),
    manager_id INTEGER REFERENCES users(id),
    start_date DATE,
    end_date DATE,
    budget_amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_requisitions_user_status ON requisitions(user_id, status);
CREATE INDEX idx_requisitions_created_at ON requisitions(created_at DESC);
CREATE INDEX idx_requisition_items_req_id ON requisition_items(requisition_id);
```

#### UI/UX Considerations
- Dynamic item addition/removal with smooth animations
- Real-time calculation of total estimated amount
- File drag-and-drop functionality for attachments
- Auto-save indicators and draft recovery
- Form validation with inline error messages
- Progress indicator for multi-step form completion
- Responsive design for desktop and tablet use

### Test Scenarios
1. **Basic Creation**: Create requisition with single item
2. **Multi-Item**: Add/remove multiple items dynamically
3. **File Attachments**: Upload various file types (PDF, images, Excel)
4. **Validation**: Test quantity/price validation rules
5. **Auto-Save**: Test draft saving and recovery
6. **Project Association**: Link requisition to specific project
7. **Submission**: Complete submission workflow
8. **Error Handling**: Network failures during submission

### Dependencies
- User authentication system (Epic 1)
- Project management basic setup
- File storage service configuration
- Email notification service

**Story Points Breakdown**: Frontend (8) + Backend (8) + Database (3) + Testing (2) = 21

---

## Story 2.2: Requisition Approval Workflow
**Story ID**: ERP-E02-S02  
**Title**: Implement Hierarchical Approval Process  
**Priority**: P0  
**Story Points**: 34  

### User Story
**As a** Procurement Manager  
**I want to** review and approve requisitions with commenting capability  
**So that** I can ensure proper spending control and provide clear feedback to requesters  

### Background & Context
Requisitions follow a hierarchical approval process based on user roles and requisition values. Managers can approve, question, or reject requisitions with detailed comments. The system must support email notifications, status tracking, and approval history.

### Acceptance Criteria
**AC1**: Given a submitted requisition, when I access it as an approver, then I can see all item details, attachments, and requester information with approval action buttons

**AC2**: Given I am reviewing a requisition, when I take an action, then I can choose to: Approve, Question (with required comments), or Reject (with required reason)

**AC3**: Given I approve a requisition, when the approval is saved, then the status changes to "Approved", the approval timestamp is recorded, and the requester receives email notification

**AC4**: Given I question a requisition, when I submit my questions, then the status changes to "Questioned", my comments are saved, and the requester receives an email with my questions

**AC5**: Given I reject a requisition, when I provide the rejection reason, then the status changes to "Rejected", the reason is saved, and the requester receives email notification

**AC6**: Given a requisition has been questioned, when the requester responds, then the status returns to "Under Review" for re-evaluation

**AC7**: Given any status change occurs, when the change is processed, then all relevant parties receive real-time notifications via WebSocket and email

### Technical Implementation Notes

#### API Endpoints Required
```
GET /api/v1/requisitions/pending-approval     # Get requisitions awaiting approval
POST /api/v1/requisitions/{id}/approve        # Approve requisition
POST /api/v1/requisitions/{id}/question       # Question requisition
POST /api/v1/requisitions/{id}/reject         # Reject requisition
GET /api/v1/requisitions/{id}/approval-history # Get approval history
POST /api/v1/requisitions/{id}/respond        # Respond to questions
GET /api/v1/requisitions/dashboard            # Approval dashboard data
```

#### Database Changes
```sql
-- Approval workflow table
CREATE TABLE requisition_approvals (
    id SERIAL PRIMARY KEY,
    requisition_id INTEGER NOT NULL REFERENCES requisitions(id) ON DELETE CASCADE,
    approver_id INTEGER NOT NULL REFERENCES users(id),
    action VARCHAR(20) NOT NULL CHECK (action IN ('Approved', 'Questioned', 'Rejected')),
    comments TEXT,
    approval_level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Requisition comments/questions
CREATE TABLE requisition_comments (
    id SERIAL PRIMARY KEY,
    requisition_id INTEGER NOT NULL REFERENCES requisitions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    comment_type VARCHAR(20) NOT NULL CHECK (comment_type IN ('Question', 'Response', 'Note')),
    comment_text TEXT NOT NULL,
    parent_comment_id INTEGER REFERENCES requisition_comments(id),
    is_internal BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Status history tracking
CREATE TABLE requisition_status_history (
    id SERIAL PRIMARY KEY,
    requisition_id INTEGER NOT NULL REFERENCES requisitions(id) ON DELETE CASCADE,
    previous_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_by INTEGER NOT NULL REFERENCES users(id),
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add approval fields to requisitions table
ALTER TABLE requisitions ADD COLUMN approved_by INTEGER REFERENCES users(id);
ALTER TABLE requisitions ADD COLUMN approved_at TIMESTAMP;
ALTER TABLE requisitions ADD COLUMN rejection_reason TEXT;
```

#### Approval Logic Implementation
```python
class RequisitionApprovalService:
    def approve_requisition(self, requisition_id: int, approver_id: int, comments: str = None):
        # Validate approver permissions
        if not self.can_approve(approver_id, requisition_id):
            raise PermissionError("User not authorized to approve this requisition")
        
        # Update requisition status
        requisition = self.get_requisition(requisition_id)
        requisition.status = 'Approved'
        requisition.approved_by = approver_id
        requisition.approved_at = datetime.utcnow()
        
        # Create approval record
        approval = RequisitionApproval(
            requisition_id=requisition_id,
            approver_id=approver_id,
            action='Approved',
            comments=comments
        )
        
        # Save and notify
        db.session.add(approval)
        db.session.commit()
        
        # Send notifications
        self.send_approval_notification(requisition)
        self.emit_status_update(requisition_id, 'Approved')
        
        return approval

    def question_requisition(self, requisition_id: int, approver_id: int, questions: str):
        # Implementation for questioning requisition
        pass

    def reject_requisition(self, requisition_id: int, approver_id: int, reason: str):
        # Implementation for rejecting requisition
        pass
```

#### Email Templates
```html
<!-- Approval Notification Template -->
<h2>Requisition Approved</h2>
<p>Your requisition {{requisition_number}} has been approved by {{approver_name}}.</p>
<p><strong>Total Amount:</strong> {{total_amount}}</p>
<p><strong>Approved on:</strong> {{approval_date}}</p>
<a href="{{requisition_url}}">View Requisition</a>

<!-- Question Notification Template -->
<h2>Questions on Your Requisition</h2>
<p>{{approver_name}} has questions about your requisition {{requisition_number}}:</p>
<blockquote>{{questions}}</blockquote>
<p>Please review and respond at your earliest convenience.</p>
<a href="{{requisition_url}}">Respond to Questions</a>
```

### Test Scenarios
1. **Approval Flow**: Test complete approval process
2. **Question Flow**: Test questioning with comments and responses
3. **Rejection Flow**: Test rejection with reasons
4. **Permission Validation**: Test approval permissions by role
5. **Email Notifications**: Test all notification scenarios
6. **Real-time Updates**: Test WebSocket notifications
7. **Approval History**: Test history tracking and display
8. **Concurrent Approvals**: Test handling of simultaneous approval attempts

### Dependencies
- User authentication and authorization (Epic 1)
- Email notification service
- WebSocket implementation for real-time updates
- Requisition creation (Story 2.1)

**Story Points Breakdown**: Backend (18) + Frontend (10) + Email/Notifications (4) + Testing (2) = 34

---

## Story 2.3: Advanced Requisition Search and Filtering
**Story ID**: ERP-E02-S03  
**Title**: Implement Comprehensive Search and Filter System  
**Priority**: P1  
**Story Points**: 21  

### User Story
**As a** system user (Engineer/Procurement staff)  
**I want to** search and filter requisitions by multiple criteria  
**So that** I can quickly find specific requisitions and track their status  

### Background & Context
Users need to efficiently locate requisitions among potentially thousands of records. The search system must support text search, date ranges, status filters, and advanced criteria while maintaining good performance on large datasets.

### Acceptance Criteria
**AC1**: Given I am on the requisitions page, when I use the search box, then I can search by requisition number, requester name, or item descriptions with auto-complete suggestions

**AC2**: Given I need to filter requisitions, when I use filter options, then I can filter by: status, date range, purpose type, requester, approval status, and estimated value range

**AC3**: Given I apply multiple filters, when I search, then the system should combine all criteria with AND logic and display matching results with pagination

**AC4**: Given I perform a search, when results are displayed, then I can sort by: creation date, submission date, status, estimated value, and requester name

**AC5**: Given I have applied filters, when I want to save them, then I can bookmark the filtered view URL and return to the same filtered results later

**AC6**: Given I am viewing search results, when I click on a requisition, then I can view its details and return to the same search results position

### Technical Implementation Notes

#### API Endpoints Required
```
GET /api/v1/requisitions/search              # Advanced search with filters
GET /api/v1/requisitions/autocomplete        # Auto-complete suggestions
GET /api/v1/requisitions/filters             # Available filter options
POST /api/v1/requisitions/export             # Export search results
```

#### Database Optimization
```sql
-- Full-text search indexes
CREATE INDEX idx_requisitions_fulltext ON requisitions USING gin(
    to_tsvector('english', req_number || ' ' || COALESCE(justification, ''))
);

CREATE INDEX idx_requisition_items_fulltext ON requisition_items USING gin(
    to_tsvector('english', item_name || ' ' || COALESCE(description, '') || ' ' || COALESCE(specifications, ''))
);

-- Composite indexes for common filter combinations
CREATE INDEX idx_requisitions_status_date ON requisitions(status, created_at DESC);
CREATE INDEX idx_requisitions_user_purpose ON requisitions(user_id, purpose, created_at DESC);
CREATE INDEX idx_requisitions_amount_range ON requisitions(total_estimated_amount) 
    WHERE total_estimated_amount > 0;
```

#### Search Implementation
```python
class RequisitionSearchService:
    def search(self, user_id: int, search_params: dict):
        query = db.session.query(Requisition)
        
        # Text search
        if search_params.get('q'):
            search_term = search_params['q']
            query = query.join(RequisitionItem).filter(
                or_(
                    Requisition.req_number.ilike(f'%{search_term}%'),
                    func.to_tsvector('english', 
                        Requisition.req_number + ' ' + 
                        func.coalesce(Requisition.justification, '')
                    ).match(search_term),
                    func.to_tsvector('english', 
                        RequisitionItem.item_name + ' ' + 
                        func.coalesce(RequisitionItem.description, '')
                    ).match(search_term)
                )
            )
        
        # Status filter
        if search_params.get('status'):
            statuses = search_params['status']
            if isinstance(statuses, str):
                statuses = [statuses]
            query = query.filter(Requisition.status.in_(statuses))
        
        # Date range filter
        if search_params.get('date_from'):
            query = query.filter(Requisition.created_at >= search_params['date_from'])
        if search_params.get('date_to'):
            query = query.filter(Requisition.created_at <= search_params['date_to'])
        
        # Value range filter
        if search_params.get('min_amount'):
            query = query.filter(Requisition.total_estimated_amount >= search_params['min_amount'])
        if search_params.get('max_amount'):
            query = query.filter(Requisition.total_estimated_amount <= search_params['max_amount'])
        
        # Purpose filter
        if search_params.get('purpose'):
            query = query.filter(Requisition.purpose == search_params['purpose'])
        
        # Role-based access control
        user_role = self.get_user_role(user_id)
        if user_role == 'Engineer':
            query = query.filter(Requisition.user_id == user_id)
        elif user_role in ['Procurement', 'ProcurementMgr']:
            # Can see all requisitions
            pass
        
        # Sorting
        sort_by = search_params.get('sort_by', 'created_at')
        sort_order = search_params.get('sort_order', 'desc')
        
        if sort_order == 'desc':
            query = query.order_by(desc(getattr(Requisition, sort_by)))
        else:
            query = query.order_by(asc(getattr(Requisition, sort_by)))
        
        # Pagination
        page = search_params.get('page', 1)
        per_page = search_params.get('per_page', 20)
        
        return query.paginate(page=page, per_page=per_page, error_out=False)
```

#### Frontend Components
```vue
<!-- SearchAndFilter.vue -->
<template>
  <div class="search-filter-container">
    <!-- Text Search -->
    <el-input
      v-model="searchQuery"
      placeholder="Search by requisition number, requester, or items"
      @input="debounceSearch"
      clearable
    >
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
    </el-input>
    
    <!-- Advanced Filters -->
    <el-collapse v-model="activeFilters">
      <el-collapse-item title="Advanced Filters" name="filters">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-select v-model="filters.status" multiple placeholder="Status">
              <el-option label="Draft" value="Draft" />
              <el-option label="Submitted" value="Submitted" />
              <el-option label="Approved" value="Approved" />
              <el-option label="Rejected" value="Rejected" />
            </el-select>
          </el-col>
          
          <el-col :span="6">
            <el-date-picker
              v-model="filters.dateRange"
              type="datetimerange"
              range-separator="To"
              start-placeholder="Start date"
              end-placeholder="End date"
            />
          </el-col>
          
          <el-col :span="6">
            <el-input-number v-model="filters.minAmount" placeholder="Min Amount" />
            <el-input-number v-model="filters.maxAmount" placeholder="Max Amount" />
          </el-col>
          
          <el-col :span="6">
            <el-button type="primary" @click="applyFilters">Apply Filters</el-button>
            <el-button @click="clearFilters">Clear</el-button>
          </el-col>
        </el-row>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>
```

### Test Scenarios
1. **Text Search**: Test search across requisition numbers, names, descriptions
2. **Filter Combinations**: Test multiple filter criteria combinations
3. **Performance**: Test search performance with large datasets (>10,000 records)
4. **Auto-complete**: Test search suggestions and auto-complete
5. **Sorting**: Test all sorting options and directions
6. **Pagination**: Test pagination with search results
7. **Bookmarking**: Test URL-based filter state preservation
8. **Access Control**: Test search results respect user permissions

### Dependencies
- Database indexes for performance
- Full-text search capability
- Role-based access control (Epic 1)
- Requisition creation and approval (Stories 2.1, 2.2)

**Story Points Breakdown**: Backend (10) + Frontend (8) + Database (2) + Testing (1) = 21

---

## Story 2.4: Draft Management and Auto-Save
**Story ID**: ERP-E02-S04  
**Title**: Implement Draft Saving and Recovery  
**Priority**: P1  
**Story Points**: 13  

### User Story
**As an** Engineer  
**I want to** save my requisition as a draft and have it auto-save while I work  
**So that** I don't lose my work if interrupted and can complete complex requisitions over time  

### Background & Context
Engineers often need to research specifications, get approvals from team leads, or gather additional information while creating requisitions. The system must allow saving work in progress with automatic recovery capabilities.

### Acceptance Criteria
**AC1**: Given I am creating a requisition, when I click "Save as Draft", then my progress is saved and I can return to complete it later

**AC2**: Given I am working on a requisition form, when 30 seconds pass after my last change, then the system automatically saves my progress as a draft

**AC3**: Given I have an auto-saved draft, when I return to the form, then I see a notification asking if I want to recover my previous work

**AC4**: Given I have multiple draft requisitions, when I view my drafts list, then I can see the last modified date, item count, and estimated total for each draft

**AC5**: Given I no longer need a draft, when I delete it, then it's permanently removed from the system after confirmation

**AC6**: Given I am working on a form and my network connection is lost, when connectivity returns, then the system attempts to save my draft automatically

### Technical Implementation Notes

#### API Endpoints Required
```
GET /api/v1/requisitions/drafts              # Get user's draft requisitions
PUT /api/v1/requisitions/{id}/draft          # Save/update draft
DELETE /api/v1/requisitions/{id}/draft       # Delete draft
POST /api/v1/requisitions/draft/recover      # Recover from auto-save
```

#### Database Changes
```sql
-- Add draft-specific fields
ALTER TABLE requisitions ADD COLUMN is_draft BOOLEAN DEFAULT TRUE;
ALTER TABLE requisitions ADD COLUMN last_auto_save TIMESTAMP;
ALTER TABLE requisitions ADD COLUMN auto_save_data JSONB; -- Backup of form state

-- Draft metadata table
CREATE TABLE requisition_drafts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    draft_name VARCHAR(255),
    form_data JSONB NOT NULL,
    item_count INTEGER DEFAULT 0,
    estimated_total DECIMAL(12,2) DEFAULT 0.00,
    last_saved TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_drafts_user_date ON requisition_drafts(user_id, last_saved DESC);
```

#### Auto-Save Implementation
```typescript
// Frontend Auto-Save Service
export class AutoSaveService {
  private saveTimer: NodeJS.Timeout | null = null;
  private readonly SAVE_DELAY = 30000; // 30 seconds
  
  scheduleAutoSave(formData: any, requisitionId?: string) {
    if (this.saveTimer) {
      clearTimeout(this.saveTimer);
    }
    
    this.saveTimer = setTimeout(async () => {
      try {
        await this.saveDraft(formData, requisitionId);
        this.showAutoSaveIndicator();
      } catch (error) {
        this.handleAutoSaveError(error);
      }
    }, this.SAVE_DELAY);
  }
  
  async saveDraft(formData: any, requisitionId?: string) {
    const payload = {
      formData: formData,
      timestamp: new Date().toISOString(),
      itemCount: formData.items?.length || 0,
      estimatedTotal: this.calculateTotal(formData.items)
    };
    
    if (requisitionId) {
      return await api.put(`/requisitions/${requisitionId}/draft`, payload);
    } else {
      return await api.post('/requisitions/draft', payload);
    }
  }
  
  private showAutoSaveIndicator() {
    // Show "Draft saved" indicator
    ElMessage({
      message: 'Draft automatically saved',
      type: 'success',
      duration: 2000,
      showClose: false
    });
  }
}
```

#### Offline/Network Handling
```javascript
// Network Status Handler
class NetworkStatusHandler {
  private pendingSaves: any[] = [];
  
  constructor() {
    window.addEventListener('online', this.syncPendingSaves.bind(this));
    window.addEventListener('offline', this.handleOffline.bind(this));
  }
  
  async saveDraftWithRetry(draftData: any) {
    if (!navigator.onLine) {
      this.pendingSaves.push(draftData);
      this.showOfflineMessage();
      return;
    }
    
    try {
      await this.saveDraft(draftData);
    } catch (error) {
      if (this.isNetworkError(error)) {
        this.pendingSaves.push(draftData);
      }
      throw error;
    }
  }
  
  private async syncPendingSaves() {
    for (const draft of this.pendingSaves) {
      try {
        await this.saveDraft(draft);
      } catch (error) {
        console.error('Failed to sync draft:', error);
      }
    }
    this.pendingSaves = [];
  }
}
```

### Test Scenarios
1. **Manual Save**: Test explicit draft saving functionality
2. **Auto-Save**: Test automatic saving every 30 seconds
3. **Recovery**: Test draft recovery after browser refresh
4. **Multiple Drafts**: Test management of multiple draft requisitions
5. **Network Issues**: Test behavior during network interruptions
6. **Data Integrity**: Test that no data is lost during auto-save
7. **Performance**: Test auto-save performance with large forms
8. **Cleanup**: Test automatic cleanup of old/expired drafts

### Dependencies
- Requisition creation form (Story 2.1)
- Stable database connection handling
- Frontend state management (Pinia)
- Network connectivity monitoring

**Story Points Breakdown**: Frontend (8) + Backend (3) + Testing (2) = 13

---

## Story 2.5: Requisition Status Tracking and History
**Story ID**: ERP-E02-S05  
**Title**: Implement Real-Time Status Tracking  
**Priority**: P1  
**Story Points**: 17  

### User Story
**As a** requisition creator or approver  
**I want to** track the complete history and current status of requisitions  
**So that** I can understand the approval process and take appropriate actions  

### Background & Context
Users need complete visibility into requisition status changes, approval history, comments, and next steps. This includes real-time updates via WebSocket, email notifications, and comprehensive audit trails.

### Acceptance Criteria
**AC1**: Given any requisition, when I view its details, then I can see its current status, submission date, approval date (if applicable), and next required action

**AC2**: Given a requisition has status changes, when I view its history, then I can see all previous statuses, who made changes, when they occurred, and any associated comments

**AC3**: Given I am the requester, when my requisition status changes, then I receive real-time notification in the UI and an email notification with details

**AC4**: Given I am an approver, when new requisitions are submitted, then I receive real-time notifications and see them in my pending approvals dashboard

**AC5**: Given a requisition is questioned, when I view it, then I can see all questions, responses, and the conversation thread with timestamps

**AC6**: Given I am viewing any requisition list, when a status changes, then the list updates in real-time without requiring a page refresh

### Technical Implementation Notes

#### API Endpoints Required
```
GET /api/v1/requisitions/{id}/history         # Get complete status history
GET /api/v1/requisitions/{id}/timeline        # Get timeline view
GET /api/v1/requisitions/notifications        # Get user notifications
PUT /api/v1/requisitions/notifications/read   # Mark notifications as read
```

#### WebSocket Events
```typescript
// WebSocket Event Types
interface RequisitionStatusUpdate {
  requisitionId: string;
  newStatus: string;
  previousStatus: string;
  updatedBy: User;
  timestamp: string;
  comments?: string;
}

interface RequisitionNotification {
  type: 'status_change' | 'new_requisition' | 'question_received';
  requisitionId: string;
  message: string;
  timestamp: string;
  read: boolean;
}

// WebSocket Handler
class RequisitionWebSocketHandler {
  handleStatusUpdate(update: RequisitionStatusUpdate) {
    // Update UI status
    store.dispatch('updateRequisitionStatus', update);
    
    // Show notification
    ElNotification({
      title: 'Requisition Update',
      message: `Requisition ${update.requisitionId} is now ${update.newStatus}`,
      type: this.getNotificationType(update.newStatus)
    });
    
    // Update notifications count
    store.dispatch('incrementNotificationCount');
  }
}
```

#### Database Tables (Additional)
```sql
-- Notifications table
CREATE TABLE user_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    requisition_id INTEGER REFERENCES requisitions(id),
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Requisition timeline view
CREATE VIEW requisition_timeline AS
SELECT 
    r.id as requisition_id,
    r.req_number,
    'created' as event_type,
    r.created_at as event_time,
    u.username as actor,
    'Requisition created' as description,
    NULL as comments
FROM requisitions r
JOIN users u ON r.user_id = u.id

UNION ALL

SELECT 
    rsh.requisition_id,
    r.req_number,
    'status_change' as event_type,
    rsh.created_at as event_time,
    u.username as actor,
    CONCAT('Status changed from ', rsh.previous_status, ' to ', rsh.new_status) as description,
    rsh.reason as comments
FROM requisition_status_history rsh
JOIN requisitions r ON rsh.requisition_id = r.id
JOIN users u ON rsh.changed_by = u.id

UNION ALL

SELECT 
    rc.requisition_id,
    r.req_number,
    'comment' as event_type,
    rc.created_at as event_time,
    u.username as actor,
    CONCAT('Added ', rc.comment_type) as description,
    rc.comment_text as comments
FROM requisition_comments rc
JOIN requisitions r ON rc.requisition_id = r.id
JOIN users u ON rc.user_id = u.id

ORDER BY event_time DESC;
```

#### Frontend Components
```vue
<!-- RequisitionTimeline.vue -->
<template>
  <el-timeline>
    <el-timeline-item
      v-for="event in timeline"
      :key="event.id"
      :timestamp="formatDate(event.event_time)"
      :type="getTimelineType(event.event_type)"
    >
      <el-card>
        <h4>{{ event.description }}</h4>
        <p><strong>By:</strong> {{ event.actor }}</p>
        <p v-if="event.comments">{{ event.comments }}</p>
      </el-card>
    </el-timeline-item>
  </el-timeline>
</template>

<!-- RequisitionNotifications.vue -->
<template>
  <el-dropdown @command="handleNotificationClick">
    <el-badge :value="unreadCount" :hidden="unreadCount === 0">
      <el-button circle>
        <el-icon><Bell /></el-icon>
      </el-button>
    </el-badge>
    
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item
          v-for="notification in notifications"
          :key="notification.id"
          :command="notification"
          :class="{ 'unread': !notification.read_at }"
        >
          <div class="notification-item">
            <p class="title">{{ notification.title }}</p>
            <p class="message">{{ notification.message }}</p>
            <p class="time">{{ formatRelativeTime(notification.created_at) }}</p>
          </div>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>
```

### Test Scenarios
1. **Status Tracking**: Test status changes are properly tracked
2. **Real-time Updates**: Test WebSocket notifications work correctly
3. **Email Notifications**: Test email notifications for status changes
4. **History Display**: Test complete history and timeline views
5. **Permission Filtering**: Test users only see appropriate notifications
6. **Performance**: Test real-time updates with multiple concurrent users
7. **Network Resilience**: Test notification delivery after connection loss
8. **Notification Management**: Test marking notifications as read/unread

### Dependencies
- WebSocket infrastructure setup
- Email notification service
- Requisition approval workflow (Story 2.2)
- Database indexing for performance

**Story Points Breakdown**: Backend (8) + Frontend (6) + WebSocket (2) + Testing (1) = 17

---

## Story 2.6: Requisition Templates and Quick Actions
**Story ID**: ERP-E02-S06  
**Title**: Implement Requisition Templates for Efficiency  
**Priority**: P2  
**Story Points**: 13  

### User Story
**As an** Engineer  
**I want to** create and use requisition templates for commonly requested items  
**So that** I can quickly create new requisitions without re-entering standard information  

### Background & Context
Engineers often request similar sets of items for recurring projects or standard operations. Templates can significantly reduce data entry time and ensure consistency in item specifications and descriptions.

### Acceptance Criteria
**AC1**: Given I have created requisitions before, when I create a new requisition, then I can choose to base it on a previous requisition or saved template

**AC2**: Given I complete a requisition, when I save it, then I can choose to save it as a template for future use with a descriptive name

**AC3**: Given I have saved templates, when I manage my templates, then I can view, edit, delete, and organize my templates by category

**AC4**: Given I use a template, when I create a new requisition from it, then all template data is populated but I can modify any field before submission

**AC5**: Given I am creating a template, when I save it, then I can mark it as personal (only I can use) or shared (my team can use)

### Technical Implementation Notes

#### API Endpoints Required
```
GET /api/v1/requisitions/templates           # Get user's templates
POST /api/v1/requisitions/templates          # Create new template
PUT /api/v1/requisitions/templates/{id}      # Update template
DELETE /api/v1/requisitions/templates/{id}   # Delete template
POST /api/v1/requisitions/from-template/{id} # Create requisition from template
```

#### Database Changes
```sql
CREATE TABLE requisition_templates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    purpose VARCHAR(20) NOT NULL CHECK (purpose IN ('Daily Operations', 'Project-Specific')),
    is_shared BOOLEAN DEFAULT FALSE,
    category VARCHAR(100),
    template_data JSONB NOT NULL, -- Stores the template structure
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE template_items (
    id SERIAL PRIMARY KEY,
    template_id INTEGER NOT NULL REFERENCES requisition_templates(id) ON DELETE CASCADE,
    item_sequence INTEGER NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    description TEXT,
    default_quantity DECIMAL(10,3),
    unit VARCHAR(50) DEFAULT 'pcs',
    estimated_unit_price DECIMAL(10,2),
    specifications TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_templates_user ON requisition_templates(user_id, created_at DESC);
CREATE INDEX idx_templates_shared ON requisition_templates(is_shared, category) WHERE is_shared = TRUE;
```

### Test Scenarios
1. **Template Creation**: Test creating templates from requisitions
2. **Template Usage**: Test creating requisitions from templates
3. **Template Management**: Test editing and deleting templates
4. **Shared Templates**: Test team template sharing functionality
5. **Template Categories**: Test organizing templates by categories
6. **Performance**: Test template loading and usage performance

### Dependencies
- Requisition creation system (Story 2.1)
- User permission system for shared templates
- Template data validation and sanitization

**Story Points Breakdown**: Backend (6) + Frontend (5) + Testing (2) = 13

---

## Story 2.7: Bulk Operations and Data Export
**Story ID**: ERP-E02-S07  
**Title**: Implement Bulk Actions and Export Capabilities  
**Priority**: P2  
**Story Points**: 17  

### User Story
**As a** Procurement Manager  
**I want to** perform bulk operations on multiple requisitions and export data  
**So that** I can efficiently manage large volumes of requisitions and generate reports  

### Background & Context
Procurement managers often need to approve multiple requisitions, export data for external analysis, or perform bulk status updates. The system should support efficient bulk operations while maintaining data integrity.

### Acceptance Criteria
**AC1**: Given I am viewing a list of requisitions, when I select multiple items, then I can perform bulk actions: approve, reject, export to Excel, or print

**AC2**: Given I select requisitions for bulk approval, when I confirm the action, then all selected requisitions are approved simultaneously with audit logging

**AC3**: Given I want to export requisition data, when I choose export options, then I can select date ranges, status filters, and choose format (Excel, CSV, PDF report)

**AC4**: Given I export requisition data, when the export completes, then I receive a file with all relevant data: requisition details, items, approval history, and timestamps

**AC5**: Given I perform bulk operations, when any operation fails, then the system provides detailed error reporting and continues processing other items

### Technical Implementation Notes

#### API Endpoints Required
```
POST /api/v1/requisitions/bulk/approve       # Bulk approve requisitions
POST /api/v1/requisitions/bulk/reject        # Bulk reject requisitions  
POST /api/v1/requisitions/export             # Export requisitions data
GET /api/v1/requisitions/export/{job_id}     # Get export job status
```

#### Bulk Operations Implementation
```python
class BulkRequisitionService:
    def bulk_approve(self, requisition_ids: List[int], approver_id: int, comments: str = None):
        results = []
        
        for req_id in requisition_ids:
            try:
                approval = self.approve_single_requisition(req_id, approver_id, comments)
                results.append({
                    'requisition_id': req_id,
                    'status': 'success',
                    'approval_id': approval.id
                })
            except Exception as e:
                results.append({
                    'requisition_id': req_id,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
    
    def export_requisitions(self, filters: dict, format: str = 'excel'):
        # Create background job for large exports
        job = ExportJob.create(
            type='requisitions',
            filters=filters,
            format=format,
            created_by=current_user.id
        )
        
        # Queue background task
        export_task.delay(job.id)
        
        return job
```

### Test Scenarios
1. **Bulk Approval**: Test bulk approval of multiple requisitions
2. **Bulk Rejection**: Test bulk rejection with error handling
3. **Data Export**: Test Excel/CSV export functionality
4. **Export Performance**: Test export of large datasets
5. **Error Handling**: Test partial failure scenarios
6. **Permission Validation**: Test bulk operations respect user permissions

### Dependencies
- Requisition approval system (Story 2.2)
- Background job processing (Celery)
- Excel/PDF generation libraries
- File download handling

**Story Points Breakdown**: Backend (10) + Frontend (4) + Testing (3) = 17

---

## Epic Summary

### Total Story Points: 144
- Story 2.1: Multi-Item Requisition Creation (21 points)
- Story 2.2: Requisition Approval Workflow (34 points)
- Story 2.3: Advanced Search and Filtering (21 points)
- Story 2.4: Draft Management and Auto-Save (13 points)
- Story 2.5: Status Tracking and History (17 points)
- Story 2.6: Requisition Templates (13 points)
- Story 2.7: Bulk Operations and Export (17 points)

### Epic Dependencies
1. **Core Systems**: Authentication and authorization (Epic 1)
2. **Infrastructure**: Email service, WebSocket support, file storage
3. **Database**: PostgreSQL with full-text search capabilities
4. **External Services**: Background job processing, export libraries

### Epic Risks & Mitigations
- **Risk**: Complex approval workflows causing confusion
  - **Mitigation**: Clear UI indicators, comprehensive testing with users
- **Risk**: Performance issues with large datasets
  - **Mitigation**: Database optimization, pagination, caching strategies
- **Risk**: Data loss during auto-save operations
  - **Mitigation**: Robust error handling, transaction management

### Success Criteria
- Requisition creation time reduced by 60% compared to manual process
- Zero data loss during draft operations
- 100% of status changes tracked and audited
- Search operations complete within 2 seconds for datasets up to 10,000 records
- User satisfaction score >4.5/5.0 for requisition workflow

This epic provides the core requisition management functionality that drives the entire procurement process and serves as the foundation for purchase order generation.