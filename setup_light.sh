#!/bin/bash

# MLflow Light Setup Script
# Single-service setup: SQLite metadata + local volume artifacts (no Postgres, no MinIO)

set -e

# Load port configuration from .env if present
if [ -f .env ]; then
    set -o allexport
    source .env
    set +o allexport
fi
MLFLOW_PORT="${MLFLOW_PORT:-5010}"

echo "=========================================="
echo "MLflow Light Setup (SQLite + local volume)"
echo "=========================================="
echo ""

# Create volumes directory structure
echo "📁 Creating volumes directory..."
mkdir -p ~/volumes/mlflow-light/db
mkdir -p ~/volumes/mlflow-light/artifacts
echo "✅ Volumes directory created at ~/volumes/mlflow-light"
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
echo "🚀 Starting MLflow..."
docker compose -f docker-compose-local-light.yml up -d

echo ""
echo "⏳ Waiting for MLflow to be ready..."
echo "This may take a minute (pip install on first run)..."
echo ""

# Wait for MLflow to be ready
max_attempts=60
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker compose -f docker-compose-local-light.yml logs mlflow 2>/dev/null | grep -q "Listening at"; then
        echo "✅ MLflow is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo -n "."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo ""
    echo "⚠️  MLflow is starting but may need more time"
    echo "Check logs with: docker compose -f docker-compose-local-light.yml logs -f"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📊 Access MLflow UI: http://localhost:${MLFLOW_PORT}"
echo ""
echo "💾 Data is stored in: ~/volumes/mlflow-light"
echo "   ~/volumes/mlflow-light/db          # SQLite database"
echo "   ~/volumes/mlflow-light/artifacts   # MLflow artifacts"
echo ""
echo "🧪 Test your setup:"
echo "  pip install mlflow"
echo "  MLFLOW_TRACKING_URI=http://localhost:${MLFLOW_PORT} python tests/test_mlflow.py"
echo ""
echo "📝 Useful commands:"
echo "  docker compose -f docker-compose-local-light.yml logs -f   # View logs"
echo "  docker compose -f docker-compose-local-light.yml down      # Stop services"
echo "  rm -rf ~/volumes/mlflow-light                         # Delete all data"
echo "  docker compose -f docker-compose-local-light.yml ps        # Check status"
echo ""
