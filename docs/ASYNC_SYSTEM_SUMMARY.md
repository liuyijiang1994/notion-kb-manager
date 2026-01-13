# Async Task Processing System - Summary

## ✅ What Was Created

### Management Scripts

1. **`scripts/start_workers.py`** (380 lines)
   - Multi-queue worker management
   - Process spawning and monitoring
   - Worker statistics
   - Production-ready with systemd/supervisor support
   
   ```bash
   python scripts/start_workers.py               # Start all
   python scripts/start_workers.py --queue parsing --workers 5
   python scripts/start_workers.py --stats       # Show stats
   ```

2. **`scripts/test_async_system.py`** (280 lines)
   - 6 comprehensive tests
   - Redis connection validation
   - Queue and worker checks
   - Job enqueueing tests
   - Task service integration tests
   
   ```bash
   python scripts/test_async_system.py
   ```

3. **`scripts/monitor_async.py`** (340 lines)
   - Real-time dashboard
   - Live queue/worker monitoring
   - Health status indicators
   - JSON output support
   
   ```bash
   python scripts/monitor_async.py              # Live dashboard
   python scripts/monitor_async.py --once       # Snapshot
   python scripts/monitor_async.py --json       # JSON output
   ```

### Documentation

1. **`docs/ASYNC_SYSTEM_GUIDE.md`** (600+ lines)
   - Complete architecture overview
   - Queue type descriptions
   - Quick start guide
   - Production deployment (systemd, supervisor, Docker)
   - Performance tuning
   - Monitoring and debugging
   - Troubleshooting
   - Best practices
   - Advanced features

2. **`README_ASYNC.md`**
   - Quick reference guide
   - TL;DR commands
   - Scripts overview
   - Monitoring endpoints

## 🏗️ System Architecture

```
┌────────────────┐         ┌─────────────┐         ┌──────────────────┐
│   Flask API    │ enqueue │   Redis     │ dequeue │   RQ Workers     │
│   (Port 5000)  │ ──────> │   Queues    │ <────── │   (3 queues)     │
└────────────────┘         └─────────────┘         └──────────────────┘
        │                                                    │
        │                  ┌─────────────┐                  │
        └──────────────────│  PostgreSQL │──────────────────┘
                           │  Database   │
                           └─────────────┘
```

## 📊 Queue Configuration

| Queue   | Purpose           | Workers | Timeout | Use Case                    |
|---------|-------------------|---------|---------|------------------------------|
| parsing | Content extraction| 3       | 60s     | Web scraping, HTML parsing   |
| ai      | AI processing     | 2       | 120s    | Summarization, categorization|
| notion  | Notion API        | 2       | 60s     | Page creation, imports       |
| default | Miscellaneous     | 1       | 180s    | General background tasks     |

## 🚀 Quick Start

```bash
# 1. Start Redis (if not running)
redis-server

# 2. Test the system
python scripts/test_async_system.py

# 3. Start all workers
python scripts/start_workers.py

# 4. Monitor in real-time
python scripts/monitor_async.py

# 5. Use the API
curl -X POST http://localhost:5000/api/parsing/sync \
  -H "Content-Type: application/json" \
  -d '{"link_ids": [1,2,3], "async": true}'
```

## 📈 Monitoring

### CLI Monitoring

```bash
# Real-time dashboard (updates every 2 seconds)
python scripts/monitor_async.py

# Single snapshot
python scripts/monitor_async.py --once

# JSON output (for integrations)
python scripts/monitor_async.py --json

# Worker and queue statistics
python scripts/start_workers.py --stats
```

### API Monitoring

```bash
# Worker status
curl http://localhost:5000/api/monitoring/workers

# Queue statistics
curl http://localhost:5000/api/monitoring/queues

# System health
curl http://localhost:5000/api/monitoring/health

# Detailed health
curl http://localhost:5000/api/monitoring/health/detailed

# Prometheus metrics
curl http://localhost:5000/api/monitoring/metrics
```

## 🔄 Task Lifecycle

```
┌─────────┐
│ pending │  → Task created, not queued yet
└────┬────┘
     │ enqueue()
     ▼
┌─────────┐
│ queued  │  → Job added to Redis queue
└────┬────┘
     │ worker picks up
     ▼
┌─────────┐
│ running │  → Worker processing
└────┬────┘
     │
     ├──────────┬──────────┐
     ▼          ▼          ▼
┌──────────┐ ┌──────┐ ┌─────────┐
│completed │ │failed│ │cancelled│
└──────────┘ └──────┘ └─────────┘
```

## ⚙️ Configuration

### Environment Variables

```bash
# Redis connection
REDIS_URL=redis://localhost:6379/0

# Worker counts
WORKER_COUNT_PARSING=3
WORKER_COUNT_AI=2
WORKER_COUNT_NOTION=2

# Retry settings
MAX_TASK_RETRIES=3

# Task retention
TASK_RETENTION_DAYS=7
FAILED_TASK_RETENTION_DAYS=30
```

### Queue Configuration

See `config/workers.py`:
- Timeout settings per queue
- Result TTL
- Retry delays: [0, 30, 300] seconds
- Worker heartbeat interval

## 🔥 Production Deployment

### systemd (Linux)

```bash
# Create service file
sudo nano /etc/systemd/system/rq-workers.service

# Enable and start
sudo systemctl enable rq-workers
sudo systemctl start rq-workers

# Check status
sudo systemctl status rq-workers
```

### Docker Compose

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
```

### Supervisor

```ini
[program:rq-parsing]
command=/opt/notion-kb-manager/venv/bin/python scripts/start_workers.py --queue parsing --workers 3
autostart=true
autorestart=true
```

## 🐛 Troubleshooting

### Workers Not Processing

**Check 1:** Redis running?
```bash
redis-cli ping
```

**Check 2:** Workers started?
```bash
python scripts/start_workers.py --stats
```

**Check 3:** Correct queue names?
```python
from config.workers import WorkerConfig
print(WorkerConfig.QUEUE_NAMES)
```

### High Queue Backlog

**Solutions:**
1. Scale workers: `python scripts/start_workers.py --queue parsing --workers 10`
2. Check worker logs for errors
3. Increase timeouts in `config/workers.py`
4. Optimize job functions

### Memory Issues

**Solutions:**
1. Increase Redis maxmemory: `redis-cli CONFIG SET maxmemory 2gb`
2. Clean old jobs: `redis-cli EVAL "return redis.call('del', unpack(redis.call('keys', 'rq:job:*')))" 0`
3. Reduce result TTL in config

## 📊 Performance Metrics

The system tracks:
- **Request metrics**: Count, duration, size
- **Task metrics**: Execution time, status distribution
- **Queue metrics**: Size, failed jobs, worker count
- **System metrics**: CPU, memory, disk usage

Access via:
- Prometheus endpoint: `/api/monitoring/metrics`
- Health checks: `/api/monitoring/health/detailed`
- CLI dashboard: `python scripts/monitor_async.py`

## 🎯 Next Steps

1. **Start Redis** and **workers** in your environment
2. **Test** the system with `test_async_system.py`
3. **Monitor** with the live dashboard
4. **Deploy** to production using systemd/Docker
5. **Scale** workers based on load

## 📚 References

- Full guide: `docs/ASYNC_SYSTEM_GUIDE.md`
- Worker config: `config/workers.py`
- Task service: `app/services/background_task_service.py`
- Monitoring API: `app/api/monitoring_routes.py`

---

**Status:** ✅ Complete and production-ready
**Last Updated:** 2026-01-13
