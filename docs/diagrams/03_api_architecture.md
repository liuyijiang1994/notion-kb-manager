# API Architecture

## API Endpoint Overview

```mermaid
graph TB
    subgraph "API Gateway"
        Router[Flask Router]
        Auth[Auth Middleware]
        RateLimit[Rate Limiter]
        CORS[CORS Handler]
    end

    subgraph "Configuration APIs"
        ConfigAPI[/api/config/*]
        ModelAPI[/api/config/models/*]
        NotionConfigAPI[/api/config/notion/*]
        ParamsAPI[/api/config/parameters/*]
        PrefsAPI[/api/config/preferences/*]
    end

    subgraph "Link Management APIs"
        LinkAPI[/api/links/*]
        ImportAPI[/api/links/import/*]
        ValidateAPI[/api/links/validate]
    end

    subgraph "Processing APIs"
        ParseAPI[/api/parsing/*]
        AIAPI[/api/ai/*]
        ArxivAPI[/api/arxiv/*]
    end

    subgraph "Notion Integration APIs"
        NotionHierarchyAPI[/api/notion/hierarchy]
        NotionImportAPI[/api/notion/import/*]
        NotionSyncAPI[/api/notion/sync/*]
        MappingAPI[/api/notion/mapping/*]
    end

    subgraph "Management APIs"
        StatsAPI[/api/stats/*]
        HistoryAPI[/api/history/*]
        ContentAPI[/api/content/*]
        BackupAPI[/api/backup/*]
        LogsAPI[/api/logs/*]
        TaskAPI[/api/tasks/*]
    end

    subgraph "Utility APIs"
        HelpAPI[/api/help/*]
        FeedbackAPI[/api/feedback]
        VersionAPI[/api/version]
    end

    Router --> Auth
    Auth --> RateLimit
    RateLimit --> CORS

    CORS --> ConfigAPI
    CORS --> LinkAPI
    CORS --> ParseAPI
    CORS --> NotionHierarchyAPI
    CORS --> StatsAPI
    CORS --> HelpAPI

    style Router fill:#90caf9
    style Auth fill:#ffcc80
    style ConfigAPI fill:#a5d6a7
    style ParseAPI fill:#ce93d8
    style NotionHierarchyAPI fill:#fff59d
```

## Complete API Endpoints Specification

### Module I: Configuration APIs

#### Model Configuration

```
POST   /api/config/models
Description: Create or update AI model configuration
Request Body:
{
  "name": "GPT-4",
  "api_url": "https://api.openai.com/v1",
  "api_token": "sk-...",
  "timeout": 30,
  "max_tokens": 4096,
  "rate_limit": 60,
  "is_default": false
}
Response: 201 Created
{
  "success": true,
  "data": {
    "id": 1,
    "name": "GPT-4",
    "status": "pending_test",
    ...
  }
}

---

GET    /api/config/models
Description: Get all model configurations
Query Params: ?active_only=true
Response: 200 OK
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "GPT-4",
      "api_url": "https://api.openai.com/v1",
      "status": "online",
      "is_default": true,
      "is_active": true,
      "created_at": "2024-01-12T10:00:00Z"
    }
  ]
}

---

GET    /api/config/models/{id}
Description: Get specific model configuration
Response: 200 OK

---

PUT    /api/config/models/{id}
Description: Update model configuration
Request Body: (same as POST)

---

DELETE /api/config/models/{id}
Description: Delete model configuration
Response: 204 No Content

---

POST   /api/config/models/{id}/test
Description: Test model connection
Response: 200 OK
{
  "success": true,
  "data": {
    "status": "online",
    "latency_ms": 234,
    "message": "Connection successful"
  }
}

---

PUT    /api/config/models/{id}/default
Description: Set as default model
Response: 200 OK
```

#### Notion Configuration

```
POST   /api/config/notion
Description: Save Notion configuration
Request Body:
{
  "api_token": "secret_...",
  "workspace_id": "workspace-123"
}
Response: 201 Created

---

GET    /api/config/notion
Description: Get Notion configuration
Response: 200 OK
{
  "success": true,
  "data": {
    "workspace_id": "workspace-123",
    "workspace_name": "My Workspace",
    "status": "online",
    "last_tested_at": "2024-01-12T10:00:00Z"
  }
}

---

POST   /api/config/notion/test
Description: Test Notion connection
Response: 200 OK
{
  "success": true,
  "data": {
    "status": "online",
    "workspace_name": "My Workspace",
    "permissions": ["read", "write"]
  }
}

---

GET    /api/config/notion/workspaces
Description: Get workspace list
Response: 200 OK
{
  "success": true,
  "data": [
    {
      "id": "workspace-123",
      "name": "My Workspace"
    }
  ]
}
```

