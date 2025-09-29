@echo off
REM ARGO Platform Setup Script for Windows
REM This script sets up the development environment for the ARGO platform

echo 🌊 ARGO Oceanographic Data Platform Setup
echo =========================================

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📄 Creating .env file from template...
    copy .env.example .env
    echo ✅ .env file created. Please edit it with your API keys and configuration.
) else (
    echo ✅ .env file already exists.
)

REM Pull and build Docker images
echo 🐳 Pulling and building Docker images...
docker-compose pull
docker-compose build

REM Start the services
echo 🚀 Starting services...
docker-compose up -d

REM Wait for services to be ready
echo ⏳ Waiting for services to start...
timeout /t 30 /nobreak >nul

REM Display access information
echo.
echo 🎉 Setup Complete!
echo ==================
echo Frontend (Streamlit):    http://localhost:8501
echo Backend API:            http://localhost:8001
echo API Documentation:      http://localhost:8001/docs
echo Vector Database:        http://localhost:8000
echo.
echo Demo Login Credentials:
echo 📧 Scientist: scientist@argo.com (any password)
echo 📧 Policymaker: policy@argo.com (any password)
echo 📧 Student: student@argo.com (any password)
echo.
echo 📚 Check README.md for detailed usage instructions.
echo.
echo To stop services: docker-compose down
echo To view logs: docker-compose logs -f [service_name]

pause