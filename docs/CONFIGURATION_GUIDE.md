# Notion KB Manager - Configuration Guide

Complete reference for all configuration options and settings.

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Database Configuration](#database-configuration)
3. [Redis Configuration](#redis-configuration)
4. [Security Configuration](#security-configuration)
5. [Worker Configuration](#worker-configuration)
6. [External API Configuration](#external-api-configuration)
7. [Logging Configuration](#logging-configuration)
8. [Performance Tuning](#performance-tuning)
9. [Configuration Validation](#configuration-validation)
10. [Environment-Specific Settings](#environment-specific-settings)

---

## Environment Variables

All configuration is managed through the `.env` file in the project root.

### Flask Application Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `FLASK_APP` | string | `app` | Flask application entry point |
| `FLASK_ENV` | string | `development` | Environment: `development`, `testing`, `production` |
| `SECRET_KEY` | string | ⚠️ Required | Flask secret key for sessions and CSRF protection |
| `DEBUG` | boolean | `False` | Enable debug mode (⚠️ Never in production!) |
| `HOST` | string | `0.0.0.0` | Server bind address |
| `PORT` | integer | `5000` | Server port |
| `API_VERSION` | string | `1.0` | API version string |

**Example:**
```bash
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DEBUG=False
HOST=0.0.0.0
PORT=5000
```

**Security Notes:**
- ⚠️ `DEBUG` must be `False` in production
- ⚠️ `SECRET_KEY` must be strong and unique per environment
- Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

---

## Database Configuration

### Database URL

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | string | `sqlite:///data/notion_kb_dev.db` | SQLAlchemy database URL |
| `DATABASE_DIR` | string | `data` | Directory for SQLite databases |

**Supported Databases:**

**SQLite (Development/Small Deployments):**
```bash
DATABASE_URL=sqlite:///data/notion_kb_prod.db
```

**PostgreSQL (Recommended for Production):**
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# With connection options
DATABASE_URL=postgresql://user:pass@host:5432/dbname?sslmode=require
```

**MySQL/MariaDB:**
```bash
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/database_name
```

### Connection Pool Settings

Configure via SQLAlchemy engine options in `config/settings.py`:

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,           # Max connections in pool
    'pool_recycle': 3600,      # Recycle connections after 1 hour
    'pool_pre_ping': True,     # Verify connections before use
    'max_overflow': 20,        # Max connections beyond pool_size
    'pool_timeout': 30,        # Timeout waiting for connection
}
```

### Migration Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_TRACK_MODIFICATIONS` | boolean | `False` | Track SQLAlchemy modifications |
| `DATABASE_ECHO` | boolean | `False` | Log all SQL queries (debug only) |

**Example:**
```bash
# Development
DATABASE_URL=sqlite:///data/notion_kb_dev.db
DATABASE_ECHO=True

# Production
DATABASE_URL=postgresql://notion_user:strong_pass@localhost:5432/notion_kb_prod
DATABASE_ECHO=False
```

---

## Redis Configuration

### Connection Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_URL` | string | `redis://localhost:6379/0` | Redis URL for task queue |
| `REDIS_RATE_LIMIT_URL` | string | `redis://localhost:6379/1` | Redis URL for rate limiting |
| `REDIS_HOST` | string | `localhost` | Redis host (alternative to URL) |
| `REDIS_PORT` | integer | `6379` | Redis port |
| `REDIS_DB` | integer | `0` | Redis database number |
| `REDIS_PASSWORD` | string | `None` | Redis authentication password |

**Redis URL Format:**
```bash
# Basic
REDIS_URL=redis://localhost:6379/0

# With password
REDIS_URL=redis://:password@localhost:6379/0

# With authentication
REDIS_URL=redis://username:password@localhost:6379/0

# SSL/TLS
REDIS_URL=rediss://localhost:6380/0

# Unix socket
REDIS_URL=unix:///var/run/redis/redis.sock?db=0
```

### Redis Configuration Best Practices

**Development:**
```bash
REDIS_URL=redis://localhost:6379/0
REDIS_RATE_LIMIT_URL=redis://localhost:6379/1
```

**Production:**
```bash
# Separate Redis instances for better isolation
REDIS_URL=redis://:strong_password@redis-tasks.internal:6379/0
REDIS_RATE_LIMIT_URL=redis://:strong_password@redis-limits.internal:6379/0

# Or separate databases on same instance
REDIS_URL=redis://:password@localhost:6379/0
REDIS_RATE_LIMIT_URL=redis://:password@localhost:6379/1
```

### Redis Persistence

Configure in `/etc/redis/redis.conf`:

```conf
# RDB snapshots (point-in-time backups)
save 900 1      # After 900 sec if at least 1 key changed
save 300 10     # After 300 sec if at least 10 keys changed
save 60 10000   # After 60 sec if at least 10000 keys changed

# AOF (append-only file) - more durable
appendonly yes
appendfsync everysec

# Memory management
maxmemory 2gb
maxmemory-policy allkeys-lru
```

---

## Security Configuration

### Encryption & Secrets

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SECRET_KEY` | string | ⚠️ Required | Flask secret key |
| `ENCRYPTION_KEY` | string | ⚠️ Required | Fernet encryption key for sensitive data |
| `JWT_SECRET_KEY` | string | ⚠️ Required | JWT token signing key |

**Generate Secure Keys:**

```bash
# SECRET_KEY (32+ bytes, URL-safe)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# ENCRYPTION_KEY (Fernet key)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# JWT_SECRET_KEY (32+ bytes)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Example:**
```bash
SECRET_KEY=xK9mP2nQ7vL3wR8sT4yU6hJ1fG5dA0zC
ENCRYPTION_KEY=n34ezR773VJT_y46aOqUSrm2ovGvgHno9iTu8KATxBk=
JWT_SECRET_KEY=aB7cD9eF2gH5iJ8kL1mN4oP6qR3sT0uV
```

### JWT Authentication

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `JWT_SECRET_KEY` | string | ⚠️ Required | Secret for JWT signing |
| `JWT_ACCESS_TOKEN_EXPIRES` | integer | `3600` | Access token lifetime (seconds) |
| `JWT_REFRESH_TOKEN_EXPIRES` | integer | `2592000` | Refresh token lifetime (seconds) |
| `REQUIRE_AUTH` | boolean | `false` | Enforce authentication on protected endpoints |

**Token Lifetime Recommendations:**

| Environment | Access Token | Refresh Token |
|-------------|-------------|---------------|
| Development | 1 hour (3600) | 30 days (2592000) |
| Production | 15 min (900) | 7 days (604800) |
| High Security | 5 min (300) | 1 day (86400) |

**Example:**
```bash
# Development
JWT_SECRET_KEY=dev-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000
REQUIRE_AUTH=false

# Production
JWT_SECRET_KEY=prod-strong-secret-key
JWT_ACCESS_TOKEN_EXPIRES=900
JWT_REFRESH_TOKEN_EXPIRES=604800
REQUIRE_AUTH=true
```

### CORS Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CORS_ORIGINS` | string | `*` | Allowed origins (comma-separated) |
| `CORS_METHODS` | string | `GET,POST,PUT,DELETE,OPTIONS` | Allowed HTTP methods |
| `CORS_ALLOW_HEADERS` | string | `Content-Type,Authorization` | Allowed headers |

**Example:**
```bash
# Development (allow all)
CORS_ORIGINS=*

# Production (specific domains)
CORS_ORIGINS=https://app.example.com,https://admin.example.com

# Multiple environments
CORS_ORIGINS=https://app.example.com,https://staging.example.com,http://localhost:3000
```

### Rate Limiting

Rate limits are configured in `app/middleware/rate_limiter.py`:

| Endpoint Type | Default Limit | Configuration |
|--------------|---------------|---------------|
| Global | 1000/hour, 100/minute | Default for all endpoints |
| Configuration | 100/hour | `config_rate_limit()` |
| Parsing | 10/minute | `parsing_rate_limit()` |
| AI Processing | 20/minute | `ai_processing_rate_limit()` |
| Backups | 5/hour | `backup_rate_limit()` |

**Custom Rate Limits:**

```python
# In your route file
from app.middleware.rate_limiter import limiter

@app.route('/custom')
@limiter.limit("50 per hour")
def custom_endpoint():
    pass
```

---

## Worker Configuration

### Worker Counts

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `WORKER_COUNT_PARSING` | integer | `3` | Number of parsing workers |
| `WORKER_COUNT_AI` | integer | `2` | Number of AI processing workers |
| `WORKER_COUNT_NOTION` | integer | `2` | Number of Notion import workers |

**Sizing Guidelines:**

| Workload | Parsing | AI | Notion | Total Workers |
|----------|---------|----|----|---------------|
| Light (<100 tasks/day) | 1 | 1 | 1 | 3 |
| Medium (100-1000 tasks/day) | 2-3 | 2 | 1-2 | 5-7 |
| Heavy (1000+ tasks/day) | 4-6 | 3-4 | 2-3 | 9-13 |

**CPU/Memory Guidelines:**
- Each worker: ~200-500 MB RAM
- Parsing workers: CPU-bound (parsing HTML)
- AI workers: I/O-bound (API calls)
- Notion workers: I/O-bound (API calls)

**Example:**
```bash
# Small deployment (2 CPU, 4GB RAM)
WORKER_COUNT_PARSING=2
WORKER_COUNT_AI=1
WORKER_COUNT_NOTION=1

# Medium deployment (4 CPU, 8GB RAM)
WORKER_COUNT_PARSING=3
WORKER_COUNT_AI=2
WORKER_COUNT_NOTION=2

# Large deployment (8 CPU, 16GB RAM)
WORKER_COUNT_PARSING=5
WORKER_COUNT_AI=3
WORKER_COUNT_NOTION=3
```

### Task Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MAX_TASK_RETRIES` | integer | `3` | Maximum retry attempts for failed tasks |
| `TASK_RETENTION_DAYS` | integer | `7` | Days to keep completed tasks |
| `FAILED_TASK_RETENTION_DAYS` | integer | `30` | Days to keep failed tasks |
| `ENABLE_RQ_DASHBOARD` | boolean | `true` | Enable RQ monitoring dashboard |
| `RQ_DASHBOARD_PORT` | integer | `9181` | Port for RQ dashboard |

**Example:**
```bash
# Production
MAX_TASK_RETRIES=3
TASK_RETENTION_DAYS=7
FAILED_TASK_RETENTION_DAYS=30
ENABLE_RQ_DASHBOARD=false  # Disable in production

# Development
MAX_TASK_RETRIES=1
TASK_RETENTION_DAYS=1
FAILED_TASK_RETENTION_DAYS=7
ENABLE_RQ_DASHBOARD=true
RQ_DASHBOARD_PORT=9181
```

---

## External API Configuration

### Notion API

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `NOTION_API_TOKEN` | string | ⚠️ Required | Notion integration token |
| `NOTION_DATABASE_ID` | string | Optional | Default Notion database ID |

**Obtain Notion Token:**

1. Go to https://www.notion.so/my-integrations
2. Create new integration
3. Copy "Internal Integration Token"
4. Share database with integration

**Example:**
```bash
NOTION_API_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=abc123def456ghi789jkl012mno345
```

### AI Model API (VolcEngine Example)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VOLCENGINE_API_TOKEN` | string | ⚠️ Required | AI API authentication token |
| `VOLCENGINE_MODEL_NAME` | string | ⚠️ Required | Model identifier |
| `VOLCENGINE_API_URL` | string | ⚠️ Required | API endpoint URL |

**Example:**
```bash
VOLCENGINE_API_TOKEN=your-api-token-here
VOLCENGINE_MODEL_NAME=doubao-seed-1-6-251015
VOLCENGINE_API_URL=https://ark.cn-beijing.volces.com/api/v3/
```

### OpenAI API (Alternative)

```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL_NAME=gpt-4
OPENAI_API_URL=https://api.openai.com/v1/
```

---

## Logging Configuration

### Log Levels

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LOG_LEVEL` | string | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `LOG_DIR` | string | `logs` | Directory for log files |
| `LOG_FORMAT` | string | `detailed` | Log format: `simple`, `detailed`, `json` |

**Log Level Guide:**

| Level | When to Use | What's Logged |
|-------|-------------|---------------|
| `DEBUG` | Development only | All debug messages, SQL queries, detailed traces |
| `INFO` | Production (default) | General information, requests, task status |
| `WARNING` | Production (quiet) | Warnings and errors only |
| `ERROR` | Production (minimal) | Errors and critical issues only |
| `CRITICAL` | Emergency only | Critical failures only |

**Example:**
```bash
# Development
LOG_LEVEL=DEBUG
LOG_DIR=logs
LOG_FORMAT=detailed

# Production
LOG_LEVEL=INFO
LOG_DIR=/var/log/notion-kb-manager
LOG_FORMAT=json
```

### Log Files

Default log files created:

- `app.log` - Main application log
- `gunicorn_access.log` - HTTP access log
- `gunicorn_error.log` - Gunicorn errors
- `parsing-worker-N.log` - Parsing worker logs
- `ai-worker-N.log` - AI worker logs
- `notion-worker-N.log` - Notion worker logs

### Log Rotation

Configure in `/etc/logrotate.d/notion-kb-manager`:

```
/path/to/logs/*.log {
    daily                    # Rotate daily
    rotate 14               # Keep 14 days
    compress                # Compress old logs
    delaycompress          # Delay compression by 1 rotation
    missingok              # Don't error if log missing
    notifempty             # Don't rotate empty logs
    create 0640 user group  # Create new log with permissions
}
```

---

## Performance Tuning

### Application Performance

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `QUALITY_THRESHOLD` | float | `0.7` | Content quality threshold (0-1) |
| `BATCH_SIZE` | integer | `50` | Batch processing size |
| `RENDER_TIMEOUT` | integer | `30` | Page render timeout (seconds) |
| `CACHE_RETENTION_DAYS` | integer | `7` | Days to retain cached content |

**Batch Size Guidelines:**

| System RAM | Recommended Batch Size |
|------------|----------------------|
| 2-4 GB | 20-30 |
| 4-8 GB | 50-75 |
| 8-16 GB | 100-150 |
| 16+ GB | 200+ |

**Example:**
```bash
# Resource-constrained environment
QUALITY_THRESHOLD=0.8
BATCH_SIZE=20
RENDER_TIMEOUT=15
CACHE_RETENTION_DAYS=3

# High-performance environment
QUALITY_THRESHOLD=0.7
BATCH_SIZE=100
RENDER_TIMEOUT=30
CACHE_RETENTION_DAYS=14
```

### Gunicorn Workers

In `gunicorn_config.py`:

```python
import multiprocessing

# Worker calculation: (2 * CPU_COUNT) + 1
workers = multiprocessing.cpu_count() * 2 + 1

# Worker type
worker_class = "sync"  # or "gevent" for async

# Connections per worker
worker_connections = 1000

# Timeout (should be > longest request time)
timeout = 120

# Keep-alive
keepalive = 5
```

**Worker Guidelines:**

| CPU Cores | Sync Workers | Async Workers |
|-----------|-------------|---------------|
| 2 | 5 | 10-20 |
| 4 | 9 | 20-40 |
| 8 | 17 | 40-80 |

### Database Optimization

**Connection Pooling:**

```python
# In config/settings.py
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,        # Base pool size
    'max_overflow': 20,     # Additional connections
    'pool_timeout': 30,     # Wait timeout
    'pool_recycle': 3600,   # Recycle after 1 hour
    'pool_pre_ping': True,  # Verify connections
}
```

**Query Optimization:**

```python
# Add indexes for frequently queried fields
from app.models.link import Link

class Link(db.Model):
    __table_args__ = (
        db.Index('idx_link_url', 'url'),
        db.Index('idx_link_status', 'validation_status'),
        db.Index('idx_link_imported', 'imported_at'),
    )
```

### Caching Strategy

| Cache Type | Use Case | TTL |
|-----------|----------|-----|
| Redis | API responses, session data | 5-60 min |
| Database | Parsed content | 7 days |
| Disk | Downloaded files | 7 days |

---

## Configuration Validation

### Validate Configuration

Create `scripts/validate_config.py`:

```python
#!/usr/bin/env python3
"""Validate configuration settings"""

import os
from dotenv import load_dotenv

load_dotenv()

def validate_config():
    """Validate all required configuration"""
    errors = []

    # Required variables
    required = [
        'SECRET_KEY',
        'ENCRYPTION_KEY',
        'JWT_SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL',
    ]

    for var in required:
        if not os.getenv(var):
            errors.append(f"Missing required variable: {var}")

    # Validate SECRET_KEY strength
    secret_key = os.getenv('SECRET_KEY', '')
    if len(secret_key) < 32:
        errors.append("SECRET_KEY must be at least 32 characters")

    # Validate production settings
    if os.getenv('FLASK_ENV') == 'production':
        if os.getenv('DEBUG', '').lower() == 'true':
            errors.append("DEBUG must be False in production")

        if os.getenv('REQUIRE_AUTH', '').lower() != 'true':
            errors.append("REQUIRE_AUTH must be True in production")

    # Print results
    if errors:
        print("❌ Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ Configuration validation passed")
        return True

if __name__ == '__main__':
    import sys
    sys.exit(0 if validate_config() else 1)
```

Run validation:

```bash
python scripts/validate_config.py
```

---

## Environment-Specific Settings

### Development Environment

```bash
# .env.development
FLASK_ENV=development
DEBUG=True
LOG_LEVEL=DEBUG

DATABASE_URL=sqlite:///data/notion_kb_dev.db
REDIS_URL=redis://localhost:6379/0

REQUIRE_AUTH=false
JWT_ACCESS_TOKEN_EXPIRES=86400  # 24 hours

WORKER_COUNT_PARSING=1
WORKER_COUNT_AI=1
WORKER_COUNT_NOTION=1

ENABLE_RQ_DASHBOARD=true
```

### Testing Environment

```bash
# .env.testing
FLASK_ENV=testing
DEBUG=False
LOG_LEVEL=WARNING

DATABASE_URL=sqlite:///data/notion_kb_test.db
REDIS_URL=redis://localhost:6379/15  # Separate DB

REQUIRE_AUTH=false  # Easier testing
TESTING=true
```

### Production Environment

```bash
# .env.production
FLASK_ENV=production
DEBUG=False
LOG_LEVEL=INFO

DATABASE_URL=postgresql://user:pass@localhost:5432/notion_kb_prod
REDIS_URL=redis://:password@localhost:6379/0

REQUIRE_AUTH=true
JWT_ACCESS_TOKEN_EXPIRES=900  # 15 minutes

WORKER_COUNT_PARSING=3
WORKER_COUNT_AI=2
WORKER_COUNT_NOTION=2

ENABLE_RQ_DASHBOARD=false

# Production-only
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
DATADOG_API_KEY=xxxxx
```

---

## Configuration Templates

### Minimal Configuration (.env.minimal)

```bash
# Bare minimum for local development
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-me
ENCRYPTION_KEY=dev-encryption-key-change-me
JWT_SECRET_KEY=dev-jwt-secret-change-me

DATABASE_URL=sqlite:///data/notion_kb_dev.db
REDIS_URL=redis://localhost:6379/0

NOTION_API_TOKEN=your_notion_token
```

### Complete Configuration (.env.complete)

```bash
# ========== Flask ==========
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=<GENERATE_STRONG_KEY>
DEBUG=False
HOST=0.0.0.0
PORT=5000

# ========== Database ==========
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# ========== Redis ==========
REDIS_URL=redis://:password@localhost:6379/0
REDIS_RATE_LIMIT_URL=redis://:password@localhost:6379/1

# ========== Security ==========
ENCRYPTION_KEY=<GENERATE_FERNET_KEY>
JWT_SECRET_KEY=<GENERATE_JWT_KEY>
JWT_ACCESS_TOKEN_EXPIRES=900
JWT_REFRESH_TOKEN_EXPIRES=604800
REQUIRE_AUTH=true

# ========== Workers ==========
WORKER_COUNT_PARSING=3
WORKER_COUNT_AI=2
WORKER_COUNT_NOTION=2
MAX_TASK_RETRIES=3
TASK_RETENTION_DAYS=7
FAILED_TASK_RETENTION_DAYS=30

# ========== External APIs ==========
NOTION_API_TOKEN=<YOUR_NOTION_TOKEN>
VOLCENGINE_API_TOKEN=<YOUR_AI_TOKEN>
VOLCENGINE_MODEL_NAME=your-model
VOLCENGINE_API_URL=https://api.example.com/v1/

# ========== Logging ==========
LOG_LEVEL=INFO
LOG_DIR=logs

# ========== Performance ==========
BATCH_SIZE=50
QUALITY_THRESHOLD=0.7
RENDER_TIMEOUT=30
CACHE_RETENTION_DAYS=7

# ========== CORS ==========
CORS_ORIGINS=https://yourdomain.com

# ========== Directories ==========
UPLOAD_FOLDER=uploads
CACHE_FOLDER=cache
BACKUP_FOLDER=backups
REPORTS_DIR=reports
```

---

## Configuration Best Practices

### ✅ DO:

- **Use strong secrets** - Generate with secure random functions
- **Separate environments** - Different configs for dev/test/prod
- **Keep secrets secret** - Never commit .env to version control
- **Validate on startup** - Check required variables exist
- **Document changes** - Comment custom configurations
- **Use environment-specific files** - .env.development, .env.production
- **Set appropriate timeouts** - Based on your workload
- **Monitor resource usage** - Adjust workers based on metrics
- **Regular security audits** - Review configuration quarterly
- **Backup configuration** - Keep secure backup of production .env

### ❌ DON'T:

- **Don't use default secrets** - Change all default keys
- **Don't enable DEBUG in production** - Security risk
- **Don't disable authentication in production** - Security risk
- **Don't overcommit workers** - Monitor CPU/memory usage
- **Don't hardcode secrets** - Always use environment variables
- **Don't share .env files** - Each environment needs unique config
- **Don't ignore warnings** - Investigate configuration warnings
- **Don't skip validation** - Always validate before deployment

---

## Troubleshooting Configuration

### Configuration Not Loading

```bash
# Verify .env file exists
ls -la .env

# Check file permissions
chmod 600 .env

# Verify environment variables loaded
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('FLASK_ENV'))"
```

### Database Connection Fails

```bash
# Test database URL
python -c "from sqlalchemy import create_engine; engine = create_engine('YOUR_DATABASE_URL'); engine.connect()"

# Check PostgreSQL
psql -U username -d database_name -c "SELECT 1;"
```

### Redis Connection Fails

```bash
# Test Redis connection
redis-cli -h localhost -p 6379 ping

# With password
redis-cli -h localhost -p 6379 -a password ping
```

### Worker Issues

```bash
# Check RQ queue
rq info --url redis://localhost:6379/0

# List workers
rq info --url redis://localhost:6379/0 | grep workers
```

---

## Quick Reference

### Generate All Keys

```bash
#!/bin/bash
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
echo "ENCRYPTION_KEY=$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
echo "JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

### Environment Quick Switch

```bash
# Development
cp .env.development .env

# Production
cp .env.production .env

# Testing
cp .env.testing .env
```

### Configuration Checklist

Before deploying to production:

- [ ] All secrets generated and unique
- [ ] `FLASK_ENV=production`
- [ ] `DEBUG=False`
- [ ] `REQUIRE_AUTH=true`
- [ ] Database connection tested
- [ ] Redis connection tested
- [ ] External APIs configured and tested
- [ ] Worker counts appropriate for system
- [ ] Logging configured
- [ ] CORS origins set correctly
- [ ] Backups configured
- [ ] Configuration validated with script

---

## Additional Resources

- **Deployment Guide**: [docs/DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **API Documentation**: `/api/docs` (Swagger UI)
- **Security Checklist**: See Deployment Guide
- **Performance Tuning**: See Deployment Guide

For questions or issues:
- GitHub Issues: https://github.com/yourusername/notion-kb-manager/issues
- Email: support@example.com

---

**Configuration Guide v1.0**
