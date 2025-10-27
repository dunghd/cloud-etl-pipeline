# Deployment Guide

## Production Deployment Checklist

### Infrastructure Setup

#### 1. AWS S3 Configuration

```bash
# Create S3 bucket
aws s3 mb s3://your-production-etl-bucket --region us-east-1

# Create bucket structure
aws s3api put-object --bucket your-production-etl-bucket --key raw-data/
aws s3api put-object --bucket your-production-etl-bucket --key processed-data/
aws s3api put-object --bucket your-production-etl-bucket --key temp/

# Enable versioning (recommended)
aws s3api put-bucket-versioning \
    --bucket your-production-etl-bucket \
    --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
    --bucket your-production-etl-bucket \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'
```

#### 2. AWS Redshift Setup

```sql
-- Create database
CREATE DATABASE etl_warehouse;

-- Create schema
CREATE SCHEMA analytics;

-- Create tables
CREATE TABLE analytics.sales_fact (
    transaction_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    sales_amount DECIMAL(10,2),
    quantity INT,
    discount DECIMAL(4,2),
    tax DECIMAL(4,2),
    transaction_date TIMESTAMP,
    store_id VARCHAR(20),
    processed_at TIMESTAMP,
    year INT,
    month INT,
    day INT,
    hour INT
)
DISTKEY(customer_id)
SORTKEY(transaction_date);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON analytics.sales_fact TO etl_user;
```

#### 3. IAM Configuration

Create an IAM policy for the ETL pipeline:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3Access",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-production-etl-bucket/*",
        "arn:aws:s3:::your-production-etl-bucket"
      ]
    },
    {
      "Sid": "RedshiftDataAccess",
      "Effect": "Allow",
      "Action": [
        "redshift:DescribeClusters",
        "redshift-data:ExecuteStatement",
        "redshift-data:GetStatementResult"
      ],
      "Resource": "*"
    }
  ]
}
```

### Deployment Options

#### Option 1: AWS EC2

1. **Launch EC2 Instance**

```bash
# Use Amazon Linux 2 or Ubuntu
# Instance type: t3.large or larger (for Spark)
# Storage: 100GB+ EBS volume
```

2. **Install Dependencies**

```bash
# Update system
sudo yum update -y  # Amazon Linux
# or
sudo apt-get update  # Ubuntu

# Install Python 3.9+
sudo yum install python39 -y

# Install Java
sudo yum install java-11-amazon-corretto -y

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Clone repository
git clone <your-repo-url>
cd cloud-etl-pipeline

# Install project dependencies
poetry install --no-dev
```

3. **Configure Environment**

```bash
# Create .env file
cp .env.example .env
nano .env  # Edit with production credentials

# Set file permissions
chmod 600 .env
```

4. **Setup Systemd Service**

```bash
# Create service file
sudo nano /etc/systemd/system/etl-pipeline.service
```

```ini
[Unit]
Description=Cloud ETL Pipeline
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/cloud-etl-pipeline
Environment="PATH=/home/ec2-user/.local/bin:/usr/bin"
ExecStart=/home/ec2-user/.local/bin/poetry run python etl/pipeline.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable etl-pipeline
sudo systemctl start etl-pipeline
sudo systemctl status etl-pipeline
```

#### Option 2: AWS ECS (Docker)

1. **Create Dockerfile**

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Java home
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY etl ./etl
COPY config ./config

# Install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Run pipeline
CMD ["python", "-m", "etl.pipeline"]
```

2. **Build and Push Image**

```bash
# Build image
docker build -t etl-pipeline:latest .

# Tag for ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag etl-pipeline:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/etl-pipeline:latest

# Push to ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/etl-pipeline:latest
```

3. **Create ECS Task Definition**

```json
{
  "family": "etl-pipeline",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "8192",
  "containerDefinitions": [
    {
      "name": "etl-pipeline",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/etl-pipeline:latest",
      "environment": [
        { "name": "AWS_REGION", "value": "us-east-1" },
        { "name": "ENVIRONMENT", "value": "production" }
      ],
      "secrets": [
        {
          "name": "AWS_ACCESS_KEY_ID",
          "valueFrom": "arn:aws:secretsmanager:..."
        },
        {
          "name": "AWS_SECRET_ACCESS_KEY",
          "valueFrom": "arn:aws:secretsmanager:..."
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/etl-pipeline",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Option 3: AWS Lambda (for small datasets)

1. **Create deployment package**

```bash
# Use AWS Lambda Layers for PySpark
# Note: Lambda has 512MB /tmp limit, suitable only for smaller datasets
```

2. **Lambda Function Code**

```python
import json
from etl.pipeline import ETLPipeline

