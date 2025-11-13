# Sample Use Case - Cost Analysis

## Scenario: Testing with AWS Blog Scraper

This analysis calculates the cost of running the sample validation use case described in `validation/README.md`, where you:
1. Use Strands agent to scrape AWS blog posts
2. Upload documents to S3
3. Trigger ingestion via sync lambda
4. Run search examples

---

## Sample Use Case Assumptions

### Documents Collected
- **Source**: AWS blogs (AI/ML, Serverless, Databases)
- **Number of documents**: 15-20 blog posts
- **Average blog post size**: 1,500 words (~9 KB)
- **Total content**: ~30,000 words

### Usage Pattern
- **One-time ingestion**: 20 documents
- **Test searches**: 10-20 queries
- **Duration**: 1-2 hours of active testing
- **Frequency**: One-time setup + occasional testing

---

## Detailed Cost Breakdown

### 1. Aurora PostgreSQL (Vector Store)

**Initial Setup:**
```
Database initialization: 5 minutes
ACU usage: 0.5 ACU × 0.083 hours = 0.0415 ACU-hours
Cost: 0.0415 × $0.12 = $0.005
```

**Document Ingestion:**
```
Processing time: ~30 minutes (20 documents)
ACU usage: 1.0 ACU × 0.5 hours = 0.5 ACU-hours
Cost: 0.5 × $0.12 = $0.06
```

**Search Testing:**
```
Search queries: 20 queries × 2 seconds = 40 seconds
ACU usage: 0.5 ACU × 0.011 hours = 0.0055 ACU-hours
Cost: 0.0055 × $0.12 = $0.0007
```

**Storage:**
```
Documents: 20 × 3 KB = 60 KB
Embeddings: 20 docs × 8 embeddings × ~1 KB = 160 KB
Total: ~0.22 MB = 0.00022 GB
Cost: 0.00022 × $0.10 = $0.000022/month
```

**I/O Requests:**
```
Writes: 20 docs × 5 chunks × 2 (insert + index) = 200 requests
Reads: 20 searches × 10 (vector similarity) = 200 requests
Total: ~400 requests = 0.0004M requests
Cost: 0.0004 × $0.20 = $0.00008
```

**Aurora Total: ~$0.066**

---

### 2. Amazon Bedrock - Titan Embeddings

**Document Ingestion:**
```
Per document:
- 1,500 words = ~7,500 tokens
- Chunks: 15 chunks × 500 tokens = 7,500 tokens
- Metadata: 100 tokens
- Fields: 2 × 50 = 100 tokens
- Total per doc: 7,700 tokens

20 documents:
Total tokens: 20 × 7,700 = 154,000 tokens
Cost: 154,000 / 1,000 × $0.0001 = $0.0154
```

**Search Queries:**
```
20 queries × 50 tokens = 1,000 tokens
Cost: 1,000 / 1,000 × $0.0001 = $0.0001
```

**Bedrock Total: ~$0.0155**

---

### 3. AWS Lambda Functions

**Sync Lambda:**
```
Invocations: 1
Duration: 5 seconds
Memory: 256 MB = 0.25 GB
GB-seconds: 1 × 5 × 0.25 = 1.25 GB-seconds

Request cost: 1 / 1M × $0.20 = $0.0000002
Compute cost: 1.25 × $0.0000166667 = $0.000021
Total: $0.000021
```

**Ingestion Lambda:**
```
Invocations: 20 documents
Duration: 30 seconds per document
Memory: 1024 MB = 1 GB
GB-seconds: 20 × 30 × 1 = 600 GB-seconds

Request cost: 20 / 1M × $0.20 = $0.000004
Compute cost: 600 × $0.0000166667 = $0.01
Total: $0.01
```

**Retrieval Lambda:**
```
Invocations: 20 searches
Duration: 2 seconds per search
Memory: 512 MB = 0.5 GB
GB-seconds: 20 × 2 × 0.5 = 20 GB-seconds

Request cost: 20 / 1M × $0.20 = $0.000004
Compute cost: 20 × $0.0000166667 = $0.00033
Total: $0.00033
```

