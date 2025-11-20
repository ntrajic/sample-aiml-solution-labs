#!/usr/bin/env python3
"""
Setup Prerequisites for AWS Cost Analysis MCP Server Deployment

This script creates the necessary AWS resources before deploying to AgentCore Runtime:
1. IAM execution role with Pricing API permissions
2. Cognito user pool with app client for authentication (optional)
3. Stores configuration for easy access

After running this script, use the agentcore CLI to deploy:
  agentcore configure --entrypoint cost_analysis_fastmcp_server.py ...
  agentcore launch
"""

import boto3
import json
import time
import sys
import argparse
from pathlib import Path
from boto3.session import Session

# Configuration
AGENT_NAME = "aws_cost_analysis_mcp"


def create_iam_role(agent_name, region):
    """
    Create IAM role with required permissions for AgentCore Runtime.
    
    Includes:
    - AWS Pricing API permissions (read-only)
    - Standard AgentCore Runtime permissions
    
    Args:
        agent_name: Name of the agent for role naming
        region: AWS region
        
    Returns:
        str: IAM role ARN
    """
    iam_client = boto3.client("iam")
    agentcore_role_name = f"agentcore-{agent_name}-role"
    account_id = boto3.client("sts").get_caller_identity()["Account"]
    
    print(f"\n🔑 Creating IAM role: {agentcore_role_name}")
    
    # IAM policy with Pricing API + standard AgentCore permissions
    role_policy = {
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
            },
            {
                "Sid": "BedrockPermissions",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                "Resource": "*",
            },
            {
                "Sid": "ECRImageAccess",
                "Effect": "Allow",
                "Action": [
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:GetAuthorizationToken",
                ],
                "Resource": [f"arn:aws:ecr:{region}:{account_id}:repository/*"],
            },
            {
                "Effect": "Allow",
                "Action": ["logs:DescribeLogStreams", "logs:CreateLogGroup"],
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*"
                ],
            },
            {
                "Effect": "Allow",
                "Action": ["logs:DescribeLogGroups"],
                "Resource": [f"arn:aws:logs:{region}:{account_id}:log-group:*"],
            },
            {
                "Effect": "Allow",
                "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
                ],
            },
            {
                "Sid": "ECRTokenAccess",
                "Effect": "Allow",
                "Action": ["ecr:GetAuthorizationToken"],
                "Resource": "*",
            },
            {
                "Effect": "Allow",
                "Action": [
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets",
                ],
                "Resource": ["*"],
            },
            {
                "Effect": "Allow",
                "Resource": "*",
                "Action": "cloudwatch:PutMetricData",
                "Condition": {
                    "StringEquals": {"cloudwatch:namespace": "bedrock-agentcore"}
                },
            },
            {
                "Sid": "GetAgentAccessToken",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:GetWorkloadAccessToken",
                    "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                    "bedrock-agentcore:GetWorkloadAccessTokenForUserId",
                ],
                "Resource": [
                    f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/default",
                    f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/default/workload-identity/{agent_name}-*",
                ],
            },
        ],
    }
    
    # Trust policy for AgentCore service
    assume_role_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AssumeRolePolicy",
                "Effect": "Allow",
                "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {"aws:SourceAccount": f"{account_id}"},
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:bedrock-agentcore:{region}:{account_id}:*"
                    },
                },
            }
        ],
    }

    assume_role_policy_document_json = json.dumps(assume_role_policy_document)
    role_policy_document = json.dumps(role_policy)
    
    # Create or update IAM Role
    try:
        agentcore_iam_role = iam_client.create_role(
            RoleName=agentcore_role_name,
            AssumeRolePolicyDocument=assume_role_policy_document_json,
        )
        print(f"✓ Created IAM role: {agentcore_role_name}")
        time.sleep(10)  # Wait for role to propagate
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"⚠️  Role {agentcore_role_name} already exists - updating policies")
        # Delete existing inline policies
        policies = iam_client.list_role_policies(
            RoleName=agentcore_role_name, MaxItems=100
        )
        for policy_name in policies["PolicyNames"]:
            iam_client.delete_role_policy(
                RoleName=agentcore_role_name, PolicyName=policy_name
            )
        
        # Get existing role
        agentcore_iam_role = iam_client.get_role(RoleName=agentcore_role_name)

    # Attach the policy
    print(f"✓ Attaching policy to role")
    iam_client.put_role_policy(
        PolicyDocument=role_policy_document,
        PolicyName="AgentCorePolicy",
        RoleName=agentcore_role_name,
    )
    
    role_arn = agentcore_iam_role['Role']['Arn']
    print(f"✓ IAM role configured successfully")
    print(f"  Role ARN: {role_arn}")
    
    return role_arn


