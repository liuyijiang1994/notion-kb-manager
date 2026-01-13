# Docker Deployment Guide

Quick guide to deploy Notion KB Manager using Docker on your local machine for testing.

## 📋 Prerequisites

- **Docker Desktop** installed and running
  - Download: https://www.docker.com/products/docker-desktop
  - Minimum: Docker 20.10+, Docker Compose v2+
- **8GB RAM** recommended (minimum 4GB)
- **10GB free disk space**

## 🚀 Quick Start (1 Command)

```bash
./scripts/docker-deploy.sh
```

This script will:
1. Check Docker installation
2. Create `.env` file if missing
3. Build all Docker images
4. Start all services
5. Run database migrations
6. Show access URLs

**First build takes 5-10 minutes** (subsequent builds are faster)

## 📝 Manual Deployment

### Step 1: Create Environment File

```bash
cp .env.docker .env
nano .env
```

Add your API keys:
```bash
NOTION_API_KEY=your-notion-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

### Step 2: Build and Start

```bash
# Build images
docker compose build

# Start all services
docker compose up -d

# Check status
docker compose ps
```

### Step 3: Run Migrations

```bash
docker compose exec backend flask db upgrade
```

### Step 4: Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:5000
- **API Docs:** http://localhost:5000/api/docs

**Default Login:**
- Username: `admin`
- Password: `admin123`

## 🐳 Docker Services

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| frontend | kb-frontend | 3000 | React dashboard |
| backend | kb-backend | 5000 | Flask API |
| worker-parsing | kb-worker-parsing | - | Content parsing worker |
| worker-ai | kb-worker-ai | - | AI processing worker |
| worker-notion | kb-worker-notion | - | Notion import worker |
| postgres | kb-postgres | 5432 | PostgreSQL database |
| redis | kb-redis | 6379 | Redis cache/queue |

## 🔧 Management Commands

### View Status

```bash
./scripts/docker-status.sh
```

Shows:
- Container health
- Backend/Frontend status
- Worker status
- Database/Redis status
- Resource usage

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f worker-parsing

# Using helper script
./scripts/docker-logs.sh
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart backend
docker compose restart worker-parsing
```

### Stop Services

```bash
# Stop all (keeps data)
docker compose down

# Stop and remove volumes (deletes data!)
docker compose down -v
```

### Rebuild After Code Changes

```bash
# Rebuild and restart
docker compose up -d --build

# Rebuild specific service
docker compose up -d --build backend
```

## 🔍 Troubleshooting

### Backend won't start

```bash
# Check logs
docker compose logs backend

# Common issue: Database not ready
docker compose restart backend
```

### Workers not processing

```bash
# Check worker logs
docker compose logs worker-parsing
docker compose logs worker-ai
docker compose logs worker-notion

# Restart workers
docker compose restart worker-parsing worker-ai worker-notion
```

### Frontend shows connection error

```bash
# Check if backend is running
curl http://localhost:5000/api/monitoring/health

# Check CORS settings
docker compose logs backend | grep CORS

# Restart frontend
docker compose restart frontend
```

### Database connection errors

```bash
# Check PostgreSQL
docker compose exec postgres pg_isready -U kbuser

# View database logs
docker compose logs postgres

# Restart database
docker compose restart postgres
```

### Redis connection errors

```bash
# Check Redis
docker compose exec redis redis-cli ping

# View Redis logs
docker compose logs redis

# Restart Redis
docker compose restart redis
```

### Port already in use

```bash
# Find process using port 3000
lsof -i :3000

# Find process using port 5000
lsof -i :5000

# Kill process (replace PID)
kill -9 PID
```

### Clean slate (reset everything)

```bash
# Stop and remove everything
docker compose down -v

# Remove images
docker compose down --rmi all

# Start fresh
./scripts/docker-deploy.sh
```

## 📊 Monitoring

### Check System Health

```bash
# API endpoint
curl http://localhost:5000/api/monitoring/health | jq

# Worker status
curl http://localhost:5000/api/monitoring/workers | jq

# Queue status
curl http://localhost:5000/api/monitoring/queues | jq
```

### Resource Usage

```bash
# Real-time stats
docker stats

# Container info
docker compose ps
```

### Database Access

```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U kbuser -d notion_kb

# Run SQL query
docker compose exec postgres psql -U kbuser -d notion_kb -c "SELECT COUNT(*) FROM links;"
```

### Redis Access

```bash
# Connect to Redis
docker compose exec redis redis-cli

# Check queue sizes
docker compose exec redis redis-cli LLEN rq:queue:parsing
docker compose exec redis redis-cli LLEN rq:queue:ai
docker compose exec redis redis-cli LLEN rq:queue:notion
```

## 💾 Data Persistence

Data is stored in Docker volumes:
- `postgres_data` - Database data
- `redis_data` - Redis persistence

**Backup data:**

```bash
# Backup database
docker compose exec postgres pg_dump -U kbuser notion_kb > backup.sql

# Restore database
cat backup.sql | docker compose exec -T postgres psql -U kbuser notion_kb
```

**Data location:**
```bash
# View volumes
docker volume ls | grep notion

# Inspect volume
docker volume inspect notion-kb-manager_postgres_data
```

## 🔒 Security Notes

**For testing only:**
- Uses default passwords (change in production!)
- REQUIRE_AUTH=false (no authentication required)
- Exposed ports (3000, 5000, 5432, 6379)

**For production deployment:**
- Use strong passwords in `.env`
- Set REQUIRE_AUTH=true
- Use reverse proxy (nginx/traefik)
- Enable SSL/TLS
- Close database/redis ports
- Use secrets management

## 🎯 Next Steps

After successful deployment:

1. **Test the frontend:** http://localhost:3000
2. **Check API docs:** http://localhost:5000/api/docs
3. **Import some links** via API
4. **Monitor workers** processing tasks
5. **View dashboard** for system health

## 📚 Additional Resources

- Main README: [README.md](README.md)
- Frontend README: [frontend/README.md](frontend/README.md)
- API Documentation: http://localhost:5000/api/docs
- Async System Guide: [docs/ASYNC_SYSTEM_GUIDE.md](docs/ASYNC_SYSTEM_GUIDE.md)

## ❓ Common Questions

**Q: Can I use this in production?**
A: This setup is for testing. For production, use the cloud deployment guide with proper security settings.

**Q: How do I update the code?**
A: Pull latest changes and rebuild: `docker compose up -d --build`

**Q: Where are the logs stored?**
A: Logs are in the `logs/` directory (mounted volume)

**Q: Can I run this on Windows?**
A: Yes, Docker Desktop works on Windows, Mac, and Linux

**Q: How much RAM does it need?**
A: ~2-3GB total (all containers combined)

---

**Version:** 1.0.0
**Last Updated:** 2026-01-13
