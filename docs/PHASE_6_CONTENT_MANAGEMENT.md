# Phase 6: Content Management and Auxiliary Tools

## Overview

Phase 6 implements comprehensive content management features and auxiliary tools for system maintenance, monitoring, and user support.

**Key Features:**
- Content management with search and filtering
- Database backup and restore
- Operation log management
- User feedback system
- Built-in help documentation

---

## Architecture

### Services Layer

```
app/services/
├── content_management_service.py  # Content CRUD operations
├── backup_service.py              # Backup/restore functionality
├── log_service.py                 # Operation log management
└── feedback_service.py            # Feedback and help services
```

### API Layer

```
app/api/
├── content_management_routes.py   # Content management endpoints
├── backup_routes.py               # Backup/restore endpoints
├── log_routes.py                  # Log management endpoints
└── help_routes.py                 # Help and feedback endpoints
```

### Data Models

```
app/models/system.py:
- Backup: Backup metadata
- BackupFiles: Individual files in backup
- OperationLog: System operation logs
- Feedback: User feedback submissions
```

---

## Features

### 1. Content Management

Manage all parsed and AI-processed content in the local database.

#### Endpoints

**GET /api/content/local**
- List all content with pagination
- Filter by status (parsed/ai_processed/imported)
- Search in title and content
- Sort by parsed_at, quality_score, title

**GET /api/content/local/{id}**
- Get detailed content information
- Includes parsed content, AI versions, and Notion imports

**PUT /api/content/local/{id}**
- Update formatted content, summary, keywords, insights

**DELETE /api/content/local/batch**
- Batch delete content by IDs
- Cascades to AI content and Notion imports

**POST /api/content/reparse**
- Queue content for reparsing
- Creates async background task

**POST /api/content/regenerate**
- Queue content for AI regeneration
- Optionally specify model and processing config

**GET /api/content/statistics**
- Get content statistics
- Breakdown by type, status, quality score

#### Example Usage

```bash
# List all content
curl "http://localhost:5000/api/content/local?page=1&per_page=20"

# Search for content
curl "http://localhost:5000/api/content/local?search=python"

# Filter by status
curl "http://localhost:5000/api/content/local?status=ai_processed"

# Get content details
curl "http://localhost:5000/api/content/local/123"

# Update content
curl -X PUT "http://localhost:5000/api/content/local/123" \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "Updated summary",
    "keywords": ["new", "keywords"]
  }'

# Batch delete
curl -X DELETE "http://localhost:5000/api/content/local/batch" \
  -H "Content-Type: application/json" \
  -d '{"content_ids": [1, 2, 3]}'

# Queue for reparsing
curl -X POST "http://localhost:5000/api/content/reparse" \
  -H "Content-Type: application/json" \
  -d '{"content_ids": [1, 2, 3]}'

# Queue for AI regeneration
curl -X POST "http://localhost:5000/api/content/regenerate" \
  -H "Content-Type: application/json" \
  -d '{
    "content_ids": [1, 2, 3],
    "model_id": 1,
    "processing_config": {
      "generate_summary": true,
      "generate_keywords": true
    }
  }'
```

---

### 2. Backup and Restore

Create, manage, and restore from backups of database and application files.

#### Endpoints

