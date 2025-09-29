@echo off
echo 🌊 Starting ARGO Oceanographic Data Platform...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Desktop is not running. Please start Docker Desktop first.
    echo 📋 Instructions:
    echo    1. Open Docker Desktop from Start menu
    echo    2. Wait for it to fully start 
    echo    3. Run this script again
    echo.
    pause
    exit /b 1
)

echo ✅ Docker is running
echo.

REM Navigate to project directory
cd /d "C:\Users\aafre\OneDrive\Desktop\FloatChat\argo-platform"

REM Start the services
echo 🐳 Starting platform services...
docker-compose up -d

if %errorlevel% equ 0 (
    echo.
    echo 🎉 Platform started successfully!
    echo ==============================
    echo.
    echo 🌐 Access Points:
    echo    Frontend Dashboard: http://localhost:8501
    echo    API Documentation:  http://localhost:8001/docs
    echo    Vector Database:    http://localhost:8000
    echo.
    echo 🔑 Demo Login Credentials:
    echo    Scientist:     scientist@argo.com
    echo    Policymaker:   policy@argo.com
    echo    Student:       student@argo.com
    echo    Password:      Any value works for demo
    echo.
    echo 💡 Try these natural language queries:
    echo    "Show temperature trends in the North Atlantic"
    echo    "Find salinity anomalies near the equator"
    echo    "What's the average temperature at 1000m depth?"
    echo.
    echo Press any key to open the frontend in your browser...
    pause >nul
    start http://localhost:8501
) else (
    echo ❌ Failed to start services. Check Docker Desktop is running.
    echo 🔍 To debug: docker-compose logs
)

pause