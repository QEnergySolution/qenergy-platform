# QEnergy Backend (FastAPI)

## Setup with Conda

### 1. Create Conda Environment
```bash
cd backend
conda env create -f environment.yml
```

### 2. Activate Environment
```bash
conda activate qenergy-backend
```

### 3. Run Development Server
```bash
uvicorn app.main:app --reload --port 8002
```

### 4. Access API Documentation
- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

## Alternative Setup (if conda not available)

### Using pip/venv
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

## Environment Variables
Create `.env` file in backend directory:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/qenergy
SECRET_KEY=your-secret-key-here
```

## Development Commands
```bash
# Run with auto-reload
uvicorn app.main:app --reload --port 8002

# Run with specific host
uvicorn app.main:app --host 0.0.0.0 --port 8002

# Run in production mode
uvicorn app.main:app --host 0.0.0.0 --port 8002 --workers 4
```

