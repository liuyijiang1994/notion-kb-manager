# Notion Knowledge Base Manager

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/typescript-5.9-3178c6.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Production Ready](https://img.shields.io/badge/status-production--ready-brightgreen.svg)]()

A production-ready full-stack application for managing knowledge base content with automated Notion integration. Features a modern React dashboard for real-time monitoring, content management, and AI-powered processing with seamless Notion integration.

## 🌟 Features

### Content Management
- ✅ **Bulk URL Import** - Import multiple URLs with validation and deduplication
- ✅ **Content Parsing** - Extract titles, text, images, and metadata from web pages
- ✅ **AI Processing** - Automatic summarization, categorization, and sentiment analysis
- ✅ **Notion Integration** - Seamless import to Notion databases with rich formatting

### Async Task Processing
- ✅ **Background Workers** - Redis Queue (RQ) with 3 specialized queues
- ✅ **Task Management** - Complete lifecycle tracking (pending → running → completed)
- ✅ **Retry Logic** - Automatic retry with exponential backoff
- ✅ **Real-time Monitoring** - Live dashboard and API endpoints

### Security & Production Features
- ✅ **JWT Authentication** - Role-based access control for protected endpoints
- ✅ **Rate Limiting** - Redis-based per-endpoint rate limits
- ✅ **Security Headers** - CSP, HSTS, X-Frame-Options, XSS protection
- ✅ **Input Sanitization** - Multi-layer defense against injection attacks
- ✅ **Encryption** - Fernet encryption for sensitive credentials

### Monitoring & Observability
- ✅ **Prometheus Metrics** - Request, task, queue, and system metrics
- ✅ **Health Checks** - Kubernetes-compatible readiness/liveness probes
- ✅ **Comprehensive Logging** - Structured logs with rotation
- ✅ **Performance Optimization** - 20+ database indexes, query optimization

### Frontend Dashboard
- ✅ **Modern React UI** - TypeScript + Vite + Tailwind CSS v4
- ✅ **Real-time Monitoring** - Live system health and task status
- ✅ **Task Management** - Browse, filter, and manage tasks
- ✅ **JWT Authentication** - Secure login with session persistence
- ✅ **Responsive Design** - Mobile-friendly, accessible interface

### Documentation
- ✅ **OpenAPI 3.0 Spec** - Interactive Swagger UI at `/api/docs`
- ✅ **Deployment Guide** - Complete production deployment instructions
- ✅ **Configuration Guide** - All environment variables documented
- ✅ **API Documentation** - 50+ endpoints with examples

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                       │
│   TypeScript + Vite + Tailwind CSS + React Query       │
│   - Dashboard (Real-time monitoring)                   │
│   - Task Management                                    │
│   - Authentication (JWT)                               │
└────────────────┬────────────────────────────────────────┘
                 │ REST API
┌────────────────▼────────────────────────────────────────┐
│               Flask API Server                         │
│   JWT Auth + Rate Limiting + Security Headers         │
└────────────────┬────────────────────────────────────────┘
                 │
      ┌──────────┼──────────┐
      ▼          ▼          ▼
┌──────────┐ ┌────────┐ ┌────────────┐
│PostgreSQL│ │ Redis  │ │ RQ Workers │
│  SQLite  │ │ Queue  │ │ (3 queues) │
└──────────┘ └────────┘ └─────┬──────┘
                              │
                   ┌──────────┼──────────┐
                   ▼          ▼          ▼
              ┌─────────┐ ┌──────┐ ┌────────┐
              │ OpenAI  │ │Notion│ │External│
              │   API   │ │ API  │ │Content │
              └─────────┘ └──────┘ └────────┘
```

**Components:**
- **React Frontend** - Modern dashboard with real-time monitoring
- **Flask API Server** - RESTful API with JWT authentication
- **Redis Queue** - Async task processing with 3 specialized queues
- **RQ Workers** - Background processing (parsing, AI, Notion)
- **PostgreSQL/SQLite** - Persistent storage with optimized indexes

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Redis 6.0+
- PostgreSQL 13+ (or SQLite for development)
- OpenAI API key
- Notion API key (optional)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/notion-kb-manager.git
cd notion-kb-manager

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 5. Initialize database
flask db upgrade

# 6. Start Redis
redis-server

# 7. Start workers
python scripts/start_workers.py

# 8. Start API server
python run.py

# 9. Setup frontend (new terminal)
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Access the Application

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Documentation**: http://localhost:5000/api/docs

**Default Login Credentials:**
```
Username: admin
Password: admin123
```

### First API Request

```bash
# Import URLs
curl -X POST http://localhost:5000/api/links/import \
  -H "Content-Type: application/json" \
  -d '{
    "links": [
      {"url": "https://example.com/article", "title": "Example Article"}
    ]
  }'