**Lambda Total: ~$0.011**

---

### 4. Amazon SQS

**Messages:**
```
Documents queued: 20 messages
Message size: ~1 KB each

Requests: 20 sends + 20 receives + 20 deletes = 60 requests
Cost: 60 / 1M × $0.40 = $0.000024

(Covered by free tier - first 1M requests free)
```

**SQS Total: $0.00**

---

### 5. Amazon S3

**Storage:**
```
Documents: 20 × 9 KB = 180 KB
Metadata: 20 × 1 KB = 20 KB
Total: 200 KB = 0.0002 GB

Storage cost: 0.0002 × $0.023 = $0.0000046/month
```

**Requests:**
```
PUT requests: 40 (20 docs + 20 metadata) = $0.000002
GET requests: 20 (ingestion) = negligible
Total: $0.000002
```

**S3 Total: ~$0.000007**

---

### 6. Supporting Services

**Secrets Manager:**
```
2 secrets × $0.40 = $0.80/month
(Prorated for 1 day of testing: $0.80 / 30 = $0.027)
```

**Cognito:**
```
Free tier (< 50,000 MAU)
Cost: $0.00
```

**VPC Networking:**
```
NAT Gateway: $0.045/hour × 2 hours = $0.09
OR
VPC Endpoints: $0.01/hour × 2 endpoints × 2 hours = $0.04

Using VPC endpoints: $0.04
```

**CloudWatch Logs:**
```
Log ingestion: ~50 MB = 0.05 GB
Cost: 0.05 × $0.50 = $0.025
```

**Supporting Services Total: ~$0.092**

---

## Total Cost Summary

### One-Time Testing Session (2 hours)

| Service | Cost |
|---------|------|
| Aurora PostgreSQL | $0.066 |
| Bedrock Embeddings | $0.016 |
| Lambda Functions | $0.011 |
| SQS | $0.000 |
| S3 Storage | $0.000 |
| VPC Networking | $0.040 |
| CloudWatch Logs | $0.025 |
| Secrets Manager (prorated) | $0.027 |
| **TOTAL** | **~$0.185** |

### Monthly Cost (if kept running)

If you keep the infrastructure deployed but idle:

| Service | Monthly Cost |
|---------|--------------|
| Aurora Storage | $0.00002 |
| S3 Storage | $0.000007 |
| Secrets Manager | $0.80 |
| VPC Endpoints (if kept) | $14.40 |
| **TOTAL (idle)** | **~$15.20/month** |

**Note:** Aurora Serverless v2 scales to zero ACU when idle, so you only pay for storage.

---

## Cost Optimization for Testing

### Option 1: Minimal Testing (Recommended)
```
Duration: 2 hours
Cost: ~$0.19
```

**After testing:**
- Delete the CloudFormation stack
- Total cost: ~$0.19 (one-time)

### Option 2: Keep Infrastructure for Occasional Use
```
Monthly base cost: ~$15/month (mostly Secrets Manager + VPC)
Per test session: ~$0.10 (Aurora + Lambda + Bedrock)
```

**Best for:**
- Ongoing development
- Multiple test sessions per month
- Demo purposes

### Option 3: Destroy and Recreate
```
Per deployment:
- Deploy: ~$0.05 (initialization)
- Test: ~$0.19
- Destroy: $0.00
Total: ~$0.24 per test cycle
```

**Best for:**
- One-time testing
- Infrequent use
- Cost-sensitive scenarios

---

## Detailed Cost Breakdown by Activity

### Activity 1: Deploy Infrastructure
```
CloudFormation deployment: 10 minutes
Aurora initialization: 5 minutes
Custom resource execution: 2 minutes

Cost: ~$0.05
```

### Activity 2: Run Strands Agent Scraper
```
Scraping: 5-10 minutes (runs locally, no AWS cost)
S3 uploads: 40 PUT requests

Cost: ~$0.000002
```

### Activity 3: Trigger Sync Lambda
```
Sync lambda: 1 invocation
SQS messages: 20 messages queued

Cost: ~$0.000021
```

