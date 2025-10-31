#!/usr/bin/env python3
"""
Vector Retrieval Lambda Test Script

This script tests the vector retrieval Lambda function with different search types:
- Content similarity search
- Metadata similarity search  
- Hybrid similarity search
- Filter and search

Usage:
    python validation/scripts/test_retrieval_lambda.py --search-type content_similarity --query "machine learning"
"""

import json
import boto3
import argparse
import sys
from typing import Dict, Any, Optional


class RetrievalLambdaTester:
    """Handles testing the vector retrieval Lambda function."""
    
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
        Get the retrieval Lambda function name from CDK stack outputs.
        
        Returns:
            Lambda function name
        """
        try:
            response = self.cf_client.describe_stacks(StackName='AuroraVectorKbStack')
            
            for stack in response['Stacks']:
                for output in stack.get('Outputs', []):
                    if output['OutputKey'] == 'RetrievalLambdaFunctionName':
                        return output['OutputValue']
            
            raise ValueError("RetrievalLambdaFunctionName output not found in stack")
            
        except Exception as e:
            print(f"Error getting Lambda function name from stack: {str(e)}")
            print("Please provide the function name manually using --function-name parameter")
            sys.exit(1)
    
    def create_test_payload(self, search_type: str, **kwargs) -> Dict[str, Any]:
        """
        Create test payload for the retrieval Lambda function.
        
        Args:
            search_type: Type of search to perform
            **kwargs: Additional parameters based on search type
            
        Returns:
            Test payload dictionary
        """
        payload = {
            "search_type": search_type,
            "k": kwargs.get('k', 10)
        }
        
        if search_type == 'content_similarity':
            payload["query"] = kwargs.get('query', 'machine learning algorithms')
            
        elif search_type == 'metadata_similarity':
            payload["metadata_query"] = kwargs.get('metadata_query', 'technical documentation')
            
        elif search_type == 'hybrid_similarity':
            payload.update({
                "query": kwargs.get('query', 'machine learning algorithms'),
                "metadata_query": kwargs.get('metadata_query', 'technical documentation'),
                "content_weight": kwargs.get('content_weight', 0.7),
                "metadata_weight": kwargs.get('metadata_weight', 0.3)
            })
            
        elif search_type == 'filter_and_search':
            payload.update({
                "query": kwargs.get('query', 'machine learning algorithms'),
                "filter_type": kwargs.get('filter_type', 'category'),
                "filter_value": kwargs.get('filter_value', 'technical')
            })
        
        return payload
    
    def invoke_retrieval_lambda(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke the retrieval Lambda function.
        
        Args:
            function_name: Name of the Lambda function
            payload: Payload to send to the function
            
        Returns:
            Lambda response
        """
        try:
            print(f"Invoking Lambda function: {function_name}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            print("-" * 60)
            
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
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
            payload = response['Payload']
            
            # Print summary information
            if payload.get('status') == 'success':
                print(f"✅ Status: {payload['status']}")
                print(f"🔍 Search Type: {payload['search_type']}")
                print(f"📊 Total Results: {payload['total_results']}")
                print(f"⏱️  Execution Time: {payload['execution_time_ms']}ms")
                
                # Print results
                if payload.get('results'):
                    print(f"\n📋 Results:")
                    for i, result in enumerate(payload['results'][:3], 1):  # Show first 3 results
                        print(f"\n  Result {i}:")
                        print(f"    ID: {result['id']}")
                        print(f"    Document: {result['document'][:100]}...")
                        print(f"    Source: {result['source_s3_uri']}")
                        print(f"    Similarity Score: {result['similarity_score']:.4f}")
                        
                        # Print additional scores if available
                        if 'content_score' in result:
                            print(f"    Content Score: {result['content_score']:.4f}")
                        if 'metadata_score' in result:
                            print(f"    Metadata Score: {result['metadata_score']:.4f}")
                        if 'filter_score' in result:
                            print(f"    Filter Score: {result['filter_score']:.4f}")
                    
                    if len(payload['results']) > 3:
                        print(f"\n  ... and {len(payload['results']) - 3} more results")
                        
            else:
                print(f"❌ Status: {payload['status']}")
                print(f"Error Type: {payload.get('error_type', 'unknown')}")
                print(f"Message: {payload.get('message', 'No error message')}")
                
        else:
            print("No payload returned")
    
    def run_test(self, search_type: str, function_name: Optional[str] = None, **kwargs) -> bool:
        """
        Run the retrieval Lambda test.
        
        Args:
            search_type: Type of search to perform
            function_name: Lambda function name (auto-detected if not provided)
            **kwargs: Additional search parameters
            
        Returns:
            True if test was successful, False otherwise
        """
        try:
            # Get function name if not provided
            if not function_name:
                print("Auto-detecting retrieval Lambda function name from CDK stack...")
                function_name = self.get_lambda_function_name()
                print(f"Found function: {function_name}")
            
            # Create test payload
            payload = self.create_test_payload(search_type, **kwargs)
            
            # Invoke Lambda
            response = self.invoke_retrieval_lambda(function_name, payload)
            
            # Print response
            self.print_response(response)
            
            # Check if successful
            success = (response['StatusCode'] == 200 and 
                      response.get('Payload', {}).get('status') == 'success')
            
            if success:
                print(f"\n🎉 {search_type} test completed successfully!")
                total_results = response.get('Payload', {}).get('total_results', 0)
                execution_time = response.get('Payload', {}).get('execution_time_ms', 0)
                print(f"Found {total_results} results in {execution_time}ms")
            else:
                print(f"\n❌ {search_type} test failed!")
                if 'Payload' in response and 'message' in response['Payload']:
                    print(f"Error: {response['Payload']['message']}")
            
            return success
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")
            return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test the vector retrieval Lambda function",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Content similarity search
  python validation/scripts/test_retrieval_lambda.py --search-type content_similarity --query "machine learning"
  
  # Metadata similarity search
  python validation/scripts/test_retrieval_lambda.py --search-type metadata_similarity --metadata-query "technical documentation"
  
  # Hybrid similarity search
  python validation/scripts/test_retrieval_lambda.py --search-type hybrid_similarity --query "AI algorithms" --metadata-query "research paper"
  
  # Filter and search
  python validation/scripts/test_retrieval_lambda.py --search-type filter_and_search --query "neural networks" --filter-type category --filter-value "machine learning"
        """
    )
    
    parser.add_argument(
        '--search-type',
        required=True,
        choices=['content_similarity', 'metadata_similarity', 'hybrid_similarity', 'filter_and_search'],
        help='Type of search to perform'
    )
    
    parser.add_argument(
        '--function-name',
        help='Retrieval Lambda function name (auto-detected from CDK stack if not provided)'
    )
    
    parser.add_argument(
        '--query',
        help='Content query text (required for content_similarity, hybrid_similarity, filter_and_search)'
    )
    
    parser.add_argument(
        '--metadata-query',
        help='Metadata query text (required for metadata_similarity, hybrid_similarity)'
    )
    
    parser.add_argument(
        '--filter-type',
        choices=['provider', 'category', 'type'],
        help='Filter type for filter_and_search (default: category)'
    )
    
    parser.add_argument(
        '--filter-value',
        help='Filter value for filter_and_search'
    )
    
    parser.add_argument(
        '--content-weight',
        type=float,
        default=0.7,
        help='Content weight for hybrid_similarity (default: 0.7)'
    )
    
    parser.add_argument(
        '--metadata-weight',
        type=float,
        default=0.3,
        help='Metadata weight for hybrid_similarity (default: 0.3)'
    )
    
    parser.add_argument(
        '--k',
        type=int,
        default=10,
        help='Number of results to return (default: 10)'
    )
    
    parser.add_argument(
        '--region',
        default='us-west-2',
        help='AWS region (default: us-west-2)'
    )
    
    args = parser.parse_args()
    
    # Validate required parameters based on search type
    if args.search_type in ['content_similarity', 'hybrid_similarity', 'filter_and_search'] and not args.query:
        print(f"Error: --query is required for {args.search_type}")
        sys.exit(1)
    
    if args.search_type in ['metadata_similarity', 'hybrid_similarity'] and not args.metadata_query:
        print(f"Error: --metadata-query is required for {args.search_type}")
        sys.exit(1)
    
    if args.search_type == 'filter_and_search':
        if not args.filter_type:
            args.filter_type = 'category'
        if not args.filter_value:
            print("Error: --filter-value is required for filter_and_search")
            sys.exit(1)
    
    # Create tester and run test
    tester = RetrievalLambdaTester(args.region)
    
    try:
        success = tester.run_test(
            search_type=args.search_type,
            function_name=args.function_name,
            query=args.query,
            metadata_query=args.metadata_query,
            filter_type=args.filter_type,
            filter_value=args.filter_value,
            content_weight=args.content_weight,
            metadata_weight=args.metadata_weight,
            k=args.k
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