"""
AgentCore Runtime Handlers

Implementation of Runtime tool handlers for generating runtime operation scripts.
"""

from typing import Dict
import json


async def handle_runtime_configure(args: Dict) -> Dict:
    """Generate script to configure AgentCore Runtime deployment settings"""
    
    region = args.get("region", "us-west-2")
    entrypoint = args["entrypoint"]
    agent_name = args["agent_name"]
    execution_role = args["execution_role"]
    cognito_client_id = args["cognito_client_id"]
    cognito_discovery_url = args["cognito_discovery_url"]
    auto_create_ecr = args.get("auto_create_ecr", True)
    memory_mode = args.get("memory_mode", "NO_MEMORY")
    requirements_file = args.get("requirements_file", "requirements.txt")
    
    # Generate Python script code
    code = f'''#!/usr/bin/env python3
"""
Script to configure AgentCore Runtime deployment.
"""

import json
from bedrock_agentcore_starter_toolkit import Runtime

# Load configuration
with open('runtime_execution_role_config.json') as f:
    role_config = json.load(f)
with open('cognito_config.json') as f:
    cognito_config = json.load(f)

# Initialize Runtime
runtime = Runtime()

# Build authorizer configuration for Cognito JWT
auth_config = {{
    "customJWTAuthorizer": {{
        "allowedClients": [cognito_config["client_id"]],
        "discoveryUrl": cognito_config["discovery_url"]
    }}
}}

# Configure runtime deployment
print("Configuring AgentCore Runtime...")
response = runtime.configure(
    entrypoint="{entrypoint}",
    agent_name="{agent_name}",
    execution_role=role_config["role_arn"],
    auto_create_ecr={auto_create_ecr},
    memory_mode="{memory_mode}",
    requirements_file="{requirements_file}",
    region="{region}",
    authorizer_configuration=auth_config
)

print("✓ Runtime configured successfully!")
print("  Configuration saved to .bedrock_agentcore.yaml")
print("  Next step: Run launch script to deploy the agent")
'''
    
    return {
        "code": code,
        "filename": "configure_runtime.py",
        "instructions": "Run this script to configure AgentCore Runtime deployment settings"
    }


