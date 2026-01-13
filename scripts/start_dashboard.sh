#!/bin/bash
#
# Start RQ Dashboard for monitoring workers and queues
#
# Usage:
#   ./scripts/start_dashboard.sh
#

set -e

# Colors for output
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
    set -a
    source .env
    set +a
fi

# Check if dashboard is enabled
if [ "${ENABLE_RQ_DASHBOARD:-true}" != "true" ]; then
    echo -e "${YELLOW}RQ Dashboard is disabled in .env${NC}"
    exit 1
fi

DASHBOARD_PORT="${RQ_DASHBOARD_PORT:-9181}"
REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"

echo -e "${GREEN}Starting RQ Dashboard...${NC}"
echo -e "Port: ${YELLOW}${DASHBOARD_PORT}${NC}"
echo -e "Redis: ${YELLOW}${REDIS_URL}${NC}"
echo ""
echo -e "${GREEN}Access dashboard at: http://localhost:${DASHBOARD_PORT}${NC}"
echo ""

# Start dashboard
rq-dashboard --port "$DASHBOARD_PORT" --redis-url "$REDIS_URL"
