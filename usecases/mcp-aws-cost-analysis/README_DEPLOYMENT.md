# AWS Cost Analysis MCP Server - AgentCore Runtime Deployment

## Overview

Deploy the AWS Cost Analysis MCP server to Amazon Bedrock AgentCore Runtime using a two-step process:
1. **Prerequisites**: Run `run_prerequisite.py` to create IAM role and Cognito
2. **Deployment**: Use `agentcore` CLI commands to configure and launch

This MCP server provides cost analysis tools for AWS Bedrock, AgentCore, and business value calculations.

## Architecture

```
┌─────────────┐
│ MCP Client  │
└──────┬──────┘
       │ JWT Auth (Client Credentials)
       ▼
┌─────────────────────┐
│ Amazon Cognito      │
│ User Pool           │
└──────┬──────────────┘
       │ Bearer Token
       ▼
┌─────────────────────┐
│ AgentCore Runtime   │
│ ┌─────────────────┐ │
│ │ FastMCP Server  │ │
│ │ (cost_analysis) │ │
│ └────────┬────────┘ │
└──────────┼──────────┘
           │
           ▼
    ┌──────────────┐
    │ AWS Pricing  │
    │ API          │
    └──────────────┘
```

## Features

### Available MCP Tools

1. **get_bedrock_pricing_tool_read_only** - Bedrock model pricing
2. **get_agentcore_pricing_tool_read_only** - AgentCore component pricing
3. **get_aws_pricing_tool_read_only** - General AWS service pricing
4. **get_attribute_values_tool_read_only** - Pricing attribute values
5. **bedrock_calculator_tool_read_only** - Bedrock cost calculations
6. **bedrock_what_if_tool_read_only** - Bedrock what-if analysis
7. **agentcore_calculator_tool_read_only** - AgentCore cost calculations
8. **agentcore_what_if_tool_read_only** - AgentCore what-if analysis
9. **business_value_calculator_tool_read_only** - ROI calculations
10. **business_value_what_if_tool_read_only** - Business value analysis
11. **health_check** - Server health status

## IAM Permissions Analysis

### AWS Services Used

The MCP server uses **AWS Pricing API** exclusively:
- All calls target `us-east-1` region (Pricing API requirement)
- Used for retrieving pricing data for Bedrock, AgentCore, and other AWS services

### Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PricingAPIReadAccess",
      "Effect": "Allow",
      "Action": [
        "pricing:GetProducts",
        "pricing:DescribeServices",
        "pricing:GetAttributeValues"
      ],
      "Resource": "*"
    }
  ]
}
```

**Additional Standard AgentCore Permissions:**
- ECR image access
- CloudWatch Logs
- X-Ray tracing
- CloudWatch metrics
- AgentCore workload identity

All operations are **read-only** with no access to customer data.

## Prerequisites

```bash
# Install required packages
pip install bedrock-agentcore-starter-toolkit boto3 mcp requests

# Configure AWS credentials
aws configure

# Ensure Docker is running (for local builds)
docker --version
```

## Deployment Steps

### Step 1: Setup Prerequisites

Run the prerequisite script to create IAM role and Cognito:

```bash
cd usecases/mcp-aws-cost-analysis
python run_prerequisite.py
```

**What it creates:**
- IAM execution role with Pricing API permissions
- Cognito user pool with OAuth client credentials flow
- Resource server with custom scopes
- Stores configuration in AWS Systems Manager and Secrets Manager

**Expected Output:**
```
================================================================================
AWS Cost Analysis MCP Server - Prerequisites Setup
================================================================================

📍 Using AWS region: us-west-2

📁 Verifying required files...
✓ Found: cost_analysis_fastmcp_server.py
✓ Found: requirements.txt

🔑 Creating IAM role: agentcore-aws_cost_analysis_mcp-role
✓ Created IAM role
✓ Attaching policy to role
✓ IAM role configured successfully
  Role ARN: arn:aws:iam::123456789012:role/agentcore-aws_cost_analysis_mcp-role

