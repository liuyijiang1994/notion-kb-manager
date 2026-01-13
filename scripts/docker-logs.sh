#!/bin/bash

# Docker Logs Viewer for Notion KB Manager

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Notion KB Manager - Logs Viewer${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Parse arguments
SERVICE=$1

if [ -z "$SERVICE" ]; then
    echo "Available services:"
    echo "  1) all        - All services"
    echo "  2) frontend   - React frontend"
    echo "  3) backend    - Flask API"
    echo "  4) workers    - All RQ workers"
    echo "  5) parsing    - Parsing worker"
    echo "  6) ai         - AI worker"
    echo "  7) notion     - Notion worker"
    echo "  8) postgres   - PostgreSQL database"
    echo "  9) redis      - Redis cache/queue"
    echo ""
    read -p "Select service (1-9): " choice

    case $choice in
        1) SERVICE="all" ;;
        2) SERVICE="frontend" ;;
        3) SERVICE="backend" ;;
        4) SERVICE="worker-parsing worker-ai worker-notion" ;;
        5) SERVICE="worker-parsing" ;;
        6) SERVICE="worker-ai" ;;
        7) SERVICE="worker-notion" ;;
        8) SERVICE="postgres" ;;
        9) SERVICE="redis" ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac
fi

echo ""
echo -e "${GREEN}Viewing logs for: $SERVICE${NC}"
echo -e "${YELLOW}Press Ctrl+C to exit${NC}"
echo ""

if [ "$SERVICE" = "all" ]; then
    docker compose logs -f
else
    docker compose logs -f $SERVICE
fi
