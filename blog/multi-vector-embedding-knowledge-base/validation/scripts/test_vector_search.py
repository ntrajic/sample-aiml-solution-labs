#!/usr/bin/env python3
"""
Vector Search Test Script

Simple test script for the vector retrieval Lambda function with explicit argument names:
--query: The text to search for
--mode: The retrieval strategy (content_similarity, metadata_similarity, hybrid_similarity, filter_and_search)
--metadata: Metadata JSON for metadata-based searches or filter parameters

Usage:
    python validation/scripts/test_vector_search.py --query "machine learning" --mode content_similarity --metadata "{}"
    python validation/scripts/test_vector_search.py --query "AI research" --mode metadata_similarity --metadata '{"query": "technical documentation"}'
    python validation/scripts/test_vector_search.py --query "neural networks" --mode hybrid_similarity --metadata '{"metadata_query": "research paper", "content_weight": 0.7, "metadata_weight": 0.3}'
    python validation/scripts/test_vector_search.py --query "deep learning" --mode filter_and_search --metadata '{"filter_type": "category", "filter_value": "machine learning"}'
"""

import json
import boto3
import sys
import argparse
from typing import Dict, Any


def get_lambda_function_name(region: str = 'us-west-2') -> str:
    """Get the retrieval Lambda function name from CDK stack outputs."""
    try:
        cf_client = boto3.client('cloudformation', region_name=region)
        response = cf_client.describe_stacks(StackName='AuroraVectorKbStack')
        
        for stack in response['Stacks']:
            for output in stack.get('Outputs', []):
                if output['OutputKey'] == 'RetrievalLambdaFunctionName':
                    return output['OutputValue']
        
        raise ValueError("RetrievalLambdaFunctionName output not found in stack")
        
    except Exception as e:
        print(f"Error getting Lambda function name: {str(e)}")
        sys.exit(1)


def create_payload(query: str, mode: str, metadata: Dict[str, Any], k: int = 3) -> Dict[str, Any]:
    """
    Create the Lambda payload based on query mode and parameters.
    
    Args:
        query: Query string
        mode: Query mode (search type)
        metadata: Metadata dictionary with additional parameters
        k: Number of results to return
        
    Returns:
        Lambda payload dictionary
    """
    # Base payload - use explicit k parameter, fallback to metadata, then default
    payload = {
        "search_type": mode,
        "k": k if k is not None else metadata.get("k", 3)
    }
    
    # Add parameters based on search type
    if mode == "content_similarity":
        payload["query"] = query
        
    elif mode == "metadata_similarity":
        payload["metadata_query"] = metadata.get("query", query)
        
    elif mode == "hybrid_similarity":
        payload.update({
            "query": query,
            "metadata_query": metadata.get("metadata_query", query),
            "content_weight": metadata.get("content_weight", 0.7),
            "metadata_weight": metadata.get("metadata_weight", 0.3)
        })
        
    elif mode == "filter_and_search":
        payload.update({
            "query": query,
            "filter_type": metadata.get("filter_type", "category"),
            "filter_value": metadata.get("filter_value", "technical")
        })
    else:
        raise ValueError(f"Invalid query mode: {mode}. Must be one of: content_similarity, metadata_similarity, hybrid_similarity, filter_and_search")
    
    return payload


def invoke_lambda(function_name: str, payload: Dict[str, Any], region: str = 'us-west-2') -> Dict[str, Any]:
    """Invoke the retrieval Lambda function."""
    lambda_client = boto3.client('lambda', region_name=region)
    
    try:
        print(f"🔍 Invoking Lambda: {function_name}")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        print("-" * 60)
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse response
        result = json.loads(response['Payload'].read())
        return result
        
    except Exception as e:
        print(f"❌ Error invoking Lambda: {str(e)}")
        sys.exit(1)


