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

**Note**: These scripts are designed for development environments. For production deployment, additional security and configuration considerations apply.
