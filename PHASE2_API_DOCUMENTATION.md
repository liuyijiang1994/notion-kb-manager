# Phase 2 API Documentation - Link Import and Task Management

## Base URL
```
http://localhost:5000/api
```

## Link Import Endpoints

### Import from Favorites
```http
POST /api/links/import/favorites
Content-Type: application/json

{
  "file_content": "<HTML>...",
  "file_type": "html",
  "task_name": "Optional task name"
}
```

**Parameters:**
- `file_content` (required): Bookmarks file content as string
- `file_type` (required): "html" or "json"
- `task_id` (optional): Existing task ID to associate links with
- `task_name` (optional): Create new task with this name

**Response:**
```json
{
  "success": true,
  "timestamp": "2026-01-13T12:00:00Z",
  "data": {
    "task_id": 1,
    "total": 10,
    "imported": 8,
    "duplicates": 2,
    "failed": 0
  },
  "message": "Imported 8 links from favorites"
}
```

---

### Import Manual Links
```http
POST /api/links/import/manual
Content-Type: application/json

{
  "text": "https://example.com\nhttps://google.com",
  "task_name": "My Links"
}
```

**Parameters:**
- `text` (required): Text containing URLs (one per line or space-separated)
- `task_id` (optional): Existing task ID
- `task_name` (optional): Create new task with this name

**Response:**
```json
{
  "success": true,
  "data": {
    "task_id": 1,
    "total": 2,
    "imported": 2,
    "duplicates": 0
  },
  "message": "Imported 2 links manually"
}
```

---

## Link Management Endpoints

### List All Links
```http
GET /api/links?source=manual&is_valid=true&limit=100&offset=0
```

**Query Parameters:**
- `source`: Filter by source (favorites/manual/history)
- `is_valid`: Filter by validation status (true/false)
- `task_id`: Filter by task ID
- `limit`: Results per page (default: 100)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 50,
    "limit": 100,
    "offset": 0,
    "links": [
      {
        "id": 1,
        "title": "Example Site",
        "url": "https://example.com",
        "source": "manual",
        "is_valid": true,
        "validation_status": "valid",
        "priority": "medium",
        "tags": ["tag1", "tag2"],
        "imported_at": "2026-01-13T12:00:00Z",
        "task_id": 1
      }
    ]
  }
}
```

---

### Get Single Link
```http
GET /api/links/{link_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Example Site",
    "url": "https://example.com",
    "source": "manual",
    "is_valid": true,
    "validation_status": "valid",
    "validation_time": "2026-01-13T12:00:00Z",
    "priority": "medium",
    "tags": ["tag1"],
    "notes": "Important site",
    "imported_at": "2026-01-13T12:00:00Z",
    "task_id": 1
  }
}
```

---

### Update Link
```http
PUT /api/links/{link_id}
Content-Type: application/json

{
  "title": "Updated Title",
  "priority": "high",
  "tags": ["important", "urgent"],
  "notes": "Updated notes"
}
```

**Parameters:**
- `title` (optional): New title
- `priority` (optional): low/medium/high
- `tags` (optional): Array of tags
- `notes` (optional): Notes text

---

### Delete Link
```http
DELETE /api/links/{link_id}
```

---

### Batch Delete Links
```http
DELETE /api/links/batch
Content-Type: application/json

{
  "link_ids": [1, 2, 3, 4, 5]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "deleted": 5
  },
  "message": "Deleted 5 links"
}
```

---

## Link Validation Endpoints

### Validate Links (Batch)
```http
POST /api/links/validate
Content-Type: application/json

{
  "link_ids": [1, 2, 3]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 3,
    "valid": 2,
    "invalid": 0,
    "errors": 1,
    "results": [
      {
        "link_id": 1,
        "url": "https://example.com",
        "is_valid": true,
        "status_code": 200,
        "status": "valid",
        "message": "URL is accessible",
        "response_time": 0.523
      },
      {
        "link_id": 2,
        "url": "https://google.com",
        "is_valid": true,
        "status_code": 200,
        "status": "valid",
        "response_time": 0.312
      },
      {
        "link_id": 3,
        "url": "https://invalid-url.test",
        "is_valid": false,
        "status": "connection_error",
        "message": "Connection failed"
      }
    ]
  },
  "message": "Validated 3 links"
}
```

---

### Validate Pending Links
```http
POST /api/links/validate/pending
Content-Type: application/json

