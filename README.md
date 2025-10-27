# Cloud ETL Pipeline

A production-ready ETL (Extract, Transform, Load) pipeline that processes large datasets from AWS S3 using PySpark and loads the transformed data into a cloud data warehouse (AWS Redshift).

## Features

- **Extract**: Pull large datasets from AWS S3 with support for multiple file formats (Parquet, CSV, JSON)
- **Transform**: Process and transform data using PySpark with:
  - Data cleaning and deduplication
  - Null value handling
  - Derived column generation
  - Aggregations and filtering
  - Data quality metrics
- **Load**: Load transformed data into AWS Redshift data warehouse
- **Configuration Management**: YAML-based configuration with environment variable support
- **Logging**: Comprehensive logging to both console and file
- **Poetry**: Modern Python dependency management

## Architecture

```
┌─────────────┐
│   AWS S3    │ (Raw Data)
│   Bucket    │
└──────┬──────┘
       │
       │ Extract
       ▼
┌─────────────┐
│   PySpark   │ (Transform)
│  Processing │
└──────┬──────┘
       │
       │ Load
       ▼
┌─────────────┐
│  Redshift   │ (Data Warehouse)
│   Cluster   │
└─────────────┘
```

## Project Structure

```
cloud-etl-pipeline/
├── etl/
│   ├── __init__.py
│   ├── extract/
│   │   ├── __init__.py
│   │   └── s3_extractor.py       # S3 data extraction
│   ├── transform/
│   │   ├── __init__.py
│   │   └── transformer.py        # PySpark transformations
│   ├── load/
│   │   ├── __init__.py
│   │   └── redshift_loader.py    # Redshift data loading
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration management
│   │   ├── logger.py             # Logging utilities
│   │   ├── spark_manager.py      # Spark session management
│   │   └── exceptions.py         # Custom exceptions
│   └── pipeline.py               # Main ETL orchestrator
├── config/
│   └── config.yml                # Pipeline configuration
├── tests/                        # Unit tests
├── logs/                         # Application logs
├── data/                         # Local data directory
├── examples.py                   # Usage examples
├── pyproject.toml                # Poetry dependencies
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

## Prerequisites

- Python 3.9+
- Poetry
- AWS Account with:
  - S3 bucket
  - Redshift cluster (or similar data warehouse)
  - IAM credentials with appropriate permissions
- Java 8+ (required for PySpark)

## Installation

1. **Clone the repository**:

   ```bash
   cd /Users/dung.ho/Documents/Training/Python/cloud-etl-pipeline
   ```

2. **Install Poetry** (if not already installed):

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies**:

   ```bash
   poetry install
   ```

4. **Activate the virtual environment**:
   ```bash
   poetry shell
   ```

## Configuration

1. **Copy the environment template**:

   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** with your AWS credentials and configuration:

   ```env
   AWS_ACCESS_KEY_ID=your_access_key_id
   AWS_SECRET_ACCESS_KEY=your_secret_access_key
   AWS_REGION=us-east-1

   S3_BUCKET_NAME=your-etl-bucket
   S3_RAW_DATA_PREFIX=raw-data/
   S3_PROCESSED_DATA_PREFIX=processed-data/

   REDSHIFT_HOST=your-cluster.region.redshift.amazonaws.com
   REDSHIFT_PORT=5439
   REDSHIFT_DATABASE=your_database
   REDSHIFT_USER=your_user
   REDSHIFT_PASSWORD=your_password
   ```

3. **Review and customize** `config/config.yml`:
   - Adjust Spark configurations (memory, cores)
   - Configure S3 paths and file formats
   - Set processing parameters
   - Configure logging preferences

## Usage

### Basic Usage

```python
from etl.pipeline import ETLPipeline

# Initialize pipeline
pipeline = ETLPipeline()

try:
    # Run complete ETL pipeline
    pipeline.run(
        source_prefix='sales_data',
        target_table='sales_fact',
        file_format='parquet',
        transformation_config={
            'clean_data': True,
            'drop_duplicates': True,
            'add_derived_columns': True,
            'timestamp_column': 'transaction_date'
        },
        load_mode='append'
    )
finally:
    pipeline.cleanup()