🔐 Setting up Amazon Cognito for app-to-app authentication...
✓ Created user pool: us-west-2_xxxxx
✓ Created resource server
✓ Created app client with client credentials: xxxxxxxxx
✓ Created user pool domain: cost-analysis-mcp-xxxxx

💾 Storing configuration...
✓ IAM role ARN stored in Parameter Store
✓ Cognito credentials stored in Secrets Manager

================================================================================
✅ PREREQUISITES SETUP COMPLETE!
================================================================================

📋 Configuration Summary:
  Agent Name: aws_cost_analysis_mcp
  Region: us-west-2
  IAM Role ARN: arn:aws:iam::123456789012:role/agentcore-aws_cost_analysis_mcp-role
  Cognito Pool ID: us-west-2_xxxxx
  Cognito Client ID: xxxxxxxxx
  Discovery URL: https://cognito-idp.us-west-2.amazonaws.com/us-west-2_xxxxx/.well-known/openid-configuration

================================================================================
NEXT STEPS: Deploy with AgentCore CLI
================================================================================

📝 COPY AND PASTE THESE COMMANDS:

# Step 1: Configure the deployment
agentcore configure \
  --entrypoint cost_analysis_fastmcp_server.py \
  --name aws_cost_analysis_mcp \
  --execution-role arn:aws:iam::123456789012:role/agentcore-aws_cost_analysis_mcp-role \
  --region us-west-2 \
  --protocol MCP \
  --requirements-file requirements.txt \
  --disable-memory \
  --authorizer-config '{"customJWTAuthorizer": {"allowedClients": ["xxxxx"], "discoveryUrl": "https://..."}}' \
  --non-interactive

# Step 2: Launch to AWS (takes 10-15 minutes)
agentcore launch --agent aws_cost_analysis_mcp

# Step 3: Check status
agentcore status --agent aws_cost_analysis_mcp

# Step 4: Test the deployment
python test_mcp_client.py

# Step 5: View logs
aws logs tail /aws/bedrock-agentcore/runtimes/aws_cost_analysis_mcp --follow

================================================================================
💡 TIP: The commands above use the actual values from your setup!
================================================================================

✅ Commands also saved to: agentcore_commands.sh
   You can run: bash agentcore_commands.sh
```

**Options:**
```bash
# Skip Cognito (not recommended for production)
python run_prerequisite.py --no-cognito

# Use different region
python run_prerequisite.py --region us-east-1
```

### Step 2: Run AgentCore Commands

The prerequisite script generates ready-to-run commands with your actual configuration values.

**Option A: Copy-paste from terminal output**

The script prints commands like this (with your actual values):
```bash
agentcore configure \
  --entrypoint cost_analysis_fastmcp_server.py \
  --name aws_cost_analysis_mcp \
  --execution-role arn:aws:iam::123456789012:role/agentcore-aws_cost_analysis_mcp-role \
  --region us-west-2 \
  --protocol MCP \
  --requirements-file requirements.txt \
  --disable-memory \
  --authorizer-config '{"customJWTAuthorizer": {"allowedClients": ["xxxxx"], "discoveryUrl": "https://..."}}' \
  --non-interactive

