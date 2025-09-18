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
        brew services start postgresql@16 2>/dev/null || brew services start postgresql@14
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

# Function to start backend (Linux)
start_backend_linux() {
    if ! is_service_running 8002; then
        print_status "Starting backend..."
        cd backend
        # Source conda for Linux (try multiple paths)
        if [[ -f "$HOME/miniforge3/etc/profile.d/conda.sh" ]]; then
            source $HOME/miniforge3/etc/profile.d/conda.sh
        elif [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
            source $HOME/miniconda3/etc/profile.d/conda.sh
        elif [[ -f "/opt/conda/etc/profile.d/conda.sh" ]]; then
            source /opt/conda/etc/profile.d/conda.sh
        fi
        conda activate qenergy-backend
        # Bootstrap DB and run migrations before starting backend
        cd ..
        bootstrap_and_migrate
        cd backend
        uvicorn app.main:app --reload --port 8002 --host 0.0.0.0 &
        cd ..
        sleep 5
        print_success "Backend started on http://localhost:8002"
    else
        print_status "Backend already running on port 8002"
    fi
}

# Function to start backend
start_backend() {
    OS=$(detect_os)
    if [[ "$OS" == "linux" ]]; then
        start_backend_linux
    else
        start_backend_macos
    fi
}

# Function to start backend (macOS)
start_backend_macos() {
    if ! is_service_running 8002; then
        print_status "Starting backend..."
        cd backend
        # Source conda for macOS (try multiple paths)
        if [[ -f "/opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh" ]]; then
            source /opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh
        elif [[ -f "$HOME/miniforge3/etc/profile.d/conda.sh" ]]; then
            source $HOME/miniforge3/etc/profile.d/conda.sh
        elif [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
            source $HOME/miniconda3/etc/profile.d/conda.sh
        fi
        conda activate qenergy-backend
        # Bootstrap DB and run migrations before starting backend
        cd ..
        bootstrap_and_migrate
        cd backend
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
        # Export NEXT_PUBLIC_API_URL from frontend/.env.local if present for visibility
        if [[ -f "frontend/.env.local" ]]; then
            API_URL=$(grep -E '^NEXT_PUBLIC_API_URL=' frontend/.env.local | sed 's/NEXT_PUBLIC_API_URL=//')
            if [[ -n "$API_URL" ]]; then
                print_status "Frontend will use NEXT_PUBLIC_API_URL=$API_URL"
            fi
        fi
        pnpm dev:fe &
        sleep 10
        # Try to detect LAN IP to show a clickable URL for others on the network
        if command -v hostname >/dev/null 2>&1; then
            LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
        fi
        if [[ -z "$LAN_IP" && "$OSTYPE" == "darwin"* ]]; then
            LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || true)
        fi
        if [[ -n "$LAN_IP" ]]; then
            print_success "Frontend started on http://$LAN_IP:3000 (and http://localhost:3000)"
        else
            print_success "Frontend started on http://localhost:3000"
        fi
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
        brew services stop postgresql@16 2>/dev/null || brew services stop postgresql@14 2>/dev/null || true
    else
        sudo systemctl stop postgresql 2>/dev/null || true
    fi
    
    print_success "All services stopped"
}

# Function to bootstrap DB (once) and run Alembic migrations safely
bootstrap_and_migrate() {
    print_status "Bootstrapping database and applying migrations..."

    local BACKEND_DIR="backend"
    local ENV_FILE="$BACKEND_DIR/.env"
    local DB_URL=""

    if [[ -f "$ENV_FILE" ]]; then
        DB_URL=$(grep -E '^DATABASE_URL=' "$ENV_FILE" | sed 's/^DATABASE_URL=//')
    fi

    if [[ -z "$DB_URL" ]]; then
        print_warning "DATABASE_URL not found in backend/.env; skipping bootstrap and running migrations using Alembic's .env loading"
    fi

    # If we have a DB URL, check schema state
    local TABLE_COUNT=""
    local HAVE_ALEMBIC=""
    local HAVE_CORE=""
    if [[ -n "$DB_URL" ]]; then
        if ! TABLE_COUNT=$(psql "$DB_URL" -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';" 2>/dev/null); then
            print_warning "Could not inspect database schema; proceeding to migrations"
        fi
        HAVE_ALEMBIC=$(psql "$DB_URL" -tAc "SELECT to_regclass('public.alembic_version') IS NOT NULL;" 2>/dev/null || echo "f")
        HAVE_CORE=$(psql "$DB_URL" -tAc "SELECT to_regclass('public.projects') IS NOT NULL;" 2>/dev/null || echo "f")
    fi

    # Activate conda and run commands from backend directory so Alembic can load .env
    pushd "$BACKEND_DIR" >/dev/null
    # Source conda (macOS and Linux)
    if [[ -f "/opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh" ]]; then
        source /opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh
    elif [[ -f "$HOME/miniforge3/etc/profile.d/conda.sh" ]]; then
        source $HOME/miniforge3/etc/profile.d/conda.sh
    elif [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
        source $HOME/miniconda3/etc/profile.d/conda.sh
    elif [[ -f "/opt/conda/etc/profile.d/conda.sh" ]]; then
        source /opt/conda/etc/profile.d/conda.sh
    fi
    conda activate qenergy-backend || true

    # If schema empty, run setup SQL once and stamp baseline
    if [[ -n "$TABLE_COUNT" && "$TABLE_COUNT" == "0" ]]; then
        print_status "Schema empty; running setup-database.sql"
        if ! psql "$DB_URL" -v ON_ERROR_STOP=1 -f "setup-database.sql"; then
            print_error "setup-database.sql failed"
            popd >/dev/null
            exit 1
        fi
        print_status "Stamping Alembic baseline to 20250826_0001"
        alembic stamp 20250826_0001 || { print_error "Alembic stamp failed"; popd >/dev/null; exit 1; }
    elif [[ "$HAVE_ALEMBIC" != "t" && "$HAVE_CORE" == "t" ]]; then
        # Existing tables but no Alembic history: stamp baseline to avoid duplicate-create
        print_status "Existing tables detected without Alembic history; stamping baseline to 20250826_0001"
        alembic stamp 20250826_0001 || { print_error "Alembic stamp failed"; popd >/dev/null; exit 1; }
    else
        print_status "Bootstrap not needed; proceeding to migrations"
    fi

    # Always run migrations to head
    alembic upgrade head || { print_error "Alembic upgrade failed"; popd >/dev/null; exit 1; }
    popd >/dev/null
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
            if command -v hostname >/dev/null 2>&1; then
                LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
            fi
            if [[ -z "$LAN_IP" && "$OSTYPE" == "darwin"* ]]; then
                LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || true)
            fi
            if [[ -n "$LAN_IP" ]]; then
                echo "• Frontend: http://$LAN_IP:3000 (and http://localhost:3000)"
            else
                echo "• Frontend: http://localhost:3000"
            fi
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
