#!/bin/bash

echo "============================================"
echo "GraphRAG Backend - Quick Start Script"
echo "============================================"
echo

# Check Java version
echo "[1/4] Checking Java version..."
java -version
if [ $? -ne 0 ]; then
    echo "ERROR: Java is not installed or not in PATH"
    echo "Please install JDK 17 or higher"
    exit 1
fi
echo

# Start Docker services
echo "[2/4] Starting Docker services..."
docker-compose up -d postgres redis
if [ $? -ne 0 ]; then
    echo "WARNING: Docker services may not be available"
    echo "Please ensure Docker is running"
fi
echo

# Wait for services
echo "[3/4] Waiting for services to be ready..."
sleep 10
echo

# Build and run
echo "[4/4] Building and starting application..."
./mvnw clean compile -DskipTests
if [ $? -ne 0 ]; then
    echo "ERROR: Build failed"
    exit 1
fi

echo
echo "============================================"
echo "Build completed successfully!"
echo "============================================"
echo
echo "To start the application, run:"
echo "  ./mvnw spring-boot:run -pl graphrag-gateway"
echo
echo "API Documentation: http://localhost:8080/api/doc.html"
echo "Health Check: http://localhost:8080/api/health"
echo
