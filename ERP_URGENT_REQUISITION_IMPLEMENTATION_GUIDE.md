# ERP 請購單加急功能技術實作文檔

## 1. 需求概述

### 1.1 核心需求
1. **請購單新增加急功能**
   - 新增請購單時可選擇「加急」選項
   - 選擇加急後必須填寫期望到貨日期和加急原因

2. **審核列表視覺標記**
   - 採購人員/採購主管審核時，列表中的加急項目整欄標記為紅色
   - 點開審核時可查看加急資訊

3. **採購單編輯提示**
   - 編輯採購單時，若供應商下有加急項目
   - 供應商下拉選單中該選項以紅色背景標註
   - 提醒採購人員優先製單

## 2. 系統架構分析

### 2.1 現有資料庫結構
- **request_orders 表**：請購單主表
- **request_order_items 表**：請購單項目表
- **purchase_orders 表**：採購單主表
- **suppliers 表**：供應商表

### 2.2 前端組件結構
- **請購單模組**：`frontend/src/views/requisitions/`
  - `Form.vue`：新增/編輯請購單
  - `Review.vue`：審核請購單
  - `List.vue`：請購單列表
- **採購單模組**：`frontend/src/views/purchase-orders/`
  - `Form.vue`：新增/編輯採購單
  - `BuildCandidates.vue`：建立採購單候選項目

### 2.3 後端 API 結構
- **請購單 API**：`backend/app/routes/requisitions.py`
- **採購單 API**：`backend/app/routes/purchase_orders.py`
- **模型定義**：`backend/app/models/request_order.py`

## 3. 資料庫修改方案

### 3.1 請購單主表新增欄位 (request_orders)

```sql
-- 新增加急相關欄位
ALTER TABLE request_orders ADD COLUMN is_urgent BOOLEAN DEFAULT FALSE;
ALTER TABLE request_orders ADD COLUMN expected_delivery_date DATE NULL;
ALTER TABLE request_orders ADD COLUMN urgent_reason TEXT NULL;
```

**欄位說明**：
- `is_urgent`：是否為加急請購單（布林值，預設 FALSE）
- `expected_delivery_date`：期望到貨日期（日期型別，可為空）
- `urgent_reason`：加急原因（文字型別，可為空）

### 3.2 資料庫遷移腳本

```python
# backend/migrations/versions/add_urgent_fields.py
"""Add urgent fields to request_orders

Revision ID: urgent_001
Revises: ef94b3ef0868
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa

revision = 'urgent_001'
down_revision = 'ef94b3ef0868'
branch_labels = None
depends_on = None

def upgrade():
    # Add urgent fields to request_orders table
    op.add_column('request_orders', sa.Column('is_urgent', sa.Boolean(), nullable=True, default=False))
    op.add_column('request_orders', sa.Column('expected_delivery_date', sa.Date(), nullable=True))
    op.add_column('request_orders', sa.Column('urgent_reason', sa.Text(), nullable=True))

    # Set default value for existing records
    op.execute("UPDATE request_orders SET is_urgent = FALSE WHERE is_urgent IS NULL")

    # Make is_urgent not nullable
    op.alter_column('request_orders', 'is_urgent', nullable=False)

def downgrade():
    op.drop_column('request_orders', 'urgent_reason')
    op.drop_column('request_orders', 'expected_delivery_date')
    op.drop_column('request_orders', 'is_urgent')
```

## 4. 後端實作方案

### 4.1 模型修改

**檔案位置**：`backend/app/models/request_order.py`

```python
class RequestOrder(db.Model):
    # ... 現有欄位 ...

    # 新增加急相關欄位
    is_urgent = db.Column(db.Boolean, nullable=False, default=False)
    expected_delivery_date = db.Column(db.Date, nullable=True)
    urgent_reason = db.Column(db.Text, nullable=True)

    def validate_urgent_fields(self):
        """驗證加急相關欄位"""
        if self.is_urgent:
            if not self.expected_delivery_date:
                raise ValueError("加急請購單必須填寫期望到貨日期")
            if not self.urgent_reason or not self.urgent_reason.strip():
                raise ValueError("加急請購單必須填寫加急原因")

            # 驗證期望到貨日期不能是過去的日期
            if self.expected_delivery_date < date.today():
                raise ValueError("期望到貨日期不能是過去的日期")

    def to_dict(self):
        data = {
            # ... 現有欄位 ...
            'is_urgent': self.is_urgent,
            'expected_delivery_date': self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            'urgent_reason': self.urgent_reason,
        }
        return data
```