# Check API documentation
open http://localhost:5000/api/docs
```

## 📖 Documentation

### Core Documentation
- **[Project Summary](docs/PROJECT_SUMMARY.md)** - Complete project overview
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Production deployment (Docker, systemd, K8s)
- **[Configuration Guide](docs/CONFIGURATION_GUIDE.md)** - Environment variables and settings
- **[API Documentation](http://localhost:5000/api/docs)** - Interactive Swagger UI

### Frontend
- **[Frontend README](frontend/README.md)** - Frontend quick start and features
- **[Phase 9 Completion](docs/PHASE_9_FRONTEND_COMPLETION.md)** - Frontend implementation details

### Async System
- **[Async System Guide](docs/ASYNC_SYSTEM_GUIDE.md)** - Complete RQ worker documentation
- **[Async Quick Start](README_ASYNC.md)** - TL;DR for async task system
- **[Async Summary](docs/ASYNC_SYSTEM_SUMMARY.md)** - Overview of async components

### Phase Documentation
- **[Phase 8: Backend Completion](docs/PHASE_8_COMPLETION_SUMMARY.md)** - Production readiness details
- **[Phase 9: Frontend Completion](docs/PHASE_9_FRONTEND_COMPLETION.md)** - Frontend dashboard implementation

## 🛠️ Management Scripts

### Worker Management

```bash
# Start all workers (3 parsing, 2 AI, 2 Notion)
python scripts/start_workers.py

# Start specific queue with custom worker count
python scripts/start_workers.py --queue parsing --workers 5

# Show worker and queue statistics
python scripts/start_workers.py --stats
```

### System Testing

```bash
# Test async task system (6 tests)
python scripts/test_async_system.py

# Test output:
# ✓ Redis connection
# ✓ Queue creation
# ✓ Worker availability
# ✓ Job enqueueing
# ✓ Background task service
# ✓ Queue statistics
```

### Monitoring

```bash
# Real-time monitoring dashboard
python scripts/monitor_async.py

# Single snapshot
python scripts/monitor_async.py --once

# JSON output (for integrations)
python scripts/monitor_async.py --json
```

## 📊 API Endpoints

### Content Management
- `POST /api/links/import` - Import URLs
- `GET /api/links` - List imported links
- `POST /api/parsing/sync` - Parse content
- `POST /api/ai/process` - AI processing
- `POST /api/notion/import` - Import to Notion

### Task Management
- `GET /api/tasks/history` - List all tasks
- `GET /api/tasks/history/{id}` - Get task status
- `POST /api/tasks/history/{id}/retry` - Retry failed items
- `POST /api/tasks/history/{id}/rerun` - Clone and rerun task
- `DELETE /api/tasks/history/{id}` - Cancel task

### Monitoring
- `GET /api/monitoring/workers` - Worker status
- `GET /api/monitoring/queues` - Queue statistics
- `GET /api/monitoring/health` - Basic health check
- `GET /api/monitoring/health/detailed` - Comprehensive health
- `GET /api/monitoring/metrics` - Prometheus metrics

### Configuration
- `GET /api/config/models` - List AI models
- `POST /api/config/models` - Create AI model
- `GET /api/config/notion` - Notion configuration
- `POST /api/config/notion` - Update Notion config

### Backup & Restore
- `POST /api/backup` - Create backup
- `GET /api/backup` - List backups
- `POST /api/backup/{id}/restore` - Restore from backup
- `DELETE /api/backup/{id}` - Delete backup

**Full API documentation:** http://localhost:5000/api/docs

## 🔧 Configuration

### Environment Variables

```bash
# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://user:pass@localhost/notion_kb
# Or SQLite: DATABASE_URL=sqlite:///data/notion_kb.db

