#!/bin/bash
#
# OpenMotiv Demo Script
# Demonstrates all major features of the API
#
# Usage: ./scripts/run-demo.sh
# Run from project root (where docker-compose.yml is located)
#

set -e

# Ensure we're in the project root
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: Run this script from the project root directory"
    echo "  cd /path/to/openmotiv && ./scripts/run-demo.sh"
    exit 1
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

API_URL="${API_URL:-http://localhost:8000}"
DEMO_TS=$(date +%s)
DEMO_EMAIL="demo-${DEMO_TS}@openmotiv.io"
DEMO_PASSWORD="demopass123"

# Helper functions
print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

print_step() {
    echo ""
    echo -e "${CYAN}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}  $1${NC}"
}

print_json() {
    echo "$1" | python3 -m json.tool 2>/dev/null || echo "$1"
}

pause() {
    echo ""
    echo -e "${YELLOW}Press Enter to continue...${NC}"
    read -r
}

# Check if API is running
check_api() {
    print_header "🔍 Checking API Status"
    
    if curl -s "${API_URL}/docs" > /dev/null 2>&1; then
        print_success "API is running at ${API_URL}"
    else
        echo -e "${RED}✗ API is not running at ${API_URL}${NC}"
        echo ""
        echo "Start the API with:"
        echo "  docker compose up -d"
        echo "  docker compose exec api alembic upgrade head"
        exit 1
    fi
}

# ============================================================================
# DEMO START
# ============================================================================

clear
echo -e "${BOLD}"
echo "  ___                   __  __       _   _       "
echo " / _ \ _ __   ___ _ __ |  \/  | ___ | |_(_)_   __"
echo "| | | | '_ \ / _ \ '_ \| |\/| |/ _ \| __| \ \ / /"
echo "| |_| | |_) |  __/ | | | |  | | (_) | |_| |\ V / "
echo " \___/| .__/ \___|_| |_|_|  |_|\___/ \__|_| \_/  "
echo "      |_|                                        "
echo ""
echo -e "${NC}"
echo -e "${CYAN}Fleet Management API Demo${NC}"
echo -e "${YELLOW}FastAPI • PostgreSQL • Redis • Celery • WebSocket${NC}"
echo ""

check_api
pause

# ============================================================================
# 1. AUTHENTICATION
# ============================================================================

print_header "🔐 Authentication"

print_step "Registering new user: ${DEMO_EMAIL}"
REGISTER_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"${DEMO_EMAIL}\", \"password\": \"${DEMO_PASSWORD}\"}")
print_json "$REGISTER_RESPONSE"
USER_ID=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
print_success "User registered!"

print_step "Promoting user to operator role..."
if docker compose exec -T db psql -U postgres -d openmotiv -c \
    "UPDATE users SET role = 'OPERATOR' WHERE id = '${USER_ID}';" > /dev/null 2>&1; then
    print_success "User promoted to operator!"
elif psql "${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/openmotiv}" -c \
    "UPDATE users SET role = 'OPERATOR' WHERE id = '${USER_ID}';" > /dev/null 2>&1; then
    print_success "User promoted to operator!"
else
    echo -e "${RED}Warning: Could not promote user. Robot creation may fail.${NC}"
    echo -e "${YELLOW}Try running: docker compose exec db psql -U postgres -d openmotiv${NC}"
fi

print_step "Logging in and obtaining JWT token..."
LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${DEMO_EMAIL}&password=${DEMO_PASSWORD}")
TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
print_info "Token: ${TOKEN:0:50}..."
print_success "Authenticated!"

pause

# ============================================================================
# 2. ROBOT MANAGEMENT
# ============================================================================

print_header "🤖 Robot Management"

print_step "Creating Robot 1: Scout Drone"
ROBOT1_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/robots" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"Scout-01\",
        \"serial_number\": \"DRN-${DEMO_TS}-001\",
        \"robot_type\": \"drone\",
        \"status\": \"idle\"
    }")
print_json "$ROBOT1_RESPONSE"
ROBOT1_ID=$(echo "$ROBOT1_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
print_success "Created robot: $ROBOT1_ID"

print_step "Creating Robot 2: Delivery Bot"
ROBOT2_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/robots" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"Carrier-07\",
        \"serial_number\": \"AGV-${DEMO_TS}-007\",
        \"robot_type\": \"agv\",
        \"status\": \"charging\"
    }")
print_json "$ROBOT2_RESPONSE"
ROBOT2_ID=$(echo "$ROBOT2_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
print_success "Created robot: $ROBOT2_ID"

print_step "Creating Robot 3: Inspection Arm"
ROBOT3_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/robots" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"Inspector-03\",
        \"serial_number\": \"ARM-${DEMO_TS}-003\",
        \"robot_type\": \"arm\",
        \"status\": \"idle\"
    }")
print_json "$ROBOT3_RESPONSE"
ROBOT3_ID=$(echo "$ROBOT3_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
print_success "Created robot: $ROBOT3_ID"

print_step "Listing all robots in fleet..."
ROBOTS_LIST=$(curl -s -X GET "${API_URL}/api/v1/robots" \
    -H "Authorization: Bearer ${TOKEN}")
print_json "$ROBOTS_LIST"
print_success "Fleet has $(echo "$ROBOTS_LIST" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "multiple") robots"

pause

# ============================================================================
# 3. MISSION CONTROL
# ============================================================================

print_header "📋 Mission Control"

print_step "Creating Mission 1: Security Patrol (High Priority)"
MISSION1_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/missions" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Warehouse Security Patrol",
        "description": "Patrol sectors A through D, check all entry points",
        "priority": "high"
    }')