{
  "limit": 50
}
```

Validates all links that haven't been validated yet.

---

### Get Link Statistics
```http
GET /api/links/statistics
```

**Response:**
```json
{
  "success": true,
  "data": {
    "import": {
      "total_links": 100,
      "by_source": {
        "manual": 50,
        "favorites": 40,
        "history": 10
      },
      "valid": 80,
      "invalid": 15,
      "pending_validation": 5
    },
    "validation": {
      "total": 100,
      "valid": 80,
      "invalid": 15,
      "pending": 5,
      "by_status": {
        "valid": 80,
        "not_found": 10,
        "connection_error": 5
      }
    }
  }
}
```

---

## Task Management Endpoints

### List Import Tasks
```http
GET /api/tasks/import?status=completed&limit=10
```

**Query Parameters:**
- `status`: Filter by status (pending/running/completed/failed)
- `limit`: Maximum number of results

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 5,
    "tasks": [
      {
        "id": 1,
        "name": "January Favorites",
        "status": "completed",
        "total_links": 50,
        "processed_links": 50,
        "config": {},
        "created_at": "2026-01-13T10:00:00Z",
        "started_at": "2026-01-13T10:01:00Z",
        "completed_at": "2026-01-13T10:05:00Z"
      }
    ]
  }
}
```

---

### Create Import Task
```http
POST /api/tasks/import
Content-Type: application/json

{
  "name": "New Import Task",
  "config": {
    "scope": "all",
    "validation": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "New Import Task",
    "status": "pending",
    "created_at": "2026-01-13T12:00:00Z"
  },
  "message": "Import task created successfully"
}
```

---

### Get Task Details
```http
GET /api/tasks/import/{task_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "January Favorites",
    "status": "completed",
    "total_links": 50,
    "processed_links": 50,
    "config": {},
    "created_at": "2026-01-13T10:00:00Z",
    "started_at": "2026-01-13T10:01:00Z",
    "completed_at": "2026-01-13T10:05:00Z",
    "link_statistics": {
      "total": 50,
      "valid": 45,
      "invalid": 3,
      "pending_validation": 2
    }
  }
}
```

---

### Start Task
```http
POST /api/tasks/import/{task_id}/start
```

Starts a pending task.

---

### Delete Task
```http
DELETE /api/tasks/import/{task_id}?delete_links=false
```

**Query Parameters:**
- `delete_links`: Whether to delete associated links (default: false)

---

### Get Task Statistics
```http
GET /api/tasks/statistics
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 10,
    "pending": 2,
    "running": 1,
    "completed": 6,
    "failed": 1
  }
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `IMP_001` | Import error |
| `VAL_001` | Validation error |
| `RES_001` | Resource not found |
| `SYS_001` | System error |

---

## Example Usage

### Import Favorites and Validate
```bash
# Step 1: Import bookmarks
curl -X POST http://localhost:5000/api/links/import/favorites \
  -H "Content-Type: application/json" \
  -d '{
    "file_content": "<HTML>...",
    "file_type": "html",
    "task_name": "January Bookmarks"
  }'

# Step 2: Get all links from the task
curl http://localhost:5000/api/links?task_id=1

# Step 3: Validate all pending links
curl -X POST http://localhost:5000/api/links/validate/pending \
  -H "Content-Type: application/json" \
  -d '{"limit": 100}'

# Step 4: Get statistics
curl http://localhost:5000/api/links/statistics
```

### Manual Import Flow
```bash
# Import URLs
curl -X POST http://localhost:5000/api/links/import/manual \
  -H "Content-Type: application/json" \
  -d '{
    "text": "https://example.com\nhttps://google.com\nhttps://github.com",
    "task_name": "Quick Links"
  }'

# Validate the imported links
curl -X POST http://localhost:5000/api/links/validate \
  -H "Content-Type: application/json" \
  -d '{"link_ids": [1, 2, 3]}'
```

---

## Phase 2 Features Summary

**Implemented:**
- ✅ Link import from browser favorites (HTML/JSON)
- ✅ Manual URL import from text
- ✅ Duplicate detection
- ✅ Batch link validation (concurrent)
- ✅ Link management (CRUD operations)
- ✅ Task tracking for import operations
- ✅ Import/validation statistics
- ✅ Link filtering and pagination

**Services:**
- `LinkImportService` - Import from various sources
- `LinkValidationService` - Batch URL validation with threading
- `TaskService` - Import task management

**Database Models:**
- `Link` - Imported links with metadata
- `ImportTask` - Task tracking

**Test Coverage:**
- 59 new tests for Phase 2
- 114/141 tests passing (81%)
- Service and API endpoint coverage

---

## Next Steps: Phase 3

Upcoming features:
- Web scraping for content extraction
- HTML-to-Markdown conversion
- Image and table extraction
- Content quality scoring
- AI-powered content processing
