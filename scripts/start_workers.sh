#!/bin/bash
#
# Start RQ workers for background task processing
#
# Usage:
#   ./scripts/start_workers.sh              # Start all workers
#   ./scripts/start_workers.sh parsing      # Start only parsing workers
#   ./scripts/start_workers.sh ai           # Start only AI workers
#   ./scripts/start_workers.sh notion       # Start only Notion workers
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Load environment variables
if [ -f .env ]; then
    echo -e "${GREEN}Loading environment variables from .env${NC}"
    set -a
    source .env
    set +a
else
    echo -e "${YELLOW}Warning: .env file not found${NC}"
fi

# Check if Redis is running
check_redis() {
    echo -e "${YELLOW}Checking Redis connection...${NC}"
    if redis-cli -u "${REDIS_URL:-redis://localhost:6379/0}" ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Redis is running${NC}"
        return 0
    else
        echo -e "${RED}✗ Redis is not running${NC}"
        echo -e "${YELLOW}Start Redis with: brew services start redis${NC}"
        return 1
    fi
}

# Start workers for a specific queue
start_queue_workers() {
    local queue_name=$1
    local worker_count=$2
    local queue_display_name=$3

    echo -e "${GREEN}Starting ${worker_count} workers for ${queue_display_name}...${NC}"

    for i in $(seq 1 $worker_count); do
        rq worker "$queue_name" \
            --name "${queue_name}-worker-${i}" \
            --with-scheduler \
            >> "logs/worker-${queue_name}-${i}.log" 2>&1 &

        worker_pid=$!
        echo -e "${GREEN}  ✓ Started worker ${i} (PID: ${worker_pid})${NC}"
    done
}

# Create logs directory
mkdir -p logs

# Check Redis
if ! check_redis; then
    exit 1
fi

# Determine which workers to start
WORKER_TYPE="${1:-all}"

case "$WORKER_TYPE" in
    parsing)
        echo -e "${GREEN}Starting parsing workers only${NC}"
        start_queue_workers "parsing-queue" "${WORKER_COUNT_PARSING:-3}" "parsing queue"
        ;;

    ai)
        echo -e "${GREEN}Starting AI workers only${NC}"
        start_queue_workers "ai-queue" "${WORKER_COUNT_AI:-2}" "AI queue"
        ;;

    notion)
        echo -e "${GREEN}Starting Notion workers only${NC}"
        start_queue_workers "notion-queue" "${WORKER_COUNT_NOTION:-2}" "Notion queue"
        ;;

    all|*)
        echo -e "${GREEN}Starting all workers${NC}"
        start_queue_workers "parsing-queue" "${WORKER_COUNT_PARSING:-3}" "parsing queue"
        start_queue_workers "ai-queue" "${WORKER_COUNT_AI:-2}" "AI queue"
        start_queue_workers "notion-queue" "${WORKER_COUNT_NOTION:-2}" "Notion queue"
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Workers started successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Logs: ${YELLOW}logs/worker-*.log${NC}"
echo -e "Stop workers: ${YELLOW}./scripts/stop_workers.sh${NC}"
echo -e "View dashboard: ${YELLOW}rq-dashboard${NC} (port ${RQ_DASHBOARD_PORT:-9181})"
echo ""