print_json "$MISSION1_RESPONSE"
MISSION1_ID=$(echo "$MISSION1_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
print_success "Created mission: $MISSION1_ID"

print_step "Creating Mission 2: Package Delivery"
MISSION2_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/missions" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Dock-to-Storage Transfer",
        "description": "Move incoming shipment from dock 3 to storage zone B",
        "priority": "normal"
    }')
print_json "$MISSION2_RESPONSE"
MISSION2_ID=$(echo "$MISSION2_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
print_success "Created mission: $MISSION2_ID"

pause

# ============================================================================
# 4. MISSION ASSIGNMENT & LIFECYCLE
# ============================================================================

print_header "🔄 Mission Lifecycle"

print_step "Assigning Scout-01 drone to security patrol..."
ASSIGN_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/missions/${MISSION1_ID}/assign" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"robot_id\": \"${ROBOT1_ID}\"}")
print_json "$ASSIGN_RESPONSE"
print_success "Robot assigned to mission!"

print_step "Starting the security patrol mission..."
START_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/missions/${MISSION1_ID}/start" \
    -H "Authorization: Bearer ${TOKEN}")
print_json "$START_RESPONSE"
print_success "Mission started! Status: in_progress"

print_step "Updating robot status to 'active'..."
STATUS_RESPONSE=$(curl -s -X PATCH "${API_URL}/api/v1/robots/${ROBOT1_ID}/status" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"status": "active"}')
print_json "$STATUS_RESPONSE"
print_success "Robot is now active!"

print_step "Simulating mission progress... (2 seconds)"
sleep 2

print_step "Completing the security patrol mission..."
COMPLETE_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/missions/${MISSION1_ID}/complete" \
    -H "Authorization: Bearer ${TOKEN}")
print_json "$COMPLETE_RESPONSE"
print_success "Mission completed!"

print_step "Returning robot to idle status..."
curl -s -X PATCH "${API_URL}/api/v1/robots/${ROBOT1_ID}/status" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"status": "idle"}' > /dev/null
print_success "Robot returned to idle"

pause

# ============================================================================
# 5. BACKGROUND TASKS
# ============================================================================

print_header "⏰ Background Tasks (Celery)"

print_step "Triggering fleet health check task..."
TASK_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/tasks/fleet-health-check" \
    -H "Authorization: Bearer ${TOKEN}")
print_json "$TASK_RESPONSE"
print_success "Health check queued! Celery worker will process it."

print_info "Note: Celery Beat runs this automatically every 60 seconds"

pause

# ============================================================================
# 6. WEBSOCKET DEMO
# ============================================================================

print_header "⚡ WebSocket Real-Time Updates"

echo ""
echo -e "${YELLOW}WebSocket endpoints available:${NC}"
echo ""
echo -e "  ${CYAN}Single Robot:${NC}  ws://localhost:8000/ws/robots/{robot_id}?token={jwt}"
echo -e "  ${CYAN}Fleet-wide:${NC}    ws://localhost:8000/ws/fleet?token={jwt}"
echo ""
echo -e "${YELLOW}Test with the included client:${NC}"
echo ""
echo "  python scripts/ws_client.py --token ${TOKEN:0:30}..."
echo ""
print_info "WebSocket connections receive real-time updates when robot status changes"

pause

# ============================================================================
# 7. FINAL STATE
# ============================================================================

print_header "📊 Final Fleet Status"

print_step "All robots:"
curl -s -X GET "${API_URL}/api/v1/robots" \
    -H "Authorization: Bearer ${TOKEN}" | python3 -m json.tool

echo ""
print_step "All missions:"
curl -s -X GET "${API_URL}/api/v1/missions" \
    -H "Authorization: Bearer ${TOKEN}" | python3 -m json.tool

# ============================================================================
# SUMMARY
# ============================================================================

print_header "✅ Demo Complete!"

echo ""
echo -e "${GREEN}Features demonstrated:${NC}"
echo ""
echo "  ✓ User registration and JWT authentication"
echo "  ✓ Robot CRUD operations"
echo "  ✓ Mission creation and assignment"
echo "  ✓ Mission lifecycle (pending → assigned → in_progress → completed)"
echo "  ✓ Robot status updates"
echo "  ✓ Background task triggering (Celery)"
echo "  ✓ WebSocket endpoint information"
echo ""
echo -e "${CYAN}Explore more:${NC}"
echo ""
echo "  📖 API Docs:     ${API_URL}/docs"
echo "  🔌 WebSocket:    ws://localhost:8000/ws/fleet?token=..."
echo "  📋 Redoc:        ${API_URL}/redoc"
echo ""
echo -e "${YELLOW}Your demo credentials:${NC}"
echo ""
echo "  Email:    ${DEMO_EMAIL}"
echo "  Password: ${DEMO_PASSWORD}"
echo "  Token:    ${TOKEN:0:50}..."
echo ""
echo -e "${BOLD}Thanks for watching! 🤖${NC}"
echo ""
