#!/bin/bash

# ARGO Platform Setup Script
# This script sets up the development environment for the ARGO platform

set -e

echo "🌊 ARGO Oceanographic Data Platform Setup"
echo "========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your API keys and configuration."
else
    echo "✅ .env file already exists."
fi

# Pull and build Docker images
echo "🐳 Pulling and building Docker images..."
docker-compose pull
docker-compose build

# Start the services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
services=("postgres" "redis" "chroma" "backend" "frontend")

for service in "${services[@]}"; do
    if docker-compose ps "$service" | grep -q "Up"; then
        echo "✅ $service is running"
    else
        echo "❌ $service is not running"
        docker-compose logs "$service"
    fi
done

# Display access information
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo "Frontend (Streamlit):    http://localhost:8501"
echo "Backend API:            http://localhost:8001"
echo "API Documentation:      http://localhost:8001/docs"
echo "Vector Database:        http://localhost:8000"
echo ""
echo "Demo Login Credentials:"
echo "📧 Scientist: scientist@argo.com (any password)"
echo "📧 Policymaker: policy@argo.com (any password)"
echo "📧 Student: student@argo.com (any password)"
echo ""
echo "📚 Check README.md for detailed usage instructions."
echo ""
echo "To stop services: docker-compose down"
echo "To view logs: docker-compose logs -f [service_name]"