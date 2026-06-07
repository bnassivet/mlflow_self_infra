# Python Environment Setup with UV

This guide explains how to set up the Python testing environment for the MLflow Docker Compose infrastructure using `uv`.

## Prerequisites

1. **Install uv** (if not already installed):
   ```bash
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Or using pip
   pip install uv

   # Or using Homebrew (macOS)
   brew install uv
   ```

2. **Docker Desktop** running (for MLflow services)

## Quick Start

### 1. Create Virtual Environment with Python 3.12

```bash
# uv will automatically use Python 3.12 based on .python-version file
uv venv
```

This creates a `.venv` directory with Python 3.12.

### 2. Activate Virtual Environment

```bash
# On macOS/Linux
source .venv/bin/activate

# On Windows
.venv\Scripts\activate
```

### 3. Install Dependencies

**Install core dependencies (for local RustFS testing):**
```bash
uv pip install -e .
```

**Install with AWS support (for production S3 testing):**
```bash
uv pip install -e ".[aws]"
```

**Install with development tools:**
```bash
uv pip install -e ".[dev]"
```

**Install everything:**
```bash
uv pip install -e ".[all]"
```

## Using UV for Dependency Management

### Add New Dependency

```bash
# Add to core dependencies
uv pip install <package-name>

# Then update pyproject.toml manually to persist
```

### Update Dependencies

```bash
# Update all packages to latest compatible versions
uv pip install --upgrade -e .
```

### Sync Dependencies from pyproject.toml

```bash
# Install exactly what's in pyproject.toml
uv pip sync
```

## Project Dependencies

### Core Dependencies (Always Installed)

- **MLflow 3.6.0+** with GenAI features
- **boto3**: S3/RustFS client
- **scikit-learn**: ML library for test examples
- **numpy**: Numerical computing
- **openai, anthropic, litellm**: LLM provider SDKs
- **langchain**: LangChain framework for GenAI
- **python-dotenv**: Environment variable management

### Optional Dependencies

#### AWS (`[aws]`)
- **awscli**: AWS CLI tools
- Enhanced boto3 support

#### Development (`[dev]`)
- **pytest**: Testing framework
- **black**: Code formatter
- **ruff**: Fast Python linter
- **mypy**: Type checker

## Running Tests

### 1. Start MLflow Services

```bash
# Start Docker Compose services
docker-compose up -d

# Wait for services to be ready (30-60 seconds)
docker-compose logs -f mlflow
```

### 2. Configure Environment

Edit `.env` file with your API keys:
```bash
# Required for GenAI features
OPENAI_API_KEY=sk-proj-your-actual-key
ANTHROPIC_API_KEY=sk-ant-your-actual-key
```

### 3. Run Test Scripts

**Test basic MLflow setup:**
```bash
python tests/test_mlflow.py
```

**Test AWS S3 setup:**
```bash
python tests/test_mlflow_aws.py
```

**Test GenAI features (create this based on plan):**
```bash
python tests/test_genai.py
```

**Test LangChain integration (create this based on plan):**
```bash
python tests/test_langchain.py
```

### 4. Run with pytest (if you have tests/ directory)

```bash
pytest
```

## Environment Variables

The project uses `.env` file for configuration. Copy from template:

```bash
cp .env.example .env
# Then edit .env with your actual credentials
```

**For Local Testing (RustFS):**
```bash
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
AWS_ACCESS_KEY_ID=rustfs
AWS_SECRET_ACCESS_KEY=rustfs123
```

**For AWS Testing (with aws optional dependency):**
```bash
MLFLOW_TRACKING_URI=http://localhost:5000
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_DEFAULT_REGION=us-east-1
MLFLOW_S3_BUCKET=your-mlflow-bucket
```

**For GenAI Features:**
```bash
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
```

## UV Commands Cheatsheet

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install project in editable mode
uv pip install -e .

# Install with optional dependencies
uv pip install -e ".[aws]"      # AWS support
uv pip install -e ".[dev]"      # Dev tools
uv pip install -e ".[all]"      # Everything

# Install a package
uv pip install <package-name>

# Uninstall a package
uv pip uninstall <package-name>

# List installed packages
uv pip list

# Freeze dependencies
uv pip freeze > requirements.txt

# Compile dependencies (create lock file)
uv pip compile pyproject.toml -o requirements.txt

# Sync environment with requirements
uv pip sync requirements.txt

# Update all packages
uv pip install --upgrade -e .

# Deactivate virtual environment
deactivate
```

## Troubleshooting

### Python 3.12 Not Found

If uv can't find Python 3.12:

```bash
# Install Python 3.12 via pyenv
pyenv install 3.12

# Or specify Python explicitly
uv venv --python 3.12
```

### Package Installation Fails

```bash
# Clear uv cache
uv cache clean

# Reinstall
uv pip install -e . --reinstall
```

### Import Errors

Make sure virtual environment is activated:
```bash
which python  # Should point to .venv/bin/python
```

## Advantages of Using UV

- **Fast**: 10-100x faster than pip
- **Reliable**: Deterministic dependency resolution
- **Modern**: Written in Rust, actively maintained
- **Compatible**: Works with existing pip/setuptools ecosystem
- **Simple**: Drop-in replacement for pip commands

## Next Steps

1. Create virtual environment: `uv venv`
2. Activate it: `source .venv/bin/activate`
3. Install dependencies: `uv pip install -e .`
4. Start Docker services: `docker-compose up -d`
5. Run tests: `python tests/test_mlflow.py`

For more information:
- UV Documentation: https://docs.astral.sh/uv/
- MLflow Documentation: https://mlflow.org/docs/latest/
