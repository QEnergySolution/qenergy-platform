#!/bin/bash

# QEnergy Platform Database Cleanup Script
# 清空数据库中的所有数据，保留schema结构

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
CLEAN="🧹"
DATABASE="🗄️"
BACKUP="💾"
DANGER="⚠️"

# Configuration
POSTGRES_DB="qenergy_platform"
POSTGRES_USER="yuxin.xue"
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_ROOT/backups"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo -e "${PURPLE}${CLEAN} QEnergy Platform Database Cleanup${NC}"
echo "=============================================="
echo -e "This script will ${RED}PERMANENTLY DELETE${NC} all data in the database."
echo -e "Database: ${CYAN}$POSTGRES_DB${NC} on ${CYAN}$POSTGRES_HOST:$POSTGRES_PORT${NC}"
echo ""

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

# Function to get current data counts
get_data_counts() {
    echo -e "${INFO} Current data in database:"
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
    SELECT 
        'Projects: ' || COUNT(*) as info FROM projects
    UNION ALL
    SELECT 
        'Project History: ' || COUNT(*) as info FROM project_history
    UNION ALL
    SELECT 
        'Report Uploads: ' || COUNT(*) as info FROM report_uploads
    UNION ALL
    SELECT 
        'Weekly Analysis: ' || COUNT(*) as info FROM weekly_report_analysis
    ORDER BY info;
    " -t 2>/dev/null | while read line; do
        if [ ! -z "$line" ]; then
            echo -e "  $line"
        fi
    done
}

# Function to create backup
create_backup() {
    local backup_file="$BACKUP_DIR/qenergy_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    echo -e "${BACKUP} Creating backup before cleanup..."
    echo -e "${INFO} Backup location: ${CYAN}$backup_file${NC}"
    
    if pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$backup_file" 2>/dev/null; then
        echo -e "${CHECK} Backup created successfully"
        echo -e "${INFO} Backup size: $(du -h "$backup_file" | cut -f1)"
        return 0
    else
        echo -e "${CROSS} Backup failed!"
        return 1
    fi
}

# Function to show cleanup options
show_options() {
    echo -e "${BLUE}🔧 Cleanup Options${NC}"
    echo "=================="
    echo "1. 🧹 Full cleanup (all data)"
    echo "2. 📊 Clean reports only (report_uploads + project_history)"
    echo "3. 📈 Clean analysis only (weekly_report_analysis)"
    echo "4. 🎯 Custom cleanup (choose tables)"
    echo "5. 💾 Backup only (no cleanup)"
    echo "6. ❌ Cancel"
    echo ""
}

# Function to clean all data
clean_all_data() {
    echo -e "${CLEAN} Cleaning ALL data from database..."
    
    # Disable foreign key checks temporarily and clean in correct order
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << EOF
    -- Clean in reverse dependency order
    TRUNCATE TABLE weekly_report_analysis CASCADE;
    TRUNCATE TABLE project_history CASCADE;
    TRUNCATE TABLE report_uploads CASCADE;
    -- Note: Keep projects table for reference data
    -- TRUNCATE TABLE projects CASCADE;
    
    -- Reset sequences
    ALTER SEQUENCE IF EXISTS report_uploads_id_seq RESTART WITH 1;
    ALTER SEQUENCE IF EXISTS project_history_id_seq RESTART WITH 1;
    ALTER SEQUENCE IF EXISTS weekly_report_analysis_id_seq RESTART WITH 1;
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${CHECK} All data cleaned successfully"
        echo -e "${INFO} Projects table preserved for reference"
    else
        echo -e "${CROSS} Cleanup failed!"
        return 1
    fi
}

# Function to clean reports only
clean_reports_only() {
    echo -e "${CLEAN} Cleaning report data (uploads + history)..."
    
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << EOF
    -- Clean reports and related history
    TRUNCATE TABLE project_history CASCADE;
    TRUNCATE TABLE report_uploads CASCADE;
    
    -- Reset sequences
    ALTER SEQUENCE IF EXISTS report_uploads_id_seq RESTART WITH 1;
    ALTER SEQUENCE IF EXISTS project_history_id_seq RESTART WITH 1;
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${CHECK} Report data cleaned successfully"
    else
        echo -e "${CROSS} Report cleanup failed!"
        return 1
    fi
}

# Function to clean analysis only
clean_analysis_only() {
    echo -e "${CLEAN} Cleaning analysis data..."
    
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << EOF
    TRUNCATE TABLE weekly_report_analysis CASCADE;
    ALTER SEQUENCE IF EXISTS weekly_report_analysis_id_seq RESTART WITH 1;
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${CHECK} Analysis data cleaned successfully"
    else
        echo -e "${CROSS} Analysis cleanup failed!"
        return 1
    fi
}

