@echo off
REM QEnergy Platform - One-Click Installation Script for Windows
REM Requires PowerShell and Chocolatey

setlocal enabledelayedexpansion

echo ==========================================
echo   QEnergy Platform - Installation Script
echo ==========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script must be run as Administrator
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Check if Chocolatey is installed
where choco >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Installing Chocolatey...
    powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to install Chocolatey
        pause
        exit /b 1
    )
    echo [SUCCESS] Chocolatey installed successfully
) else (
    echo [INFO] Chocolatey already installed
)

REM Install Node.js
echo [INFO] Installing Node.js...
choco install nodejs -y
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install Node.js
    pause
    exit /b 1
)

REM Install pnpm
echo [INFO] Installing pnpm...
npm install -g pnpm
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install pnpm
    pause
    exit /b 1
)

REM Install PostgreSQL
echo [INFO] Installing PostgreSQL...
choco install postgresql -y
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install PostgreSQL
    pause
    exit /b 1
)

REM Install Miniconda
echo [INFO] Installing Miniconda...
choco install miniconda3 -y
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install Miniconda
    pause
    exit /b 1
)

REM Refresh environment variables
call refreshenv

REM Start PostgreSQL service
echo [INFO] Starting PostgreSQL service...
net start postgresql-x64-14
if %errorLevel% neq 0 (
    echo [WARNING] PostgreSQL service might already be running
)

REM Setup database
echo [INFO] Setting up database...
psql -U postgres -c "CREATE USER qenergy_user WITH SUPERUSER PASSWORD 'qenergy_password';" 2>nul || echo [INFO] User might already exist
psql -U postgres -c "CREATE DATABASE qenergy_platform OWNER qenergy_user;" 2>nul || echo [INFO] Database might already exist

REM Import schema
if exist "backend\setup-database.sql" (
    psql -h localhost -U qenergy_user -d qenergy_platform -f backend\setup-database.sql
    echo [SUCCESS] Database schema imported
) else (
    echo [ERROR] Database schema file not found
    pause
    exit /b 1
)

REM Setup backend
echo [INFO] Setting up backend...
cd backend

REM Create conda environment
call conda env create -f environment.yml
if %errorLevel% neq 0 (
    call conda env update -f environment.yml
)

REM Activate environment and install dependencies
call conda activate qenergy-backend
pip install -r requirements.txt

REM Copy environment file
if not exist ".env" (
    copy env.example .env
    echo [WARNING] Please update backend\.env with your database credentials
)

cd ..

REM Setup frontend
echo [INFO] Setting up frontend...
pnpm install

REM Create environment file if not exists
if not exist ".env.local" (
    echo NEXT_PUBLIC_API_URL=http://localhost:8002/api > .env.local
    echo [SUCCESS] Frontend environment file created
)

REM Verify installation
echo [INFO] Verifying installation...

REM Check Node.js
node --version >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=*" %%i in ('node --version') do echo [SUCCESS] Node.js: %%i
) else (
    echo [ERROR] Node.js not found
)

REM Check pnpm
pnpm --version >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=*" %%i in ('pnpm --version') do echo [SUCCESS] pnpm: %%i
) else (
    echo [ERROR] pnpm not found
)

REM Check PostgreSQL
psql --version >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=*" %%i in ('psql --version') do echo [SUCCESS] PostgreSQL: %%i
) else (
    echo [ERROR] PostgreSQL not found
)

REM Check Conda
conda --version >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=*" %%i in ('conda --version') do echo [SUCCESS] Conda: %%i
) else (
    echo [ERROR] Conda not found
)

REM Check database connection
psql -h localhost -U qenergy_user -d qenergy_platform -c "SELECT COUNT(*) FROM projects;" >nul 2>&1
if %errorLevel% equ 0 (
    echo [SUCCESS] Database connection: OK
) else (
    echo [WARNING] Database connection: Please check credentials
)

echo.
echo ==========================================
echo [SUCCESS] Installation completed successfully!
echo ==========================================
echo.
echo Next steps:
echo 1. Update backend\.env with your database credentials
echo 2. Start the backend: cd backend ^&^& conda activate qenergy-backend ^&^& uvicorn app.main:app --reload --port 8002
echo 3. Start the frontend: pnpm dev
echo 4. Open http://localhost:3000 in your browser
echo.
echo For more information, see README.md
echo.
pause
