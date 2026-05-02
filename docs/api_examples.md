# API Examples

## Demo Login

```http
POST /api/v1/auth/demo-login
Content-Type: application/json

{
  "nickname": "xiaoxiao"
}
```

## Parse Quote

```http
POST /api/v1/quotes/parse
Content-Type: application/json

{
  "supplier_name": "Shenzhen Parts Co.",
  "currency": "CNY",
  "source_text": "Laptop stand x 10 unit_price 88 lead_time 5 shipping 20 tax included"
}
```

## Compare Quotes

```http
POST /api/v1/quotes/compare
Content-Type: application/json

{
  "demand_title": "Laptop Stand Purchase",
  "quotes": [
    {
      "supplier_name": "Shenzhen Parts Co.",
      "shipping_fee": 20,
      "parse_confidence": 0.92,
      "items": [
        {
          "product_name": "Laptop stand",
          "quantity": 10,
          "unit_price": 88,
          "currency": "CNY",
          "lead_time_days": 5,
          "line_total": 880
        }
      ]
    },
    {
      "supplier_name": "Guangzhou Smart Supply",
      "shipping_fee": 30,
      "parse_confidence": 0.87,
      "items": [
        {
          "product_name": "Laptop stand",
          "quantity": 10,
          "unit_price": 90,
          "currency": "CNY",
          "lead_time_days": 3,
          "line_total": 900
        }
      ]
    }
  ]
}
```

## Analyze Text

```http
POST /api/v1/ai/analyze-text
Content-Type: application/json

{
  "text": "display screen module quotation quantity 20 unit price 320 lead_time 12 shipping 40 tax included"
}
```

## Upload Quote File (Image/PDF)

上传报价单图片或 PDF 文件进行解析。支持的文件格式：JPG、JPEG、PNG、GIF、BMP、PDF。

```http
POST /api/v1/upload/upload
Content-Type: multipart/form-data

file: @/path/to/quote.jpg
```

**响应示例：**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "quote.jpg",
  "file_type": "image/jpeg",
  "status": "pending",
  "message": "File uploaded successfully. Parsing in progress."
}
```

**Python 示例：**

```python
import requests

url = "http://localhost:8000/api/v1/upload/upload"
files = {"file": open("quote.pdf", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

**cURL 示例：**

```bash
curl -X POST "http://localhost:8000/api/v1/upload/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@quote.jpg"
```

## Get Task Status

查询解析任务的状态和结果。

```http
GET /api/v1/upload/tasks/{task_id}
```

**响应示例（处理中）：**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "quote.jpg",
  "file_type": "image/jpeg",
  "status": "processing",
  "error_message": null,
  "parse_result": null,
  "supplier_name": null,
  "created_at": "2026-04-28T10:30:00",
  "updated_at": "2026-04-28T10:30:05",
  "completed_at": null
}
```

**响应示例（完成）：**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "quote.jpg",
  "file_type": "image/jpeg",
  "status": "completed",
  "error_message": null,
  "parse_result": {
    "supplier_name": "Uploaded_Quote",
    "currency": "CNY",
    "items": [
      {
        "product_name": "Laptop stand",
        "quantity": 10,
        "unit_price": 88.0,
        "currency": "CNY",
        "lead_time_days": 5,
        "line_total": 880.0
      }
    ],
    "shipping_fee": 20.0,
    "tax_included": true,
    "parse_confidence": 0.9,
    "warnings": [],
    "source_preview": "Laptop stand x 10 unit_price 88..."
  },
  "supplier_name": "Uploaded_Quote",
  "created_at": "2026-04-28T10:30:00",
  "updated_at": "2026-04-28T10:30:15",
  "completed_at": "2026-04-28T10:30:15"
}
```

**响应示例（失败）：**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "quote.jpg",
  "file_type": "image/jpeg",
  "status": "failed",
  "error_message": "Failed to extract text from image: Tesseract not found",
  "parse_result": null,
  "supplier_name": null,
  "created_at": "2026-04-28T10:30:00",
  "updated_at": "2026-04-28T10:30:10",
  "completed_at": "2026-04-28T10:30:10"
}
```

## List Tasks

获取任务列表，支持按状态过滤和分页。

```http
GET /api/v1/upload/tasks?status=completed&limit=20&offset=0
```

**参数说明：**
- `status` (可选): 按状态过滤，可选值：`pending`, `processing`, `completed`, `failed`
- `limit` (可选): 返回数量限制，默认 50，最大 100
- `offset` (可选): 偏移量，默认 0

**响应示例：**

```json
{
  "total": 15,
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "file_name": "quote.pdf",
      "file_type": "application/pdf",
      "status": "completed",
      "error_message": null,
      "parse_result": {...},
      "supplier_name": "Uploaded_Quote",
      "created_at": "2026-04-28T10:30:00",
      "updated_at": "2026-04-28T10:30:15",
      "completed_at": "2026-04-28T10:30:15"
    },
    ...
  ]
}
```

## Error Responses

所有错误响应都遵循统一的格式：

```json
{
  "error_code": "ERROR_CODE",
  "message": "Human readable error message",
  "details": {
    "additional": "information"
  }
}
```

**常见错误码：**

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `INVALID_FILE_TYPE` | 400 | 文件类型不支持 |
| `FILE_TOO_LARGE` | 413 | 文件超过大小限制（默认 50MB） |
| `FILE_SAVE_ERROR` | 500 | 文件保存失败 |
| `TASK_NOT_FOUND` | 404 | 任务不存在 |
| `VALIDATION_ERROR` | 422 | 请求参数验证失败 |
| `INTERNAL_SERVER_ERROR` | 500 | 服务器内部错误 |

**无效文件类型示例：**

```http
POST /api/v1/upload/upload
Content-Type: multipart/form-data

