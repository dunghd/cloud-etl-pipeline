# Troubleshooting Guide

## Common Issues and Solutions

### NumPy/PyArrow Compatibility Error

**Error Message:**

```
AttributeError: _ARRAY_API not found
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.0.2
```

**Solution:**
This issue occurs when PyArrow is incompatible with NumPy 2.x. The project is already configured to use NumPy 1.x (`numpy = "^1.24.0,<2.0.0"`).

If you encounter this error:

```bash
# Update dependencies to use compatible versions
poetry update numpy pyarrow
```

**Status:** ✅ Fixed - NumPy 1.26.4 is compatible with PyArrow 14.0.0

---

### Import Errors After Installation

**Error Message:**

```
ModuleNotFoundError: No module named 'pyspark'
```

**Solution:**

```bash
# Ensure all dependencies are installed
poetry install

# Activate the virtual environment
poetry shell
```

---

### AWS Credentials Not Found

**Error Message:**

```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**Solution:**

1. Create `.env` file from template:

   ```bash
   cp .env.example .env
   ```

2. Add your AWS credentials to `.env`:

   ```env
   AWS_ACCESS_KEY_ID=your_access_key_id
   AWS_SECRET_ACCESS_KEY=your_secret_access_key
   ```

3. Or configure AWS CLI:
   ```bash
   aws configure
   ```

---

### S3 FileSystem Error

**Error Message:**

```
org.apache.hadoop.fs.UnsupportedFileSystemException: No FileSystem for scheme "s3"
```

**Cause:**
Spark cannot access S3 because the Hadoop AWS libraries are not properly loaded.

**Solutions:**

1. **Wait for JAR Download (First Run):**
   The first time you run Spark with S3 access, it needs to download the required JAR files from Maven Central. This can take 1-5 minutes. You'll see messages like:

   ```
   Ivy Default Cache set to: ...
   ```

   Just wait for the download to complete.

2. **Test Locally First:**
   Use the local testing script instead:

   ```bash
   poetry run python local_test.py
   ```

   This works with local files and doesn't require S3.

3. **Verify AWS Credentials:**
   Make sure your `.env` file has:

   ```env
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=us-east-1
   ```

4. **Check Internet Connection:**
   Spark needs internet access to download JARs from Maven Central on first run.

5. **Use s3a:// instead of s3://**
   If manually specifying S3 paths, use:

   ```python
   df = spark.read.parquet("s3a://bucket/path")
   ```

   Not:

   ```python
   df = spark.read.parquet("s3://bucket/path")  # May not work
   ```

6. **Manual JAR Download (Alternative):**
   If automatic download fails, manually download:

   - hadoop-aws-3.3.4.jar
   - aws-java-sdk-bundle-1.12.262.jar

   Place in: `$SPARK_HOME/jars/` or specify with `--jars` option.

---

### S3 Access Denied

**Error Message:**

```
botocore.exceptions.ClientError: An error occurred (AccessDenied)
```

**Solutions:**

1. **Check AWS Credentials:**

   - Verify credentials in `.env` file
   - Ensure credentials are valid

2. **Check IAM Permissions:**

   ```json
   {
     "Effect": "Allow",
     "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
     "Resource": ["arn:aws:s3:::your-bucket/*", "arn:aws:s3:::your-bucket"]
   }
   ```

3. **Check Bucket Name:**
   - Verify bucket name in `.env` or `config/config.yml`
   - Ensure bucket exists in your AWS account

---

### Redshift Connection Failed

**Error Message:**

```
psycopg2.OperationalError: could not connect to server
```

**Solutions:**

1. **Verify Cluster Status:**

   - Check if Redshift cluster is running
   - Verify endpoint and port

2. **Check Security Group:**

   - Ensure security group allows your IP
   - Default port: 5439

3. **Verify Credentials:**
   - Check username and password in `.env`
   - Test connection manually

---

### PySpark Out of Memory

**Error Message:**

```
java.lang.OutOfMemoryError: Java heap space
```

**Solutions:**

1. **Increase Spark Memory:**
   Edit `config/config.yml`:

   ```yaml
   spark:
     executor_memory: '8g' # Increase from 4g
     driver_memory: '4g' # Increase from 2g
   ```

2. **Enable Partitioning:**

   ```python
   transformation_config={
       'partition_by': ['year', 'month']
   }
   ```

3. **Process in Batches:**
   - Split large datasets into smaller chunks
   - Process incrementally

---

### Java Not Found

**Error Message:**

```
Exception: Java gateway process exited before sending its port number
```

**Solution:**
Install Java 8 or higher:

**macOS:**

```bash
brew install openjdk@11
```

**Ubuntu:**

```bash
sudo apt-get install openjdk-11-jdk
```

**Verify Installation:**

```bash
java -version
```

---

### Poetry Command Not Found

**Error Message:**

```
zsh: command not found: poetry
```

**Solution:**
Install Poetry:

```bash
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (add to ~/.zshrc or ~/.bash_profile)
export PATH="$HOME/.local/bin:$PATH"

