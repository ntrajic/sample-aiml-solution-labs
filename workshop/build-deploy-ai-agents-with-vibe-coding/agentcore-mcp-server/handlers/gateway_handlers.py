"""
AgentCore Gateway Handlers

Implementation of Gateway tool handlers for generating gateway operation scripts.
"""

from typing import Dict
import json


async def handle_gateway_create(args: Dict) -> Dict:
    """Generate script to create AgentCore Gateway with OAuth authentication"""
    
    region = args.get("region", "us-west-2")
    name = args["name"]
    role_arn = args["role_arn"]
    cognito_client_id = args["cognito_client_id"]
    cognito_discovery_url = args["cognito_discovery_url"]
    protocol_type = args.get("protocol_type", "MCP")
    authorizer_type = args.get("authorizer_type", "CUSTOM_JWT")
    description = args.get("description", "")
    
    # Validate protocol type
    if protocol_type != "MCP":
        raise ValueError("Only MCP protocol is supported in this handler")
    
    # Generate Python script code
    code = f'''#!/usr/bin/env python3
"""
Script to create AgentCore Gateway.

Prerequisites:
- cognito_config.json (from Cognito setup)
- gateway_role_config.json (from IAM role setup)
"""

import json
import boto3

# Load configuration
with open('cognito_config.json') as f:
    cognito_config = json.load(f)
with open('gateway_role_config.json') as f:
    role_config = json.load(f)

# Initialize AgentCore control plane client
gateway_client = boto3.client("bedrock-agentcore-control", region_name='{region}')

# Build auth configuration for Cognito JWT
auth_config = {{
    "customJWTAuthorizer": {{
        "allowedClients": [cognito_config["client_id"]],
        "discoveryUrl": cognito_config["discovery_url"]
    }}
}}

# Create gateway
print("Creating AgentCore Gateway...")
create_response = gateway_client.create_gateway(
    name="{name}",
    roleArn=role_config["role_arn"],
    protocolType="{protocol_type}",
    authorizerType="{authorizer_type}",
    authorizerConfiguration=auth_config,
    description="{description}"
)

# Extract gateway details
gateway_id = create_response["gatewayId"]
gateway_url = create_response["gatewayUrl"]
gateway_arn = create_response["gatewayArn"]

# Save gateway config (using 'id' to match reference code pattern)
config = {{
    "id": gateway_id,
    "gateway_id": gateway_id,  # Keep for backward compatibility
    "gateway_url": gateway_url,
    "gateway_arn": gateway_arn,
    "name": "{name}",
    "region": "{region}"
}}

with open('gateway_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print(f"✓ Gateway created successfully!")
print(f"  Gateway ID: {{gateway_id}}")
print(f"  Gateway URL: {{gateway_url}}")
print(f"✓ Configuration saved to gateway_config.json")
'''
    
    return {
        "code": code,
        "filename": f"{name.lower().replace(' ', '_')}_gateway_create.py",
        "instructions": f"Ensure cognito_config.json and gateway_role_config.json exist, then run this script to create the AgentCore Gateway '{name}'"
    }


async def handle_gateway_add_lambda_target(args: Dict) -> Dict:
    """Generate script to add Lambda function as gateway target
    
    Note: This handler uses lambda_arn and tool_schema directly from args
    and inlines them into the generated script for clarity.
    """
    
    region = args.get("region", "us-west-2")
    # gateway_id loaded from config file in generated script
    target_name = args["target_name"]
    lambda_arn = args["lambda_arn"]
    tool_schema = args["tool_schema"]
    target_description = args.get("target_description", "")
    
    # Generate Python script code with inlined values
    code = f'''#!/usr/bin/env python3
"""
Script to add Lambda target to AgentCore Gateway.

Prerequisites:
- gateway_config.json (from gateway creation)
"""

import json
import boto3

# Load gateway configuration
with open('gateway_config.json') as f:
    gateway_config = json.load(f)

# Initialize AgentCore control plane client
gateway_client = boto3.client("bedrock-agentcore-control", region_name='{region}')

# Lambda ARN and tool schema (inlined from MCP call)
lambda_arn = "{lambda_arn}"
tool_schema = {json.dumps(tool_schema, indent=4)}

# Build Lambda target configuration with MCP protocol
lambda_target_config = {{
    "mcp": {{
        "lambda": {{
            "lambdaArn": lambda_arn,
            "toolSchema": {{
                "inlinePayload": tool_schema
            }}
        }}
    }}
}}

# Use gateway's IAM role for Lambda invocation
credential_config = [{{"credentialProviderType": "GATEWAY_IAM_ROLE"}}]

# Create target
print("Adding Lambda target to gateway...")
print(f"  Gateway ID: {{gateway_config['gateway_id']}}")
print(f"  Target Name: {target_name}")
print(f"  Lambda ARN: {{lambda_arn}}")

create_response = gateway_client.create_gateway_target(
    gatewayIdentifier=gateway_config["gateway_id"],
    name="{target_name}",
    description="{target_description}",
    targetConfiguration=lambda_target_config,
    credentialProviderConfigurations=credential_config
)

target_id = create_response["targetId"]

print(f"\\n✓ Lambda target added successfully!")
print(f"  Target ID: {{target_id}}")
print(f"  Target Name: {target_name}")
'''
    
    return {
        "code": code,
        "filename": f"add_{target_name.lower().replace(' ', '_')}_target.py",
        "instructions": f"Ensure gateway_config.json exists, then run this script to add Lambda target '{target_name}' to the gateway"
    }