def setup_cognito(agent_name, region, pool_name="AWSCostAnalysisMCPPool"):
    """
    Create Cognito user pool with app client for app-to-app authentication.
    Uses client credentials flow (no user passwords).
    
    Args:
        agent_name: Name of the agent
        region: AWS region
        pool_name: Name for the Cognito user pool
        
    Returns:
        dict: Cognito configuration with pool_id, client_id, client_secret, etc.
    """
    cognito_client = boto3.client("cognito-idp", region_name=region)
    
    print("\n🔐 Setting up Amazon Cognito for app-to-app authentication...")
    
    try:
        # Create User Pool
        user_pool_response = cognito_client.create_user_pool(
            PoolName=pool_name,
            Policies={"PasswordPolicy": {"MinimumLength": 8}}
        )
        pool_id = user_pool_response["UserPool"]["Id"]
        print(f"✓ Created user pool: {pool_id}")
        
        # Create Resource Server for OAuth scopes
        resource_server_response = cognito_client.create_resource_server(
            UserPoolId=pool_id,
            Identifier=f"{agent_name}-api",
            Name=f"{agent_name} API",
            Scopes=[
                {
                    'ScopeName': 'invoke',
                    'ScopeDescription': 'Invoke MCP tools'
                }
            ]
        )
        print(f"✓ Created resource server")
        
        # Create App Client with client credentials
        app_client_response = cognito_client.create_user_pool_client(
            UserPoolId=pool_id,
            ClientName=f"{pool_name}Client",
            GenerateSecret=True,  # Generate client secret for app-to-app
            AllowedOAuthFlows=["client_credentials"],
            AllowedOAuthScopes=[f"{agent_name}-api/invoke"],
            AllowedOAuthFlowsUserPoolClient=True
        )
        client_id = app_client_response["UserPoolClient"]["ClientId"]
        client_secret = app_client_response["UserPoolClient"]["ClientSecret"]
        print(f"✓ Created app client with client credentials: {client_id}")
        
        # Create User Pool Domain for OAuth endpoints
        domain_base = agent_name.replace('_', '-').replace('aws-', '').replace('-aws', '')
        domain_name = f"{domain_base}-{pool_id.split('_')[1]}"
        try:
            cognito_client.create_user_pool_domain(
                Domain=domain_name,
                UserPoolId=pool_id
            )
            print(f"✓ Created user pool domain: {domain_name}")
        except cognito_client.exceptions.InvalidParameterException:
            # Domain might already exist, try with timestamp
            domain_name = f"cost-analysis-mcp-{int(time.time())}"
            cognito_client.create_user_pool_domain(
                Domain=domain_name,
                UserPoolId=pool_id
            )
            print(f"✓ Created user pool domain: {domain_name}")
        
        discovery_url = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/openid-configuration"
        token_endpoint = f"https://{domain_name}.auth.{region}.amazoncognito.com/oauth2/token"
        
        print(f"\nCognito Configuration:")
        print(f"  Pool ID: {pool_id}")
        print(f"  Client ID: {client_id}")
        print(f"  Domain: {domain_name}")
        print(f"  Token Endpoint: {token_endpoint}")
        print(f"  Discovery URL: {discovery_url}")
        
        return {
            "pool_id": pool_id,
            "client_id": client_id,
            "client_secret": client_secret,
            "domain": domain_name,
            "token_endpoint": token_endpoint,
            "discovery_url": discovery_url,
            "region": region
        }
    except Exception as e:
        print(f"❌ Error setting up Cognito: {e}")
        raise


def store_configuration(role_arn, cognito_config, region, agent_name):
    """
    Store configuration in AWS Systems Manager and Secrets Manager.
    
    Args:
        role_arn: IAM role ARN
        cognito_config: Cognito configuration dictionary
        region: AWS region
        agent_name: Agent name
    """
    print(f"\n💾 Storing configuration...")
    
    ssm_client = boto3.client('ssm', region_name=region)
    secrets_client = boto3.client('secretsmanager', region_name=region)
    
    # Store IAM role ARN in Parameter Store
    ssm_client.put_parameter(
        Name=f'/app/{agent_name}/iam_role_arn',
        Value=role_arn,
        Type='String',
        Description=f'IAM execution role ARN for {agent_name}',
        Overwrite=True
    )
    print(f"✓ IAM role ARN stored in Parameter Store")
    print(f"  Parameter: /app/{agent_name}/iam_role_arn")
    
    # Store Cognito credentials in Secrets Manager
    if cognito_config:
        try:
            secrets_client.create_secret(
                Name=f'{agent_name}/cognito/credentials',
                Description=f'Cognito credentials for {agent_name}',
                SecretString=json.dumps(cognito_config)
            )
            print(f"✓ Cognito credentials stored in Secrets Manager")
        except secrets_client.exceptions.ResourceExistsException:
            secrets_client.update_secret(
                SecretId=f'{agent_name}/cognito/credentials',
                SecretString=json.dumps(cognito_config)
            )
            print(f"✓ Cognito credentials updated in Secrets Manager")
        print(f"  Secret: {agent_name}/cognito/credentials")