# Redis
REDIS_URL=redis://localhost:6379/0

# Notion API
NOTION_API_KEY=your-notion-api-key
NOTION_DATABASE_ID=your-database-id

# JWT Authentication
JWT_SECRET_KEY=your-jwt-secret
REQUIRE_AUTH=false  # Set true in production

# AI Configuration
OPENAI_API_KEY=your-openai-key
DEFAULT_AI_MODEL=gpt-3.5-turbo

# Worker Configuration
WORKER_COUNT_PARSING=3
WORKER_COUNT_AI=2
WORKER_COUNT_NOTION=2

# Monitoring
PROMETHEUS_ENABLED=true
```

See [Configuration Guide](docs/CONFIGURATION_GUIDE.md) for complete reference.

## 🔒 Security Features

### Authentication
- JWT token-based authentication
- Role-based access control (admin, user)
- API key support for programmatic access
- Configurable token expiration

### Rate Limiting
- Per-endpoint rate limits
- Redis-based storage
- Configurable thresholds
- Graceful error responses

### Input Validation
- Multi-layer sanitization
- XSS prevention (HTML escaping)
- SQL injection prevention
- Path traversal prevention
- SSRF prevention (URL validation)

### Security Headers
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options: SAMEORIGIN
- X-Content-Type-Options: nosniff
- X-XSS-Protection

## 📈 Monitoring & Metrics

### Prometheus Metrics

```bash
# Expose metrics for Prometheus scraping
curl http://localhost:5000/api/monitoring/metrics
```

**Metrics available:**
- `api_requests_total` - Total API requests (by method, endpoint, status)
- `api_request_duration_seconds` - Request duration histogram
- `task_duration_seconds` - Task execution time (by type, status)
- `queue_size` - Current queue sizes
- `db_connections_active` - Database connection pool
- `redis_memory_used_bytes` - Redis memory usage
- `system_cpu_percent` - CPU usage
- `system_memory_used_bytes` - Memory usage

### Health Checks

```bash
# Basic health
curl http://localhost:5000/api/monitoring/health

# Comprehensive health (all components)
curl http://localhost:5000/api/monitoring/health/detailed

# Kubernetes readiness probe
curl http://localhost:5000/api/monitoring/health/ready

# Kubernetes liveness probe
curl http://localhost:5000/api/monitoring/health/alive
```

### Real-time Dashboard

```bash
# Live monitoring (updates every 2 seconds)
python scripts/monitor_async.py
```

Dashboard shows:
- Redis status and memory usage
- Queue sizes (pending, running, failed)
- Worker status (idle, busy, suspended)
- Overall system health

## 🚢 Production Deployment

### Docker Compose

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Gunicorn (Production WSGI Server)

```bash
# Start with 4 workers
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app('production')"
```

### systemd (Linux Service)

```bash
# Copy service file
sudo cp deploy/notion-kb-manager.service /etc/systemd/system/

# Enable and start
sudo systemctl enable notion-kb-manager
sudo systemctl start notion-kb-manager

# Check status
sudo systemctl status notion-kb-manager
```

### Kubernetes

See [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) for complete Kubernetes manifests.

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test suite
pytest tests/integration/ -v        # Integration tests
pytest tests/security/ -v           # Security tests
pytest tests/unit/ -v               # Unit tests

# Test async system
python scripts/test_async_system.py
```

