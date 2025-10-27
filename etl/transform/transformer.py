"""PySpark data transformation module"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *
from typing import Optional, List, Dict, Any

from etl.utils.logger import LoggerMixin


class DataTransformer(LoggerMixin):
    """Transform data using PySpark"""
    
    def __init__(self, spark: SparkSession):
        """
        Initialize data transformer
        
        Args:
            spark: SparkSession instance
        """
        self.spark = spark
        self.logger.info("Initialized DataTransformer")
    
    def read_from_s3(
        self,
        s3_path: str,
        file_format: str = 'parquet',
        options: Optional[Dict[str, Any]] = None
    ) -> DataFrame:
        """
        Read data from S3
        
        Args:
            s3_path: S3 path (s3://bucket/path)
            file_format: File format (parquet, csv, json)
            options: Additional read options
            
        Returns:
            Spark DataFrame
        """
        try:
            self.logger.info(f"Reading {file_format} from {s3_path}")
            
            reader = self.spark.read.format(file_format)
            
            if options:
                for key, value in options.items():
                    reader = reader.option(key, value)
            
            df = reader.load(s3_path)
            
            self.logger.info(f"Read {df.count()} rows with {len(df.columns)} columns")
            return df
            
        except Exception as e:
            self.logger.error(f"Error reading from S3: {e}")
            raise
    
    def clean_data(
        self,
        df: DataFrame,
        drop_duplicates: bool = True,
        drop_null_columns: Optional[List[str]] = None,
        fill_null_values: Optional[Dict[str, Any]] = None
    ) -> DataFrame:
        """
        Clean data by removing duplicates and handling nulls
        
        Args:
            df: Input DataFrame
            drop_duplicates: Whether to drop duplicate rows
            drop_null_columns: Columns where null values should be dropped
            fill_null_values: Dictionary mapping column names to fill values
            
        Returns:
            Cleaned DataFrame
        """
        self.logger.info("Starting data cleaning")
        
        cleaned_df = df
        
        # Drop duplicates
        if drop_duplicates:
            initial_count = cleaned_df.count()
            cleaned_df = cleaned_df.dropDuplicates()
            duplicates_removed = initial_count - cleaned_df.count()
            self.logger.info(f"Removed {duplicates_removed} duplicate rows")
        
        # Drop rows with null values in specific columns
        if drop_null_columns:
            initial_count = cleaned_df.count()
            cleaned_df = cleaned_df.dropna(subset=drop_null_columns)
            nulls_removed = initial_count - cleaned_df.count()
            self.logger.info(f"Removed {nulls_removed} rows with null values")
        
        # Fill null values
        if fill_null_values:
            cleaned_df = cleaned_df.fillna(fill_null_values)
            self.logger.info(f"Filled null values for columns: {list(fill_null_values.keys())}")
        
        return cleaned_df
    
    def add_derived_columns(
        self,
        df: DataFrame,
        timestamp_column: Optional[str] = None
    ) -> DataFrame:
        """
        Add derived columns like timestamps, date parts, etc.
        
        Args:
            df: Input DataFrame
            timestamp_column: Column to extract date parts from
            
        Returns:
            DataFrame with derived columns
        """
        self.logger.info("Adding derived columns")
        
        result_df = df
        
        # Add processing timestamp
        result_df = result_df.withColumn('processed_at', F.current_timestamp())
        
        # Extract date parts if timestamp column provided
        if timestamp_column and timestamp_column in df.columns:
            result_df = result_df \
                .withColumn('year', F.year(F.col(timestamp_column))) \
                .withColumn('month', F.month(F.col(timestamp_column))) \
                .withColumn('day', F.dayofmonth(F.col(timestamp_column))) \
                .withColumn('hour', F.hour(F.col(timestamp_column)))
            
            self.logger.info(f"Extracted date parts from {timestamp_column}")
        
        return result_df
    
    def aggregate_data(
        self,
        df: DataFrame,
        group_by_columns: List[str],
        agg_expressions: Dict[str, str]
    ) -> DataFrame:
        """
        Aggregate data by specified columns
        
        Args:
            df: Input DataFrame
            group_by_columns: Columns to group by
            agg_expressions: Dictionary mapping column names to aggregation functions
                           e.g., {'sales': 'sum', 'quantity': 'avg'}
            
        Returns:
            Aggregated DataFrame
        """
        self.logger.info(f"Aggregating data by {group_by_columns}")
        
        agg_list = []
        for col_name, agg_func in agg_expressions.items():
            if agg_func == 'sum':
                agg_list.append(F.sum(col_name).alias(f"{col_name}_sum"))
            elif agg_func == 'avg':
                agg_list.append(F.avg(col_name).alias(f"{col_name}_avg"))
            elif agg_func == 'count':
                agg_list.append(F.count(col_name).alias(f"{col_name}_count"))
            elif agg_func == 'min':
                agg_list.append(F.min(col_name).alias(f"{col_name}_min"))
            elif agg_func == 'max':
                agg_list.append(F.max(col_name).alias(f"{col_name}_max"))
        
        result_df = df.groupBy(*group_by_columns).agg(*agg_list)
        
        self.logger.info(f"Aggregation complete: {result_df.count()} rows")
        return result_df
    
    def filter_data(
        self,
        df: DataFrame,
        filter_conditions: str
    ) -> DataFrame:
        """
        Filter data based on conditions
        
        Args:
            df: Input DataFrame
            filter_conditions: Filter condition as SQL string
            
        Returns:
            Filtered DataFrame
        """
        self.logger.info(f"Filtering data with condition: {filter_conditions}")
        
        initial_count = df.count()
        filtered_df = df.filter(filter_conditions)
        final_count = filtered_df.count()
        
        self.logger.info(f"Filtered from {initial_count} to {final_count} rows")
        return filtered_df
    
    def join_dataframes(
        self,
        left_df: DataFrame,
        right_df: DataFrame,
        join_columns: List[str],
        join_type: str = 'inner'
    ) -> DataFrame:
        """
        Join two DataFrames
        
        Args:
            left_df: Left DataFrame
            right_df: Right DataFrame
            join_columns: Columns to join on
            join_type: Type of join (inner, left, right, outer)
            
        Returns:
            Joined DataFrame
        """
        self.logger.info(f"Performing {join_type} join on columns: {join_columns}")
        
        joined_df = left_df.join(right_df, on=join_columns, how=join_type)
        
        self.logger.info(f"Join complete: {joined_df.count()} rows")
        return joined_df
    
    def write_to_s3(
        self,
        df: DataFrame,
        s3_path: str,
        file_format: str = 'parquet',
        partition_by: Optional[List[str]] = None,
        mode: str = 'overwrite',
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Write DataFrame to S3
        
        Args:
            df: DataFrame to write
            s3_path: S3 path (s3://bucket/path)
            file_format: File format (parquet, csv, json)
            partition_by: Columns to partition by
            mode: Write mode (overwrite, append, error, ignore)
            options: Additional write options
        """
        try:
            self.logger.info(f"Writing {file_format} to {s3_path}")
            
            writer = df.write.format(file_format).mode(mode)
            
            if partition_by:
                writer = writer.partitionBy(*partition_by)
                self.logger.info(f"Partitioning by: {partition_by}")
            
            if options:
                for key, value in options.items():
                    writer = writer.option(key, value)
            
            writer.save(s3_path)
            
            self.logger.info(f"Successfully wrote {df.count()} rows to {s3_path}")
            
        except Exception as e:
            self.logger.error(f"Error writing to S3: {e}")
            raise
    
    def get_data_quality_metrics(self, df: DataFrame) -> Dict[str, Any]:
        """
        Calculate data quality metrics
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary of metrics
        """
        self.logger.info("Calculating data quality metrics")
        
        metrics = {
            'total_rows': df.count(),
            'total_columns': len(df.columns),
            'columns': {}
        }
        
        for col_name in df.columns:
            col_metrics = {
                'null_count': df.filter(F.col(col_name).isNull()).count(),
                'distinct_count': df.select(col_name).distinct().count()
            }
            metrics['columns'][col_name] = col_metrics
        
        return metrics
