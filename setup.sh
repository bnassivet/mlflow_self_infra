#!/bin/bash

# MLflow Setup Script
# This script prepares the volumes directory and starts the services

set -e

# Load port configuration from .env if present
if [ -f .env ]; then
    set -o allexport
    source .env
    set +o allexport
fi
MLFLOW_PORT="${MLFLOW_PORT:-5010}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
RUSTFS_API_PORT="${RUSTFS_API_PORT:-9000}"
RUSTFS_CONSOLE_PORT="${RUSTFS_CONSOLE_PORT:-9001}"

echo "=========================================="
echo "MLflow Docker Setup"
echo "=========================================="
echo ""

# Create volumes directory structure
echo "📁 Creating volumes directory structure..."
mkdir -p ~/volumes/postgres
mkdir -p ~/volumes/rustfs
# RustFS runs as non-root UID 10001. On a Linux host the data dir must be owned
# by that UID; on macOS Docker Desktop handles bind-mount ownership in its VM, so
# only chown when running on a native Linux host.
if [ "$(uname)" = "Linux" ]; then
    sudo chown -R 10001:10001 ~/volumes/rustfs 2>/dev/null \
        || echo "⚠️  Could not chown ~/volumes/rustfs to 10001 — RustFS may fail to write /data"
fi

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
echo "  • MLflow UI:      http://localhost:${MLFLOW_PORT}"
echo "  • RustFS Console: http://localhost:${RUSTFS_CONSOLE_PORT}"
echo "                    (user: rustfs, password: rustfs123)"
echo ""
echo "💾 Data is stored in:"
echo "  ~/volumes/postgres"
echo "  ~/volumes/rustfs"
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
