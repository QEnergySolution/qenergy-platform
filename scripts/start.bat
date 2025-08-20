@echo off
REM QEnergy Platform - Start Script for Windows
REM Starts all services (database, backend, frontend)

setlocal enabledelayedexpansion

echo ==========================================
echo   QEnergy Platform - Start Script
echo ==========================================
echo.

REM Function to check if service is running
:check_port
set port=%1
netstat -an | find ":%port% " | find "LISTENING" >nul
if %errorlevel% equ 0 (
    echo [INFO] Port %port% is in use
    exit /b 0
) else (
    echo [INFO] Port %port% is free
    exit /b 1
)

REM Function to start PostgreSQL
:start_postgres
echo [INFO] Starting PostgreSQL...
net start postgresql-x64-14 >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] PostgreSQL started
) else (
    echo [WARNING] PostgreSQL might already be running
)
timeout /t 3 /nobreak >nul
goto :eof

REM Function to start backend
:start_backend
echo [INFO] Starting backend...
cd backend
call conda activate qenergy-backend
start "QEnergy Backend" cmd /k "uvicorn app.main:app --reload --port 8002 --host 0.0.0.0"
cd ..
timeout /t 5 /nobreak >nul
echo [SUCCESS] Backend started on http://localhost:8002
goto :eof

REM Function to start frontend
:start_frontend
echo [INFO] Starting frontend...
start "QEnergy Frontend" cmd /k "pnpm dev"
timeout /t 10 /nobreak >nul
echo [SUCCESS] Frontend started on http://localhost:3000
goto :eof

REM Function to check services
:check_services
echo [INFO] Checking services...

REM Check database
call :check_port 5432
if %errorlevel% equ 0 (
    echo [SUCCESS] Database: Running on port 5432
) else (
    echo [ERROR] Database: Not running
)

REM Check backend
call :check_port 8002
if %errorlevel% equ 0 (
    echo [SUCCESS] Backend: Running on port 8002
    curl -s http://localhost:8002/api/health >nul 2>&1
    if %errorlevel% equ 0 (
        echo [SUCCESS] Backend API: Responding
    ) else (
        echo [WARNING] Backend API: Not responding
    )
) else (
    echo [ERROR] Backend: Not running
)

REM Check frontend
call :check_port 3000
if %errorlevel% equ 0 (
    echo [SUCCESS] Frontend: Running on port 3000
) else (
    echo [ERROR] Frontend: Not running
)
goto :eof

REM Function to stop all services
:stop_services
echo [INFO] Stopping all services...

REM Stop frontend
taskkill /f /im node.exe >nul 2>&1

REM Stop backend
taskkill /f /im python.exe >nul 2>&1

REM Stop PostgreSQL
net stop postgresql-x64-14 >nul 2>&1

echo [SUCCESS] All services stopped
goto :eof

REM Main function
:main
if "%1"=="" goto :start
if "%1"=="start" goto :start
if "%1"=="stop" goto :stop
if "%1"=="status" goto :status
if "%1"=="restart" goto :restart
goto :usage

:start
echo [INFO] Starting QEnergy Platform...

REM Start PostgreSQL
call :start_postgres

REM Start backend
call :start_backend

REM Start frontend
call :start_frontend

REM Check services
call :check_services

echo.
echo ==========================================
echo [SUCCESS] QEnergy Platform started successfully!
echo ==========================================
echo.
echo Services:
echo • Frontend: http://localhost:3000
echo • Backend API: http://localhost:8002/api
echo • API Docs: http://localhost:8002/docs
echo • Health Check: http://localhost:8002/api/health
echo.
echo To stop all services, run: %0 stop
echo.
pause
goto :eof

:stop
call :stop_services
pause
goto :eof

:status
call :check_services
pause
goto :eof

:restart
call :stop_services
timeout /t 2 /nobreak >nul
goto :start

:usage
echo Usage: %0 {start^|stop^|status^|restart}
echo   start   - Start all services (default)
echo   stop    - Stop all services
echo   status  - Check service status
echo   restart - Restart all services
pause
exit /b 1

:eof