### 4.2 API 端點修改

**檔案位置**：`backend/app/routes/requisitions.py`

```python
@bp.route('', methods=['POST'])
@authenticated_required
def create_requisition(current_user):
    """創建請購單 - 支援加急功能"""
    try:
        data = request.get_json()

        # ... 現有驗證邏輯 ...

        # 創建請購單
        requisition = RequestOrder(
            # ... 現有欄位 ...
            is_urgent=data.get('is_urgent', False),
            expected_delivery_date=datetime.strptime(data['expected_delivery_date'], '%Y-%m-%d').date()
                if data.get('expected_delivery_date') else None,
            urgent_reason=data.get('urgent_reason')
        )

        # 驗證加急相關欄位
        requisition.validate_urgent_fields()

        # ... 其餘邏輯 ...

    except ValueError as e:
        return create_error_response(
            'VALIDATION_ERROR',
            str(e),
            status_code=400
        )

@bp.route('/<request_order_no>', methods=['PUT'])
@authenticated_required
def update_requisition(current_user, request_order_no):
    """更新請購單 - 支援加急功能"""
    try:
        requisition = RequestOrder.query.get_or_404(request_order_no)
        data = request.get_json()

        # 檢查是否可以編輯
        if not requisition.can_edit():
            return create_error_response(
                'CANNOT_EDIT',
                '請購單無法編輯',
                status_code=400
            )

        # 更新加急相關欄位
        if 'is_urgent' in data:
            requisition.is_urgent = data['is_urgent']
        if 'expected_delivery_date' in data:
            requisition.expected_delivery_date = datetime.strptime(data['expected_delivery_date'], '%Y-%m-%d').date() \
                if data['expected_delivery_date'] else None
        if 'urgent_reason' in data:
            requisition.urgent_reason = data['urgent_reason']

        # 驗證加急相關欄位
        requisition.validate_urgent_fields()

        # ... 其餘更新邏輯 ...

    except ValueError as e:
        return create_error_response(
            'VALIDATION_ERROR',
            str(e),
            status_code=400
        )

@bp.route('/urgent-suppliers', methods=['GET'])
@procurement_required
def get_urgent_suppliers(current_user):
    """取得有加急項目的供應商列表"""
    try:
        # 查詢有加急且已核准項目的供應商
        urgent_suppliers = db.session.query(
            Supplier.supplier_id,
            Supplier.supplier_name_zh,
            db.func.count(RequestOrderItem.detail_id).label('urgent_item_count')
        ).join(
            RequestOrderItem, Supplier.supplier_id == RequestOrderItem.supplier_id
        ).join(
            RequestOrder, RequestOrderItem.request_order_no == RequestOrder.request_order_no
        ).filter(
            RequestOrder.is_urgent == True,
            RequestOrderItem.item_status == 'approved'
        ).group_by(
            Supplier.supplier_id,
            Supplier.supplier_name_zh
        ).all()

        result = []
        for supplier_id, supplier_name, count in urgent_suppliers:
            result.append({
                'supplier_id': supplier_id,
                'supplier_name_zh': supplier_name,
                'urgent_item_count': count
            })

        return create_response(result)

    except Exception as e:
        return create_error_response(
            'URGENT_SUPPLIERS_ERROR',
            'Failed to get urgent suppliers',
            {'error': str(e)},
            status_code=500
        )
```

### 4.3 採購單建立候選項目 API 修改

**檔案位置**：`backend/app/routes/purchase_orders.py`

