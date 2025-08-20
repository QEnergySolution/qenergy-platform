#!/bin/bash

# QEnergy Platform - Test Script
# Tests all services and provides a comprehensive health check

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

# Function to test database
test_database() {
    print_status "Testing database..."
    
    if ! is_service_running 5432; then
        print_error "Database not running on port 5432"
        return 1
    fi
    
    # Test connection (try different user configurations)
    if psql -h localhost -U qenergy_user -d qenergy_platform -c "SELECT 1;" >/dev/null 2>&1; then
        print_success "Database connection: OK (qenergy_user)"
        DB_USER="qenergy_user"
    elif psql qenergy_platform -c "SELECT 1;" >/dev/null 2>&1; then
        print_success "Database connection: OK (default user)"
        DB_USER=""
    else
        print_error "Database connection: Failed"
        return 1
    fi
    
    # Test tables
    if [[ -n "$DB_USER" ]]; then
        local table_count=$(psql -h localhost -U $DB_USER -d qenergy_platform -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
    else
        local table_count=$(psql qenergy_platform -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
    fi
    
    if [[ "$table_count" -ge 3 ]]; then
        print_success "Database tables: $table_count tables found"
    else
        print_error "Database tables: Expected 3+ tables, found $table_count"
        return 1
    fi
    
    # Test sample data
    if [[ -n "$DB_USER" ]]; then
        local project_count=$(psql -h localhost -U $DB_USER -d qenergy_platform -t -c "SELECT COUNT(*) FROM projects;" | tr -d ' ')
    else
        local project_count=$(psql qenergy_platform -t -c "SELECT COUNT(*) FROM projects;" | tr -d ' ')
    fi
    if [[ "$project_count" -ge 1 ]]; then
        print_success "Sample data: $project_count projects found"
    else
        print_warning "Sample data: No projects found"
    fi
    
    return 0
}

# Function to test backend
test_backend() {
    print_status "Testing backend..."
    
    if ! is_service_running 8002; then
        print_error "Backend not running on port 8002"
        return 1
    fi
    
    # Test health endpoint
    local health_response=$(curl -s http://localhost:8002/api/health 2>/dev/null || echo "FAILED")
    if [[ "$health_response" == *"ok"* ]]; then
        print_success "Backend health: OK"
    else
        print_error "Backend health: Failed"
        return 1
    fi
    
    # Test API documentation
    local docs_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/docs 2>/dev/null || echo "000")
    if [[ "$docs_response" == "200" ]]; then
        print_success "API documentation: Available"
    else
        print_warning "API documentation: Not accessible (HTTP $docs_response)"
    fi
    
    # Test CORS headers
    local cors_response=$(curl -s -I http://localhost:8002/api/health 2>/dev/null | grep -i "access-control-allow-origin" || echo "NO_CORS")
    if [[ "$cors_response" != "NO_CORS" ]]; then
        print_success "CORS headers: Configured"
    else
        print_warning "CORS headers: Not configured"
    fi
    
    return 0
}

# Function to test frontend
test_frontend() {
    print_status "Testing frontend..."
    
    if ! is_service_running 3000; then
        print_error "Frontend not running on port 3000"
        return 1
    fi
    
    # Test frontend response
    local frontend_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
    if [[ "$frontend_response" == "200" ]]; then
        print_success "Frontend: Responding (HTTP $frontend_response)"
    else
        print_warning "Frontend: Not responding properly (HTTP $frontend_response)"
    fi
    
    # Test if it's a Next.js app
    local nextjs_check=$(curl -s http://localhost:3000 2>/dev/null | grep -i "next" || echo "NO_NEXT")
    if [[ "$nextjs_check" != "NO_NEXT" ]]; then
        print_success "Frontend type: Next.js detected"
    else
        print_warning "Frontend type: Next.js not detected"
    fi
    
    return 0
}

# Function to test API integration
test_api_integration() {
    print_status "Testing API integration..."
    
    # Test if frontend can reach backend
    local integration_test=$(curl -s http://localhost:3000 2>/dev/null | grep -i "localhost:8002" || echo "NO_INTEGRATION")
    if [[ "$integration_test" != "NO_INTEGRATION" ]]; then
        print_success "API integration: Frontend configured for backend"
    else
        print_warning "API integration: Frontend not configured for backend"
    fi
    
    return 0
}

# Function to run performance tests
test_performance() {
    print_status "Running performance tests..."
    
    # Database query performance
    local db_start=$(date +%s%3N)
    psql -h localhost -U qenergy_user -d qenergy_platform -c "SELECT COUNT(*) FROM projects;" >/dev/null 2>&1
    local db_end=$(date +%s%3N)
    local db_time=$((db_end - db_start))
    
    if [[ $db_time -lt 100 ]]; then
        print_success "Database performance: ${db_time}ms (Good)"
    elif [[ $db_time -lt 500 ]]; then
        print_warning "Database performance: ${db_time}ms (Acceptable)"
    else
        print_error "Database performance: ${db_time}ms (Slow)"
    fi
    
    # Backend API performance
    local api_start=$(date +%s%3N)
    curl -s http://localhost:8002/api/health >/dev/null 2>&1
    local api_end=$(date +%s%3N)
    local api_time=$((api_end - api_start))
    
    if [[ $api_time -lt 100 ]]; then
        print_success "API performance: ${api_time}ms (Good)"
    elif [[ $api_time -lt 500 ]]; then
        print_warning "API performance: ${api_time}ms (Acceptable)"
    else
        print_error "API performance: ${api_time}ms (Slow)"
    fi
    
    return 0
}

# Function to generate test report
generate_report() {
    local db_status=$1
    local backend_status=$2
    local frontend_status=$3
    
    echo
    echo "=========================================="
    echo "  QEnergy Platform - Test Report"
    echo "=========================================="
    echo
    
    echo "Service Status:"
    if [[ $db_status -eq 0 ]]; then
        echo "• Database: ✅ PASS"
    else
        echo "• Database: ❌ FAIL"
    fi
    
    if [[ $backend_status -eq 0 ]]; then
        echo "• Backend: ✅ PASS"
    else
        echo "• Backend: ❌ FAIL"
    fi
    
    if [[ $frontend_status -eq 0 ]]; then
        echo "• Frontend: ✅ PASS"
    else
        echo "• Frontend: ❌ FAIL"
    fi
    
    echo
    echo "Access URLs:"
    echo "• Frontend: http://localhost:3000"
    echo "• Backend API: http://localhost:8002/api"
    echo "• API Docs: http://localhost:8002/docs"
    echo "• Health Check: http://localhost:8002/api/health"
    echo
    
    if [[ $db_status -eq 0 && $backend_status -eq 0 && $frontend_status -eq 0 ]]; then
        print_success "All tests passed! QEnergy Platform is ready to use."
        return 0
    else
        print_error "Some tests failed. Please check the errors above."
        return 1
    fi
}

# Main function
main() {
    echo "=========================================="
    echo "  QEnergy Platform - Test Script"
    echo "=========================================="
    echo
    
    # Test database
    test_database
    local db_status=$?
    
    # Test backend
    test_backend
    local backend_status=$?
    
    # Test frontend
    test_frontend
    local frontend_status=$?
    
    # Test API integration
    test_api_integration
    
    # Run performance tests
    test_performance
    
    # Generate report
    generate_report $db_status $backend_status $frontend_status
    
    return $?
}

# Run main function
main "$@"