file: @document.txt
```

**响应：**

```json
{
  "error_code": "INVALID_FILE_TYPE",
  "message": "File extension '.txt' is not allowed. Allowed: .jpg, .jpeg, .png, .gif, .bmp, .pdf",
  "details": null
}
```

---

## 用户管理 (Users)

### 创建用户

```http
POST /api/v1/users
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "nickname": "John Doe",
  "role": "buyer",
  "company_id": "demo-company-001"
}
```

**响应：**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "nickname": "John Doe",
  "role": "buyer",
  "company_id": "demo-company-001",
  "is_active": true,
  "last_login_at": null,
  "created_at": "2026-04-28T10:30:00",
  "updated_at": "2026-04-28T10:30:00"
}
```

### 用户登录

```http
POST /api/v1/users/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePass123"
}
```

**响应：**

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "nickname": "John Doe",
    "role": "buyer",
    "company_id": "demo-company-001",
    "is_active": true,
    "last_login_at": "2026-04-28T11:00:00",
    "created_at": "2026-04-28T10:30:00",
    "updated_at": "2026-04-28T11:00:00"
  },
  "token": "token_550e8400-e29b-41d4-a716-446655440000_1744542000",
  "expires_at": "2026-04-29T11:00:00"
}
```

### 获取用户列表

```http
GET /api/v1/users?role=buyer&limit=20&offset=0
```

**响应：**

```json
{
  "total": 15,
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "john_doe",
      "email": "john@example.com",
      "nickname": "John Doe",
      "role": "buyer",
      "company_id": "demo-company-001",
      "is_active": true,
      "last_login_at": "2026-04-28T11:00:00",
      "created_at": "2026-04-28T10:30:00",
      "updated_at": "2026-04-28T11:00:00"
    }
  ]
}
```

### 获取单个用户

```http
GET /api/v1/users/550e8400-e29b-41d4-a716-446655440000
```

### 更新用户

```http
PUT /api/v1/users/550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "nickname": "John Updated",
  "email": "john_new@example.com"
}
```

### 修改密码

```http
POST /api/v1/users/550e8400-e29b-41d4-a716-446655440000/change-password
Content-Type: application/json

{
  "old_password": "SecurePass123",
  "new_password": "NewSecurePass456"
}
```

### 删除用户

```http
DELETE /api/v1/users/550e8400-e29b-41d4-a716-446655440000
```

---

## 供应商管理 (Suppliers)

### 创建供应商

```http
POST /api/v1/suppliers
Content-Type: application/json

