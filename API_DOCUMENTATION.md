# API Documentation - Notion KB Manager

## Base URL
```
http://localhost:5000/api
```

## Response Format

All API responses follow a standardized format:

**Success Response:**
```json
{
  "success": true,
  "timestamp": "2026-01-13T03:23:53.626Z",
  "data": { ... },
  "message": "Operation successful"
}
```

**Error Response:**
```json
{
  "success": false,
  "timestamp": "2026-01-13T03:23:53.626Z",
  "error": {
    "code": "VAL_001",
    "message": "Validation error message"
  }
}
```

---

## Configuration Endpoints

### Model Configuration

#### List All Models
```http
GET /api/config/models?active_only=false
```

**Query Parameters:**
- `active_only` (boolean, optional): Only return active models

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "doubao-seed-1-6-251015",
      "api_url": "https://ark.cn-beijing.volces.com/api/v3/",
      "max_tokens": 4096,
      "timeout": 30,
      "rate_limit": 60,
      "is_default": false,
      "is_active": true,
      "status": "active",
      "created_at": "2026-01-13T03:23:53.626Z",
      "updated_at": "2026-01-13T03:24:47.122Z"
    }
  ]
}
```

#### Get Specific Model
```http
GET /api/config/models/{model_id}
```

#### Create Model Configuration
```http
POST /api/config/models
Content-Type: application/json

{
  "name": "doubao-seed-1-6-251015",
  "api_url": "https://ark.cn-beijing.volces.com/api/v3/",
  "api_token": "your-api-token",
  "max_tokens": 4096,
  "timeout": 30,
  "rate_limit": 60,
  "is_default": false
}
```

**Required Fields:**
- `name` (string): Model name/identifier
- `api_url` (string): API endpoint URL
- `api_token` (string): API authentication token
- `max_tokens` (integer): Maximum tokens per request (1-1000000)

**Optional Fields:**
- `timeout` (integer): Request timeout in seconds (1-300, default: 30)
- `rate_limit` (integer): Requests per minute (1-10000, default: 60)
- `is_default` (boolean): Set as default model (default: false)

#### Update Model Configuration
```http
PUT /api/config/models/{model_id}
Content-Type: application/json

{
  "max_tokens": 8192,
  "is_active": true
}
```

#### Delete Model Configuration
```http
DELETE /api/config/models/{model_id}
```

**Note:** Cannot delete the default model.

#### Set Default Model
```http
PUT /api/config/models/{model_id}/set-default
```

#### Test Model Connection
```http
POST /api/config/models/{model_id}/test
```

**Response:**
```json
{
  "success": true,
  "data": {
    "success": true,
    "latency_ms": 3182,
    "model_info": {
      "model": "doubao-seed-1-6-251015",
      "response": "OK",
      "usage": {
        "completion_tokens": 30,
        "prompt_tokens": 46,
        "total_tokens": 76
      },
      "finish_reason": "stop"
    },
    "message": "Connection successful. Response time: 3182ms"
  }
}
```

---

### Notion Configuration

#### Get Notion Configuration
```http
GET /api/config/notion
```

#### Create/Update Notion Configuration
```http
POST /api/config/notion
Content-Type: application/json

{
  "api_token": "ntn_your_notion_token",
  "workspace_id": "optional-workspace-id",
  "workspace_name": "optional-workspace-name"
}
```

**Required Fields:**
- `api_token` (string): Notion integration token

#### Test Notion Connection
```http
POST /api/config/notion/test
```

**Response:**
```json
{
  "success": true,
  "data": {
    "success": true,
    "workspace_info": {
      "bot_id": "a6e2451e-ff88-4ea2-8e2f-cf992382bdff",
      "bot_name": "KB Manager",
      "workspace_name": "宜江 柳's Notion",
      "bot_type": "bot",
      "owner": { ... }
    },
    "databases_count": 0,
    "databases": [],
    "message": "Connected successfully. Found 0 accessible databases."
  }
}
```

---

### Tool Parameters

#### Get Tool Parameters
```http
GET /api/config/parameters
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "quality_threshold": 60,
    "render_timeout": 30,
    "ocr_language": "auto",
    "batch_size": 10,
    "retain_cache": true,
    "export_format": "excel",
    "cache_retention_days": 7,
    "cache_auto_clean": true,
    "enable_notifications": true,
    "notification_frequency": "all",
    "updated_at": "2026-01-13T03:23:53.626Z"
  }
}
```

#### Update Tool Parameters
```http
PUT /api/config/parameters
Content-Type: application/json

