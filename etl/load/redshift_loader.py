"""Redshift data warehouse loader module"""

from pyspark.sql import DataFrame
from typing import Optional, Dict, Any
import psycopg2
from psycopg2 import sql

from etl.utils.logger import LoggerMixin


class RedshiftLoader(LoggerMixin):
    """Load data into AWS Redshift data warehouse"""
    
    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        schema: str = 'public',
        temp_dir: Optional[str] = None,
        iam_role: Optional[str] = None
    ):
        """
        Initialize Redshift loader
        
        Args:
            host: Redshift cluster host
            port: Redshift port
            database: Database name
            user: Username
            password: Password
            schema: Schema name (default: public)
            temp_dir: S3 temporary directory for staging
            iam_role: IAM role ARN for S3 access (optional)
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.schema = schema
        self.temp_dir = temp_dir
        self.iam_role = iam_role
        
        self.logger.info(f"Initialized RedshiftLoader for {host}:{port}/{database}")
    
    def get_connection(self):
        """
        Create a connection to Redshift
        
        Returns:
            psycopg2 connection object
        """
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            return conn
        except Exception as e:
            self.logger.error(f"Error connecting to Redshift: {e}")
            raise
    
    def create_table(
        self,
        table_name: str,
        columns: Dict[str, str],
        drop_if_exists: bool = False
    ) -> None:
        """
        Create a table in Redshift
        
        Args:
            table_name: Name of the table
            columns: Dictionary mapping column names to data types
            drop_if_exists: Whether to drop the table if it exists
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            full_table_name = f"{self.schema}.{table_name}"
            
            if drop_if_exists:
                drop_query = f"DROP TABLE IF EXISTS {full_table_name}"
                self.logger.info(f"Dropping table if exists: {full_table_name}")
                cursor.execute(drop_query)
            
            # Build CREATE TABLE query
            column_defs = [f"{col} {dtype}" for col, dtype in columns.items()]
            create_query = f"""
                CREATE TABLE IF NOT EXISTS {full_table_name} (
                    {', '.join(column_defs)}
                )
            """
            
            self.logger.info(f"Creating table: {full_table_name}")
            cursor.execute(create_query)
            conn.commit()
            
            cursor.close()
            conn.close()
            
            self.logger.info(f"Table created successfully: {full_table_name}")
            
        except Exception as e:
            self.logger.error(f"Error creating table {table_name}: {e}")
            raise
    
    def load_from_s3(
        self,
        table_name: str,
        s3_path: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        file_format: str = 'parquet',
        mode: str = 'append'
    ) -> None:
        """
        Load data from S3 into Redshift using COPY command
        
        Args:
            table_name: Target table name
            s3_path: S3 path to data
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            file_format: File format (parquet, csv, json)
            mode: Load mode ('append' or 'overwrite')
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            full_table_name = f"{self.schema}.{table_name}"
            
            # Truncate table if overwrite mode
            if mode == 'overwrite':
                self.logger.info(f"Truncating table: {full_table_name}")
                cursor.execute(f"TRUNCATE TABLE {full_table_name}")
            
            # Build COPY command based on file format
            if file_format == 'parquet':
                # Use IAM role if provided, otherwise fall back to access keys
                if self.iam_role:
                    copy_query = f"""
                        COPY {full_table_name}
                        FROM '{s3_path}'
                        IAM_ROLE '{self.iam_role}'
                        FORMAT AS PARQUET;
                    """
                else:
                    raise ValueError("IAM role is required for Redshift COPY from S3. Set REDSHIFT_IAM_ROLE in .env file")
            elif file_format == 'csv':
                copy_query = f"""
                    COPY {full_table_name}
                    FROM '{s3_path}'
                    ACCESS_KEY_ID '{aws_access_key_id}'
                    SECRET_ACCESS_KEY '{aws_secret_access_key}'
                    CSV
                    IGNOREHEADER 1
                    DELIMITER ','
                    REGION 'us-east-1';
                """
            elif file_format == 'json':
                copy_query = f"""
                    COPY {full_table_name}
                    FROM '{s3_path}'
                    ACCESS_KEY_ID '{aws_access_key_id}'
                    SECRET_ACCESS_KEY '{aws_secret_access_key}'
                    JSON 'auto'
                    REGION 'us-east-1';
                """
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            self.logger.info(f"Loading data from {s3_path} to {full_table_name}")
            cursor.execute(copy_query)
            conn.commit()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {full_table_name}")
            row_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            self.logger.info(f"Successfully loaded data. Total rows: {row_count}")
            
        except Exception as e:
            self.logger.error(f"Error loading data from S3: {e}")
            raise
    
    def load_from_dataframe(
        self,
        df: DataFrame,
        table_name: str,
        mode: str = 'append',
        temp_s3_path: Optional[str] = None
    ) -> None:
        """
        Load data from Spark DataFrame into Redshift
        
        Args:
            df: Spark DataFrame
            table_name: Target table name
            mode: Write mode ('append' or 'overwrite')
            temp_s3_path: Temporary S3 path for staging
        """
        try:
            if temp_s3_path is None and self.temp_dir is None:
                raise ValueError("temp_s3_path or temp_dir must be provided")
            
            staging_path = temp_s3_path or f"{self.temp_dir}/{table_name}_staging"
            
            self.logger.info(f"Writing DataFrame to staging location: {staging_path}")
            
            # Write DataFrame to S3 as Parquet
            df.write \
                .mode('overwrite') \
                .parquet(staging_path)
            
            # Build Redshift connection URL
            jdbc_url = f"jdbc:redshift://{self.host}:{self.port}/{self.database}"
            
            # Write to Redshift using JDBC
            df.write \
                .format("io.github.spark_redshift_community.spark.redshift") \
                .option("url", jdbc_url) \
                .option("dbtable", f"{self.schema}.{table_name}") \
                .option("user", self.user) \
                .option("password", self.password) \
                .option("tempdir", staging_path) \
                .mode(mode) \
                .save()
            
            self.logger.info(f"Successfully loaded DataFrame to {table_name}")
            
        except Exception as e:
            self.logger.error(f"Error loading DataFrame: {e}")
            raise
    
    def execute_query(self, query: str) -> None:
        """
        Execute a SQL query on Redshift
        
        Args:
            query: SQL query to execute
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            self.logger.info(f"Executing query: {query[:100]}...")
            cursor.execute(query)
            conn.commit()
            
            cursor.close()
            conn.close()
            
            self.logger.info("Query executed successfully")
            
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in Redshift
        
        Args:
            table_name: Name of the table
            
        Returns:
            True if table exists, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = f"""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = '{self.schema}'
                    AND table_name = '{table_name}'
                )
            """
            
            cursor.execute(query)
            exists = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return exists
            
        except Exception as e:
            self.logger.error(f"Error checking table existence: {e}")
            raise