```python
@bp.route('/build-candidates', methods=['GET'])
@procurement_required
def get_build_candidates(current_user):
    """Get approved items grouped by supplier for PO creation - 支援加急標記"""
    try:
        supplier_id = request.args.get('supplier_id')

        # 查詢時連接請購單主表以取得加急資訊
        query = db.session.query(RequestOrderItem, RequestOrder.is_urgent).join(
            RequestOrder, RequestOrderItem.request_order_no == RequestOrder.request_order_no
        ).filter(RequestOrderItem.item_status == 'approved')

        if supplier_id:
            query = query.filter(RequestOrderItem.supplier_id == supplier_id)

        results = query.all()

        # Group by supplier
        suppliers = {}
        for item, is_urgent in results:
            if item.supplier_id not in suppliers:
                suppliers[item.supplier_id] = {
                    'supplier_id': item.supplier_id,
                    'supplier': item.supplier.to_summary_dict() if item.supplier else None,
                    'has_urgent_items': False,
                    'items': []
                }

            # 標記供應商是否有加急項目
            if is_urgent:
                suppliers[item.supplier_id]['has_urgent_items'] = True

            item_dict = item.to_dict()
            item_dict['is_urgent'] = is_urgent
            suppliers[item.supplier_id]['items'].append(item_dict)

        return create_response(list(suppliers.values()))

    except Exception as e:
        return create_error_response(
            'BUILD_CANDIDATES_ERROR',
            'Failed to get build candidates',
            {'error': str(e)},
            status_code=500
        )
```

## 5. 前端實作方案

### 5.1 請購單新增/編輯表單修改

**檔案位置**：`frontend/src/views/requisitions/Form.vue`

#### 5.1.1 模板修改

```vue
<template>
  <div class="requisition-form">
    <!-- ... 現有內容 ... -->

    <!-- 基本信息區塊修改 -->
    <div class="form-section">
      <h3 class="section-title">基本信息</h3>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="用途類型" prop="usage_type" required>
            <el-radio-group v-model="formData.usage_type">
              <el-radio label="daily">日常用品</el-radio>
              <el-radio label="project">專案用品</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            v-if="formData.usage_type === 'project'"
            label="專案編號"
            prop="project_id"
            required
          >
            <!-- ... 現有專案選擇 ... -->
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 新增：加急設定區塊 -->
      <el-row :gutter="20">
        <el-col :span="24">
          <el-form-item label="加急設定">
            <el-checkbox
              v-model="formData.is_urgent"
              @change="onUrgentChange"
              class="urgent-checkbox"
            >
              <span class="urgent-label">此為加急請購單</span>
            </el-checkbox>
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 加急詳細資訊區塊 -->
      <div v-if="formData.is_urgent" class="urgent-details">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item
              label="期望到貨日期"
              prop="expected_delivery_date"
              required
            >
              <el-date-picker
                v-model="formData.expected_delivery_date"
                type="date"
                placeholder="選擇期望到貨日期"
                format="YYYY/MM/DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
                :disabled-date="disabledDate"
                class="urgent-date-picker"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item
              label="加急原因"
              prop="urgent_reason"
              required
            >
              <el-input
                v-model="formData.urgent_reason"
                type="textarea"
                :rows="3"
                placeholder="請詳細說明加急原因"
                maxlength="200"
                show-word-limit
                class="urgent-reason-input"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- ... 其餘現有內容 ... -->
  </div>
</template>
```

#### 5.1.2 腳本修改

```typescript
// 在 FormData 介面中新增欄位
interface FormData {
  usage_type: 'daily' | 'project'
  project_id?: string
  items: RequisitionItem[]
  // 新增加急相關欄位
  is_urgent: boolean
  expected_delivery_date?: string
  urgent_reason?: string
}

// 初始化表單資料
const formData = reactive<FormData>({
  usage_type: 'daily',
  items: [],
  // 新增加急相關欄位初始值
  is_urgent: false,
  expected_delivery_date: undefined,
  urgent_reason: ''
})

// 表單驗證規則新增
const formRules = {
  // ... 現有規則 ...
  expected_delivery_date: [
    {
      required: true,
      message: '請選擇期望到貨日期',
      trigger: 'change',
      validator: (rule: any, value: any, callback: any) => {
        if (formData.is_urgent && !value) {
          callback(new Error('加急請購單必須選擇期望到貨日期'))
        } else {
          callback()
        }
      }
    }
  ],
  urgent_reason: [
    {
      required: true,
      message: '請填寫加急原因',
      trigger: 'blur',
      validator: (rule: any, value: any, callback: any) => {
        if (formData.is_urgent && (!value || !value.trim())) {
          callback(new Error('加急請購單必須填寫加急原因'))
        } else {
          callback()
        }
      }
    }
  ]
}

// 新增方法
const onUrgentChange = (isUrgent: boolean) => {
  if (!isUrgent) {
    // 取消加急時清空相關欄位
    formData.expected_delivery_date = undefined
    formData.urgent_reason = ''
  }
}

const disabledDate = (time: Date) => {
  // 禁用今天之前的日期
  return time.getTime() < Date.now() - 8.64e7
}

// 修改提交請求資料
const handleSubmit = async () => {
  // ... 現有驗證邏輯 ...

  const requestData: CreateRequisitionRequest = {
    usage_type: formData.usage_type,
    project_id: formData.project_id,
    status: 'submitted',
    // 新增加急相關欄位
    is_urgent: formData.is_urgent,
    expected_delivery_date: formData.expected_delivery_date,
    urgent_reason: formData.urgent_reason,
    items: formData.items.map(item => ({
      // ... 現有項目欄位 ...
    }))
  }

  // ... 其餘邏輯 ...
}
```