agentcore launch --agent aws_cost_analysis_mcp
```

**Option B: Run the generated script**

The script also saves all commands to `agentcore_commands.sh`:
```bash
bash agentcore_commands.sh
```

**Configuration Options Explained:**
- `--entrypoint`: The FastMCP server file
- `--name`: Unique name for your MCP server
- `--execution-role`: IAM role ARN from Step 1 (actual value inserted)
- `--region`: AWS region
- `--protocol MCP`: Specifies MCP protocol
- `--requirements-file`: Python dependencies
- `--disable-memory`: No memory needed for this stateless service
- `--authorizer-config`: Cognito JWT authentication config (actual values inserted)
- `--non-interactive`: Skip prompts

**What happens during launch:**
- Builds the Docker image using CodeBuild (or locally if `--local-build` specified)
- Pushes the image to ECR
- Creates the AgentCore Runtime endpoint
- Starts the MCP server

**Deployment takes approximately 10-15 minutes.**

### Step 3: Verify Deployment

```bash
agentcore status --agent aws_cost_analysis_mcp
```

**Expected Output:**
```
Agent: aws_cost_analysis_mcp
Status: ACTIVE
Endpoint: https://bedrock-agentcore.us-west-2.amazonaws.com/runtimes/...
Protocol: MCP
Memory: Disabled
```

### Step 4: Test the MCP Server

```bash
python test_mcp_client.py
```

The test client will:
- Retrieve Agent ARN from Parameter Store
- Get Cognito credentials from Secrets Manager
- Obtain access token using client credentials flow
- Connect to MCP server and list tools
- Test health check and pricing tools

**Expected Output:**
```
Using AWS region: us-west-2
================================================================================
✓ Retrieved Agent ARN from Parameter Store
✓ Retrieved Cognito credentials from Secrets Manager
🔐 Getting access token from Cognito...
✓ Obtained access token (expires in 3600 seconds)

🔗 Connecting to MCP server...
🔄 Initializing MCP session...
✓ MCP session initialized

================================================================================
📋 Available MCP Tools
================================================================================

🔧 get_bedrock_pricing_tool_read_only
   Get pricing information for Amazon Bedrock models
   Parameters: model_name, region

...

✅ Successfully connected to MCP server!
   Found 11 tools available
================================================================================
```

## What Gets Deployed

### AWS Resources Created

1. **IAM Role** (by run_prerequisite.py)
   - Name: `agentcore-aws_cost_analysis_mcp-role`
   - Pricing API read-only permissions
   - Standard AgentCore Runtime permissions

2. **Amazon Cognito User Pool** (by run_prerequisite.py)
   - OAuth client credentials flow
   - Resource server with custom scopes
   - App client with client secret
   - User pool domain for token endpoint

3. **Amazon ECR Repository** (by agentcore launch)
   - Stores the MCP server Docker image
   - Auto-created by toolkit

4. **AgentCore Runtime** (by agentcore launch)
   - Hosts the MCP server
   - Protocol: MCP (Streamable HTTP)
   - Authentication: JWT via Cognito

5. **AWS Systems Manager Parameters**
   - `/app/aws_cost_analysis_mcp/iam_role_arn` - IAM role ARN
   - `/app/aws_cost_analysis_mcp/agent_arn` - Agent ARN (after launch)

6. **AWS Secrets Manager Secret**
   - `aws_cost_analysis_mcp/cognito/credentials` - Cognito config with client secret

## Monitoring

### View Logs

```bash
# Real-time logs
aws logs tail /aws/bedrock-agentcore/runtimes/aws_cost_analysis_mcp --follow

# Last 100 lines
aws logs tail /aws/bedrock-agentcore/runtimes/aws_cost_analysis_mcp --since 1h
```

### Check Status

```bash
# Using toolkit
agentcore status --agent aws_cost_analysis_mcp

# Verbose output with full details
agentcore status --agent aws_cost_analysis_mcp --verbose
```

### CloudWatch Metrics

- Navigate to CloudWatch Console
- Look for `bedrock-agentcore` namespace
- Filter by agent name

## Troubleshooting

### Prerequisites Script Fails

**Issue:** Permission denied creating IAM role

**Solution:**
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check IAM permissions
aws iam get-user

# Ensure you have permissions to:
# - iam:CreateRole, iam:PutRolePolicy
# - cognito-idp:CreateUserPool, CreateUserPoolClient
# - ssm:PutParameter
# - secretsmanager:CreateSecret
```

### Configure Command Fails