{
  "quality_threshold": 80,
  "batch_size": 20,
  "export_format": "csv"
}
```

**Validation Rules:**
- `quality_threshold`: 0-100
- `render_timeout`: 1-300 seconds
- `batch_size`: 1-1000
- `cache_retention_days`: 1-365
- `export_format`: `excel`, `csv`, or `json`
- `notification_frequency`: `all`, `errors`, or `none`

#### Reset Tool Parameters
```http
POST /api/config/parameters/reset
```

Resets all parameters to default values.

---

### User Preferences

#### Get User Preferences
```http
GET /api/config/preferences
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "theme": "system",
    "font_size": "14",
    "panel_layout": "vertical",
    "shortcuts": null,
    "updated_at": "2026-01-13T03:23:53.626Z"
  }
}
```

#### Update User Preferences
```http
PUT /api/config/preferences
Content-Type: application/json

{
  "theme": "dark",
  "font_size": "16",
  "panel_layout": "horizontal"
}
```

**Allowed Values:**
- `theme`: `light`, `dark`, or `system`
- `panel_layout`: `vertical`, `horizontal`, or `grid`

---

## Health Check Endpoints

#### API Ping
```http
GET /api/ping
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "pong"
  },
  "timestamp": "2026-01-13T03:23:53.626Z"
}
```

#### Application Health
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy"
}
```

#### Application Info
```http
GET /
```

**Response:**
```json
{
  "name": "Notion KB Manager",
  "version": "1.0.0",
  "status": "running"
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `VAL_001` | Validation error - Invalid input data |
| `RES_001` | Resource not found |
| `RES_002` | Resource already exists |
| `REQ_001` | Method not allowed |
| `EXT_001` | External API error |
| `SYS_001` | Internal server error |
| `SYS_002` | Database error |

---

## Example Usage with curl

### Create VolcEngine Model
```bash
curl -X POST http://localhost:5000/api/config/models \
  -H "Content-Type: application/json" \
  -d '{
    "name": "doubao-seed-1-6-251015",
    "api_url": "https://ark.cn-beijing.volces.com/api/v3/",
    "api_token": "your-api-token",
    "max_tokens": 4096,
    "timeout": 30,
    "rate_limit": 60
  }'
```

### Test Model Connection
```bash
curl -X POST http://localhost:5000/api/config/models/1/test
```

### Create Notion Configuration
```bash
curl -X POST http://localhost:5000/api/config/notion \
  -H "Content-Type: application/json" \
  -d '{
    "api_token": "ntn_your_notion_token"
  }'
```

### Test Notion Connection
```bash
curl -X POST http://localhost:5000/api/config/notion/test
```

### Update Tool Parameters
```bash
curl -X PUT http://localhost:5000/api/config/parameters \
  -H "Content-Type: application/json" \
  -d '{
    "quality_threshold": 80,
    "batch_size": 20
  }'
```

---

## Testing

Run the test script to verify API connections:

```bash
python3 test_real_apis.py
```

This will:
1. Create/update VolcEngine model configuration
2. Test VolcEngine API connection
3. Create/update Notion configuration
4. Test Notion API connection
5. Display connection results

---

## Next Steps

Phase 2 will implement:
- Link import functionality
- Web scraping and file upload
- Import task management
- Batch processing
- Progress tracking

For questions or issues, see the main README.md.
