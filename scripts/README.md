# Worker Management Scripts

Scripts for managing RQ background workers for the Notion KB Manager.

## Prerequisites

1. **Redis** must be installed and running:
   ```bash
   # Install Redis (macOS)
   brew install redis

   # Start Redis
   brew services start redis

   # Or run Redis manually
   redis-server
   ```

2. **Python dependencies** must be installed:
   ```bash
   pip install -r requirements.txt
   ```

## Scripts

### `start_workers.sh`

Start RQ workers for background task processing.

**Usage:**
```bash
# Start all workers (parsing, AI, and Notion)
./scripts/start_workers.sh

# Start only parsing workers
./scripts/start_workers.sh parsing

# Start only AI workers
./scripts/start_workers.sh ai

# Start only Notion workers
./scripts/start_workers.sh notion
```

**What it does:**
- Checks Redis connection
- Starts configured number of workers for each queue
- Creates log files in `logs/` directory
- Runs workers in background

**Worker counts** (configured in `.env`):
- `WORKER_COUNT_PARSING=3` - Parsing queue workers
- `WORKER_COUNT_AI=2` - AI processing queue workers
- `WORKER_COUNT_NOTION=2` - Notion import queue workers

### `stop_workers.sh`

Stop all running RQ workers gracefully.

**Usage:**
```bash
./scripts/stop_workers.sh
```

**What it does:**
- Finds all running `rq worker` processes
- Sends SIGTERM for graceful shutdown
- Waits 3 seconds for workers to finish current jobs
- Force stops any remaining workers

### `start_dashboard.sh`

Start the RQ Dashboard web interface for monitoring workers and queues.

**Usage:**
```bash
./scripts/start_dashboard.sh
```

**What it does:**
- Starts RQ Dashboard on port `9181` (configurable via `RQ_DASHBOARD_PORT`)
- Provides web UI to monitor:
  - Active workers
  - Queue statistics
  - Job status
  - Failed jobs

**Access:** http://localhost:9181

## Typical Workflow

### Development

1. **Start Redis:**
   ```bash
   redis-server
   ```

2. **Start workers:**
   ```bash
   ./scripts/start_workers.sh
   ```

3. **Start dashboard (optional):**
   ```bash
   ./scripts/start_dashboard.sh
   ```

4. **Start Flask app:**
   ```bash
   python3 run.py
   ```

5. **Stop workers when done:**
   ```bash
   ./scripts/stop_workers.sh
   ```

### Production

Use Docker Compose or systemd services for production deployment. See deployment documentation for details.

## Logs

Worker logs are stored in:
```
logs/worker-parsing-queue-1.log
logs/worker-parsing-queue-2.log
logs/worker-ai-queue-1.log
logs/worker-notion-queue-1.log
...
```

**View logs:**
```bash
# Tail all worker logs
tail -f logs/worker-*.log

# Tail specific queue
tail -f logs/worker-parsing-queue-*.log
```

## Troubleshooting

### "Redis is not running"

Start Redis:
```bash
brew services start redis
```

Or check Redis URL in `.env`:
```bash
REDIS_URL=redis://localhost:6379/0
```

### Workers not processing jobs

1. Check workers are running:
   ```bash
   ps aux | grep "rq worker"
   ```

2. Check Redis connection:
   ```bash
   redis-cli -u redis://localhost:6379/0 ping
   ```

3. Check worker logs:
   ```bash
   tail -f logs/worker-*.log
   ```

4. Check queue status via monitoring API:
   ```bash
   curl http://localhost:5000/api/monitoring/queues
   ```

### Workers crash on startup

1. Check Python environment:
   ```bash
   which python3
   pip list | grep rq
   ```

2. Check for import errors:
   ```bash
   python3 -c "from app import create_app; create_app()"
   ```

3. Check database migrations:
   ```bash
   alembic current
   alembic upgrade head
   ```

## Configuration

Edit `.env` to configure workers:

```bash
# Redis
REDIS_URL=redis://localhost:6379/0

# Worker counts
WORKER_COUNT_PARSING=3
WORKER_COUNT_AI=2
WORKER_COUNT_NOTION=2

# Retry settings
MAX_TASK_RETRIES=3

# Dashboard
ENABLE_RQ_DASHBOARD=true
RQ_DASHBOARD_PORT=9181
```
