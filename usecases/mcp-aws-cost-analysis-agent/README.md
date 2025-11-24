# AWS Cost Analysis Agent - MCP Server on AgentCore Runtime

An AI-powered cost analysis agent that provides detailed AWS pricing calculations and business value analysis for Amazon Bedrock, Amazon Bedrock AgentCore, and Amazon EMR. Deployed as an MCP (Model Context Protocol) server on Amazon Bedrock AgentCore Runtime.

## Overview

This agent helps AWS sales teams and customers with:
- **Bedrock Pricing**: Calculate costs for LLM models, vector databases, and agentic workflows
- **AgentCore Pricing**: Estimate costs for runtime, memory, tools, and gateway components
- **EMR Sizing**: Size and cost EMR clusters (EC2, Serverless, EKS)
- **Business Value Analysis**: Calculate ROI, cost savings, and revenue impact
- **What-If Analysis**: Compare scenarios and perform sensitivity analysis

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Application                       │
│ (Amazon Quick Suite, Claude Desktop, Custom App, etc.)      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS + OAuth2
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Amazon Cognito User Pool                       │
│                  (Authentication)                           │
└────────────────────────┬────────────────────────────────────┘
                         │ Bearer Token
                         │
┌────────────────────────▼────────────────────────────────────┐
│         Amazon Bedrock AgentCore Runtime                    │
│                                                             │
│  ┌────────────────────────────────────────────────────┐     │
│  │         Cost Analysis Agent (MCP Server)           │     │
│  │                                                    │     │
│  │  • Strands Agent with Claude Haiku 4.5             │     │
│  │  • 12 Tools for pricing and calculations           │     │
│  │  • FastMCP for MCP protocol                        │     │
│  └────────────────────────────────────────────────────┘     │
│                                                             │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐  ┌──────▼──────┐  ┌─────▼──────┐
│   Bedrock    │  │   Pricing   │  │ CloudWatch │
│   Models     │  │     API     │  │    Logs    │
└──────────────┘  └─────────────┘  └────────────┘
```

## Features

### Pricing Queries
- Real-time AWS pricing lookup for Bedrock, AgentCore, and EMR
- Support for multiple regions
- Fuzzy model name matching

### Cost Calculations
- **Bedrock**: Multi-model support, vector databases, tool invocations, conversation history
- **AgentCore**: Runtime, memory, browser tool, code interpreter, gateway, identity
- **EMR**: EC2, Serverless, and EKS deployment modes

### Business Value Analysis
- Cost savings from time efficiency
- Revenue growth from reallocated resources
- Customer churn reduction impact
- ROI calculations over time

### What-If Analysis
- 1D and 2D parameter sensitivity analysis
- Scenario comparison
- Heatmap-ready output

## Prerequisites

- **AWS Account** with appropriate permissions
- **Python 3.11+** installed
- **AWS CLI** configured with credentials
- **AgentCore CLI** installed (`pip install bedrock-agentcore-cli`)
- **Docker** (for local testing)

## Deployment Guide

### Step 1: Create IAM Role

Create an IAM role with permissions for Bedrock, Pricing API, and CloudWatch Logs:

```bash
# Navigate to the agent directory
cd usecases/mcp-aws-cost-analysis-agent

# Create the IAM role
python create_agentcore_iam_role.py

# Note the Role ARN from the output
# Example: arn:aws:iam::123456789012:role/CostAnalysisAgentCoreRole
```

**What this does:**
- Creates IAM role with trust policy for AgentCore
- Grants permissions to invoke Bedrock models (Claude)
- Grants permissions to access Pricing API
- Grants permissions to write CloudWatch Logs

**Output:**
```
✅ Role created successfully!
   Role ARN: arn:aws:iam::123456789012:role/CostAnalysisAgentCoreRole

💡 Use this role ARN when deploying to AgentCore:
   agentcore configure --execution-role-arn arn:aws:iam::123456789012:role/CostAnalysisAgentCoreRole ...