#### 5.1.3 樣式修改

```scss
.requisition-form {
  // ... 現有樣式 ...

  .urgent-details {
    background: #fff2f0;
    border: 1px solid #ffccc7;
    border-radius: 6px;
    padding: 16px;
    margin-top: 16px;

    .el-form-item__label {
      color: #cf1322;
      font-weight: 600;
    }
  }

  .urgent-checkbox {
    .urgent-label {
      color: #cf1322;
      font-weight: 600;
    }
  }

  .urgent-date-picker {
    :deep(.el-input__inner) {
      border-color: #ff7875;

      &:focus {
        border-color: #cf1322;
        box-shadow: 0 0 0 2px rgba(207, 19, 34, 0.2);
      }
    }
  }

  .urgent-reason-input {
    :deep(.el-textarea__inner) {
      border-color: #ff7875;

      &:focus {
        border-color: #cf1322;
        box-shadow: 0 0 0 2px rgba(207, 19, 34, 0.2);
      }
    }
  }
}
```

### 5.2 請購單審核頁面修改

**檔案位置**：`frontend/src/views/requisitions/Review.vue`

#### 5.2.1 模板修改

```vue
<template>
  <div class="requisition-review">
    <div class="review-header">
      <div class="requisition-info">
        <h3>
          {{ requisition.request_order_no }}
          <!-- 新增：加急標記 -->
          <el-tag
            v-if="requisition.is_urgent"
            type="danger"
            effect="dark"
            class="urgent-tag"
          >
            <el-icon><Warning /></el-icon>
            加急
          </el-tag>
        </h3>
        <div class="info-meta">
          <el-tag>{{ requisition.requester_name }}</el-tag>
          <el-tag type="info">{{ requisition.usage_type === 'daily' ? '日常用品' : '專案用品' }}</el-tag>
          <StatusTag :status="requisition.order_status" />
        </div>

        <!-- 新增：加急資訊顯示 -->
        <div v-if="requisition.is_urgent" class="urgent-info">
          <div class="urgent-info-item">
            <span class="label">期望到貨日期：</span>
            <span class="value urgent-date">{{ formatDate(requisition.expected_delivery_date) }}</span>
          </div>
          <div class="urgent-info-item">
            <span class="label">加急原因：</span>
            <span class="value">{{ requisition.urgent_reason }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="review-content">
      <!-- 項目表格 - 加急項目整列標紅 -->
      <div class="table-wrapper">
        <el-table
          :data="items"
          border
          max-height="600px"
          @selection-change="handleSelectionChange"
          style="min-width: 1200px"
          class="review-table"
          :row-class-name="getRowClassName"
        >
          <!-- ... 現有欄位 ... -->
        </el-table>
      </div>
    </div>

    <!-- ... 其餘現有內容 ... -->
  </div>
</template>

<script setup lang="ts">
import { Warning } from '@element-plus/icons-vue'

// ... 現有邏輯 ...

// 新增方法
const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('zh-TW')
}

const getRowClassName = ({ row }: { row: any }) => {
  // 如果是加急請購單的項目，整列標紅
  return props.requisition.is_urgent ? 'urgent-row' : ''
}

// ... 其餘現有邏輯 ...
</script>
```

#### 5.2.2 樣式修改