{
  "name": "Shenzhen Electronics Co., Ltd.",
  "short_name": "SZ Electronics",
  "contact_person": "张先生",
  "phone": "13800138000",
  "email": "contact@szelec.com",
  "address": "广东省深圳市南山区科技园",
  "tax_id": "91440300MA5D8Y4K8L",
  "bank_name": "中国工商银行深圳分行",
  "bank_account": "6222024000001234567",
  "status": "active",
  "is_verified": true,
  "notes": "主要供应商，合作5年"
}
```

**响应：**

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "Shenzhen Electronics Co., Ltd.",
  "short_name": "SZ Electronics",
  "contact_person": "张先生",
  "phone": "13800138000",
  "email": "contact@szelec.com",
  "address": "广东省深圳市南山区科技园",
  "tax_id": "91440300MA5D8Y4K8L",
  "bank_name": "中国工商银行深圳分行",
  "bank_account": "6222024000001234567",
  "rating": 3.0,
  "status": "active",
  "is_verified": true,
  "notes": "主要供应商，合作5年",
  "extra": null,
  "created_by": "demo-user-001",
  "created_at": "2026-04-28T10:30:00",
  "updated_at": "2026-04-28T10:30:00"
}
```

### 获取供应商列表

```http
GET /api/v1/suppliers?status=active&limit=20&offset=0
```

### 获取单个供应商

```http
GET /api/v1/suppliers/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### 更新供应商

```http
PUT /api/v1/suppliers/a1b2c3d4-e5f6-7890-abcd-ef1234567890
Content-Type: application/json

{
  "phone": "13900139000",
  "is_verified": true
}
```

### 更新供应商评分

```http
PATCH /api/v1/suppliers/a1b2c3d4-e5f6-7890-abcd-ef1234567890/rating
Content-Type: application/json

{
  "rating": 4.5
}
```

### 删除供应商

```http
DELETE /api/v1/suppliers/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

---

## 报价单管理 (Quote CRUD)

### 创建报价单

```http
POST /api/v1/quote-crud
Content-Type: application/json

{
  "quote_number": "QT-2026-001",
  "supplier_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "demand_title": "办公设备采购",
  "currency": "CNY",
  "shipping_fee": 50.0,
  "tax_rate": 0.13,
  "discount_amount": 100.0,
  "status": "draft",
  "terms": "付款方式：预付30%，货到付清余款",
  "notes": "报价有效期30天",
  "items": [
    {
      "line_number": 1,
      "product_name": "笔记本电脑支架",
      "product_code": "LAP-001",
      "product_category": "办公设备",
      "quantity": 10,
      "unit": "pc",
      "unit_price": 88.0,
      "currency": "CNY",
      "lead_time_days": 5,
      "description": "铝合金材质，可调节高度"
    },
    {
      "line_number": 2,
      "product_name": "机械键盘",
      "product_code": "KEY-002",
      "product_category": "办公设备",
      "quantity": 10,
      "unit": "pc",
      "unit_price": 150.0,
      "currency": "CNY",
      "lead_time_days": 3,
      "description": "青轴，RGB背光"
    }
  ]
}
```

**响应：**

```json
{
  "id": "quote-001-abcdef",
  "quote_number": "QT-2026-001",
  "supplier_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "demo-user-001",
  "demand_title": "办公设备采购",
  "currency": "CNY",
  "item_count": 2,
  "sub_total": 2380.0,
  "shipping_fee": 50.0,
  "tax_rate": 0.13,
  "tax_amount": 309.4,
  "discount_amount": 100.0,
  "grand_total": 2639.4,
  "status": "draft",
  "valid_from": null,
  "valid_until": null,
  "terms": "付款方式：预付30%，货到付清余款",
  "notes": "报价有效期30天",
  "extra": null,
  "submitted_at": null,
  "approved_at": null,
  "rejected_at": null,
  "rejected_reason": null,
  "created_at": "2026-04-28T10:30:00",
  "updated_at": "2026-04-28T10:30:00",
  "items": [
    {
      "id": "item-001",
      "quote_id": "quote-001-abcdef",
      "line_number": 1,
      "product_name": "笔记本电脑支架",
      "product_code": "LAP-001",
      "product_category": "办公设备",
      "quantity": 10,
      "unit": "pc",
      "unit_price": 88.0,
      "currency": "CNY",
      "line_total": 880.0,
      "lead_time_days": 5,
      "specs": null,
      "description": "铝合金材质，可调节高度",
      "created_at": "2026-04-28T10:30:00"
    },
    {
      "id": "item-002",
      "quote_id": "quote-001-abcdef",
      "line_number": 2,
      "product_name": "机械键盘",
      "product_code": "KEY-002",
      "product_category": "办公设备",
      "quantity": 10,
      "unit": "pc",
      "unit_price": 150.0,
      "currency": "CNY",
      "line_total": 1500.0,
      "lead_time_days": 3,
      "specs": null,
      "description": "青轴，RGB背光",
      "created_at": "2026-04-28T10:30:00"
    }
  ]
}
```

