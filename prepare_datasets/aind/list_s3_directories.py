#!/usr/bin/env python3
"""
Script to list directories in s3://aind-benchmark-data/ephys-compression
Lists directories up to depth 2
"""
import boto3
from botocore import UNSIGNED
from botocore.config import Config


def list_s3_directories(bucket_name: str, prefix: str = '', depth: int = 1):
    """
    List directories (common prefixes) in an S3 bucket recursively up to a certain depth
    
    Args:
        bucket_name: Name of the S3 bucket
        prefix: Prefix path to list directories under (default: root)
        depth: How deep to recurse (1 = only immediate subdirs)
    """
    # S3 configuration for public bucket (no credentials needed)
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    
    # Ensure prefix ends with / if not empty
    if prefix and not prefix.endswith('/'):
        prefix += '/'
    
    # List objects with delimiter to get "directories"
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter='/')
    
    directories = []
    
    for page in pages:
        # CommonPrefixes contains the "directories"
        if 'CommonPrefixes' in page:
            for prefix_obj in page['CommonPrefixes']:
                dir_path = prefix_obj['Prefix']
                # Remove the base prefix to get relative path
                relative_dir = dir_path[len(prefix):] if prefix else dir_path
                directories.append(relative_dir)
    
    # Sort directories
    directories = sorted(directories)
    
    # Print current level directories and their subdirectories
    for directory in directories:
        print(f"  {directory}")
        
        # Recurse if depth > 1
        if depth > 1:
            # List subdirectories
            full_prefix = prefix + directory
            subpages = paginator.paginate(Bucket=bucket_name, Prefix=full_prefix, Delimiter='/')
            
            subdirs = []
            for page in subpages:
                if 'CommonPrefixes' in page:
                    for prefix_obj in page['CommonPrefixes']:
                        dir_path = prefix_obj['Prefix']
                        relative_dir = dir_path[len(full_prefix):] if full_prefix else dir_path
                        subdirs.append(relative_dir)
            
            # Print subdirectories with indentation
            for subdir in sorted(subdirs):
                print(f"    {subdir}")
    
    return directories


if __name__ == '__main__':
    bucket_name = 'aind-benchmark-data'
    prefix = 'ephys-compression'
    
    print(f"Listing directories in s3://{bucket_name}/{prefix} (depth 2)")
    print()
    
    list_s3_directories(bucket_name, prefix, depth=2)
