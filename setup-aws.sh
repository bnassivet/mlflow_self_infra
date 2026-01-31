#!/bin/bash

# MLflow with AWS S3 Setup Script
# This script prepares the environment and starts the services

set -e

echo "=========================================="
echo "MLflow Docker Setup (AWS S3 Version)"
echo "=========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found!"
    echo ""
    echo "Creating .env from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your AWS credentials:"
    echo "   - AWS_ACCESS_KEY_ID"
    echo "   - AWS_SECRET_ACCESS_KEY"
    echo "   - AWS_DEFAULT_REGION"
    echo "   - MLFLOW_S3_BUCKET"
    echo ""
    echo "Run this command to edit:"
    echo "   nano .env"
    echo ""
    read -p "Press Enter after you've configured .env, or Ctrl+C to exit..."
fi

# Validate .env has required values
echo "🔍 Validating .env configuration..."
source .env

if [ -z "$AWS_ACCESS_KEY_ID" ] || [ "$AWS_ACCESS_KEY_ID" = "your_aws_access_key_here" ]; then
    echo "❌ Error: AWS_ACCESS_KEY_ID not set in .env"
    exit 1
fi

if [ -z "$AWS_SECRET_ACCESS_KEY" ] || [ "$AWS_SECRET_ACCESS_KEY" = "your_aws_secret_key_here" ]; then
    echo "❌ Error: AWS_SECRET_ACCESS_KEY not set in .env"
    exit 1
fi

if [ -z "$MLFLOW_S3_BUCKET" ] || [ "$MLFLOW_S3_BUCKET" = "your-mlflow-bucket-name" ]; then
    echo "❌ Error: MLFLOW_S3_BUCKET not set in .env"
    exit 1
fi

echo "✅ .env configuration looks good"
echo ""

# Check if AWS CLI is available and verify bucket exists
if command -v aws &> /dev/null; then
    echo "🔍 Checking if S3 bucket exists..."
    if aws s3 ls "s3://$MLFLOW_S3_BUCKET" &> /dev/null; then
        echo "✅ S3 bucket '$MLFLOW_S3_BUCKET' exists"
    else
        echo "⚠️  Warning: Cannot access S3 bucket '$MLFLOW_S3_BUCKET'"
        echo "   Make sure:"
        echo "   1. The bucket exists in your AWS account"
        echo "   2. Your credentials have access to this bucket"
        echo "   3. The bucket is in region: ${AWS_DEFAULT_REGION:-us-east-1}"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo "ℹ️  AWS CLI not found - skipping bucket verification"
    echo "   Install AWS CLI to enable bucket checks: https://aws.amazon.com/cli/"
fi

echo ""

# Create volumes directory structure
echo "📁 Creating volumes directory..."
mkdir -p ~/volumes/postgres
echo "✅ Postgres volume created at ~/volumes/postgres"
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
docker-compose -f docker-compose-aws.yml up -d

echo ""
echo "⏳ Waiting for services to be ready..."
echo "This may take 30-60 seconds..."
echo ""

# Wait for MLflow to be ready
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose -f docker-compose-aws.yml logs mlflow 2>/dev/null | grep -q "Listening at"; then
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
    echo "Check logs with: docker-compose -f docker-compose-aws.yml logs -f"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📊 Access your services:"
echo "  • MLflow UI:      http://localhost:5000"
echo ""
echo "☁️  AWS Configuration:"
echo "  • S3 Bucket:      s3://$MLFLOW_S3_BUCKET/mlflow-artifacts/"
echo "  • Region:         ${AWS_DEFAULT_REGION:-us-east-1}"
echo ""
echo "💾 Local data storage:"
echo "  • PostgreSQL:     ~/volumes/postgres"
echo "  • Artifacts:      AWS S3 (cloud)"
echo ""
echo "🧪 Test your setup:"
echo "  pip install mlflow scikit-learn boto3"
echo "  python test_mlflow_aws.py"
echo ""
echo "📝 Useful commands:"
echo "  docker-compose -f docker-compose-aws.yml logs -f     # View logs"
echo "  docker-compose -f docker-compose-aws.yml down        # Stop services"
echo "  docker-compose -f docker-compose-aws.yml ps          # Check status"
echo ""