# Function for custom cleanup
custom_cleanup() {
    echo -e "${INFO} Available tables for cleanup:"
    echo "1. project_history"
    echo "2. report_uploads" 
    echo "3. weekly_report_analysis"
    echo "4. projects (${RED}WARNING: Reference data${NC})"
    echo ""
    echo -e "Enter table numbers to clean (e.g., 1,2): "
    read -r table_choice
    
    # Convert input to array
    IFS=',' read -ra TABLES <<< "$table_choice"
    
    echo -e "${CLEAN} Cleaning selected tables..."
    
    for table_num in "${TABLES[@]}"; do
        case ${table_num// /} in
            1)
                echo -e "${INFO} Cleaning project_history..."
                psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "TRUNCATE TABLE project_history CASCADE;"
                ;;
            2)
                echo -e "${INFO} Cleaning report_uploads..."
                psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "TRUNCATE TABLE report_uploads CASCADE;"
                ;;
            3)
                echo -e "${INFO} Cleaning weekly_report_analysis..."
                psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "TRUNCATE TABLE weekly_report_analysis CASCADE;"
                ;;
            4)
                echo -e "${WARNING} Cleaning projects (reference data)..."
                echo -e "${DANGER} Are you sure? This will remove all project definitions! (y/N): "
                read -r confirm_projects
                if [[ $confirm_projects =~ ^[Yy]$ ]]; then
                    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "TRUNCATE TABLE projects CASCADE;"
                else
                    echo -e "${INFO} Skipping projects table"
                fi
                ;;
            *)
                echo -e "${WARNING} Invalid table number: $table_num"
                ;;
        esac
    done
    
    echo -e "${CHECK} Custom cleanup completed"
}

# Function to verify cleanup
verify_cleanup() {
    echo -e "${INFO} Verifying cleanup..."
    get_data_counts
}

# Check database connection
if ! test_database; then
    echo -e "${CROSS} Cannot connect to database!"
    echo -e "${INFO} Check if PostgreSQL is running: ${CYAN}brew services start postgresql@14${NC}"
    echo -e "${INFO} Check connection: ${CYAN}psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB${NC}"
    exit 1
fi

echo -e "${CHECK} Connected to database successfully"
echo ""

# Show current data
get_data_counts
echo ""

# Warning and confirmation
echo -e "${DANGER} ${RED}WARNING: This operation cannot be undone!${NC}"
echo -e "${INFO} A backup will be created automatically before cleanup."
echo ""
echo -e "Do you want to continue? (y/N): "
read -r confirm

if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo -e "${INFO} Operation cancelled."
    exit 0
fi

echo ""

# Create backup first
if ! create_backup; then
    echo -e "${CROSS} Backup failed. Aborting cleanup for safety."
    exit 1
fi

echo ""

# Show cleanup options
show_options

echo -e "Choose an option (1-6): "
read -r choice

case $choice in
    1)
        echo -e "${DANGER} Full cleanup selected. This will delete ALL data!"
        echo -e "Are you absolutely sure? Type 'DELETE ALL' to confirm: "
        read -r final_confirm
        if [ "$final_confirm" = "DELETE ALL" ]; then
            clean_all_data
        else
            echo -e "${INFO} Full cleanup cancelled."
            exit 0
        fi
        ;;
    2)
        clean_reports_only
        ;;
    3)
        clean_analysis_only
        ;;
    4)
        custom_cleanup
        ;;
    5)
        echo -e "${INFO} Backup completed. No cleanup performed."
        exit 0
        ;;
    6)
        echo -e "${INFO} Operation cancelled."
        exit 0
        ;;
    *)
        echo -e "${CROSS} Invalid option. Operation cancelled."
        exit 1
        ;;
esac

echo ""

# Verify the cleanup
verify_cleanup

echo ""
echo -e "${CHECK} Database cleanup completed successfully!"
echo -e "${BACKUP} Backup saved to: ${CYAN}$backup_file${NC}"

# Show restoration info
echo ""
echo -e "${BLUE}📋 Restoration Information${NC}"
echo "=========================="
echo -e "To restore from backup:"
echo -e "${CYAN}psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB < [backup_file]${NC}"
echo ""
echo -e "To reinitialize with sample data:"
echo -e "${CYAN}cd $PROJECT_ROOT && ./scripts/install.sh${NC}"

echo ""
echo "Cleanup completed at $(date)"
