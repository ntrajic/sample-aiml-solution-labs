# Aurora Vector Knowledge Base Design

## Overview

The Aurora Vector Knowledge Base system provides multi-modal vector search capabilities using Amazon Aurora PostgreSQL with pgvector extension. The system supports four distinct search methods: content similarity, metadata similarity, hybrid similarity, and filtered search. This design document outlines the architecture for the Vector Retrieval Service Lambda function that implements these search capabilities.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Application   │───▶│ Vector Retrieval │───▶│ Aurora PostgreSQL   │
│                 │    │     Lambda       │    │   with pgvector     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Amazon Bedrock   │
                       │  (Titan v2)      │
                       └──────────────────┘
```

### Vector Retrieval Service Components

1. **Query Processing Layer**: Validates input parameters and routes requests to appropriate search handlers
2. **Embedding Generation Layer**: Generates query embeddings using Amazon Titan v2
3. **Search Engine Layer**: Implements the four search algorithms using pgvector operations
4. **Response Formatting Layer**: Standardizes output format and includes similarity scores

## Components and Interfaces

### Lambda Function Interface

**Function Name**: `vector-retrieval-lambda`

**Input Event Structure**:
```json
{
  "search_type": "content_similarity|metadata_similarity|hybrid_similarity|filter_and_search",
  "query": "search query text",
  "k": 10,
  "metadata_query": "metadata search text (for metadata_similarity)",
  "content_weight": 0.7,
  "metadata_weight": 0.3,
  "filter_type": "category|industry",
  "filter_value": "filter criteria text"
}
```

**Output Response Structure**:
```json
{
  "status": "success|error",
  "search_type": "content_similarity",
  "total_results": 10,
  "execution_time_ms": 245,
  "results": [
    {
      "id": "chunk-uuid",
      "document": "document content chunk",
      "metadata": {...},
      "source_s3_uri": "s3://bucket/key",
      "similarity_score": 0.95,
      "content_score": 0.92,
      "metadata_score": 0.88
    }
  ]
}
```

### Search Algorithm Implementations

#### 1. Content Similarity Search

**Algorithm**:
1. Generate 1024-dimension embedding for query text using Titan v2
2. Execute pgvector cosine similarity query against `embedding_document` column
3. Return top k results ordered by similarity score

**SQL Query Pattern**:
```sql
SELECT id, document, metadata, source_s3_uri,
       1 - (embedding_document <=> %s::vector) as similarity_score
FROM vector_store
ORDER BY embedding_document <=> %s::vector
LIMIT %s;
```

#### 2. Metadata Similarity Search

**Algorithm**:
1. Generate 512-dimension embedding for metadata query using Titan v2
2. Execute pgvector cosine similarity query against `embedding_metadata` column
3. Return top k results ordered by metadata similarity score

**SQL Query Pattern**:
```sql
SELECT id, document, metadata, source_s3_uri,
       1 - (embedding_metadata <=> %s::vector) as similarity_score
FROM vector_store
ORDER BY embedding_metadata <=> %s::vector
LIMIT %s;
```

#### 3. Hybrid Similarity Search

**Algorithm**:
1. Generate embeddings for both content query (1024-dim) and metadata query (512-dim)
2. Calculate weighted combined similarity score: `(content_weight * content_score) + (metadata_weight * metadata_score)`
3. Return top k results ordered by combined score

**SQL Query Pattern**:
```sql
SELECT id, document, metadata, source_s3_uri,
       ((%s * (1 - (embedding_document <=> %s::vector))) + 
        (%s * (1 - (embedding_metadata <=> %s::vector)))) as combined_score,
       1 - (embedding_document <=> %s::vector) as content_score,
       1 - (embedding_metadata <=> %s::vector) as metadata_score
FROM vector_store
ORDER BY combined_score DESC
LIMIT %s;
```

#### 4. Filter and Search

**Algorithm**:
1. Generate 256-dimension embedding for filter_value using Titan v2
2. Find top k*5 documents using field embedding similarity (embedding_category or embedding_industry)
3. Generate 1024-dimension embedding for query text
4. Within the filtered results, find top k documents using content similarity
5. Return results with both filter and content similarity scores

**SQL Query Pattern**:
```sql
WITH filtered_docs AS (
  SELECT id, document, metadata, source_s3_uri, embedding_document,
         1 - (embedding_{filter_type} <=> %s::vector) as filter_score
  FROM vector_store
  ORDER BY embedding_{filter_type} <=> %s::vector
  LIMIT %s
)
SELECT id, document, metadata, source_s3_uri,
       1 - (embedding_document <=> %s::vector) as content_score,
       filter_score