```

See [IAM_ROLE_GUIDE.md](IAM_ROLE_GUIDE.md) for detailed permissions information.

### Step 2: Configure Cognito User Pool (Optional)

For secure app-to-app integration, set up Amazon Cognito authentication:

#### 2.1 Create Cognito User Pool

1. Open **AWS Console** → **Amazon Cognito**
2. Click **Create user pool**
3. Configure sign-in options:
   - Select **Email** or **Username**
   - Click **Next**
4. Configure security requirements:
   - Password policy: Use defaults or customize
   - MFA: Optional (recommended for production)
   - Click **Next**
5. Configure sign-up experience:
   - Self-registration: **Disable** (for app-to-app)
   - Click **Next**
6. Configure message delivery:
   - Email provider: Use Cognito default or SES
   - Click **Next**
7. Integrate your app:
   - User pool name: `cost-analysis-agent-pool`
   - App client name: `cost-analysis-mcp-client`
   - Click **Next**
8. Review and create

#### 2.2 Create App Client for Machine-to-Machine

1. In your user pool, go to **App integration** tab
2. Click **Create app client**
3. Configure app client:
   - App type: **Confidential client**
   - App client name: `cost-analysis-m2m-client`
   - Authentication flows: **Client credentials** (OAuth 2.0)
   - OAuth 2.0 grant types: Select **Client credentials**
   - Custom scopes: Create a resource server first (see below)
4. Click **Create app client**
5. Note the **Client ID** and **Client Secret**

#### 2.3 Create Resource Server and Scopes

1. In user pool, go to **App integration** → **Resource servers**
2. Click **Create resource server**
3. Configure:
   - Name: `cost-analysis-api`
   - Identifier: `cost-analysis-api`
   - Custom scopes:
     - Scope name: `read`
     - Description: `Read access to cost analysis`
4. Click **Create**

#### 2.4 Update App Client with Scopes

1. Go back to your app client
2. Edit **Hosted UI** settings
3. Under **Allowed OAuth Scopes**, select:
   - `cost-analysis-api/read`
4. Save changes

#### 2.5 Get Token Endpoint

1. In user pool, go to **App integration** → **Domain**
2. If no domain exists, create one:
   - Domain prefix: `cost-analysis-agent-<random>`
   - Click **Create**
3. Note the domain: `https://cost-analysis-agent-<random>.auth.<region>.amazoncognito.com`
4. Token endpoint: `https://<domain>/oauth2/token`

#### 2.6 Store Credentials in Secrets Manager

```bash
# Store Cognito credentials for the agent to use
aws secretsmanager create-secret \
  --name cost-analysis-agent/cognito/credentials \
  --secret-string '{
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "token_endpoint": "https://your-domain.auth.region.amazoncognito.com/oauth2/token"
  }'
```

**For no-auth deployment** (testing only), skip this step and use `--no-auth` flag in Step 4.

### Step 3: Configure AgentCore Deployment

Configure the agent for deployment to AgentCore Runtime:

```bash
# Install dependencies
pip install -r requirements.txt

# Configure AgentCore deployment
agentcore configure \
  --entrypoint strands_cost_calc_agent.py \
  --name cost-analysis-agent \
  --execution-role-arn arn:aws:iam::123456789012:role/CostAnalysisAgentCoreRole \
  --region us-west-2 \
  --memory 2048 \
  --timeout 300
```

**Parameters:**
- `--entrypoint`: Python file containing the MCP server
- `--name`: Agent name (used in logs and URLs)
- `--execution-role-arn`: IAM role ARN from Step 1
- `--region`: AWS region for deployment
- `--memory`: Memory allocation in MB (2048 recommended)
- `--timeout`: Request timeout in seconds

**Optional parameters:**
```bash
# With authentication
agentcore configure \
  --entrypoint strands_cost_calc_agent.py \
  --name cost-analysis-agent \
  --execution-role-arn arn:aws:iam::123456789012:role/CostAnalysisAgentCoreRole \
  --region us-west-2 \
  --memory 2048 \
  --timeout 300 \
  --cognito-user-pool-id us-west-2_XXXXXXXXX \
  --cognito-client-id your-client-id

# Without authentication (testing only)
agentcore configure \
  --entrypoint strands_cost_calc_agent.py \
  --name cost-analysis-agent \
  --execution-role-arn arn:aws:iam::123456789012:role/CostAnalysisAgentCoreRole \
  --region us-west-2 \
  --memory 2048 \
  --timeout 300 \
  --no-auth
```

**Output:**
```
✅ Configuration saved to .bedrock_agentcore.yaml
```

### Step 4: Launch Agent on AgentCore

Deploy the agent to AgentCore Runtime:

```bash
# Launch the agent
agentcore launch --agent cost-analysis-agent

# This will:
# 1. Package the agent code and dependencies
# 2. Upload to AgentCore Runtime
# 3. Create the runtime environment
# 4. Deploy the MCP server
# 5. Return the agent ARN and endpoint URL
```

