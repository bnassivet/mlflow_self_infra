# AGENTS.md

This file provides guidance to AI agents when working with code in this repository.

## Overview

MLflow tracking server infrastructure with two deployment configurations:
1. **Local setup** (docker-compose.yml): PostgreSQL + RustFS (S3-compatible storage)
2. **AWS setup** (docker-compose-aws.yml): PostgreSQL + AWS S3

Both configurations use PostgreSQL 15 for metadata/experiment tracking and MLflow server
running on Python 3.12-slim. The key architectural difference is artifact storage: RustFS
for local development vs. AWS S3 for production/cloud environments.

## Common Commands

### Starting Services

**Local (RustFS) setup:**
```bash
# Quick start with setup script
./setup.sh

# Or manually
mkdir -p ~/volumes/postgres ~/volumes/rustfs
docker-compose up -d
```

**AWS (S3) setup:**
```bash
# Configure credentials first
cp .env.example .env
# Edit .env with AWS credentials and S3 bucket name

# Quick start with setup script
./setup-aws.sh

# Or manually
mkdir -p ~/volumes/postgres
docker-compose -f docker-compose-aws.yml up -d
```

### Service Management

```bash
# View logs (all services)
docker-compose logs -f

# View specific service logs
docker-compose logs -f mlflow
docker-compose logs -f postgres
docker-compose logs -f rustfs  # local setup only

# Check service status
docker-compose ps

# Restart MLflow server
docker-compose restart mlflow

# Stop services
docker-compose down

```

### Testing the Setup

**Install dependencies:**
```bash
pip install mlflow scikit-learn boto3
```

**Run test scripts:**
```bash
# Test local RustFS setup
python test_mlflow.py

# Test AWS S3 setup
python test_mlflow_aws.py
```

**Manual test:**
```bash
# Local setup
export MLFLOW_TRACKING_URI=http://localhost:5000
export MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
export AWS_ACCESS_KEY_ID=rustfs
export AWS_SECRET_ACCESS_KEY=rustfs123

# AWS setup
export MLFLOW_TRACKING_URI=http://localhost:5000
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

## Architecture

### Service Dependencies

**Local setup:**
1. PostgreSQL starts first (with healthcheck)
2. RustFS starts (with healthcheck)
3. rustfs-setup container creates bucket (waits for RustFS healthy)
4. MLflow server starts (waits for PostgreSQL healthy, RustFS healthy, rustfs-setup completed)

**AWS setup:**
1. PostgreSQL starts first (with healthcheck)
2. MLflow server starts (waits for PostgreSQL healthy)

### Network Configuration

All services run on a custom bridge network `mlflow-network`. Services communicate using
container names as hostnames (e.g., `postgres:5432`, `rustfs:9000`).

### Data Persistence

**PostgreSQL:**
- Volume: `~/volumes/postgres:/var/lib/postgresql/data`
- Connection URI: `postgresql://mlflow:mlflow123@postgres:5432/mlflow`
- Port: 5432 (exposed to host)

**RustFS (local only):**
- Volume: `~/volumes/rustfs:/data`
- API Port: 9000 (S3-compatible API)
- Console Port: 9001 (web UI)
- Bucket: `mlflow` (auto-created by rustfs-setup container)

**AWS S3 (AWS setup only):**
- Bucket name configured via `.env` file: `MLFLOW_S3_BUCKET`
- Artifacts stored at: `s3://${MLFLOW_S3_BUCKET}/mlflow-artifacts/`

### MLflow Server Configuration

Both setups run MLflow with:
- Backend store: PostgreSQL (experiments, runs, metrics, params)
- Artifact root: S3 or S3-compatible storage (models, artifacts, files)
- Host: 0.0.0.0:5000
- Python dependencies installed at runtime: mlflow, psycopg2-binary, boto3

### MLflow Assistant (Beta)

The assistant API (`/ajax-api/3.0/mlflow/assistant/*`) is gated per route in
`mlflow/server/assistant/api.py`. `_is_localhost()` checks `request.client.host` for a
loopback IP; under Docker that is the bridge gateway, never `127.0.0.1`, so every gated
route 403s with "You do not have permission to access this resource".

