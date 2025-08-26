#!/bin/bash

# QEnergy Platform - Start Script
# Starts all services (database, backend, frontend)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if service is running
is_service_running() {
    local port=$1
    lsof -i :$port >/dev/null 2>&1
}

# Function to start PostgreSQL (macOS)
start_postgres_macos() {
    if ! is_service_running 5432; then
        print_status "Starting PostgreSQL..."
        brew services start postgresql@14
        sleep 3
        print_success "PostgreSQL started"
    else
        print_status "PostgreSQL already running"
    fi
}

# Function to start PostgreSQL (Linux)
start_postgres_linux() {
    if ! is_service_running 5432; then
        print_status "Starting PostgreSQL..."
        sudo systemctl start postgresql
        sleep 3
        print_success "PostgreSQL started"
    else
        print_status "PostgreSQL already running"
    fi
}

# Function to start backend
start_backend() {
    if ! is_service_running 8002; then
        print_status "Starting backend..."
        cd backend
        source /opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh
        conda activate qenergy-backend
        uvicorn app.main:app --reload --port 8002 --host 0.0.0.0 &
        cd ..
        sleep 5
        print_success "Backend started on http://localhost:8002"
    else
        print_status "Backend already running on port 8002"
    fi
}

# Function to start frontend
start_frontend() {
    if ! is_service_running 3000; then
        print_status "Starting frontend..."
        pnpm dev:fe &
        sleep 10
        print_success "Frontend started on http://localhost:3000"
    else
        print_status "Frontend already running on port 3000"
    fi
}

# Function to check services
check_services() {
    print_status "Checking services..."
    
    # Check database
    if is_service_running 5432; then
        print_success "Database: Running on port 5432"
    else
        print_error "Database: Not running"
    fi
    
    # Check backend
    if is_service_running 8002; then
        print_success "Backend: Running on port 8002"
        if curl -s http://localhost:8002/api/health >/dev/null 2>&1; then
            print_success "Backend API: Responding"
        else
            print_warning "Backend API: Not responding"
        fi
    else
        print_error "Backend: Not running"
    fi
    
    # Check frontend
    if is_service_running 3000; then
        print_success "Frontend: Running on port 3000"
    else
        print_error "Frontend: Not running"
    fi
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# Function to stop all services
stop_services() {
    print_status "Stopping all services..."
    
    # Stop frontend
    pkill -f "pnpm.*frontend.*dev" 2>/dev/null || true
    # Fallback: kill any process bound to port 3000
    if lsof -i :3000 >/dev/null 2>&1; then
        kill -9 $(lsof -t -i :3000) 2>/dev/null || true
    fi
    
    # Stop backend
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    
    # Stop PostgreSQL (macOS)
    if [[ "$(detect_os)" == "macos" ]]; then
        brew services stop postgresql@14 2>/dev/null || true
    else
        sudo systemctl stop postgresql 2>/dev/null || true
    fi
    
    print_success "All services stopped"
}

# Main function
main() {
    echo "=========================================="
    echo "  QEnergy Platform - Start Script"
    echo "=========================================="
    echo
    
    OS=$(detect_os)
    
    # Parse command line arguments
    case "${1:-start}" in
        "start")
            print_status "Starting QEnergy Platform..."
            
            # Start PostgreSQL
            if [[ "$OS" == "macos" ]]; then
                start_postgres_macos
            else
                start_postgres_linux
            fi
            
            # Start backend
            start_backend
            
            # Start frontend
            start_frontend
            
            # Check services
            check_services
            
            echo
            echo "=========================================="
            print_success "QEnergy Platform started successfully!"
            echo "=========================================="
            echo
            echo "Services:"
            echo "• Frontend: http://localhost:3000"
            echo "• Backend API: http://localhost:8002/api"
            echo "• API Docs: http://localhost:8002/docs"
            echo "• Health Check: http://localhost:8002/api/health"
            echo
            echo "To stop all services, run: $0 stop"
            echo
            ;;
        "stop")
            stop_services
            ;;
        "status")
            check_services
            ;;
        "restart")
            stop_services
            sleep 2
            $0 start
            ;;
        *)
            echo "Usage: $0 {start|stop|status|restart}"
            echo "  start   - Start all services (default)"
            echo "  stop    - Stop all services"
            echo "  status  - Check service status"
            echo "  restart - Restart all services"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
