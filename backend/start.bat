@echo off
echo ============================================
echo GraphRAG Backend - Quick Start Script
echo ============================================
echo.

REM Check Java version
echo [1/4] Checking Java version...
java -version
if errorlevel 1 (
    echo ERROR: Java is not installed or not in PATH
    echo Please install JDK 17 or higher
    pause
    exit /b 1
)
echo.

REM Start Docker services
echo [2/4] Starting Docker services...
docker-compose up -d postgres redis
if errorlevel 1 (
    echo WARNING: Docker services may not be available
    echo Please ensure Docker is running
)
echo.

REM Wait for services
echo [3/4] Waiting for services to be ready...
timeout /t 10 /nobreak > nul
echo.

REM Build and run
echo [4/4] Building and starting application...
call mvnw.cmd clean compile -DskipTests
if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo ============================================
echo Build completed successfully!
echo ============================================
echo.
echo To start the application, run:
echo   mvnw.cmd spring-boot:run -pl graphrag-gateway
echo.
echo API Documentation: http://localhost:8080/api/doc.html
echo Health Check: http://localhost:8080/api/health
echo.
pause
