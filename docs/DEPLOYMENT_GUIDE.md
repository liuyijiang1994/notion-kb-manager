# Notion KB Manager - Production Deployment Guide

Complete guide for deploying Notion KB Manager to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Database Setup](#database-setup)
5. [Redis Setup](#redis-setup)
6. [Worker Setup](#worker-setup)
7. [Application Server](#application-server)
8. [Reverse Proxy (Nginx)](#reverse-proxy-nginx)
9. [SSL/TLS Setup](#ssltls-setup)
10. [Monitoring & Logging](#monitoring--logging)
11. [Backup Strategy](#backup-strategy)
12. [Security Checklist](#security-checklist)
13. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 20 GB SSD
- OS: Ubuntu 20.04+ / Debian 11+ / CentOS 8+ / macOS 11+

**Recommended:**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 50 GB SSD
- OS: Ubuntu 22.04 LTS

### Software Dependencies

```bash
# Ubuntu/Debian
Python 3.9+
Redis 6.0+
PostgreSQL 13+ (or SQLite for small deployments)
Nginx 1.18+
Git 2.x

# Install on Ubuntu 22.04
sudo apt update
sudo apt install -y python3.9 python3.9-venv python3-pip \
    redis-server postgresql postgresql-contrib \
    nginx git build-essential
```

### Network Requirements

**Open Ports:**
- `5000` - Flask application (internal)
- `80` - HTTP (redirect to HTTPS)
- `443` - HTTPS (public access)
- `6379` - Redis (localhost only)
- `5432` - PostgreSQL (localhost only)

**Firewall Configuration:**
```bash
# Ubuntu UFW
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Installation

### 1. Clone Repository

```bash
# Clone from GitHub
git clone https://github.com/yourusername/notion-kb-manager.git
cd notion-kb-manager

# Or download release tarball
wget https://github.com/yourusername/notion-kb-manager/archive/v1.0.0.tar.gz
tar -xzf v1.0.0.tar.gz
cd notion-kb-manager-1.0.0
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify Python version
python --version  # Should be 3.9+
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install production dependencies
pip install -r requirements.txt

# Install production server (Gunicorn)
pip install gunicorn==21.2.0
```

### 4. Create Required Directories

```bash
# Create application directories
mkdir -p logs data backups reports cache uploads

# Set permissions
chmod 755 logs data backups reports cache uploads
```

---

## Configuration

### 1. Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

### 2. Production .env Configuration

```bash
# ==================== Flask Configuration ====================
FLASK_APP=app
FLASK_ENV=production  # IMPORTANT: Set to production
SECRET_KEY=<GENERATE_STRONG_SECRET_KEY>  # See below
DEBUG=False  # IMPORTANT: Disable debug mode

# ==================== Server Configuration ====================
HOST=0.0.0.0
PORT=5000

# ==================== Database Configuration ====================
# Option 1: PostgreSQL (Recommended for production)
DATABASE_URL=postgresql://username:password@localhost:5432/notion_kb_prod

# Option 2: SQLite (Simple deployments only)
# DATABASE_URL=sqlite:///data/notion_kb_prod.db

# ==================== Security ====================
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=<YOUR_STRONG_SECRET_KEY_HERE>

# Generate with: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())
ENCRYPTION_KEY=<YOUR_ENCRYPTION_KEY_HERE>

# JWT Authentication
JWT_SECRET_KEY=<YOUR_JWT_SECRET_HERE>
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour
JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 days
REQUIRE_AUTH=true  # IMPORTANT: Enable authentication

# ==================== Redis Configuration ====================
REDIS_URL=redis://localhost:6379/0
REDIS_RATE_LIMIT_URL=redis://localhost:6379/1

# ==================== Worker Configuration ====================
WORKER_COUNT_PARSING=3
WORKER_COUNT_AI=2
WORKER_COUNT_NOTION=2
MAX_TASK_RETRIES=3
TASK_RETENTION_DAYS=7
FAILED_TASK_RETENTION_DAYS=30
ENABLE_RQ_DASHBOARD=false  # Disable in production

# ==================== External APIs ====================
# Notion API
NOTION_API_TOKEN=<YOUR_NOTION_TOKEN>

# AI Model API (e.g., OpenAI, VolcEngine)
VOLCENGINE_API_TOKEN=<YOUR_AI_TOKEN>
VOLCENGINE_MODEL_NAME=your-model-name
VOLCENGINE_API_URL=https://api.your-ai-provider.com/v1/

# ==================== Logging ====================
LOG_LEVEL=INFO
LOG_DIR=logs

# ==================== File Storage ====================
UPLOAD_FOLDER=uploads
CACHE_FOLDER=cache
BACKUP_FOLDER=backups
REPORTS_DIR=reports

# ==================== CORS Configuration ====================
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 3. Generate Secure Keys

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}')"

# Generate ENCRYPTION_KEY
python3 -c "from cryptography.fernet import Fernet; print(f'ENCRYPTION_KEY={Fernet.generate_key().decode()}')"

# Generate JWT_SECRET_KEY
python3 -c "import secrets; print(f'JWT_SECRET_KEY={secrets.token_urlsafe(32)}')"
```

---

## Database Setup

### Option 1: PostgreSQL (Recommended)

#### Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql@14
```

#### Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE notion_kb_prod;
CREATE USER notion_user WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE notion_kb_prod TO notion_user;

# Exit psql
\q
```

#### Configure Connection

```bash
# Update .env
DATABASE_URL=postgresql://notion_user:strong_password_here@localhost:5432/notion_kb_prod
```

#### Run Migrations

```bash
# Activate virtual environment
source venv/bin/activate

# Initialize database
flask db upgrade

# Verify tables created
psql -U notion_user -d notion_kb_prod -c "\dt"
```

### Option 2: SQLite (Simple Deployments)

```bash
# Update .env
DATABASE_URL=sqlite:///data/notion_kb_prod.db

# Run migrations
flask db upgrade

# Verify database created
ls -lh data/notion_kb_prod.db
```

---

## Redis Setup

### Install Redis

```bash
# Ubuntu/Debian
sudo apt install redis-server

# macOS
brew install redis
```

### Configure Redis

```bash
# Edit Redis configuration
sudo nano /etc/redis/redis.conf

# Recommended settings:
# bind 127.0.0.1  # Only listen on localhost
# maxmemory 2gb  # Limit memory usage
# maxmemory-policy allkeys-lru  # Eviction policy
# requirepass your_redis_password  # Set password (recommended)
```

### Start Redis

```bash
# Ubuntu (systemd)
sudo systemctl enable redis-server
sudo systemctl start redis-server

# macOS
brew services start redis
```

### Verify Redis

```bash
# Test connection
redis-cli ping  # Should return PONG

# Test with password (if set)
redis-cli -a your_redis_password ping
```

---

## Worker Setup

### Create Worker Scripts

Create `start_workers.sh`:

```bash
#!/bin/bash
# start_workers.sh - Start RQ worker processes

# Activate virtual environment
source /path/to/notion-kb-manager/venv/bin/activate

# Change to app directory
cd /path/to/notion-kb-manager

# Start parsing workers (3 workers)
for i in {1..3}; do
    rq worker parsing --url redis://localhost:6379/0 \
        --name "parsing-worker-$i" \
        --log-format "%(asctime)s %(levelname)s: %(message)s" \
        >> logs/parsing-worker-$i.log 2>&1 &
done

# Start AI workers (2 workers)
for i in {1..2}; do
    rq worker ai --url redis://localhost:6379/0 \
        --name "ai-worker-$i" \
        --log-format "%(asctime)s %(levelname)s: %(message)s" \
        >> logs/ai-worker-$i.log 2>&1 &
done

# Start Notion workers (2 workers)
for i in {1..2}; do
    rq worker notion --url redis://localhost:6379/0 \
        --name "notion-worker-$i" \
        --log-format "%(asctime)s %(levelname)s: %(message)s" \
        >> logs/notion-worker-$i.log 2>&1 &
done

echo "Workers started successfully"
```

Make executable:

```bash
chmod +x start_workers.sh
```

### Create systemd Service (Recommended)

Create `/etc/systemd/system/notion-kb-workers.service`:

```ini
[Unit]
Description=Notion KB Manager Workers
After=network.target redis.service

[Service]
Type=forking
User=ubuntu
Group=ubuntu
WorkingDirectory=/path/to/notion-kb-manager
ExecStart=/path/to/notion-kb-manager/start_workers.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable notion-kb-workers
sudo systemctl start notion-kb-workers
sudo systemctl status notion-kb-workers
```

---

## Application Server

### Option 1: Gunicorn (Recommended)

#### Create Gunicorn Configuration

Create `gunicorn_config.py`:

```python
# gunicorn_config.py

import multiprocessing

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # Recommended formula
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "notion-kb-manager"

# Server mechanics
daemon = False
pidfile = "gunicorn.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if terminating SSL at Gunicorn)
# keyfile = "/path/to/private.key"
# certfile = "/path/to/certificate.crt"
```

#### Create systemd Service

Create `/etc/systemd/system/notion-kb-app.service`:

```ini
[Unit]
Description=Notion KB Manager Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/path/to/notion-kb-manager
Environment="PATH=/path/to/notion-kb-manager/venv/bin"
ExecStart=/path/to/notion-kb-manager/venv/bin/gunicorn \
    --config gunicorn_config.py \
    "app:create_app()"
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Start Application

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable notion-kb-app
sudo systemctl start notion-kb-app

# Check status
sudo systemctl status notion-kb-app

# View logs
sudo journalctl -u notion-kb-app -f
```

### Option 2: Docker

#### Create Dockerfile

```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==21.2.0

# Copy application
COPY . .

# Create directories
RUN mkdir -p logs data backups reports cache uploads

# Expose port
EXPOSE 5000

# Run migrations and start Gunicorn
CMD ["sh", "-c", "flask db upgrade && gunicorn --config gunicorn_config.py 'app:create_app()'"]
```

#### Create docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: notion-kb-app
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://notion_user:password@db:5432/notion_kb_prod
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./backups:/app/backups
      - ./reports:/app/reports
    restart: unless-stopped

  db:
    image: postgres:14-alpine
    container_name: notion-kb-db
    environment:
      - POSTGRES_DB=notion_kb_prod
      - POSTGRES_USER=notion_user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    container_name: notion-kb-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

  worker-parsing:
    build: .
    container_name: notion-kb-worker-parsing
    command: rq worker parsing --url redis://redis:6379/0
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - db
    restart: unless-stopped

  worker-ai:
    build: .
    container_name: notion-kb-worker-ai
    command: rq worker ai --url redis://redis:6379/0
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - db
    restart: unless-stopped

  worker-notion:
    build: .
    container_name: notion-kb-worker-notion
    command: rq worker notion --url redis://redis:6379/0
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - db
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: notion-kb-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

#### Deploy with Docker

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f app

# Check status
docker-compose ps
```

---

## Reverse Proxy (Nginx)

### Install Nginx

```bash
# Ubuntu/Debian
sudo apt install nginx

# macOS
brew install nginx
```

### Configure Nginx

Create `/etc/nginx/sites-available/notion-kb-manager`:

```nginx
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;

# Upstream application server
upstream notion_kb_app {
    server 127.0.0.1:5000 fail_timeout=0;
}

# HTTP server (redirect to HTTPS)
server {
    listen 80;
    listen [::]:80;
    server_name api.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.yourdomain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/notion-kb-access.log combined;
    error_log /var/log/nginx/notion-kb-error.log warn;

    # Max upload size
    client_max_body_size 100M;

    # Proxy to application
    location / {
        proxy_pass http://notion_kb_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Rate limiting
        limit_req zone=api_limit burst=20 nodelay;
    }

    # Rate limit login endpoint
    location /api/auth/login {
        proxy_pass http://notion_kb_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Stricter rate limit for login
        limit_req zone=login_limit burst=3 nodelay;
    }

    # Health check endpoint (no rate limit)
    location /api/health {
        proxy_pass http://notion_kb_app;
        proxy_set_header Host $host;
        access_log off;
    }
}
```

### Enable Configuration

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/notion-kb-manager /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## SSL/TLS Setup

### Using Let's Encrypt (Free)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.yourdomain.com

# Verify auto-renewal
sudo certbot renew --dry-run

# Auto-renewal is handled by systemd timer
sudo systemctl status certbot.timer
```

### Using Custom Certificate

```bash
# Copy certificates
sudo mkdir -p /etc/ssl/notion-kb
sudo cp your-certificate.crt /etc/ssl/notion-kb/
sudo cp your-private.key /etc/ssl/notion-kb/
sudo chmod 600 /etc/ssl/notion-kb/your-private.key

# Update Nginx config
ssl_certificate /etc/ssl/notion-kb/your-certificate.crt;
ssl_certificate_key /etc/ssl/notion-kb/your-private.key;
```

---

## Monitoring & Logging

### Log Rotation

Create `/etc/logrotate.d/notion-kb-manager`:

```
/path/to/notion-kb-manager/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
    sharedscripts
    postrotate
        systemctl reload notion-kb-app > /dev/null 2>&1 || true
    endscript
}
```

### Health Check Monitoring

Use monitoring tools like:
- **Uptime Robot**: Free basic monitoring
- **Datadog**: Comprehensive monitoring
- **New Relic**: Application performance
- **Prometheus + Grafana**: Self-hosted

Example health check script:

```bash
#!/bin/bash
# health_check.sh

HEALTH_URL="https://api.yourdomain.com/api/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ "$RESPONSE" != "200" ]; then
    echo "Health check failed: HTTP $RESPONSE"
    # Send alert (email, Slack, etc.)
    exit 1
fi

echo "Health check passed"
```

### Application Metrics

Access metrics at:
- **Application logs**: `/path/to/notion-kb-manager/logs/`
- **Nginx logs**: `/var/log/nginx/notion-kb-*.log`
- **System logs**: `sudo journalctl -u notion-kb-app -f`

---

## Backup Strategy

### Automated Database Backups

Create backup script `backup_db.sh`:

```bash
#!/bin/bash
# backup_db.sh - Automated database backup

BACKUP_DIR="/path/to/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="notion_kb_prod"
DB_USER="notion_user"

# Create backup directory
mkdir -p $BACKUP_DIR

# PostgreSQL backup
pg_dump -U $DB_USER -d $DB_NAME | gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# Remove backups older than 30 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Database backup completed: db_backup_$DATE.sql.gz"
```

### Cron Job for Daily Backups

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/notion-kb-manager/backup_db.sh >> /path/to/logs/backup.log 2>&1
```

### Application Backups via API

```bash
# Create backup via API
curl -X POST https://api.yourdomain.com/api/backup/ \
    -H "Authorization: Bearer YOUR_JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"type": "auto", "include_database": true, "include_files": true}'
```

---

## Security Checklist

Before going live, verify all security measures:

### Application Security

- [ ] `FLASK_ENV=production` in .env
- [ ] `DEBUG=False` in .env
- [ ] `REQUIRE_AUTH=true` in .env
- [ ] Strong SECRET_KEY generated and set
- [ ] Strong ENCRYPTION_KEY generated and set
- [ ] Strong JWT_SECRET_KEY generated and set
- [ ] Default admin password changed
- [ ] CORS_ORIGINS configured correctly

### Infrastructure Security

- [ ] Firewall configured (only 80, 443 open)
- [ ] SSH key authentication enabled
- [ ] Root login disabled
- [ ] Fail2ban installed and configured
- [ ] UFW/iptables configured
- [ ] System updates automated

### SSL/TLS

- [ ] Valid SSL certificate installed
- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] TLS 1.2+ only
- [ ] Strong cipher suites configured
- [ ] HSTS header enabled

### Database Security

- [ ] PostgreSQL bound to localhost only
- [ ] Strong database password
- [ ] Database user has minimal privileges
- [ ] Regular backups scheduled
- [ ] Backup encryption enabled

### Redis Security

- [ ] Redis bound to localhost only
- [ ] Redis password set
- [ ] Redis maxmemory configured
- [ ] Redis persistence enabled

### Monitoring

- [ ] Health check monitoring configured
- [ ] Log rotation configured
- [ ] Alert notifications set up
- [ ] Backup verification automated

---

## Troubleshooting

### Application Won't Start

```bash
# Check logs
sudo journalctl -u notion-kb-app -n 50 --no-pager

# Verify configuration
python3 -c "from app import create_app; app = create_app('production')"

# Check environment variables
env | grep FLASK
```

### Workers Not Processing Tasks

```bash
# Check worker logs
tail -f logs/parsing-worker-1.log

# Verify Redis connection
redis-cli ping

# Check RQ queue status
rq info --url redis://localhost:6379/0
```

### Database Connection Errors

```bash
# Test database connection
psql -U notion_user -d notion_kb_prod -c "SELECT 1;"

# Check DATABASE_URL in .env
grep DATABASE_URL .env

# Verify PostgreSQL is running
sudo systemctl status postgresql
```

### Nginx Configuration Issues

```bash
# Test Nginx configuration
sudo nginx -t

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Verify proxy configuration
curl -I http://localhost:5000/api/health
```

### SSL Certificate Issues

```bash
# Test SSL configuration
openssl s_client -connect api.yourdomain.com:443 -servername api.yourdomain.com

# Verify certificate
curl -vI https://api.yourdomain.com

# Renew Let's Encrypt certificate
sudo certbot renew --force-renewal
```

### Performance Issues

```bash
# Check system resources
htop
df -h
free -m

# Check application performance
curl -w "@curl-format.txt" -o /dev/null -s https://api.yourdomain.com/api/health

# Analyze slow queries (PostgreSQL)
sudo -u postgres psql notion_kb_prod -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

---

## Next Steps

After successful deployment:

1. **Test API endpoints** - Use Swagger UI at `/api/docs`
2. **Configure monitoring** - Set up health checks and alerts
3. **Run backup** - Create initial backup and test restore
4. **Load testing** - Verify performance under load
5. **Documentation** - Document any custom configurations
6. **Team training** - Train team on operations and maintenance

For questions or issues, refer to:
- **API Documentation**: https://api.yourdomain.com/api/docs
- **GitHub Issues**: https://github.com/yourusername/notion-kb-manager/issues
- **Support Email**: support@yourdomain.com

---

**Congratulations! Your Notion KB Manager is now production-ready!** 🚀
