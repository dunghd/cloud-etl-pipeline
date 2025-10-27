# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your AWS credentials
# Required fields:
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
# - S3_BUCKET_NAME
# - REDSHIFT_HOST, REDSHIFT_USER, REDSHIFT_PASSWORD
```

### 3. Generate Sample Data (Optional)

```bash
# Generate local test data
poetry run python generate_sample_data.py
```

### 4. Run Your First Pipeline

```python
# Create a file: my_pipeline.py
from etl.pipeline import ETLPipeline

pipeline = ETLPipeline()

try:
    pipeline.run(
        source_prefix='sales_data',      # S3 prefix in your bucket
        target_table='sales_fact',       # Redshift table name
        file_format='parquet',
        transformation_config={
            'clean_data': True,
            'drop_duplicates': True,
        },
        load_mode='append'
    )
finally:
    pipeline.cleanup()
```

```bash
# Run the pipeline
poetry run python my_pipeline.py
```

## 📋 Pre-requisites Checklist

- [ ] AWS Account with S3 and Redshift access
- [ ] Python 3.9+ installed
- [ ] Java 8+ installed (for PySpark)
- [ ] Poetry installed
- [ ] AWS credentials configured
- [ ] S3 bucket created
- [ ] Redshift cluster running

## 🔧 Common Commands

```bash
# Activate virtual environment
poetry shell

# Run tests
poetry run pytest

# Format code
poetry run black etl/

# View logs
tail -f logs/ETLPipeline_*.log
```

## 📁 Upload Data to S3

```bash
# Using AWS CLI
aws s3 cp data/raw/sample_data/ s3://your-bucket/raw-data/sales_data/ --recursive

# Or use the Python SDK in your code
from etl.extract.s3_extractor import S3Extractor

extractor = S3Extractor(bucket_name='your-bucket')
extractor.upload_file('local/file.parquet', 'raw-data/sales_data/file.parquet')
```

## 🎯 Next Steps

1. Review `config/config.yml` and customize for your needs
2. Check `examples.py` for advanced usage patterns
3. Read the full `README.md` for detailed documentation
4. Set up monitoring and alerting
5. Deploy to production environment

## ❓ Quick Troubleshooting

**Issue**: "Import pyspark could not be resolved"

- **Fix**: Run `poetry install` and ensure Java is installed

**Issue**: "S3 Access Denied"

- **Fix**: Check AWS credentials in `.env` and IAM permissions

**Issue**: "Redshift connection failed"

- **Fix**: Verify cluster is running and security group allows your IP

## 📚 Resources

- [Full Documentation](README.md)
- [Configuration Guide](config/config.yml)
- [Example Scripts](examples.py)
- AWS Documentation: [S3](https://docs.aws.amazon.com/s3/) | [Redshift](https://docs.aws.amazon.com/redshift/)
- [PySpark Documentation](https://spark.apache.org/docs/latest/api/python/)

Happy ETL-ing! 🎉