FROM filtered_docs
ORDER BY embedding_document <=> %s::vector
LIMIT %s;
```

## Data Models

### Vector Store Schema

The existing `vector_store` table supports all search operations:

```sql
CREATE TABLE vector_store (
    id UUID PRIMARY KEY,
    document TEXT NOT NULL,
    embedding_document vector(1024) NOT NULL,
    metadata JSONB NOT NULL,
    embedding_metadata vector(512) NOT NULL,
    provider VARCHAR(255) NOT NULL,
    embedding_provider vector(256) NOT NULL,
    category VARCHAR(255) NOT NULL,
    embedding_category vector(256) NOT NULL,
    type VARCHAR(255) NOT NULL,
    embedding_type vector(256) NOT NULL,
    source_s3_uri VARCHAR(1024) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Indexes for Performance

```sql
-- Indexes for vector similarity searches
CREATE INDEX idx_vector_store_embedding_document ON vector_store 
USING ivfflat (embedding_document vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_vector_store_embedding_metadata ON vector_store 
USING ivfflat (embedding_metadata vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_vector_store_embedding_provider ON vector_store 
USING ivfflat (embedding_provider vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_vector_store_embedding_category ON vector_store 
USING ivfflat (embedding_category vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_vector_store_embedding_type ON vector_store 
USING ivfflat (embedding_type vector_cosine_ops) WITH (lists = 100);
```

## Error Handling

### Input Validation

1. **Search Type Validation**: Ensure search_type is one of the four supported values
2. **Parameter Validation**: Validate required parameters based on search type
3. **K Value Validation**: Ensure k is between 1 and 100
4. **Weight Validation**: Ensure content_weight + metadata_weight = 1.0 for hybrid search
5. **Filter Type Validation**: Ensure filter_type is "category" or "industry"

### Database Error Handling

1. **Connection Errors**: Implement retry logic with exponential backoff
2. **Query Timeout**: Set appropriate timeout values and handle gracefully
3. **Vector Dimension Mismatch**: Validate embedding dimensions before queries
4. **Empty Result Sets**: Return appropriate responses for no matches found

### Embedding Generation Errors

1. **Bedrock Service Errors**: Handle rate limiting and service unavailability
2. **Token Limit Exceeded**: Truncate long queries appropriately
3. **Invalid Input Text**: Sanitize and validate query text

### Vector Formatting

1. **PostgreSQL Compatibility**: Convert Python lists to pgvector format using `format_vector_for_postgres()` function
2. **Type Casting**: Use explicit `::vector` casting in SQL queries to ensure proper vector operations
3. **Dimension Validation**: Validate embedding dimensions match expected values before database operations

## Testing Strategy

### Unit Tests

1. **Search Algorithm Tests**: Test each search type with known data sets
2. **Parameter Validation Tests**: Test input validation for all parameters
3. **Embedding Generation Tests**: Mock Bedrock calls and test embedding logic
4. **Database Query Tests**: Test SQL query generation and execution

### Integration Tests

1. **End-to-End Search Tests**: Test complete search workflows with real data
2. **Performance Tests**: Measure response times under various loads
3. **Concurrent Access Tests**: Test multiple simultaneous search requests
4. **Error Scenario Tests**: Test error handling and recovery

### Test Infrastructure

1. **Test Script**: `validation/scripts/test_vector_search.py` provides command-line testing interface
2. **Explicit Arguments**: Uses argparse with `--query`, `--mode`, `--metadata`, and `--k` parameters
3. **Default K Value**: Supports configurable result count with default of 3 results
4. **Example Scripts**: `validation/scripts/run_search_examples.sh` demonstrates all search modes

### Performance Benchmarks

1. **Search Latency**: Target < 2 seconds for datasets up to 100K documents
2. **Throughput**: Support 100+ concurrent searches
3. **Memory Usage**: Optimize for Lambda memory constraints
4. **Database Connection Efficiency**: Minimize connection overhead

## Security Considerations

### Access Control

1. **IAM Permissions**: Restrict Lambda execution role to minimum required permissions
2. **VPC Security**: Deploy Lambda in private subnets with appropriate security groups
3. **Database Access**: Use IAM database authentication where possible
4. **Secrets Management**: Store database credentials in AWS Secrets Manager

### Input Sanitization

1. **SQL Injection Prevention**: Use parameterized queries exclusively
2. **Query Text Validation**: Sanitize and validate all input text
3. **Parameter Bounds Checking**: Enforce limits on k values and query lengths

## Deployment Architecture

### Lambda Configuration

- **Runtime**: Python 3.11
- **Memory**: 3008 MB (maximum for optimal performance)
- **Timeout**: 5 minutes
- **Concurrent Executions**: 50 (configurable based on database capacity)
- **VPC**: Deploy in private subnets with NAT Gateway access

### Dependencies

- **psycopg2-binary**: PostgreSQL database connectivity
- **boto3**: AWS SDK for Bedrock integration
- **numpy**: Vector operations and similarity calculations
- **json**: Response formatting

### Environment Variables

- `DB_SECRET_NAME`: Secrets Manager secret containing database credentials
- `DB_HOST`: Aurora cluster endpoint hostname
- `DB_PORT`: Database port (5432)
- `DB_NAME`: Database name (vector_kb)
- `BEDROCK_REGION`: AWS region for Bedrock service
- `LOG_LEVEL`: Logging level (INFO/DEBUG)

## Monitoring and Observability

### CloudWatch Metrics

1. **Search Latency**: Track response times by search type
2. **Error Rates**: Monitor failed searches and error types
3. **Database Connection Pool**: Monitor connection usage and timeouts
4. **Bedrock API Calls**: Track embedding generation requests and costs

### Logging Strategy

1. **Request Logging**: Log all search requests with parameters
2. **Performance Logging**: Log execution times for each search phase
3. **Error Logging**: Detailed error information for troubleshooting
4. **Debug Logging**: Configurable detailed logging for development

### Alerting

1. **High Error Rate**: Alert when error rate exceeds 5%
2. **High Latency**: Alert when average response time exceeds 3 seconds
3. **Database Connection Issues**: Alert on connection pool exhaustion
4. **Bedrock Service Issues**: Alert on embedding generation failures