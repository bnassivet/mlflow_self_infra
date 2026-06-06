# MLflow with PostgreSQL and RustFS - Docker Setup

This Docker Compose setup provides a complete MLflow tracking server with:
- **PostgreSQL** for metadata and experiment tracking
- **RustFS** for artifact storage (S3-compatible)
- **MLflow Server** for experiment tracking and model registry

## Prerequisites

- Docker Desktop for Mac installed and running
- At least 4GB of RAM allocated to Docker

## Quick Start

1. **Copy and configure the environment file:**
   ```bash
   cp .env.example .env
   # Edit .env to customize ports, credentials, or MLflow version
   ```

2. **Create the volumes directories:**
   ```bash
   mkdir -p ~/volumes/postgres ~/volumes/rustfs ~/volumes/postgres-backups
   # RustFS runs as UID 10001; on a native Linux host: sudo chown -R 10001:10001 ~/volumes/rustfs
   ```

3. **Start the services:**
   ```bash
   docker-compose up -d
   ```

4. **Wait for services to be ready** (usually takes 30-60 seconds):
   ```bash
   docker-compose logs -f mlflow
   ```
   Wait until you see "Listening at: http://0.0.0.0:5000"

5. **Access the services** (using default `.env` values):
   - MLflow UI: http://localhost:5010
   - RustFS Console: http://localhost:9001 (user: `rustfs`, password: `rustfs123`)
   - PostgreSQL: localhost:5432 (user: `mlflow`, password: `mlflow123`, db: `mlflow`)

## Configuration

All configurable values live in `.env`. Copy `.env.example` as a starting point.

### Ports

| Variable | Default | Description |
|---|---|---|
| `MLFLOW_PORT` | `5010` | Host port for the MLflow UI |
| `POSTGRES_PORT` | `5432` | Host port for PostgreSQL |
| `RUSTFS_API_PORT` | `9000` | Host port for the RustFS S3 API |
| `RUSTFS_CONSOLE_PORT` | `9001` | Host port for the RustFS web console |

### Credentials

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | `mlflow` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `mlflow123` | PostgreSQL password |
| `POSTGRES_DB` | `mlflow` | PostgreSQL database name |
| `RUSTFS_ROOT_USER` | `rustfs` | RustFS root username |
| `RUSTFS_ROOT_PASSWORD` | `rustfs123` | RustFS root password |
| `RUSTFS_BUCKET` | `mlflow` | RustFS bucket for artifacts |

### GenAI / LLM Endpoint

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | _(empty)_ | OpenAI API key for GenAI evaluation |
| `ANTHROPIC_API_KEY` | _(empty)_ | Anthropic API key for GenAI evaluation |
| `OPENAI_API_BASE` | `http://host.docker.internal:1234/v1` | OpenAI-compatible API endpoint — override to point at a local LLM (e.g. LM Studio, vLLM) |

### MLflow Version

Set `MLFLOW_VERSION` in `.env` to pin or upgrade MLflow:

```env
# Default — latest 3.x with GenAI extras
MLFLOW_VERSION=mlflow[genai]>=3.10.0

# Pin to an exact version
MLFLOW_VERSION=mlflow[genai]==3.10.0
```

### Port Conflicts

If any default ports clash with other services on your machine, change them in `.env`:

```env
MLFLOW_PORT=5020
RUSTFS_CONSOLE_PORT=9091
```

No changes to `docker-compose.yml` are needed.

## Using MLflow from Your Python Code

Install the MLflow client:
```bash
pip install mlflow boto3
```

Set environment variables (adjust port if you changed `MLFLOW_PORT`):
```bash
export MLFLOW_TRACKING_URI=http://localhost:5010
export MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
export AWS_ACCESS_KEY_ID=rustfs
export AWS_SECRET_ACCESS_KEY=rustfs123
```

Example Python code:
```python
import mlflow
import os

mlflow.set_tracking_uri("http://localhost:5010")

os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://localhost:9000'
os.environ['AWS_ACCESS_KEY_ID'] = 'rustfs'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'rustfs123'

mlflow.set_experiment("my-experiment")

with mlflow.start_run():
    mlflow.log_param("param1", 5)
    mlflow.log_metric("metric1", 0.85)

    with open("example.txt", "w") as f:
        f.write("Hello MLflow!")
    mlflow.log_artifact("example.txt")
```

## Useful Commands

**Stop all services:**
```bash
docker-compose down
```

**Stop and remove all data:**
```bash
docker-compose down
rm -rf ~/volumes/postgres ~/volumes/rustfs
```

**View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f mlflow
docker-compose logs -f postgres
docker-compose logs -f rustfs
```

**Restart a specific service:**
```bash
docker-compose restart mlflow
```

**Update MLflow to a new version:**

Edit `MLFLOW_VERSION` in `.env`, then force-recreate only the MLflow container (postgres and rustfs are left untouched):
```bash
docker-compose up -d --force-recreate mlflow
```
This triggers a fresh `pip install` on startup with the new version.

**Run a schema migration (before upgrading MLflow):**

The `mlflow-migrate` service is opt-in and will:
1. Create a timestamped pg_dump backup in `~/volumes/postgres-backups/`
2. Run `mlflow db upgrade` to apply any pending schema changes

```bash
docker-compose --profile migrate up mlflow-migrate
```

This service exits automatically when done. Check the output for the backup file path. The stack (postgres, rustfs, mlflow) does not need to be stopped beforehand.

**Check service status:**
```bash
docker-compose ps
```

## Data Persistence

All data is stored in the `~/volumes` directory on your Mac:
- `~/volumes/postgres`: PostgreSQL database files
- `~/volumes/rustfs`: RustFS object storage files
- `~/volumes/postgres-backups`: Pre-migration pg_dump backups (created by `mlflow-migrate`)

This data persists even when containers are stopped. To completely remove data:
```bash
docker-compose down
rm -rf ~/volumes/postgres ~/volumes/rustfs
mkdir -p ~/volumes/postgres ~/volumes/rustfs
```

## Accessing RustFS Console

1. Open http://localhost:9001 (or your `RUSTFS_CONSOLE_PORT`)
2. Login with your `RUSTFS_ROOT_USER` / `RUSTFS_ROOT_PASSWORD` from `.env`
3. Navigate to "Buckets" to see the `mlflow` bucket and stored artifacts

## Health Checks

All services include health checks:
```bash
docker-compose ps
```
All services should show "healthy" status after startup.

## Troubleshooting

**MLflow can't connect to PostgreSQL:**
- Wait a few seconds after starting services
- Check logs: `docker-compose logs postgres`
- Verify PostgreSQL is healthy: `docker-compose ps`

**Artifacts not uploading:**
- Verify RustFS is running: `docker-compose ps rustfs`
- Check RustFS console at http://localhost:9001
- Ensure bucket exists (created automatically by `rustfs-setup`)

## Backup and Restore

**Backup:**
```bash
docker-compose down
tar czf mlflow-backup-$(date +%Y%m%d).tar.gz -C ~ volumes/
docker-compose up -d
```

**Restore:**
```bash
docker-compose down
rm -rf ~/volumes/postgres ~/volumes/rustfs
tar xzf mlflow-backup-YYYYMMDD.tar.gz -C ~
docker-compose up -d
```

## Resource Requirements

Typical resource usage:
- CPU: 0.5-1 cores
- RAM: 1-2 GB
- Disk: Depends on your artifacts and experiments
