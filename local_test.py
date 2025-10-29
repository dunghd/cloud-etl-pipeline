"""Local testing example without AWS S3/Redshift

This example demonstrates how to test the ETL pipeline locally
using the sample data generated in data/raw/sample_data/
"""

from etl.transform.transformer import DataTransformer
from etl.utils.spark_manager import get_spark_session
from etl.utils.config import get_config
from etl.utils.logger import setup_logger
import os

# Setup logger
logger = setup_logger('LocalPipeline', log_level='INFO')

def run_local_pipeline():
    """Run ETL pipeline locally with sample data"""
    
    logger.info("=" * 80)
    logger.info("Starting LOCAL ETL Pipeline Test")
    logger.info("=" * 80)
    
    try:
        # Get configuration
        config = get_config()
        spark_config = config.get_spark_config()
        
        # Initialize Spark session
        logger.info("Initializing Spark session...")
        spark = get_spark_session(spark_config)
        
        # Initialize transformer
        transformer = DataTransformer(spark)
        
        # Input and output paths (local filesystem)
        input_path = "data/raw/sample_data/sales_data.parquet"
        output_path = "data/processed/sales_data_transformed"
        
        # Check if input file exists
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            logger.info("Please run: poetry run python generate_sample_data.py")
            return
        
        # Read local Parquet file
        logger.info(f"Reading data from {input_path}")
        df = spark.read.parquet(input_path)
        
        logger.info(f"Initial data shape: {df.count()} rows, {len(df.columns)} columns")
        
        # Show sample data
        logger.info("Sample data (first 5 rows):")
        df.show(5, truncate=False)
        
        # Data cleaning
        logger.info("Cleaning data...")
        df = transformer.clean_data(
            df,
            drop_duplicates=True,
            drop_null_columns=['customer_id', 'product_id'],
            fill_null_values={'discount': 0.0, 'tax': 0.0}
        )
        
        # Add derived columns
        logger.info("Adding derived columns...")
        df = transformer.add_derived_columns(
            df,
            timestamp_column='transaction_date'
        )
        
        # Filter data
        logger.info("Filtering data...")
        df = transformer.filter_data(
            df,
            filter_conditions='sales_amount > 0'
        )
        
        logger.info(f"Transformed data shape: {df.count()} rows, {len(df.columns)} columns")
        
        # Show transformed schema
        logger.info("Transformed schema:")
        df.printSchema()
        
        # Calculate data quality metrics
        logger.info("Calculating data quality metrics...")
        metrics = transformer.get_data_quality_metrics(df)
        logger.info(f"Total rows: {metrics['total_rows']}")
        logger.info(f"Total columns: {metrics['total_columns']}")
        
        # Show sample of transformed data
        logger.info("Sample transformed data (first 10 rows):")
        df.show(10, truncate=False)
        
        # Write to local parquet (partitioned by year and month)
        logger.info(f"Writing transformed data to {output_path}")
        df.write \
            .mode('overwrite') \
            .partitionBy('year', 'month') \
            .parquet(output_path)
        
        logger.info("=" * 80)
        logger.info("LOCAL ETL Pipeline completed successfully!")
        logger.info("=" * 80)
        
        # Show some statistics
        logger.info("\nPipeline Statistics:")
        logger.info(f"  - Input file: {input_path}")
        logger.info(f"  - Output directory: {output_path}")
        logger.info(f"  - Records processed: {metrics['total_rows']}")
        logger.info(f"  - Partitioned by: year, month")
        
        # Optional: Show aggregated data
        logger.info("\nSales by Store (Top 10):")
        df.groupBy('store_id') \
            .agg({'sales_amount': 'sum', 'quantity': 'sum'}) \
            .orderBy('sum(sales_amount)', ascending=False) \
            .show(10)
        
        logger.info("\nSales by Month:")
        df.groupBy('year', 'month') \
            .agg({'sales_amount': 'sum'}) \
            .orderBy('year', 'month') \
            .show()
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise
    finally:
        # Stop Spark session
        from etl.utils.spark_manager import stop_spark_session
        logger.info("Cleaning up...")
        stop_spark_session()
        logger.info("Cleanup completed")


if __name__ == '__main__':
    run_local_pipeline()
