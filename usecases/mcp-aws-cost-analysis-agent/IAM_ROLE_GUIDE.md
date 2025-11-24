# IAM Role Guide for AgentCore Runtime

This guide explains the IAM permissions required for the Cost Analysis Agent to run on Amazon Bedrock AgentCore Runtime.

## Quick Start

Create the IAM role with default settings:

```bash
python create_agentcore_iam_role.py
```

This creates a role named `CostAnalysisAgentCoreRole` with all necessary permissions.

## Required Permissions

The Cost Analysis Agent requires access to three AWS services:

### 1. Amazon Bedrock (Foundation Models)

**Why needed:** The agent uses Claude models for reasoning and generating cost analysis responses.

**Permissions:**
- `bedrock:InvokeModel` - Invoke foundation models
- `bedrock:InvokeModelWithResponseStream` - Stream responses from models

**Resources:**
- `arn:aws:bedrock:*::foundation-model/anthropic.claude-*`
- `arn:aws:bedrock:us-*::foundation-model/us.anthropic.claude-*`

**Model used:** `us.anthropic.claude-haiku-4-5-20251001-v1:0`

### 2. AWS Pricing API

**Why needed:** The agent retrieves real-time AWS pricing information for:
- Amazon Bedrock models (input/output token costs)
- Amazon Bedrock AgentCore components (runtime, memory, tools)
- Amazon EMR (EC2, Serverless, EKS pricing)
- Other AWS services as needed

**Permissions:**
- `pricing:GetProducts` - Get product pricing information
- `pricing:GetAttributeValues` - Get attribute values for filtering
- `pricing:DescribeServices` - List available services

**Resources:** `*` (Pricing API doesn't support resource-level permissions)

**Note:** Pricing API calls are always made to `us-east-1` region regardless of where the agent runs.

### 3. Amazon CloudWatch Logs

**Why needed:** AgentCore Runtime writes execution logs for monitoring and debugging.

**Permissions:**
- `logs:CreateLogGroup` - Create log groups
- `logs:CreateLogStream` - Create log streams
- `logs:PutLogEvents` - Write log events

**Resources:** `arn:aws:logs:*:*:log-group:/aws/bedrock-agentcore/*`

## Usage Examples

### Create Role with Default Name

```bash
python create_agentcore_iam_role.py
```

Output:
```
Role Name: CostAnalysisAgentCoreRole
Role ARN: arn:aws:iam::123456789012:role/CostAnalysisAgentCoreRole
```

### Create Role with Custom Name

```bash
python create_agentcore_iam_role.py --role-name MyCustomAgentRole
```

### Create Role in Specific Region

```bash
python create_agentcore_iam_role.py --region us-east-1
```

### Preview Permissions (Dry Run)

```bash
python create_agentcore_iam_role.py --dry-run
```

This shows the trust policy and permissions policy without creating anything.

### Update Existing Role

If the role already exists, the script will ask if you want to update the permissions:

```bash
python create_agentcore_iam_role.py --role-name ExistingRole
```

### Delete Role

```bash
python create_agentcore_iam_role.py --delete --role-name MyRole
```

## Using the Role with AgentCore

After creating the role, use it when deploying to AgentCore:

```bash
agentcore configure \
  --entrypoint strands_cost_calc_agent.py \
  --name cost-analysis-agent \
  --execution-role-arn arn:aws:iam::123456789012:role/CostAnalysisAgentCoreRole \
  --region us-west-2
```

## Trust Policy

The role trusts the AgentCore service to assume it:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## Permissions Policy

The role has an inline policy with three statement IDs:

### BedrockModelInvocation

Allows invoking Claude models for agent reasoning.

### PricingAPIAccess

Allows retrieving AWS pricing information for cost calculations.

### CloudWatchLogsAccess

Allows writing execution logs to CloudWatch.

## Security Best Practices

### Principle of Least Privilege

The role grants only the minimum permissions needed:
- Bedrock access is limited to Claude models only
- CloudWatch Logs access is limited to AgentCore log groups
- Pricing API requires wildcard resource (service limitation)

### Resource Restrictions

Where possible, permissions are restricted to specific resources:
- Bedrock: Only Claude model ARNs
- CloudWatch Logs: Only `/aws/bedrock-agentcore/*` log groups

### Monitoring

Monitor role usage through:
- CloudTrail logs for API calls
- CloudWatch Logs for agent execution
- IAM Access Analyzer for permission usage

## Troubleshooting

### Access Denied Errors

If you get access denied when creating the role:

```
❌ Access Denied: You don't have permission to create IAM roles
```

You need these IAM permissions:
- `iam:CreateRole`
- `iam:PutRolePolicy`
- `iam:TagRole`

### Role Already Exists

If the role already exists, the script will:
1. Detect the existing role
2. Show the current ARN
3. Ask if you want to update the permissions policy

### Bedrock Model Access Denied

If the agent can't invoke Bedrock models:

1. Verify the role has `bedrock:InvokeModel` permission
2. Check the model ARN matches the pattern in the policy
3. Ensure Bedrock is enabled in your region
4. Verify model access is granted in Bedrock console

### Pricing API Errors

If pricing lookups fail:

1. Verify `pricing:GetProducts` permission exists
2. Remember: Pricing API only works from `us-east-1`
3. Check CloudWatch Logs for detailed error messages

## Cost Considerations

### IAM Role Costs

IAM roles are free - no charges for creating or using them.

### API Call Costs

The agent makes API calls that may incur costs:

1. **Bedrock Model Invocation**
   - Charged per input/output token
   - Claude Haiku: ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens

2. **Pricing API**
   - Free - no charges for pricing API calls

3. **CloudWatch Logs**
   - Charged for log ingestion and storage
   - Typically minimal for agent logs

## Additional Resources

- [Amazon Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [AWS Pricing API Documentation](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/price-changes.html)
- [IAM Roles for Services](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-service.html)
- [AgentCore Runtime Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)

## Support

For issues or questions:
1. Check CloudWatch Logs for agent execution errors
2. Review IAM role permissions in AWS Console
3. Verify Bedrock model access in Bedrock console
4. Check the agent code for required AWS service calls
