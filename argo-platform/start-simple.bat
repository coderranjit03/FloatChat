@echo off
echo Starting ARGO Platform Prototype...
echo.

echo Stopping any existing containers...
docker-compose -f docker-compose-simple.yml down

echo.
echo Building and starting the platform...
docker-compose -f docker-compose-simple.yml up --build -d

echo.
echo Waiting for services to start...
timeout /t 10

echo.
echo Checking service status...
docker-compose -f docker-compose-simple.yml ps

echo.
echo ============================================
echo ARGO Platform Prototype is starting up!
echo ============================================
echo.
echo Frontend (Streamlit): http://localhost:8501
echo Backend API: http://localhost:8001
echo API Documentation: http://localhost:8001/docs
echo.
echo Demo Login Credentials:
echo - Scientist: scientist@argo.com (any password)
echo - Policy Maker: policy@argo.com (any password)  
echo - Student: student@argo.com (any password)
echo.
echo Press any key to view logs...
pause
docker-compose -f docker-compose-simple.yml logs -f