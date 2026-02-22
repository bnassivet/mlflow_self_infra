# MLflow Test Suite

This directory contains tests for validating different MLflow Docker Compose setups.

## Test Files

### test_mlflow.py
Tests the **local MinIO setup** (`docker-compose.yml`).

**What it tests:**
- MLflow server connectivity
- PostgreSQL backend storage
- MinIO artifact storage
- Model training and logging
- Artifact upload/download
- Model serialization and loading

**Prerequisites:**
- Docker Compose services running: `docker-compose up -d`
- `.env` configured with MinIO credentials (defaults work out of the box):
  ```env
  MLFLOW_PORT=5010
  MINIO_API_PORT=9000
  MINIO_ROOT_USER=minio
  MINIO_ROOT_PASSWORD=minio123
  ```

**Run:**
```bash
MLFLOW_TRACKING_URI=http://localhost:5010 python tests/test_mlflow.py
```

### test_mlflow_aws.py
Tests the **AWS S3 setup** (`docker-compose-aws.yml`).

**What it tests:**
- MLflow server connectivity
- PostgreSQL backend storage
- AWS S3 artifact storage
- Model training and logging
- Artifact upload to S3
- Model serialization and loading

**Prerequisites:**
- Docker Compose services running: `docker-compose -f docker-compose-aws.yml up -d`
- AWS credentials in `.env`:
  ```env
  MLFLOW_PORT=5010
  AWS_ACCESS_KEY_ID=your-access-key
  AWS_SECRET_ACCESS_KEY=your-secret-key
  AWS_DEFAULT_REGION=us-east-1
  MLFLOW_S3_BUCKET=your-bucket-name
  ```

**Run:**
```bash
MLFLOW_TRACKING_URI=http://localhost:5010 python tests/test_mlflow_aws.py
```

## Running Tests

### Using Python directly

```bash
# Test local MinIO setup
MLFLOW_TRACKING_URI=http://localhost:5010 python tests/test_mlflow.py

# Test AWS S3 setup
MLFLOW_TRACKING_URI=http://localhost:5010 python tests/test_mlflow_aws.py
```

### Using pytest

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_mlflow.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=term-missing
```

## Test Configuration

Tests use `conftest.py` for shared fixtures and configuration:
- `load_env`: Automatically loads `.env` file
- `mlflow_tracking_uri`: MLflow server URI (reads `MLFLOW_PORT` from `.env`)
- `minio_config`: MinIO configuration fixture
- `aws_config`: AWS configuration fixture

## Creating New Tests

When adding new tests:

1. Create a new test file: `test_<feature>.py`
2. Use the provided fixtures from `conftest.py`
3. Follow the naming convention: test functions should start with `test_`
4. Document prerequisites and what the test validates

Example:
```python
def test_langchain_integration(mlflow_tracking_uri):
    """Test LangChain model logging"""
    import mlflow
    from langchain_openai import ChatOpenAI

    mlflow.set_tracking_uri(mlflow_tracking_uri)
    # ... test implementation
```

## Troubleshooting

**Tests fail with connection errors:**
- Ensure Docker services are running
- Wait 30-60 seconds after starting services
- Check the port in `MLFLOW_PORT` matches what you're connecting to
- Check logs: `docker-compose logs -f mlflow`

**AWS tests fail:**
- Verify AWS credentials in `.env`
- Check S3 bucket exists and has correct permissions
- Ensure IAM user has required S3 permissions

**Import errors:**
- Activate virtual environment: `source .venv/bin/activate`
- Install dependencies: `uv pip install -e .`
