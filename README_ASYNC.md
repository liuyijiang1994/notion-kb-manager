# 🚀 Quick Start: Async Task System

## TL;DR

```bash
# 1. Start Redis
redis-server

# 2. Start workers
python scripts/start_workers.py

# 3. Test system
python scripts/test_async_system.py

# 4. Use the API
curl -X POST http://localhost:5000/api/parsing/sync \
  -H "Content-Type: application/json" \
  -d '{"link_ids": [1,2,3], "async": true}'
```

## What is This?

The async task system allows **background processing** of:
- 📄 **Content parsing** (web scraping)
- 🤖 **AI processing** (summarization, categorization)
- 📝 **Notion imports** (database creation, page updates)

**Without blocking the API!**

## Architecture

```
API Request → Redis Queue → Workers → Database
     ↓                           ↓
   Returns                   Process
   task_id                  in background
```

## Scripts

### `start_workers.py`
Manages RQ worker processes

```bash
# Start all workers (3 parsing, 2 AI, 2 Notion)
python scripts/start_workers.py

# Start specific queue with 5 workers
python scripts/start_workers.py --queue parsing --workers 5

# Show worker/queue statistics
python scripts/start_workers.py --stats
```

### `test_async_system.py`
Tests the entire async infrastructure

```bash
python scripts/test_async_system.py
```

Tests:
1. ✓ Redis connection
2. ✓ Queue creation
3. ✓ Worker availability
4. ✓ Job enqueueing
5. ✓ Task service
6. ✓ Queue statistics

## Queues

| Queue    | Purpose           | Workers | Timeout |
|----------|-------------------|---------|---------|
| parsing  | Content extraction| 3       | 60s     |
| ai       | AI processing     | 2       | 120s    |
| notion   | Notion API calls  | 2       | 60s     |
| default  | Miscellaneous     | 1       | 180s    |

## Monitoring

### API Endpoints

```bash
# Workers
curl http://localhost:5000/api/monitoring/workers

# Queues
curl http://localhost:5000/api/monitoring/queues

# Health
curl http://localhost:5000/api/monitoring/health

# Metrics (Prometheus)
curl http://localhost:5000/api/monitoring/metrics
```

### CLI

```bash
# Worker stats
python scripts/start_workers.py --stats

# Redis stats
redis-cli INFO stats
```

## Full Documentation

See [docs/ASYNC_SYSTEM_GUIDE.md](docs/ASYNC_SYSTEM_GUIDE.md) for:
- Detailed architecture
- Production deployment
- Performance tuning
- Troubleshooting
- Advanced features

---

**Need help?** Check the logs:
```bash
tail -f logs/app.log
```
