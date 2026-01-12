# System Architecture Diagram

## Overall System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
        WS_Client[WebSocket Client]
    end

    subgraph "Frontend - Web Application"
        UI[UI Components<br/>React/Vue]
        State[State Management<br/>Redux/Vuex]
        API_Client[API Client<br/>Axios]
        WS_Handler[WebSocket Handler]
        Charts[Chart Library<br/>ECharts]
    end

    subgraph "Backend - Python Flask"
        subgraph "API Layer"
            REST[REST API<br/>Flask Routes]
            WS_Server[WebSocket Server<br/>Flask-SocketIO]
            Auth[Authentication<br/>Middleware]
        end

        subgraph "Service Layer"
            ConfigSvc[Config Service]
            LinkSvc[Link Service]
            ParseSvc[Parsing Service]
            AISvc[AI Service]
            NotionSvc[Notion Service]
            TaskSvc[Task Service]
            StatsSvc[Statistics Service]
            BackupSvc[Backup Service]
        end

        subgraph "Data Layer"
            ORM[SQLAlchemy ORM]
            Cache[Cache Layer<br/>Optional Redis]
            FileStore[File Storage<br/>Local/S3]
        end

        subgraph "Background Workers"
            TaskQueue[Task Queue<br/>Threading/Celery]
            Scheduler[Task Scheduler<br/>APScheduler]
        end
    end

    subgraph "External Services"
        OpenAI[OpenAI API<br/>GPT-4]
        Claude[Anthropic API<br/>Claude]
        OtherLLM[Other LLM APIs]
        NotionAPI[Notion API]
        ArxivAPI[arXiv API]
    end

    subgraph "Data Storage"
        DB[(Database<br/>SQLite/PostgreSQL)]
        Files[File System<br/>Cache/Uploads/Backups]
    end

    Browser --> UI
    Browser --> WS_Client
    UI --> State
    UI --> API_Client
    WS_Client --> WS_Handler
    State --> API_Client

    API_Client --> REST
    WS_Handler --> WS_Server

    REST --> Auth
    Auth --> ConfigSvc
    Auth --> LinkSvc
    Auth --> ParseSvc
    Auth --> AISvc
    Auth --> NotionSvc
    Auth --> TaskSvc
    Auth --> StatsSvc
    Auth --> BackupSvc

    ConfigSvc --> ORM
    LinkSvc --> ORM
    ParseSvc --> ORM
    AISvc --> ORM
    NotionSvc --> ORM
    TaskSvc --> ORM
    StatsSvc --> ORM
    BackupSvc --> FileStore

    ORM --> DB
    ORM --> Cache

    TaskQueue --> ParseSvc
    TaskQueue --> AISvc
    TaskQueue --> NotionSvc
    Scheduler --> BackupSvc

    WS_Server --> TaskQueue

    AISvc --> OpenAI
    AISvc --> Claude
    AISvc --> OtherLLM
    NotionSvc --> NotionAPI
    ParseSvc --> ArxivAPI

    BackupSvc --> Files
    ParseSvc --> Files

    Charts --> State

    style Browser fill:#e1f5ff
    style UI fill:#bbdefb
    style REST fill:#c8e6c9
    style DB fill:#fff9c4
    style OpenAI fill:#ffccbc
    style NotionAPI fill:#ffccbc
