# Architecture Diagrams

This directory contains comprehensive visual architecture diagrams for the Notion KB Manager project. All diagrams use Mermaid syntax for easy rendering in Markdown viewers.

## Diagram Index

### 1. [System Architecture](./01_system_architecture.md)
**Purpose**: Overview of the entire system architecture

**Contains**:
- Overall system architecture with frontend, backend, and external services
- Technology stack details for frontend and backend
- Deployment architecture (production environment)
- Security architecture and protection measures
- Data flow overview
- Component communication patterns

**Best For**: Understanding the high-level system design, technology choices, and how components communicate

---

### 2. [Database Schema](./02_database_schema.md)
**Purpose**: Complete database design and entity relationships

**Contains**:
- Entity Relationship Diagram (ERD) with all 16 tables
- Detailed table specifications with columns, types, and descriptions
- Indexes and foreign key relationships
- Database migration strategy
- Data relationships and flow
- Optimization considerations (indexes, partitioning, archival)

**Best For**: Understanding data models, relationships, and database implementation

---

### 3. [API Architecture](./03_api_architecture.md)
**Purpose**: Complete API specifications and communication patterns

**Contains**:
- API endpoint overview diagram
- All 100+ REST API endpoints organized by module
- Request/response formats with examples
- WebSocket events specification
- Error codes and rate limiting
- Authentication methods

**Best For**: API development, frontend-backend integration, understanding request/response contracts

---

### 4. [Module Relationships](./04_module_relationships.md)
**Purpose**: Internal module dependencies and interactions

**Contains**:
- Backend service dependency graph
- Frontend component hierarchy
- Service layer architecture
- Data flow sequence diagrams
- Module dependency matrix
- Cross-module communication patterns
- Service lifecycle and error handling flows
- Scalability architecture
- Testing strategy by module type
- Development order recommendations

**Best For**: Understanding internal architecture, service dependencies, development planning

---

### 5. [User Flow](./05_user_flow.md)
**Purpose**: User interaction and workflow diagrams

**Contains**:
- Overall user journey from onboarding to all features
- Detailed flows for:
  - Configuration setup
  - Link import process
  - Content parsing & AI processing
  - Notion import
- User interaction patterns
- Mobile responsiveness
- Accessibility features
- Feedback collection points

**Best For**: UI/UX design, understanding user workflows, feature implementation planning

---

## How to View Diagrams

### Option 1: GitHub (Recommended)
Push the repository to GitHub. GitHub automatically renders Mermaid diagrams in Markdown files.

### Option 2: VS Code with Mermaid Extension
1. Install "Markdown Preview Mermaid Support" extension
2. Open any diagram file
3. Press `Ctrl+Shift+V` (or `Cmd+Shift+V` on Mac) to preview

### Option 3: Mermaid Live Editor
1. Copy the Mermaid code from any diagram
2. Go to https://mermaid.live
3. Paste and view/edit the diagram

### Option 4: Documentation Site
Use tools like:
- **MkDocs** with Mermaid plugin
- **Docusaurus** with Mermaid support
- **GitBook** with Mermaid integration

## Diagram Navigation Guide

### For Different Roles

**Product Managers / Stakeholders**
- Start with: User Flow → System Architecture
- Focus on: Understanding features, user journey, and system capabilities

**Frontend Developers**
- Start with: User Flow → API Architecture → Module Relationships
- Focus on: Component hierarchy, API endpoints, state management

**Backend Developers**
- Start with: Database Schema → API Architecture → Module Relationships
- Focus on: Data models, service architecture, API implementation

**DevOps Engineers**
- Start with: System Architecture → Module Relationships
- Focus on: Deployment architecture, scalability, infrastructure

**Full-Stack Developers**
- Review all diagrams in order
- Focus on: Complete system understanding, integration points

### By Development Phase

**Phase 0: Project Foundation**
- Database Schema (all tables)
- API Architecture (endpoint contracts)
- Module Relationships (service dependencies)

**Phase 1-7: Feature Development**
- User Flow (feature-specific flows)
- API Architecture (module-specific endpoints)
- Module Relationships (service interactions)

**Phase 8: Integration & Deployment**
- System Architecture (deployment setup)
- Module Relationships (scalability patterns)

## Diagram Maintenance

### When to Update Diagrams

**Add New Feature**
- Update User Flow with new user journey
- Add API endpoints to API Architecture
- Update Module Relationships if new services added

**Modify Database**
- Update Database Schema ERD
- Update table specifications
- Adjust relationships

**Change Architecture**
- Update System Architecture
- Modify deployment diagrams
- Adjust service dependencies in Module Relationships

**API Changes**
- Update endpoint specifications
- Modify request/response examples
- Add new error codes

### Diagram Version Control
- Diagrams are stored in Git alongside code
- Update diagrams in the same PR as implementation
- Use meaningful commit messages for diagram changes
- Tag major architecture changes

## Related Documentation

- [Development Plan](../DEVELOPMENT_PLAN.md) - Detailed 15-week implementation plan
- [API Documentation](../api/) - (To be generated with Swagger/OpenAPI)
- [User Manual](../user-manual/) - (To be created)
- [Deployment Guide](../deployment/) - (To be created)

## Diagram Legend

### Colors Used in Diagrams

```
🟦 Blue (#90caf9)     - API/HTTP layers, routing, external communication
🟩 Green (#a5d6a7)    - Services, business logic, success states
🟨 Yellow (#fff59d)   - Data storage, state management, dashboards
🟧 Orange (#ffcc80)   - External services, cache, warnings
🟪 Purple (#e1bee7)   - UI components, user interactions
🟥 Red (#ffcdd2)      - Errors, failures, critical states
```

### Common Diagram Shapes

- **Rectangles**: Components, services, pages
- **Rounded Rectangles**: Start/end points, key actions
- **Diamonds**: Decision points, conditionals
- **Cylinders**: Databases, data storage
- **Clouds**: External services
- **Parallel lines**: Subgraphs, grouped components

## Questions or Issues?

If you find any diagrams unclear, incomplete, or incorrect:
1. Open an issue in the project repository
2. Provide specific feedback on which diagram and section
3. Suggest improvements if possible

## Export Options

### Generate PNG/SVG from Mermaid
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Convert to PNG
mmdc -i diagram.md -o diagram.png

# Convert to SVG
mmdc -i diagram.md -o diagram.svg -b transparent
```

### Generate PDF Documentation
```bash
# Using pandoc
pandoc *.md -o architecture-diagrams.pdf

# Or use print-to-PDF in browser after rendering
```

---

**Last Updated**: 2024-01-12
**Maintainer**: Development Team
**Status**: Initial Version
