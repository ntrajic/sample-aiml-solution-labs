# Aurora Vector Knowledge Base - Cost Estimation Report

## Executive Summary

This report provides a detailed cost analysis for running the Aurora Vector Knowledge Base solution on AWS. The solution uses Aurora PostgreSQL Serverless v2 with pgvector, Amazon Bedrock Titan embeddings, Lambda functions, and supporting services.

**Estimated Monthly Cost Range:**
- **Light Usage (Dev/Test)**: $15 - $20/month
- **Medium Usage (Small Production)**: $85 - $100/month
- **Heavy Usage (Large Production)**: $470 - $550/month

**Optimized Costs (using VPC endpoints instead of NAT Gateway):**
- **Light Usage**: $5 - $10/month
- **Medium Usage**: $70 - $85/month
- **Heavy Usage**: $450 - $520/month

## Cost Factors Overview

**Main Cost Drivers (excluding VPC):** Aurora PostgreSQL Serverless v2 dominates the cost structure at 70-90% of total expenses, driven by ACU consumption for vector similarity searches and continuous database activity, while storage and I/O costs scale with document volume and query frequency.

**Cost-Reducing Factors:** The solution leverages serverless Aurora's pay-per-use model with automatic scaling to zero during idle periods, enables reuse of existing Aurora clusters to eliminate redundant infrastructure, benefits from Amazon Titan Embedding's highly cost-effective token pricing at $0.0001 per 1K tokens (resulting in just $0.00027 per document based on 2,700 tokens: 5 document chunks × 500 tokens + 100 metadata tokens + 2 field embeddings × 50 tokens), and utilizes Lambda's sub-second billing to minimize compute costs for both ingestion and retrieval operations.

---

## Cost Assumptions

### Document Processing Assumptions

**Per Document:**
- Average size: 500 words (~3 KB text file)
- Tokens: ~2,500 tokens (500 words × 5 tokens/word average)
- Chunks: 5 chunks per document (~100 words/500 tokens each)
- Chunk overlap: 10% (50 tokens)
- Metadata file: ~1 KB JSON

**Embeddings per Document:**
- Document chunk embeddings: 5 × 1024 dimensions
- Metadata embedding: 1 × 512 dimensions
- Category embedding: 1 × 256 dimensions
- Industry embedding: 1 × 256 dimensions
- **Total: 8 embeddings per document**

**Search Query:**
- Average query: 10-20 words (~50 tokens)
- Embeddings per search: 1-3 (depending on search type)

### Usage Scenarios

#### Light Usage (Development/Testing)
- **Documents**: 1,000 documents (~500 words each)
- **Ingestion**: 100 new documents/month
- **Searches**: 1,000 queries/month
- **Database Activity**: 2-4 hours/day active
- **Storage**: 5 GB total

#### Medium Usage (Small Production)
- **Documents**: 10,000 documents (~500 words each)
- **Ingestion**: 1,000 new documents/month
- **Searches**: 10,000 queries/month
- **Database Activity**: 8-12 hours/day active
- **Storage**: 50 GB total

#### Heavy Usage (Large Production)
- **Documents**: 100,000 documents (~500 words each)
- **Ingestion**: 5,000 new documents/month
- **Searches**: 100,000 queries/month
- **Database Activity**: 24/7 active
- **Storage**: 500 GB total

### Pricing (US East/West - as of 2024)

- **Aurora Serverless v2**: $0.12 per ACU-hour
- **Aurora Storage**: $0.10 per GB-month
- **Aurora I/O**: $0.20 per 1M requests
- **Bedrock Titan Embed v2**: $0.0001 per 1K input tokens
- **Lambda**: $0.20 per 1M requests + $0.0000166667 per GB-second
- **S3 Standard**: $0.023 per GB-month
- **SQS**: $0.40 per 1M requests (first 1M free)
- **Secrets Manager**: $0.40 per secret per month
- **Cognito**: Free tier: 50,000 MAUs

---

## Detailed Cost Breakdown

### 1. Aurora PostgreSQL Serverless v2 (Vector Store)