#### Tool Parameters

```
GET    /api/config/parameters
Description: Get all tool parameters
Response: 200 OK
{
  "success": true,
  "data": {
    "quality_threshold": 60,
    "render_timeout": 30,
    "ocr_language": "auto",
    "batch_size": 10,
    ...
  }
}

---

PUT    /api/config/parameters
Description: Update tool parameters
Request Body: (partial or full parameter object)

---

POST   /api/config/parameters/reset
Description: Reset to default parameters
Response: 200 OK
```

#### User Preferences

```
GET    /api/config/preferences
Description: Get user preferences
Response: 200 OK

---

PUT    /api/config/preferences
Description: Update preferences
Request Body:
{
  "theme": "dark",
  "font_size": "medium",
  "panel_layout": {...},
  "shortcuts": {...}
}
```

---

### Module II: Link Management APIs

#### Link Import

```
POST   /api/links/import/favorites
Description: Import links from favorites file
Request: multipart/form-data
{
  "file": <bookmark.html>
}
Response: 201 Created
{
  "success": true,
  "data": {
    "total_imported": 150,
    "links": [...],
    "duplicates": 5
  }
}

---

POST   /api/links/import/manual
Description: Manually import links
Request Body:
{
  "links": [
    {
      "url": "https://example.com",
      "title": "Example Site",
      "tags": ["tech", "blog"]
    }
  ]
}
Response: 201 Created

---

POST   /api/links/import/history/{task_id}
Description: Re-import from historical task
Response: 201 Created
```

#### Link Operations

```
GET    /api/links
Description: Get all links with filters
Query Params:
  ?source=favorites
  &is_valid=true
  &priority=high
  &tags=tech,blog
  &search=keyword
  &page=1
  &limit=20
  &sort_by=imported_at
  &order=desc
Response: 200 OK
{
  "success": true,
  "data": {
    "links": [...],
    "total": 150,
    "page": 1,
    "limit": 20
  }
}

---

GET    /api/links/{id}
Description: Get specific link details
Response: 200 OK

---

PUT    /api/links/{id}
Description: Update link
Request Body:
{
  "title": "Updated Title",
  "tags": ["new-tag"],
  "priority": "high",
  "notes": "Important article"
}

---

DELETE /api/links/{id}
Description: Delete link
Response: 204 No Content
```

#### Link Validation

```
POST   /api/links/validate
Description: Batch validate links
Request Body:
{
  "link_ids": [1, 2, 3, 4, 5]
}
Response: 202 Accepted
{
  "success": true,
  "data": {
    "task_id": "val-task-123",
    "total_links": 5
  }
}

---

GET    /api/links/validate/status/{task_id}
Description: Get validation progress
Response: 200 OK
{
  "success": true,
  "data": {
    "task_id": "val-task-123",
    "status": "running",
    "progress": 60,
    "completed": 3,
    "total": 5
  }
}
```

#### Batch Operations

```
PUT    /api/links/batch
Description: Batch update links
Request Body:
{
  "link_ids": [1, 2, 3],
  "updates": {
    "priority": "high",
    "tags": ["urgent"]
  }
}
Response: 200 OK

---

DELETE /api/links/batch
Description: Batch delete links
Request Body:
{
  "link_ids": [1, 2, 3]
}
Response: 204 No Content
```

#### Import Tasks

```
GET    /api/tasks/import
Description: Get all import tasks
Query Params: ?status=pending&page=1&limit=20
Response: 200 OK

---

POST   /api/tasks/import
Description: Create new import task
Request Body:
{
  "name": "Tech Articles - Jan 2024",
  "link_ids": [1, 2, 3, 4, 5],
  "config": {
    "auto_start": false
  }
}
Response: 201 Created

---

GET    /api/tasks/import/{id}
Description: Get task details

---

PUT    /api/tasks/import/{id}
Description: Update task

---

DELETE /api/tasks/import/{id}
Description: Delete task

---

POST   /api/tasks/import/{id}/start
Description: Start task execution
```

