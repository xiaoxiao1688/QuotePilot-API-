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
