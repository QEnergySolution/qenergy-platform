# PostgreSQL Local Setup Guide

This guide will help you set up PostgreSQL locally for the QEnergy platform development.

## 🐘 Installation by Operating System

### macOS (using Homebrew)

```bash
# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Create database
createdb qenergy_platform

# Connect to database and run setup script
psql qenergy_platform < setup-database.sql
```

### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE qenergy_platform;
CREATE USER qenergy_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE qenergy_platform TO qenergy_user;
\q

# Run setup script
psql -U qenergy_user -d qenergy_platform -f setup-database.sql
```

### Windows

1. **Download PostgreSQL** from [postgresql.org](https://www.postgresql.org/download/windows/)
2. **Run installer** and follow the setup wizard
3. **Set password** for postgres user
4. **Open pgAdmin** or Command Prompt
5. **Create database**:
   ```sql
   CREATE DATABASE qenergy_platform;
   ```
6. **Run setup script**:
   ```bash
   psql -U postgres -d qenergy_platform -f setup-database.sql
   ```

### Using Docker (Recommended for Development)

```bash
# Create PostgreSQL container
docker run --name qenergy-postgres \
  -e POSTGRES_DB=qenergy_platform \
  -e POSTGRES_USER=qenergy_user \
  -e POSTGRES_PASSWORD=qenergy_password \
  -p 5432:5432 \
  -d postgres:15

# Run setup script
docker exec -i qenergy-postgres psql -U qenergy_user -d qenergy_platform < setup-database.sql
```

## 🔧 Database Configuration

### Environment Variables

Create `backend/.env` file:

```env
DATABASE_URL=postgresql://qenergy_user:qenergy_password@localhost:5432/qenergy_platform
DB_HOST=localhost
DB_PORT=5432
DB_NAME=qenergy_platform
DB_USER=qenergy_user
DB_PASSWORD=qenergy_password
```

### Connection Testing

```bash
# Test connection
psql -h localhost -U qenergy_user -d qenergy_platform

# List tables
\dt

# Check sample data
SELECT * FROM projects LIMIT 5;
```

## 📊 Database Schema Overview

### Tables Created

1. **`projects`** - Main project information
   - `project_code` (VARCHAR(32), UNIQUE) - Business identifier
   - `project_name` (VARCHAR(255)) - Project name
   - `portfolio_cluster` (VARCHAR(128)) - Portfolio/Cluster
   - `status` (INTEGER) - 0=Inactive, 1=Active
   - Audit fields: `created_at`, `created_by`, `updated_at`, `updated_by`

2. **`project_history`** - Weekly project reports
   - `project_code` (FK to projects)
   - `log_date` (DATE) - Report date
   - `cw_label` (VARCHAR(8)) - Calendar week label
   - `summary` (TEXT) - Report content
   - `entry_type` (ENUM) - Report type
   - Unique constraint: `(project_code, log_date)`

3. **`weekly_report_analysis`** - AI analysis results
   - `project_code` (FK to projects)
   - `cw_label` (VARCHAR(8)) - Analysis week
   - `risk_lvl` (DECIMAL(5,2)) - Risk percentage
   - `similarity_lvl` (DECIMAL(5,2)) - Similarity percentage
   - `negative_words` (JSONB) - Negative keywords
   - Unique constraint: `(project_code, cw_label, language)`

### Extensions Enabled

- **`pgcrypto`** - Cryptographic functions for UUID generation
- **`uuid-ossp`** - UUID generation functions

### Indexes Created

- Performance indexes on frequently queried columns
- Composite indexes for complex queries
- Descending indexes for sorting

## 🚀 Quick Start Commands

```bash
# 1. Install PostgreSQL (choose your OS method above)

# 2. Create database
createdb qenergy_platform

# 3. Run setup script
psql qenergy_platform < backend/setup-database.sql

# 4. Test connection
psql qenergy_platform -c "SELECT COUNT(*) FROM projects;"

# 5. Start backend (make sure .env is configured)
cd backend
conda activate qenergy-backend
uvicorn app.main:app --reload --port 8000
```

## 🔍 Verification

After setup, verify everything works:

```sql
-- Check tables exist
\dt

-- Check sample data
SELECT project_code, project_name, status FROM projects;

-- Check extensions
SELECT * FROM pg_extension WHERE extname IN ('pgcrypto', 'uuid-ossp');

-- Check indexes
\di
```

## 🛠️ Troubleshooting

### Common Issues

1. **Connection refused**
   ```bash
   # Check if PostgreSQL is running
   brew services list | grep postgresql  # macOS
   sudo systemctl status postgresql     # Linux
   ```

2. **Permission denied**
   ```bash
   # Grant permissions
   sudo -u postgres psql
   GRANT ALL PRIVILEGES ON DATABASE qenergy_platform TO qenergy_user;
   ```

3. **Database doesn't exist**
   ```bash
   # Create database
   createdb qenergy_platform
   ```

4. **Extensions not found**
   ```sql
   -- Install extensions
   CREATE EXTENSION IF NOT EXISTS "pgcrypto";
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   ```

### Reset Database

```bash
# Drop and recreate database
dropdb qenergy_platform
createdb qenergy_platform
psql qenergy_platform < backend/setup-database.sql
```

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