---

### Module III: Content Processing APIs

#### Parsing APIs

```
POST   /api/parsing/start
Description: Start parsing task
Request Body:
{
  "link_ids": [1, 2, 3],
  "config": {
    "threads": 4,
    "quality_threshold": 60,
    "enable_ocr": true
  }
}
Response: 202 Accepted
{
  "success": true,
  "data": {
    "task_id": "parse-task-456"
  }
}

---

GET    /api/parsing/status/{task_id}
Description: Get parsing progress
Response: 200 OK
{
  "success": true,
  "data": {
    "task_id": "parse-task-456",
    "status": "running",
    "progress": 45,
    "total_items": 10,
    "completed_items": 4,
    "failed_items": 1,
    "current_item": {
      "id": 5,
      "title": "Processing..."
    }
  }
}

---

POST   /api/parsing/pause/{task_id}
Description: Pause parsing task
Response: 200 OK

---

POST   /api/parsing/resume/{task_id}
Description: Resume parsing task
Response: 200 OK

---

POST   /api/parsing/retry
Description: Retry failed parsing items
Request Body:
{
  "content_ids": [1, 2, 3]
}
Response: 202 Accepted
```

#### Content APIs

```
GET    /api/content/{id}
Description: Get parsed content
Response: 200 OK
{
  "success": true,
  "data": {
    "id": 1,
    "link_id": 5,
    "raw_content": "...",
    "formatted_content": "...",
    "quality_score": 85,
    "parsing_method": "html",
    "images": [...],
    "tables": [...],
    "paper_info": {
      "title": "Research Paper Title",
      "authors": ["Author 1", "Author 2"],
      "year": 2024
    },
    "arxiv_id": "2401.12345",
    "status": "completed",
    "parsed_at": "2024-01-12T10:00:00Z"
  }
}

---

PUT    /api/content/{id}
Description: Update parsed content (manual optimization)
Request Body:
{
  "formatted_content": "Updated content...",
  "quality_score": 90
}
Response: 200 OK
```

#### AI Processing APIs

```
POST   /api/ai/process
Description: Start AI processing
Request Body:
{
  "content_ids": [1, 2, 3],
  "model_id": 1,
  "config": {
    "temperature": 0.7,
    "functions": [
      "summary",
      "chapter_summaries",
      "structured_content",
      "keywords",
      "insights"
    ],
    "summary_length": 300,
    "structure_framework": "problem-solution"
  }
}
Response: 202 Accepted
{
  "success": true,
  "data": {
    "task_id": "ai-task-789"
  }
}

---

GET    /api/ai/status/{task_id}
Description: Get AI processing progress
Response: 200 OK
{
  "success": true,
  "data": {
    "task_id": "ai-task-789",
    "status": "running",
    "progress": 33,
    "total_items": 3,
    "completed_items": 1,
    "tokens_used": 5000,
    "estimated_cost": 0.25
  }
}

---

POST   /api/ai/regenerate
Description: Regenerate AI content
Request Body:
{
  "content_id": 1,
  "model_id": 1,
  "instruction": "Make the summary more concise",
  "functions": ["summary"]
}
Response: 202 Accepted

---

GET    /api/ai/versions/{content_id}
Description: Get all AI processing versions
Response: 200 OK
{
  "success": true,
  "data": [
    {
      "id": 1,
      "version": 1,
      "is_active": false,
      "model_used": "GPT-4",
      "processed_at": "2024-01-12T10:00:00Z"
    },
    {
      "id": 2,
      "version": 2,
      "is_active": true,
      "model_used": "Claude 3",
      "processed_at": "2024-01-12T11:00:00Z"
    }
  ]
}

---

GET    /api/ai/content/{id}
Description: Get AI processed content
Response: 200 OK
{
  "success": true,
  "data": {
    "id": 1,
    "parsed_content_id": 1,
    "model_used": "GPT-4",
    "summary": "...",
    "chapter_summaries": [...],
    "structured_content": "...",
    "keywords": ["keyword1", "keyword2"],
    "secondary_content": "...",
    "insights": "...",
    "version": 2,
    "tokens_used": 3500,
    "cost": 0.15
  }
}

---

PUT    /api/ai/content/{id}
Description: Update AI content manually
Request Body: (partial update)

---

PUT    /api/ai/content/{id}/activate
Description: Set as active version
Response: 200 OK
```