**Test Coverage:**
- Unit tests: Core functionality
- Integration tests: E2E workflows, concurrent operations
- Security tests: OWASP Top 10 vulnerabilities
- Performance tests: Query optimization, load testing

## 📦 Project Structure

```
notion-kb-manager/
├── app/
│   ├── api/                    # API route handlers
│   ├── models/                 # SQLAlchemy models
│   ├── services/               # Business logic
│   ├── middleware/             # Auth, rate limiting, security
│   ├── utils/                  # Utilities and helpers
│   └── workers/                # RQ worker functions
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── api/                # API client layer
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── store/              # Zustand state management
│   │   └── hooks/              # Custom hooks
│   ├── Dockerfile              # Frontend Docker image
│   ├── nginx.conf              # Nginx configuration
│   └── package.json            # Node dependencies
├── config/                     # Configuration files
├── tests/                      # Test suites
├── scripts/                    # Management scripts
│   ├── start_workers.py        # Worker management
│   ├── test_async_system.py   # System tests
│   └── monitor_async.py        # Monitoring dashboard
├── docs/                       # Documentation
│   ├── PROJECT_SUMMARY.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── CONFIGURATION_GUIDE.md
│   ├── ASYNC_SYSTEM_GUIDE.md
│   ├── PHASE_8_COMPLETION_SUMMARY.md
│   └── PHASE_9_FRONTEND_COMPLETION.md
├── migrations/                 # Database migrations
├── data/                       # SQLite database (dev)
├── logs/                       # Application logs
├── backups/                    # Database backups
├── docker-compose.yml          # Docker orchestration
├── Dockerfile.backend          # Backend Docker image
└── requirements.txt            # Python dependencies
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

### Backend
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Redis Queue (RQ)](https://python-rq.org/) - Async task processing
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [Notion API](https://developers.notion.com/) - Notion integration
- [OpenAI API](https://platform.openai.com/) - AI processing

### Frontend
- [React](https://react.dev/) - UI library
- [TypeScript](https://www.typescriptlang.org/) - Type safety
- [Vite](https://vitejs.dev/) - Build tool
- [Tailwind CSS](https://tailwindcss.com/) - Styling framework
- [React Query](https://tanstack.com/query) - Server state management
- [Zustand](https://zustand-demo.pmnd.rs/) - Client state management

## 📞 Support

- **Documentation:** [docs/](docs/)
- **Issues:** [GitHub Issues](https://github.com/yourusername/notion-kb-manager/issues)
- **API Docs:** http://localhost:5000/api/docs

## 🗺️ Roadmap

### Completed (Phase 1-9) ✅
- ✅ Content import and parsing
- ✅ AI processing integration
- ✅ Notion database integration
- ✅ Async task processing with Redis/RQ
- ✅ Task management system
- ✅ Security hardening (JWT, rate limiting, sanitization)
- ✅ Production monitoring (Prometheus, health checks)
- ✅ Complete API documentation (OpenAPI/Swagger)
- ✅ React dashboard with real-time monitoring
- ✅ Frontend task management UI
- ✅ Docker deployment support

### Future Enhancements (Phase 10+)
- 🔲 Content browser with advanced search
- 🔲 Settings/configuration panel UI
- 🔲 Advanced analytics and charts
- 🔲 WebSocket real-time updates
- 🔲 Webhook notifications
- 🔲 Multi-tenancy support
- 🔲 GraphQL API
- 🔲 Progressive Web App (PWA)
- 🔲 Mobile apps (iOS, Android)
- 🔲 Enterprise features (SSO, audit logging, compliance)

---

**Version:** 1.0.0
**Status:** ✅ Production Ready
**Last Updated:** 2026-01-13

Made with ❤️ by the Notion KB Manager Team
