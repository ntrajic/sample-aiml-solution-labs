# Aurora Vector Knowledge Base

A scalable vector knowledge base system built on Amazon RDS Aurora PostgreSQL with pgvector extension, featuring multi-embedding support, automated document ingestion, and secure retrieval through Amazon Bedrock AgentCore Gateway.

## 🤖 Built with Kiro AI

This project was developed using **Kiro's Spec Mode**, an AI-powered development workflow that transforms ideas into production-ready code through structured specification-driven development.

### How This Code Was Created

1. **Requirements Gathering**: Started with a rough idea for a vector knowledge base system
2. **Specification Development**: Used Kiro to create detailed requirements following EARS (Easy Approach to Requirements Syntax) patterns
3. **Design Documentation**: Generated comprehensive architecture and implementation design
4. **Task Planning**: Created an actionable implementation plan with incremental development tasks
5. **Code Generation**: Kiro implemented each task systematically, building the complete system

### Spec Documentation

The complete development specification is available in the `.kiro/specs/aurora-vector-kb/` directory:

- **[📋 Requirements](/.kiro/specs/aurora-vector-kb/requirements.md)**: Detailed functional requirements with user stories and acceptance criteria
- **[🏗️ Design](/.kiro/specs/aurora-vector-kb/design.md)**: Comprehensive system architecture, API interfaces, and implementation details  
- **[✅ Tasks](/.kiro/specs/aurora-vector-kb/tasks.md)**: Complete implementation plan with task breakdown and completion status

These documents provide insight into the systematic approach used to build this system and can serve as a reference for understanding the codebase architecture and design decisions.

### Key Benefits of Spec-Driven Development

- **Systematic Approach**: Each feature was planned, designed, and implemented methodically
- **Documentation-First**: Requirements and design were established before coding began
- **Incremental Development**: Complex features were broken down into manageable tasks
- **Quality Assurance**: Each component was validated against requirements during implementation
- **Maintainable Code**: Well-structured codebase with clear separation of concerns

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
4. Prepare Lambda layer dependencies:
   
   **Linux/macOS:**
   ```bash
   ./scripts/prepare-lambda-layer.sh
   ```
   
   **Windows:**
   ```cmd
   scripts\prepare-lambda-layer.bat
   ```
   
   This script installs the required Python packages (psycopg2-binary, tiktoken, boto3) for the Lambda layer that enables PostgreSQL connectivity. The dependencies are installed locally and excluded from version control.

## Deployment

### Prerequisites Check

Before deploying, ensure you have:
- AWS CLI configured with appropriate permissions
- Python 3.11+ installed
- Lambda layer dependencies prepared (see Installation step 4)

### Deploy Steps

1. Bootstrap CDK (first time only):
   ```bash
   cdk bootstrap
   ```

2. Prepare Lambda layer (if not done during installation):
   
   **Linux/macOS:**
   ```bash
   ./scripts/prepare-lambda-layer.sh
   ```
   
   **Windows:**
   ```cmd
   scripts\prepare-lambda-layer.bat
   ```

3. Deploy the stack:
   ```bash
   cdk deploy
   ```

4. To destroy the stack:
   ```bash
   cdk destroy
   ```

   **Note**: All resources are configured with `RemovalPolicy.DESTROY` for development environments, ensuring complete cleanup when the stack is destroyed. For production deployments, consider changing removal policies for critical resources like Cognito User Pools and Secrets Manager secrets to `RemovalPolicy.RETAIN`.

### Troubleshooting Deployment

**Lambda Layer Issues:**
- If you get layer-related errors, run the layer preparation script to reinstall dependencies:
  - Linux/macOS: `./scripts/prepare-lambda-layer.sh`
  - Windows: `scripts\prepare-lambda-layer.bat`
- Ensure you have pip3 installed and internet connectivity for package downloads
- The layer dependencies are not included in version control and must be prepared locally

**Permission Issues:**
- Verify your AWS credentials have sufficient permissions for creating VPC, RDS, Lambda, and other resources
- Check that your AWS account has service limits available for the resources being created

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

## Testing

For comprehensive testing instructions, validation scripts, and sample data, see **[📋 Testing Guide](/validation/README.md)**.

The validation directory includes:
- **Test Scripts**: Automated testing for all Lambda functions
- **Sample Data**: Example documents and metadata for testing
- **Vector Search Testing**: Scripts to test all four search modes (content similarity, metadata similarity, hybrid similarity, filter and search)
- **Upload Utilities**: Tools for uploading test documents to S3
- **Usage Examples**: Complete examples demonstrating system capabilities

## Development

This project uses:
- AWS CDK for infrastructure as code
- Python for Lambda functions
- PostgreSQL with pgvector for vector storage
- Amazon Titan Text Embedding v2 for embeddings

## License

This project is licensed under the MIT License.