**Deployment takes 10-15 minutes.** Monitor progress:

```bash
# Check deployment status
agentcore status --agent cost-analysis-agent

# View logs
aws logs tail /aws/bedrock-agentcore/runtimes/cost-analysis-agent --follow
```

**Successful deployment output:**
```
✅ Agent deployed successfully!
   Agent ARN: arn:aws:bedrock-agentcore:us-west-2:123456789012:agent-runtime/cost-analysis-agent-xxxxx
   Endpoint: https://bedrock-agentcore.us-west-2.amazonaws.com/runtimes/...
   Status: READY
```

### Step 5: Test the Deployment

Test the deployed agent:

```bash
# Run the test client
python test_mcp_client.py

# Or test specific query
python test_mcp_client.py --query "Calculate Bedrock costs for 10,000 questions"
```

**With authentication:**
```bash
# Test with Cognito authentication (retrieves token automatically)
python test_mcp_client.py

# Test with manual bearer token
python test_mcp_client.py --bearer-token <your-token>
```

**Without authentication:**
```bash
python test_mcp_client.py --no-auth
```

See [README_TESTING.md](README_TESTING.md) for comprehensive testing guide.

## Local Development

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the MCP server locally
python strands_cost_calc_agent.py

# In another terminal, test it
python test_local_mcp_server.py
```

### Direct Testing (No MCP Server)

```bash
# Test agent directly without MCP protocol
python test_direct_function_calls.py

# Interactive mode
python test_direct_function_calls.py --interactive

# Single query
python test_direct_function_calls.py --query "Calculate Bedrock costs"
```

## Usage Examples

### Example 1: Bedrock Cost Calculation

**Query:**
```
Calculate Bedrock costs for 10,000 questions per month using Claude Haiku 
with 1000 input tokens and 500 output tokens per question
```

**Response:**
```json
{
  "BEDROCK_COSTS": {
    "models": {
      "model1": {
        "model_name": "claude-3-haiku",
        "input_cost": 2.50,
        "output_cost": 6.25,
        "total_cost": 8.75
      }
    },
    "total_monthly_cost": 8.75
  }
}
```

### Example 2: AgentCore Cost Calculation

**Query:**
```
Calculate AgentCore costs for an agent that runs 100 hours per month 
with 2GB memory and handles 10,000 requests
```

**Response:**
```json
{
  "AGENTCORE_COSTS": {
    "runtime_cost": 17.90,
    "memory_cost": 2.50,
    "total_monthly_cost": 20.40
  }
}
```

### Example 3: Business Value Analysis

**Query:**
```
What's the ROI if I process 10,000 questions per month, save 10 minutes 
per question, and my labor cost is $50/hour? The AI agent costs $500/month.
```

**Response:**
```json
{
  "BUSINESS_VALUE": {
    "cost_savings": {
      "hours_saved_per_month": 1666.67,
      "costs_saved_per_month": 83333.33
    },
    "total_costs": 6000.00,
    "net_value": 994000.00,
    "roi_percent": 16566.67
  }
}
```

## Available Tools

The agent provides 12 tools:

### Pricing Tools
1. `get_bedrock_pricing` - Get Bedrock model pricing
2. `get_agentcore_pricing` - Get AgentCore component pricing
3. `get_aws_pricing` - Get AWS service pricing (generic)
4. `get_attribute_values` - Get pricing attribute values

### Calculator Tools
5. `use_bedrock_calculator` - Calculate Bedrock costs
6. `bedrock_what_if_analysis` - Bedrock scenario analysis
7. `use_agentcore_calculator` - Calculate AgentCore costs
8. `agentcore_what_if_analysis` - AgentCore scenario analysis
9. `use_emr_calculator` - Size and cost EMR clusters
10. `emr_what_if_analysis` - EMR scenario analysis
11. `bva_calculator` - Business value analysis
12. `bva_what_if_analysis` - Business value scenario analysis

## Configuration Files

### `.bedrock_agentcore.yaml`

Created by `agentcore configure`, contains deployment configuration:

```yaml
agents:
  cost-analysis-agent:
    entrypoint: strands_cost_calc_agent.py
    execution_role_arn: arn:aws:iam::123456789012:role/CostAnalysisAgentCoreRole
    region: us-west-2
    memory: 2048
    timeout: 300
    bedrock_agentcore:
      agent_arn: arn:aws:bedrock-agentcore:us-west-2:123456789012:agent-runtime/...
      status: READY
