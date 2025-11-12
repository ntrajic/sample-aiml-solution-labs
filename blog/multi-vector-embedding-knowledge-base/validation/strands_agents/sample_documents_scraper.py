from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.models import BedrockModel
from strands_tools import http_request, use_aws, file_write
import os
import boto3
from botocore.exceptions import ClientError

os.environ["BYPASS_TOOL_CONSENT"] = "true"

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
model = BedrockModel(model_id="global.anthropic.claude-haiku-4-5-20251001-v1:0")
agent = Agent(tools=[http_request, use_aws, file_write], model = model , system_prompt=SYSTEM_PROMPT)

urls = [
    "https://aws.amazon.com/blogs/machine-learning/how-amazon-music-uses-sagemaker-with-nvidia-to-optimize-ml-training-and-inference-performance-and-cost/",
    "https://aws.amazon.com/blogs/machine-learning/enhance-sports-narratives-with-natural-language-generation-using-amazon-sagemaker/",
    "https://aws.amazon.com/blogs/gametech/revolutionizing-games-with-small-language-model-ai-companions/",
    "https://aws.amazon.com/blogs/machine-learning/build-a-scalable-ai-video-generator-using-amazon-sagemaker-ai-and-cogvideox/",
    "https://aws.amazon.com/blogs/industries/generative-ai-in-manufacturing/",
    "https://aws.amazon.com/blogs/machine-learning/impel-enhances-automotive-dealership-customer-experience-with-fine-tuned-llms-on-amazon-sagemaker/",
    "https://aws.amazon.com/blogs/machine-learning/solve-forecasting-challenges-for-the-retail-and-cpg-industry-using-amazon-sagemaker-canvas/",
    "https://aws.amazon.com/blogs/machine-learning/fraud-detection-empowered-by-federated-learning-with-the-flower-framework-on-amazon-sagemaker-ai/",
    "https://aws.amazon.com/blogs/supply-chain/aws-offerings-for-visibility-and-on-time-arrival-of-maintenance-spares-for-mining-and-energy/",
    "https://aws.amazon.com/blogs/machine-learning/how-ifood-built-a-platform-to-run-hundreds-of-machine-learning-models-with-amazon-sagemaker-inference/"
]


# The agent() call returns an AgentResult object directly
agent_result = agent(str(urls))