#!/bin/bash

# MLflow Setup Script
# This script prepares the volumes directory and starts the services

set -e

echo "=========================================="
echo "MLflow Docker Setup"
echo "=========================================="
echo ""

# Create volumes directory structure
echo "📁 Creating volumes directory structure..."
mkdir -p ~/volumes/postgres
mkdir -p ~/volumes/minio

echo "✅ Volumes directory created at ~/volumes"
echo ""

# Check if Docker is running
echo "🐳 Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi
echo "✅ Docker is running"
echo ""

# Start services
echo "🚀 Starting MLflow services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
echo "This may take 30-60 seconds..."
echo ""

# Wait for MLflow to be ready
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose logs mlflow 2>/dev/null | grep -q "Listening at"; then
        echo "✅ MLflow is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo -n "."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo ""
    echo "⚠️  Services are starting but may need more time"
    echo "Check logs with: docker-compose logs -f"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📊 Access your services:"
echo "  • MLflow UI:      http://localhost:5000"
echo "  • MinIO Console:  http://localhost:9001"
echo "                    (user: minio, password: minio123)"
echo ""
echo "💾 Data is stored in:"
echo "  ~/volumes/postgres"
echo "  ~/volumes/minio"
echo ""
echo "🧪 Test your setup:"
echo "  pip install mlflow scikit-learn boto3"
echo "  python tests/test_mlflow.py"
echo ""
echo "📝 Useful commands:"
echo "  docker-compose logs -f     # View logs"
echo "  docker-compose down        # Stop services"
echo "  docker-compose ps          # Check status"
echo ""
