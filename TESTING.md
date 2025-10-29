# Testing Guide

## Local Testing (Recommended First Step)

Before connecting to AWS S3 and Redshift, test the pipeline locally with sample data.

### 1. Generate Sample Data

```bash
poetry run python generate_sample_data.py
```

This creates:

- `data/raw/sample_data/sales_data.parquet`
- `data/raw/sample_data/sales_data.csv`
- `data/raw/sample_data/sales_data.json`

### 2. Run Local Test Pipeline

```bash
poetry run python local_test.py
```

This will:

- ✅ Read local Parquet file
- ✅ Clean and transform data
- ✅ Add derived columns (year, month, day, hour)
- ✅ Filter invalid records
- ✅ Calculate data quality metrics
- ✅ Write partitioned output to `data/processed/`
- ✅ Show aggregated statistics

**Output:**

```
data/processed/sales_data_transformed/
├── year=2024/
│   ├── month=1/
│   │   └── part-*.parquet
│   ├── month=2/
│   │   └── part-*.parquet
│   └── ...
```

### 3. Verify Output

```bash
# List output files
ls -lh data/processed/sales_data_transformed/year=2024/month=*/

# Count records
poetry run python -c "
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName('test').getOrCreate()
df = spark.read.parquet('data/processed/sales_data_transformed')
print(f'Total records: {df.count()}')
spark.stop()
"
```

---

## AWS Integration Testing

Once local testing works, proceed with AWS S3 and Redshift.

### Prerequisites

1. **AWS Account Setup:**

   - S3 bucket created
   - Redshift cluster running
   - IAM credentials with appropriate permissions

2. **Configure Credentials:**

   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials
   ```

3. **Upload Sample Data to S3:**
   ```bash
   # Using AWS CLI
   aws s3 cp data/raw/sample_data/ s3://your-bucket/raw-data/sales_data/ --recursive
   ```

### Test S3 Connection

Create `test_s3.py`:

```python
from etl.extract.s3_extractor import S3Extractor
from etl.utils.config import get_config

config = get_config()
s3_config = config.get_s3_config()
aws_config = config.get_aws_config()

# Initialize extractor
extractor = S3Extractor(
    bucket_name=s3_config['bucket_name'],
    aws_access_key_id=aws_config.get('access_key_id'),
    aws_secret_access_key=aws_config.get('secret_access_key'),
    region=aws_config['region']
)

# List objects
objects = extractor.list_objects(prefix='raw-data/', suffix='.parquet')
print(f"Found {len(objects)} files")
for obj in objects:
    print(f"  - {obj['key']} ({obj['size']} bytes)")
```

Run:

```bash
poetry run python test_s3.py
```

### Test Spark S3 Integration

Create `test_spark_s3.py`:

```python
from etl.utils.spark_manager import get_spark_session
from etl.utils.config import get_config

config = get_config()
spark = get_spark_session(config.get_spark_config())

# Important: First run will download JAR files (takes 1-5 minutes)
print("Reading from S3 (first run may take time to download dependencies)...")

# Use s3a:// protocol
df = spark.read.parquet("s3a://your-bucket/raw-data/sales_data/sales_data.parquet")

print(f"Read {df.count()} rows")
df.show(5)

spark.stop()
```

Run:

```bash
poetry run python test_spark_s3.py
```

**Note:** The first run will download Hadoop AWS JARs from Maven Central. Wait for:

```
Ivy Default Cache set to: ...
:: loading settings :: url = jar:file:...
```

This is normal and only happens once.

### Test Redshift Connection

Create `test_redshift.py`:

```python
from etl.load.redshift_loader import RedshiftLoader
from etl.utils.config import get_config

config = get_config()
redshift_config = config.get_redshift_config()

loader = RedshiftLoader(
    host=redshift_config['host'],
    port=redshift_config['port'],
    database=redshift_config['database'],
    user=redshift_config['user'],
    password=redshift_config['password']
)

# Test connection
try:
    conn = loader.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT version()")
    version = cursor.fetchone()
    print(f"Connected to Redshift: {version[0]}")
    cursor.close()
    conn.close()
    print("✅ Redshift connection successful!")
except Exception as e:
    print(f"❌ Redshift connection failed: {e}")
```

Run:

```bash
poetry run python test_redshift.py
```

---

## Full Pipeline Testing

### Test with S3 and Redshift

Update `my_pipeline.py` to use actual S3 paths:

```python
from etl.pipeline import ETLPipeline

pipeline = ETLPipeline()

try:
    # Make sure data exists at s3://your-bucket/raw-data/sales_data/
    pipeline.run(
        source_prefix='sales_data',      # Will look in raw-data/sales_data/
        target_table='sales_fact',
        file_format='parquet',
        transformation_config={
            'clean_data': True,
            'drop_duplicates': True,
            'add_derived_columns': True,
            'timestamp_column': 'transaction_date',
            'partition_by': ['year', 'month']
        },
        load_mode='append'  # or 'overwrite'
    )
finally:
    pipeline.cleanup()
```

Run:

```bash
poetry run python my_pipeline.py
```

---

## Unit Testing

Run the test suite:

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=etl --cov-report=html

# Run specific test
poetry run pytest tests/test_s3_extractor.py -v

# Run with verbose output
poetry run pytest -v -s
```

---

## Performance Testing

### Test with Large Dataset

Generate larger sample data:

```python
# In generate_sample_data.py, modify:
df = generate_sample_sales_data(100000)  # 100K rows instead of 10K
```

Then run:

```bash
poetry run python generate_sample_data.py
poetry run python local_test.py
```

Monitor:

- Execution time
- Memory usage
- Output file sizes

### Optimize Spark Configuration

If processing is slow, adjust in `config/config.yml`:

```yaml
spark:
  executor_memory: '8g' # Increase for larger datasets
  driver_memory: '4g'
  executor_cores: 4
```

---

## Troubleshooting Tests

### Common Issues

1. **Spark JAR Download Timeout:**

   - Check internet connection
   - Wait longer (first download can take 5+ minutes)
   - Consider manual JAR download

2. **S3 Access Denied:**

   - Verify AWS credentials in `.env`
   - Check IAM permissions
   - Ensure bucket exists

3. **Redshift Connection Failed:**

   - Verify cluster is running
   - Check security group rules
   - Confirm credentials

4. **Out of Memory:**
   - Reduce dataset size
   - Increase Spark memory settings
   - Enable partitioning

See `TROUBLESHOOTING.md` for detailed solutions.

---

## Testing Checklist

- [ ] Generate sample data successfully
- [ ] Run local test pipeline
- [ ] Verify transformed output files
- [ ] Test S3 connection
- [ ] Test Spark S3 read/write
- [ ] Test Redshift connection
- [ ] Run full pipeline with S3 and Redshift
- [ ] Run unit tests
- [ ] Check logs for errors
- [ ] Verify data quality metrics

---

## Next Steps

Once all tests pass:

1. ✅ Review and optimize transformation logic
2. ✅ Set up monitoring and alerting
3. ✅ Schedule automated runs
4. ✅ Deploy to production environment
5. ✅ Document any custom transformations

See `DEPLOYMENT.md` for production deployment guide.
