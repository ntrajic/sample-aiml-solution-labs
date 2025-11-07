from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands_tools import http_request, use_aws, file_write
import os
import boto3
from botocore.exceptions import ClientError


def get_s3_bucket_from_stack(stack_name: str = "AuroraVectorKbStack", region: str = "us-west-2") -> str:
    """
    Get the S3 bucket name from CloudFormation stack output.
    
    Args:
        stack_name: Name of the CloudFormation stack
        region: AWS region
        
    Returns:
        S3 bucket name
        
    Raises:
        ValueError: If bucket name not found in stack outputs
    """
    try:
        cf_client = boto3.client('cloudformation', region_name=region)
        response = cf_client.describe_stacks(StackName=stack_name)
        
        for stack in response['Stacks']:
            for output in stack.get('Outputs', []):
                if output['OutputKey'] == 'KnowledgeBaseBucketName':
                    bucket_name = output['OutputValue']
                    print(f"✅ Found S3 bucket from stack: {bucket_name}")
                    return bucket_name
        
        raise ValueError(f"KnowledgeBaseBucketName output not found in stack {stack_name}")
        
    except ClientError as e:
        raise ValueError(f"Error accessing CloudFormation stack {stack_name}: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error getting S3 bucket name: {str(e)}")


# Get S3 bucket name from CloudFormation stack
try:
    S3_BUCKET_NAME = get_s3_bucket_from_stack()
except Exception as e:
    print(f"⚠️  Warning: Could not get S3 bucket from stack: {str(e)}")
    print("Using environment variable fallback...")
    S3_BUCKET_NAME = os.environ.get("MULTI_VECTOR_KB_S3_BUCKET", "default-bucket")


SYSTEM_PROMPT = f"""You are an AWS Documentation Agent that reads AWS blog documents and documentation using the MCP server tools.

Your tasks:
1. Use the read_documentation tool to fetch content from AWS URLs
2. Store documents in S3 bucket: {S3_BUCKET_NAME}
3. Save documents as .txt files in the 'documents/' prefix
4. Create companion .metadata.json files with inferred metadata

For each document, analyze the content and create metadata in this format:
```json
{{
    "category": ["comma", "separated", "topics"],
    "industry": "if applicable: Gaming, Music, Sports, Healthcare, Finance, etc."
}}
```

Sample categories: GenAI, Machine Learning, Analytics, Compute, Storage, Security, Networking, Database
Sample industries: Gaming, Music, Sports, Healthcare, Finance, Retail, Manufacturing

Always create both the .txt file and .txt.metadata.json file for each document processed.
"""

agent = Agent(tools=[http_request, use_aws, file_write], system_prompt=SYSTEM_PROMPT)

urls = [
    "https://aws.amazon.com/blogs/gametech/designing-compliant-and-secure-betting-and-gaming-applications-on-aws/"

# The agent() call returns an AgentResult object directly
agent_result = agent(str(urls))