#!/usr/bin/env python3
"""
Test client for AWS Cost Analysis MCP Server deployed on AgentCore Runtime

This script retrieves the Agent ARN from AWS and tests the deployed MCP server.
Supports both authenticated (Cognito client credentials) and non-authenticated deployments.
"""

import asyncio
import boto3
import json
import sys
import argparse
import base64
import requests
from pathlib import Path
from boto3.session import Session
from datetime import timedelta

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

AGENT_NAME = "aws_cost_analysis_mcp"


def get_cognito_token(cognito_config):
    """
    Get access token using Cognito client credentials flow.
    
    Args:
        cognito_config: Dictionary with client_id, client_secret, token_endpoint
        
    Returns:
        str: Access token
    """
    print("🔐 Getting access token from Cognito...")
    
    client_id = cognito_config['client_id']
    client_secret = cognito_config['client_secret']
    token_endpoint = cognito_config['token_endpoint']
    print(f"Token endpoint: {token_endpoint}")
    
    # Encode client credentials
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    # Request token using client credentials flow
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    data = {
        "grant_type": "client_credentials",
        "scope": "default-m2m-resource-server-bqlhav/read"
    }
    
    try:
        response = requests.post(token_endpoint, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data['access_token']
        print(f"✓ Obtained access token (expires in {token_data.get('expires_in', 'unknown')} seconds)")
        return access_token
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        raise


async def test_mcp_server(agent_arn, region, bearer_token=None):
    """
    Test the MCP server.
    
    Args:
        agent_arn: AgentCore Runtime agent ARN
        region: AWS region
        bearer_token: Optional bearer token for authentication
    """
    # Construct MCP URL
    encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
    mcp_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    
    headers = {"Content-Type": "application/json"}
    if bearer_token:
        headers["authorization"] = f"Bearer {bearer_token}"
        print("🔐 Using authentication")
    else:
        print("⚠️  No authentication (ensure server was deployed with --no-auth)")
    
    print(f"\n🔗 Connecting to MCP server...")
    print(f"   URL: {mcp_url}")
    print(f"\n💡 If this hangs, check server logs:")
    print(f"   aws logs tail /aws/bedrock-agentcore/runtimes/{AGENT_NAME} --follow")

    try:
        print("\n🔄 Creating HTTP client connection...")
        async with streamablehttp_client(
            mcp_url, 
            headers, 
            timeout=timedelta(seconds=60),  # Longer timeout for connection
            terminate_on_close=False
        ) as (read_stream, write_stream, _):
            print("✓ HTTP connection established")
            
            print("🔄 Creating MCP session...")
            async with ClientSession(read_stream, write_stream) as session:
                print("✓ MCP session created")
                
                print("🔄 Initializing MCP session (this may take 10-30 seconds)...")
                try:
                    # Add timeout to initialize
                    await asyncio.wait_for(session.initialize(), timeout=60.0)
                    print("✓ MCP session initialized")
                except asyncio.TimeoutError:
                    print("❌ Timeout waiting for MCP session initialization")
                    print("   The server may be starting up or there's a configuration issue")
                    print("   Check the server logs for errors")
                    raise
                except Exception as e:
                    print(f"❌ Error during session initialization: {e}")
                    print(f"   Error type: {type(e).__name__}")
                    raise
                
                print("\n🔄 Listing available tools...")
                tool_result = await session.list_tools()
                
                print("\n" + "="*80)
                print("📋 Available MCP Tools")
                print("="*80)
                for tool in tool_result.tools:
                    print(f"\n🔧 {tool.name}")
                    print(f"   {tool.description}")
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        properties = tool.inputSchema.get('properties', {})
                        if properties:
                            print(f"   Parameters: {', '.join(properties.keys())}")
                
                print("\n" + "="*80)
                print(f"✅ Successfully connected to MCP server!")
                print(f"   Found {len(tool_result.tools)} tools available")
                print("="*80)
                
                # Define test cases for each tool
                test_cases = [
                    {
                        "name": "health_check",
                        "args": {},
                        "description": "Server health check"
                    },
                    {
                        "name": "get_bedrock_pricing_tool_read_only",
                        "args": {"model_name": "claude", "region": "us-west-2"},
                        "description": "Bedrock model pricing"
                    },
                    {
                        "name": "get_agentcore_pricing_tool_read_only",
                        "args": {"region": "us-west-2"},
                        "description": "AgentCore component pricing"
                    },
                    {
                        "name": "get_aws_pricing_tool_read_only",
                        "args": {"service_code": "AmazonS3", "region": "us-west-2"},
                        "description": "AWS service pricing"
                    },
                    {
                        "name": "get_attribute_values_tool_read_only",
                        "args": {"service_code": "AmazonS3", "attribute_name": "regionCode"},
                        "description": "Pricing attribute values"
                    },
                    {
                        "name": "bedrock_calculator_tool_read_only",
                        "args": {
                            "params": {
                                "questions_per_month": 10000,
                                "system_prompt_tokens": 500,
                                "history_qa_pairs": 3,
                                "model1": {
                                    "model_name": "claude-3-haiku",
                                    "cost_per_million_input_tokens": 0.25,
                                    "cost_per_million_output_tokens": 1.25,
                                    "input_tokens_per_question": 1000,
                                    "output_tokens_per_question": 500
                                }
                            }
                        },
                        "description": "Bedrock cost calculation"
                    },      
                    {
                        "name": "agentcore_calculator_tool_read_only",
                        "args": {
                            "params": {
                                "runtime_hours": 100,
                                "memory_gb": 2,
                                "requests": 10000
                            }
                        },
                        "description": "AgentCore cost calculation"
                    }             
                ]
                
                # Run tests
                print("\n" + "="*80)
                print("🧪 Running Tool Tests")
                print("="*80)
                
                passed = 0
                failed = 0
                
                for test in test_cases:
                    print(f"\n📝 Testing: {test['name']}")
                    print(f"   Description: {test['description']}")
                    
                    try:
                        result = await session.call_tool(
                            name=test['name'],
                            arguments=test['args']
                        )
                        result_text = result.content[0].text
                        
                        # Parse and display result
                        try:
                            result_data = json.loads(result_text)
                            
                            # Check for errors
                            if isinstance(result_data, dict) and 'error' in result_data:
                                print(f"   ⚠️  Tool returned error: {result_data['error'][:100]}")
                                failed += 1
                            else:
                                # Success - show summary
                                if isinstance(result_data, dict):
                                    if 'pricing_data' in result_data:
                                        count = result_data.get('count', 0)
                                        print(f"   ✅ Success: Retrieved {count} pricing entries")
                                    elif 'attribute_values' in result_data:
                                        count = result_data.get('count', 0)
                                        print(f"   ✅ Success: Retrieved {count} attribute values")
                                    elif 'status' in result_data:
                                        print(f"   ✅ Success: {result_data.get('status', 'OK')}")
                                    elif 'total_cost' in result_data or 'monthly_cost' in result_data:
                                        cost = result_data.get('total_cost') or result_data.get('monthly_cost', 'N/A')
                                        print(f"   ✅ Success: Calculated cost: ${cost}")
                                    else:
                                        print(f"   ✅ Success: {str(result_data)[:100]}")
                                else:
                                    print(f"   ✅ Success: {str(result_data)[:100]}")
                                passed += 1
                        except json.JSONDecodeError:
                            # Not JSON, just show text
                            print(f"   ✅ Success: {result_text[:100]}")
                            passed += 1
                            
                    except Exception as e:
                        print(f"   ❌ Failed: {str(e)[:100]}")
                        failed += 1
                
                # Summary
                print("\n" + "="*80)
                print("📊 Test Summary")
                print("="*80)
                print(f"   Total Tests: {passed + failed}")
                print(f"   ✅ Passed: {passed}")
                print(f"   ❌ Failed: {failed}")
                print(f"   Success Rate: {(passed/(passed+failed)*100):.1f}%")
                
                print("\n" + "="*80)
                print("✅ MCP Server Testing Complete!")
                print("="*80)
                
    except Exception as e:
        print(f"\n❌ Error connecting to MCP server: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Check for common issues
        if "403" in str(e) or "Forbidden" in str(e):
            print("\n💡 Authentication issue detected:")
            print("   - Verify the bearer token is valid")
            print("   - Check that the Cognito configuration is correct")
            print("   - Ensure the server was deployed with authentication enabled")
        elif "404" in str(e) or "Not Found" in str(e):
            print("\n💡 Server not found:")
            print("   - Verify the Agent ARN is correct")
            print("   - Check that the server was successfully deployed")
            print("   - Run: agentcore status --agent aws_cost_analysis_mcp")
        elif "timeout" in str(e).lower() or "TimeoutError" in str(type(e).__name__):
            print("\n💡 Timeout issue:")
            print("   - The server may still be starting up (wait 2-3 minutes)")
            print("   - Check server logs for errors")
            print("   - Verify the server is running: agentcore status --agent aws_cost_analysis_mcp")
        elif "TaskGroup" in str(e) or "unhandled errors" in str(e):
            print("\n💡 Connection/Protocol issue:")
            print("   - The server may not be responding correctly")
            print("   - Check server logs: aws logs tail /aws/bedrock-agentcore/runtimes/aws_cost_analysis_mcp --follow")
            print("   - Verify the server is ACTIVE: agentcore status --agent aws_cost_analysis_mcp")
            print("   - The server may have errors in the MCP implementation")
        
        import traceback
        print("\n📋 Full traceback:")
        traceback.print_exc()
        sys.exit(1)


def check_runtime_status(agent_arn, region):
    """
    Check if the AgentCore Runtime is active.
    
    Args:
        agent_arn: AgentCore Runtime agent ARN
        region: AWS region
    """
    print("\n🔍 Checking AgentCore Runtime status...")
    try:
        agentcore_client = boto3.client('bedrock-agentcore-control', region_name=region)
        
        # Extract runtime ID from ARN
        # ARN format: arn:aws:bedrock-agentcore:region:account:runtime/name-id
        runtime_id = agent_arn.split('/')[-1]
        
        response = agentcore_client.get_agent_runtime(
            agentRuntimeId=runtime_id
        )
        
        status = response.get('status', 'UNKNOWN')
        print(f"✓ Runtime status: {status}")
        
        if status != 'READY':
            print(f"⚠️  Runtime is not READY. Current status: {status}")
            print(f"   Wait for the runtime to become READY before testing")
            return False
        
        return True
    except Exception as e:
        print(f"⚠️  Could not check runtime status: {e}")
        print(f"   Proceeding with test anyway...")
        return True


async def main():
    parser = argparse.ArgumentParser(
        description='Test AWS Cost Analysis MCP Server on AgentCore Runtime',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with Cognito authentication (retrieves credentials automatically)
  python test_mcp_client.py
  
  # Test without authentication (for --no-auth deployments)
  python test_mcp_client.py --no-auth
  
  # Test with manual bearer token
  python test_mcp_client.py --bearer-token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  
  # Test with specific agent ARN
  python test_mcp_client.py --agent-arn arn:aws:bedrock-agentcore:us-west-2:123456789012:agent-runtime/xxx
        """
    )
    parser.add_argument('--no-auth', action='store_true',
                        help='Test without authentication')
    parser.add_argument('--bearer-token', type=str,
                        help='Bearer token for authentication')
    parser.add_argument('--agent-arn', type=str,
                        help='Agent ARN (if not provided, retrieves from Parameter Store)')
    parser.add_argument('--region', type=str,
                        help='AWS region (defaults to configured region)')
    parser.add_argument('--skip-status-check', action='store_true',
                        help='Skip runtime status check')
    
    args = parser.parse_args()
    
    boto_session = Session()
    region = args.region or boto_session.region_name
    
    print(f"Using AWS region: {region}")
    print("="*80)
    
    try:
        # Get Agent ARN
        if args.agent_arn:
            agent_arn = args.agent_arn
            print(f"✓ Using provided Agent ARN: {agent_arn}")
        else:
            # Try to get Agent ARN from .bedrock_agentcore.yaml
            print(f"🔍 Looking for Agent ARN...")
            agent_arn = None
            
            # First try: Read from .bedrock_agentcore.yaml
            try:
                import yaml
                config_file = '.bedrock_agentcore.yaml'
                if Path(config_file).exists():
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f)
                        if config and 'agents' in config:
                            # agents is a dict, not a list
                            if AGENT_NAME in config['agents']:
                                agent_config = config['agents'][AGENT_NAME]
                                if 'bedrock_agentcore' in agent_config:
                                    agent_arn = agent_config['bedrock_agentcore'].get('agent_arn')
                                    if agent_arn:
                                        print(f"✓ Retrieved Agent ARN from .bedrock_agentcore.yaml: {agent_arn}")
            except Exception as e:
                print(f"⚠️  Could not read .bedrock_agentcore.yaml: {e}")
            
            # Second try: agentcore status command
            if not agent_arn:
                try:
                    import subprocess
                    result = subprocess.run(
                        ['agentcore', 'status', '--agent', AGENT_NAME, '--verbose'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        # Parse the output for agent ARN
                        try:
                            status_data = json.loads(result.stdout)
                            if 'agent' in status_data and 'agentArn' in status_data['agent']:
                                agent_arn = status_data['agent']['agentArn']
                                print(f"✓ Retrieved Agent ARN from agentcore status: {agent_arn}")
                        except:
                            pass
                except:
                    pass
            
            # If still not found, show error
            if not agent_arn:
                print(f"❌ Agent ARN not found")
                print(f"\n📋 Deployment Status:")
                print(f"   Run this to check if deployment is complete:")
                print(f"   agentcore status --agent {AGENT_NAME}")
                print(f"\n💡 If not deployed yet:")
                print(f"   1. Run: python run_prerequisite.py")
                print(f"   2. Run: agentcore configure ... (from script output)")
                print(f"   3. Run: agentcore launch --agent {AGENT_NAME}")
                print(f"   4. Wait for launch to complete (~10-15 minutes)")
                print(f"\n💡 Or provide the Agent ARN manually:")
                print(f"   python test_mcp_client.py --agent-arn <ARN>")
                sys.exit(1)
        
        # Get bearer token
        bearer_token = None
        if not args.no_auth:
            if args.bearer_token:
                bearer_token = args.bearer_token
                print("✓ Using provided bearer token")
            else:
                # Try to get Cognito credentials from Secrets Manager
                secrets_client = boto3.client('secretsmanager', region_name=region)
                try:
                    response = secrets_client.get_secret_value(
                        SecretId=f'{AGENT_NAME}/cognito/credentials'
                    )
                    cognito_config = json.loads(response['SecretString'])
                    print(f"✓ Retrieved Cognito credentials from Secrets Manager")
                    
                    # Get access token using client credentials flow
                    bearer_token = get_cognito_token(cognito_config)
                    
                except secrets_client.exceptions.ResourceNotFoundException:
                    print(f"⚠️  Cognito credentials not found in Secrets Manager")
                    print(f"   Expected secret: {AGENT_NAME}/cognito/credentials")
                    print(f"\nIf the server was deployed with --no-auth, use --no-auth flag")
                    print(f"Otherwise, provide a bearer token with --bearer-token")
                    sys.exit(1)
        
        # Check runtime status
        if not args.skip_status_check:
            if not check_runtime_status(agent_arn, region):
                print("\n⚠️  Runtime is not ready. Exiting...")
                print("   Run with --skip-status-check to test anyway")
                sys.exit(1)
        
        # Test the MCP server
        await test_mcp_server(agent_arn, region, bearer_token)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
