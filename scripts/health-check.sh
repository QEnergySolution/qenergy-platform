#!/bin/bash

# QEnergy Platform Health Check Script
# Check the health status of the front end, back end and database

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Icons
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
ROCKET="🚀"
DATABASE="🗄️"
GLOBE="🌐"
GEAR="⚙️"

# Configuration
FRONTEND_URL="http://localhost:3001"
BACKEND_URL="http://localhost:8002"
POSTGRES_DB="qenergy_platform"
POSTGRES_USER="yuxin.xue"
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"

# Health check results
FRONTEND_HEALTHY=false
BACKEND_HEALTHY=false
DATABASE_HEALTHY=false
API_HEALTHY=false
UPLOADS_HEALTHY=false

echo -e "${PURPLE}${ROCKET} QEnergy Platform Health Check${NC}"
echo "=================================================="
echo -e "Checking system health at $(date)"
echo ""

# Function to test HTTP endpoint
test_http() {
    local url=$1
    local timeout=${2:-10}
    local expected_status=${3:-200}
    
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $timeout "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        return 0
    else
        return 1
    fi
}

# Function to test database connection
test_database() {
    local result
    result=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" -t 2>/dev/null | tr -d '[:space:]' || echo "")
    
    if [ "$result" = "1" ]; then
        return 0
    else
        return 1
    fi
}

# Function to get database stats
get_db_stats() {
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
    SELECT 
        'projects' as table_name, COUNT(*) as count FROM projects
    UNION ALL
    SELECT 
        'project_history' as table_name, COUNT(*) as count FROM project_history
    UNION ALL
    SELECT 
        'report_uploads' as table_name, COUNT(*) as count FROM report_uploads
    UNION ALL
    SELECT 
        'weekly_report_analysis' as table_name, COUNT(*) as count FROM weekly_report_analysis
    ORDER BY table_name;
    " -t 2>/dev/null || echo "Failed to get stats"
}

# Check Frontend Health
echo -e "${BLUE}${GLOBE} Frontend Health Check${NC}"
echo "---------------------------"

# Check if Next.js is running
if test_http "$FRONTEND_URL" 10 200; then
    echo -e "${CHECK} Frontend server is ${GREEN}HEALTHY${NC} (${FRONTEND_URL})"
    FRONTEND_HEALTHY=true
    
    # Check if frontend can load main page
    if curl -s "$FRONTEND_URL" | grep -q "QEnergy\|Dashboard\|Platform" 2>/dev/null; then
        echo -e "${CHECK} Frontend content is ${GREEN}LOADING CORRECTLY${NC}"
    else
        echo -e "${WARNING} Frontend is running but content may not be loading properly"
    fi
else
    echo -e "${CROSS} Frontend server is ${RED}NOT RESPONDING${NC} (${FRONTEND_URL})"
    echo -e "${INFO} Try: ${CYAN}pnpm dev:fe${NC}"
fi

echo ""

# Check Backend Health
echo -e "${BLUE}${GEAR} Backend Health Check${NC}"
echo "--------------------------"

# Check if FastAPI is running
if test_http "$BACKEND_URL/api/health" 10 200; then
    echo -e "${CHECK} Backend server is ${GREEN}HEALTHY${NC} (${BACKEND_URL})"
    BACKEND_HEALTHY=true
    
    # Test specific API endpoints
    echo -e "${INFO} Testing API endpoints..."
    
    # Test reports endpoints
    if test_http "$BACKEND_URL/api/reports/uploads" 10; then
        echo -e "  ${CHECK} Reports API: ${GREEN}OK${NC}"
        API_HEALTHY=true
    else
        echo -e "  ${CROSS} Reports API: ${RED}FAILED${NC}"
    fi
    
    # Test projects endpoint (if exists)
    if test_http "$BACKEND_URL/api/projects" 10; then
        echo -e "  ${CHECK} Projects API: ${GREEN}OK${NC}"
    else
        echo -e "  ${WARNING} Projects API: ${YELLOW}NOT AVAILABLE${NC}"
    fi
    
    # Test task queue
    if test_http "$BACKEND_URL/api/tasks" 10; then
        echo -e "  ${CHECK} Task Queue: ${GREEN}OK${NC}"
    else
        echo -e "  ${WARNING} Task Queue: ${YELLOW}NOT AVAILABLE${NC}"
    fi
    
