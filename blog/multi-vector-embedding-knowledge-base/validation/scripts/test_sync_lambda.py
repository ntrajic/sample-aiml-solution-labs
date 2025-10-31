#!/usr/bin/env python3
"""
Sync Lambda Test Script

This script directly invokes the sync Lambda function using IAM authentication
to test the document synchronization process.

Usage:
    python validation/scripts/test_sync_lambda.py
"""

import json
import boto3
import argparse
import sys
from typing import Dict, Any, Optional


class SyncLambdaTester:
    """Handles testing the sync Lambda function."""
    
    def __init__(self, region: str = 'us-west-2'):
        """
        Initialize the tester.
        
        Args:
            region: AWS region (default: us-west-2)
        """
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.cf_client = boto3.client('cloudformation', region_name=region)
        
    def get_lambda_function_name(self) -> str:
        """
        Get the sync Lambda function name from CDK stack outputs.
        
        Returns:
            Lambda function name
        """
        try:
            response = self.cf_client.describe_stacks(StackName='AuroraVectorKbStack')
            
            for stack in response['Stacks']:
                for output in stack.get('Outputs', []):
                    if output['OutputKey'] == 'SyncLambdaFunctionName':
                        return output['OutputValue']
            
            raise ValueError("SyncLambdaFunctionName output not found in stack")
            
        except Exception as e:
            print(f"Error getting Lambda function name from stack: {str(e)}")
            print("Please provide the function name manually using --function-name parameter")
            sys.exit(1)
    
    def get_bucket_name(self) -> str:
        """
        Get the S3 bucket name from CDK stack outputs.
        
        Returns:
            S3 bucket name
        """
        try:
            response = self.cf_client.describe_stacks(StackName='AuroraVectorKbStack')
            
            for stack in response['Stacks']:
                for output in stack.get('Outputs', []):
                    if output['OutputKey'] == 'KnowledgeBaseBucketName':
                        return output['OutputValue']
            
            raise ValueError("KnowledgeBaseBucketName output not found in stack")
            
        except Exception as e:
            print(f"Error getting bucket name from stack: {str(e)}")
            return None
    
    def create_test_payload(self, s3_bucket: Optional[str] = None, s3_prefix: str = "documents/") -> Dict[str, Any]:
        """
        Create test payload for the sync Lambda function.
        
        Args:
            s3_bucket: S3 bucket name (optional, will use default if not provided)
            s3_prefix: S3 prefix to sync (default: documents/)
            
        Returns:
            Test payload dictionary
        """
        payload = {
            "s3_prefix": s3_prefix
        }
        
        # Only include s3_bucket if explicitly provided
        # If not provided, Lambda will use the default bucket from environment variable
        if s3_bucket:
            payload["s3_bucket"] = s3_bucket
            
        return payload
    
    def invoke_sync_lambda(self, function_name: str, payload: Dict[str, Any], invocation_type: str = 'RequestResponse') -> Dict[str, Any]:
        """
        Invoke the sync Lambda function.
        
        Args:
            function_name: Name of the Lambda function
            payload: Payload to send to the function
            invocation_type: Type of invocation (RequestResponse or Event)
            
        Returns:
            Lambda response
        """
        try:
            print(f"Invoking Lambda function: {function_name}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            print(f"Invocation type: {invocation_type}")
            print("-" * 60)
            
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType=invocation_type,
                Payload=json.dumps(payload)
            )
            
            # Parse response
            status_code = response['StatusCode']
            
            if 'Payload' in response:
                payload_data = json.loads(response['Payload'].read())
            else:
                payload_data = {}
            
            result = {
                'StatusCode': status_code,
                'ExecutedVersion': response.get('ExecutedVersion'),
                'Payload': payload_data
            }
            
            if 'LogResult' in response:
                # Decode base64 log result if present
                import base64
                log_result = base64.b64decode(response['LogResult']).decode('utf-8')
                result['LogResult'] = log_result
            
            return result
            
        except Exception as e:
            print(f"Error invoking Lambda function: {str(e)}")
            raise
    
    def print_response(self, response: Dict[str, Any]):
        """
        Print Lambda response in a formatted way.
        
        Args:
            response: Lambda response dictionary
        """
        print("LAMBDA RESPONSE")
        print("=" * 60)
        print(f"Status Code: {response['StatusCode']}")
        
        if 'ExecutedVersion' in response:
            print(f"Executed Version: {response['ExecutedVersion']}")
        
        print("\nPayload:")
        if response.get('Payload'):
            print(json.dumps(response['Payload'], indent=2))
        else:
            print("No payload returned")
        
        if 'LogResult' in response:
            print("\nLogs:")
            print(response['LogResult'])
    
    def run_test(self, function_name: Optional[str] = None, s3_bucket: Optional[str] = None, 
                 s3_prefix: str = "documents/", invocation_type: str = 'RequestResponse') -> bool:
        """
        Run the sync Lambda test.
        
        Args:
            function_name: Lambda function name (auto-detected if not provided)
            s3_bucket: S3 bucket name (uses default if not provided)
            s3_prefix: S3 prefix to sync
            invocation_type: Type of invocation
            
        Returns:
            True if test was successful, False otherwise
        """
        try:
            # Get function name if not provided
            if not function_name:
                print("Auto-detecting sync Lambda function name from CDK stack...")
                function_name = self.get_lambda_function_name()
                print(f"Found function: {function_name}")
            
            # Get bucket name for display (but don't require it for the test)
            if not s3_bucket:
                bucket_name = self.get_bucket_name()
                if bucket_name:
                    print(f"Using default bucket: {bucket_name}")
                else:
                    print("Using default bucket from Lambda environment variable")
            
            # Create test payload
            payload = self.create_test_payload(s3_bucket, s3_prefix)
            
            # Invoke Lambda
            response = self.invoke_sync_lambda(function_name, payload, invocation_type)
            
            # Print response
            self.print_response(response)
            
            # Check if successful
            success = (response['StatusCode'] == 200 and 
                      response.get('Payload', {}).get('status') == 'success')
            
            if success:
                print("\n🎉 Sync Lambda test completed successfully!")
                files_queued = response.get('Payload', {}).get('files_queued', 0)
                print(f"Files queued for ingestion: {files_queued}")
            else:
                print("\n❌ Sync Lambda test failed!")
                if 'Payload' in response and 'message' in response['Payload']:
                    print(f"Error: {response['Payload']['message']}")
            
            return success
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")
            return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test the sync Lambda function",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect function name and use default bucket
  python validation/scripts/test_sync_lambda.py
  
  # Specify function name manually
  python validation/scripts/test_sync_lambda.py --function-name my-sync-function
  
  # Test specific S3 location
  python validation/scripts/test_sync_lambda.py --s3-bucket my-bucket --s3-prefix "test-docs/"
  
  # Asynchronous invocation
  python validation/scripts/test_sync_lambda.py --async
        """
    )
    
    parser.add_argument(
        '--function-name',
        help='Sync Lambda function name (auto-detected from CDK stack if not provided)'
    )
    
    parser.add_argument(
        '--s3-bucket',
        help='S3 bucket name (uses Lambda default if not provided)'
    )
    
    parser.add_argument(
        '--s3-prefix',
        default='documents/',
        help='S3 prefix to sync (default: documents/)'
    )
    
    parser.add_argument(
        '--region',
        default='us-west-2',
        help='AWS region (default: us-west-2)'
    )
    
    parser.add_argument(
        '--async',
        dest='async_invoke',
        action='store_true',
        help='Use asynchronous invocation (Event type)'
    )
    
    args = parser.parse_args()
    
    # Determine invocation type
    if args.async_invoke:
        invocation_type = 'Event'
    else:
        invocation_type = 'RequestResponse'
    
    # Create tester and run test
    tester = SyncLambdaTester(args.region)
    
    try:
        success = tester.run_test(
            function_name=args.function_name,
            s3_bucket=args.s3_bucket,
            s3_prefix=args.s3_prefix,
            invocation_type=invocation_type
        )
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()