**Issue:** Invalid agent name or parameters

**Solution:**
```bash
# Agent name must contain only letters, numbers, underscores
# Check the command from run_prerequisite.py output
# Ensure all parameters are correctly copied
```

### Launch Fails

**Issue:** CodeBuild fails during image build

**Solution:**
```bash
# Check CodeBuild logs in AWS Console
# Or try local build:
agentcore launch --local-build --agent aws_cost_analysis_mcp

# Verify Docker is running
docker ps

# Check requirements.txt is valid
pip install -r requirements.txt
```

### Test Client Hangs

**Issue:** Stalls at "Initializing MCP session"

**Solution:**
```bash
# Check runtime status
agentcore status --agent aws_cost_analysis_mcp

# View server logs
aws logs tail /aws/bedrock-agentcore/runtimes/aws_cost_analysis_mcp --follow

# Runtime may still be starting (wait 2-3 minutes after launch)
# Or there may be an error in the server code
```

### Authentication Errors

**Issue:** 403 Forbidden or "Unauthorized"

**Solution:**
```bash
# Verify Cognito credentials
aws secretsmanager get-secret-value \
  --secret-id aws_cost_analysis_mcp/cognito/credentials

# Test token generation manually
python -c "
import boto3, json, requests, base64
secrets = boto3.client('secretsmanager')
response = secrets.get_secret_value(SecretId='aws_cost_analysis_mcp/cognito/credentials')
config = json.loads(response['SecretString'])

credentials = f\"{config['client_id']}:{config['client_secret']}\"
encoded = base64.b64encode(credentials.encode()).decode()

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': f'Basic {encoded}'
}
data = {'grant_type': 'client_credentials', 'scope': 'aws_cost_analysis_mcp-api/invoke'}

r = requests.post(config['token_endpoint'], headers=headers, data=data)
print(r.json())
"
```

### Import Errors in Server

**Issue:** Module not found errors in logs

**Solution:**
- Verify all files in `utils/` directory are present
- Check `requirements.txt` includes all dependencies:
  ```
  boto3
  botocore
  pyyaml
  retrying
  pandas
  strands-agents
  strands-agents-tools
  fastmcp
  bedrock-agentcore
  mcp
  ```
- Ensure directory structure is maintained:
  ```
  usecases/mcp-aws-cost-analysis/
  ├── cost_analysis_fastmcp_server.py
  ├── requirements.txt
  └── utils/
      ├── __init__.py
      ├── pricing_util.py
      ├── use_bedrock_calculator.py
      ├── use_agentcore_calculator.py
      └── bva_calculator.py
  ```

### Pricing API Errors

**Issue:** "Access Denied" from Pricing API

**Solution:**
```bash
# Verify IAM role has pricing permissions
aws iam get-role-policy \
  --role-name agentcore-aws_cost_analysis_mcp-role \
  --policy-name AgentCorePolicy

# Test Pricing API access directly
aws pricing get-products \
  --service-code AmazonBedrock \
  --region us-east-1 \
  --max-items 1
```

## Cleanup

### Remove All Resources

```bash
# 1. Destroy AgentCore resources
agentcore destroy --agent aws_cost_analysis_mcp --force --delete-ecr-repo

# 2. Delete IAM role
aws iam delete-role-policy \
  --role-name agentcore-aws_cost_analysis_mcp-role \
  --policy-name AgentCorePolicy
aws iam delete-role --role-name agentcore-aws_cost_analysis_mcp-role

# 3. Delete Cognito user pool (get pool ID from run_prerequisite.py output)
POOL_ID=$(aws secretsmanager get-secret-value \
  --secret-id aws_cost_analysis_mcp/cognito/credentials \
  --query SecretString --output text | jq -r .pool_id)
aws cognito-idp delete-user-pool --user-pool-id $POOL_ID

# 4. Delete Secrets Manager secret
aws secretsmanager delete-secret \
  --secret-id aws_cost_analysis_mcp/cognito/credentials \
  --force-delete-without-recovery

# 5. Delete SSM parameters
aws ssm delete-parameter --name /app/aws_cost_analysis_mcp/iam_role_arn
aws ssm delete-parameter --name /app/aws_cost_analysis_mcp/agent_arn
```