### 获取报价单列表

```http
GET /api/v1/quote-crud?status=draft&limit=20&offset=0
```

### 获取报价单统计

```http
GET /api/v1/quote-crud/summary
```

**响应：**

```json
{
  "total_quotes": 15,
  "total_amount": 45678.50,
  "by_status": {
    "draft": 5,
    "submitted": 3,
    "approved": 5,
    "rejected": 2
  },
  "by_supplier": {
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890": 8,
    "another-supplier-id": 7
  }
}
```

### 获取单个报价单

```http
GET /api/v1/quote-crud/quote-001-abcdef
```

### 更新报价单

```http
PUT /api/v1/quote-crud/quote-001-abcdef
Content-Type: application/json

{
  "shipping_fee": 30.0,
  "notes": "更新备注信息"
}
```

### 提交报价单

```http
POST /api/v1/quote-crud/quote-001-abcdef/submit
Content-Type: application/json

{}
```

### 审批报价单

```http
POST /api/v1/quote-crud/quote-001-abcdef/approve
Content-Type: application/json

{
  "notes": "价格合理，同意审批"
}
```

### 拒绝报价单

```http
POST /api/v1/quote-crud/quote-001-abcdef/reject
Content-Type: application/json

{
  "reason": "价格过高，超出预算范围"
}
```

### 添加报价单明细

```http
POST /api/v1/quote-crud/quote-001-abcdef/items
Content-Type: application/json

{
  "line_number": 3,
  "product_name": "无线鼠标",
  "product_code": "MOU-003",
  "product_category": "办公设备",
  "quantity": 10,
  "unit": "pc",
  "unit_price": 45.0,
  "currency": "CNY",
  "lead_time_days": 2,
  "description": "蓝牙5.0，静音按键"
}
```

### 更新报价单明细

```http
PUT /api/v1/quote-crud/quote-001-abcdef/items/item-001
Content-Type: application/json

{
  "unit_price": 85.0,
  "quantity": 15
}
```

### 删除报价单明细

```http
DELETE /api/v1/quote-crud/quote-001-abcdef/items/item-001
```

### 删除报价单

```http
DELETE /api/v1/quote-crud/quote-001-abcdef
```

---

## 新增错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `USERNAME_EXISTS` | 409 | 用户名已存在 |
| `EMAIL_EXISTS` | 409 | 邮箱已存在 |
| `USER_NOT_FOUND` | 404 | 用户不存在 |
| `INVALID_CREDENTIALS` | 401 | 用户名或密码错误 |
| `USER_INACTIVE` | 403 | 用户账户已停用 |
| `INVALID_PASSWORD` | 400 | 密码错误 |
| `SUPPLIER_EXISTS` | 409 | 供应商名称已存在 |
| `SUPPLIER_NOT_FOUND` | 404 | 供应商不存在 |
| `QUOTE_NOT_FOUND` | 404 | 报价单不存在 |
| `ITEM_NOT_FOUND` | 404 | 报价单明细不存在 |
| `INVALID_STATUS` | 400 | 状态无效（如重复提交、审批非草稿状态的报价单） |

---

## 替代料管理 (Substitute Materials)

替代料管理模块用于管理物料替代申请、审批流程。

### 证书状态说明

| 状态值 | 说明 |
|--------|------|
| `draft` | 草稿，可编辑、可删除 |
| `pending` | 待审批，等待管理员审批 |
| `approved` | 已通过，审批通过 |
| `rejected` | 已驳回，审批驳回 |

### 创建替代料申请

