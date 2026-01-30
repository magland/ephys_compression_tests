"""
Utility functions for downloading from S3 public buckets
"""
import boto3
from botocore import UNSIGNED
from botocore.config import Config
import os
from pathlib import Path
import sys


class ProgressCallback:
    """Callback to show download progress"""
    def __init__(self, filename, filesize):
        self._filename = filename
        self._size = filesize
        self._seen_so_far = 0
        
    def __call__(self, bytes_amount):
        self._seen_so_far += bytes_amount
        percentage = (self._seen_so_far / self._size) * 100 if self._size > 0 else 0
        sys.stdout.write(
            f"\r  Progress: {self._seen_so_far:,} / {self._size:,} bytes ({percentage:.1f}%)"
        )
        sys.stdout.flush()


def download_s3_folder(s3_url: str, local_dir: str, skip_confirmation: bool = False):
    """
    Download entire folder from S3 public bucket
    
    Args:
        s3_url: S3 URL in format s3://bucket-name/path/to/folder/
        local_dir: Local directory path to download files to
        skip_confirmation: If True, skip user confirmation prompt
    """
    # Parse S3 URL
    if not s3_url.startswith('s3://'):
        raise ValueError(f"S3 URL must start with 's3://': {s3_url}")
    
    s3_url = s3_url.rstrip('/')
    s3_parts = s3_url[5:].split('/', 1)
    bucket_name = s3_parts[0]
    prefix = s3_parts[1] + '/' if len(s3_parts) > 1 else ''
    
    # S3 configuration for public bucket (no credentials needed)
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    
    # Create local directory
    Path(local_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"Scanning s3://{bucket_name}/{prefix}")
    print(f"Will download to local directory: {local_dir}/")
    print()
    
    # List all objects in the folder to calculate total size
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
    
    files_to_download = []
    total_size = 0
    
    for page in pages:
        if 'Contents' not in page:
            print("No files found in the specified path")
            return
        
        for obj in page['Contents']:
            s3_key = obj['Key']
            file_size = obj['Size']
            
            # Skip if it's just the directory itself
            if s3_key == prefix or s3_key == prefix.rstrip('/'):
                continue
            
            # Get the relative path (remove the prefix)
            relative_path = s3_key[len(prefix):]
            if not relative_path:
                continue
            
            files_to_download.append({
                's3_key': s3_key,
                'relative_path': relative_path,
                'size': file_size
            })
            total_size += file_size
    
    print(f"Found {len(files_to_download)} files")
    print(f"Total size: {total_size:,} bytes ({total_size / (1024**2):.2f} MB, {total_size / (1024**3):.2f} GB)")
    print()
    
    if not skip_confirmation:
        response = input("Continue with download? (y/n): ")
        if response.lower() != 'y':
            print("Download cancelled")
            return
    
    print()
    print("Starting download...")
    print()
    
    # Download all files
    downloaded_bytes = 0
    for idx, file_info in enumerate(files_to_download, 1):
        s3_key = file_info['s3_key']
        relative_path = file_info['relative_path']
        file_size = file_info['size']
        
        # Local file path
        local_file = os.path.join(local_dir, relative_path)
        
        # Create subdirectories if needed
        local_file_dir = os.path.dirname(local_file)
        if local_file_dir:
            Path(local_file_dir).mkdir(parents=True, exist_ok=True)
        
        # Download the file with progress callback
        print(f"[{idx}/{len(files_to_download)}] {relative_path} ({file_size:,} bytes)")
        progress = ProgressCallback(relative_path, file_size)
        s3.download_file(bucket_name, s3_key, local_file, Callback=progress)
        print()  # New line after progress
        
        downloaded_bytes += file_size
        overall_progress = (downloaded_bytes / total_size) * 100
        print(f"  Overall progress: {downloaded_bytes:,} / {total_size:,} bytes ({overall_progress:.1f}%)")
        print()
    
    print(f"Download complete!")
    print(f"Total files: {len(files_to_download)}")
    print(f"Total size: {total_size:,} bytes ({total_size / (1024**3):.2f} GB)")
