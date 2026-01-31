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

# Or create via AWS Console:
# - Go to S3 in AWS Console
# - Click "Create bucket"
# - Name it (e.g., "my-mlflow-artifacts")
# - Choose your preferred region
# - Keep default settings or adjust as needed
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

Create a `.env` file in the same directory as `docker-compose-aws.yml`:

```bash
# Copy the example file
cp .env.example .env

# Edit with your values
nano .env
```

Your `.env` file should look like:
```env
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=us-east-1
MLFLOW_S3_BUCKET=my-mlflow-bucket-name
```

**⚠️ Security Note:** Never commit `.env` file to version control!

## Quick Start

1. **Create the PostgreSQL volume directory:**
   ```bash
   mkdir -p ~/volumes/postgres
   ```

2. **Configure your `.env` file** (see above)

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
   - MLflow UI: http://localhost:5000

## Using MLflow from Your Python Code

Install the MLflow client:
```bash
pip install mlflow boto3
```

Set environment variables:
```bash
export MLFLOW_TRACKING_URI=http://localhost:5000
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

Example Python code:
```python
import mlflow
import os

# Set MLflow tracking URI
mlflow.set_tracking_uri("http://localhost:5000")

# Set AWS credentials (same as in .env file)
os.environ['AWS_ACCESS_KEY_ID'] = 'your_access_key'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'your_secret_key'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Start an experiment
mlflow.set_experiment("my-experiment")

# Log parameters, metrics, and artifacts
with mlflow.start_run():
    mlflow.log_param("param1", 5)
    mlflow.log_metric("metric1", 0.85)
    
    # Log a file as an artifact (will be stored in S3)
    with open("example.txt", "w") as f:
        f.write("Hello MLflow with S3!")
    mlflow.log_artifact("example.txt")
```

## Useful Commands

**Stop all services:**
```bash
docker-compose -f docker-compose-aws.yml down
```

**View logs:**
```bash
# All services
docker-compose -f docker-compose-aws.yml logs -f

# Specific service
docker-compose -f docker-compose-aws.yml logs -f mlflow
docker-compose -f docker-compose-aws.yml logs -f postgres
```

**Restart MLflow server:**
```bash
docker-compose -f docker-compose-aws.yml restart mlflow
```

**Check service status:**
```bash
docker-compose -f docker-compose-aws.yml ps
```

## Configuration

### PostgreSQL
- Host: localhost:5432
- Database: mlflow
- User: mlflow
- Password: mlflow123

### AWS S3
- Configured via `.env` file
- Artifacts stored at: `s3://your-bucket-name/mlflow-artifacts/`

### Changing PostgreSQL Credentials

Edit the `docker-compose-aws.yml` file:
```yaml
environment:
  POSTGRES_USER: your_user
  POSTGRES_PASSWORD: your_password
  POSTGRES_DB: your_db
```

Also update the `DB_URI` in the MLflow service accordingly.

## Data Persistence

- **PostgreSQL data**: Stored in `~/volumes/postgres` on your Mac
- **MLflow artifacts**: Stored in your AWS S3 bucket

To backup PostgreSQL data:
```bash
docker-compose -f docker-compose-aws.yml down
tar czf postgres-backup.tar.gz -C ~ volumes/postgres
```

S3 artifacts are automatically backed up by AWS (consider enabling versioning).

## Cost Considerations

**AWS S3 Costs:**
- Storage: ~$0.023 per GB/month (Standard tier)
- PUT requests: ~$0.005 per 1,000 requests
- GET requests: ~$0.0004 per 1,000 requests
- Data transfer: Free for downloads within same region

**Estimated costs for typical usage:**
- Small team (10 experiments/day, 100MB artifacts): ~$1-5/month
- Medium usage (100 experiments/day, 1GB artifacts): ~$10-20/month

**Cost optimization tips:**
- Enable S3 lifecycle policies to archive old artifacts to Glacier
- Use S3 Intelligent-Tiering for automatic cost optimization
- Delete old experiment runs you no longer need

## Security Best Practices

1. **Use IAM roles instead of access keys** (when running on EC2)
2. **Enable S3 bucket versioning** for artifact history
3. **Enable S3 encryption at rest**
4. **Use separate buckets for different environments** (dev/staging/prod)
5. **Set up S3 bucket policies** to restrict access
6. **Never commit `.env` file** to version control
7. **Rotate AWS credentials regularly**
8. **Enable CloudTrail** for audit logging

## Troubleshooting

**MLflow can't connect to S3:**
- Verify AWS credentials in `.env` file
- Check IAM permissions for the user
- Verify S3 bucket exists and region is correct
- Check CloudWatch logs in AWS Console

**"Access Denied" errors:**
- Review IAM policy permissions
- Ensure bucket policy allows your IAM user
- Check if bucket is in the correct region

**Slow artifact uploads:**
- Consider using S3 Transfer Acceleration
- Check your internet connection
- Ensure you're using the correct regional endpoint

**PostgreSQL connection issues:**
- Wait a few seconds after starting services
- Check logs: `docker-compose -f docker-compose-aws.yml logs postgres`
- Verify PostgreSQL is healthy: `docker-compose -f docker-compose-aws.yml ps`

## Using AWS Profiles

If you have multiple AWS profiles configured, you can specify which one to use:

```yaml
# In docker-compose-aws.yml, add to mlflow service:
environment:
  AWS_PROFILE: your-profile-name
volumes:
  - ~/.aws:/root/.aws:ro  # Mount AWS credentials
```

## Advanced: S3 Lifecycle Policies

Archive old artifacts to reduce costs:

```json
{
  "Rules": [
    {
      "Id": "ArchiveOldMLflowArtifacts",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ],
      "NoncurrentVersionTransitions": [
        {
          "NoncurrentDays": 30,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
```

Apply via AWS CLI:
```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket your-mlflow-bucket-name \
  --lifecycle-configuration file://lifecycle.json
```

## Monitoring

**View artifacts in S3:**
```bash
# List artifacts
aws s3 ls s3://your-mlflow-bucket-name/mlflow-artifacts/ --recursive

# Check bucket size
aws s3 ls s3://your-mlflow-bucket-name --recursive --summarize
```

**Monitor costs:**
- Enable AWS Cost Explorer
- Set up billing alerts
- Use AWS Budgets to track spending

## Migration from MinIO

If you're migrating from the MinIO setup:

1. Export experiments from MinIO-based MLflow
2. Set up AWS S3 version
3. Use `aws s3 sync` to copy artifacts from MinIO to S3
4. Update your tracking server URI in client code

```bash
# Example: Copy MinIO data to S3
# (requires mc CLI configured for MinIO)
mc mirror myminio/mlflow s3://your-aws-bucket/mlflow-artifacts/
```