else
    echo -e "${CROSS} Backend server is ${RED}NOT RESPONDING${NC} (${BACKEND_URL})"
    echo -e "${INFO} Try: ${CYAN}conda activate qenergy-backend && cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload${NC}"
fi

echo ""

# Check Database Health
echo -e "${BLUE}${DATABASE} Database Health Check${NC}"
echo "----------------------------"

if test_database; then
    echo -e "${CHECK} PostgreSQL database is ${GREEN}HEALTHY${NC} (${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB})"
    DATABASE_HEALTHY=true
    
    echo -e "${INFO} Database statistics:"
    get_db_stats | while read line; do
        if [ ! -z "$line" ]; then
            echo -e "  ${line}"
        fi
    done
    
    # Check for recent uploads
    recent_uploads=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
        SELECT COUNT(*) FROM report_uploads WHERE uploaded_at > NOW() - INTERVAL '24 hours';
    " -t 2>/dev/null | tr -d '[:space:]' || echo "0")
    
    if [ "$recent_uploads" -gt 0 ]; then
        echo -e "  ${CHECK} Recent uploads (24h): ${GREEN}$recent_uploads${NC}"
        UPLOADS_HEALTHY=true
    else
        echo -e "  ${INFO} Recent uploads (24h): ${YELLOW}0${NC}"
    fi
    
else
    echo -e "${CROSS} PostgreSQL database is ${RED}NOT ACCESSIBLE${NC}"
    echo -e "${INFO} Check if PostgreSQL is running: ${CYAN}brew services start postgresql@14${NC} (macOS)"
    echo -e "${INFO} Check connection: ${CYAN}psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB${NC}"
fi

echo ""

# Environment Check
echo -e "${BLUE}🔧 Environment Check${NC}"
echo "--------------------"

# Check conda environment
if conda info --envs | grep -q "qenergy-backend"; then
    echo -e "${CHECK} Conda environment 'qenergy-backend': ${GREEN}EXISTS${NC}"
else
    echo -e "${CROSS} Conda environment 'qenergy-backend': ${RED}MISSING${NC}"
    echo -e "${INFO} Create with: ${CYAN}conda env create -f backend/environment.yml${NC}"
fi

# Check if backend dependencies are available
if conda run -n qenergy-backend python -c "import fastapi, sqlalchemy, psycopg2" 2>/dev/null; then
    echo -e "${CHECK} Backend dependencies: ${GREEN}INSTALLED${NC}"
else
    echo -e "${CROSS} Backend dependencies: ${RED}MISSING${NC}"
    echo -e "${INFO} Install with: ${CYAN}conda activate qenergy-backend && pip install -r backend/requirements.txt${NC}"
fi

# Check if frontend dependencies are available
if [ -d "frontend/node_modules" ]; then
    echo -e "${CHECK} Frontend dependencies: ${GREEN}INSTALLED${NC}"
else
    echo -e "${CROSS} Frontend dependencies: ${RED}MISSING${NC}"
    echo -e "${INFO} Install with: ${CYAN}cd frontend && pnpm install${NC}"
fi

# Check environment files
if [ -f "backend/.env" ]; then
    echo -e "${CHECK} Backend .env file: ${GREEN}EXISTS${NC}"
else
    echo -e "${WARNING} Backend .env file: ${YELLOW}MISSING${NC}"
    echo -e "${INFO} Copy from: ${CYAN}cp backend/env.example backend/.env${NC}"
fi

if [ -f "frontend/.env.local" ]; then
    echo -e "${CHECK} Frontend .env.local file: ${GREEN}EXISTS${NC}"
else
    echo -e "${WARNING} Frontend .env.local file: ${YELLOW}MISSING${NC}"
