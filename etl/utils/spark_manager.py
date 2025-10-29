"""Spark session management utilities"""

from pyspark.sql import SparkSession
from typing import Optional, Dict, Any
import os

from etl.utils.logger import LoggerMixin


class SparkManager(LoggerMixin):
    """Manage Spark session lifecycle"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Spark manager
        
        Args:
            config: Spark configuration dictionary
        """
        self.config = config or {}
        self._spark_session: Optional[SparkSession] = None
    
    def create_session(self) -> SparkSession:
        """
        Create and configure Spark session
        
        Returns:
            Configured SparkSession
        """
        if self._spark_session is not None:
            return self._spark_session
        
        app_name = self.config.get('app_name', 'CloudETLPipeline')
        master = self.config.get('master', 'local[*]')
        
        self.logger.info(f"Creating Spark session: {app_name} on {master}")
        
        builder = SparkSession.builder \
            .appName(app_name) \
            .master(master)
        
        # Set Spark configurations
        executor_memory = self.config.get('executor_memory', '4g')
        driver_memory = self.config.get('driver_memory', '2g')
        executor_cores = self.config.get('executor_cores', 2)
        max_result_size = self.config.get('max_result_size', '2g')
        
        builder = builder \
            .config('spark.executor.memory', executor_memory) \
            .config('spark.driver.memory', driver_memory) \
            .config('spark.executor.cores', executor_cores) \
            .config('spark.driver.maxResultSize', max_result_size)
        
        # Add Hadoop AWS dependencies for S3 access
        # Using compatible versions for Hadoop 3.3.x
        builder = builder \
            .config('spark.jars.packages', 
                   'org.apache.hadoop:hadoop-aws:3.3.4,'
                   'com.amazonaws:aws-java-sdk-bundle:1.12.262,'
                   'org.apache.hadoop:hadoop-common:3.3.4') \
            .config('spark.hadoop.fs.s3a.impl', 'org.apache.hadoop.fs.s3a.S3AFileSystem') \
            .config('spark.hadoop.fs.s3.impl', 'org.apache.hadoop.fs.s3a.S3AFileSystem')
        
        # Configure AWS credentials if provided
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        if aws_access_key and aws_secret_key:
            builder = builder \
                .config('spark.hadoop.fs.s3a.access.key', aws_access_key) \
                .config('spark.hadoop.fs.s3a.secret.key', aws_secret_key) \
                .config('spark.hadoop.fs.s3a.endpoint', f's3.{aws_region}.amazonaws.com') \
                .config('spark.hadoop.fs.s3a.aws.credentials.provider', 
                       'org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider')
        
        self._spark_session = builder.getOrCreate()
        
        # Set log level
        self._spark_session.sparkContext.setLogLevel('WARN')
        
        self.logger.info("Spark session created successfully")
        return self._spark_session
    
    def get_session(self) -> SparkSession:
        """
        Get existing Spark session or create new one
        
        Returns:
            SparkSession
        """
        if self._spark_session is None:
            return self.create_session()
        return self._spark_session
    
    def stop_session(self) -> None:
        """Stop Spark session"""
        if self._spark_session is not None:
            self.logger.info("Stopping Spark session")
            self._spark_session.stop()
            self._spark_session = None


# Global Spark manager instance
_spark_manager: Optional[SparkManager] = None


def get_spark_session(config: Optional[Dict[str, Any]] = None) -> SparkSession:
    """
    Get singleton Spark session
    
    Args:
        config: Spark configuration dictionary
        
    Returns:
        SparkSession
    """
    global _spark_manager
    if _spark_manager is None:
        _spark_manager = SparkManager(config)
    return _spark_manager.get_session()


def stop_spark_session() -> None:
    """Stop singleton Spark session"""
    global _spark_manager
    if _spark_manager is not None:
        _spark_manager.stop_session()
        _spark_manager = None