async def handle_runtime_launch(args: Dict) -> Dict:
    """Generate script to deploy agent to AgentCore Runtime"""
    
    region = args.get("region", "us-west-2")
    env_vars = args["env_vars"]
    auto_update_on_conflict = args.get("auto_update_on_conflict", True)
    
    # Build env_vars dict from args
    env_vars_dict = env_vars
    
    # Generate Python script code
    code = f'''#!/usr/bin/env python3
"""
Script to launch agent to AgentCore Runtime.

This creates a CodeBuild pipeline, builds Docker container, pushes to ECR,
and deploys to runtime. Process takes 5-10 minutes.
"""

import json
import os
from bedrock_agentcore_starter_toolkit import Runtime

# Load configuration files that exist
config_files = {{}}

if os.path.exists('memory_config.json'):
    with open('memory_config.json') as f:
        config_files['memory'] = json.load(f)

if os.path.exists('gateway_config.json'):
    with open('gateway_config.json') as f:
        config_files['gateway'] = json.load(f)

if os.path.exists('cognito_config.json'):
    with open('cognito_config.json') as f:
        config_files['cognito'] = json.load(f)
else:
    print("❌ Error: cognito_config.json not found")
    exit(1)

if os.path.exists('runtime_execution_role_config.json'):
    with open('runtime_execution_role_config.json') as f:
        config_files['role'] = json.load(f)
else:
    print("❌ Error: runtime_execution_role_config.json not found")
    exit(1)

# Load .bedrock_agentcore.yaml to get agent name and entrypoint
if not os.path.exists('.bedrock_agentcore.yaml'):
    print("❌ Error: .bedrock_agentcore.yaml not found")
    print("Please run configure_runtime.py first")
    exit(1)

import yaml
with open('.bedrock_agentcore.yaml') as f:
    runtime_config = yaml.safe_load(f)

default_agent = runtime_config.get('default_agent')
agent_config = runtime_config.get('agents', {{}}).get(default_agent, {{}})
agent_name = agent_config.get('name')
entrypoint = agent_config.get('entrypoint')

# Initialize Runtime
runtime = Runtime()

# Build authorizer configuration for Cognito JWT
auth_config = {{
    "customJWTAuthorizer": {{
        "allowedClients": [config_files['cognito']["client_id"]],
        "discoveryUrl": config_files['cognito']["discovery_url"]
    }}
}}

# Configure runtime (loads existing config or creates new one)
print("Configuring runtime...")
runtime.configure(
    entrypoint=entrypoint,
    agent_name=agent_name,
    execution_role=config_files['role']["role_arn"],
    auto_create_ecr=True,
    memory_mode="NO_MEMORY",
    requirements_file="requirements.txt",
    region="{region}",
    authorizer_configuration=auth_config
)
print("✓ Runtime configured")

# Build environment variables from config files
env_vars = {{}}

# Add environment variables passed from MCP tool
env_vars.update({json.dumps(env_vars_dict)})

# Add memory ID if available
if 'memory' in config_files:
    env_vars["MEMORY_ID"] = config_files['memory']["memory_id"]

# Add gateway info if available
if 'gateway' in config_files:
    env_vars["GATEWAY_URL"] = config_files['gateway']["gateway_url"]

# Add Cognito credentials
env_vars["COGNITO_CLIENT_ID"] = config_files['cognito']["client_id"]
env_vars["COGNITO_CLIENT_SECRET"] = config_files['cognito']["client_secret"]
env_vars["COGNITO_DISCOVERY_URL"] = config_files['cognito']["discovery_url"]
env_vars["OAUTH_SCOPES"] = " ".join(config_files['cognito'].get("scopes", ["agentcore-gateway/read", "agentcore-gateway/write"]))

print("\\nEnvironment variables:")
for key in env_vars:
    if "SECRET" in key or "PASSWORD" in key:
        print(f"  {{key}}: ***")
    else:
        print(f"  {{key}}: {{env_vars[key]}}")

# Launch agent
print("\\n" + "=" * 80)
print("LAUNCHING AGENT TO AGENTCORE RUNTIME")
print("=" * 80)
print("\\nThis process will:")
print("  1. Create CodeBuild project")
print("  2. Build Docker container from your agent code")
print("  3. Push container to Amazon ECR")
print("  4. Deploy to AgentCore Runtime")
print("\\n⏱️  Expected time: 5-10 minutes")
print("\\n☕ Grab a coffee while the deployment runs...")
print("=" * 80)

launch_result = runtime.launch(
    env_vars=env_vars,
    auto_update_on_conflict={auto_update_on_conflict}
)

agent_arn = launch_result.agent_arn

# Save agent ARN to config
runtime_output_config = {{
    "agent_arn": agent_arn,
    "agent_name": agent_name,
    "region": "{region}"
}}

# Add memory_id if available
if 'memory' in config_files:
    runtime_output_config["memory_id"] = config_files['memory']["memory_id"]

# Add gateway_url if available
if 'gateway' in config_files:
    runtime_output_config["gateway_url"] = config_files['gateway']["gateway_url"]

with open('runtime_config.json', 'w') as f:
    json.dump(runtime_output_config, f, indent=2)

print(f"\\n✓ Agent deployment initiated!")
print(f"  Agent ARN: {{agent_arn}}")
print(f"✓ Configuration saved to runtime_config.json")
print("\\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)
print("\\n1. Monitor deployment status:")
print("   Run: python check_runtime_status.py")
print("\\n2. Wait for status to show 'READY' (may take a few more minutes)")
print("\\n3. Once READY, test your agent:")
print("   Run: python invoke_agent.py")
print("\\n" + "=" * 80)
'''
    
    return {
        "code": code,
        "filename": "launch_to_runtime.py",
        "instructions": "Run this script to deploy the agent to AgentCore Runtime"
    }