```http
POST /api/v1/substitute-materials
Content-Type: application/json
Authorization: Bearer <token>

{
  "original_product_code": "CPU-INTEL-I7-12700",
  "original_product_name": "Intel Core i7-12700 Processor",
  "original_specs": {
    "cores": 12,
    "threads": 20,
    "base_freq": "2.1 GHz",
    "max_freq": "4.9 GHz"
  },
  "substitute_product_code": "CPU-AMD-R7-5800X",
  "substitute_product_name": "AMD Ryzen 7 5800X Processor",
  "substitute_specs": {
    "cores": 8,
    "threads": 16,
    "base_freq": "3.8 GHz",
    "max_freq": "4.7 GHz"
  },
  "original_supplier_id": "supplier-id-001",
  "substitute_supplier_id": "supplier-id-002",
  "reason": "Intel 处理器供应短缺，需要寻找替代方案",
  "advantage": "AMD 处理器价格更低，性价比更高；供货周期更稳定",
  "risk_assessment": "性能略低于 Intel，但在大多数场景下可以满足需求；需要进行兼容性测试",
  "test_report": {
    "compatibility_test": "passed",
    "performance_test": "92% of original",
    "test_date": "2026-04-25"
  }
}
```

**响应：**

```json
{
  "id": "sub-mat-app-id-001",
  "application_no": "SMA-20260502-ABC123DE",
  "original_product_code": "CPU-INTEL-I7-12700",
  "original_product_name": "Intel Core i7-12700 Processor",
  "original_specs": {
    "cores": 12,
    "threads": 20,
    "base_freq": "2.1 GHz",
    "max_freq": "4.9 GHz"
  },
  "substitute_product_code": "CPU-AMD-R7-5800X",
  "substitute_product_name": "AMD Ryzen 7 5800X Processor",
  "substitute_specs": {
    "cores": 8,
    "threads": 16,
    "base_freq": "3.8 GHz",
    "max_freq": "4.7 GHz"
  },
  "original_supplier_id": "supplier-id-001",
  "substitute_supplier_id": "supplier-id-002",
  "reason": "Intel 处理器供应短缺，需要寻找替代方案",
  "advantage": "AMD 处理器价格更低，性价比更高；供货周期更稳定",
  "risk_assessment": "性能略低于 Intel，但在大多数场景下可以满足需求；需要进行兼容性测试",
  "test_report": {
    "compatibility_test": "passed",
    "performance_test": "92% of original",
    "test_date": "2026-04-25"
  },
  "status": "draft",
  "created_by": "user-id-001",
  "submitted_at": null,
  "approved_at": null,
  "rejected_at": null,
  "rejected_reason": null,
  "created_at": "2026-05-02T10:00:00",
  "updated_at": "2026-05-02T10:00:00"
}
```

### 查询替代料申请列表

```http
GET /api/v1/substitute-materials?status=pending&limit=20&offset=0
Authorization: Bearer <token>
```

**参数说明：**
- `status` (可选): 按状态过滤，可选值：`draft`, `pending`, `approved`, `rejected`
- `original_supplier_id` (可选): 原供应商 ID
- `substitute_supplier_id` (可选): 替代供应商 ID
- `created_by` (可选): 创建者 ID
- `search` (可选): 搜索关键词（申请单号、产品编码、产品名称）
- `limit` (可选): 返回数量限制，默认 50，最大 100
- `offset` (可选): 偏移量，默认 0

### 获取替代料申请详情

```http
GET /api/v1/substitute-materials/sub-mat-app-id-001
Authorization: Bearer <token>
```

**响应包含审批记录：**

```json
{
  "id": "sub-mat-app-id-001",
  "application_no": "SMA-20260502-ABC123DE",
  "status": "approved",
  "approval_records": [
    {
      "id": "approval-record-id-001",
      "application_id": "sub-mat-app-id-001",
      "approver_id": "admin-user-id",
      "approval_action": "approve",
      "comment": "测试报告完整，同意替代",
      "before_status": "pending",
      "after_status": "approved",
      "created_at": "2026-05-03T14:30:00"
    }
  ]
}
```

### 更新替代料申请

仅草稿状态可更新。

