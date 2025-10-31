# Validation Scripts

This directory contains scripts and sample data for testing the Aurora Vector Knowledge Base system.

## Setup

1. Install dependencies:
   ```bash
   pip install -r validation/requirements.txt
   ```

2. Ensure your AWS credentials are configured:
   ```bash
   aws configure
   ```

## Sample Data Upload

### Quick Start

Upload sample data to the knowledge base S3 bucket (auto-detects bucket from CDK stack):

```bash
python validation/scripts/upload_sample_data.py
```

### Advanced Usage

```bash
# Specify bucket name manually
python validation/scripts/upload_sample_data.py --bucket-name your-bucket-name

# Use custom CSV file
python validation/scripts/upload_sample_data.py --csv-file path/to/your/data.csv

# Upload to specific S3 prefix
python validation/scripts/upload_sample_data.py --s3-prefix "test-documents/"

# Use different AWS region
python validation/scripts/upload_sample_data.py --region us-east-1
```

### CSV Format

The CSV file should have the following structure:

| Column | Description | Required |
|--------|-------------|----------|
| document | The text content to be processed | Yes |
| type | Document type (e.g., "Blog", "Technical Documentation") | No |
| category | Document category (e.g., "Cloud Computing", "AI") | No |
| provider | Content provider/company (e.g., "Google", "Amazon") | No |

Additional columns can be added and will be included in the metadata JSON files.

### Output Files

For each CSV row, the script creates two files in S3:

1. **Document file**: `{random-uuid}.txt`
   - Contains the content from the "document" column
   
2. **Metadata file**: `{random-uuid}.txt.metadata.json`
   - Contains JSON metadata from other CSV columns
   - Example:
     ```json
     {
       "type": "Blog",
       "category": "Artificial Intelligence", 
       "provider": "OpenAI"
     }
     ```

### Sample Data

The included `samples-web-crawl.csv` contains 10 sample documents covering:
- Cloud computing platforms (AWS, GCP, Azure)
- AI/ML topics (AI, Machine Learning, NLP, Computer Vision)
- DevOps and containerization (DevOps, Kubernetes, Docker)

## Testing the Pipeline

### 1. Upload Sample Data

First, upload sample documents to the S3 bucket:

```bash
python validation/scripts/upload_sample_data.py
```

### 2. Test Sync Lambda

Trigger the sync Lambda to process uploaded documents:

```bash
# Auto-detect function name and use default bucket
python validation/scripts/test_sync_lambda.py

# Test specific S3 prefix
python validation/scripts/test_sync_lambda.py --s3-prefix "documents/"

# Asynchronous invocation (fire and forget)
python validation/scripts/test_sync_lambda.py --async
```

### 3. Monitor Processing

After triggering sync:

1. **Monitor SQS Queue**: Check the ingestion queue for processing status
2. **Verify Database**: Query the Aurora database to confirm vector storage
3. **Test Retrieval**: Use the retrieval Lambda to search for similar documents

### Complete Test Workflow

```bash
# 1. Upload sample data
python validation/scripts/upload_sample_data.py

# 2. Trigger sync Lambda to queue documents for processing
python validation/scripts/test_sync_lambda.py

# 3. Check results (documents should be processed by ingestion Lambda)
# Use AWS Console to monitor SQS queue and Aurora database
```

## File Structure

```
validation/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── scripts/
│   ├── upload_sample_data.py   # Sample data upload script
│   └── test_sync_lambda.py     # Sync Lambda test script
└── sample_data/
    └── samples-web-crawl.csv   # Sample CSV data
```

## Troubleshooting

### Common Issues

1. **Bucket not found**: Ensure the CDK stack is deployed and the bucket exists
2. **Access denied**: Check AWS credentials and IAM permissions
3. **CSV format errors**: Verify the CSV has a "document" column with content

### Getting Help

Run the script with `--help` for detailed usage information:

```bash
python validation/scripts/upload_sample_data.py --help
```