async def handle_runtime_status(args: Dict) -> Dict:
    """Generate script to check AgentCore Runtime deployment status"""
    
    region = args.get("region", "us-west-2")
    
    # Generate Python script code
    code = f'''#!/usr/bin/env python3
"""
Script to check AgentCore Runtime deployment status.
"""

import json
import os
from bedrock_agentcore_starter_toolkit import Runtime

# Check if runtime config exists
if not os.path.exists('runtime_config.json'):
    print("❌ Error: Agent not deployed yet")
    print("Please run launch script first")
    exit(1)

# Load configuration files
with open('runtime_execution_role_config.json') as f:
    role_config = json.load(f)
with open('cognito_config.json') as f:
    cognito_config = json.load(f)

# Load .bedrock_agentcore.yaml to get agent name and entrypoint
if not os.path.exists('.bedrock_agentcore.yaml'):
    print("❌ Error: .bedrock_agentcore.yaml not found")
    print("Please run configure_runtime.py first")
    exit(1)

import yaml
with open('.bedrock_agentcore.yaml') as f:
    runtime_config = yaml.safe_load(f)

default_agent = runtime_config.get('default_agent')
agent_config = runtime_config.get('agents', {{}}).get(default_agent, {{}})
agent_name = agent_config.get('name')
entrypoint = agent_config.get('entrypoint')

# Initialize Runtime
runtime = Runtime()

# Build authorizer configuration for Cognito JWT
auth_config = {{
    "customJWTAuthorizer": {{
        "allowedClients": [cognito_config["client_id"]],
        "discoveryUrl": cognito_config["discovery_url"]
    }}
}}

# Configure runtime (to load existing configuration)
print("Loading runtime configuration...")
runtime.configure(
    entrypoint=entrypoint,
    agent_name=agent_name,
    execution_role=role_config["role_arn"],
    auto_create_ecr=True,
    memory_mode="NO_MEMORY",
    requirements_file="requirements.txt",
    region="{region}",
    authorizer_configuration=auth_config
)

# Check status
print("Checking runtime deployment status...")
status_response = runtime.status()

status = status_response.endpoint["status"]

print(f"\\nAgent Status: {{status}}")
print(f"Endpoint Details: {{json.dumps(status_response.endpoint, indent=2, default=str)}}")

if status == "READY":
    print("\\n" + "=" * 80)
    print("✓ Agent is READY to receive requests!")
    print("=" * 80)
    print("\\nYou can now invoke your agent with:")
    print("  python invoke_agent.py")
elif status in ["CREATING", "UPDATING"]:
    print("\\n" + "=" * 80)
    print("⏳ Agent deployment in progress...")
    print("=" * 80)
    print("\\nThe deployment is still running. This is normal.")
    print("Run this script again in 1-2 minutes to check status.")
elif status in ["CREATE_FAILED", "UPDATE_FAILED"]:
    print("\\n" + "=" * 80)
    print("✗ Agent deployment failed!")
    print("=" * 80)
    print("\\nCheck CloudWatch logs for details:")
    print(f"  Log group: /aws/bedrock-agentcore/runtime/{{agent_name}}")
else:
    print(f"\\n⚠ Unknown status: {{status}}")
'''
    
    return {
        "code": code,
        "filename": "check_runtime_status.py",
        "instructions": "Run this script to check the deployment status"
    }


