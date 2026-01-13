# Async Task Processing System Guide

## Overview

The Notion KB Manager uses **Redis Queue (RQ)** for asynchronous task processing. This allows resource-intensive operations (parsing, AI processing, Notion imports) to run in the background without blocking the API.

## Architecture

```
┌─────────────┐         ┌─────────┐         ┌──────────────┐
│   API       │  ─────> │  Redis  │  <────  │  RQ Workers  │
│  Server     │  enqueue│  Queue  │  dequeue│  (3 queues)  │
└─────────────┘         └─────────┘         └──────────────┘
      │                                              │
      │                                              │
      └──────────────────┬───────────────────────────┘
                         │
                  ┌──────▼───────┐
                  │  PostgreSQL  │
                  │   Database   │
                  └──────────────┘
```

### Components

1. **Redis Server** - Message broker and queue storage
2. **RQ Queues** - Three specialized queues for different task types
3. **RQ Workers** - Background processes that execute jobs
4. **Task Service** - Python API for managing tasks
5. **Database** - Task status and result persistence

## Queue Types

### 1. Parsing Queue (`parsing`)
- **Purpose**: Content extraction from URLs
- **Timeout**: 60 seconds per job
- **Workers**: 3 (recommended)
- **Use cases**: Web scraping, HTML parsing, content extraction

### 2. AI Queue (`ai`)
- **Purpose**: AI/LLM processing
- **Timeout**: 120 seconds per job
- **Workers**: 2 (recommended)
- **Use cases**: Content summarization, categorization, sentiment analysis

### 3. Notion Queue (`notion`)
- **Purpose**: Notion API interactions
- **Timeout**: 60 seconds per job
- **Workers**: 2 (recommended)
- **Use cases**: Page creation, database updates, imports

### 4. Default Queue (`default`)
- **Purpose**: Miscellaneous tasks
- **Timeout**: 180 seconds per job
- **Workers**: 1 (recommended)
- **Use cases**: General background tasks, cleanup, maintenance

## Quick Start

### 1. Start Redis

```bash
# macOS (Homebrew)
brew install redis
redis-server

# Linux (apt)
sudo apt install redis-server
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:6-alpine
```

Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

### 2. Start Workers

**Start all workers:**
```bash
python scripts/start_workers.py
```

**Start specific queue:**
```bash
python scripts/start_workers.py --queue parsing --workers 3
```

**Start with custom configuration:**
```bash
# Set worker counts via environment
export WORKER_COUNT_PARSING=5
export WORKER_COUNT_AI=3
python scripts/start_workers.py
```

### 3. Test the System

```bash
python scripts/test_async_system.py
```

This will run 6 tests:
- ✓ Redis connection
- ✓ Queue creation
- ✓ Worker availability
- ✓ Job enqueueing
- ✓ Background task service
- ✓ Queue statistics

### 4. Monitor Workers

**Check worker status:**
```bash
python scripts/start_workers.py --stats
```

**Monitor via API:**
```bash
# Get worker info
curl http://localhost:5000/api/monitoring/workers

# Get queue stats
curl http://localhost:5000/api/monitoring/queues

# Get system health
curl http://localhost:5000/api/monitoring/health
```

## Usage Examples

### Creating a Background Task (Python)

```python
from app.services.background_task_service import get_background_task_service

# Get service instance
task_service = get_background_task_service()

# Create a parsing task
task = task_service.create_task(
    type='parsing',
    total_items=10,  # Number of URLs to parse
    config={'parser': 'beautifulsoup'},
    queue_name='parsing'
)

# Create task items (one per URL)
for i, url in enumerate(urls):
    item = task_service.create_task_item(
        task_id=task.id,
        item_id=link_ids[i],
        item_type='link'
    )

# Enqueue jobs to workers
for link_id in link_ids:
    job_id = task_service.enqueue_job(
        task_id=task.id,
        queue_name='parsing',
        job_func='app.workers.parsing_worker.parse_content_job',
        link_id=link_id
    )

# Check task status
status = task_service.get_task_status(task.id)
print(f"Progress: {status['progress']}%")
print(f"Completed: {status['completed_items']}/{status['total_items']}")
```

### Creating a Background Task (API)

```bash
# Start a parsing task
curl -X POST http://localhost:5000/api/parsing/sync \
  -H "Content-Type: application/json" \
  -d '{
    "link_ids": [1, 2, 3],
    "async": true
  }'

# Response
{
  "success": true,
  "data": {
    "task_id": 42,
    "status": "queued",
    "total_items": 3
  }
}

# Check task status
curl http://localhost:5000/api/tasks/history/42

# Get detailed progress
curl http://localhost:5000/api/tasks/history/42/items
```

## Worker Management

### Starting Workers in Production

**Option 1: systemd (Linux)**