```scss
.requisition-review {
  // ... 現有樣式 ...

  .review-header {
    .requisition-info {
      h3 {
        display: flex;
        align-items: center;
        gap: 12px;

        .urgent-tag {
          animation: urgentPulse 2s infinite;

          .el-icon {
            margin-right: 4px;
          }
        }
      }

      .urgent-info {
        margin-top: 12px;
        padding: 12px;
        background: #fff2f0;
        border: 1px solid #ffccc7;
        border-radius: 6px;

        .urgent-info-item {
          display: flex;
          align-items: flex-start;
          margin-bottom: 8px;

          &:last-child {
            margin-bottom: 0;
          }

          .label {
            font-weight: 600;
            color: #cf1322;
            min-width: 120px;
          }

          .value {
            flex: 1;

            &.urgent-date {
              font-weight: 600;
              color: #cf1322;
            }
          }
        }
      }
    }
  }

  // 加急項目列樣式
  .review-table {
    :deep(.urgent-row) {
      background-color: #fff2f0 !important;

      td {
        border-color: #ffccc7 !important;

        &:first-child {
          border-left: 4px solid #cf1322 !important;
        }
      }

      &:hover {
        background-color: #ffebe8 !important;
      }
    }
  }
}

// 加急標記動畫
@keyframes urgentPulse {
  0% {
    box-shadow: 0 0 0 0 rgba(207, 19, 34, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(207, 19, 34, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(207, 19, 34, 0);
  }
}
```

### 5.3 採購單建立頁面修改

**檔案位置**：`frontend/src/views/purchase-orders/BuildCandidates.vue`

#### 5.3.1 模板修改

```vue
<template>
  <div class="build-candidates">
    <!-- ... 現有內容 ... -->

    <!-- 供應商列表 - 有加急項目的供應商標紅 -->
    <div class="suppliers-list">
      <el-card
        v-for="supplier in suppliers"
        :key="supplier.supplier_id"
        :class="['supplier-card', { 'urgent-supplier': supplier.has_urgent_items }]"
        @click="selectSupplier(supplier)"
      >
        <div class="supplier-header">
          <h3>
            {{ supplier.supplier.supplier_name_zh }}
            <!-- 新增：加急標記 -->
            <el-tag
              v-if="supplier.has_urgent_items"
              type="danger"
              size="small"
              effect="dark"
              class="urgent-supplier-tag"
            >
              <el-icon><Warning /></el-icon>
              有加急項目
            </el-tag>
          </h3>
          <p>{{ supplier.supplier.supplier_id }}</p>
        </div>

        <div class="supplier-stats">
          <span>共 {{ supplier.items.length }} 個項目</span>
          <span v-if="supplier.has_urgent_items" class="urgent-count">
            其中 {{ getUrgentItemCount(supplier.items) }} 個加急項目
          </span>
        </div>

        <!-- 項目列表預覽 -->
        <div class="items-preview">
          <div
            v-for="item in supplier.items.slice(0, 3)"
            :key="item.detail_id"
            :class="['item-preview', { 'urgent-item': item.is_urgent }]"
          >
            <span class="item-name">{{ item.item_name }}</span>
            <span class="item-qty">{{ item.item_quantity }} {{ item.item_unit }}</span>
            <el-tag v-if="item.is_urgent" type="danger" size="small">加急</el-tag>
          </div>
          <div v-if="supplier.items.length > 3" class="more-items">
            還有 {{ supplier.items.length - 3 }} 個項目...
          </div>
        </div>
      </el-card>
    </div>

    <!-- ... 其餘現有內容 ... -->
  </div>
</template>

<script setup lang="ts">
import { Warning } from '@element-plus/icons-vue'

// ... 現有邏輯 ...

// 新增方法
const getUrgentItemCount = (items: any[]) => {
  return items.filter(item => item.is_urgent).length
}

// ... 其餘現有邏輯 ...
</script>
```

#### 5.3.2 樣式修改

