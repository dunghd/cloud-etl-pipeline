"""Example pipeline usage scripts"""

import os
from etl.pipeline import ETLPipeline


def example_simple_pipeline():
    """
    Simple ETL pipeline example
    Extracts data from S3, applies basic transformations, and loads to Redshift
    """
    # Initialize pipeline
    pipeline = ETLPipeline()
    
    try:
        # Run pipeline
        pipeline.run(
            source_prefix='sample_data',
            target_table='processed_data',
            file_format='parquet',
            transformation_config={
                'clean_data': True,
                'drop_duplicates': True,
                'add_derived_columns': False
            },
            load_mode='overwrite'
        )
    finally:
        pipeline.cleanup()


def example_advanced_pipeline():
    """
    Advanced ETL pipeline example with custom transformations
    """
    pipeline = ETLPipeline()
    
    try:
        # Run pipeline with advanced transformations
        pipeline.run(
            source_prefix='sales_data/2024',
            target_table='sales_aggregated',
            file_format='parquet',
            transformation_config={
                'clean_data': True,
                'drop_duplicates': True,
                'drop_null_columns': ['customer_id', 'product_id', 'sales_amount'],
                'fill_null_values': {
                    'discount': 0.0,
                    'tax': 0.0
                },
                'add_derived_columns': True,
                'timestamp_column': 'order_date',
                'filter_conditions': 'sales_amount > 0',
                'aggregate': {
                    'group_by': ['product_id', 'year', 'month'],
                    'expressions': {
                        'sales_amount': 'sum',
                        'quantity': 'sum',
                        'customer_id': 'count'
                    }
                },
                'partition_by': ['year', 'month']
            },
            load_mode='overwrite'
        )
    finally:
        pipeline.cleanup()


def example_custom_workflow():
    """
    Custom workflow with separate extract, transform, and load steps
    """
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
                'add_derived_columns': True,
                'timestamp_column': 'registration_date'
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


if __name__ == '__main__':
    # Choose which example to run
    print("Running simple pipeline example...")
    # example_simple_pipeline()
    
    # Or run advanced example
    # example_advanced_pipeline()
    
    # Or run custom workflow
    # example_custom_workflow()
