#!/bin/bash
#
# Stop all RQ workers
#
# Usage:
#   ./scripts/stop_workers.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping RQ workers...${NC}"

# Find all rq worker processes
worker_pids=$(pgrep -f "rq worker" || true)

if [ -z "$worker_pids" ]; then
    echo -e "${YELLOW}No RQ workers found running${NC}"
    exit 0
fi

# Count workers
worker_count=$(echo "$worker_pids" | wc -l | tr -d ' ')
echo -e "${YELLOW}Found ${worker_count} RQ workers${NC}"

# Stop each worker gracefully (SIGTERM)
echo "$worker_pids" | while read -r pid; do
    echo -e "${YELLOW}Stopping worker (PID: ${pid})...${NC}"
    kill -TERM "$pid" 2>/dev/null || true
done

# Wait for graceful shutdown (max 10 seconds)
echo -e "${YELLOW}Waiting for workers to shut down gracefully...${NC}"
sleep 3

# Check if any workers are still running
remaining_pids=$(pgrep -f "rq worker" || true)

if [ -n "$remaining_pids" ]; then
    echo -e "${YELLOW}Some workers did not stop gracefully, forcing shutdown...${NC}"
    echo "$remaining_pids" | while read -r pid; do
        echo -e "${RED}Force stopping worker (PID: ${pid})${NC}"
        kill -KILL "$pid" 2>/dev/null || true
    done
fi

echo -e "${GREEN}✓ All RQ workers stopped${NC}"