#### Configuration
- **Min Capacity**: 0.5 ACU
- **Max Capacity**: 16 ACU
- **Auto-scaling**: Scales based on workload

#### Cost Calculation

**Light Usage:**
```
Average ACU: 0.5 ACU (mostly idle)
Active hours: 60 hours/month (2 hours/day)
Cost = 0.5 ACU × 60 hours × $0.12 = $3.60/month

Storage: 5 GB × $0.10 = $0.50/month
I/O: ~1M requests × $0.20 = $0.20/month

Total: ~$4.30/month
```

**Medium Usage:**
```
Average ACU: 1.5 ACU (moderate activity)
Active hours: 300 hours/month (10 hours/day)
Cost = 1.5 ACU × 300 hours × $0.12 = $54/month

Storage: 50 GB × $0.10 = $5/month
I/O: ~10M requests × $0.20 = $2/month

Total: ~$61/month
```

**Heavy Usage:**
```
Average ACU: 4 ACU (high activity, 24/7)
Active hours: 720 hours/month (24/7)
Cost = 4 ACU × 720 hours × $0.12 = $345.60/month

Storage: 500 GB × $0.10 = $50/month
I/O: ~100M requests × $0.20 = $20/month

Total: ~$415.60/month
```

**Key Factors:**
- Vector similarity searches (HNSW index) are CPU-intensive
- Embedding storage requires significant memory
- Auto-scaling helps optimize costs during idle periods
- Storage grows with document count and embeddings

---

### 2. Amazon Bedrock - Titan Text Embedding v2

#### Embedding Generation

**Per Document Processing:**
- Average document size: ~500 words (2,500 tokens)
- Document chunks: ~5 chunks per document (~100 words/500 tokens each)
- Metadata: 1 consolidated embedding
- Field embeddings: 2 fields (category, industry)
- Total embeddings per document: 8 embeddings (5 document + 1 metadata + 2 fields)

**Token Calculation:**
- Document chunk: ~500 tokens each
- Metadata: ~100 tokens
- Field: ~50 tokens each

**Cost per Document:**
```
Document embeddings: 5 chunks × 500 tokens = 2,500 tokens
Metadata embedding: 100 tokens
Field embeddings: 2 × 50 = 100 tokens
Total: 2,700 tokens per document

Cost = 2,700 tokens / 1,000 × $0.0001 = $0.00027 per document
```

**Per Search Query:**
- Query embedding: ~50 tokens
- Filter embeddings (if used): ~50 tokens
- Total: ~100 tokens per search

**Cost per Search:**
```
Cost = 100 tokens / 1,000 × $0.0001 = $0.00001 per search
```

#### Monthly Costs

**Light Usage:**
```
Ingestion: 100 documents × $0.00027 = $0.027
Searches: 1,000 queries × $0.00001 = $0.01

Total: ~$0.04/month
```

**Medium Usage:**
```
Ingestion: 1,000 documents × $0.00027 = $0.27
Searches: 10,000 queries × $0.00001 = $0.10

Total: ~$0.37/month
```

**Heavy Usage:**
```
Ingestion: 5,000 documents × $0.00027 = $1.35
Searches: 100,000 queries × $0.00001 = $1.00

Total: ~$2.35/month
```

**Key Factors:**
- Bedrock costs are surprisingly low due to efficient token usage
- Titan v2 supports multiple dimensions (256, 512, 1024)
- Batch processing reduces overhead
- Caching can further reduce costs

---

### 3. AWS Lambda Functions

#### Lambda Configuration

**Ingestion Lambda:**
- Memory: 1024 MB
- Avg Duration: 30 seconds per document
- Invocations: Based on document ingestion rate

**Retrieval Lambda:**
- Memory: 512 MB
- Avg Duration: 2 seconds per search
- Invocations: Based on search rate

**Sync Lambda:**
- Memory: 256 MB
- Avg Duration: 5 seconds per invocation
- Invocations: ~10 per month

#### Cost Calculation

