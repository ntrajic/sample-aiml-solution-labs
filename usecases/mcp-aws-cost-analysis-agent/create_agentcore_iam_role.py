#!/usr/bin/env python3
"""
Create IAM Role for AgentCore Runtime

This script creates an IAM role with the necessary permissions for the
Cost Analysis Agent to run on Amazon Bedrock AgentCore Runtime.

Required permissions:
- Bedrock: Invoke foundation models (Claude)
- Pricing: Get product pricing information
- Logs: Write CloudWatch logs

Usage:
    python create_agentcore_iam_role.py
    python create_agentcore_iam_role.py --role-name CustomRoleName
    python create_agentcore_iam_role.py --region us-west-2
"""

import boto3
import json
import argparse
import sys
from botocore.exceptions import ClientError

def create_trust_policy():
    """Create trust policy for AgentCore Runtime"""
    return {
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

def create_permissions_policy():
    """
    Create permissions policy based on analysis of the agent code.
    
    Required AWS services:
    1. Bedrock - Invoke Claude models for agent reasoning
    2. Pricing - Get AWS pricing information for cost calculations
    3. CloudWatch Logs - Write agent execution logs
    """
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "BedrockModelInvocation",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": [
                    # Claude models used by the agent
                    "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
                    "arn:aws:bedrock:us-*::foundation-model/us.anthropic.claude-*"
                ]
            },
            {
                "Sid": "PricingAPIAccess",
                "Effect": "Allow",
                "Action": [
                    "pricing:GetProducts",
                    "pricing:GetAttributeValues",
                    "pricing:DescribeServices"
                ],
                "Resource": "*"
            },
            {
                "Sid": "CloudWatchLogsAccess",
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:log-group:/aws/bedrock-agentcore/*"
            }
        ]
    }

def create_iam_role(role_name, region='us-west-2'):
    """
    Create IAM role for AgentCore Runtime
    
    Args:
        role_name: Name of the IAM role to create
        region: AWS region (default: us-west-2)
    
    Returns:
        Role ARN if successful, None otherwise
    """
    iam_client = boto3.client('iam', region_name=region)
    
    print(f"🔧 Creating IAM role: {role_name}")
    print(f"   Region: {region}")
    
    try:
        # Create the role
        trust_policy = create_trust_policy()
        
        print(f"\n📋 Trust Policy:")
        print(json.dumps(trust_policy, indent=2))
        
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='IAM role for Cost Analysis Agent on Bedrock AgentCore Runtime',
            Tags=[
                {'Key': 'Purpose', 'Value': 'BedrockAgentCore'},
                {'Key': 'Agent', 'Value': 'CostAnalysisAgent'},
                {'Key': 'ManagedBy', 'Value': 'create_agentcore_iam_role.py'}
            ]
        )
        
        role_arn = response['Role']['Arn']
        print(f"\n✅ Role created successfully!")
        print(f"   Role ARN: {role_arn}")
        
        # Create and attach inline policy
        permissions_policy = create_permissions_policy()
        policy_name = f"{role_name}-Permissions"
        
        print(f"\n📋 Permissions Policy: {policy_name}")
        print(json.dumps(permissions_policy, indent=2))
        
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(permissions_policy)
        )
        
        print(f"\n✅ Permissions policy attached successfully!")
        
        # Summary
        print(f"\n{'='*80}")
        print(f"📊 IAM Role Summary")
        print(f"{'='*80}")
        print(f"Role Name: {role_name}")
        print(f"Role ARN: {role_arn}")
        print(f"\nPermissions granted:")
        print(f"  ✓ Bedrock: Invoke Claude models")
        print(f"  ✓ Pricing: Get AWS pricing information")
        print(f"  ✓ CloudWatch Logs: Write agent execution logs")
        print(f"\n💡 Use this role ARN when deploying to AgentCore:")
        print(f"   agentcore configure --execution-role-arn {role_arn} ...")
        print(f"{'='*80}")
        
        return role_arn
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        
        if error_code == 'EntityAlreadyExists':
            print(f"\n⚠️  Role '{role_name}' already exists")
            
            # Get existing role
            try:
                response = iam_client.get_role(RoleName=role_name)
                role_arn = response['Role']['Arn']
                print(f"   Existing Role ARN: {role_arn}")
                
                # Ask if user wants to update the policy
                print(f"\n❓ Do you want to update the permissions policy? (y/n): ", end='')
                answer = input().strip().lower()
                
                if answer == 'y':
                    permissions_policy = create_permissions_policy()
                    policy_name = f"{role_name}-Permissions"
                    
                    iam_client.put_role_policy(
                        RoleName=role_name,
                        PolicyName=policy_name,
                        PolicyDocument=json.dumps(permissions_policy)
                    )
                    print(f"✅ Permissions policy updated successfully!")
                    return role_arn
                else:
                    print(f"   Using existing role without changes")
                    return role_arn
                    
            except ClientError as e2:
                print(f"❌ Error getting existing role: {e2}")
                return None
                
        elif error_code == 'AccessDenied':
            print(f"\n❌ Access Denied: You don't have permission to create IAM roles")
            print(f"   Required IAM permissions:")
            print(f"   - iam:CreateRole")
            print(f"   - iam:PutRolePolicy")
            print(f"   - iam:TagRole")
            return None
        else:
            print(f"\n❌ Error creating role: {e}")
            return None
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return None


def delete_iam_role(role_name, region='us-west-2'):
    """
    Delete IAM role and its policies
    
    Args:
        role_name: Name of the IAM role to delete
        region: AWS region
    """
    iam_client = boto3.client('iam', region_name=region)
    
    print(f"🗑️  Deleting IAM role: {role_name}")
    
    try:
        # List and delete inline policies
        response = iam_client.list_role_policies(RoleName=role_name)
        for policy_name in response['PolicyNames']:
            print(f"   Deleting policy: {policy_name}")
            iam_client.delete_role_policy(
                RoleName=role_name,
                PolicyName=policy_name
            )
        
        # Delete the role
        iam_client.delete_role(RoleName=role_name)
        print(f"✅ Role deleted successfully!")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchEntity':
            print(f"⚠️  Role '{role_name}' does not exist")
        else:
            print(f"❌ Error deleting role: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Create IAM role for Cost Analysis Agent on Bedrock AgentCore',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create role with default name
  python create_agentcore_iam_role.py
  
  # Create role with custom name
  python create_agentcore_iam_role.py --role-name MyCustomRole
  
  # Create role in specific region
  python create_agentcore_iam_role.py --region us-east-1
  
  # Delete existing role
  python create_agentcore_iam_role.py --delete --role-name MyRole
  
  # Show what permissions would be granted (dry run)
  python create_agentcore_iam_role.py --dry-run
        """
    )
    parser.add_argument('--role-name', type=str, 
                        default='CostAnalysisAgentCoreRole',
                        help='Name of the IAM role (default: CostAnalysisAgentCoreRole)')
    parser.add_argument('--region', type=str,
                        default='us-west-2',
                        help='AWS region (default: us-west-2)')
    parser.add_argument('--delete', action='store_true',
                        help='Delete the IAM role instead of creating it')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be created without actually creating it')
    
    args = parser.parse_args()
    
    print(f"{'='*80}")
    print(f"🚀 AgentCore IAM Role Management")
    print(f"{'='*80}")
    
    # Verify AWS credentials
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"\n✓ AWS Account: {identity['Account']}")
        print(f"✓ User/Role: {identity['Arn']}")
    except Exception as e:
        print(f"\n❌ Error: Unable to verify AWS credentials")
        print(f"   {e}")
        print(f"\n💡 Configure AWS credentials:")
        print(f"   aws configure")
        sys.exit(1)
    
    if args.dry_run:
        print(f"\n🔍 Dry Run Mode - No changes will be made")
        print(f"\nRole Name: {args.role_name}")
        print(f"Region: {args.region}")
        print(f"\nTrust Policy:")
        print(json.dumps(create_trust_policy(), indent=2))
        print(f"\nPermissions Policy:")
        print(json.dumps(create_permissions_policy(), indent=2))
        return
    
    if args.delete:
        delete_iam_role(args.role_name, args.region)
    else:
        role_arn = create_iam_role(args.role_name, args.region)
        if role_arn:
            print(f"\n✅ Success! Role is ready to use with AgentCore")
            sys.exit(0)
        else:
            print(f"\n❌ Failed to create role")
            sys.exit(1)


if __name__ == "__main__":
    main()