**POST /api/backup/**
- Create new backup
- Options: include_database, include_files, retention_days
- Returns backup ID and file info

**GET /api/backup/**
- List all backups with pagination
- Filter by type (manual/auto)

**GET /api/backup/{id}**
- Get detailed backup information
- Shows file breakdown by type

**GET /api/backup/{id}/download**
- Download backup ZIP file

**POST /api/backup/{id}/restore**
- Restore from backup
- Options: restore_database, restore_files
- Creates backup of current database first

**DELETE /api/backup/{id}**
- Delete backup and optionally physical file

**POST /api/backup/cleanup**
- Cleanup expired backups

**GET /api/backup/statistics**
- Get backup statistics

#### Backup Structure

```
backup_manual_20260113_143000.zip
├── database/
│   └── notion_kb.db
├── instance/
│   └── [instance files]
├── logs/
│   └── [log files]
└── uploads/
    └── [uploaded files]
```

#### Example Usage

```bash
# Create backup
curl -X POST "http://localhost:5000/api/backup/" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "manual",
    "include_database": true,
    "include_files": true,
    "retention_days": 30
  }'

# List backups
curl "http://localhost:5000/api/backup/?page=1&per_page=10"

# Get backup details
curl "http://localhost:5000/api/backup/1"

# Download backup
curl "http://localhost:5000/api/backup/1/download" -O

# Restore from backup
curl -X POST "http://localhost:5000/api/backup/1/restore" \
  -H "Content-Type: application/json" \
  -d '{
    "restore_database": true,
    "restore_files": true
  }'

# Delete backup
curl -X DELETE "http://localhost:5000/api/backup/1?delete_file=true"

# Cleanup expired backups
curl -X POST "http://localhost:5000/api/backup/cleanup"
```

#### Environment Configuration

```bash
# .env
BACKUP_DIR=backups
DATABASE_PATH=instance/notion_kb.db
```

---

### 3. Log Management

Query, filter, and export operation logs.

#### Endpoints

**GET /api/logs/**
- Get logs with filtering
- Filter by level (info/warning/error), module, date range
- Search in action and message
- Pagination support

**GET /api/logs/statistics**
- Get log statistics for recent days
- Breakdown by level and module
- Recent errors list

**GET /api/logs/export**
- Export logs to JSON
- Filter by level, module, date range

**POST /api/logs/cleanup**
- Delete logs older than specified days

**GET /api/logs/modules**
- Get list of unique modules

#### Log Levels

- **info**: Normal operation logs
- **warning**: Warning conditions
- **error**: Error conditions requiring attention

#### Example Usage

```bash
# Get all logs
curl "http://localhost:5000/api/logs/?page=1&per_page=50"

# Filter by level
curl "http://localhost:5000/api/logs/?level=error"

# Filter by module
curl "http://localhost:5000/api/logs/?module=parsing"

# Search logs
curl "http://localhost:5000/api/logs/?search=timeout"

# Filter by date range
curl "http://localhost:5000/api/logs/?start_date=2026-01-01T00:00:00Z&end_date=2026-01-13T23:59:59Z"

# Get statistics
curl "http://localhost:5000/api/logs/statistics?days=7"

# Export logs
curl "http://localhost:5000/api/logs/export?level=error" > error_logs.json

# Cleanup old logs
curl -X POST "http://localhost:5000/api/logs/cleanup" \
  -H "Content-Type: application/json" \
  -d '{"days": 90}'

# Get modules
curl "http://localhost:5000/api/logs/modules"
```

---

### 4. Help and Feedback

Built-in help documentation and user feedback system.

#### Help Endpoints

**GET /api/help/topics**
- Get list of help topics

**GET /api/help/topics/{topic_id}**
- Get specific help topic content

**GET /api/help/search**
- Search help topics

#### Feedback Endpoints

**POST /api/feedback/**
- Submit user feedback
- Types: bug, feature, other

**GET /api/feedback/**
- List all feedback with filtering

**GET /api/feedback/{id}**
- Get feedback details

**PUT /api/feedback/{id}**
- Update feedback status

**DELETE /api/feedback/{id}**
- Delete feedback

**GET /api/feedback/statistics**
- Get feedback statistics

#### Help Topics

- `getting_started`: Quick start guide
- `configuration`: Configuration guide
- `content_management`: Content management guide
- `api_reference`: API documentation
- `troubleshooting`: Common issues and solutions

#### Example Usage

```bash
# Get help topics
curl "http://localhost:5000/api/help/topics"

# Get specific topic
curl "http://localhost:5000/api/help/topics/getting_started"

# Search help
curl "http://localhost:5000/api/help/search?q=configuration"

# Submit feedback
curl -X POST "http://localhost:5000/api/feedback/" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "bug",
    "content": "Found a bug when parsing URLs with special characters",
    "user_email": "user@example.com"
  }'

# List feedback
curl "http://localhost:5000/api/feedback/?type=bug&status=new"

# Update feedback status
curl -X PUT "http://localhost:5000/api/feedback/1" \
  -H "Content-Type: application/json" \
  -d '{"status": "reviewed"}'
```

---

## Database Schema

### Backup Table

```sql
CREATE TABLE backup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(500) NOT NULL,
    filepath VARCHAR(1000) NOT NULL,
    size BIGINT NOT NULL,
    type VARCHAR(20) NOT NULL,  -- manual/auto
    created_at DATETIME NOT NULL,
    expires_at DATETIME
);
```

### BackupFiles Table

```sql
CREATE TABLE backup_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_id INTEGER NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    size BIGINT NOT NULL,
    FOREIGN KEY (backup_id) REFERENCES backup(id) ON DELETE CASCADE
);
```

### OperationLog Table

```sql
CREATE TABLE operation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level VARCHAR(20) NOT NULL,  -- info/warning/error
    module VARCHAR(100) NOT NULL,
    action VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    user_id VARCHAR(100),
    ip_address VARCHAR(50),
    created_at DATETIME NOT NULL
);
```

### Feedback Table

```sql
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type VARCHAR(50) NOT NULL,  -- bug/feature/other
    content TEXT NOT NULL,
    screenshot_path VARCHAR(500),
    user_email VARCHAR(200),
    status VARCHAR(50) NOT NULL DEFAULT 'new',
    created_at DATETIME NOT NULL
);
```

---

## Service Layer Details

### ContentManagementService

```python
class ContentManagementService:
    def get_local_content(page, per_page, status, search, sort, order)
    def get_content_details(content_id)
    def update_content(content_id, updates)
    def delete_content_batch(content_ids)
    def reparse_content(content_ids)
    def regenerate_ai_content(content_ids, model_id, processing_config)
    def get_content_statistics()
```

### BackupService

```python
class BackupService:
    def create_backup(backup_type, include_database, include_files, retention_days)
    def list_backups(backup_type, page, per_page)
    def get_backup_details(backup_id)
    def restore_backup(backup_id, restore_database, restore_files)
    def delete_backup(backup_id, delete_file)
    def cleanup_expired_backups()
    def get_backup_statistics()
```

### LogService

```python
class LogService:
    def create_log(level, module, action, message, user_id, ip_address)
    def get_logs(level, module, search, start_date, end_date, page, per_page)
    def get_log_statistics(days)
    def cleanup_old_logs(days)
    def export_logs(level, module, start_date, end_date, format)
    def get_modules()
```

### FeedbackService

```python
class FeedbackService:
    def submit_feedback(feedback_type, content, user_email, screenshot_path)
    def get_feedback_list(feedback_type, status, page, per_page)
    def get_feedback_details(feedback_id)
    def update_feedback_status(feedback_id, status)
    def delete_feedback(feedback_id)
    def get_feedback_statistics()
```

### HelpService

```python
class HelpService:
    def get_help_topics()
    def get_help_topic(topic_id)
    def search_help(query)
```

---

## Testing

### Integration Tests

```bash
# Run all Phase 6 tests
python3 -m pytest tests/integration/test_phase6_features.py -v

# Run specific test class
python3 -m pytest tests/integration/test_phase6_features.py::TestContentManagement -v

# Run specific test
python3 -m pytest tests/integration/test_phase6_features.py::TestBackupService::test_create_backup -v
```

### Test Coverage

```
tests/integration/test_phase6_features.py:
- TestContentManagement: 7 tests
- TestBackupService: 7 tests
- TestLogService: 8 tests
- TestFeedbackService: 7 tests
- TestHelpService: 4 tests
Total: 33 tests
```

---

## Best Practices

### Backup Strategy

1. **Scheduled Backups**: Create automatic backups daily
2. **Retention Policy**: Keep backups for 30 days
3. **Before Major Operations**: Create manual backup before:
   - Database migrations
   - Bulk deletions
   - Configuration changes

### Log Management

1. **Log Rotation**: Clean up logs older than 90 days
2. **Error Monitoring**: Review error logs daily
3. **Performance Tracking**: Monitor log statistics for bottlenecks

### Content Management

1. **Batch Operations**: Use batch endpoints for multiple items
2. **Async Processing**: Use reparse/regenerate for large batches
3. **Regular Cleanup**: Delete unwanted content periodically

---

## Future Enhancements

### Potential Improvements

1. **Scheduled Backups**: Cron-based automatic backups
2. **Cloud Backup**: S3/GCS integration
3. **Advanced Search**: Full-text search with Elasticsearch
4. **Real-time Logs**: WebSocket-based live log streaming
5. **Email Notifications**: Feedback notifications via email
6. **User Authentication**: Multi-user support with permissions
7. **Audit Trail**: Track all modifications with user attribution

---

## Troubleshooting

### Common Issues

**Backup Creation Fails**
- Check disk space: `df -h`
- Verify write permissions: `ls -la backups/`
- Check database file exists: `ls -la instance/notion_kb.db`

**Restore Fails**
- Ensure backup file exists
- Stop application before restore
- Backup current database first

**Log Query Slow**
- Add indexes on `created_at`, `level`, `module`
- Clean up old logs: `POST /api/logs/cleanup`
- Use date range filters

**Content Search Returns Wrong Results**
- Check search syntax (case-insensitive, wildcard)
- Verify formatted_content has data
- Try exact title match

---

## Summary

Phase 6 provides comprehensive content management and auxiliary tools:

✅ **Content Management** - Full CRUD with search and filtering
✅ **Backup/Restore** - Database and file backup system
✅ **Log Management** - Query, filter, and export logs
✅ **Help System** - Built-in documentation
✅ **Feedback System** - User feedback collection and management

All features are fully functional with RESTful APIs and singleton service instances.