#### arXiv APIs

```
POST   /api/arxiv/search
Description: Search arXiv by paper title
Request Body:
{
  "title": "Attention Is All You Need"
}
Response: 200 OK
{
  "success": true,
  "data": {
    "results": [
      {
        "arxiv_id": "1706.03762",
        "title": "Attention Is All You Need",
        "authors": ["Vaswani et al."],
        "published": "2017-06-12",
        "summary": "...",
        "pdf_url": "https://arxiv.org/pdf/1706.03762"
      }
    ]
  }
}

---

POST   /api/arxiv/download/{arxiv_id}
Description: Download PDF from arXiv
Response: 202 Accepted
{
  "success": true,
  "data": {
    "arxiv_id": "1706.03762",
    "download_task_id": "arxiv-dl-123",
    "status": "downloading"
  }
}

---

GET    /api/arxiv/download/status/{task_id}
Description: Get download status
Response: 200 OK
{
  "success": true,
  "data": {
    "task_id": "arxiv-dl-123",
    "status": "completed",
    "file_path": "/cache/arxiv/1706.03762.pdf",
    "size": 1234567
  }
}
```

---

### Module IV: Notion Integration APIs

#### Notion Hierarchy

```
GET    /api/notion/hierarchy
Description: Get Notion page hierarchy
Query Params: ?refresh=true
Response: 200 OK
{
  "success": true,
  "data": {
    "workspace_id": "workspace-123",
    "pages": [
      {
        "id": "page-1",
        "title": "Knowledge Base",
        "type": "page",
        "children": [
          {
            "id": "page-2",
            "title": "Technical Articles",
            "type": "database",
            "children": []
          }
        ]
      }
    ]
  }
}

---

POST   /api/notion/page
Description: Create new Notion page
Request Body:
{
  "parent_id": "page-1",
  "title": "New Subpage",
  "type": "page"
}
Response: 201 Created
{
  "success": true,
  "data": {
    "id": "page-3",
    "title": "New Subpage",
    "url": "https://notion.so/..."
  }
}

---

GET    /api/notion/databases
Description: Get all databases in workspace
Response: 200 OK
```

#### Field Mapping

```
POST   /api/notion/mapping
Description: Save field mapping configuration
Request Body:
{
  "name": "Tech Articles Mapping",
  "target_location": "database-123",
  "target_hierarchy": ["Knowledge Base", "Technical Articles"],
  "field_mappings": {
    "summary": "Abstract",
    "keywords": "Tags",
    "structured_content": "Content",
    "source_url": "Source Link"
  },
  "format_settings": {
    "image_mode": "upload",
    "code_block_format": "notion",
    "list_format": "preserve"
  }
}
Response: 201 Created

---

GET    /api/notion/mapping
Description: Get all saved mappings
Response: 200 OK

---

GET    /api/notion/mapping/{id}
Description: Get specific mapping

---

PUT    /api/notion/mapping/{id}
Description: Update mapping

---

DELETE /api/notion/mapping/{id}
Description: Delete mapping
```

#### Notion Import

```
POST   /api/notion/import
Description: Start import to Notion
Request Body:
{
  "content_ids": [1, 2, 3],
  "mapping_id": 1,
  "config": {
    "mode": "batch",
    "concurrency": 3,
    "schedule": null
  }
}
Response: 202 Accepted
{
  "success": true,
  "data": {
    "task_id": "notion-import-999"
  }
}

---

GET    /api/notion/import/status/{task_id}
Description: Get import progress
Response: 200 OK
{
  "success": true,
  "data": {
    "task_id": "notion-import-999",
    "status": "running",
    "progress": 66,
    "total_items": 3,
    "completed_items": 2,
    "failed_items": 0,
    "imported_pages": [
      {
        "content_id": 1,
        "notion_page_id": "page-123",
        "notion_url": "https://notion.so/..."
      }
    ]
  }
}

---

POST   /api/notion/import/pause/{task_id}
Description: Pause import

---

POST   /api/notion/import/resume/{task_id}
Description: Resume import

---

POST   /api/notion/import/retry
Description: Retry failed imports
Request Body:
{
  "import_ids": [1, 2, 3]
}
```

#### Notion Synchronization

