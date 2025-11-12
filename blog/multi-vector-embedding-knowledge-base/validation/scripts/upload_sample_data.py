#!/usr/bin/env python3
"""
Sample Data Upload Script

This script reads sample data from a CSV file and uploads documents to the S3 bucket
created by the CDK stack. For each row in the CSV:
1. Creates a .txt file with the document content
2. Creates a .metadata.json file with the metadata from other columns

Usage:
    python validation/scripts/upload_sample_data.py
"""

import csv
import json
import os
import sys
import uuid
import boto3
from typing import Dict, Any, List
import argparse
from pathlib import Path


class SampleDataUploader:
    """Handles uploading sample data to S3 bucket."""
    
    def __init__(self, bucket_name: str, region: str = 'us-west-2'):
        """
        Initialize the uploader.
        
        Args:
            bucket_name: Name of the S3 bucket to upload to
            region: AWS region (default: us-west-2)
        """
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
        
    def read_csv_data(self, csv_file_path: str) -> List[Dict[str, Any]]:
        """
        Read data from CSV file.
        
        Args:
            csv_file_path: Path to the CSV file
            
        Returns:
            List of dictionaries containing row data
        """
        data = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    data.append(dict(row))
                    
            print(f"Successfully read {len(data)} rows from {csv_file_path}")
            return data
            
        except FileNotFoundError:
            print(f"Error: CSV file not found at {csv_file_path}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
            sys.exit(1)
    
    def generate_filename(self) -> str:
        """
        Generate a random filename.
        
        Returns:
            Random filename without extension
        """
        return str(uuid.uuid4())
    
    def create_metadata(self, row_data: Dict[str, Any], exclude_columns: List[str] = None) -> Dict[str, Any]:
        """
        Create metadata dictionary from CSV row, excluding specified columns.
        
        Args:
            row_data: Dictionary containing CSV row data
            exclude_columns: List of column names to exclude from metadata
            
        Returns:
            Metadata dictionary
        """
        if exclude_columns is None:
            exclude_columns = ['document']
            
        metadata = {}
        for key, value in row_data.items():
            if key not in exclude_columns and value:  # Only include non-empty values
                metadata[key] = value.strip() if isinstance(value, str) else value
                
        return metadata
    
    def upload_document(self, filename: str, content: str, s3_prefix: str = "documents/") -> bool:
        """
        Upload document content to S3.
        
        Args:
            filename: Name of the file (without extension)
            content: Document content
            s3_prefix: S3 prefix/folder (default: documents/)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            s3_key = f"{s3_prefix}{filename}.txt"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content.encode('utf-8'),
                ContentType='text/plain',
                Metadata={
                    'source': 'sample-data-upload',
                    'filename': f"{filename}.txt"
                }
            )
            
            print(f"✓ Uploaded document: s3://{self.bucket_name}/{s3_key}")
            return True
            
        except Exception as e:
            print(f"✗ Error uploading document {filename}.txt: {str(e)}")
            return False
    
    def upload_metadata(self, filename: str, metadata: Dict[str, Any], s3_prefix: str = "documents/") -> bool:
        """
        Upload metadata JSON to S3.
        
        Args:
            filename: Name of the file (without extension)
            metadata: Metadata dictionary
            s3_prefix: S3 prefix/folder (default: documents/)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            s3_key = f"{s3_prefix}{filename}.txt.metadata.json"
            metadata_json = json.dumps(metadata, indent=2, ensure_ascii=False)
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=metadata_json.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'source': 'sample-data-upload',
                    'filename': f"{filename}.txt.metadata.json"
                }
            )
            
            print(f"✓ Uploaded metadata: s3://{self.bucket_name}/{s3_key}")
            return True
            
        except Exception as e:
            print(f"✗ Error uploading metadata {filename}.txt.metadata.json: {str(e)}")
            return False
    
    def upload_sample_data(self, csv_file_path: str, s3_prefix: str = "documents/") -> Dict[str, int]:
        """
        Upload all sample data from CSV to S3.
        
        Args:
            csv_file_path: Path to the CSV file
            s3_prefix: S3 prefix/folder (default: documents/)
            
        Returns:
            Dictionary with upload statistics
        """
        print(f"Starting upload to S3 bucket: {self.bucket_name}")
        print(f"S3 prefix: {s3_prefix}")
        print("-" * 60)
        
        # Read CSV data
        data = self.read_csv_data(csv_file_path)
        
        stats = {
            'total_rows': len(data),
            'successful_documents': 0,
            'successful_metadata': 0,
            'failed_uploads': 0
        }
        
        # Process each row
        for i, row in enumerate(data, 1):
            print(f"\nProcessing row {i}/{len(data)}:")
            
            # Check if document column exists
            if 'document' not in row or not row['document']:
                print(f"✗ Skipping row {i}: No document content found")
                stats['failed_uploads'] += 1
                continue
            
            # Generate random filename
            filename = self.generate_filename()
            
            # Extract document content
            document_content = row['document'].strip()
            
            # Create metadata (exclude document column)
            metadata = self.create_metadata(row, exclude_columns=['document'])
            
            print(f"  Filename: {filename}")
            print(f"  Document length: {len(document_content)} characters")
            print(f"  Metadata fields: {list(metadata.keys())}")
            
            # Upload document
            doc_success = self.upload_document(filename, document_content, s3_prefix)
            if doc_success:
                stats['successful_documents'] += 1
            
            # Upload metadata
            meta_success = self.upload_metadata(filename, metadata, s3_prefix)
            if meta_success:
                stats['successful_metadata'] += 1
            
            # Track failures
            if not (doc_success and meta_success):
                stats['failed_uploads'] += 1
        
        return stats
    
    def print_upload_summary(self, stats: Dict[str, int]):
        """
        Print upload summary statistics.
        
        Args:
            stats: Dictionary with upload statistics
        """
        print("\n" + "=" * 60)
        print("UPLOAD SUMMARY")
        print("=" * 60)
        print(f"Total rows processed: {stats['total_rows']}")
        print(f"Successful documents: {stats['successful_documents']}")
        print(f"Successful metadata files: {stats['successful_metadata']}")
        print(f"Failed uploads: {stats['failed_uploads']}")
        
        success_rate = ((stats['successful_documents'] + stats['successful_metadata']) / 
                       (stats['total_rows'] * 2) * 100) if stats['total_rows'] > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
        
        if stats['failed_uploads'] == 0:
            print("\n🎉 All uploads completed successfully!")
        else:
            print(f"\n⚠️  {stats['failed_uploads']} uploads failed. Check the logs above for details.")


