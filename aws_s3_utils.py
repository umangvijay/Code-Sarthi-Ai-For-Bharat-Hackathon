"""
AWS S3 Utilities for Code-Sarthi
Handles PDF upload/download operations with S3 integration

This module implements secure S3 operations for PDF storage:
1. Upload PDFs to S3 with server-side encryption
2. Download PDFs from S3 with caching
3. Generate unique S3 keys for file organization
4. File integrity verification using checksums
5. Progress tracking for upload/download operations

Requirements Implemented:
- Requirement 7.1: Encrypt PDFs at rest using S3 server-side encryption
- Requirement 7.2: Encrypt data in transit using TLS 1.2+
- Requirement 7.3: Delete PDFs from S3 when requested

Key Features:
- Server-side encryption (AES-256)
- Unique key generation (UUID-based)
- Progress callbacks for UI integration
- Local caching for performance
- MD5 checksum verification
"""

import boto3
import os
import hashlib
import uuid
from datetime import datetime
from typing import Optional, Callable, Dict, Any
from botocore.exceptions import ClientError
import json


class S3Manager:
    """
    Manages S3 operations for PDF storage and retrieval
    
    Handles secure upload/download of PDFs with encryption,
    progress tracking, and local caching.
    """
    
    def __init__(
        self,
        bucket_name: str,
        region_name: str = "us-east-1",
        cache_dir: str = ".pdf_cache"
    ):
        """
        Initialize S3 Manager
        
        Args:
            bucket_name: S3 bucket name for PDF storage
            region_name: AWS region (default: us-east-1)
            cache_dir: Local directory for caching downloaded PDFs
        """
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.cache_dir = cache_dir
        
        # Initialize S3 client
        self.s3_client = boto3.client('s3', region_name=region_name)
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # Load cache metadata
        self.cache_metadata_file = os.path.join(cache_dir, "cache_metadata.json")
        self.cache_metadata = self._load_cache_metadata()
    
    def upload_pdf(
        self,
        pdf_bytes: bytes,
        original_filename: str,
        user_id: str = "default_user",
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Upload PDF to S3 with server-side encryption
        
        Process:
        1. Generate unique S3 key
        2. Calculate MD5 checksum
        3. Upload to S3 with encryption
        4. Store metadata
        5. Report progress
        
        Args:
            pdf_bytes: PDF file content as bytes
            original_filename: Original filename
            user_id: User identifier
            progress_callback: Optional callback(progress_percent, status_message)
            
        Returns:
            Dictionary with upload results including S3 URL and metadata
            
        Validates: Requirements 7.1 (encryption at rest), 7.2 (TLS in transit)
        """
        try:
            # Step 1: Generate unique S3 key
            if progress_callback:
                progress_callback(10, "Generating unique S3 key...")
            
            s3_key = self._generate_s3_key(original_filename, user_id)
            
            # Step 2: Calculate MD5 checksum for integrity
            if progress_callback:
                progress_callback(20, "Calculating checksum...")
            
            md5_checksum = self._calculate_md5(pdf_bytes)
            
            # Step 3: Upload to S3 with server-side encryption
            if progress_callback:
                progress_callback(30, "Uploading to S3...")
            
            # Upload with AES-256 server-side encryption
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=pdf_bytes,
                ServerSideEncryption='AES256',  # Requirement 7.1: Server-side encryption
                ContentType='application/pdf',
                Metadata={
                    'original-filename': original_filename,
                    'user-id': user_id,
                    'upload-timestamp': datetime.now().isoformat(),
                    'md5-checksum': md5_checksum
                }
            )
            
            if progress_callback:
                progress_callback(80, "Upload complete, generating URL...")
            
            # Step 4: Generate S3 URL
            s3_url = f"s3://{self.bucket_name}/{s3_key}"
            https_url = f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{s3_key}"
            
            # Step 5: Store metadata
            metadata = {
                's3_key': s3_key,
                's3_url': s3_url,
                'https_url': https_url,
                'bucket_name': self.bucket_name,
                'original_filename': original_filename,
                'user_id': user_id,
                'upload_timestamp': datetime.now().isoformat(),
                'file_size': len(pdf_bytes),
                'md5_checksum': md5_checksum,
                'encrypted': True
            }
            
            if progress_callback:
                progress_callback(100, "Upload successful!")
            
            return {
                'status': 'success',
                'message': f'Successfully uploaded {original_filename} to S3',
                'metadata': metadata
            }
            
        except ClientError as e:
            error_msg = f"S3 upload error: {str(e)}"
            if progress_callback:
                progress_callback(0, error_msg)
            
            return {
                'status': 'error',
                'message': error_msg
            }
        
        except Exception as e:
            error_msg = f"Unexpected error during upload: {str(e)}"
            if progress_callback:
                progress_callback(0, error_msg)
            
            return {
                'status': 'error',
                'message': error_msg
            }
    
    def download_pdf(
        self,
        s3_key: str,
        use_cache: bool = True,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Download PDF from S3 with local caching
        
        Process:
        1. Check local cache first
        2. Download from S3 if not cached
        3. Verify file integrity
        4. Cache locally for performance
        5. Report progress
        
        Args:
            s3_key: S3 object key
            use_cache: Whether to use local cache (default: True)
            progress_callback: Optional callback(progress_percent, status_message)
            
        Returns:
            Dictionary with download results including PDF bytes and metadata
            
        Validates: Requirements 7.2 (TLS in transit)
        """
        try:
            # Step 1: Check cache
            if use_cache:
                if progress_callback:
                    progress_callback(10, "Checking local cache...")
                
                cached_data = self._get_from_cache(s3_key)
                if cached_data:
                    if progress_callback:
                        progress_callback(100, "Retrieved from cache!")
                    
                    return {
                        'status': 'success',
                        'message': 'Retrieved from local cache',
                        'pdf_bytes': cached_data['pdf_bytes'],
                        'metadata': cached_data['metadata'],
                        'from_cache': True
                    }
            
            # Step 2: Download from S3
            if progress_callback:
                progress_callback(30, "Downloading from S3...")
            
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            pdf_bytes = response['Body'].read()
            
            if progress_callback:
                progress_callback(60, "Download complete, verifying integrity...")
            
            # Step 3: Verify integrity
            stored_checksum = response.get('Metadata', {}).get('md5-checksum')
            calculated_checksum = self._calculate_md5(pdf_bytes)
            
            if stored_checksum and stored_checksum != calculated_checksum:
                return {
                    'status': 'error',
                    'message': 'File integrity check failed - checksums do not match'
                }
            
            # Step 4: Cache locally
            if use_cache:
                if progress_callback:
                    progress_callback(80, "Caching locally...")
                
                metadata = {
                    's3_key': s3_key,
                    'bucket_name': self.bucket_name,
                    'original_filename': response.get('Metadata', {}).get('original-filename', 'unknown.pdf'),
                    'download_timestamp': datetime.now().isoformat(),
                    'file_size': len(pdf_bytes),
                    'md5_checksum': calculated_checksum
                }
                
                self._save_to_cache(s3_key, pdf_bytes, metadata)
            
            if progress_callback:
                progress_callback(100, "Download successful!")
            
            return {
                'status': 'success',
                'message': 'Successfully downloaded from S3',
                'pdf_bytes': pdf_bytes,
                'metadata': metadata,
                'from_cache': False
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                error_msg = f"PDF not found in S3: {s3_key}"
            else:
                error_msg = f"S3 download error: {str(e)}"
            
            if progress_callback:
                progress_callback(0, error_msg)
            
            return {
                'status': 'error',
                'message': error_msg
            }
        
        except Exception as e:
            error_msg = f"Unexpected error during download: {str(e)}"
            if progress_callback:
                progress_callback(0, error_msg)
            
            return {
                'status': 'error',
                'message': error_msg
            }
    
    def delete_pdf(
        self,
        s3_key: str,
        clear_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Delete PDF from S3 and optionally clear cache
        
        Args:
            s3_key: S3 object key
            clear_cache: Whether to clear local cache (default: True)
            
        Returns:
            Dictionary with deletion results
            
        Validates: Requirement 7.3 (data deletion)
        """
        try:
            # Delete from S3
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            # Clear cache if requested
            if clear_cache:
                self._remove_from_cache(s3_key)
            
            return {
                'status': 'success',
                'message': f'Successfully deleted {s3_key} from S3'
            }
            
        except ClientError as e:
            return {
                'status': 'error',
                'message': f'S3 deletion error: {str(e)}'
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Unexpected error during deletion: {str(e)}'
            }
    
    def get_pdf_metadata(self, s3_key: str) -> Dict[str, Any]:
        """
        Get metadata for a PDF in S3
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Dictionary with PDF metadata
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {
                'status': 'success',
                'metadata': {
                    's3_key': s3_key,
                    'bucket_name': self.bucket_name,
                    'file_size': response['ContentLength'],
                    'last_modified': response['LastModified'].isoformat(),
                    'encrypted': response.get('ServerSideEncryption') == 'AES256',
                    'custom_metadata': response.get('Metadata', {})
                }
            }
            
        except ClientError as e:
            return {
                'status': 'error',
                'message': f'Error getting metadata: {str(e)}'
            }
    
    # Private helper methods
    
    def _generate_s3_key(self, filename: str, user_id: str) -> str:
        """
        Generate unique S3 key using UUID and timestamp
        
        Format: pdfs/{user_id}/{timestamp}_{uuid}_{filename}
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        # Sanitize filename
        safe_filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
        
        return f"pdfs/{user_id}/{timestamp}_{unique_id}_{safe_filename}"
    
    def _calculate_md5(self, data: bytes) -> str:
        """Calculate MD5 checksum for data integrity verification"""
        return hashlib.md5(data).hexdigest()
    
    def _get_from_cache(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve PDF from local cache"""
        cache_key = self._get_cache_key(s3_key)
        cache_file = os.path.join(self.cache_dir, cache_key)
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    pdf_bytes = f.read()
                
                metadata = self.cache_metadata.get(s3_key, {})
                
                return {
                    'pdf_bytes': pdf_bytes,
                    'metadata': metadata
                }
            except Exception as e:
                print(f"Error reading from cache: {str(e)}")
                return None
        
        return None
    
    def _save_to_cache(self, s3_key: str, pdf_bytes: bytes, metadata: Dict[str, Any]):
        """Save PDF to local cache"""
        cache_key = self._get_cache_key(s3_key)
        cache_file = os.path.join(self.cache_dir, cache_key)
        
        try:
            # Save PDF bytes
            with open(cache_file, 'wb') as f:
                f.write(pdf_bytes)
            
            # Update metadata
            self.cache_metadata[s3_key] = metadata
            self._save_cache_metadata()
            
        except Exception as e:
            print(f"Error saving to cache: {str(e)}")
    
    def _remove_from_cache(self, s3_key: str):
        """Remove PDF from local cache"""
        cache_key = self._get_cache_key(s3_key)
        cache_file = os.path.join(self.cache_dir, cache_key)
        
        try:
            if os.path.exists(cache_file):
                os.remove(cache_file)
            
            if s3_key in self.cache_metadata:
                del self.cache_metadata[s3_key]
                self._save_cache_metadata()
                
        except Exception as e:
            print(f"Error removing from cache: {str(e)}")
    
    def _get_cache_key(self, s3_key: str) -> str:
        """Generate cache filename from S3 key"""
        # Use MD5 of S3 key as cache filename
        return hashlib.md5(s3_key.encode()).hexdigest() + '.pdf'
    
    def _load_cache_metadata(self) -> Dict[str, Any]:
        """Load cache metadata from JSON file"""
        if os.path.exists(self.cache_metadata_file):
            try:
                with open(self.cache_metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cache metadata: {str(e)}")
                return {}
        return {}
    
    def _save_cache_metadata(self):
        """Save cache metadata to JSON file"""
        try:
            with open(self.cache_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving cache metadata: {str(e)}")
    
    def clear_cache(self):
        """Clear all cached PDFs"""
        try:
            # Remove all cache files
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.pdf'):
                    os.remove(os.path.join(self.cache_dir, filename))
            
            # Clear metadata
            self.cache_metadata = {}
            self._save_cache_metadata()
            
            return {
                'status': 'success',
                'message': 'Cache cleared successfully'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error clearing cache: {str(e)}'
            }


# Convenience function for testing
def test_s3_manager():
    """Test S3 Manager functionality"""
    # Note: Requires actual S3 bucket to be configured
    bucket_name = "code-sarthi-pdfs"  # Replace with actual bucket name
    
    manager = S3Manager(bucket_name=bucket_name)
    
    print("S3 Manager initialized")
    print(f"Bucket: {bucket_name}")
    print(f"Cache directory: {manager.cache_dir}")
    
    # Test would require actual PDF file
    # This is just a structure demonstration
    
    return manager


if __name__ == "__main__":
    test_s3_manager()