```
POST   /api/notion/sync
Description: Start synchronization
Request Body:
{
  "direction": "local_to_notion",
  "content_ids": [1, 2, 3],
  "conflict_resolution": "keep_newer"
}
Response: 202 Accepted
{
  "success": true,
  "data": {
    "task_id": "sync-task-111"
  }
}

---

GET    /api/notion/sync/status/{task_id}
Description: Get sync progress
Response: 200 OK

---

GET    /api/notion/sync/compare
Description: Compare local and Notion content
Request Body:
{
  "content_ids": [1, 2, 3]
}
Response: 200 OK
{
  "success": true,
  "data": {
    "changes": [
      {
        "content_id": 1,
        "status": "modified_local",
        "local_updated": "2024-01-12T10:00:00Z",
        "notion_updated": "2024-01-11T15:00:00Z"
      }
    ]
  }
}
```

---

### Module V: Statistics and History APIs

#### Statistics

```
GET    /api/stats/overview
Description: Get overall statistics
Response: 200 OK
{
  "success": true,
  "data": {
    "total_links": 500,
    "total_parsed": 450,
    "total_ai_processed": 400,
    "total_imported": 380,
    "parsing_success_rate": 90.0,
    "import_success_rate": 95.0,
    "avg_parsing_time": 5.2,
    "avg_ai_time": 15.8,
    "avg_import_time": 2.1
  }
}

---

GET    /api/stats/details/{task_id}
Description: Get task-specific statistics
Response: 200 OK

---

GET    /api/stats/trends
Description: Get time-based trends
Query Params: ?period=week&metric=imports
Response: 200 OK
{
  "success": true,
  "data": {
    "period": "week",
    "metric": "imports",
    "data_points": [
      {"date": "2024-01-08", "value": 25},
      {"date": "2024-01-09", "value": 30},
      {"date": "2024-01-10", "value": 28}
    ]
  }
}

---

GET    /api/stats/quality
Description: Get quality metrics
Response: 200 OK
{
  "success": true,
  "data": {
    "avg_parsing_quality": 82.5,
    "avg_ai_satisfaction": 4.2,
    "format_consistency": 95.0,
    "quality_distribution": {
      "high": 65,
      "medium": 25,
      "low": 10
    }
  }
}

---

POST   /api/stats/export
Description: Export statistics report
Request Body:
{
  "format": "excel",
  "include_charts": true,
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-01-12"
  }
}
Response: 200 OK
{
  "success": true,
  "data": {
    "file_url": "/downloads/report-20240112.xlsx",
    "expires_at": "2024-01-13T10:00:00Z"
  }
}
```

#### History

```
GET    /api/history/tasks
Description: Get historical tasks
Query Params:
  ?type=import
  &status=completed
  &date_from=2024-01-01
  &date_to=2024-01-12
  &search=keyword
  &page=1
  &limit=20
Response: 200 OK
{
  "success": true,
  "data": {
    "tasks": [...],
    "total": 50,
    "page": 1
  }
}

---

GET    /api/history/tasks/{id}
Description: Get task full details
Response: 200 OK
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Tech Import - Jan",
    "type": "parsing",
    "status": "completed",
    "total_items": 10,
    "completed_items": 9,
    "failed_items": 1,
    "started_at": "2024-01-12T09:00:00Z",
    "completed_at": "2024-01-12T09:15:00Z",
    "items": [
      {
        "id": 1,
        "title": "Article 1",
        "status": "success",
        "duration": 5.2
      }
    ]
  }
}

---

POST   /api/history/tasks/{id}/rerun
Description: Re-execute historical task
Response: 202 Accepted

---

POST   /api/history/tasks/{id}/export
Description: Export task report
Request Body:
{
  "format": "pdf"
}
Response: 200 OK
```

#### Logs

```
GET    /api/logs
Description: Get operation logs
Query Params:
  ?level=error
  &module=parsing
  &date_from=2024-01-12
  &date_to=2024-01-12
  &search=keyword
  &page=1
  &limit=50
Response: 200 OK
{
  "success": true,
  "data": {
    "logs": [
      {
        "id": 1,
        "level": "error",
        "module": "parsing",
        "action": "parse_pdf",
        "message": "Failed to parse encrypted PDF",
        "created_at": "2024-01-12T10:00:00Z"
      }
    ],
    "total": 100
  }
}

---

DELETE /api/logs/clean
Description: Clean old logs
Query Params: ?older_than_days=30
Response: 200 OK

---

POST   /api/logs/export
Description: Export logs
Request Body:
{
  "format": "csv",
  "filters": {...}
}
Response: 200 OK
```