def get_bucket_name_from_stack() -> str:
    """
    Get the S3 bucket name from CDK stack outputs.
    
    Returns:
        S3 bucket name
    """
    try:
        # Try to get bucket name from CloudFormation stack outputs
        cf_client = boto3.client('cloudformation', region_name='us-west-2')
        
        response = cf_client.describe_stacks(StackName='AuroraVectorKbStack')
        
        for stack in response['Stacks']:
            for output in stack.get('Outputs', []):
                if output['OutputKey'] == 'KnowledgeBaseBucketName':
                    return output['OutputValue']
        
        raise ValueError("KnowledgeBaseBucketName output not found in stack")
        
    except Exception as e:
        print(f"Error getting bucket name from stack: {str(e)}")
        print("Please provide the bucket name manually using --bucket-name parameter")
        sys.exit(1)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Upload sample data from CSV to S3 bucket",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect bucket name from CDK stack
  python validation/scripts/upload_sample_data.py
  
  # Specify bucket name manually
  python validation/scripts/upload_sample_data.py --bucket-name my-bucket
  
  # Use custom CSV file and S3 prefix
  python validation/scripts/upload_sample_data.py --csv-file custom.csv --s3-prefix "test-data/"
        """
    )
    
    parser.add_argument(
        '--csv-file',
        default='validation/sample_data/samples-web-crawl.csv',
        help='Path to CSV file (default: validation/sample_data/samples-web-crawl.csv)'
    )
    
    parser.add_argument(
        '--bucket-name',
        help='S3 bucket name (auto-detected from CDK stack if not provided)'
    )
    
    parser.add_argument(
        '--s3-prefix',
        default='documents/',
        help='S3 prefix/folder for uploads (default: documents/)'
    )
    
    parser.add_argument(
        '--region',
        default='us-west-2',
        help='AWS region (default: us-west-2)'
    )
    
    args = parser.parse_args()
    
    # Validate CSV file exists
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file not found at {args.csv_file}")
        print("Please create the CSV file or specify a different path with --csv-file")
        sys.exit(1)
    
    # Get bucket name
    bucket_name = args.bucket_name
    if not bucket_name:
        print("Auto-detecting S3 bucket name from CDK stack...")
        bucket_name = get_bucket_name_from_stack()
        print(f"Found bucket: {bucket_name}")
    
    # Create uploader and process data
    uploader = SampleDataUploader(bucket_name, args.region)
    
    try:
        stats = uploader.upload_sample_data(args.csv_file, args.s3_prefix)
        uploader.print_upload_summary(stats)
        
    except KeyboardInterrupt:
        print("\n\nUpload interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()