```

## Technology Stack Details

### Frontend Stack
- **Framework**: React (v18+) or Vue 3
- **State Management**: Redux Toolkit / Pinia
- **HTTP Client**: Axios
- **WebSocket**: Socket.IO Client
- **Charts**: Apache ECharts
- **UI Components**: Material-UI / Ant Design / Custom
- **Build Tool**: Vite / Webpack
- **Styling**: CSS Modules / Styled Components / Tailwind CSS

### Backend Stack
- **Framework**: Flask 3.0
- **ORM**: SQLAlchemy 2.0
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **WebSocket**: Flask-SocketIO
- **Task Queue**: Python Threading / Celery (optional)
- **Scheduler**: APScheduler
- **Encryption**: cryptography (Fernet)
- **HTTP Client**: requests
- **Parsing**: BeautifulSoup4, PyPDF2, pdfplumber
- **OCR**: pytesseract
- **API Clients**:
  - notion-client (Notion)
  - openai (OpenAI)
  - anthropic (Claude)
  - arxiv (arXiv)

### Infrastructure
- **Web Server**: Nginx (reverse proxy)
- **WSGI Server**: Gunicorn
- **Process Manager**: Supervisor / systemd
- **Containerization**: Docker + Docker Compose
- **Cache**: Redis (optional)
- **Storage**: Local filesystem / AWS S3 (optional)

## Deployment Architecture

```mermaid
graph TB
    subgraph "Production Environment"
        LB[Load Balancer<br/>Nginx]

        subgraph "Application Servers"
            App1[Flask App Instance 1<br/>Gunicorn]
            App2[Flask App Instance 2<br/>Gunicorn]
        end

        subgraph "Worker Nodes"
            Worker1[Background Worker 1]
            Worker2[Background Worker 2]
        end

        subgraph "Data Layer"
            PG[(PostgreSQL<br/>Primary)]
            Redis[(Redis<br/>Cache/Queue)]
            S3[S3 Bucket<br/>File Storage]
        end

        Monitor[Monitoring<br/>Prometheus/Grafana]
    end

    Users[Users] --> LB
    LB --> App1
    LB --> App2

    App1 --> PG
    App2 --> PG
    App1 --> Redis
    App2 --> Redis
    App1 --> S3
    App2 --> S3

    Worker1 --> PG
    Worker2 --> PG
    Worker1 --> Redis
    Worker2 --> Redis
    Worker1 --> S3
    Worker2 --> S3

    App1 --> Monitor
    App2 --> Monitor
    Worker1 --> Monitor
    Worker2 --> Monitor

    style LB fill:#90caf9
    style App1 fill:#a5d6a7
    style App2 fill:#a5d6a7
    style PG fill:#fff59d
    style Redis fill:#ffab91
```

## Security Architecture

```mermaid
graph LR
    subgraph "Security Layers"
        Input[User Input] --> Validation[Input Validation<br/>& Sanitization]
        Validation --> Auth[Authentication<br/>JWT/Session]
        Auth --> Authz[Authorization<br/>Role-Based]
        Authz --> Encryption[Data Encryption<br/>at Rest]
        Encryption --> Secure[Secure Communication<br/>HTTPS/WSS]
    end

    subgraph "Protection Measures"
        RateLimit[Rate Limiting]
        CORS[CORS Policy]
        CSP[Content Security Policy]
        XSS[XSS Prevention]
        CSRF[CSRF Protection]
        SQL[SQL Injection Prevention]
    end

    Validation --> RateLimit
    Auth --> CORS
    Authz --> CSP
    Secure --> XSS
    Secure --> CSRF
    Encryption --> SQL

    style Validation fill:#c5e1a5
    style Auth fill:#90caf9
    style Encryption fill:#ffcc80
```

## Data Flow Overview

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Service
    participant Database
    participant External

    User->>Frontend: Interact with UI
    Frontend->>API: HTTP Request
    API->>API: Validate & Authenticate
    API->>Service: Call Business Logic
    Service->>Database: Query/Update Data
    Database-->>Service: Return Data
    Service->>External: Call External API
    External-->>Service: Return Response
    Service-->>API: Return Result
    API-->>Frontend: JSON Response
    Frontend-->>User: Update UI

    Note over Service,Database: Background Task
    Service->>Database: Start Async Task
    Service-->>API: Task Started
    Service->>External: Process Data
    Service->>Database: Update Progress
    Database-->>Frontend: WebSocket Push
    Frontend-->>User: Real-time Update
```

## Component Communication

```mermaid
graph LR
    subgraph "Frontend Components"
        Page[Page Component]
        Panel[Panel Component]
        Form[Form Component]
        Table[Table Component]
    end

    subgraph "State Management"
        Store[Global Store]
        Actions[Actions]
        Mutations[Mutations/Reducers]
    end

    subgraph "API Communication"
        HTTP[HTTP Client]
        WS[WebSocket Client]
    end

    Page --> Panel
    Panel --> Form
    Panel --> Table

    Form --> Actions
    Table --> Actions
    Actions --> HTTP
    Actions --> WS

    HTTP --> Store
    WS --> Store
    Store --> Mutations
    Mutations --> Page

    style Page fill:#e1bee7
    style Store fill:#fff59d
    style HTTP fill:#90caf9
```