---

### Module VI: Content Management APIs

#### Local Content

```
GET    /api/content/local
Description: Get all local content
Query Params:
  ?status=to_import
  &tags=tech
  &quality_min=70
  &search=keyword
  &sort_by=quality_score
  &order=desc
  &page=1
  &limit=20
Response: 200 OK
{
  "success": true,
  "data": {
    "contents": [
      {
        "id": 1,
        "title": "Article Title",
        "source_url": "https://...",
        "status": "to_import",
        "quality_score": 85,
        "processed_at": "2024-01-12T10:00:00Z",
        "tags": ["tech", "ai"]
      }
    ],
    "total": 50
  }
}

---

GET    /api/content/local/{id}
Description: Get content full details
Response: 200 OK

---

PUT    /api/content/local/{id}
Description: Update local content
Request Body: (partial update)

---

DELETE /api/content/local/batch
Description: Batch delete content
Request Body:
{
  "content_ids": [1, 2, 3]
}

---

POST   /api/content/reparse
Description: Batch reparse content
Request Body:
{
  "content_ids": [1, 2, 3]
}
Response: 202 Accepted

---

POST   /api/content/regenerate
Description: Batch regenerate AI content
Request Body:
{
  "content_ids": [1, 2, 3],
  "model_id": 1
}
Response: 202 Accepted
```

#### Backup

```
POST   /api/backup/create
Description: Create manual backup
Request Body:
{
  "name": "Manual Backup Jan 12",
  "include_cache": true,
  "include_uploads": true
}
Response: 202 Accepted
{
  "success": true,
  "data": {
    "backup_id": 1,
    "status": "creating"
  }
}

---

GET    /api/backup/list
Description: List all backups
Response: 200 OK
{
  "success": true,
  "data": [
    {
      "id": 1,
      "filename": "backup-20240112-100000.zip",
      "type": "manual",
      "size": 10485760,
      "created_at": "2024-01-12T10:00:00Z",
      "expires_at": "2024-02-12T10:00:00Z"
    }
  ]
}

---

POST   /api/backup/restore
Description: Restore from backup
Request Body:
{
  "backup_id": 1,
  "mode": "incremental"
}
Response: 202 Accepted

---

DELETE /api/backup/{id}
Description: Delete backup
Response: 204 No Content

---

POST   /api/backup/schedule
Description: Configure auto backup schedule
Request Body:
{
  "enabled": true,
  "frequency": "daily",
  "time": "02:00",
  "retention_days": 30
}
Response: 200 OK

---

GET    /api/backup/schedule
Description: Get backup schedule config
Response: 200 OK
```

---

### Module VII: Task Management APIs

#### Pending Tasks

```
GET    /api/tasks/pending
Description: Get all pending tasks
Response: 200 OK
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Tech Articles Processing",
      "type": "import",
      "status": "pending",
      "total_links": 20,
      "progress": 0,
      "created_at": "2024-01-12T09:00:00Z"
    }
  ]
}

---

GET    /api/tasks/pending/{id}
Description: Get task details

---

PUT    /api/tasks/pending/{id}
Description: Edit pending task
Request Body:
{
  "name": "Updated Task Name",
  "config": {...}
}

---

POST   /api/tasks/pending/{id}/start
Description: Start pending task
Response: 202 Accepted

---

DELETE /api/tasks/pending/{id}
Description: Delete pending task
Response: 204 No Content
```

#### Task Operations

```
GET    /api/tasks/{id}/progress
Description: Get real-time task progress
Response: 200 OK (Server-Sent Events also available)

---

POST   /api/tasks/{id}/pause
Description: Pause running task

---

POST   /api/tasks/{id}/resume
Description: Resume paused task

---

POST   /api/tasks/{id}/cancel
Description: Cancel task
```

---

### Utility APIs

#### Help and Support