async def handle_gateway_list_targets(args: Dict) -> Dict:
    """Generate script to list all targets attached to a gateway
    
    Note: gateway_id is loaded from gateway_config.json in the generated script
    """
    
    region = args.get("region", "us-west-2")
    # gateway_id loaded from config file in generated script
    
    # Generate Python script code
    code = f'''#!/usr/bin/env python3
"""
Script to list AgentCore Gateway targets.

Prerequisites:
- gateway_config.json (from gateway creation)
"""

import json
import boto3

# Load configuration
with open('gateway_config.json') as f:
    gateway_config = json.load(f)

# Initialize AgentCore control plane client
gateway_client = boto3.client("bedrock-agentcore-control", region_name='{region}')

# List targets using correct API method
print(f"Listing targets for gateway: {{gateway_config['gateway_id']}}")
response = gateway_client.list_gateway_targets(
    gatewayIdentifier=gateway_config["gateway_id"]
)

targets = response.get("items", [])

print(f"\\n✓ Found {{len(targets)}} target(s):")
for i, target in enumerate(targets, 1):
    print(f"\\n{{i}}. {{target.get('name', 'N/A')}}")
    print(f"   Target ID: {{target.get('targetId', 'N/A')}}")
    print(f"   Status: {{target.get('status', 'unknown')}}")
    print(f"   Description: {{target.get('description', 'N/A')}}")
'''
    
    return {
        "code": code,
        "filename": "list_gateway_targets.py",
        "instructions": "Ensure gateway_config.json exists, then run this script to list all gateway targets"
    }


async def handle_gateway_delete_target(args: Dict) -> Dict:
    """Generate script to delete a target from gateway
    
    Note: gateway_id and target_id are used from args
    """
    
    region = args.get("region", "us-west-2")
    # Use target_id from args (not from config file)
    target_id = args["target_id"]
    
    # Generate Python script code
    code = f'''#!/usr/bin/env python3
"""
Script to delete a target from AgentCore Gateway.

WARNING: This removes the tool from the gateway.
RERUNNABLE: Safe to run multiple times - handles missing resources gracefully.

Prerequisites:
- gateway_config.json (from gateway creation)
"""

import json
import os
import boto3

print("Deleting gateway target...")

# Check if gateway config exists
if not os.path.exists('gateway_config.json'):
    print("⚠️  Gateway config not found - nothing to delete")
    print("✓ Script completed successfully (no resources to delete)")
    exit(0)

# Load configuration
try:
    with open('gateway_config.json') as f:
        gateway_config = json.load(f)
except Exception as e:
    print(f"⚠️  Failed to load gateway config: {{e}}")
    print("✓ Script completed successfully (no resources to delete)")
    exit(0)

# Initialize AgentCore control plane client
gateway_client = boto3.client("bedrock-agentcore-control", region_name='{region}')

# Delete target using correct API method name
try:
    print(f"  Gateway ID: {{gateway_config['gateway_id']}}")
    print(f"  Target ID: {target_id}")
    
    gateway_client.delete_gateway_target(
        gatewayIdentifier=gateway_config["gateway_id"],
        targetId="{target_id}"
    )
    print("✓ Gateway target deleted successfully!")
except Exception as e:
    error_msg = str(e).lower()
    if "resourcenotfound" in error_msg or "not found" in error_msg:
        print("⚠️  Target already deleted or not found")
        print("✓ Script completed successfully (resource already removed)")
    else:
        print(f"✗ Error deleting target: {{e}}")
        exit(1)

print("\\n✓ Target deletion completed successfully")
print("✓ This script is RERUNNABLE - you can safely run it multiple times.")
'''
    
    return {
        "code": code,
        "filename": "delete_gateway_target.py",
        "instructions": f"Ensure gateway_config.json exists, then run this script to delete target '{target_id}'"
    }