```http
PUT /api/v1/substitute-materials/sub-mat-app-id-001
Content-Type: application/json
Authorization: Bearer <token>

{
  "advantage": "AMD 处理器价格更低，性价比更高；供货周期更稳定；功耗更低",
  "risk_assessment": "经过充分测试，兼容性良好；性能可满足需求"
}
```

### 提交替代料申请

提交后状态变为 `pending`，等待审批。

```http
POST /api/v1/substitute-materials/sub-mat-app-id-001/submit
Authorization: Bearer <token>
```

**响应：**

```json
{
  "id": "sub-mat-app-id-001",
  "application_no": "SMA-20260502-ABC123DE",
  "original_product_code": "CPU-INTEL-I7-12700",
  "original_product_name": "Intel Core i7-12700 Processor",
  "substitute_product_code": "CPU-AMD-R7-5800X",
  "substitute_product_name": "AMD Ryzen 7 5800X Processor",
  "original_supplier_id": "supplier-id-001",
  "substitute_supplier_id": "supplier-id-002",
  "reason": "Intel 处理器供应短缺，需要寻找替代方案",
  "advantage": "AMD 处理器价格更低，性价比更高；供货周期更稳定",
  "risk_assessment": "性能略低于 Intel，但在大多数场景下可以满足需求",
  "status": "pending",
  "created_by": "user-id-001",
  "submitted_at": "2026-05-02T11:30:00",
  "approved_at": null,
  "rejected_at": null,
  "rejected_reason": null,
  "created_at": "2026-05-02T10:00:00",
  "updated_at": "2026-05-02T11:30:00"
}
```

### 审批通过替代料申请

需要管理员权限。

```http
POST /api/v1/substitute-materials/sub-mat-app-id-001/approve
Content-Type: application/json
Authorization: Bearer <token>

{
  "comment": "测试报告完整，性能评估合格，同意替代方案"
}
```

**响应：**

```json
{
  "id": "sub-mat-app-id-001",
  "application_no": "SMA-20260502-ABC123DE",
  "original_product_code": "CPU-INTEL-I7-12700",
  "original_product_name": "Intel Core i7-12700 Processor",
  "substitute_product_code": "CPU-AMD-R7-5800X",
  "substitute_product_name": "AMD Ryzen 7 5800X Processor",
  "original_supplier_id": "supplier-id-001",
  "substitute_supplier_id": "supplier-id-002",
  "reason": "Intel 处理器供应短缺，需要寻找替代方案",
  "advantage": "AMD 处理器价格更低，性价比更高；供货周期更稳定",
  "risk_assessment": "性能略低于 Intel，但在大多数场景下可以满足需求",
  "status": "approved",
  "created_by": "user-id-001",
  "submitted_at": "2026-05-02T11:30:00",
  "approved_at": "2026-05-03T14:30:00",
  "rejected_at": null,
  "rejected_reason": null,
  "created_at": "2026-05-02T10:00:00",
  "updated_at": "2026-05-03T14:30:00"
}
```

### 驳回替代料申请

需要管理员权限。

```http
POST /api/v1/substitute-materials/sub-mat-app-id-002/reject
Content-Type: application/json
Authorization: Bearer <token>

{
  "reason": "性能测试结果未达到预期标准，建议寻找性能更接近的替代产品"
}
```

**响应：**

```json
{
  "id": "sub-mat-app-id-002",
  "application_no": "SMA-20260502-XYZ789AB",
  "original_product_code": "RAM-DDR4-16GB",
  "original_product_name": "DDR4 16GB Desktop Memory",
  "substitute_product_code": "RAM-DDR4-8GB",
  "substitute_product_name": "DDR4 8GB Desktop Memory",
  "original_supplier_id": "supplier-id-001",
  "substitute_supplier_id": "supplier-id-003",
  "reason": "原厂内存供应延迟",
  "status": "rejected",
  "created_by": "user-id-002",
  "submitted_at": "2026-05-02T12:00:00",
  "approved_at": null,
  "rejected_at": "2026-05-03T15:00:00",
  "rejected_reason": "性能测试结果未达到预期标准，建议寻找性能更接近的替代产品",
  "created_at": "2026-05-02T11:00:00",
  "updated_at": "2026-05-03T15:00:00"
}
```

