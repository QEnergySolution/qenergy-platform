# QEnergy Platform - Deployment Scripts

This directory contains deployment and management scripts for the QEnergy Platform.

## 📁 Scripts Overview

### Installation Scripts
- **`install.sh`** - One-click installation for macOS/Linux
- **`install.bat`** - One-click installation for Windows

### Management Scripts
- **`start.sh`** - Start all services (macOS/Linux)
- **`start.bat`** - Start all services (Windows)
- **`test.sh`** - Comprehensive health check and testing
- **`demo.sh`** - Platform demonstration and feature showcase
- **`health-check.sh`** - Quick system health check (macOS/Linux)
- **`health-check.py`** - Cross-platform system health check (Python)
- **`clean-database.sh`** - Database cleanup utility with backup

### Database Inspection Scripts
- **`check-database.py`** - Comprehensive database inspection tool
- **`db-check.sh`** - Quick database check wrapper script

## 🚀 Quick Start

### macOS/Linux
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Install everything
./scripts/install.sh

# Start all services
./scripts/start.sh

# Test everything
./scripts/test.sh

# Run demo
./scripts/demo.sh

### Windows
```cmd
# Run as Administrator
scripts\install.bat

# Start all services
scripts\start.bat

# Test everything (requires Git Bash or WSL)
./scripts/test.sh

# Run demo (requires Git Bash or WSL)
./scripts/demo.sh

## 📋 Script Details

### Installation Scripts

#### `install.sh` (macOS/Linux)
**Features:**
- Auto-detects OS (macOS/Linux)
- Installs all dependencies:
  - Node.js via Homebrew (macOS) or NodeSource (Linux)
  - pnpm package manager
  - PostgreSQL 14
  - Miniforge (Conda)
- Sets up database with schema and sample data
- Creates conda environment for backend
- Installs frontend dependencies
- Verifies installation

**Usage:**
```bash
./scripts/install.sh
```

#### `install.bat` (Windows)
**Features:**
- Requires Administrator privileges
- Installs Chocolatey package manager
- Installs all dependencies:
  - Node.js
  - pnpm
  - PostgreSQL
  - Miniconda3
- Sets up database and backend environment
- Installs frontend dependencies

**Usage:**
```cmd
# Run as Administrator
scripts\install.bat
```

### Management Scripts

#### `start.sh` (macOS/Linux)
**Commands:**
- `./scripts/start.sh` or `./scripts/start.sh start` - Start all services
- `./scripts/start.sh stop` - Stop all services
- `./scripts/start.sh status` - Check service status
- `./scripts/start.sh restart` - Restart all services

**Services Started:**
- PostgreSQL database
- FastAPI backend (port 8002)
- Next.js frontend (port 3000)

#### `start.bat` (Windows)
**Commands:**
- `scripts\start.bat` or `scripts\start.bat start` - Start all services
- `scripts\start.bat stop` - Stop all services
- `scripts\start.bat status` - Check service status
- `scripts\start.bat restart` - Restart all services

### Testing Script

#### `test.sh`
**Features:**
- Comprehensive health check of all services
- Database connection and schema validation
- Backend API testing
- Frontend accessibility testing
- Performance benchmarking
- Integration testing
- Detailed test report

**Usage:**
```bash
./scripts/test.sh
```

#### `demo.sh`
**Features:**
- Platform demonstration and feature showcase
- Service status overview
- Database schema and sample data display
- API endpoint documentation
- Frontend feature highlights
- Architecture overview
- Development workflow guidance

**Usage:**
```bash
./scripts/demo.sh
```

#### `health-check.sh` (macOS/Linux)
**Features:**
- Quick system health assessment
- Frontend, backend, and database connectivity tests
- API endpoint validation
- Environment configuration checks
- Database statistics and recent activity
- Color-coded status indicators
- Performance recommendations
- Quick access URLs

**Usage:**
```bash
./scripts/health-check.sh
```

#### `health-check.py` (Cross-platform)
**Features:**
- Python-based health check (works on Windows/macOS/Linux)
- Same functionality as bash version
- No shell dependencies
- Detailed error reporting
- JSON-compatible output option

**Usage:**
```bash
# With conda environment
conda activate qenergy-backend
python scripts/health-check.py

