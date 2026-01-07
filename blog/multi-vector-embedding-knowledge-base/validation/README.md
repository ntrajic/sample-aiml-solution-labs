# Aurora Vector KB - Testing and Validation Guide

This directory contains tools and scripts for testing the Aurora Vector Knowledge Base system. You can collect sample documents from AWS blogs, upload them to S3, and test the vector search capabilities.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Step-by-Step Testing Guide](#step-by-step-testing-guide)
- [Testing Scripts](#testing-scripts)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before testing, ensure you have:

1. **Deployed the Aurora Vector KB stack** (see main [README.md](../README.md))
2. **Python 3.11+** installed
3. **AWS CLI** configured with appropriate credentials
4. **Strands Agents** installed (for web scraping)
5. **Stack outputs** available from your CDK deployment

## Installation

### Install Required Dependencies

The validation scripts only require two packages:

```bash
# Install boto3 for AWS SDK
pip install boto3

# Install Strands Agents for web scraping
pip install strands-agents strands-agents-tools
```

**Dependencies:**
- `boto3` - AWS SDK for Python (required for all scripts)
- `strands-agents` - Strands AI agent framework (required for web scraper)
- `strands-agents-tools` - Strands tools library (required for web scraper)

**Note**: Strands Agents requires Python 3.11 or later.

### Navigate to Validation Directory

All validation scripts should be run from the `validation` directory:

```bash
cd validation
```

### Verify AWS Configuration

Ensure your AWS credentials are configured:

```bash
aws sts get-caller-identity
```

This should return your AWS account information.

## Quick Start

Here's the fastest way to test the system:

```bash
# 1. Install dependencies
pip install boto3 strands-agents strands-agents-tools

# 2. Navigate to validation directory
cd validation

# 3. Collect sample documents from AWS blogs
python scripts/sample_documents_scraper.py

# 4. Trigger document ingestion (sync S3 to vector store)
python scripts/test_sync_lambda.py

# 5. Wait a few moments for ingestion to complete, then run search examples
bash scripts/run_search_examples.sh
```

## Step-by-Step Testing Guide

### Step 1: Collect Sample Documents

The `scripts/sample_documents_scraper.py` script uses Strands Agents to:
- Scrape content from AWS blog posts
- Extract text and metadata
- Create `.txt` files with content
- Create `.metadata.json` files with category and industry information
- Upload both to your S3 bucket

**Run the scraper:**

```bash
python scripts/sample_documents_scraper.py
```

**What it does:**
1. Automatically detects your S3 bucket from CloudFormation stack outputs
2. Scrapes AWS blog posts about AI/ML, serverless, and databases
3. Extracts clean text content
4. Generates metadata with:
   - `category`: Topic categories (e.g., "AI/ML", "Serverless")
   - `industry`: Industry classification (e.g., "Technology", "Cloud Computing")
5. Uploads both `.txt` and `.metadata.json` files to `s3://your-bucket/documents/`

**Important:** After running this script, you must run the sync lambda (Step 2) to process the documents into the vector store.

**Expected output:**
```
✅ Found S3 bucket from stack: auroravectorkbstack-s3storage...
📄 Processing: AWS Blog Post Title
✅ Uploaded: documents/aws-blog-post-1.txt
✅ Uploaded: documents/aws-blog-post-1.txt.metadata.json
...
```

### Step 2: Trigger Document Ingestion

After the Strands agent uploads documents to S3, you need to trigger the sync lambda to process them into the vector store:

```bash
python scripts/test_sync_lambda.py
```

**What this does:**
1. Lists all documents in the S3 bucket
2. Queues them for ingestion via SQS
3. Lambda functions process the documents:
   - Download from S3
   - Extract text and metadata
   - Generate embeddings
   - Store in Aurora PostgreSQL vector store
4. Displays the number of files queued

**Expected output:**
```
🔍 Retrieving database connection details...
✅ Connected to database: vector_kb
Auto-detecting sync Lambda function name from CDK stack...
Found function: AuroraVectorKbStack-SyncLambdaSyncLambdaFunction4B-...
Using default bucket: auroravectorkbstack-s3storage...

Invoking Lambda function: AuroraVectorKbStack-SyncLambda...
Payload: {"s3_prefix": "documents/"}
...
🎉 Sync Lambda test completed successfully!
Files queued for ingestion: 15
```

**Wait for processing:** The ingestion process takes a few moments. You can check the CloudWatch logs if needed:

```bash
# Check ingestion lambda logs (optional)
aws logs tail /aws/lambda/$(aws cloudformation describe-stacks \
  --stack-name AuroraVectorKbStack \
  --query 'Stacks[0].Outputs[?OutputKey==`IngestionLambdaFunctionName`].OutputValue' \
  --output text) \
  --since 5m
```

### Step 3: Test Vector Search

Once documents are ingested, test the search capabilities:

#### Option A: Run All Search Examples (Recommended)

```bash
bash scripts/run_search_examples.sh
```

This script runs all four search modes:
1. **Content Similarity Search** - Find documents similar to a query
2. **Metadata Similarity Search** - Search based on metadata
3. **Hybrid Search** - Combine content and metadata search
4. **Filter and Search** - Filter by category/industry, then search

#### Option B: Run Individual Tests

**Test content similarity search:**
```bash
python scripts/test_vector_search.py \
  --search-type content_similarity \
  --query "machine learning on AWS" \
  --k 5
```

**Test filter and search:**
```bash
python scripts/test_vector_search.py \
  --search-type filter_and_search \
  --query "serverless architecture" \
  --filter-type category \
  --filter-value "Serverless" \
  --k 3
```

**Test hybrid search:**
```bash
python scripts/test_vector_search.py \
  --search-type hybrid_similarity \
  --query "AI and machine learning" \
  --metadata-query "AWS services for AI" \
  --content-weight 0.7 \
  --metadata-weight 0.3 \
  --k 5
```

### Step 4: Verify Results

The search results will show:
- **Document ID**: Unique identifier for each chunk
- **Content**: Text snippet from the document
- **Similarity Score**: Relevance score (0-1, higher is better)
- **Metadata**: Category, industry, and other metadata
- **Source**: S3 URI of the original document

**Example output:**
```
Search Results (5 documents found):
================================================================================

Result 1:
  ID: 550e8400-e29b-41d4-a716-446655440000
  Score: 0.8523
  Content: Amazon Bedrock is a fully managed service that offers...
  Metadata:
     Category: AI/ML, Generative AI
     Industry: Technology
  Source: s3://bucket/documents/bedrock-announcement.txt

Result 2:
  ID: 550e8400-e29b-41d4-a716-446655440001
  Score: 0.7891
  Content: AWS Lambda enables you to run code without...
  ...
```

## Testing Scripts

### `scripts/sample_documents_scraper.py`

**Purpose**: Collect sample documents from AWS blogs and upload to S3

**Features**:
- Automatic S3 bucket detection from CloudFormation
- Web scraping with Strands Agents
- Metadata generation
- Batch upload to S3

**Usage**:
```bash
python scripts/sample_documents_scraper.py
```

**Important Note**: This script only uploads files to S3. You must run `test_sync_lambda.py` afterwards to trigger ingestion into the vector store.

**Environment Variables** (optional):
- `MULTI_VECTOR_KB_S3_BUCKET`: Override S3 bucket name
- `AWS_REGION`: AWS region (default: us-west-2)

### `scripts/test_sync_lambda.py`

**Purpose**: Trigger the sync lambda to process S3 documents into the vector store

**When to use**: Run this after uploading documents to S3 (either via the scraper or manually) to trigger ingestion.

**What it does**:
1. Invokes the sync lambda function
2. Lambda lists all documents in S3
3. Queues them for processing via SQS
4. Ingestion lambdas process documents and store vectors in Aurora

**Usage**:
```bash
python scripts/test_sync_lambda.py [--function-name FUNCTION_NAME] [--s3-prefix PREFIX]
```

**Options**:
- `--function-name`: Lambda function name (auto-detected if not provided)
- `--s3-prefix`: S3 prefix to sync (default: documents/)
- `--region`: AWS region (default: us-west-2)

### `scripts/test_vector_search.py`

**Purpose**: Test vector search with different search modes

**Usage**:
```bash
python scripts/test_vector_search.py --search-type TYPE --query "search query" [OPTIONS]
```

**Search Types**:
- `content_similarity`: Search by document content
- `metadata_similarity`: Search by metadata
- `hybrid_similarity`: Combined content and metadata search
- `filter_and_search`: Filter by field, then search

**Common Options**:
- `--query`: Search query text
- `--k`: Number of results to return (default: 5)
- `--region`: AWS region (default: us-west-2)

**Filter and Search Options**:
- `--filter-type`: Field to filter by (category or industry)
- `--filter-value`: Value to filter for

**Hybrid Search Options**:
- `--metadata-query`: Metadata search query
- `--content-weight`: Weight for content similarity (default: 0.7)
- `--metadata-weight`: Weight for metadata similarity (default: 0.3)

### `scripts/run_search_examples.sh`

**Purpose**: Run all search examples in sequence

**Usage**:
```bash
bash scripts/run_search_examples.sh
```

This script demonstrates all four search modes with example queries.

### `scripts/upload_sample_data.py`

**Purpose**: Upload custom documents and metadata to S3

**Usage**:
```bash
python scripts/upload_sample_data.py --file document.txt --category "AI/ML" --industry "Technology"
```

**Options**:
- `--file`: Path to document file
- `--category`: Document category
- `--industry`: Document industry
- `--bucket`: S3 bucket name (auto-detected if not provided)

## Troubleshooting

### Issue: "S3 bucket not found"

**Solution**: Ensure the CDK stack is deployed and outputs are available:
```bash
aws cloudformation describe-stacks --stack-name AuroraVectorKbStack \
  --query 'Stacks[0].Outputs[?OutputKey==`KnowledgeBaseBucketName`].OutputValue' \
  --output text
```

### Issue: "No search results returned"

**Possible causes**:
1. Documents uploaded to S3 but sync lambda not run yet
2. Documents still being processed (ingestion in progress)
3. Search query doesn't match document content
4. Database table is empty

**Solution**:
1. Ensure you ran the sync lambda after uploading documents:
   ```bash
   python scripts/test_sync_lambda.py
   ```

2. Wait a few moments for ingestion to complete

3. Check CloudWatch logs to verify ingestion succeeded:
   ```bash
   aws logs tail /aws/lambda/$(aws cloudformation describe-stacks \
     --stack-name AuroraVectorKbStack \
     --query 'Stacks[0].Outputs[?OutputKey==`IngestionLambdaFunctionName`].OutputValue' \
     --output text) \
     --since 10m
   ```

### Issue: "Lambda function not found"

**Solution**: The function name may have changed. List all Lambda functions:
```bash
aws lambda list-functions --query 'Functions[?contains(FunctionName, `AuroraVectorKb`)].FunctionName'
```

### Issue: "Strands Agents import error"

**Solution**: Ensure Strands Agents is installed:
```bash
pip install --upgrade strands-agents strands-agents-tools
```

Strands Agents requires Python 3.11+. Check your Python version:
```bash
python --version
```

### Issue: "Permission denied" errors

**Solution**: Verify your AWS credentials have the necessary permissions:
- S3: `s3:PutObject`, `s3:GetObject`, `s3:ListBucket`
- Lambda: `lambda:InvokeFunction`
- CloudFormation: `cloudformation:DescribeStacks`
- SQS: `sqs:SendMessage`, `sqs:GetQueueAttributes`

### Issue: "Metadata validation error"

**Solution**: Ensure metadata files have the required fields:
```json
{
  "category": "AI/ML",
  "industry": "Technology"
}
```

Both `category` and `industry` are required fields.

## Advanced Testing

### Custom Document Upload

Create your own test documents:

1. **Create a text file** (`my-document.txt`):
```
Your document content here...
```

2. **Create metadata file** (`my-document.txt.metadata.json`):
```json
{
  "category": "Custom Category",
  "industry": "Custom Industry",
  "author": "Your Name",
  "date": "2024-01-01"
}
```

3. **Upload to S3**:
```bash
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name AuroraVectorKbStack \
  --query 'Stacks[0].Outputs[?OutputKey==`KnowledgeBaseBucketName`].OutputValue' \
  --output text)

aws s3 cp my-document.txt s3://$BUCKET/documents/ --content-type "text/plain"
aws s3 cp my-document.txt.metadata.json s3://$BUCKET/documents/ --content-type "application/json"
```

### Performance Testing

Test search performance with different parameters:

```bash
# Test with different k values
for k in 5 10 20; do
  echo "Testing with k=$k"
  time python scripts/test_vector_search.py \
    --search-type content_similarity \
    --query "AWS services" \
    --k $k
done
```

### Batch Testing

Test multiple queries:

```bash
# Create a file with test queries
cat > test_queries.txt << EOF
machine learning on AWS
serverless architecture patterns
database optimization techniques
cloud security best practices
EOF

# Run each query
while read query; do
  echo "Testing: $query"
  python scripts/test_vector_search.py \
    --search-type content_similarity \
    --query "$query" \
    --k 3
  echo "---"
done < test_queries.txt
```

## Next Steps

After successful testing:

1. **Integrate with your application** - Use the retrieval Lambda function in your app
2. **Add more documents** - Upload your own document corpus
3. **Tune search parameters** - Adjust weights and k values for your use case
4. **Monitor performance** - Use CloudWatch to track Lambda execution times
5. **Scale as needed** - Adjust Aurora capacity and Lambda concurrency

## Additional Resources

- [Main README](../README.md) - System overview and deployment guide
- [Design Documentation](../.kiro/specs/aurora-vector-kb/design.md) - Architecture details
- [Requirements](../.kiro/specs/aurora-vector-kb/requirements.md) - System requirements
- [Strands Agents Documentation](https://docs.strands.ai/) - Strands Agents guide

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section above
2. Review CloudWatch logs for Lambda functions
3. Check SQS dead letter queue for failed messages
4. Verify database connectivity and table schema
