"""
AgentCore Observability Handlers

Implementation of Observability tool handlers for generating observability scripts.
"""

from typing import Dict
import json


async def handle_observability_get_dashboard_url(args: Dict) -> Dict:
    """Generate script to get CloudWatch GenAI Observability dashboard URL"""
    
    region = args.get("region", "us-west-2")
    
    # Generate Python script code
    code = f'''#!/usr/bin/env python3
"""
Script to get CloudWatch GenAI Observability dashboard URL.
"""

# Build dashboard URL
region = "{region}"
dashboard_url = f"https://console.aws.amazon.com/cloudwatch/home?region={{region}}#gen-ai-observability/agent-core"

print("CloudWatch GenAI Observability Dashboard")
print("=" * 80)
print(f"\\nDashboard URL: {{dashboard_url}}")
print(f"Region: {{region}}")
print("\\nFeatures:")
print("  - Agent performance metrics")
print("  - Request traces and spans")
print("  - Session history")
print("  - Error rates and patterns")
print("  - Tool invocation details")
print("\\nOpen this URL in your browser to view the dashboard")
'''
    
    return {
        "code": code,
        "filename": "get_dashboard_url.py",
        "instructions": "Run this script to get the observability dashboard URL"
    }


async def handle_observability_get_logs_info(args: Dict) -> Dict:
    """Generate script to get CloudWatch log group information"""
    
    region = args.get("region", "us-west-2")
    agent_arn = args["agent_arn"]
    
    # Generate Python script code
    code = f'''#!/usr/bin/env python3
"""
Script to get CloudWatch log group information for agent logs.
"""

import json
from datetime import datetime

# Load configuration
with open('runtime_config.json') as f:
    runtime_config = json.load(f)

agent_arn = runtime_config["agent_arn"]

# Extract agent ID from ARN
agent_id = agent_arn.split('/')[-1]

# Build log group name
log_group = f"/aws/bedrock-agentcore/runtimes/{{agent_id}}-DEFAULT"

# Get current date for log stream prefix
current_date = datetime.now().strftime("%Y/%m/%d")

# Build CLI commands
tail_command = f'aws logs tail {{log_group}} --log-stream-name-prefix "{{current_date}}/[runtime-logs]" --follow'
recent_command = f'aws logs tail {{log_group}} --log-stream-name-prefix "{{current_date}}/[runtime-logs]" --since 1h'

print("CloudWatch Logs Information")
print("=" * 80)
print(f"\\nAgent ARN: {{agent_arn}}")
print(f"Agent ID: {{agent_id}}")
print(f"Log Group: {{log_group}}")
print(f"Region: {region}")
print("\\nCLI Commands:")
print(f"\\nTail logs (real-time):")
print(f"  {{tail_command}}")
print(f"\\nView recent logs (last hour):")
print(f"  {{recent_command}}")
'''
    
    return {
        "code": code,
        "filename": "get_logs_info.py",
        "instructions": "Run this script to get log group information and CLI commands"
    }


async def handle_observability_get_recent_logs(args: Dict) -> Dict:
    """Generate script to retrieve recent logs from CloudWatch"""
    
    region = args.get("region", "us-west-2")
    agent_arn = args["agent_arn"]
    limit = args.get("limit", 50)
    hours_back = args.get("hours_back", 1)
    
    # Generate Python script code
    code = f'''#!/usr/bin/env python3
"""
Script to retrieve recent logs from CloudWatch.
"""

import json
import boto3
from datetime import datetime, timedelta

# Load configuration
with open('runtime_config.json') as f:
    runtime_config = json.load(f)

agent_arn = runtime_config["agent_arn"]

# Extract agent ID from ARN
agent_id = agent_arn.split('/')[-1]
log_group = f"/aws/bedrock-agentcore/runtimes/{{agent_id}}-DEFAULT"

# Initialize CloudWatch Logs client
logs_client = boto3.client('logs', region_name='{region}')

# Calculate start time
start_time = int((datetime.now() - timedelta(hours={hours_back})).timestamp() * 1000)

try:
    # Fetch log events
    print(f"Retrieving logs from {{log_group}}...")
    response = logs_client.filter_log_events(
        logGroupName=log_group,
        limit={limit},
        startTime=start_time
    )
    
    events = response.get('events', [])
    
    print(f"\\n✓ Retrieved {{len(events)}} log events from the last {hours_back} hour(s)\\n")
    print("=" * 80)
    
    for event in events:
        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000).isoformat()
        message = event['message']
        print(f"[{{timestamp}}] {{message}}")
        print("-" * 80)
        
except logs_client.exceptions.ResourceNotFoundException:
    print(f"✗ Log group not found: {{log_group}}")
    print("  Agent may not have been invoked yet, or logs may not be available.")
except Exception as e:
    print(f"✗ Error retrieving logs: {{str(e)}}")
'''
    
    return {
        "code": code,
        "filename": "get_recent_logs.py",
        "instructions": "Run this script to retrieve recent agent logs"
    }
