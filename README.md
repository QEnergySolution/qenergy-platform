# QEnergy AI Analysis Platform

A comprehensive AI-powered platform for energy project management and weekly report analysis. Built with Next.js 15, FastAPI, and PostgreSQL.

## 🚀 Features

- **Project Management**: CRUD operations for energy projects with bulk import/export
- **Weekly Report Analysis**: AI-powered analysis of project reports with risk assessment
- **Multi-language Support**: Internationalization ready (EN, DE, ES, FR, PT, KO)

## 🏗️ Architecture

```
qenergy-platform/
├── frontend/          # Next.js 15 + TypeScript + Tailwind
├── backend/           # FastAPI + SQLAlchemy + PostgreSQL
└── shared/            # Shared types and constants
```

## 📋 Prerequisites

- **Node.js** 18+ 
- **Python** 3.11+
- **PostgreSQL** 15+
- **Conda** (recommended) or pip/venv
- **pnpm** (recommended) or npm

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd qenergy-platform
```

### 2. Frontend Setup
```bash
# Install dependencies
pnpm install

# Set environment variables
cp frontend/.env.example frontend/.env.local
# Edit frontend/.env.local with your configuration

# Start development server
pnpm dev
```

### 3. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create conda environment (recommended)
conda env create -f environment.yml
conda activate qenergy-backend

# Alternative: Using pip/venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
cp env.example .env
# Edit .env with your database configuration

# Start development server
uvicorn app.main:app --reload --port 8002
```

### 4. Database Setup
```bash
# Create PostgreSQL database
createdb qenergy_platform

# Run setup script to create tables and sample data
psql qenergy_platform < backend/setup-database.sql

# Verify setup
psql qenergy_platform -c "SELECT COUNT(*) FROM projects;"
```

## 🔧 Development

### Frontend Development
```bash
# Start development server
pnpm dev

# Build for production
pnpm build

# Run linting
pnpm lint

# Run type checking
pnpm type-check
```

### Backend Development
```bash
# Activate environment
conda activate qenergy-backend

# Start development server
uvicorn app.main:app --reload --port 8002

# Test API endpoints
curl http://localhost:8002/api/health

# Run tests (when available)
pytest

# Run database migrations (when Alembic is set up)
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### API Documentation
- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc
- **Health Check**: http://localhost:8002/api/health

## 📁 Project Structure

### Frontend (`frontend/`)
```
frontend/
├── app/                 # Next.js App Router
├── components/          # React components
│   ├── ui/             # shadcn/ui components
│   └── features/       # Feature-specific components
├── lib/                # Utilities and configurations
├── hooks/              # Custom React hooks
└── styles/             # Global styles
```

### Backend (`backend/`)
```
backend/
├── app/
│   ├── main.py         # FastAPI application entry
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── api/            # API routes
│   └── services/       # Business logic
├── alembic/            # Database migrations
└── tests/              # Test files
```

## 🌐 Environment Variables

### Frontend (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8002/api
NEXT_PUBLIC_APP_NAME=QEnergy Platform
```

### Backend (`.env`)
```env
DATABASE_URL=postgresql://qenergy_user:qenergy_password@localhost:5432/qenergy_platform
DB_HOST=localhost
DB_PORT=5432
DB_NAME=qenergy_platform
DB_USER=qenergy_user
DB_PASSWORD=qenergy_password
SECRET_KEY=your-super-secret-key-change-this-in-production
OPENAI_API_KEY=your-openai-api-key-here
```

## 🚀 Deployment

### Docker (Recommended)
```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Manual Deployment
1. Build frontend: `pnpm build`
2. Set production environment variables
3. Run backend with production server (Gunicorn)
4. Configure reverse proxy (Nginx)

## 🔄 Version History

- **v0.3.0** - Database setup complete, FastAPI backend running
- **v0.2.0** - Added AI analysis features
- **v0.1.0** - Project foundation and UI components
