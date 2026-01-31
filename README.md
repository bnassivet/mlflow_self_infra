# MLflow with PostgreSQL and MinIO - Docker Setup

This Docker Compose setup provides a complete MLflow tracking server with:
- **PostgreSQL** for metadata and experiment tracking
- **MinIO** for artifact storage (S3-compatible)
- **MLflow Server** for experiment tracking and model registry

## Prerequisites

- Docker Desktop for Mac installed and running
- At least 4GB of RAM allocated to Docker

## Quick Start

1. **Create the volumes directory:**
   ```bash
   mkdir -p ~/volumes/postgres ~/volumes/minio
   ```

2. **Start the services:**
   ```bash
   docker-compose up -d
   ```

3. **Wait for services to be ready** (usually takes 30-60 seconds):
   ```bash
   docker-compose logs -f mlflow
   ```
   Wait until you see "Listening at: http://0.0.0.0:5000"

4. **Access the services:**
   - MLflow UI: http://localhost:5000
   - MinIO Console: http://localhost:9001 (user: `minio`, password: `minio123`)
   - PostgreSQL: localhost:5432 (user: `mlflow`, password: `mlflow123`, db: `mlflow`)

## Using MLflow from Your Python Code

Install the MLflow client:
```bash
pip install mlflow boto3
```

Set environment variables:
```bash
export MLFLOW_TRACKING_URI=http://localhost:5000
export MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
export AWS_ACCESS_KEY_ID=minio
export AWS_SECRET_ACCESS_KEY=minio123
```

Example Python code:
```python
import mlflow
import os

# Set MLflow tracking URI
mlflow.set_tracking_uri("http://localhost:5000")

# Set MinIO credentials for artifact storage
os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://localhost:9000'
os.environ['AWS_ACCESS_KEY_ID'] = 'minio'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minio123'

# Start an experiment
mlflow.set_experiment("my-experiment")

# Log parameters, metrics, and artifacts
with mlflow.start_run():
    mlflow.log_param("param1", 5)
    mlflow.log_metric("metric1", 0.85)
    
    # Log a file as an artifact
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
rm -rf ~/volumes/postgres ~/volumes/minio
```

**View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f mlflow
docker-compose logs -f postgres
docker-compose logs -f minio
```

**Restart a specific service:**
```bash
docker-compose restart mlflow
```

**Check service status:**
```bash
docker-compose ps
```

## Configuration

### Default Credentials

**PostgreSQL:**
- Host: localhost:5432
- Database: mlflow
- User: mlflow
- Password: mlflow123

**MinIO:**
- API Endpoint: http://localhost:9000
- Console: http://localhost:9001
- Access Key: minio
- Secret Key: minio123
- Bucket: mlflow

### Changing Credentials

Edit the `docker-compose.yml` file and update the environment variables:
- PostgreSQL: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- MinIO: `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`
- MLflow: Update `DB_URI` and MinIO credentials accordingly

## Data Persistence

All data is stored in the `~/volumes` directory on your Mac:
- `~/volumes/postgres`: PostgreSQL database files
- `~/volumes/minio`: MinIO object storage files

This data persists even when containers are stopped. To completely remove data:
```bash
# Stop containers
docker-compose down

# Remove data (optional)
rm -rf ~/volumes/postgres ~/volumes/minio

# Recreate directories for fresh start
mkdir -p ~/volumes/postgres ~/volumes/minio
```

**Advantages of this approach:**
- Easy to back up (just copy the ~/volumes folder)
- Easy to inspect data directly on your Mac
- Data survives Docker Desktop restarts
- Can easily move or archive entire setups

## Troubleshooting

**MLflow can't connect to PostgreSQL:**
- Wait a few seconds after starting services
- Check logs: `docker-compose logs postgres`
- Verify PostgreSQL is healthy: `docker-compose ps`

**Artifacts not uploading:**
- Verify MinIO is running: `docker-compose ps minio`
- Check MinIO console at http://localhost:9001
- Ensure bucket exists (should be created automatically)

**Port conflicts:**
If ports 5000, 5432, 9000, or 9001 are already in use, edit the `docker-compose.yml` file and change the port mappings:
```yaml
ports:
  - "5001:5000"  # Change 5001 to any available port
```

## Accessing MinIO Console

1. Open http://localhost:9001
2. Login with:
   - Username: `minio`
   - Password: `minio123`
3. Navigate to "Buckets" to see the `mlflow` bucket and stored artifacts

## Health Checks

All services include health checks. You can verify they're running properly:
```bash
docker-compose ps
```

All services should show "healthy" status after startup.

## Resource Requirements

Typical resource usage:
- CPU: 0.5-1 cores
- RAM: 1-2 GB
- Disk: Depends on your artifacts and experiments

## Backup and Restore

Since data is stored in `~/volumes`, backup is simple:

**Backup:**
```bash
# Stop services first
docker-compose down

# Create backup
tar czf mlflow-backup-$(date +%Y%m%d).tar.gz -C ~ volumes/

# Restart services
docker-compose up -d
```

**Restore:**
```bash
# Stop services
docker-compose down

# Remove current data
rm -rf ~/volumes/postgres ~/volumes/minio

# Extract backup
tar xzf mlflow-backup-YYYYMMDD.tar.gz -C ~

# Restart services
docker-compose up -d
```

**Alternative: Copy to external drive**
```bash
cp -r ~/volumes /path/to/external/drive/mlflow-backup
```