def print_results(response: Dict[str, Any]):
    """Print the search results in a formatted way."""
    if response.get('status') == 'success':
        print(f"✅ Status: {response['status']}")
        print(f"🔍 Search Type: {response['search_type']}")
        print(f"📊 Total Results: {response['total_results']}")
        print(f"⏱️  Execution Time: {response['execution_time_ms']}ms")
        
        results = response.get('results', [])
        if results:
            print(f"\n📋 Top Results:")
            for i, result in enumerate(results[:5], 1):  # Show top 5 results
                print(f"\n  🔸 Result {i}:")
                print(f"     ID: {result['id']}")
                print(f"     Document: {result['document'][:150]}...")
                print(f"     Source: {result['source_s3_uri']}")
                print(f"     Similarity Score: {result['similarity_score']:.4f}")
                
                # Print additional scores if available
                if 'content_score' in result:
                    print(f"     Content Score: {result['content_score']:.4f}")
                if 'metadata_score' in result:
                    print(f"     Metadata Score: {result['metadata_score']:.4f}")
                if 'filter_score' in result:
                    print(f"     Filter Score: {result['filter_score']:.4f}")
                
                # Print metadata
                if result.get('metadata'):
                    metadata = result['metadata']
                    print(f"     Category: {metadata.get('category', 'N/A')}")
                    print(f"     Industry: {metadata.get('industry', 'N/A')}")
            
            if len(results) > 5:
                print(f"\n  ... and {len(results) - 5} more results")
        else:
            print("\n📭 No results found")
            
    else:
        print(f"❌ Status: {response['status']}")
        print(f"🚫 Error Type: {response.get('error_type', 'unknown')}")
        print(f"💬 Message: {response.get('message', 'No error message')}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test the vector retrieval Lambda function",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Content similarity search (default k=3)
  python test_vector_search.py --query "machine learning" --mode content_similarity --metadata "{}"
  
  # Content similarity search with custom k
  python test_vector_search.py --query "machine learning" --mode content_similarity --metadata "{}" --k 5
  
  # Metadata similarity search
  python test_vector_search.py --query "AI research" --mode metadata_similarity --metadata '{"query": "technical documentation"}'
  
  # Hybrid similarity search
  python test_vector_search.py --query "neural networks" --mode hybrid_similarity --metadata '{"metadata_query": "research paper", "content_weight": 0.7, "metadata_weight": 0.3}'
  
  # Filter and search with custom k
  python test_vector_search.py --query "deep learning" --mode filter_and_search --metadata '{"filter_type": "category", "filter_value": "machine learning"}' --k 10
        """
    )
    
    parser.add_argument(
        '--query',
        required=True,
        help='The text to search for'
    )
    
    parser.add_argument(
        '--mode',
        required=True,
        choices=['content_similarity', 'metadata_similarity', 'hybrid_similarity', 'filter_and_search'],
        help='The retrieval strategy to use'
    )
    
    parser.add_argument(
        '--metadata',
        required=True,
        help='Metadata JSON string with additional parameters'
    )
    
    parser.add_argument(
        '--k',
        type=int,
        default=3,
        help='Number of results to return (default: 3)'
    )
    
    parser.add_argument(
        '--region',
        default='us-west-2',
        help='AWS region (default: us-west-2)'
    )
    
    args = parser.parse_args()
    
    query = args.query
    mode = args.mode
    metadata_json = args.metadata
    
    # Parse metadata JSON
    try:
        metadata = json.loads(metadata_json)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in metadata parameter: {str(e)}")
        sys.exit(1)
    
    print(f"🚀 Starting Vector Search Test")
    print(f"🔤 Query: {query}")
    print(f"🎯 Mode: {mode}")
    print(f"📝 Metadata: {json.dumps(metadata, indent=2)}")
    print("=" * 60)
    
    try:
        # Get Lambda function name
        function_name = get_lambda_function_name(args.region)
        
        # Create payload
        payload = create_payload(query, mode, metadata, args.k)
        
        # Invoke Lambda
        response = invoke_lambda(function_name, payload, args.region)
        
        # Print results
        print_results(response)
        
        # Exit with appropriate code
        if response.get('status') == 'success':
            print(f"\n🎉 Search completed successfully!")
            sys.exit(0)
        else:
            print(f"\n💥 Search failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()