### 删除替代料申请

仅草稿状态可删除。

```http
DELETE /api/v1/substitute-materials/sub-mat-app-id-001
Authorization: Bearer <token>
```

---

## 供应商证书管理 (Supplier Certificates)

供应商证书管理模块用于管理供应商资质证书、有效期预警。

### 证书状态说明

| 状态值 | 说明 |
|--------|------|
| `valid` | 有效，有效期超过 30 天 |
| `expiring` | 即将过期，有效期不足 30 天 |
| `expired` | 已过期，当前日期超过有效期 |

### 证书类型说明

| 类型值 | 说明 |
|--------|------|
| `iso_9001` | ISO 9001 质量管理体系 |
| `iso_14001` | ISO 14001 环境管理体系 |
| `iso_45001` | ISO 45001 职业健康安全管理 |
| `iatf_16949` | IATF 16949 汽车行业质量管理 |
| `ce` | CE 认证（欧盟合格认证） |
| `rohs` | RoHS 认证（有害物质限制） |
| `reach` | REACH 认证（欧盟化学品注册） |
| `fda` | FDA 认证（美国食品药品管理局） |
| `ul` | UL 认证（美国安全检测实验室） |
| `ccc` | CCC 认证（中国强制认证） |
| `other` | 其他类型证书 |

### 录入供应商证书

```http
POST /api/v1/supplier-certificates
Content-Type: application/json
Authorization: Bearer <token>

{
  "supplier_id": "supplier-id-001",
  "certificate_type": "iso_9001",
  "certificate_no": "CN-2023-ISO-12345",
  "issuing_authority": "中国质量认证中心",
  "issue_date": "2023-06-15T00:00:00",
  "valid_from": "2023-06-15T00:00:00",
  "valid_until": "2026-06-14T23:59:59",
  "scope": "电子元器件的设计、生产和销售",
  "certificate_file": {
    "file_name": "ISO9001_Certificate.pdf",
    "file_path": "/certificates/supplier-001/ISO9001_Certificate.pdf",
    "file_size": 1048576
  },
  "notes": "证书有效期三年，需提前三个月申请续期",
  "extra": {
    "audit_date": "2026-03-15",
    "next_audit_due": "2026-06-01"
  }
}
```

**响应：**

```json
{
  "id": "cert-id-001",
  "supplier_id": "supplier-id-001",
  "certificate_type": "iso_9001",
  "certificate_no": "CN-2023-ISO-12345",
  "issuing_authority": "中国质量认证中心",
  "issue_date": "2023-06-15T00:00:00",
  "valid_from": "2023-06-15T00:00:00",
  "valid_until": "2026-06-14T23:59:59",
  "scope": "电子元器件的设计、生产和销售",
  "certificate_file": {
    "file_name": "ISO9001_Certificate.pdf",
    "file_path": "/certificates/supplier-001/ISO9001_Certificate.pdf",
    "file_size": 1048576
  },
  "status": "valid",
  "is_renewed": false,
  "renewed_from_id": null,
  "created_by": "user-id-001",
  "notes": "证书有效期三年，需提前三个月申请续期",
  "extra": {
    "audit_date": "2026-03-15",
    "next_audit_due": "2026-06-01"
  },
  "created_at": "2026-05-02T10:00:00",
  "updated_at": "2026-05-02T10:00:00"
}
```

### 查询供应商证书列表

```http
GET /api/v1/supplier-certificates?supplier_id=supplier-id-001&status=valid&limit=20&offset=0
Authorization: Bearer <token>
```

**参数说明：**
- `supplier_id` (可选): 按供应商 ID 过滤
- `certificate_type` (可选): 按证书类型过滤
- `status` (可选): 按状态过滤，可选值：`valid`, `expiring`, `expired`
- `search` (可选): 搜索关键词（证书编号、发证机构、范围）
- `created_by` (可选): 创建者 ID
- `limit` (可选): 返回数量限制，默认 50，最大 100
- `offset` (可选): 偏移量，默认 0

### 查询即将过期证书

按指定天数查询即将过期的证书。

```http
GET /api/v1/supplier-certificates/expiring?days=30&supplier_id=supplier-id-001
Authorization: Bearer <token>
```