```scss
.build-candidates {
  // ... 現有樣式 ...

  .suppliers-list {
    .supplier-card {
      transition: all 0.3s ease;
      cursor: pointer;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }

      // 有加急項目的供應商卡片
      &.urgent-supplier {
        border: 2px solid #ff7875;
        background: linear-gradient(135deg, #fff2f0 0%, #ffffff 100%);

        .supplier-header h3 {
          color: #cf1322;
        }

        &:hover {
          border-color: #cf1322;
          box-shadow: 0 4px 12px rgba(207, 19, 34, 0.2);
        }
      }

      .supplier-header {
        h3 {
          display: flex;
          align-items: center;
          gap: 8px;

          .urgent-supplier-tag {
            animation: urgentPulse 2s infinite;

            .el-icon {
              margin-right: 4px;
            }
          }
        }
      }

      .supplier-stats {
        .urgent-count {
          color: #cf1322;
          font-weight: 600;
          margin-left: 12px;
        }
      }

      .items-preview {
        .item-preview {
          &.urgent-item {
            background: #fff2f0;
            border-left: 3px solid #cf1322;
            padding-left: 8px;
          }
        }
      }
    }
  }
}
```

### 5.4 採購單表單修改

**檔案位置**：`frontend/src/views/purchase-orders/Form.vue`

#### 5.4.1 模板修改

```vue
<template>
  <div class="purchase-order-form">
    <!-- ... 現有內容 ... -->

    <el-form-item label="供應商" prop="supplier_id">
      <el-select
        v-model="form.supplier_id"
        placeholder="選擇供應商"
        style="width: 100%"
        @change="onSupplierChange"
      >
        <el-option
          v-for="supplier in suppliers"
          :key="supplier.supplier_id"
          :label="`${supplier.supplier_id} - ${supplier.supplier_name_zh}`"
          :value="supplier.supplier_id"
          :class="{ 'urgent-supplier-option': isUrgentSupplier(supplier.supplier_id) }"
        >
          <div class="supplier-option-content">
            <span>{{ supplier.supplier_id }} - {{ supplier.supplier_name_zh }}</span>
            <el-tag
              v-if="isUrgentSupplier(supplier.supplier_id)"
              type="danger"
              size="small"
              class="urgent-option-tag"
            >
              有加急項目
            </el-tag>
          </div>
        </el-option>
      </el-select>
    </el-form-item>

    <!-- ... 其餘現有內容 ... -->
  </div>
</template>

<script setup lang="ts">
// ... 現有邏輯 ...

// 新增狀態
const urgentSuppliers = ref<string[]>([])

// 新增方法
const isUrgentSupplier = (supplierId: string) => {
  return urgentSuppliers.value.includes(supplierId)
}

const fetchUrgentSuppliers = async () => {
  try {
    const response = await requisitionsApi.getUrgentSuppliers()
    urgentSuppliers.value = response.map((s: any) => s.supplier_id)
  } catch (error) {
    console.error('Failed to fetch urgent suppliers:', error)
  }
}

// 在 onMounted 中呼叫
onMounted(async () => {
  // ... 現有邏輯 ...
  await fetchUrgentSuppliers()
})
</script>
```

#### 5.4.2 樣式修改

```scss
.purchase-order-form {
  // ... 現有樣式 ...

  :deep(.urgent-supplier-option) {
    background: #fff2f0 !important;
    border-left: 4px solid #cf1322;

    &:hover {
      background: #ffebe8 !important;
    }

    .supplier-option-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;

      .urgent-option-tag {
        margin-left: 8px;
      }
    }
  }
}
```

## 6. 前端 API 整合

### 6.1 API 類型定義

**檔案位置**：`frontend/src/types/common.ts`

```typescript
// 更新 RequestOrder 介面
export interface RequestOrder {
  request_order_no: string
  requester_id: number
  requester_name: string
  usage_type: 'daily' | 'project'
  project_id?: string
  submit_date?: string
  order_status: string
  created_at?: string
  updated_at?: string
  items?: RequestOrderItem[]
  summary?: any
  // 新增加急相關欄位
  is_urgent: boolean
  expected_delivery_date?: string
  urgent_reason?: string
}

// 新增請購單創建請求介面
export interface CreateRequisitionRequest {
  usage_type: 'daily' | 'project'
  project_id?: string
  status?: string
  items: RequisitionItem[]
  // 新增加急相關欄位
  is_urgent: boolean
  expected_delivery_date?: string
  urgent_reason?: string
}

// 新增加急供應商介面
export interface UrgentSupplier {
  supplier_id: string
  supplier_name_zh: string
  urgent_item_count: number
}
```

### 6.2 API 服務更新

**檔案位置**：`frontend/src/api/requisition.ts`

