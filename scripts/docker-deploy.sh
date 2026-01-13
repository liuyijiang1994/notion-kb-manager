#!/bin/bash

# Docker Deployment Script for Notion KB Manager

set -e

echo "========================================="
echo "Notion KB Manager - Docker Deployment"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not available${NC}"
    echo "Please update Docker Desktop to the latest version"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed${NC}"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ No .env file found${NC}"
    echo "Creating .env from .env.docker..."
    cp .env.docker .env
    echo -e "${YELLOW}Please edit .env and add your API keys:${NC}"
    echo "  - NOTION_API_KEY"
    echo "  - OPENAI_API_KEY"
    echo ""
    read -p "Press Enter to continue after editing .env, or Ctrl+C to exit..."
fi

# Stop any existing containers
echo "Stopping existing containers..."
docker compose down 2>/dev/null || true
echo ""

# Build and start services
echo "Building Docker images..."
echo "This may take 5-10 minutes on first run..."
docker compose build --no-cache

echo ""
echo "Starting services..."
docker compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check if backend is healthy
echo "Checking backend health..."
for i in {1..30}; do
    if curl -f http://localhost:5000/api/monitoring/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is healthy${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Backend failed to start${NC}"
        echo "Check logs: docker compose logs backend"
        exit 1
    fi
    sleep 2
done

echo ""
echo "Running database migrations..."
docker compose exec -T backend flask db upgrade

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Services running:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:5000"
echo "  API Docs:  http://localhost:5000/api/docs"
echo ""
echo "Default login:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "Useful commands:"
echo "  View logs:     docker compose logs -f"
echo "  Stop services: docker compose down"
echo "  Restart:       docker compose restart"
echo "  Shell access:  docker compose exec backend bash"
echo ""
echo -e "${YELLOW}Note: First build may take 5-10 minutes${NC}"