fi

echo ""

# Overall Health Summary
echo -e "${PURPLE}📊 Health Summary${NC}"
echo "=================="

total_checks=5
healthy_checks=0

if [ "$FRONTEND_HEALTHY" = true ]; then
    echo -e "${CHECK} Frontend: ${GREEN}HEALTHY${NC}"
    ((healthy_checks++))
else
    echo -e "${CROSS} Frontend: ${RED}UNHEALTHY${NC}"
fi

if [ "$BACKEND_HEALTHY" = true ]; then
    echo -e "${CHECK} Backend: ${GREEN}HEALTHY${NC}"
    ((healthy_checks++))
else
    echo -e "${CROSS} Backend: ${RED}UNHEALTHY${NC}"
fi

if [ "$DATABASE_HEALTHY" = true ]; then
    echo -e "${CHECK} Database: ${GREEN}HEALTHY${NC}"
    ((healthy_checks++))
else
    echo -e "${CROSS} Database: ${RED}UNHEALTHY${NC}"
fi

if [ "$API_HEALTHY" = true ]; then
    echo -e "${CHECK} API Endpoints: ${GREEN}HEALTHY${NC}"
    ((healthy_checks++))
else
    echo -e "${CROSS} API Endpoints: ${RED}UNHEALTHY${NC}"
fi

if [ "$UPLOADS_HEALTHY" = true ]; then
    echo -e "${CHECK} Upload System: ${GREEN}ACTIVE${NC}"
    ((healthy_checks++))
else
    echo -e "${WARNING} Upload System: ${YELLOW}NO RECENT ACTIVITY${NC}"
fi

echo ""
health_percentage=$((healthy_checks * 100 / total_checks))

if [ $health_percentage -eq 100 ]; then
    echo -e "${ROCKET} Overall Status: ${GREEN}EXCELLENT${NC} (${health_percentage}%)"
    echo -e "${CHECK} All systems operational! Ready for development."
elif [ $health_percentage -ge 80 ]; then
    echo -e "${CHECK} Overall Status: ${GREEN}GOOD${NC} (${health_percentage}%)"
    echo -e "${INFO} Most systems operational. Minor issues detected."
elif [ $health_percentage -ge 60 ]; then
    echo -e "${WARNING} Overall Status: ${YELLOW}FAIR${NC} (${health_percentage}%)"
    echo -e "${WARNING} Some systems need attention."
else
    echo -e "${CROSS} Overall Status: ${RED}POOR${NC} (${health_percentage}%)"
    echo -e "${CROSS} Major issues detected. System may not function properly."
fi

echo ""

# Quick Start Recommendations
if [ $health_percentage -lt 100 ]; then
    echo -e "${BLUE}🛠️  Quick Fix Recommendations${NC}"
    echo "==============================="
    
    if [ "$DATABASE_HEALTHY" = false ]; then
        echo -e "${INFO} 1. Start PostgreSQL: ${CYAN}brew services start postgresql@14${NC}"
    fi
    
    if [ "$BACKEND_HEALTHY" = false ]; then
        echo -e "${INFO} 2. Start Backend: ${CYAN}conda activate qenergy-backend && cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload${NC}"
    fi
    
    if [ "$FRONTEND_HEALTHY" = false ]; then
        echo -e "${INFO} 3. Start Frontend: ${CYAN}pnpm dev:fe${NC}"
    fi
    
    echo ""
fi

# URLs for quick access
echo -e "${BLUE}🔗 Quick Access URLs${NC}"
echo "===================="
echo -e "Frontend: ${CYAN}$FRONTEND_URL${NC}"
echo -e "Backend API: ${CYAN}$BACKEND_URL/api${NC}"
echo -e "API Health: ${CYAN}$BACKEND_URL/api/health${NC}"
echo -e "API Docs: ${CYAN}$BACKEND_URL/docs${NC}"

echo ""
echo "Health check completed at $(date)"

# Exit with appropriate code
if [ $health_percentage -ge 80 ]; then
    exit 0
else
    exit 1
fi