Create `/etc/systemd/system/rq-worker-parsing.service`:
```ini
[Unit]
Description=RQ Worker - Parsing Queue
After=redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/notion-kb-manager
Environment="REDIS_URL=redis://localhost:6379/0"
ExecStart=/opt/notion-kb-manager/venv/bin/python scripts/start_workers.py --queue parsing --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable rq-worker-parsing
sudo systemctl start rq-worker-parsing
sudo systemctl status rq-worker-parsing
```

**Option 2: Supervisor**

Create `/etc/supervisor/conf.d/rq-workers.conf`:
```ini
[program:rq-parsing]
command=/opt/notion-kb-manager/venv/bin/python scripts/start_workers.py --queue parsing --workers 3
directory=/opt/notion-kb-manager
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/rq-parsing.log
```

**Option 3: Docker Compose**

```yaml
services:
  worker-parsing:
    build: .
    command: python scripts/start_workers.py --queue parsing --workers 3
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped

  worker-ai:
    build: .
    command: python scripts/start_workers.py --queue ai --workers 2
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped
```

### Scaling Workers

**Horizontal scaling:**
```bash
# Start more parsing workers
python scripts/start_workers.py --queue parsing --workers 10

# Or use environment variables
export WORKER_COUNT_PARSING=10
python scripts/start_workers.py
```

**Multiple machines:**
```bash
# Machine 1: Parsing workers
REDIS_URL=redis://redis-server:6379/0 python scripts/start_workers.py --queue parsing

# Machine 2: AI workers
REDIS_URL=redis://redis-server:6379/0 python scripts/start_workers.py --queue ai

# Machine 3: Notion workers
REDIS_URL=redis://redis-server:6379/0 python scripts/start_workers.py --queue notion
```

## Task Lifecycle

```
┌─────────┐
│ pending │  Task created but not queued
└────┬────┘
     │
     ▼
┌─────────┐
│ queued  │  Job enqueued to Redis
└────┬────┘
     │
     ▼
┌─────────┐
│ running │  Worker processing job
└────┬────┘
     │
     ├──────────┬──────────┐
     ▼          ▼          ▼
┌──────────┐ ┌──────┐ ┌─────────┐
│completed │ │failed│ │cancelled│
└──────────┘ └──────┘ └─────────┘
```

### Status Transitions

1. **pending** → **queued**: Job enqueued to Redis
2. **queued** → **running**: Worker picks up job
3. **running** → **completed**: Job finished successfully
4. **running** → **failed**: Job raised exception
5. **any** → **cancelled**: User cancelled task

## Retry Logic

Failed jobs are automatically retried with exponential backoff:

```python
# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [0, 30, 300]  # seconds

# Retry 1: Immediate
# Retry 2: After 30 seconds
# Retry 3: After 5 minutes
```

After 3 failed attempts, the item is marked as permanently failed.

### Manual Retry

```bash
# Retry all failed items in a task
curl -X POST http://localhost:5000/api/tasks/history/42/retry

# Or via Python
task_service.retry_failed_items(
    task_id=42,
    queue_name='parsing',
    job_func='app.workers.parsing_worker.parse_content_job'
)
```

## Monitoring & Debugging

### Queue Statistics

```bash
# Via script
python scripts/start_workers.py --stats

# Via API
curl http://localhost:5000/api/monitoring/queues
```

Output:
```json
{
  "success": true,
  "queues": {
    "parsing": {
      "count": 5,
      "started_job_registry": 2,
      "finished_job_registry": 100,
      "failed_job_registry": 3
    }
  }
}
```

### Worker Health

```bash
# Check all workers
curl http://localhost:5000/api/monitoring/workers

# Check specific worker
redis-cli HGETALL rq:worker:parsing-worker-1
```

### Failed Jobs

```bash
# List failed jobs
redis-cli ZRANGE rq:queue:parsing:failed 0 -1

# Get job details
redis-cli HGETALL rq:job:abc123

# Requeue failed job
redis-cli ZADD rq:queue:parsing 0 abc123
redis-cli ZREM rq:queue:parsing:failed abc123
```

### Logging

Workers log to stdout by default. Redirect to file:

```bash
python scripts/start_workers.py > logs/workers.log 2>&1
```

Or configure Python logging in `config/settings.py`:

```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/workers.log',
            'formatter': 'default'
        }
    },
    'loggers': {
        'rq.worker': {
            'handlers': ['file'],
            'level': 'INFO'
        }
    }
}
```

## Performance Tuning

### Redis Configuration

**redis.conf optimizations:**
```conf
# Increase max memory
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence (optional)
save 900 1
save 300 10
save 60 10000

# Disable slow operations
rename-command KEYS ""
rename-command FLUSHALL ""
```

### Worker Configuration

**Optimal worker counts:**
- **CPU-bound tasks**: Workers = CPU cores
- **I/O-bound tasks**: Workers = CPU cores × 2-4
- **Mixed workload**: Start with CPU cores and tune