### Activity 4: Document Ingestion
```
Ingestion lambda: 20 invocations × 30 seconds
Bedrock embeddings: 154,000 tokens
Aurora writes: 20 documents × 5 chunks

Cost: ~$0.086
```

### Activity 5: Run Search Examples
```
Retrieval lambda: 20 invocations × 2 seconds
Bedrock embeddings: 1,000 tokens
Aurora reads: 20 queries

Cost: ~$0.001
```

### Activity 6: Infrastructure Idle Time
```
Aurora: Scales to 0 ACU (no cost)
VPC: $0.02/hour
Secrets: Prorated

Cost: ~$0.047 for 2 hours
```

---

## Cost Comparison: Testing Scenarios

### Scenario A: Quick Test (1 hour)
```
Deploy + Test + Destroy immediately
- Deployment: $0.05
- Testing: $0.10
- Idle time: $0.02
Total: ~$0.17
```

### Scenario B: Extended Testing (1 day)
```
Deploy + Multiple test sessions + Destroy
- Deployment: $0.05
- Testing (5 sessions): $0.50
- Idle time (20 hours): $0.40
Total: ~$0.95
```

### Scenario C: Keep for 1 Week
```
Deploy + Occasional testing + Keep running
- Deployment: $0.05
- Testing (10 sessions): $1.00
- Idle time (7 days): $3.50
Total: ~$4.55
```

### Scenario D: Keep for 1 Month
```
Full month deployment
- Base infrastructure: $15.20
- Testing (20 sessions): $2.00
Total: ~$17.20
```

---

## Recommendations

### For First-Time Testing
✅ **Deploy → Test → Destroy**
- **Duration**: 2-3 hours
- **Cost**: $0.20 - $0.30
- **Best for**: Evaluating the solution

### For Development
✅ **Keep deployed, test as needed**
- **Monthly cost**: $15-20/month
- **Per test**: $0.10
- **Best for**: Active development

### For Production Evaluation
✅ **Deploy with real data**
- **Setup**: $0.50
- **Monthly**: $85-100/month
- **Best for**: Production pilot

---

## Free Tier Benefits

If you're within AWS Free Tier:

**Included Free:**
- Lambda: First 1M requests + 400,000 GB-seconds/month
- SQS: First 1M requests/month
- CloudWatch Logs: 5 GB ingestion/month
- Cognito: 50,000 MAU

**Still Pay For:**
- Aurora PostgreSQL (no free tier)
- Bedrock Titan embeddings (no free tier)
- VPC networking (no free tier)
- Secrets Manager (no free tier)

**Estimated cost with Free Tier: ~$0.15** (saves ~$0.04)

---

## Cost Per Document Analysis

### Ingestion Cost per Document
```
Bedrock: $0.00077 (7,700 tokens)
Lambda: $0.0005 (30 seconds processing)
Aurora: $0.003 (write + index)
Total: ~$0.004 per document
```

### Search Cost per Query
```
Bedrock: $0.000005 (50 tokens)
Lambda: $0.00002 (2 seconds)
Aurora: $0.00001 (vector search)
Total: ~$0.000035 per search
```

### Storage Cost per Document (monthly)
```
S3: $0.0000002/month (9 KB)
Aurora: $0.000001/month (embeddings)
Total: ~$0.0000012/month per document
```

---

## Conclusion

### Sample Use Case Cost: **~$0.19**

**Breakdown:**
- 💰 **One-time testing**: $0.19
- 📊 **Per document ingestion**: $0.004
- 🔍 **Per search query**: $0.000035
- 💾 **Storage (monthly)**: $0.000024

**Key Insights:**
1. ✅ Very affordable for testing and evaluation
2. ✅ Most cost is infrastructure overhead (VPC, Secrets Manager)
3. ✅ Actual usage costs (Bedrock, Lambda) are minimal
4. ✅ Destroying the stack after testing keeps costs under $0.20
5. ✅ Keeping deployed for development is ~$15-20/month

**Recommendation for Sample Use Case:**
Deploy → Test → Destroy = **$0.19 total cost** 🎯

---

**Last Updated:** November 2024  
**Pricing Region:** US East/West  
**Currency:** USD