**Light Usage:**
```
Ingestion:
- Requests: 100 documents = 100 requests
- Compute: 100 × 30s × 1GB = 3,000 GB-seconds
- Request cost: 100 / 1M × $0.20 = $0.00002
- Compute cost: 3,000 × $0.0000166667 = $0.05
- Subtotal: $0.05

Retrieval:
- Requests: 1,000 searches = 1,000 requests
- Compute: 1,000 × 2s × 0.5GB = 1,000 GB-seconds
- Request cost: 1,000 / 1M × $0.20 = $0.0002
- Compute cost: 1,000 × $0.0000166667 = $0.017
- Subtotal: $0.017

Sync: ~$0.001

Total: ~$0.07/month
```

**Medium Usage:**
```
Ingestion:
- Requests: 1,000 documents
- Compute: 30,000 GB-seconds
- Cost: $0.50

Retrieval:
- Requests: 10,000 searches
- Compute: 10,000 GB-seconds
- Cost: $0.17

Sync: ~$0.01

Total: ~$0.68/month
```

**Heavy Usage:**
```
Ingestion:
- Requests: 5,000 documents
- Compute: 150,000 GB-seconds
- Cost: $2.50

Retrieval:
- Requests: 100,000 searches
- Compute: 100,000 GB-seconds
- Cost: $1.67

Sync: ~$0.05

Total: ~$4.22/month
```

**Key Factors:**
- Lambda has generous free tier (1M requests, 400,000 GB-seconds/month)
- VPC Lambda functions have slightly higher cold start times
- Concurrent executions affect scaling
- Reserved concurrency can be used for predictable workloads

---

### 4. Amazon SQS (Message Queue)

#### Usage Pattern
- Messages per document: 1 message
- Message size: ~1 KB
- Retention: 4 days (default)

#### Cost Calculation

**Light Usage:**
```
Messages: 100 documents = 100 messages
Cost: 100 / 1M × $0.40 = $0.00004
(Covered by free tier)

Total: $0/month
```

**Medium Usage:**
```
Messages: 1,000 documents = 1,000 messages
Cost: 1,000 / 1M × $0.40 = $0.0004
(Covered by free tier)

Total: $0/month
```

**Heavy Usage:**
```
Messages: 5,000 documents = 5,000 messages
Cost: 5,000 / 1M × $0.40 = $0.002

Total: ~$0.002/month
```

**Key Factors:**
- First 1M requests per month are free
- Dead letter queue adds minimal cost
- FIFO queues cost more but not needed here
- Message retention doesn't affect cost

---

### 5. Amazon S3 (Document Storage)

#### Storage Calculation

**Light Usage:**
```
Documents: 1,000 × 3 KB (text, ~500 words) = 3 MB
Metadata: 1,000 × 1 KB = 1 MB
Total: 4 MB

Storage: 0.004 GB × $0.023 = $0.0001/month
Requests: 200 PUT + 1,000 GET = negligible

Total: ~$0.001/month
```

**Medium Usage:**
```
Documents: 10,000 × 3 KB = 30 MB
Metadata: 10,000 × 1 KB = 10 MB
Total: 40 MB

Storage: 0.04 GB × $0.023 = $0.001/month
Requests: ~$0.01

Total: ~$0.01/month
```

**Heavy Usage:**
```
Documents: 100,000 × 3 KB = 300 MB
Metadata: 100,000 × 1 KB = 100 MB
Total: 400 MB

Storage: 0.4 GB × $0.023 = $0.01/month
Requests: ~$0.10

Total: ~$0.11/month
```

**Key Factors:**
- S3 costs are minimal for text documents
- Lifecycle policies can reduce costs further
- Intelligent-Tiering can optimize storage costs
- Transfer costs are minimal within same region

---

### 6. Supporting Services

#### AWS Secrets Manager
```
Secrets: 2 (database credentials, Cognito config)
Cost: 2 × $0.40 = $0.80/month
```

#### Amazon Cognito
```
Monthly Active Users (MAU): Typically < 50,000
Cost: Free tier covers most use cases
Cost: $0/month (assuming < 50,000 MAU)
```

