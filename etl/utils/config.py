"""Configuration management utilities"""

import os
import yaml
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration manager for the ETL pipeline"""
    
    def __init__(self, config_path: str = None, env_file: str = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to YAML configuration file
            env_file: Path to .env file
        """
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        # Load YAML configuration
        if config_path is None:
            config_path = os.path.join(
                Path(__file__).parent.parent.parent,
                "config",
                "config.yml"
            )
        
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key
        
        Args:
            key: Configuration key in dot notation (e.g., 'aws.region')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def get_aws_config(self) -> Dict[str, str]:
        """Get AWS configuration from environment variables"""
        return {
            'access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
            'secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'region': os.getenv('AWS_REGION', self.get('aws.region', 'us-east-1'))
        }
    
    def get_s3_config(self) -> Dict[str, str]:
        """Get S3 configuration"""
        return {
            'bucket_name': os.getenv('S3_BUCKET_NAME', self.get('s3.bucket_name')),
            'raw_data_prefix': os.getenv('S3_RAW_DATA_PREFIX', self.get('s3.raw_data_prefix')),
            'processed_data_prefix': os.getenv('S3_PROCESSED_DATA_PREFIX', 
                                               self.get('s3.processed_data_prefix')),
            'temp_prefix': self.get('s3.temp_prefix', 'temp/'),
            'file_format': self.get('s3.file_format', 'parquet')
        }
    
    def get_redshift_config(self) -> Dict[str, Any]:
        """Get Redshift configuration from environment variables"""
        return {
            'host': os.getenv('REDSHIFT_HOST', self.get('redshift.host')),
            'port': int(os.getenv('REDSHIFT_PORT', self.get('redshift.port', 5439))),
            'database': os.getenv('REDSHIFT_DATABASE', self.get('redshift.database')),
            'user': os.getenv('REDSHIFT_USER'),
            'password': os.getenv('REDSHIFT_PASSWORD'),
            'schema': os.getenv('REDSHIFT_SCHEMA', self.get('redshift.schema', 'public')),
            'temp_dir': self.get('redshift.temp_dir'),
            'iam_role': os.getenv('REDSHIFT_IAM_ROLE', self.get('redshift.iam_role'))
        }
    
    def get_spark_config(self) -> Dict[str, Any]:
        """Get Spark configuration"""
        return {
            'app_name': self.get('spark.app_name', 'CloudETLPipeline'),
            'master': os.getenv('SPARK_MASTER', self.get('spark.master', 'local[*]')),
            'executor_memory': self.get('spark.executor_memory', '4g'),
            'driver_memory': self.get('spark.driver_memory', '2g'),
            'executor_cores': self.get('spark.executor_cores', 2),
            'max_result_size': self.get('spark.max_result_size', '2g')
        }
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self._config


# Global configuration instance
_config_instance = None


def get_config(config_path: str = None, env_file: str = None) -> Config:
    """
    Get singleton configuration instance
    
    Args:
        config_path: Path to YAML configuration file
        env_file: Path to .env file
        
    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path, env_file)
    return _config_instance