```
GET    /api/help/guides
Description: Get user guides
Response: 200 OK
{
  "success": true,
  "data": {
    "guides": [
      {
        "id": "getting-started",
        "title": "Getting Started",
        "content": "...",
        "steps": [...]
      }
    ]
  }
}

---

GET    /api/help/faq
Description: Get FAQ
Query Params: ?category=configuration&search=notion
Response: 200 OK
{
  "success": true,
  "data": {
    "categories": [
      {
        "name": "Configuration",
        "questions": [
          {
            "question": "How to get Notion API token?",
            "answer": "..."
          }
        ]
      }
    ]
  }
}

---

POST   /api/feedback
Description: Submit user feedback
Request: multipart/form-data
{
  "type": "bug",
  "content": "Description...",
  "screenshot": <file>,
  "email": "user@example.com"
}
Response: 201 Created

---

GET    /api/version
Description: Get current version and check updates
Response: 200 OK
{
  "success": true,
  "data": {
    "current_version": "1.0.0",
    "latest_version": "1.1.0",
    "update_available": true,
    "release_notes": "..."
  }
}
```

---

## WebSocket Events

### Connection

```javascript
// Client connects
socket = io('https://api.example.com', {
  auth: {
    token: 'jwt-token'
  }
});

// Connection events
socket.on('connect', () => {});
socket.on('disconnect', () => {});
socket.on('error', (error) => {});
```

### Task Subscription

```javascript
// Subscribe to task updates
socket.emit('subscribe_task', {
  task_id: 'parse-task-456'
});

// Unsubscribe
socket.emit('unsubscribe_task', {
  task_id: 'parse-task-456'
});

// Receive updates
socket.on('task_progress', (data) => {
  // data = {
  //   task_id: 'parse-task-456',
  //   progress: 45,
  //   status: 'running',
  //   current_item: {...}
  // }
});

socket.on('task_completed', (data) => {
  // data = {
  //   task_id: 'parse-task-456',
  //   status: 'completed',
  //   result: {...}
  // }
});

socket.on('task_failed', (data) => {
  // data = {
  //   task_id: 'parse-task-456',
  //   status: 'failed',
  //   error: {...}
  // }
});
```

### General Notifications

```javascript
socket.on('notification', (data) => {
  // data = {
  //   type: 'success|info|warning|error',
  //   title: 'Notification title',
  //   message: 'Notification message',
  //   timestamp: '2024-01-12T10:00:00Z'
  // }
});
```

### Real-time Updates

```javascript
// Link validation update
socket.on('link_validated', (data) => {
  // data = {
  //   link_id: 1,
  //   is_valid: true,
  //   status: 200
  // }
});

// Content parsed
socket.on('content_parsed', (data) => {
  // data = {
  //   content_id: 1,
  //   quality_score: 85,
  //   status: 'completed'
  // }
});

// AI processing complete
socket.on('ai_processed', (data) => {
  // data = {
  //   ai_content_id: 1,
  //   tokens_used: 3500
  // }
});

// Import to Notion complete
socket.on('notion_imported', (data) => {
  // data = {
  //   import_id: 1,
  //   notion_url: 'https://...'
  // }
});
```

---

## API Response Standards

### Success Response

```json
{
  "success": true,
  "data": { },
  "message": "Optional success message",
  "timestamp": "2024-01-12T10:00:00Z"
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { }
  },
  "timestamp": "2024-01-12T10:00:00Z"
}
```

### Pagination Response

```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "total": 100,
      "page": 1,
      "limit": 20,
      "total_pages": 5
    }
  }
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| AUTH_001 | Authentication failed |
| AUTH_002 | Token expired |
| AUTH_003 | Insufficient permissions |
| VAL_001 | Validation error |
| VAL_002 | Invalid input format |
| RES_001 | Resource not found |
| RES_002 | Resource already exists |
| EXT_001 | External API error (Notion) |
| EXT_002 | External API error (AI Model) |
| EXT_003 | External API error (arXiv) |
| SYS_001 | Internal server error |
| SYS_002 | Database error |
| RATE_001 | Rate limit exceeded |

---

## Rate Limiting

```
Rate Limit Headers:
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1673524800

Response when exceeded:
HTTP 429 Too Many Requests
{
  "success": false,
  "error": {
    "code": "RATE_001",
    "message": "Rate limit exceeded",
    "retry_after": 60
  }
}
```

---

## Authentication

### JWT Token

```
Authorization: Bearer <jwt-token>

Token Payload:
{
  "user_id": "user-123",
  "exp": 1673524800,
  "iat": 1673521200
}
```

### API Key (Alternative)

```
X-API-Key: <api-key>
```