async def handle_gateway_delete(args: Dict) -> Dict:
    """Generate script to delete AgentCore Gateway
    
    Note: gateway_id is loaded from gateway_config.json in the generated script
    """
    
    region = args.get("region", "us-west-2")
    # gateway_id loaded from config file in generated script
    
    # Generate Python script code
    code = f'''#!/usr/bin/env python3
"""
Script to delete AgentCore Gateway.

WARNING: This permanently deletes the gateway and all its targets.
RERUNNABLE: Safe to run multiple times - handles missing resources gracefully.

Prerequisites:
- gateway_config.json (from gateway creation)
"""

import json
import os
import boto3

print("=" * 80)
print("Delete AgentCore Gateway")
print("=" * 80)

# Check if gateway config exists
if not os.path.exists('gateway_config.json'):
    print("⚠️  Gateway config not found - nothing to delete")
    print("✓ Script completed successfully (no resources to delete)")
    exit(0)

# Load configuration
try:
    with open('gateway_config.json') as f:
        gateway_config = json.load(f)
except Exception as e:
    print(f"⚠️  Failed to load gateway config: {{e}}")
    print("✓ Script completed successfully (no resources to delete)")
    exit(0)

# Initialize AgentCore control plane client
gateway_client = boto3.client("bedrock-agentcore-control", region_name='{region}')

print(f"\\nGateway ID: {{gateway_config['gateway_id']}}")

# Step 1: Delete all targets first
print("\\nStep 1: Deleting gateway targets...")
try:
    response = gateway_client.list_gateway_targets(gatewayIdentifier=gateway_config["gateway_id"])
    targets = response.get('items', [])
    
    if targets:
        for target in targets:
            try:
                gateway_client.delete_gateway_target(
                    gatewayIdentifier=gateway_config["gateway_id"],
                    targetId=target['targetId']
                )
                print(f"✓ Deleted target: {{target.get('name', target['targetId'])}}")
            except Exception as e:
                if "ResourceNotFound" in str(e) or "not found" in str(e).lower():
                    print(f"⚠️  Target already deleted: {{target.get('name', target['targetId'])}}")
                else:
                    print(f"✗ Error deleting target: {{e}}")
                    raise  # Re-raise to prevent gateway deletion
    else:
        print("⚠️  No targets found")
except Exception as e:
    if "ResourceNotFound" in str(e) or "not found" in str(e).lower():
        print("⚠️  Gateway not found (may already be deleted)")
    else:
        print(f"⚠️  Could not delete targets: {{e}}")
        raise  # Re-raise to prevent gateway deletion

# Step 1.5: Verify all targets are deleted
print("\\nStep 1.5: Verifying targets are deleted...")
try:
    response = gateway_client.list_gateway_targets(gatewayIdentifier=gateway_config["gateway_id"])
    remaining_targets = response.get('items', [])
    if remaining_targets:
        print(f"⚠️  Warning: {{len(remaining_targets)}} target(s) still exist. Waiting 5 seconds...")
        import time
        time.sleep(5)
        # Check again
        response = gateway_client.list_gateway_targets(gatewayIdentifier=gateway_config["gateway_id"])
        remaining_targets = response.get('items', [])
        if remaining_targets:
            print(f"✗ Error: {{len(remaining_targets)}} target(s) still exist after waiting")
            for target in remaining_targets:
                print(f"  - {{target.get('name', target['targetId'])}} ({{target['targetId']}})")
            print("\\nPlease wait a few moments and run this script again.")
            exit(1)
    print("✓ All targets confirmed deleted")
except Exception as e:
    if "ResourceNotFound" not in str(e) and "not found" not in str(e).lower():
        print(f"⚠️  Could not verify targets: {{e}}")

# Step 2: Delete gateway
print("\\nStep 2: Deleting gateway...")
try:
    gateway_client.delete_gateway(
        gatewayIdentifier=gateway_config["gateway_id"]
    )
    print("✓ Gateway deleted successfully!")
except Exception as e:
    error_msg = str(e).lower()
    if "resourcenotfound" in error_msg or "not found" in error_msg:
        print("⚠️  Gateway already deleted or not found")
        print("✓ Script completed successfully (resource already removed)")
    else:
        print(f"✗ Error deleting gateway: {{e}}")
        exit(1)

print("\\n" + "=" * 80)
print("✓ Gateway deletion completed successfully")
print("✓ This script is RERUNNABLE - you can safely run it multiple times.")
print("=" * 80)
'''
    
    return {
        "code": code,
        "filename": "delete_gateway.py",
        "instructions": "Ensure gateway_config.json exists, then run this script to delete the AgentCore Gateway and all its targets"
    }

