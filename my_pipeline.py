# Create a file: my_pipeline.py
from etl.pipeline import ETLPipeline

pipeline = ETLPipeline()

try:
    pipeline.run(
        # Use specific parquet file path instead of prefix containing mixed formats
        source_prefix='sales_data/sales_data.parquet',  # Specific parquet file
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