#### VPC (Networking)
```
NAT Gateway (if used): $0.045/hour = ~$32.40/month
VPC Endpoints: $0.01/hour each = ~$7.20/month per endpoint
Data Transfer: Minimal within same region

Note: Can use VPC endpoints instead of NAT Gateway to reduce costs
Estimated: $0-40/month depending on architecture
```

#### CloudWatch Logs
```
Light: 1 GB ingestion = $0.50/month
Medium: 5 GB ingestion = $2.50/month
Heavy: 20 GB ingestion = $10/month
```

---

## Total Monthly Cost Summary

### Light Usage (Development/Testing)
| Service | Monthly Cost |
|---------|--------------|
| Aurora PostgreSQL | $4.30 |
| Bedrock Embeddings | $0.04 |
| Lambda Functions | $0.07 |
| SQS | $0.00 |
| S3 Storage | $0.001 |
| Secrets Manager | $0.80 |
| Cognito | $0.00 |
| VPC/Networking | $10.00 |
| CloudWatch Logs | $0.50 |
| **TOTAL** | **~$15.71/month** |

**Optimized (no NAT Gateway):** ~$5.71/month

---

### Medium Usage (Small Production)
| Service | Monthly Cost |
|---------|--------------|
| Aurora PostgreSQL | $61.00 |
| Bedrock Embeddings | $0.37 |
| Lambda Functions | $0.68 |
| SQS | $0.00 |
| S3 Storage | $0.01 |
| Secrets Manager | $0.80 |
| Cognito | $0.00 |
| VPC/Networking | $20.00 |
| CloudWatch Logs | $2.50 |
| **TOTAL** | **~$85.36/month** |

**Optimized (VPC endpoints):** ~$72.56/month

---

### Heavy Usage (Large Production)
| Service | Monthly Cost |
|---------|--------------|
| Aurora PostgreSQL | $415.60 |
| Bedrock Embeddings | $2.35 |
| Lambda Functions | $4.22 |
| SQS | $0.002 |
| S3 Storage | $0.11 |
| Secrets Manager | $0.80 |
| Cognito | $0.00 |
| VPC/Networking | $40.00 |
| CloudWatch Logs | $10.00 |
| **TOTAL** | **~$473.08/month** |

---

## Cost Optimization Strategies

### 1. Aurora PostgreSQL Optimization

**Reduce ACU Usage:**
- Set appropriate min/max ACU limits
- Use Aurora Serverless v2 auto-pause (when available)
- Schedule scaling based on usage patterns
- Optimize queries and indexes

**Potential Savings:** 20-40% on database costs

**Example:**
```
Medium usage: $61 → $37-49/month (save $12-24)
Heavy usage: $415 → $250-332/month (save $83-165)
```

### 2. Networking Cost Reduction

**Use VPC Endpoints instead of NAT Gateway:**
- S3 Gateway Endpoint: Free
- Bedrock Interface Endpoint: $7.20/month
- Secrets Manager Endpoint: $7.20/month

**Savings:** $32.40/month (NAT Gateway) - $14.40/month (endpoints) = $18/month

### 3. Lambda Optimization

**Strategies:**
- Use Lambda Power Tuning to find optimal memory
- Implement connection pooling for database
- Use Lambda layers to reduce deployment size
- Enable Lambda SnapStart (when available for Python)

**Potential Savings:** 10-30% on Lambda costs

### 4. Bedrock Cost Reduction

**Strategies:**
- Cache embeddings for frequently searched queries
- Batch document processing
- Use appropriate embedding dimensions (256 vs 1024)
- Implement deduplication before embedding

**Potential Savings:** 20-50% on embedding costs

### 5. Storage Optimization

**S3 Lifecycle Policies:**
- Move old documents to S3 Glacier after 90 days
- Delete temporary files after processing
- Use S3 Intelligent-Tiering

**Aurora Storage:**
- Regular cleanup of old/unused data
- Implement data retention policies
- Archive historical data

**Potential Savings:** 30-50% on storage costs

