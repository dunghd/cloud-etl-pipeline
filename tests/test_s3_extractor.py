"""Unit tests for S3 Extractor"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from etl.extract.s3_extractor import S3Extractor


class TestS3Extractor:
    """Test cases for S3Extractor"""
    
    @patch('etl.extract.s3_extractor.boto3')
    def test_initialization(self, mock_boto3):
        """Test S3Extractor initialization"""
        extractor = S3Extractor(
            bucket_name='test-bucket',
            region='us-east-1'
        )
        
        assert extractor.bucket_name == 'test-bucket'
        assert extractor.region == 'us-east-1'
        mock_boto3.client.assert_called()
        mock_boto3.resource.assert_called()
    
    @patch('etl.extract.s3_extractor.boto3')
    def test_get_s3_uri(self, mock_boto3):
        """Test S3 URI generation"""
        extractor = S3Extractor(bucket_name='test-bucket')
        uri = extractor.get_s3_uri('data/file.parquet')
        
        assert uri == 's3://test-bucket/data/file.parquet'
    
    @patch('etl.extract.s3_extractor.boto3')
    def test_list_objects(self, mock_boto3):
        """Test listing S3 objects"""
        # Mock S3 bucket
        mock_bucket = MagicMock()
        mock_object1 = MagicMock()
        mock_object1.key = 'data/file1.parquet'
        mock_object1.size = 1000
        
        mock_object2 = MagicMock()
        mock_object2.key = 'data/file2.parquet'
        mock_object2.size = 2000
        
        mock_bucket.objects.filter.return_value = [mock_object1, mock_object2]
        
        extractor = S3Extractor(bucket_name='test-bucket')
        extractor.bucket = mock_bucket
        
        objects = extractor.list_objects(prefix='data/', suffix='.parquet')
        
        assert len(objects) == 2
        assert objects[0]['key'] == 'data/file1.parquet'
        assert objects[1]['size'] == 2000


if __name__ == '__main__':
    pytest.main([__file__])
