"""S3 data extractor module"""

import boto3
from typing import List, Optional, Dict, Any
from botocore.exceptions import ClientError
import os
from pathlib import Path

from etl.utils.logger import LoggerMixin


class S3Extractor(LoggerMixin):
    """Extract data from AWS S3 bucket"""
    
    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region: str = 'us-east-1'
    ):
        """
        Initialize S3 extractor
        
        Args:
            bucket_name: S3 bucket name
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region: AWS region
        """
        self.bucket_name = bucket_name
        self.region = region
        
        # Initialize S3 client
        session_config = {'region_name': region}
        if aws_access_key_id and aws_secret_access_key:
            session_config['aws_access_key_id'] = aws_access_key_id
            session_config['aws_secret_access_key'] = aws_secret_access_key
        
        self.s3_client = boto3.client('s3', **session_config)
        self.s3_resource = boto3.resource('s3', **session_config)
        self.bucket = self.s3_resource.Bucket(bucket_name)
        
        self.logger.info(f"Initialized S3Extractor for bucket: {bucket_name}")
    
    def list_objects(
        self,
        prefix: str = '',
        suffix: str = '',
        max_keys: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List objects in S3 bucket with optional filtering
        
        Args:
            prefix: Filter objects by prefix
            suffix: Filter objects by suffix
            max_keys: Maximum number of objects to return
            
        Returns:
            List of object metadata dictionaries
        """
        try:
            self.logger.info(f"Listing objects with prefix: {prefix}, suffix: {suffix}")
            
            objects = []
            for obj in self.bucket.objects.filter(Prefix=prefix):
                if suffix and not obj.key.endswith(suffix):
                    continue
                
                objects.append({
                    'key': obj.key,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                    'etag': obj.e_tag
                })
                
                if max_keys and len(objects) >= max_keys:
                    break
            
            self.logger.info(f"Found {len(objects)} objects")
            return objects
            
        except ClientError as e:
            self.logger.error(f"Error listing objects: {e}")
            raise
    
    def download_file(self, s3_key: str, local_path: str) -> str:
        """
        Download a single file from S3
        
        Args:
            s3_key: S3 object key
            local_path: Local file path to save the downloaded file
            
        Returns:
            Local file path
        """
        try:
            self.logger.info(f"Downloading {s3_key} to {local_path}")
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            
            self.logger.info(f"Successfully downloaded {s3_key}")
            return local_path
            
        except ClientError as e:
            self.logger.error(f"Error downloading file {s3_key}: {e}")
            raise
    
    def download_prefix(
        self,
        prefix: str,
        local_dir: str,
        file_extension: Optional[str] = None
    ) -> List[str]:
        """
        Download all files with a given prefix from S3
        
        Args:
            prefix: S3 prefix to download
            local_dir: Local directory to save files
            file_extension: Optional file extension filter
            
        Returns:
            List of local file paths
        """
        try:
            self.logger.info(f"Downloading files with prefix {prefix} to {local_dir}")
            
            objects = self.list_objects(
                prefix=prefix,
                suffix=file_extension if file_extension else ''
            )
            
            downloaded_files = []
            for obj in objects:
                s3_key = obj['key']
                
                # Skip directories
                if s3_key.endswith('/'):
                    continue
                
                # Create local path maintaining S3 structure
                relative_path = s3_key[len(prefix):].lstrip('/')
                local_path = os.path.join(local_dir, relative_path)
                
                self.download_file(s3_key, local_path)
                downloaded_files.append(local_path)
            
            self.logger.info(f"Downloaded {len(downloaded_files)} files")
            return downloaded_files
            
        except Exception as e:
            self.logger.error(f"Error downloading prefix {prefix}: {e}")
            raise
    
    def get_s3_uri(self, key: str) -> str:
        """
        Get S3 URI for a given key
        
        Args:
            key: S3 object key
            
        Returns:
            S3 URI (s3://bucket/key)
        """
        return f"s3://{self.bucket_name}/{key}"
    
    def upload_file(self, local_path: str, s3_key: str) -> str:
        """
        Upload a file to S3
        
        Args:
            local_path: Local file path
            s3_key: S3 object key
            
        Returns:
            S3 URI
        """
        try:
            self.logger.info(f"Uploading {local_path} to {s3_key}")
            
            self.s3_client.upload_file(local_path, self.bucket_name, s3_key)
            
            self.logger.info(f"Successfully uploaded to {s3_key}")
            return self.get_s3_uri(s3_key)
            
        except ClientError as e:
            self.logger.error(f"Error uploading file {local_path}: {e}")
            raise
    
    def delete_object(self, s3_key: str) -> None:
        """
        Delete an object from S3
        
        Args:
            s3_key: S3 object key to delete
        """
        try:
            self.logger.info(f"Deleting object {s3_key}")
            
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            
            self.logger.info(f"Successfully deleted {s3_key}")
            
        except ClientError as e:
            self.logger.error(f"Error deleting object {s3_key}: {e}")
            raise
    
    def object_exists(self, s3_key: str) -> bool:
        """
        Check if an object exists in S3
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if object exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False
