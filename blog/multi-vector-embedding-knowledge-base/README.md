# Aurora Vector Knowledge Base

A scalable vector knowledge base system built on Amazon RDS Aurora PostgreSQL with pgvector extension, featuring multi-embedding support, automated document ingestion, and secure retrieval through Amazon Bedrock AgentCore Gateway.

## Architecture Overview

This system provides:
- **Vector Storage**: Aurora PostgreSQL with pgvector extension for multi-dimensional embeddings
- **Document Processing**: Automated ingestion from S3 with chunking and metadata extraction
- **Multi-Vector Search**: Support for document, metadata, provider, category, and type embeddings
- **Authentication**: JWT-based security through Amazon Cognito
- **API Integration**: AgentCore Gateway MCP endpoints for seamless integration
- **Scalable Processing**: SQS-based queuing with concurrency controls

## Prerequisites

- Python 3.9 or later
- AWS CLI configured with appropriate permissions
- AWS CDK v2 installed (`npm install -g aws-cdk`)
- Docker (for Lambda function packaging)

## Installation

1. Clone the repository and navigate to the project directory
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Deployment

1. Bootstrap CDK (first time only):
   ```bash
   cdk bootstrap
   ```

2. Deploy the stack:
   ```bash
   cdk deploy
   ```

3. To destroy the stack:
   ```bash
   cdk destroy
   ```

   **Note**: All resources are configured with `RemovalPolicy.DESTROY` for development environments, ensuring complete cleanup when the stack is destroyed. For production deployments, consider changing removal policies for critical resources like Cognito User Pools and Secrets Manager secrets to `RemovalPolicy.RETAIN`.

## Configuration

### CDK Context Configuration

The system uses a `cdk.context.json` file to store deployment configuration and cached AWS resource information. This file contains:

#### Required Configuration
- `account`: Your AWS account ID (e.g., "123456789012")
- `region`: Target AWS region for deployment (e.g., "us-west-2")

#### Cached AWS Information
- `availability-zones`: Cached list of availability zones for the specified account/region
- Other AWS resource metadata cached by CDK during deployment

#### Managing cdk.context.json

**For New Deployments:**
1. Update the `account` field with your AWS account ID
2. Update the `region` field with your target region
3. Remove any cached entries (availability-zones, etc.) - CDK will regenerate them

**Important Notes:**
- This file should be committed to version control for consistent deployments
- CDK automatically updates cached values during `cdk synth` and `cdk deploy`
- If you change regions, delete cached availability-zone entries to force refresh
- The file helps CDK avoid repeated AWS API calls for resource discovery

**Example cdk.context.json:**
```json
{
  "account": "YOUR_ACCOUNT_ID",
  "region": "us-west-2"
}
```

### Additional CDK Context Parameters
The system also supports these optional context parameters:
- `environment`: Environment name (dev/staging/prod)
- Custom parameters can be passed via `cdk deploy -c key=value`

## Components

- **Aurora Database**: PostgreSQL cluster with pgvector extension
- **Lambda Functions**: Sync, ingestion, retrieval, and custom resource handlers
- **SQS Queue**: Job processing with dead letter queue
- **Cognito**: User authentication and JWT token management
- **AgentCore Gateway**: MCP endpoint exposure
- **VPC**: Secure networking with private subnets

## Usage

### Document Metadata Requirements

Each document uploaded to S3 must have a companion metadata file with the same name plus `.metadata.json` extension. For example:
- Document: `example.txt`
- Metadata: `example.txt.metadata.json`

The metadata file must contain JSON with these required fields:
```json
{
  "provider": "AWS",
  "type": "blog", 
  "category": "Agentic AI, GenAI"
}
```

**Field Descriptions:**
- `provider`: Company or organization name (string)
- `type`: Document type (e.g., "blog", "news", "technical_doc", "manual")
- `category`: Topics/categories (string with comma-separated values or array)

Additional custom fields can be included and will be stored with the document.

### System Features

After deployment, the system provides:
1. S3 directory synchronization through the Sync Lambda
2. Automated document processing with metadata-driven categorization
3. Multi-dimensional embedding generation (document, metadata, provider, category, type)
4. Vector similarity search with multiple embedding types
5. Secure API access through JWT authentication
6. Integration with Strands Agents through AgentCore Gateway

## Development

This project uses:
- AWS CDK for infrastructure as code
- Python for Lambda functions
- PostgreSQL with pgvector for vector storage
- Amazon Titan Text Embedding v2 for embeddings

## License

This project is licensed under the MIT License.