```

### `requirements.txt`

Python dependencies:

```
strands-agents>=1.12.0
strands-agents-tools>=0.2.11
fastmcp
mcp
boto3
botocore
pydantic
pyyaml
requests
```

## Monitoring and Troubleshooting

### View Logs

```bash
# Tail logs in real-time
aws logs tail /aws/bedrock-agentcore/runtimes/cost-analysis-agent --follow

# Get recent logs
aws logs tail /aws/bedrock-agentcore/runtimes/cost-analysis-agent --since 1h

# Filter for errors
aws logs tail /aws/bedrock-agentcore/runtimes/cost-analysis-agent --filter-pattern "ERROR"
```

### Check Agent Status

```bash
# Get agent status
agentcore status --agent cost-analysis-agent

# Get detailed status
agentcore status --agent cost-analysis-agent --verbose
```

### Common Issues

#### 1. Agent Not Ready

**Symptom:** Status shows `CREATING` or `UPDATING`

**Solution:** Wait 10-15 minutes for deployment to complete

#### 2. Authentication Errors

**Symptom:** `403 Forbidden` or `401 Unauthorized`

**Solutions:**
- Verify Cognito configuration
- Check bearer token is valid
- Ensure app client has correct scopes
- For testing, use `--no-auth` flag

#### 3. Bedrock Model Access Denied

**Symptom:** `AccessDeniedException` when invoking models

**Solutions:**
- Verify IAM role has `bedrock:InvokeModel` permission
- Enable model access in Bedrock console
- Check model is available in your region

#### 4. Pricing API Errors

**Symptom:** Empty pricing results or API errors

**Solutions:**
- Verify IAM role has `pricing:GetProducts` permission
- Remember: Pricing API only works from `us-east-1`
- Check CloudWatch Logs for detailed errors

## Cost Considerations

### AgentCore Runtime Costs

- **vCPU-Hour**: ~$0.09 per vCPU-hour
- **Memory**: ~$0.01 per GB-hour
- **Requests**: Minimal (included in runtime)

**Example:** Agent with 2 vCPUs, 2GB memory, running 100 hours/month:
- vCPU cost: 2 × $0.09 × 100 = $18.00
- Memory cost: 2 × $0.01 × 100 = $2.00
- **Total: ~$20/month**

### Bedrock Model Costs

- **Claude Haiku 4.5**: ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens
- **Example:** 10,000 questions with 1000 input + 500 output tokens each:
  - Input: 10M tokens × $0.25 = $2.50
  - Output: 5M tokens × $1.25 = $6.25
  - **Total: ~$8.75/month**

### Total Estimated Cost

For moderate usage (10,000 questions/month):
- AgentCore Runtime: ~$20
- Bedrock Models: ~$9
- CloudWatch Logs: ~$1
- **Total: ~$30/month**

## Security Best Practices

1. **Use Cognito Authentication** for production deployments
2. **Rotate Credentials** regularly (client secrets, tokens)
3. **Monitor Access** through CloudTrail and CloudWatch
4. **Restrict IAM Permissions** to minimum required
5. **Enable MFA** for Cognito user pool (if using user authentication)
6. **Use VPC Endpoints** for private connectivity (optional)
7. **Encrypt Secrets** in Secrets Manager
8. **Review Logs** regularly for suspicious activity

## Updating the Agent

To update the agent code:

```bash
# Make your code changes
# Then redeploy
agentcore launch --agent cost-analysis-agent

# Monitor the update
agentcore status --agent cost-analysis-agent --verbose
```

## Deleting the Agent

To remove the agent and clean up resources:

```bash
# Delete the agent
agentcore delete --agent cost-analysis-agent

# Delete the IAM role
python create_agentcore_iam_role.py --delete --role-name CostAnalysisAgentCoreRole

# Delete Cognito resources (manual via console)
# Delete Secrets Manager secrets (manual or via CLI)
```

## Additional Resources

- [IAM Role Guide](IAM_ROLE_GUIDE.md) - Detailed IAM permissions
- [Testing Guide](README_TESTING.md) - Comprehensive testing instructions
- [User Guide](USER_GUIDE.md) - End-user documentation
- [AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Strands Agents Documentation](https://docs.strands.ai/)

## Support

For issues or questions:
1. Check CloudWatch Logs for errors
2. Review the troubleshooting section above
3. Verify IAM permissions and Cognito configuration
4. Test locally before deploying to AgentCore

## License

MIT License - See LICENSE file for details