# Reload shell
source ~/.zshrc
```

---

### Slow Performance

**Symptoms:**

- Pipeline takes too long to execute
- High memory usage

**Solutions:**

1. **Optimize Spark Configuration:**

   ```yaml
   spark:
     executor_cores: 4 # Increase cores
     executor_memory: '8g' # Increase memory
   ```

2. **Use Parquet Format:**

   - Better compression
   - Faster reads
   - Columnar storage

3. **Enable Partitioning:**

   ```python
   transformation_config={
       'partition_by': ['year', 'month', 'day']
   }
   ```

4. **Filter Early:**
   - Apply filters before transformations
   - Reduce data volume early in pipeline

---

### Data Quality Issues

**Symptoms:**

- Incorrect row counts
- Missing or null values
- Duplicate records

**Solutions:**

1. **Enable Data Cleaning:**

   ```python
   transformation_config={
       'clean_data': True,
       'drop_duplicates': True,
       'drop_null_columns': ['customer_id', 'product_id']
   }
   ```

2. **Check Data Quality Metrics:**

   ```python
   metrics = transformer.get_data_quality_metrics(df)
   print(metrics)
   ```

3. **Validate Source Data:**
   - Check S3 files are complete
   - Verify file formats
   - Inspect sample records

---

### Log Files Not Created

**Symptoms:**

- No log files in `logs/` directory

**Solutions:**

1. **Check Directory Exists:**

   ```bash
   mkdir -p logs
   ```

2. **Verify Logging Configuration:**
   In `config/config.yml`:

   ```yaml
   logging:
     level: 'INFO'
     log_to_file: true
     log_dir: 'logs'
   ```

3. **Check Permissions:**
   ```bash
   chmod 755 logs/
   ```

---

## Getting Help

### Check Logs

```bash
# View latest log file
ls -lt logs/ | head -5
tail -f logs/ETLPipeline_*.log
```

### Verify Setup

```bash
./verify_setup.sh
```

### Test Dependencies

```bash
poetry run python -c "import pyspark; import boto3; import pandas; print('All imports successful')"
```

### Run Tests

```bash
poetry run pytest -v
```

---

## Useful Commands

### Check Python Version

```bash
python --version  # Should be 3.9+
```

### Check Java Version

```bash
java -version  # Should be 8+
```

### List Installed Packages

```bash
poetry show
```

### Update Dependencies

```bash
poetry update
```

### Clear Cache

```bash
# Clear Poetry cache
poetry cache clear pypi --all

# Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
```

---

## Still Need Help?

1. Check the full documentation in `README.md`
2. Review example scripts in `examples.py`
3. Consult AWS documentation
4. Check project issues on GitHub

---

**Last Updated:** October 27, 2025
