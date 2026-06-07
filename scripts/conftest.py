"""
Pytest configuration for MLflow test suite
"""

import os
import pytest
from dotenv import load_dotenv


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables from .env file for all tests"""
    load_dotenv()


@pytest.fixture
def mlflow_tracking_uri():
    """MLflow tracking server URI"""
    return os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")


@pytest.fixture
def rustfs_config():
    """RustFS (S3) configuration for local testing"""
    return {
        "endpoint_url": os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://localhost:9000"),
        "access_key": os.getenv("AWS_ACCESS_KEY_ID", "rustfs"),
        "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY", "rustfs123"),
    }


@pytest.fixture
def aws_config():
    """AWS configuration for production testing"""
    return {
        "access_key": os.getenv("AWS_ACCESS_KEY_ID"),
        "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "region": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        "bucket": os.getenv("MLFLOW_S3_BUCKET"),
    }