---

## Scaling Projections

### Cost Growth by Document Count

| Documents | Monthly Ingestion | Searches/Month | Estimated Cost |
|-----------|-------------------|----------------|----------------|
| 1K | 100 | 1K | $15-20 |
| 10K | 1K | 10K | $85-100 |
| 50K | 2.5K | 50K | $250-300 |
| 100K | 5K | 100K | $473-550 |
| 500K | 10K | 500K | $1,800-2,200 |
| 1M | 20K | 1M | $3,500-4,500 |

**Key Insight:** Costs scale sub-linearly due to:
- Aurora's efficient storage
- Bedrock's low per-token cost
- Lambda's pay-per-use model

---

## Cost Monitoring and Alerts

### Recommended CloudWatch Alarms

1. **Aurora ACU Usage**
   - Alert when average ACU > 80% of max for 1 hour
   - Indicates need to increase max capacity

2. **Lambda Duration**
   - Alert when p99 duration > 25 seconds (ingestion)
   - Alert when p99 duration > 5 seconds (retrieval)

3. **Bedrock Token Usage**
   - Alert when daily token usage > expected threshold
   - Indicates potential inefficiency or abuse

4. **Monthly Cost**
   - Set AWS Budget alerts at 50%, 80%, 100% of expected cost

### Cost Allocation Tags

Recommended tags for cost tracking:
```
Environment: dev/staging/prod
Component: database/lambda/storage
CostCenter: your-cost-center
Project: aurora-vector-kb
```

---

## Recommendations

### For Development/Testing
- Use minimum Aurora capacity (0.5 ACU)
- Implement auto-pause when possible
- Use VPC endpoints instead of NAT Gateway
- **Estimated Cost:** $5-15/month

### For Small Production
- Set Aurora min: 0.5 ACU, max: 4 ACU
- Implement caching for frequent queries
- Monitor and optimize based on usage
- **Estimated Cost:** $70-100/month

### For Large Production
- Set Aurora min: 2 ACU, max: 16 ACU
- Use Aurora read replicas for read-heavy workloads
- Implement comprehensive caching strategy
- Consider Reserved Capacity for predictable workloads
- **Estimated Cost:** $400-600/month

---

## Conclusion

The Aurora Vector Knowledge Base solution offers:

✅ **Cost-Effective**: Competitive with managed alternatives
✅ **Scalable**: Pay-per-use model scales with demand
✅ **Flexible**: Serverless architecture reduces idle costs
✅ **Predictable**: Most costs are usage-based and linear

**Key Cost Drivers:**
1. **Aurora PostgreSQL** (70-90% of total cost)
2. **VPC Networking** (10-20% if using NAT Gateway)
3. **Lambda & Bedrock** (5-10% combined)

**Optimization Priority:**
1. Right-size Aurora capacity
2. Optimize networking (use VPC endpoints)
3. Implement query caching
4. Monitor and adjust based on actual usage

**Break-Even Analysis:**
- For < 10K documents: Aurora Vector KB is cost-effective
- For 10K-100K documents: Highly competitive with alternatives
- For > 100K documents: More cost-effective than most managed solutions

---

## Appendix: Cost Calculation Formulas

### Aurora Serverless v2
```
Monthly Cost = (Average ACU × Hours Active × $0.12) + (Storage GB × $0.10) + (I/O Requests / 1M × $0.20)
```

### Bedrock Titan Embeddings
```
Cost per Document = (Total Tokens / 1,000) × $0.0001
Total Tokens = (5 chunks × 500 tokens) + 100 (metadata) + (2 fields × 50 tokens)
Total Tokens = 2,500 + 100 + 100 = 2,700 tokens per document
Cost per Document = $0.00027
```

### Lambda
```
Request Cost = (Invocations / 1M) × $0.20
Compute Cost = (GB-seconds) × $0.0000166667
GB-seconds = Invocations × Duration (seconds) × Memory (GB)
```

### Total Monthly Cost
```
Total = Aurora + Bedrock + Lambda + S3 + Supporting Services
```

---