**参数说明：**
- `days` (可选): 即将过期的天数，默认 30，范围 1-365
- `supplier_id` (可选): 按供应商 ID 过滤
- `limit` (可选): 返回数量限制，默认 50，最大 100
- `offset` (可选): 偏移量，默认 0

**响应示例：**

```json
{
  "total": 3,
  "items": [
    {
      "id": "cert-id-002",
      "supplier_id": "supplier-id-001",
      "certificate_type": "rohs",
      "certificate_no": "ROHS-2023-67890",
      "valid_from": "2023-08-20T00:00:00",
      "valid_until": "2026-05-20T23:59:59",
      "status": "expiring",
      "created_at": "2026-05-02T10:00:00",
      "updated_at": "2026-05-02T10:00:00"
    }
  ]
}
```

### 查询已过期证书

```http
GET /api/v1/supplier-certificates/expired?supplier_id=supplier-id-001
Authorization: Bearer <token>
```

### 获取证书统计

```http
GET /api/v1/supplier-certificates/statistics?supplier_id=supplier-id-001
Authorization: Bearer <token>
```

**响应示例：**

```json
{
  "total": 15,
  "by_status": {
    "valid": 10,
    "expiring": 3,
    "expired": 2
  },
  "by_type": [
    {
      "certificate_type": "iso_9001",
      "count": 5
    },
    {
      "certificate_type": "rohs",
      "count": 4
    },
    {
      "certificate_type": "ce",
      "count": 3
    }
  ]
}
```

### 获取供应商证书详情

```http
GET /api/v1/supplier-certificates/cert-id-001
Authorization: Bearer <token>
```

### 更新供应商证书

```http
PUT /api/v1/supplier-certificates/cert-id-001
Content-Type: application/json
Authorization: Bearer <token>

{
  "notes": "证书已完成年度审核，有效期至 2026-06-14",
  "extra": {
    "audit_date": "2026-04-20",
    "next_audit_due": "2026-06-01"
  }
}
```

### 删除供应商证书

```http
DELETE /api/v1/supplier-certificates/cert-id-001
Authorization: Bearer <token>
```

### 刷新单个证书状态

手动刷新证书状态（根据有效期自动计算）。

```http
GET /api/v1/supplier-certificates/cert-id-001/refresh-status
Authorization: Bearer <token>
```

### 刷新所有证书状态

需要管理员权限，批量刷新所有证书状态。

```http
POST /api/v1/supplier-certificates/refresh-status
Authorization: Bearer <token>
```

**响应：**

```json
{
  "updated_count": 5
}
```

### 查询证书预警列表

```http
GET /api/v1/supplier-certificates/alerts?is_read=false&limit=50
Authorization: Bearer <token>
```

**参数说明：**
- `certificate_id` (可选): 按证书 ID 过滤
- `is_read` (可选): 按已读状态过滤
- `alert_type` (可选): 按预警类型过滤
- `limit` (可选): 返回数量限制，默认 50，最大 100
- `offset` (可选): 偏移量，默认 0

### 标记预警已读/未读

```http
PATCH /api/v1/supplier-certificates/alerts/alert-id-001/read
Content-Type: application/json
Authorization: Bearer <token>

{
  "is_read": true
}
```

---

## 新增错误码（替代料和证书模块）

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `APPLICATION_NOT_FOUND` | 404 | 替代料申请不存在 |
| `ORIGINAL_SUPPLIER_NOT_FOUND` | 404 | 原供应商不存在 |
| `SUBSTITUTE_SUPPLIER_NOT_FOUND` | 404 | 替代供应商不存在 |
| `SUBMIT_FAILED` | 500 | 提交申请失败 |
| `APPROVE_FAILED` | 500 | 审批通过失败 |
| `REJECT_FAILED` | 500 | 驳回申请失败 |
| `CERTIFICATE_NOT_FOUND` | 404 | 证书不存在 |
| `CERTIFICATE_EXISTS` | 409 | 同一供应商、类型、编号的证书已存在 |
| `INVALID_DATE_RANGE` | 400 | 有效期结束日期必须晚于开始日期 |
| `REFRESH_FAILED` | 500 | 刷新证书状态失败 |
| `ALERT_NOT_FOUND` | 404 | 预警不存在 |
