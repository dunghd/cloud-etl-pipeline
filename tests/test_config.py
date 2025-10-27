"""Unit tests for configuration management"""

import pytest
import os
from unittest.mock import patch, mock_open
from etl.utils.config import Config


class TestConfig:
    """Test cases for Config class"""
    
    @patch('builtins.open', new_callable=mock_open, read_data="""
pipeline:
  name: "test-pipeline"
  version: "1.0.0"

aws:
  region: "us-west-2"

s3:
  bucket_name: "test-bucket"
  raw_data_prefix: "raw/"
""")
    @patch('etl.utils.config.load_dotenv')
    def test_config_initialization(self, mock_load_dotenv, mock_file):
        """Test configuration loading"""
        config = Config(config_path='test.yml')
        
        assert config.get('pipeline.name') == 'test-pipeline'
        assert config.get('aws.region') == 'us-west-2'
        assert config.get('s3.bucket_name') == 'test-bucket'
    
    @patch('builtins.open', new_callable=mock_open, read_data="""
aws:
  region: "us-east-1"
""")
    @patch('etl.utils.config.load_dotenv')
    def test_get_with_default(self, mock_load_dotenv, mock_file):
        """Test getting config with default value"""
        config = Config(config_path='test.yml')
        
        value = config.get('nonexistent.key', 'default_value')
        assert value == 'default_value'


if __name__ == '__main__':
    pytest.main([__file__])