```typescript
// 新增 API 方法
export const requisitionsApi = {
  // ... 現有方法 ...

  // 取得有加急項目的供應商
  getUrgentSuppliers(): Promise<UrgentSupplier[]> {
    return request.get('/api/v1/requisitions/urgent-suppliers')
  },

  // 創建請購單（支援加急）
  createRequisition(data: CreateRequisitionRequest): Promise<RequestOrder> {
    return request.post('/api/v1/requisitions', data)
  },

  // 更新請購單（支援加急）
  updateRequisition(id: string, data: CreateRequisitionRequest): Promise<RequestOrder> {
    return request.put(`/api/v1/requisitions/${id}`, data)
  }
}
```

## 7. 實作步驟

### 7.1 後端實作順序

1. **資料庫遷移**
   ```bash
   cd backend
   flask db migrate -m "Add urgent fields to request_orders"
   flask db upgrade
   ```

2. **模型更新**
   - 修改 `backend/app/models/request_order.py`
   - 新增加急相關欄位和驗證方法

3. **API 端點更新**
   - 修改 `backend/app/routes/requisitions.py`
   - 修改 `backend/app/routes/purchase_orders.py`
   - 新增加急供應商查詢端點

4. **測試後端功能**
   ```bash
   python test_urgent_functionality.py
   ```

### 7.2 前端實作順序

1. **類型定義更新**
   - 修改 `frontend/src/types/common.ts`
   - 新增加急相關介面

2. **API 服務更新**
   - 修改 `frontend/src/api/requisition.ts`
   - 新增加急相關 API 方法

3. **組件更新**
   - 修改請購單表單 `Form.vue`
   - 修改請購單審核 `Review.vue`
   - 修改採購單建立 `BuildCandidates.vue`
   - 修改採購單表單 `Form.vue`

4. **樣式整合**
   - 新增加急相關 CSS 樣式
   - 確保響應式設計

5. **測試前端功能**
   - 測試加急請購單建立
   - 測試審核介面顯示
   - 測試採購單建立提示

### 7.3 整合測試

1. **端到端測試流程**
   - 建立加急請購單
   - 審核加急項目
   - 建立採購單時確認提示
   - 驗證視覺標記正確性

2. **效能測試**
   - 測試大量資料下的查詢效能
   - 確認加急標記不影響系統效能

## 8. 注意事項

### 8.1 資料驗證
- 加急請購單必須填寫期望到貨日期和加急原因
- 期望到貨日期不能是過去的日期
- 加急原因不能為空白

### 8.2 權限控制
- 所有使用者都可以建立加急請購單
- 採購人員和採購主管可以查看加急資訊
- 加急資訊在審核過程中清楚可見

### 8.3 視覺設計原則
- 使用紅色 (#cf1322) 作為加急的主色調
- 確保加急標記在各種背景下都清晰可見
- 保持一致的視覺語言

### 8.4 效能考量
- 加急供應商查詢應該快取結果
- 避免在列表頁面進行過多的關聯查詢
- 確保資料庫索引優化

## 9. 測試案例

### 9.1 功能測試
1. 建立一般請購單（非加急）
2. 建立加急請購單（包含必填欄位驗證）
3. 編輯加急請購單
4. 審核加急請購單（視覺標記驗證）
5. 建立採購單時加急供應商提示

### 9.2 邊界測試
1. 期望到貨日期設為今天
2. 期望到貨日期設為過去日期（應失敗）
3. 加急原因為空白（應失敗）
4. 取消加急設定後重新設定

### 9.3 整合測試
1. 多個使用者同時操作加急請購單
2. 加急請購單的完整工作流程
3. 資料庫遷移後的相容性測試

## 10. 部署注意事項

### 10.1 資料庫遷移
- 在生產環境部署前先備份資料庫
- 在測試環境驗證遷移腳本
- 確認既有資料的相容性

### 10.2 向下相容性
- 確保既有的 API 介面不受影響
- 新增欄位都設為可選或有預設值
- 前端組件向下相容舊版本資料

### 10.3 監控和日誌
- 新增加急功能相關的監控指標
- 記錄加急請購單的建立和審核日誌
- 監控加急功能對系統效能的影響

---

這份技術實作文檔提供了完整的加急功能實作指南，開發人員可以依照此文檔進行系統開發和部署。