## Cost Considerations

- **AgentCore Runtime**: ~$0.10 per hour when active (auto-scales to zero when idle)
- **Pricing API**: Free tier, minimal costs for typical usage
- **CloudWatch Logs**: ~$0.50/GB ingested
- **ECR Storage**: ~$0.10/GB per month
- **Cognito**: Free tier covers testing (50,000 MAUs free)

**Optimization Tips:**
- Runtime auto-scales to zero when idle
- Use session management to control costs
- Monitor CloudWatch metrics for usage patterns
- Consider caching frequently accessed pricing data

## Security Best Practices

1. ✅ **Least Privilege**: IAM role has only Pricing API read access
2. ✅ **App-to-App Authentication**: OAuth client credentials flow (no user passwords)
3. ✅ **Encryption**: All data encrypted in transit and at rest
4. ✅ **Audit Logging**: CloudWatch Logs and X-Ray tracing
5. ✅ **Secrets Management**: Client secret stored in Secrets Manager
6. ✅ **Resource Isolation**: AgentCore Runtime provides isolated execution

## Advanced Configuration

### VPC Networking

To deploy with VPC networking for private resource access:

```bash
agentcore configure \
  --entrypoint cost_analysis_fastmcp_server.py \
  --name aws_cost_analysis_mcp \
  --execution-role <role-arn> \
  --region us-west-2 \
  --protocol MCP \
  --requirements-file requirements.txt \
  --disable-memory \
  --vpc \
  --subnets subnet-abc123,subnet-def456 \
  --security-groups sg-xyz789 \
  --authorizer-config '...'
```

### Custom Lifecycle Settings

Configure session timeout and max lifetime:

```bash
agentcore configure \
  ... \
  --idle-timeout 1800 \
  --max-lifetime 7200
```

### Local Testing

Test locally before deploying to AWS:

```bash
# Build and run locally
agentcore launch --agent aws_cost_analysis_mcp --local

# In another terminal, test locally
python test_mcp_client.py --no-auth --agent-arn <local-arn>
```

## Integration Examples

### Using with Strands Agents

```python
from strands import Agent
import boto3
import json
import requests
import base64

# Get Cognito credentials
secrets = boto3.client('secretsmanager')
response = secrets.get_secret_value(SecretId='aws_cost_analysis_mcp/cognito/credentials')
cognito_config = json.loads(response['SecretString'])

# Get access token
credentials = f"{cognito_config['client_id']}:{cognito_config['client_secret']}"
encoded = base64.b64encode(credentials.encode()).decode()
headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': f'Basic {encoded}'
}
data = {
    'grant_type': 'client_credentials',
    'scope': 'aws_cost_analysis_mcp-api/invoke'
}
token_response = requests.post(cognito_config['token_endpoint'], headers=headers, data=data)
access_token = token_response.json()['access_token']

# Get Agent ARN
ssm = boto3.client('ssm')
agent_arn = ssm.get_parameter(Name='/app/aws_cost_analysis_mcp/agent_arn')['Parameter']['Value']

# Create agent with MCP tools
# (Integration code depends on your specific use case)
```

## Additional Resources

- [AgentCore Starter Toolkit Documentation](https://aws.github.io/bedrock-agentcore-starter-toolkit/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [AWS Pricing API Documentation](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/price-changes.html)
- [Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

## Support

For issues:
1. Check CloudWatch logs for error details
2. Verify IAM permissions are correctly configured
3. Ensure all dependencies are in requirements.txt
4. Test locally before deploying to AWS
5. Review the troubleshooting section above
