#!/bin/bash

# Quick Database Check Script for QEnergy Platform
# This is a convenient wrapper around check-database.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Activate conda environment
echo "🔄 Activating qenergy-backend environment..."
eval "$(conda shell.bash hook)"
conda activate qenergy-backend

cd "$PROJECT_ROOT"

# Default to summary if no arguments provided
if [ $# -eq 0 ]; then
    echo "📊 Running database summary..."
    python scripts/check-database.py summary
else
    echo "🔍 Running: check-database.py $*"
    python scripts/check-database.py "$@"
fi

echo ""
echo "✨ Quick commands you can try:"
echo "   ./scripts/db-check.sh summary         # Database overview"
echo "   ./scripts/db-check.sh projects        # List all projects"
echo "   ./scripts/db-check.sh history         # Recent project history"
echo "   ./scripts/db-check.sh uploads         # Report uploads"
echo "   ./scripts/db-check.sh recent          # Recent activity"
echo "   ./scripts/db-check.sh search <term>   # Search projects"
echo "   ./scripts/db-check.sh project <code>  # Project details"
echo ""
echo "📚 For full help: python scripts/check-database.py --help"
