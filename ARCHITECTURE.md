# Cloud ETL Pipeline Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          AWS Cloud Environment                      │
│                                                                     │
│  ┌────────────┐                                                    │
│  │  Data      │                                                    │
│  │  Sources   │                                                    │
│  └─────┬──────┘                                                    │
│        │ Upload                                                     │
│        ▼                                                            │
│  ┌──────────────────────────────────────┐                         │
│  │         AWS S3 Bucket                │                         │
│  │  ┌─────────────────────────────┐    │                         │
│  │  │  raw-data/                   │    │                         │
│  │  │  ├── sales_data/             │    │                         │
│  │  │  ├── customer_data/          │    │                         │
│  │  │  └── product_data/           │    │                         │
│  │  └─────────────────────────────┘    │                         │
│  └──────────────┬───────────────────────┘                         │
│                 │                                                   │
│                 │ EXTRACT                                          │
│                 ▼                                                   │
│  ┌──────────────────────────────────────┐                         │
│  │      ETL Pipeline (EC2/ECS)          │                         │
│  │  ┌────────────────────────────────┐  │                         │
│  │  │  S3Extractor                   │  │                         │
│  │  │  - List objects                │  │                         │
│  │  │  - Download files              │  │                         │
│  │  │  - Validate data               │  │                         │
│  │  └────────────┬───────────────────┘  │                         │
│  │               │                       │                         │
│  │               │ TRANSFORM             │                         │
│  │               ▼                       │                         │
│  │  ┌────────────────────────────────┐  │                         │
│  │  │  PySpark DataTransformer       │  │                         │
│  │  │  - Clean data                  │  │                         │
│  │  │  - Remove duplicates           │  │                         │
│  │  │  - Handle nulls                │  │                         │
│  │  │  - Add derived columns         │  │                         │
│  │  │  - Aggregate                   │  │                         │
│  │  │  - Filter                      │  │                         │
│  │  │  - Calculate metrics           │  │                         │
│  │  └────────────┬───────────────────┘  │                         │
│  │               │                       │                         │
│  │               ▼                       │                         │
│  │  ┌────────────────────────────────┐  │                         │
│  │  │  Write to S3                   │  │                         │
│  │  │  processed-data/               │  │                         │
│  │  └────────────┬───────────────────┘  │                         │
│  └───────────────┼───────────────────────┘                         │
│                  │                                                  │
│  ┌───────────────┼──────────────────────┐                         │
│  │               │ S3 (Processed Data)  │                         │
│  │  ┌────────────▼────────────────┐    │                         │
│  │  │  processed-data/             │    │                         │
│  │  │  └── sales_data_20241024/   │    │                         │
│  │  │      ├── part-00000.parquet │    │                         │
│  │  │      └── part-00001.parquet │    │                         │
│  │  └─────────────────────────────┘    │                         │
│  └──────────────┬───────────────────────┘                         │
│                 │                                                   │
│                 │ LOAD (COPY command)                             │
│                 ▼                                                   │
│  ┌──────────────────────────────────────┐                         │
│  │      AWS Redshift Cluster            │                         │
│  │  ┌────────────────────────────────┐  │                         │
│  │  │  Data Warehouse                │  │                         │
│  │  │  ├── analytics.sales_fact      │  │                         │
│  │  │  ├── analytics.customer_dim    │  │                         │
│  │  │  └── analytics.product_dim     │  │                         │
│  │  └────────────────────────────────┘  │                         │
│  └──────────────────────────────────────┘                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        ETL Pipeline                             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  pipeline.py (Orchestrator)                              │  │
│  │  - Initialize components                                 │  │
│  │  - Coordinate ETL phases                                 │  │
│  │  - Handle errors                                         │  │
│  │  - Cleanup resources                                     │  │
│  └────┬────────────────────┬──────────────────┬─────────────┘  │
│       │                    │                  │                 │
│       ▼                    ▼                  ▼                 │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────┐        │
│  │ Extract     │   │  Transform   │   │   Load      │        │
│  │             │   │              │   │             │        │
│  │ S3Extractor │   │ Transformer  │   │ Redshift    │        │
│  │             │   │ (PySpark)    │   │ Loader      │        │
│  │ - List      │   │ - Clean      │   │ - Create    │        │
│  │ - Download  │   │ - Transform  │   │   table     │        │
│  │ - Upload    │   │ - Aggregate  │   │ - COPY      │        │
│  │ - Validate  │   │ - Filter     │   │   from S3   │        │
│  └─────────────┘   └──────────────┘   └─────────────┘        │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Utilities                                               │  │
│  │  ┌─────────────┬──────────────┬──────────────────────┐  │  │
│  │  │ Config      │  Logger      │  SparkManager        │  │  │
│  │  │ - YAML      │  - Console   │  - Create session    │  │  │
│  │  │ - Env vars  │  - File      │  - Configure Spark   │  │  │
│  │  │ - Accessors │  - Levels    │  - Resource mgmt     │  │  │
│  │  └─────────────┴──────────────┴──────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
Input Data          Extract             Transform            Write              Load
────────────────────────────────────────────────────────────────────────────────

