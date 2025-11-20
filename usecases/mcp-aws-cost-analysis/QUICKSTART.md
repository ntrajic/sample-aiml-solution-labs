# Quick Start - Deploy AWS Cost Analysis MCP Server

## Three-Step Deployment

### Step 1: Setup Prerequisites

```bash
cd usecases/mcp-aws-cost-analysis
python run_prerequisite.py
```

This creates:
- ✅ IAM execution role with Pricing API permissions
- ✅ Cognito user pool for authentication
- ✅ Stores configuration in AWS
- ✅ **Generates `agentcore_commands.sh` with ready-to-run commands**

**Time:** ~30 seconds

### Step 2: Run the Generated Commands

The script outputs commands with your actual configuration. Either:

**Option A: Copy-paste from terminal output**
```bash
# The script prints commands like:
agentcore configure \
  --entrypoint cost_analysis_fastmcp_server.py \
  --name aws_cost_analysis_mcp \
  --execution-role arn:aws:iam::YOUR_ACCOUNT:role/agentcore-aws_cost_analysis_mcp-role \
  --region us-west-2 \
  --protocol MCP \
  --requirements-file requirements.txt \
  --disable-memory \
  --authorizer-config '{"customJWTAuthorizer": {...}}' \
  --non-interactive

agentcore launch --agent aws_cost_analysis_mcp
```

**Option B: Run the generated script**
```bash
bash agentcore_commands.sh
```

**Time:** 10-15 minutes (mostly waiting for launch)

### Step 3: Test Your Deployment

```bash
python test_mcp_client.py
```

Or if you ran the script:
```bash
# The script already includes this command
```

## What You Get

### 11 MCP Tools for Cost Analysis

1. **get_bedrock_pricing_tool_read_only** - Bedrock model pricing
2. **get_agentcore_pricing_tool_read_only** - AgentCore pricing
3. **get_aws_pricing_tool_read_only** - AWS service pricing
4. **get_attribute_values_tool_read_only** - Pricing attributes
5. **bedrock_calculator_tool_read_only** - Cost calculations
6. **bedrock_what_if_tool_read_only** - What-if analysis
7. **agentcore_calculator_tool_read_only** - AgentCore costs
8. **agentcore_what_if_tool_read_only** - AgentCore what-if
9. **business_value_calculator_tool_read_only** - ROI analysis
10. **business_value_what_if_tool_read_only** - Business value
11. **health_check** - Server status

## View Logs

```bash
aws logs tail /aws/bedrock-agentcore/runtimes/aws_cost_analysis_mcp --follow
```

## Check Status

```bash
agentcore status --agent aws_cost_analysis_mcp
```

## Cleanup

```bash
# Destroy AgentCore resources
agentcore destroy --agent aws_cost_analysis_mcp --force

# Delete IAM role
aws iam delete-role-policy \
  --role-name agentcore-aws_cost_analysis_mcp-role \
  --policy-name AgentCorePolicy
aws iam delete-role --role-name agentcore-aws_cost_analysis_mcp-role

# Delete Cognito user pool (get pool ID from run_prerequisite.py output)
aws cognito-idp delete-user-pool --user-pool-id us-west-2_xxxxx

# Delete Secrets Manager secret
aws secretsmanager delete-secret \
  --secret-id aws_cost_analysis_mcp/cognito/credentials \
  --force-delete-without-recovery
```

## Prerequisites

```bash
# Install AgentCore Toolkit
pip install bedrock-agentcore-starter-toolkit boto3 mcp requests

# Configure AWS credentials
aws configure

# Ensure Docker is running (for local builds)
docker --version
```

## Options

### Deploy Without Authentication

```bash
# Step 1: Skip Cognito
python run_prerequisite.py --no-cognito

# Step 2: Configure without auth
agentcore configure \
  --entrypoint cost_analysis_fastmcp_server.py \
  --name aws_cost_analysis_mcp \
  --execution-role <ROLE_ARN> \
  --region us-west-2 \
  --protocol MCP \
  --requirements-file requirements.txt \
  --disable-memory \
  --non-interactive

# Step 3: Launch
agentcore launch --agent aws_cost_analysis_mcp

# Test without auth
python test_mcp_client.py --no-auth
```

### Use Different Region

```bash
python run_prerequisite.py --region us-east-1
```

## Troubleshooting

**Prerequisites fail?**
- Check AWS credentials: `aws sts get-caller-identity`
- Verify permissions to create IAM roles and Cognito resources

**Launch fails?**
- Check Docker is running: `docker ps`
- View CodeBuild logs in AWS Console
- Try local build: `agentcore launch --local-build`

**Test fails?**
- Check runtime status: `agentcore status --agent aws_cost_analysis_mcp`
- View logs: `aws logs tail /aws/bedrock-agentcore/runtimes/aws_cost_analysis_mcp --follow`
- Verify authentication: Token may have expired

**Import errors?**
- Ensure all files in `utils/` directory exist
- Check `requirements.txt` is complete

## Full Documentation

See [README_DEPLOYMENT.md](README_DEPLOYMENT.md) for:
- Architecture details
- IAM permissions analysis
- Advanced configuration
- Security best practices
- Integration examples
