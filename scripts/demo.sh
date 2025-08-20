#!/bin/bash

# QEnergy Platform - Demo Script
# Demonstrates all platform features

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}==========================================${NC}"
    echo -e "${CYAN}  QEnergy Platform - Demo${NC}"
    echo -e "${CYAN}==========================================${NC}"
    echo
}

print_section() {
    echo -e "${BLUE}📋 $1${NC}"
    echo
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if service is running
is_service_running() {
    local port=$1
    lsof -i :$port >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local port=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_info "Waiting for $service_name to start..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if is_service_running $port; then
            print_success "$service_name is running on port $port"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    print_error "$service_name failed to start"
    return 1
}

# Function to start services if not running
ensure_services_running() {
    print_section "Starting Services"
    
    # Check and start database
    if ! is_service_running 5432; then
        print_info "Starting PostgreSQL..."
        brew services start postgresql@14 2>/dev/null || true
        wait_for_service 5432 "PostgreSQL"
    else
        print_success "PostgreSQL already running"
    fi
    
    # Check and start backend
    if ! is_service_running 8002; then
        print_info "Starting Backend..."
        cd backend
        conda activate qenergy-backend
        uvicorn app.main:app --reload --port 8002 --host 0.0.0.0 >/dev/null 2>&1 &
        cd ..
        wait_for_service 8002 "Backend"
    else
        print_success "Backend already running"
    fi
    
    # Check and start frontend
    if ! is_service_running 3000; then
        print_info "Starting Frontend..."
        pnpm dev >/dev/null 2>&1 &
        wait_for_service 3000 "Frontend"
    else
        print_success "Frontend already running"
    fi
    
    echo
}

# Function to demonstrate database features
demo_database() {
    print_section "Database Features"
    
    # Show database schema
    print_info "Database Schema:"
    echo "• projects - Energy project management"
    echo "• project_history - Project activity logs"
    echo "• weekly_report_analysis - AI analysis results"
    echo
    
    # Show sample data
    print_info "Sample Projects:"
    psql qenergy_platform -c "SELECT project_code, project_name, status FROM projects LIMIT 3;" 2>/dev/null || echo "Database not accessible"
    echo
    
    # Show table statistics
    print_info "Database Statistics:"
    local project_count=$(psql qenergy_platform -t -c "SELECT COUNT(*) FROM projects;" 2>/dev/null | tr -d ' ' || echo "0")
    local history_count=$(psql qenergy_platform -t -c "SELECT COUNT(*) FROM project_history;" 2>/dev/null | tr -d ' ' || echo "0")
    local analysis_count=$(psql qenergy_platform -t -c "SELECT COUNT(*) FROM weekly_report_analysis;" 2>/dev/null | tr -d ' ' || echo "0")
    
    echo "• Projects: $project_count"
    echo "• History Records: $history_count"
    echo "• Analysis Reports: $analysis_count"
    echo
}

# Function to demonstrate backend features
demo_backend() {
    print_section "Backend API Features"
    
    # Test health endpoint
    print_info "Health Check:"
    local health_response=$(curl -s http://localhost:8002/api/health 2>/dev/null || echo "FAILED")
    if [[ "$health_response" == *"ok"* ]]; then
        print_success "API Health: OK"
    else
        print_error "API Health: Failed"
    fi
    echo
    
    # Show available endpoints
    print_info "Available Endpoints:"
    echo "• GET /api/health - Health check"
    echo "• GET /docs - API documentation (Swagger UI)"
    echo "• GET /redoc - API documentation (ReDoc)"
    echo "• POST /api/projects - Create project"
    echo "• GET /api/projects - List projects"
    echo "• GET /api/projects/{id} - Get project details"
    echo "• PUT /api/projects/{id} - Update project"
    echo "• DELETE /api/projects/{id} - Delete project"
    echo
    
    # Show API documentation URLs
    print_info "API Documentation:"
    echo "• Swagger UI: http://localhost:8002/docs"
    echo "• ReDoc: http://localhost:8002/redoc"
    echo
}

# Function to demonstrate frontend features
demo_frontend() {
    print_section "Frontend Features"
    
    # Test frontend accessibility
    print_info "Frontend Status:"
    local frontend_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
    if [[ "$frontend_response" == "200" ]]; then
        print_success "Frontend: Accessible (HTTP $frontend_response)"
    else
        print_error "Frontend: Not accessible (HTTP $frontend_response)"
    fi
    echo
    
    # Show frontend features
    print_info "Frontend Features:"
    echo "• Modern React 18 + Next.js 15"
    echo "• TypeScript for type safety"
    echo "• Tailwind CSS for styling"
    echo "• shadcn/ui components"
    echo "• Responsive design"
    echo "• Dark/Light theme support"
    echo "• Internationalization ready"
    echo
    
    # Show frontend URLs
    print_info "Frontend URLs:"
    echo "• Main App: http://localhost:3000"
    echo "• Project Management: http://localhost:3000/projects"
    echo "• Report Upload: http://localhost:3000/upload"
    echo "• Weekly Reports: http://localhost:3000/reports"
    echo
}

# Function to demonstrate integration
demo_integration() {
    print_section "Platform Integration"
    
    print_info "Architecture Overview:"
    echo "┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐"
    echo "│   Frontend      │    │    Backend      │    │   Database      │"
    echo "│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │"
    echo "│   Port 3000     │    │   Port 8002     │    │   Port 5432     │"
    echo "└─────────────────┘    └─────────────────┘    └─────────────────┘"
    echo
    
    print_info "Data Flow:"
    echo "1. User interacts with Next.js frontend"
    echo "2. Frontend makes API calls to FastAPI backend"
    echo "3. Backend processes requests and queries PostgreSQL"
    echo "4. Database returns data to backend"
    echo "5. Backend sends JSON responses to frontend"
    echo "6. Frontend updates UI with received data"
    echo
    
    print_info "Technology Stack:"
    echo "• Frontend: Next.js 15, React 18, TypeScript, Tailwind CSS"
    echo "• Backend: FastAPI, SQLAlchemy, Pydantic, Python 3.11"
    echo "• Database: PostgreSQL 14 with pgcrypto extensions"
    echo "• Package Manager: pnpm (frontend), conda (backend)"
    echo "• Development: Hot reload, TypeScript checking, ESLint"
    echo
}

# Function to show next steps
show_next_steps() {
    print_section "Next Steps"
    
    print_info "Development Workflow:"
    echo "1. Start services: ./scripts/start.sh"
    echo "2. Make code changes"
    echo "3. Test changes: ./scripts/test.sh"
    echo "4. Stop services: ./scripts/start.sh stop"
    echo
    
    print_info "API Development:"
    echo "1. Add new endpoints in backend/app/api/"
    echo "2. Update database models in backend/app/models/"
    echo "3. Test with Swagger UI: http://localhost:8002/docs"
    echo
    
    print_info "Frontend Development:"
    echo "1. Add new pages in frontend/app/"
    echo "2. Create components in frontend/components/"
    echo "3. Update API calls in frontend/lib/api/"
    echo
    
    print_info "Database Development:"
    echo "1. Create migrations: alembic revision --autogenerate"
    echo "2. Apply migrations: alembic upgrade head"
    echo "3. Update schema: backend/setup-database.sql"
    echo
    
    print_info "Useful Commands:"
    echo "• Start all: ./scripts/start.sh"
    echo "• Stop all: ./scripts/start.sh stop"
    echo "• Test all: ./scripts/test.sh"
    echo "• Install: ./scripts/install.sh"
    echo "• Status: ./scripts/start.sh status"
    echo
}

# Main demo function
main() {
    print_header
    
    # Ensure all services are running
    ensure_services_running
    
    # Demonstrate each component
    demo_database
    demo_backend
    demo_frontend
    demo_integration
    
    # Show next steps
    show_next_steps
    
    print_header
    print_success "Demo completed! QEnergy Platform is ready for development."
    echo
    print_info "Open your browser and visit:"
    echo "• Frontend: http://localhost:3000"
    echo "• API Docs: http://localhost:8002/docs"
    echo
}

# Run main function
main "$@"