def print_next_steps(role_arn, cognito_config, region, agent_name):
    """Print instructions for deploying with agentcore CLI."""
    print("\n" + "="*80)
    print("✅ PREREQUISITES SETUP COMPLETE!")
    print("="*80)
    
    print(f"\n📋 Configuration Summary:")
    print(f"  Agent Name: {agent_name}")
    print(f"  Region: {region}")
    print(f"  IAM Role ARN: {role_arn}")
    if cognito_config:
        print(f"  Cognito Pool ID: {cognito_config['pool_id']}")
        print(f"  Cognito Client ID: {cognito_config['client_id']}")
        print(f"  Discovery URL: {cognito_config['discovery_url']}")
    
    print("\n" + "="*80)
    print("NEXT STEPS: Deploy with AgentCore CLI")
    print("="*80)
    
    print("\n📝 COPY AND PASTE THESE COMMANDS:\n")
    
    print("# Step 1: Configure the deployment")
    configure_cmd = f"agentcore configure \\\n"
    configure_cmd += f"  --entrypoint cost_analysis_fastmcp_server.py \\\n"
    configure_cmd += f"  --name {agent_name} \\\n"
    configure_cmd += f"  --execution-role {role_arn} \\\n"
    configure_cmd += f"  --region {region} \\\n"
    configure_cmd += f"  --protocol MCP \\\n"
    configure_cmd += f"  --requirements-file requirements.txt \\\n"
    configure_cmd += f"  --disable-memory"
    
    if cognito_config:
        auth_config = json.dumps({
            "customJWTAuthorizer": {
                "allowedClients": [cognito_config['client_id']],
                "discoveryUrl": cognito_config['discovery_url']
            }
        })
        configure_cmd += f" \\\n  --authorizer-config '{auth_config}'"
    
    configure_cmd += f" \\\n  --non-interactive"
    
    print(configure_cmd)
    
    print(f"\n# Step 2: Launch to AWS (takes 10-15 minutes)")
    print(f"agentcore launch --agent {agent_name}")
    
    print(f"\n# Step 3: Check status")
    print(f"agentcore status --agent {agent_name}")
    
    print(f"\n# Step 4: Test the deployment")
    print(f"python test_mcp_client.py")
    
    print(f"\n# Step 5: View logs")
    print(f"aws logs tail /aws/bedrock-agentcore/runtimes/{agent_name} --follow")
    
    print("\n" + "="*80)
    print("💡 TIP: The commands above use the actual values from your setup!")
    print("="*80)
    
    # Also save to a file for easy reference
    with open("agentcore_commands.sh", "w") as f:
        f.write("#!/bin/bash\n")
        f.write("# AgentCore deployment commands\n")
        f.write("# Generated by run_prerequisite.py\n\n")
        f.write("# Step 1: Configure\n")
        f.write(configure_cmd + "\n\n")
        f.write("# Step 2: Launch\n")
        f.write(f"agentcore launch --agent {agent_name}\n\n")
        f.write("# Step 3: Check status\n")
        f.write(f"agentcore status --agent {agent_name}\n\n")
        f.write("# Step 4: Test\n")
        f.write(f"python test_mcp_client.py\n\n")
        f.write("# Step 5: View logs\n")
        f.write(f"aws logs tail /aws/bedrock-agentcore/runtimes/{agent_name} --follow\n")
    
    print(f"\n✅ Commands also saved to: agentcore_commands.sh")
    print(f"   You can run: bash agentcore_commands.sh\n")


def main():
    """Main function to setup prerequisites."""
    parser = argparse.ArgumentParser(
        description='Setup prerequisites for AWS Cost Analysis MCP Server deployment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script creates:
  1. IAM execution role with Pricing API permissions
  2. Cognito user pool for authentication (optional)
  3. Stores configuration in AWS

After running this script, use agentcore CLI commands to deploy.

Examples:
  # Setup with Cognito authentication
  python run_prerequisite.py
  
  # Setup without Cognito (not recommended for production)
  python run_prerequisite.py --no-cognito
  
  # Specify region
  python run_prerequisite.py --region us-east-1
        """
    )
    parser.add_argument('--no-cognito', action='store_true',
                        help='Skip Cognito setup (not recommended for production)')
    parser.add_argument('--region', type=str,
                        help='AWS region (defaults to configured region)')
    
    args = parser.parse_args()
    
    print("="*80)
    print("AWS Cost Analysis MCP Server - Prerequisites Setup")
    print("="*80)
    
    boto_session = Session()
    region = args.region or boto_session.region_name
    print(f"\n📍 Using AWS region: {region}")
    
    # Verify required files exist
    print(f"\n📁 Verifying required files...")
    required_files = ["cost_analysis_fastmcp_server.py", "requirements.txt"]
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ Required file not found: {file}")
            sys.exit(1)
        print(f"✓ Found: {file}")
    
    try:
        # Step 1: Create IAM Role
        role_arn = create_iam_role(AGENT_NAME, region)
        
        # Step 2: Setup Cognito (optional)
        cognito_config = None
        if not args.no_cognito:
            cognito_config = setup_cognito(AGENT_NAME, region)
        else:
            print("\n⚠️  Skipping Cognito setup (--no-cognito specified)")
            print("   Your MCP server will not have authentication")
        
        # Step 3: Store configuration
        store_configuration(role_arn, cognito_config, region, AGENT_NAME)
        
        # Step 4: Print next steps
        print_next_steps(role_arn, cognito_config, region, AGENT_NAME)
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