async def handle_runtime_invoke(args: Dict) -> Dict:
    """Generate script to invoke a deployed AgentCore Runtime agent"""
    
    region = args.get("region", "us-west-2")
    payload = args.get("payload", {"actor_id": "user_001", "prompt": "What do you know about me?"})
    
    # Generate Python script code
    code = f'''#!/usr/bin/env python3
"""
Script to invoke deployed AgentCore Runtime agent.
"""

import json
import base64
import os
import requests
from bedrock_agentcore_starter_toolkit import Runtime

# Check if runtime config exists
if not os.path.exists('runtime_config.json'):
    print("❌ Error: Agent not deployed yet")
    print("Please run launch script first")
    exit(1)

# Load configuration
with open('cognito_config.json') as f:
    cognito_config = json.load(f)
with open('runtime_execution_role_config.json') as f:
    role_config = json.load(f)

# Load .bedrock_agentcore.yaml to get agent name and entrypoint
if not os.path.exists('.bedrock_agentcore.yaml'):
    print("❌ Error: .bedrock_agentcore.yaml not found")
    print("Please run configure_runtime.py first")
    exit(1)

import yaml
with open('.bedrock_agentcore.yaml') as f:
    runtime_config = yaml.safe_load(f)

default_agent = runtime_config.get('default_agent')
agent_config = runtime_config.get('agents', {{}}).get(default_agent, {{}})
agent_name = agent_config.get('name')
entrypoint = agent_config.get('entrypoint')

# Generate bearer token using Cognito client credentials flow
print("Generating OAuth bearer token...")

# Extract domain and region from cognito config
domain = cognito_config["domain"].split('.')[0]  # Get domain prefix
region = cognito_config["region"]

# Construct token endpoint
token_endpoint = f"https://{{domain}}.auth.{{region}}.amazoncognito.com/oauth2/token"

# Prepare credentials for Basic Auth
credentials = f"{{cognito_config['client_id']}}:{{cognito_config['client_secret']}}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

# Get OAuth scopes
oauth_scopes = " ".join(cognito_config.get("scopes", ["agentcore-gateway/read", "agentcore-gateway/write"]))

# Request token
response = requests.post(
    token_endpoint,
    headers={{
        "Authorization": f"Basic {{encoded_credentials}}",
        "Content-Type": "application/x-www-form-urlencoded"
    }},
    data={{
        "grant_type": "client_credentials",
        "scope": oauth_scopes
    }}
)

if response.status_code != 200:
    print(f"❌ Failed to get OAuth token: {{response.text}}")
    exit(1)

bearer_token = response.json()["access_token"]
print("✓ OAuth token obtained")

# Initialize Runtime
runtime = Runtime()

# Build authorizer configuration for Cognito JWT
auth_config = {{
    "customJWTAuthorizer": {{
        "allowedClients": [cognito_config["client_id"]],
        "discoveryUrl": cognito_config["discovery_url"]
    }}
}}

# Configure runtime (to load existing configuration)
print("\\nConfiguring runtime...")
runtime.configure(
    entrypoint=entrypoint,
    agent_name=agent_name,
    execution_role=role_config["role_arn"],
    auto_create_ecr=True,
    memory_mode="NO_MEMORY",
    requirements_file="requirements.txt",
    region="{region}",
    authorizer_configuration=auth_config
)

# Invoke agent
print("\\nInvoking agent...")
payload = {json.dumps(payload, indent=4)}

try:
    response = runtime.invoke(
        payload,
        bearer_token=bearer_token
    )
    
    print(f"\\n" + "=" * 80)
    print("✓ AGENT RESPONSE")
    print("=" * 80)
    print(response)
    print("=" * 80)
except Exception as e:
    print(f"\\n" + "=" * 80)
    print(f"❌ Error invoking agent")
    print("=" * 80)
    print(f"Error: {{e}}")
    print("\\nTroubleshooting:")
    print("  1. Check agent status: python check_runtime_status.py")
    print("  2. Verify agent is in READY state")
    print("  3. Check CloudWatch logs for errors")
    print("=" * 80)
    exit(1)
'''
    
    return {
        "code": code,
        "filename": "invoke_agent.py",
        "instructions": "Run this script to invoke the deployed agent"
    }


async def handle_runtime_delete(args: Dict) -> Dict:
    """Generate script to delete an AgentCore Runtime agent deployment"""
    
    region = args.get("region", "us-west-2")
    
    # Generate Python script code using boto3 (like reference notebook)
    code = f'''#!/usr/bin/env python3
"""
Script to delete AgentCore Runtime agent deployment.

WARNING: This permanently deletes the agent runtime.
RERUNNABLE: Safe to run multiple times - handles missing resources gracefully.
"""

import json
import os
import boto3

print("Deleting AgentCore Runtime...")

# Check if runtime config exists
if not os.path.exists('runtime_config.json'):
    print("⚠️  Runtime config not found - nothing to delete")
    print("✓ Script completed successfully (no resources to delete)")
    exit(0)

# Load runtime configuration
try:
    with open('runtime_config.json') as f:
        runtime_config = json.load(f)
except Exception as e:
    print(f"⚠️  Failed to load runtime config: {{e}}")
    print("✓ Script completed successfully (no resources to delete)")
    exit(0)

agent_arn = runtime_config.get('agent_arn')

if not agent_arn:
    print("⚠️  No agent ARN found in config")
    print("✓ Script completed successfully (no resources to delete)")
    exit(0)

# Extract agent ID from ARN
agent_id = agent_arn.split('/')[-1]

print(f"  Agent ID: {{agent_id}}")

# Delete the agent using boto3 (like reference notebook)
try:
    agentcore_client = boto3.client('bedrock-agentcore-control', region_name='{region}')
    agentcore_client.delete_agent_runtime(agentRuntimeId=agent_id)
    print("✓ Agent runtime deleted successfully!")
except Exception as e:
    error_msg = str(e).lower()
    if "resourcenotfound" in error_msg or "not found" in error_msg:
        print("⚠️  Agent already deleted or not found")
        print("✓ Script completed successfully (resource already removed)")
    else:
        print(f"✗ Error deleting agent: {{e}}")
        exit(1)

print("\\n✓ Runtime deletion completed successfully")
print("✓ This script is RERUNNABLE - you can safely run it multiple times.")
'''
    
    return {
        "code": code,
        "filename": "delete_runtime.py",
        "instructions": "Run this script to delete the AgentCore Runtime deployment"
    }