# Or direct Python
python3 scripts/health-check.py
```

#### `clean-database.sh`
**Features:**
- Safe database cleanup with automatic backup
- Multiple cleanup options:
  - Full cleanup (all data)
  - Reports only (uploads + history)
  - Analysis only (weekly reports)
  - Custom table selection
- Automatic backup creation before cleanup
- Backup restoration instructions
- Safety confirmations and warnings

**Usage:**
```bash
./scripts/clean-database.sh
```

**Cleanup Options:**
1. **Full cleanup** - Removes all data except projects table
2. **Reports only** - Cleans report_uploads and project_history
3. **Analysis only** - Cleans weekly_report_analysis
4. **Custom** - Choose specific tables to clean
5. **Backup only** - Create backup without cleanup

## 🔧 Prerequisites

### macOS
- Homebrew (installed automatically if missing)
- Administrator access for PostgreSQL installation

### Linux (Ubuntu/Debian)
- sudo access
- curl and wget
- systemd (for service management)

### Windows
- Administrator privileges
- PowerShell execution policy set to allow scripts
- Chocolatey (installed automatically if missing)

## 📊 Service Ports

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | Database |
| FastAPI Backend | 8002 | API Server |
| Next.js Frontend | 3000 | Web Application |

## 🛠️ Troubleshooting

### Common Issues

#### Installation Fails
1. **macOS/Linux**: Ensure you have sudo access
2. **Windows**: Run as Administrator
3. **Network**: Check internet connection for package downloads

#### Services Won't Start
1. **Port Conflicts**: Check if ports 3000, 8002, 5432 are available
2. **Dependencies**: Ensure all dependencies are installed
3. **Environment**: Check conda environment activation

#### Database Connection Issues
1. **PostgreSQL Service**: Ensure PostgreSQL is running
2. **Credentials**: Check `backend/.env` file
3. **Permissions**: Verify database user permissions

### Debug Commands

```bash
# Check service status
./scripts/start.sh status

# Test individual components
./scripts/test.sh

# Check logs
tail -f backend/logs/app.log  # Backend logs
tail -f .next/logs/*          # Frontend logs
```

## 🔄 Development Workflow

### Daily Development
```bash
# Start services
./scripts/start.sh

# Make changes to code...

# Test changes
./scripts/test.sh

# Stop services when done
./scripts/start.sh stop
```

### New Environment Setup
```bash
# Fresh installation
./scripts/install.sh

# Verify installation
./scripts/test.sh

# Start development
./scripts/start.sh
```

## 📝 Environment Variables

The scripts automatically create these environment files:

### Frontend (`.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:8002/api
```

### Backend (`backend/.env`)
```
DATABASE_URL=postgresql://qenergy_user:qenergy_password@localhost:5432/qenergy_platform
DB_HOST=localhost
DB_PORT=5432
DB_NAME=qenergy_platform
DB_USER=qenergy_user
DB_PASSWORD=qenergy_password
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_V1_STR=/api
PROJECT_NAME=QEnergy Platform
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## 🎯 Best Practices

1. **Always run tests** after installation or major changes
2. **Check service status** before starting development
3. **Use the scripts** instead of manual commands
4. **Keep environment files** updated with correct credentials
5. **Monitor logs** for debugging issues

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run `./scripts/test.sh` for detailed diagnostics
3. Check the main project README.md
4. Review service logs for error messages

---

## 📊 Database Inspection Tools

### check-database.py

Comprehensive database inspection tool with multiple viewing options:

**Basic Usage:**
```bash
# Quick database overview
python scripts/check-database.py summary

# List projects (with filtering)
python scripts/check-database.py projects --limit 20
python scripts/check-database.py projects --status 1  # Active projects only

# View project history
python scripts/check-database.py history --limit 10

# Check uploaded reports
python scripts/check-database.py uploads

# Recent activity (last 7 days)
python scripts/check-database.py recent --days 7

# Detailed project information
python scripts/check-database.py project 2ES00069

# Search across projects and history
python scripts/check-database.py search "Carmona"
python scripts/check-database.py search "Taurus"
```

**Example Output:**
```
📊 QEnergy Platform Database Summary
====================================
📁 Total Projects: 107
📋 Project History Records: 20
📄 Report Uploads: 1

🟢 Active Projects: 107  🔴 Inactive Projects: 0
🏢 Real Projects: 95     🤖 Virtual Projects: 12
```

### db-check.sh

Quick wrapper script for common database checks:

```bash
# Quick summary (default)
./scripts/db-check.sh

# Other commands with simpler syntax
./scripts/db-check.sh projects
./scripts/db-check.sh history
./scripts/db-check.sh search "project name"
```

**Key Features:**
- 📊 Database overview with counts and statistics
- 🏢 Project listings with status and type indicators  
- 📋 Project history with creation dates and summaries
- 📄 Report upload tracking
- 🔍 Powerful search across all data
- 📈 Recent activity monitoring
- 🤖 Virtual vs Real project identification

---

**Note**: These scripts are designed for development environments. For production deployment, additional security and configuration considerations apply.
