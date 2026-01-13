# Notion KB Manager - Frontend Dashboard

Modern React + TypeScript frontend for the Notion Knowledge Base Manager.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

Access at: **http://localhost:3000**

## 📋 Prerequisites

- Node.js 18+
- Backend API running on http://localhost:5000
- Redis and RQ workers for full functionality

## 🏗️ Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS v4** - Styling
- **React Router v7** - Routing
- **React Query** - Server state
- **Zustand** - Client state
- **Axios** - HTTP client
- **Lucide React** - Icons
- **date-fns** - Date formatting

## 🎨 Features

### ✅ Authentication
- JWT token-based auth
- Automatic token management
- Protected routes
- Persistent sessions

### ✅ System Dashboard
- Real-time health monitoring
- System statistics
- Queue status visualization
- Auto-refresh every 5 seconds

### ✅ Task Management
- Task list with filtering
- Real-time updates
- Progress tracking
- Status indicators

## 🔐 Default Credentials

```
Username: admin
Password: admin123
```

## 📁 Project Structure

```
src/
├── api/              # API client layer
├── components/       # React components
│   ├── common/       # Reusable components
│   ├── layout/       # Header, Sidebar
│   ├── dashboard/    # Dashboard components
│   └── tasks/        # Task components
├── hooks/            # Custom hooks
├── pages/            # Page components
├── store/            # State management
└── App.tsx           # Root component
```

## 🚦 Routes

| Path | Component | Auth | Description |
|------|-----------|------|-------------|
| `/` | → Dashboard | ✅ | Redirect |
| `/login` | LoginPage | ❌ | Login form |
| `/dashboard` | DashboardPage | ✅ | System overview |
| `/tasks` | TasksPage | ✅ | Task management |
| `/content` | Placeholder | ✅ | Coming soon |
| `/settings` | Placeholder | ✅ | Coming soon |

## 🧪 Development

### Running the Full Stack

```bash
# Terminal 1: Backend API
cd /Users/peco/Workspace/notion-kb-manager
python run.py

# Terminal 2: Workers
python scripts/start_workers.py

# Terminal 3: Frontend
cd frontend
npm run dev
```

### Build Commands

```bash
npm run dev      # Dev server with HMR
npm run build    # Production build
npm run preview  # Preview build
npm run lint     # ESLint
```

## 📦 Build Output

```
dist/
├── index.html
└── assets/
    ├── index-[hash].js   # ~340KB (110KB gzipped)
    └── index-[hash].css  # ~22KB (5KB gzipped)
```

## 🎯 Phase 9 Status

**✅ Completed:**
- Project setup with Vite + React + TypeScript
- Tailwind CSS v4 configuration
- API client with Axios interceptors
- TypeScript types for all API responses
- Authentication with JWT and Zustand
- Protected routes
- Layout components (Header, Sidebar)
- Dashboard with real-time monitoring
- Task management interface
- Login page with form validation
- Routing with React Router v7
- Production build optimization

**🔲 Future Enhancements (Phase 10+):**
- Content browser and search
- Settings/configuration panel
- Task detail modal
- Retry/cancel task actions
- Charts and analytics
- Dark mode toggle
- WebSocket real-time updates
- Toast notifications

## 📝 Configuration

Create `.env`:

```bash
VITE_API_BASE_URL=http://localhost:5000
```

Vite proxy is pre-configured to forward `/api` to backend.

---

**Version:** 1.0.0
**Status:** ✅ Production Ready
**Last Updated:** 2026-01-13
