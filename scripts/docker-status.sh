#!/bin/bash

# Docker Status Checker for Notion KB Manager

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Notion KB Manager - System Status${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Check if containers are running
echo -e "${YELLOW}Container Status:${NC}"
docker compose ps
echo ""

# Check backend health
echo -e "${YELLOW}Backend Health:${NC}"
if curl -f http://localhost:5000/api/monitoring/health 2>/dev/null | jq '.' 2>/dev/null; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend is not responding${NC}"
fi
echo ""

# Check frontend
echo -e "${YELLOW}Frontend Status:${NC}"
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is accessible${NC}"
else
    echo -e "${RED}✗ Frontend is not responding${NC}"
fi
echo ""

# Check workers
echo -e "${YELLOW}Worker Status:${NC}"
WORKERS_RUNNING=$(docker compose ps worker-parsing worker-ai worker-notion 2>/dev/null | grep -c "Up" || echo "0")
echo "Workers running: $WORKERS_RUNNING/3"
if [ "$WORKERS_RUNNING" -eq 3 ]; then
    echo -e "${GREEN}✓ All workers are running${NC}"
else
    echo -e "${RED}✗ Some workers are down${NC}"
fi
echo ""

# Check database
echo -e "${YELLOW}Database Status:${NC}"
if docker compose exec -T postgres pg_isready -U kbuser > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not ready${NC}"
fi
echo ""

# Check Redis
echo -e "${YELLOW}Redis Status:${NC}"
if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is ready${NC}"
else
    echo -e "${RED}✗ Redis is not ready${NC}"
fi
echo ""

# Show resource usage
echo -e "${YELLOW}Resource Usage:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" kb-frontend kb-backend kb-worker-parsing kb-worker-ai kb-worker-notion kb-postgres kb-redis 2>/dev/null || echo "No containers running"
echo ""

# Show URLs
echo -e "${YELLOW}Access URLs:${NC}"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:5000"
echo "  API Docs:  http://localhost:5000/api/docs"
echo "  Health:    http://localhost:5000/api/monitoring/health"
echo ""

# Quick actions
echo -e "${YELLOW}Quick Actions:${NC}"
echo "  View logs:       ./scripts/docker-logs.sh"
echo "  Restart all:     docker compose restart"
echo "  Stop all:        docker compose down"
echo "  Rebuild:         docker compose up -d --build"
