"""Main ETL pipeline orchestration"""

import os
from datetime import datetime
from typing import Optional, Dict, Any

from etl.extract.s3_extractor import S3Extractor
from etl.transform.transformer import DataTransformer
from etl.load.redshift_loader import RedshiftLoader
from etl.utils.config import get_config
from etl.utils.logger import setup_logger
from etl.utils.spark_manager import get_spark_session, stop_spark_session


class ETLPipeline:
    """Main ETL pipeline orchestrator"""
    
    def __init__(self, config_path: Optional[str] = None, env_file: Optional[str] = None):
        """
        Initialize ETL pipeline
        
        Args:
            config_path: Path to configuration file
            env_file: Path to .env file
        """
        # Load configuration
        self.config = get_config(config_path, env_file)
        
        # Setup logger
        self.logger = setup_logger(
            'ETLPipeline',
            log_level=self.config.get('logging.level', 'INFO'),
            log_dir=self.config.get('logging.log_dir', 'logs')
        )
        
        self.logger.info("=" * 80)
        self.logger.info("Initializing Cloud ETL Pipeline")
        self.logger.info("=" * 80)
        
        # Initialize components
        self._init_components()
    
    def _init_components(self):
        """Initialize ETL components"""
        # Get configurations
        aws_config = self.config.get_aws_config()
        s3_config = self.config.get_s3_config()
        spark_config = self.config.get_spark_config()
        redshift_config = self.config.get_redshift_config()
        
        # Initialize S3 Extractor
        self.logger.info("Initializing S3 Extractor...")
        self.extractor = S3Extractor(
            bucket_name=s3_config['bucket_name'],
            aws_access_key_id=aws_config.get('access_key_id'),
            aws_secret_access_key=aws_config.get('secret_access_key'),
            region=aws_config['region']
        )
        
        # Initialize Spark session
        self.logger.info("Initializing Spark session...")
        self.spark = get_spark_session(spark_config)
        
        # Initialize Data Transformer
        self.logger.info("Initializing Data Transformer...")
        self.transformer = DataTransformer(self.spark)
        
        # Initialize Redshift Loader
        self.logger.info("Initializing Redshift Loader...")
        self.loader = RedshiftLoader(
            host=redshift_config['host'],
            port=redshift_config['port'],
            database=redshift_config['database'],
            user=redshift_config['user'],
            password=redshift_config['password'],
            schema=redshift_config['schema'],
            temp_dir=redshift_config.get('temp_dir')
        )
        
        self.logger.info("All components initialized successfully")
    
    def extract(self, s3_prefix: str, file_format: str = 'parquet') -> str:
        """
        Extract data from S3
        
        Args:
            s3_prefix: S3 prefix to extract from
            file_format: File format (parquet, csv, json)
            
        Returns:
            S3 path to extracted data
        """
        self.logger.info(f"Starting EXTRACT phase - Prefix: {s3_prefix}")
        
        try:
            # List objects in S3
            objects = self.extractor.list_objects(prefix=s3_prefix, suffix=file_format)
            
            if not objects:
                raise ValueError(f"No {file_format} files found with prefix: {s3_prefix}")
            
            self.logger.info(f"Found {len(objects)} files to process")
            
            # Return S3 URI for the prefix
            s3_path = self.extractor.get_s3_uri(s3_prefix)
            
            self.logger.info(f"EXTRACT phase completed - S3 Path: {s3_path}")
            return s3_path
            
        except Exception as e:
            self.logger.error(f"EXTRACT phase failed: {e}")
            raise
    
    def transform(
        self,
        input_s3_path: str,
        output_s3_prefix: str,
        file_format: str = 'parquet',
        transformation_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Transform data using PySpark
        
        Args:
            input_s3_path: S3 path to input data
            output_s3_prefix: S3 prefix for output data
            file_format: File format
            transformation_config: Custom transformation configuration
            
        Returns:
            S3 path to transformed data
        """
        self.logger.info(f"Starting TRANSFORM phase - Input: {input_s3_path}")
        
        try:
            # Read data from S3
            df = self.transformer.read_from_s3(input_s3_path, file_format)
            
            self.logger.info(f"Initial data shape: {df.count()} rows, {len(df.columns)} columns")
            
            # Show sample data
            self.logger.info("Sample data:")
            df.show(5, truncate=False)
            
            # Apply transformations
            transformation_config = transformation_config or {}
            
            # Clean data
            if transformation_config.get('clean_data', True):
                df = self.transformer.clean_data(
                    df,
                    drop_duplicates=transformation_config.get('drop_duplicates', True),
                    drop_null_columns=transformation_config.get('drop_null_columns'),
                    fill_null_values=transformation_config.get('fill_null_values')
                )
            
            # Add derived columns
            if transformation_config.get('add_derived_columns', True):
                df = self.transformer.add_derived_columns(
                    df,
                    timestamp_column=transformation_config.get('timestamp_column')
                )
            
            # Filter data
            if 'filter_conditions' in transformation_config:
                df = self.transformer.filter_data(
                    df,
                    transformation_config['filter_conditions']
                )
            
            # Aggregate data
            if 'aggregate' in transformation_config:
                agg_config = transformation_config['aggregate']
                df = self.transformer.aggregate_data(
                    df,
                    group_by_columns=agg_config['group_by'],
                    agg_expressions=agg_config['expressions']
                )
            
            self.logger.info(f"Transformed data shape: {df.count()} rows, {len(df.columns)} columns")
            
            # Calculate data quality metrics
            metrics = self.transformer.get_data_quality_metrics(df)
            self.logger.info(f"Data quality metrics: {metrics}")
            
            # Write transformed data to S3
            output_s3_path = self.extractor.get_s3_uri(output_s3_prefix)
            
            partition_by = transformation_config.get('partition_by')
            self.transformer.write_to_s3(
                df,
                output_s3_path,
                file_format=file_format,
                partition_by=partition_by
            )
            
            self.logger.info(f"TRANSFORM phase completed - Output: {output_s3_path}")
            return output_s3_path
            
        except Exception as e:
            self.logger.error(f"TRANSFORM phase failed: {e}")
            raise
    
    def load(
        self,
        s3_path: str,
        table_name: str,
        file_format: str = 'parquet',
        mode: str = 'append'
    ) -> None:
        """
        Load data into Redshift data warehouse
        
        Args:
            s3_path: S3 path to data
            table_name: Target table name
            file_format: File format
            mode: Load mode ('append' or 'overwrite')
        """
        self.logger.info(f"Starting LOAD phase - Table: {table_name}")
        
        try:
            aws_config = self.config.get_aws_config()
            
            # Load data from S3 to Redshift
            self.loader.load_from_s3(
                table_name=table_name,
                s3_path=s3_path,
                aws_access_key_id=aws_config.get('access_key_id'),
                aws_secret_access_key=aws_config.get('secret_access_key'),
                file_format=file_format,
                mode=mode
            )
            
            self.logger.info(f"LOAD phase completed - Table: {table_name}")
            
        except Exception as e:
            self.logger.error(f"LOAD phase failed: {e}")
            raise
    
    def run(
        self,
        source_prefix: str,
        target_table: str,
        file_format: str = 'parquet',
        transformation_config: Optional[Dict[str, Any]] = None,
        load_mode: str = 'append'
    ) -> None:
        """
        Run complete ETL pipeline
        
        Args:
            source_prefix: S3 prefix for source data
            target_table: Target Redshift table name
            file_format: File format
            transformation_config: Transformation configuration
            load_mode: Load mode ('append' or 'overwrite')
        """
        start_time = datetime.now()
        self.logger.info("=" * 80)
        self.logger.info(f"Starting ETL Pipeline Run - {start_time}")
        self.logger.info("=" * 80)
        
        try:
            # Get S3 configuration
            s3_config = self.config.get_s3_config()
            
            # Construct full source path
            full_source_prefix = f"{s3_config['raw_data_prefix']}{source_prefix}"
            
            # Extract
            extracted_path = self.extract(full_source_prefix, file_format)
            
            # Transform
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_prefix = f"{s3_config['processed_data_prefix']}{source_prefix}_{timestamp}"
            
            transformed_path = self.transform(
                extracted_path,
                output_prefix,
                file_format,
                transformation_config
            )
            
            # Load
            self.load(transformed_path, target_table, file_format, load_mode)
            
            # Calculate execution time
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info("=" * 80)
            self.logger.info(f"ETL Pipeline completed successfully in {duration:.2f} seconds")
            self.logger.info("=" * 80)
            
        except Exception as e:
            self.logger.error(f"ETL Pipeline failed: {e}")
            raise
    
    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up resources...")
        stop_spark_session()
        self.logger.info("Cleanup completed")


def main():
    """Main entry point"""
    # Initialize pipeline
    pipeline = ETLPipeline()
    
    try:
        # Example usage
        pipeline.run(
            source_prefix='sales_data',
            target_table='sales_fact',
            file_format='parquet',
            transformation_config={
                'clean_data': True,
                'drop_duplicates': True,
                'add_derived_columns': True,
                'timestamp_column': 'transaction_date',
                'partition_by': ['year', 'month']
            },
            load_mode='append'
        )
    finally:
        # Cleanup
        pipeline.cleanup()


if __name__ == '__main__':
    main()