def lambda_handler(event, context):
    pipeline = ETLPipeline()

    try:
        pipeline.run(
            source_prefix=event['source_prefix'],
            target_table=event['target_table'],
            file_format=event.get('file_format', 'parquet'),
            load_mode=event.get('load_mode', 'append')
        )

        return {
            'statusCode': 200,
            'body': json.dumps('ETL pipeline completed successfully')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'ETL pipeline failed: {str(e)}')
        }
    finally:
        pipeline.cleanup()
```

#### Option 4: AWS Glue (Recommended for AWS-native)

Convert the pipeline to use AWS Glue for serverless execution:

```python
# glue_job.py
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'source_prefix', 'target_table'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Use existing transformer logic
from etl.transform.transformer import DataTransformer

transformer = DataTransformer(spark)
# ... rest of pipeline logic

job.commit()
```

### Scheduling

#### Using Cron (EC2)

```bash
# Edit crontab
crontab -e

# Run daily at 2 AM
0 2 * * * cd /home/ec2-user/cloud-etl-pipeline && /home/ec2-user/.local/bin/poetry run python etl/pipeline.py >> /var/log/etl-pipeline.log 2>&1

# Run every 6 hours
0 */6 * * * cd /home/ec2-user/cloud-etl-pipeline && /home/ec2-user/.local/bin/poetry run python etl/pipeline.py
```

#### Using AWS EventBridge

```json
{
  "ScheduleExpression": "cron(0 2 * * ? *)",
  "Target": {
    "Arn": "arn:aws:ecs:us-east-1:123456789012:cluster/etl-cluster",
    "RoleArn": "arn:aws:iam::123456789012:role/ecsEventsRole",
    "EcsParameters": {
      "TaskDefinitionArn": "arn:aws:ecs:us-east-1:123456789012:task-definition/etl-pipeline:1",
      "TaskCount": 1,
      "LaunchType": "FARGATE"
    }
  }
}
```

### Monitoring and Alerting

#### CloudWatch Metrics

```python
# Add to pipeline.py
import boto3

cloudwatch = boto3.client('cloudwatch')

def send_metric(metric_name, value, unit='Count'):
    cloudwatch.put_metric_data(
        Namespace='ETL/Pipeline',
        MetricData=[{
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit
        }]
    )

# Example usage
send_metric('RecordsProcessed', record_count)
send_metric('PipelineDuration', duration_seconds, 'Seconds')
```

#### CloudWatch Alarms

```bash
# Create alarm for failed pipelines
aws cloudwatch put-metric-alarm \
    --alarm-name etl-pipeline-failures \
    --alarm-description "Alert on ETL pipeline failures" \
    --metric-name Errors \
    --namespace ETL/Pipeline \
    --statistic Sum \
    --period 300 \
    --threshold 1 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1 \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:etl-alerts
```

### Security Best Practices

1. **Use AWS Secrets Manager** for credentials
2. **Enable VPC endpoints** for S3 and Redshift
3. **Use IAM roles** instead of access keys where possible
4. **Enable CloudTrail** for audit logging
5. **Encrypt data** at rest and in transit
6. **Use private subnets** for compute resources
7. **Implement least privilege** access policies

### Backup and Disaster Recovery

```bash
# S3 Cross-region replication
aws s3api put-bucket-replication \
    --bucket your-production-etl-bucket \
    --replication-configuration file://replication.json

# Redshift automated snapshots (configure via console or CLI)
aws redshift modify-cluster \
    --cluster-identifier your-cluster \
    --automated-snapshot-retention-period 7
```

### Performance Optimization

1. **Increase Spark resources** for large datasets
2. **Use S3 partitioning** by date/region
3. **Enable Redshift distribution keys** and sort keys
4. **Use Parquet** for columnar storage
5. **Implement data partitioning** in transformations
6. **Cache intermediate results** when appropriate

### Cost Optimization

1. **Use S3 Intelligent-Tiering** for infrequent data
2. **Schedule Redshift pause/resume** for non-business hours
3. **Use Spot instances** for non-critical workloads
4. **Implement S3 lifecycle policies**
5. **Monitor and optimize Spark job execution**

### Testing in Production

```bash
# Run in dry-run mode first
ENVIRONMENT=production DRY_RUN=true poetry run python etl/pipeline.py

# Run with small dataset
poetry run python etl/pipeline.py --limit 1000

# Monitor logs
tail -f logs/ETLPipeline_*.log
```

### Rollback Strategy

1. Keep previous versions of processed data
2. Use S3 versioning
3. Maintain Redshift snapshots
4. Document rollback procedures
5. Test rollback process regularly

## Support

For production issues:

- Check CloudWatch logs
- Review application logs in `logs/`
- Verify AWS service health
- Contact support team

---

**Last Updated**: 2024