Route policies:
- `DENY` — `PUT /config`, `POST /skills/install`. Always blocked remotely. **Config
  changes must be made server-side**, not through the settings panel's Save button.
- `ONLY_SAFE_PROVIDER` — chat, sessions, models. Allowed only when
  `MLFLOW_ENABLE_REMOTE_ASSISTANT=true` **and** the provider declares
  `allows_remote_access`. Ollama / OpenAI-compatible providers return `False`
  unconditionally; `mlflow_gateway` returns `True`; `claude_code`/`codex` only under
  `MLFLOW_ENABLE_ASSISTANT_SANDBOX`.
- `NONE` — `GET /config`, `GET /providers`.

Consequences for this repo:
- `MLFLOW_PORT` is the host **and** container port. The assistant derives its gateway
  self-call URL from the browser's `Host` header (`get_server_base_url` in
  `mlflow/server/asgi_utils.py`), so mismatched ports make the server dial a closed port.
- Assistant config lives at `$HOME/.mlflow/assistant/config.json` in the container and is
  persisted via the `~/volumes/mlflow-assistant` mount.
- `scripts/setup_assistant.py` (mounted at `/scripts`) creates the gateway secret, model
  definition and endpoint, then selects the `mlflow_gateway` provider. Run it with
  `docker compose exec mlflow python /scripts/setup_assistant.py --model <model>`.
- Two gotchas the script encodes: `api_base` belongs in the secret's `auth_config`, not
  its `secret_value`; and the store caches resolved endpoint configs (`store.secret_cache`),
  so **restart the mlflow service after any gateway change**.
- All three compose files are wired identically; for the light config pass
  `-f docker-compose-local-light.yml`. The AI Gateway only needs a database-backed store,
  which SQLite satisfies, so it needs no Postgres. Its assistant config persists under
  `~/volumes/mlflow-light/assistant`.
- An OpenAI-compatible local server (Ollama, LM Studio, vLLM) is registered as
  `provider="openai"` with an `api_base` override — there is no dedicated Ollama gateway
  provider.

## Configuration Files

### docker-compose.yml
Local development setup with RustFS. Uses hardcoded credentials (not production-ready).

### docker-compose-aws.yml
AWS S3 integration. Requires `.env` file with:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION` (defaults to us-east-1)
- `MLFLOW_S3_BUCKET`

### .env.example
Template for AWS credentials. Copy to `.env` and fill in actual values. Never commit `.env`
to version control.

## Default Credentials

**Local PostgreSQL:**
- User: `mlflow`
- Password: `mlflow123`
- Database: `mlflow`
- Port: 5432

**RustFS (local only):**
- Access Key: `rustfs`
- Secret Key: `rustfs123`
- Console login: same credentials

## Test Scripts

### test_mlflow.py
Tests local RustFS setup. Trains a RandomForest classifier on iris dataset, logs
parameters/metrics/artifacts, and demonstrates model loading. Expects services running
on localhost:5000 (MLflow) and localhost:9000 (RustFS).

### test_mlflow_aws.py
Tests AWS S3 setup. Similar workflow but connects to AWS S3 for artifacts. Requires
AWS credentials configured.

## Modifying Credentials

To change PostgreSQL credentials:
1. Edit environment variables in docker-compose.yml (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB)
2. Update DB_URI in mlflow service to match
3. Restart: `docker-compose up -d`

To change RustFS credentials (local only):
1. Edit RUSTFS_ROOT_USER and RUSTFS_ROOT_PASSWORD in docker-compose.yml (or `.env`)
2. Update AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in mlflow service
3. Update rustfs-setup entrypoint script with new credentials
4. Restart: `docker-compose up -d`

## UI Access

- **MLflow UI:** http://localhost:5000
  - View experiments, runs, metrics, parameters
  - Compare runs, visualize metrics
  - Access model registry

- **RustFS Console** (local only): http://localhost:9001
  - Browse buckets and artifacts
  - Monitor storage usage
  - Login: rustfs/rustfs123