**Adjust timeouts:**
```python
# config/workers.py
PARSING_TIMEOUT = 120  # Increase if parsing large pages
AI_TIMEOUT = 300       # Increase for slow LLM APIs
NOTION_TIMEOUT = 90    # Increase for large imports
```

### Queue Priorities

Prioritize urgent jobs:
```python
from rq import Queue

# Enqueue with higher priority (lower number = higher priority)
queue.enqueue(job_func, args, at_front=True)  # Jump to front
```

## Troubleshooting

### Workers Not Processing Jobs

**Check 1: Redis connection**
```bash
redis-cli ping
```

**Check 2: Workers running**
```bash
python scripts/start_workers.py --stats
```

**Check 3: Queue names match**
```python
# Verify queue names
from config.workers import WorkerConfig
print(WorkerConfig.QUEUE_NAMES)
```

### Jobs Stuck in Queue

**Symptoms:** Jobs enqueued but never start

**Solutions:**
1. Check worker logs for errors
2. Verify job function path is correct
3. Ensure dependencies are installed in worker environment
4. Check Redis memory (may be full)

### Jobs Failing Silently

**Enable verbose logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check exception info:**
```python
from rq.job import Job
job = Job.fetch('job-id', connection=redis_conn)
print(job.exc_info)
```

### Memory Issues

**Symptoms:** Workers crashing, Redis OOM

**Solutions:**
1. Increase Redis maxmemory
2. Reduce result TTL
3. Clean up old jobs:
   ```bash
   redis-cli DEL $(redis-cli KEYS "rq:job:*" | head -1000)
   ```
4. Use smaller batch sizes

### High Queue Backlog

**Symptoms:** Thousands of pending jobs

**Solutions:**
1. Scale workers horizontally
2. Increase worker timeout
3. Optimize job functions
4. Consider job batching

## Best Practices

### 1. Keep Jobs Small
```python
# ❌ Bad: One job for 1000 items
job = queue.enqueue(process_all_links, link_ids)

# ✓ Good: One job per item
for link_id in link_ids:
    job = queue.enqueue(process_single_link, link_id)
```

### 2. Handle Failures Gracefully
```python
def job_function(item_id):
    try:
        # Process item
        result = process_item(item_id)
        return {'success': True, 'result': result}
    except Exception as e:
        logger.error(f"Job failed: {e}")
        return {'success': False, 'error': str(e)}
```

### 3. Use Timeouts
```python
# Set realistic timeouts
queue.enqueue(
    long_running_task,
    timeout=300,  # 5 minutes
    result_ttl=3600  # Keep result for 1 hour
)
```

### 4. Monitor Queue Health
```python
from rq import Queue

def check_queue_health(queue_name):
    q = Queue(queue_name, connection=redis_conn)
    pending = len(q)

    if pending > 1000:
        alert("Queue backlog critical!")
    elif pending > 100:
        warn("Queue backlog high")
```

### 5. Clean Up Old Data
```python
# Schedule periodic cleanup
from rq.registry import FinishedJobRegistry

def cleanup_old_jobs():
    registry = FinishedJobRegistry('parsing', connection=redis_conn)
    # Keep jobs for 1 day
    registry.cleanup(60 * 60 * 24)
```

## Advanced Features

### Job Dependencies

Execute jobs sequentially:
```python
job1 = queue.enqueue(parse_content, url)
job2 = queue.enqueue(ai_process, depends_on=job1)
job3 = queue.enqueue(import_notion, depends_on=job2)
```

### Scheduled Jobs

Delay job execution:
```python
from datetime import datetime, timedelta

# Execute in 1 hour
queue.enqueue_at(
    datetime.utcnow() + timedelta(hours=1),
    cleanup_task
)

# Execute every day (use RQ Scheduler)
from rq_scheduler import Scheduler
scheduler = Scheduler(connection=redis_conn)
scheduler.cron(
    "0 0 * * *",  # Daily at midnight
    func=daily_backup,
    queue_name='default'
)
```

### Job Result Storage

Store and retrieve results:
```python
# Enqueue with result storage
job = queue.enqueue(calculate_stats, result_ttl=3600)

# Later, retrieve result
from rq.job import Job
job = Job.fetch(job_id, connection=redis_conn)
print(job.result)
```

### Custom Worker Classes

```python
from rq.worker import Worker

class CustomWorker(Worker):
    def perform_job(self, job, queue):
        # Add custom logic
        logger.info(f"Starting job {job.id}")
        result = super().perform_job(job, queue)
        logger.info(f"Finished job {job.id}")
        return result
```

## References

- [RQ Documentation](https://python-rq.org/)
- [Redis Documentation](https://redis.io/docs/)
- [Background Task Service](../app/services/background_task_service.py)
- [Worker Configuration](../config/workers.py)
- [Monitoring API](../app/api/monitoring_routes.py)

---

**Last Updated:** 2026-01-13
**Version:** 1.0
**Maintained by:** Notion KB Manager Team
