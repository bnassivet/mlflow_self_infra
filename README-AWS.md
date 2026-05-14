# MLflow with PostgreSQL and AWS S3 - Docker Setup

This Docker Compose setup provides MLflow tracking server with:
- **PostgreSQL** for metadata and experiment tracking
- **AWS S3** for artifact storage
- **MLflow Server** for experiment tracking and model registry

## Prerequisites

- Docker Desktop for Mac installed and running
- AWS account with S3 access
- AWS credentials (Access Key ID and Secret Access Key)
- An existing S3 bucket for MLflow artifacts

## AWS Setup

### 1. Create an S3 Bucket

```bash
# Using AWS CLI
aws s3 mb s3://your-mlflow-bucket-name --region us-east-1
```

### 2. Create IAM User (Recommended)

Create a dedicated IAM user for MLflow with S3 access:

1. Go to IAM in AWS Console
2. Create new user (e.g., "mlflow-user")
3. Attach policy with S3 permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-mlflow-bucket-name",
        "arn:aws:s3:::your-mlflow-bucket-name/*"
      ]
    }
  ]
}
```

4. Save the Access Key ID and Secret Access Key

### 3. Configure Environment Variables

```bash
cp .env.example .env
nano .env
```

Your `.env` file should include at minimum:
```env
# AWS credentials
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=us-east-1
MLFLOW_S3_BUCKET=my-mlflow-bucket-name

# Ports (optional — change to avoid conflicts)
MLFLOW_PORT=5010
POSTGRES_PORT=5432

# PostgreSQL credentials (optional — defaults shown)
POSTGRES_USER=mlflow
POSTGRES_PASSWORD=mlflow123
POSTGRES_DB=mlflow

# MLflow version (optional)
MLFLOW_VERSION=mlflow[genai]>=3.10.0

# GenAI / LLM endpoint (optional — override to point at a local LLM)
# OPENAI_API_BASE=http://host.docker.internal:1234/v1
```

**⚠️ Security Note:** Never commit `.env` to version control!

## Quick Start

1. **Configure your `.env` file** (see above)

2. **Create the volume directories:**
   ```bash
   mkdir -p ~/volumes/postgres ~/volumes/postgres-backups
   ```

3. **Start the services:**
   ```bash
   docker-compose -f docker-compose-aws.yml up -d
   ```

4. **Wait for services to be ready** (usually takes 30-60 seconds):
   ```bash
   docker-compose -f docker-compose-aws.yml logs -f mlflow
   ```
   Wait until you see "Listening at: http://0.0.0.0:5000"

5. **Access MLflow UI:**
   - MLflow UI: http://localhost:5010 (or your `MLFLOW_PORT`)

## Configuration

All configurable values live in `.env`. See `.env.example` for the full list.

### Ports

| Variable | Default | Description |
|---|---|---|
| `MLFLOW_PORT` | `5010` | Host port for the MLflow UI |
| `POSTGRES_PORT` | `5432` | Host port for PostgreSQL |

### MLflow Version

```env
MLFLOW_VERSION=mlflow[genai]>=3.10.0   # default
MLFLOW_VERSION=mlflow[genai]==3.10.0   # pin exact version
```

### GenAI / LLM Endpoint

`OPENAI_API_BASE` controls which OpenAI-compatible endpoint MLflow uses for GenAI evaluation. It defaults to `http://host.docker.internal:1234/v1` (LM Studio). Override in `.env` to point at any OpenAI-compatible server (vLLM, Ollama, etc.) or leave unset to use the public OpenAI API.

### Changing PostgreSQL Credentials

Update `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` in `.env`. The compose file reads these automatically — no manual edits to `docker-compose-aws.yml` needed.

## Using MLflow from Your Python Code

```bash
pip install mlflow boto3
```

```bash
export MLFLOW_TRACKING_URI=http://localhost:5010   # match your MLFLOW_PORT
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

```python
import mlflow

mlflow.set_tracking_uri("http://localhost:5010")
mlflow.set_experiment("my-experiment")

with mlflow.start_run():
    mlflow.log_param("param1", 5)
    mlflow.log_metric("metric1", 0.85)

    with open("example.txt", "w") as f:
        f.write("Hello MLflow with S3!")
    mlflow.log_artifact("example.txt")
```

## Useful Commands

```bash
# Stop services
docker-compose -f docker-compose-aws.yml down

# View logs
docker-compose -f docker-compose-aws.yml logs -f
docker-compose -f docker-compose-aws.yml logs -f mlflow

# Restart MLflow
docker-compose -f docker-compose-aws.yml restart mlflow

# Check status
docker-compose -f docker-compose-aws.yml ps
```

**Update MLflow to a new version:**

Edit `MLFLOW_VERSION` in `.env`, then force-recreate only the MLflow container (postgres is left untouched):
```bash
docker-compose -f docker-compose-aws.yml up -d --force-recreate mlflow
```
This triggers a fresh `pip install` on startup with the new version.

**Run a schema migration (before upgrading MLflow):**

The `mlflow-migrate` service is opt-in and will:
1. Create a timestamped pg_dump backup in `~/volumes/postgres-backups/`
2. Run `mlflow db upgrade` to apply any pending schema changes

```bash
docker-compose -f docker-compose-aws.yml --profile migrate up mlflow-migrate
```

This service exits automatically when done. Check the output for the backup file path.

## Data Persistence

- **PostgreSQL data**: `~/volumes/postgres` on your Mac
- **MLflow artifacts**: Your AWS S3 bucket
- **Pre-migration backups**: `~/volumes/postgres-backups` (pg_dump files created by `mlflow-migrate`)

Backup PostgreSQL data manually:
```bash
docker-compose -f docker-compose-aws.yml down
tar czf postgres-backup.tar.gz -C ~ volumes/postgres
```

S3 artifacts are managed by AWS (consider enabling bucket versioning).

## Cost Considerations

**AWS S3 Costs (approximate):**
- Storage: ~$0.023 per GB/month (Standard tier)
- PUT requests: ~$0.005 per 1,000 requests
- GET requests: ~$0.0004 per 1,000 requests

**Cost optimization tips:**
- Enable S3 lifecycle policies to archive old artifacts to Glacier
- Use S3 Intelligent-Tiering for automatic cost optimization
- Delete old experiment runs you no longer need

## Security Best Practices

1. **Use IAM roles instead of access keys** (when running on EC2)
2. **Enable S3 bucket versioning** for artifact history
3. **Enable S3 encryption at rest**
4. **Use separate buckets for different environments** (dev/staging/prod)
5. **Never commit `.env` file** to version control
6. **Rotate AWS credentials regularly**

## Troubleshooting

**MLflow can't connect to S3:**
- Verify AWS credentials in `.env`
- Check IAM permissions for the user
- Verify S3 bucket exists and region matches `AWS_DEFAULT_REGION`

**"Access Denied" errors:**
- Review IAM policy permissions
- Ensure bucket policy allows your IAM user

**PostgreSQL connection issues:**
- Wait a few seconds after starting services
- Check logs: `docker-compose -f docker-compose-aws.yml logs postgres`

## Using AWS Profiles

```yaml
# In docker-compose-aws.yml, add to mlflow service:
environment:
  AWS_PROFILE: your-profile-name
volumes:
  - ~/.aws:/root/.aws:ro
```

## Migration from MinIO

```bash
# Copy MinIO artifacts to S3 (requires mc CLI configured for MinIO)
mc mirror myminio/mlflow s3://your-aws-bucket/mlflow-artifacts/
```
