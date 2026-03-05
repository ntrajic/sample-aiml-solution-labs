"""
AgentCore Identity & IAM Handlers

Implementation of handlers for generating IAM role and Cognito resource creation scripts.
"""

from typing import Dict


async def handle_create_runtime_execution_role_script(args: Dict) -> Dict:
    """Generate script to create IAM execution role for AgentCore Runtime"""
    
    region = args.get("region", "us-west-2")
    
    # Generate Python script code with validated minimal permissions
    code = f'''#!/usr/bin/env python3
"""
Script to create IAM execution role for AgentCore Runtime.

This script creates an IAM role with minimal required permissions for running
agents in AgentCore Runtime.
"""

import json
import boto3
import time

# Configuration
REGION = "{region}"
ROLE_NAME = f"AgentCoreRuntimeExecutionRole-{{int(time.time())}}"
POLICY_NAME = f"AgentCoreRuntimePolicy-{{int(time.time())}}"

# Create IAM client
iam_client = boto3.client('iam', region_name=REGION)

print("Creating IAM Execution Role for AgentCore Runtime")
print("=" * 80)

# Get AWS account ID
sts_client = boto3.client('sts', region_name=REGION)
account_id = sts_client.get_caller_identity()['Account']
print(f"\\nAWS Account: {{account_id}}")
print(f"Region: {{REGION}}")

# Step 1: Define trust policy for bedrock-agentcore.amazonaws.com
print("\\n1. Creating IAM role with trust policy...")
trust_policy = {{
    "Version": "2012-10-17",
    "Statement": [
        {{
            "Effect": "Allow",
            "Principal": {{
                "Service": "bedrock-agentcore.amazonaws.com"
            }},
            "Action": "sts:AssumeRole"
        }}
    ]
}}

try:
    role_response = iam_client.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description="Execution role for AgentCore Runtime with minimal required permissions"
    )
    role_arn = role_response['Role']['Arn']
    print(f"   ✓ Role created: {{ROLE_NAME}}")
    print(f"   ✓ Role ARN: {{role_arn}}")
except Exception as e:
    print(f"   ✗ Error creating role: {{e}}")
    exit(1)

# Step 2: Create comprehensive permissions policy with minimal required permissions
print("\\n2. Creating permissions policy...")
permissions_policy = {{
    "Version": "2012-10-17",
    "Statement": [
        {{
            "Sid": "ECRAccess",
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage"
            ],
            "Resource": "*"
        }},
        {{
            "Sid": "CloudWatchLogsAccess",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams",
                "logs:DescribeLogGroups"
            ],
            "Resource": [
                f"arn:aws:logs:{{REGION}}:{{account_id}}:log-group:/aws/bedrock-agentcore/*",
                f"arn:aws:logs:{{REGION}}:{{account_id}}:log-group:*"
            ]
        }},
        {{
            "Sid": "XRayAccess",
            "Effect": "Allow",
            "Action": [
                "xray:PutTraceSegments",
                "xray:PutTelemetryRecords",
                "xray:GetSamplingRules",
                "xray:GetSamplingTargets"
            ],
            "Resource": "*"
        }},
        {{
            "Sid": "CloudWatchMetrics",
            "Effect": "Allow",
            "Action": "cloudwatch:PutMetricData",
            "Resource": "*",
            "Condition": {{
                "StringEquals": {{
                    "cloudwatch:namespace": "bedrock-agentcore"
                }}
            }}
        }},
        {{
            "Sid": "BedrockModelAccess",
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:ApplyGuardrail",
                "bedrock:Retrieve"
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/*",
                f"arn:aws:bedrock:{{REGION}}:{{account_id}}:*"
            ]
        }},
        {{
            "Sid": "AgentCoreMemoryAccess",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:CreateEvent",
                "bedrock-agentcore:ListEvents",
                "bedrock-agentcore:GetMemoryRecord",
                "bedrock-agentcore:GetMemory",
                "bedrock-agentcore:RetrieveMemoryRecords",
                "bedrock-agentcore:ListMemoryRecords"
            ],
            "Resource": f"arn:aws:bedrock-agentcore:{{REGION}}:{{account_id}}:*"
        }},
        {{
            "Sid": "WorkloadIdentityAccess",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:GetWorkloadAccessToken",
                "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                "bedrock-agentcore:GetWorkloadAccessTokenForUserId"
            ],
            "Resource": [
                f"arn:aws:bedrock-agentcore:{{REGION}}:{{account_id}}:workload-identity-directory/default",
                f"arn:aws:bedrock-agentcore:{{REGION}}:{{account_id}}:workload-identity-directory/default/workload-identity/*"
            ]
        }},
        {{
            "Sid": "STSAccess",
            "Effect": "Allow",
            "Action": [
                "sts:AssumeRole",
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        }},
        {{
            "Sid": "SSMParameterAccess",
            "Effect": "Allow",
            "Action": "ssm:GetParameter",
            "Resource": f"arn:aws:ssm:{{REGION}}:{{account_id}}:parameter/app/*"
        }},
        {{
            "Sid": "MarketplaceAccess",
            "Effect": "Allow",
            "Action": [
                "aws-marketplace:ViewSubscriptions",
                "aws-marketplace:Subscribe"
            ],
            "Resource": "*"
        }}
    ]
}}

try:
    policy_response = iam_client.create_policy(
        PolicyName=POLICY_NAME,
        PolicyDocument=json.dumps(permissions_policy),
        Description="Minimal required permissions for AgentCore Runtime"
    )
    policy_arn = policy_response['Policy']['Arn']
    print(f"   ✓ Policy created: {{POLICY_NAME}}")
    print(f"   ✓ Policy ARN: {{policy_arn}}")
except Exception as e:
    print(f"   ✗ Error creating policy: {{e}}")
    print(f"   Cleaning up role: {{ROLE_NAME}}")
    try:
        iam_client.delete_role(RoleName=ROLE_NAME)
    except:
        pass
    exit(1)

# Step 3: Attach policy to role
print("\\n3. Attaching policy to role...")
try:
    iam_client.attach_role_policy(
        RoleName=ROLE_NAME,
        PolicyArn=policy_arn
    )
    print(f"   ✓ Policy attached to role")
except Exception as e:
    print(f"   ✗ Error attaching policy: {{e}}")
    print(f"   Cleaning up resources...")
    try:
        iam_client.delete_policy(PolicyArn=policy_arn)
        iam_client.delete_role(RoleName=ROLE_NAME)
    except:
        pass
    exit(1)

# Step 4: Wait for role to propagate using waiter
print("\\n4. Waiting for role to propagate...")
try:
    waiter = iam_client.get_waiter('role_exists')
    waiter.wait(RoleName=ROLE_NAME)
    print("   ✓ Role propagation confirmed")
except Exception as e:
    print(f"   ⚠️  Waiter not available, using 10-second sleep: {{e}}")
    time.sleep(10)
    print("   ✓ Role propagation wait complete")

# Save configuration
config = {{
    "role_name": ROLE_NAME,
    "role_arn": role_arn,
    "policy_name": POLICY_NAME,
    "policy_arn": policy_arn,
    "region": REGION
}}

with open('runtime_execution_role_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("\\n" + "=" * 80)
print("✓ Runtime execution role setup complete!")
print(f"\\nConfiguration saved to runtime_execution_role_config.json:")
print(f"  Role Name: {{ROLE_NAME}}")
print(f"  Role ARN: {{role_arn}}")
print(f"  Policy ARN: {{policy_arn}}")
print("\\nPermissions granted:")
print("  ✓ ECR - Pull container images")
print("  ✓ CloudWatch Logs - Write and read logs")
print("  ✓ X-Ray - Distributed tracing")
print("  ✓ CloudWatch Metrics - Performance monitoring")
print("  ✓ Bedrock - Invoke models and guardrails")
print("  ✓ AgentCore Memory - Store/retrieve conversation history")
print("  ✓ Workload Identity - Secure credential management")
print("  ✓ STS - Role assumption and identity")
print("  ✓ SSM Parameter Store - Configuration access")
print("  ✓ AWS Marketplace - Model subscriptions")
print("\\nThis role will be used for runtime deployment.")
'''
    
    return {
        "code": code,
        "filename": "create_runtime_execution_role.py",
        "instructions": "Run this script to create the IAM execution role with minimal required permissions"
    }