```

### Advanced Usage

For more control, run each phase separately:

```python
from etl.pipeline import ETLPipeline

pipeline = ETLPipeline()

try:
    # Extract
    extracted_path = pipeline.extract(
        s3_prefix='raw-data/customer_data',
        file_format='csv'
    )

    # Transform
    transformed_path = pipeline.transform(
        input_s3_path=extracted_path,
        output_s3_prefix='processed-data/customer_data_transformed',
        file_format='parquet',
        transformation_config={
            'clean_data': True,
            'drop_duplicates': True,
            'filter_conditions': 'active = true',
            'partition_by': ['country', 'year']
        }
    )

    # Load
    pipeline.load(
        s3_path=transformed_path,
        table_name='customer_dimension',
        file_format='parquet',
        mode='overwrite'
    )
finally:
    pipeline.cleanup()
```

### Transformation Options

The `transformation_config` dictionary supports:

- **clean_data** (bool): Enable data cleaning
- **drop_duplicates** (bool): Remove duplicate rows
- **drop_null_columns** (list): Columns where null rows should be dropped
- **fill_null_values** (dict): Fill null values `{'column': value}`
- **add_derived_columns** (bool): Add timestamp and date part columns
- **timestamp_column** (str): Column to extract date parts from
- **filter_conditions** (str): SQL-like filter conditions
- **aggregate** (dict): Aggregation configuration
  ```python
  {
      'group_by': ['column1', 'column2'],
      'expressions': {
          'sales': 'sum',
          'quantity': 'avg',
          'orders': 'count'
      }
  }
  ```
- **partition_by** (list): Columns to partition output data

### Running Examples

```bash
poetry run python examples.py
```

## AWS Setup

### S3 Bucket Structure

```
your-etl-bucket/
├── raw-data/              # Source data
│   ├── sales_data/
│   ├── customer_data/
│   └── product_data/
├── processed-data/        # Transformed data
└── temp/                  # Temporary staging
```

### IAM Permissions

Your IAM user/role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::your-etl-bucket/*",
        "arn:aws:s3:::your-etl-bucket"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["redshift:DescribeClusters", "redshift-data:ExecuteStatement"],
      "Resource": "*"
    }
  ]
}
```

### Redshift Setup

1. Create a table in Redshift:

   ```sql
   CREATE TABLE IF NOT EXISTS sales_fact (
       transaction_id VARCHAR(50),
       customer_id VARCHAR(50),
       product_id VARCHAR(50),
       sales_amount DECIMAL(10,2),
       transaction_date TIMESTAMP,
       processed_at TIMESTAMP,
       year INT,
       month INT,
       day INT
   );
   ```

2. (Optional) Create IAM role for Redshift COPY command

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

```bash
poetry run black etl/
```

### Linting

```bash
poetry run flake8 etl/
```

### Type Checking

```bash
poetry run mypy etl/
```

## Monitoring and Logging

Logs are written to:

- Console (stdout)
- File: `logs/ETLPipeline_YYYYMMDD_HHMMSS.log`

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

Configure in `config/config.yml` or via `LOG_LEVEL` environment variable.

## Performance Tuning

### Spark Configuration

Adjust in `config/config.yml`:

```yaml
spark:
  executor_memory: '8g' # Increase for larger datasets
  driver_memory: '4g'
  executor_cores: 4
  max_result_size: '4g'
```

### Partitioning

Use partitioning for large datasets:

```python
transformation_config={
    'partition_by': ['year', 'month', 'day']
}
```

### File Formats

- **Parquet**: Best for columnar data, good compression
- **CSV**: Universal compatibility, larger size
- **JSON**: Nested data structures, slower processing

## Troubleshooting

### Common Issues

1. **"Import pyspark could not be resolved"**

   - Install dependencies: `poetry install`
   - Ensure Java is installed: `java -version`

2. **S3 Access Denied**

   - Check AWS credentials in `.env`
   - Verify IAM permissions
   - Ensure bucket name is correct

3. **Redshift Connection Failed**

   - Check Redshift cluster is running
   - Verify security group allows your IP
   - Confirm credentials in `.env`

4. **Out of Memory Error**
   - Increase Spark executor/driver memory
   - Enable partitioning
   - Process data in smaller batches

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions, please open an issue on the repository.
