"""Test configuration"""

import pytest


@pytest.fixture
def sample_config():
    """Sample configuration for tests"""
    return {
        'aws': {
            'region': 'us-east-1',
            'access_key_id': 'test_key',
            'secret_access_key': 'test_secret'
        },
        's3': {
            'bucket_name': 'test-bucket',
            'raw_data_prefix': 'raw/',
            'processed_data_prefix': 'processed/'
        },
        'spark': {
            'app_name': 'TestPipeline',
            'master': 'local[2]'
        }
    }