┌──────────┐
│ CSV/     │
│ Parquet/ │──┐
│ JSON     │  │
└──────────┘  │
              │
┌──────────┐  │    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ S3       │  │    │ Download │    │ PySpark  │    │ Write to │    │ Redshift │
│ raw-data/│──┼───▶│ or Read  │───▶│ Process  │───▶│ S3       │───▶│ COPY     │
│          │  │    │ Direct   │    │ DataFrame│    │ processed│    │ Command  │
└──────────┘  │    └──────────┘    └──────────┘    └──────────┘    └──────────┘
              │                          │
┌──────────┐  │                          │
│ Database │  │                          ▼
│ Export   │──┘                    ┌──────────┐
└──────────┘                       │ Quality  │
                                   │ Metrics  │
                                   └──────────┘

Data Transformations:
──────────────────────
1. Deduplication     │ Remove duplicate rows
2. Null Handling     │ Drop or fill null values
3. Type Casting      │ Ensure correct data types
4. Derived Columns   │ Add timestamp, date parts
5. Aggregation       │ Group by and aggregate
6. Filtering         │ Apply business rules
7. Partitioning      │ Partition by date/region
```

## Deployment Architecture

```
Development                 Staging                  Production
─────────────────────────────────────────────────────────────────

┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│ Local        │        │ EC2 Instance │        │ ECS Cluster  │
│ Machine      │        │              │        │              │
│              │        │ - Poetry     │        │ - Fargate    │
│ - Poetry     │        │ - Cron       │        │ - Auto-scale │
│ - PySpark    │        │ - Systemd    │        │ - Load bal.  │
└──────┬───────┘        └──────┬───────┘        └──────┬───────┘
       │                       │                       │
       │                       │                       │
       ▼                       ▼                       ▼
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│ S3           │        │ S3           │        │ S3           │
│ dev-bucket   │        │ stg-bucket   │        │ prod-bucket  │
└──────┬───────┘        └──────┬───────┘        └──────┬───────┘
       │                       │                       │
       ▼                       ▼                       ▼
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│ Redshift     │        │ Redshift     │        │ Redshift     │
│ dev-cluster  │        │ stg-cluster  │        │ prod-cluster │
│ (dc2.large)  │        │ (dc2.large)  │        │ (ra3.4xlarge)│
└──────────────┘        └──────────────┘        └──────────────┘
```

## Monitoring & Logging

```
┌─────────────────────────────────────────────────────────────────┐
│                      Monitoring Stack                           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Application Logs                                        │  │
│  │  logs/ETLPipeline_YYYYMMDD_HHMMSS.log                   │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│                           ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CloudWatch Logs                                         │  │
│  │  - Log streams by date                                   │  │
│  │  - Search and filter                                     │  │
│  │  - Export to S3                                          │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│                           ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CloudWatch Metrics                                      │  │
│  │  - RecordsProcessed                                      │  │
│  │  - PipelineDuration                                      │  │
│  │  - ErrorCount                                            │  │
│  │  - DataQualityScore                                      │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│                           ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CloudWatch Alarms                                       │  │
│  │  - Pipeline failures                                     │  │
│  │  - Long running jobs                                     │  │
│  │  - Data quality issues                                   │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│                           ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SNS Notifications                                       │  │
│  │  - Email alerts                                          │  │
│  │  - Slack integration                                     │  │
│  │  - PagerDuty                                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Security Layers                             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  IAM (Identity & Access Management)                      │  │
│  │  - Roles for EC2/ECS                                     │  │
│  │  - Policies for S3/Redshift access                       │  │
│  │  - MFA enforcement                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  VPC (Virtual Private Cloud)                             │  │
│  │  - Private subnets for compute                           │  │
│  │  - Security groups                                       │  │
│  │  - Network ACLs                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Encryption                                              │  │
│  │  - S3 encryption at rest (AES-256)                       │  │
│  │  - Redshift encryption                                   │  │
│  │  - SSL/TLS in transit                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Secrets Management                                      │  │
│  │  - AWS Secrets Manager                                   │  │
│  │  - Environment variables                                 │  │
│  │  - No hardcoded credentials                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Audit & Compliance                                      │  │
│  │  - CloudTrail logging                                    │  │
│  │  - S3 access logs                                        │  │
│  │  - Redshift audit logs                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```
