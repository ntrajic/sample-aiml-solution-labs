#!/usr/bin/env python3
"""
AWS Bedrock AgentCore MCP Server

Build production-ready AI agents with AWS Bedrock AgentCore using natural language.

This MCP server provides tools for:
- Identity: IAM roles and Cognito authentication
- Memory: Conversation storage with semantic search
- Gateway: Lambda function exposure with OAuth
- Runtime: Serverless agent deployment
- Observability: CloudWatch monitoring and logs
- Strands: Agent code generation

PREREQUISITES:
Before using these tools, you need AWS credentials configured and access to:
- AWS Bedrock
- AWS IAM
- AWS Lambda
- AWS Cognito
- AWS CloudWatch

PACKAGE REQUIREMENTS:
- fastmcp>=0.1.0
- bedrock-agentcore>=1.2.0
- strands-agents>=1.22.0
- strands-agents-tools>=0.2.19
- boto3>=1.34.0
- requests>=2.31.0

For detailed examples, see: https://github.com/awslabs/mcp-aws-bedrock-agentcore
"""

from typing import Optional
from fastmcp import FastMCP

# Import handlers
from handlers import (
    # Identity handlers
    handle_create_runtime_execution_role_script,
    
    # Memory handlers
    handle_memory_create,
    handle_memory_create_event,
    handle_memory_retrieve,
    handle_memory_delete,

    # Gateway handlers
    handle_gateway_create,
    handle_gateway_add_lambda_target,
    handle_gateway_list_targets,
    handle_gateway_delete_target,
    handle_gateway_delete,
    
    # Runtime handlers
    handle_runtime_configure,
    handle_runtime_launch,
    handle_runtime_status,
    handle_runtime_invoke,
    handle_runtime_delete,
    
    # Observability handlers
    handle_observability_get_dashboard_url,
    handle_observability_get_logs_info,
    handle_observability_get_recent_logs,
    
    # Strands handlers
    handle_generate_strands_agent,
    handle_generate_agentcore_runtime_agent,
)

# Initialize FastMCP server
mcp = FastMCP("aws-bedrock-agentcore")


# ============================================================================
# IDENTITY TOOLS
# ============================================================================

@mcp.tool()
async def agentcore_create_runtime_execution_role_script(
    region: str = "us-west-2"
) -> dict:
    """Generate script to create IAM execution role for AgentCore Runtime.
    
    This script creates an IAM role with minimal required permissions for running
    agents in AgentCore Runtime, including:
    - ECR: Container image access
    - CloudWatch Logs: Logging and monitoring
    - X-Ray: Distributed tracing
    - Bedrock: Model invocation
    - AgentCore Memory: Conversation history
    - Workload Identity: Secure credentials
    
    Args:
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Generated script with code, filename, and instructions
    """
    return await handle_create_runtime_execution_role_script({"region": region})


# ============================================================================
# MEMORY TOOLS
# ============================================================================

@mcp.tool()
async def agentcore_memory_create(
    name: str,
    strategies: list[dict],
    description: str = "",
    region: str = "us-west-2"
) -> dict:
    """Create an AgentCore Memory resource with memory strategies.
    
    Memory enables agents to remember customer preferences, past conversations,
    and context across sessions through three strategies:
    - USER_PREFERENCE: Captures customer preferences (e.g., "prefers Python")
    - SEMANTIC: Stores factual details (e.g., "purchased Fire TV Stick")
    - SUMMARY: Maintains conversation context and summaries
    
    Processing: Memory strategies process data asynchronously (20-30 seconds).
    
    Args:
        name: Unique identifier for the memory resource (alphanumeric with underscores)
        strategies: Array of memory strategy objects. Each strategy format:
            - summaryMemoryStrategy: {'name': 'summary', 'namespaces': ['app/{actorId}/{sessionId}/summary']}
            - userPreferenceMemoryStrategy: {'name': 'preferences', 'namespaces': ['app/{actorId}/preferences']}
            - semanticMemoryStrategy: {'name': 'semantic', 'namespaces': ['app/{actorId}/semantic']}
        description: Human-readable description of the memory's purpose
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Generated script with code, filename, and instructions
    """
    return await handle_memory_create({
        "name": name,
        "strategies": strategies,
        "description": description,
        "region": region
    })


@mcp.tool()
async def agentcore_memory_create_event(
    memory_id: str,
    actor_id: str,
    session_id: str,
    messages: list[tuple[str, str]],
    region: str = "us-west-2"
) -> dict:
    """Store conversation messages in AgentCore Memory.
    
    Messages are stored immediately in short-term memory, then asynchronously
    processed (20-30 seconds) into long-term memory strategies:
    - Preferences extracted → USER_PREFERENCE namespace
    - Facts embedded → SEMANTIC namespace
    - Summaries generated → SUMMARY namespace
    
    Args:
        memory_id: Memory ID from agentcore_memory_create (e.g., 'my_memory-ABC123')
        actor_id: Unique identifier for the user (e.g., 'user_001')
        session_id: Unique identifier for the session (e.g., 'session_20240116')
        messages: List of (message, role) tuples where role is 'USER' or 'ASSISTANT'
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Generated script with code, filename, and instructions
    """
    return await handle_memory_create_event({
        "memory_id": memory_id,
        "actor_id": actor_id,
        "session_id": session_id,
        "messages": messages,
        "region": region
    })


@mcp.tool()
async def agentcore_memory_retrieve(
    memory_id: str,
    namespace: str,
    query: str,
    top_k: int = 3,
    relevance_score: float = 0.2,
    region: str = "us-west-2"
) -> dict:
    """Retrieve memories using semantic search.
    
    Query memories by namespace pattern and search text. Returns relevant
    memories ranked by semantic similarity.
    
    Namespace patterns:
    - Preferences: 'app/{actorId}/preferences'
    - Semantic: 'app/{actorId}/semantic'
    - Summary: 'app/{actorId}/{sessionId}/summary'
    
    Use actual values (e.g., 'app/user_001/preferences') not placeholders.
    
    Args:
        memory_id: Memory ID to query (e.g., 'my_memory-ABC123')
        namespace: Namespace pattern with actual values (e.g., 'app/user_001/preferences')
        query: Natural language search query (e.g., 'user preferences and settings')
        top_k: Maximum number of results to return (default: 3)
        relevance_score: Minimum similarity threshold 0.0-1.0 (default: 0.2)
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Generated script with code, filename, and instructions
    """
    return await handle_memory_retrieve({
        "memory_id": memory_id,
        "namespace": namespace,
        "query": query,
        "top_k": top_k,
        "relevance_score": relevance_score,
        "region": region
    })


@mcp.tool()
async def agentcore_memory_delete(
    memory_id: str,
    region: str = "us-west-2"
) -> dict:
    """Delete an AgentCore Memory resource and all associated data.
    
    WARNING: This permanently deletes the memory and all stored conversations,
    preferences, and summaries. This action cannot be undone.
    
    Args:
        memory_id: Memory ID to delete (e.g., 'my_memory-ABC123')
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Generated script with code, filename, and instructions
    """
    return await handle_memory_delete({
        "memory_id": memory_id,
        "region": region
    })


# ============================================================================
# GATEWAY TOOLS
# ============================================================================

@mcp.tool()
async def agentcore_gateway_create(
    name: str,
    role_arn: str,
    cognito_client_id: str,
    cognito_discovery_url: str,
    protocol_type: str = "MCP",
    authorizer_type: str = "CUSTOM_JWT",
    description: str = "",
    region: str = "us-west-2"
) -> dict:
    """Create an AgentCore Gateway with OAuth authentication.
    
    Gateway provides a unified, secure interface for agents to discover and
    invoke tools. It handles authentication, authorization, and protocol
    translation automatically.
    
    Args:
        name: Gateway name (must be unique within AWS account)
        role_arn: IAM role ARN for gateway execution
        cognito_client_id: Cognito app client ID for token validation
        cognito_discovery_url: Cognito OIDC discovery URL
        protocol_type: Protocol type (default: MCP)
        authorizer_type: Authorization type (default: CUSTOM_JWT)
        description: Human-readable description of gateway purpose
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Generated script with code, filename, and instructions
    """
    return await handle_gateway_create({
        "name": name,
        "role_arn": role_arn,
        "cognito_client_id": cognito_client_id,
        "cognito_discovery_url": cognito_discovery_url,
        "protocol_type": protocol_type,
        "authorizer_type": authorizer_type,
        "description": description,
        "region": region
    })


@mcp.tool()
async def agentcore_gateway_add_lambda_target(
    gateway_id: str,
    target_name: str,
    lambda_arn: str,
    tool_schema: list[dict],
    target_description: str = "",
    region: str = "us-west-2"
) -> dict:
    """Add a Lambda function as a gateway target with MCP tool schema.
    
    Targets are the actual services (Lambda functions) that the gateway exposes
    as tools. Each target has a tool schema that defines its inputs and outputs.
    
    Args:
        gateway_id: Gateway ID to attach target to
        target_name: Name for the target (e.g., 'CreateRefundRequest')
        lambda_arn: Lambda function ARN
        tool_schema: MCP tool schema array with tool definitions. Each tool must have:
            - name: Tool function name (string)
            - description: What the tool does (string)
            - inputSchema: JSON Schema for tool inputs (object)
        target_description: Description of what this target does
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Generated script with code, filename, and instructions
    """
    return await handle_gateway_add_lambda_target({
        "gateway_id": gateway_id,
        "target_name": target_name,
        "lambda_arn": lambda_arn,
        "tool_schema": tool_schema,
        "target_description": target_description,
        "region": region
    })


@mcp.tool()
async def agentcore_gateway_list_targets(
    gateway_id: str,
    region: str = "us-west-2"
) -> dict:
    """List all targets attached to a gateway.
    
    Use this to see what tools are available through the gateway and verify
    target configuration.
    
    Args:
        gateway_id: Gateway ID to list targets for
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Generated script with code, filename, and instructions
    """
    return await handle_gateway_list_targets({
        "gateway_id": gateway_id,
        "region": region
    })


@mcp.tool()
async def agentcore_gateway_delete_target(
    gateway_id: str,
    target_id: str,
    region: str = "us-west-2"
) -> dict:
    """Delete a target from AgentCore Gateway.
    
    WARNING: This removes the tool from the gateway. Agents will no longer
    be able to access this tool.
    
    Args:
        gateway_id: Gateway ID
        target_id: Target ID to delete
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Generated script with code, filename, and instructions
    """
    return await handle_gateway_delete_target({
        "gateway_id": gateway_id,
        "target_id": target_id,
        "region": region
    })


@mcp.tool()
async def agentcore_gateway_delete(
    gateway_id: str,
    region: str = "us-west-2"
) -> dict:
    """Delete an AgentCore Gateway.
    
    WARNING: This permanently deletes the gateway and all its targets. Agents
    will no longer be able to access any tools through this gateway.
    
    Args:
        gateway_id: Gateway ID to delete
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Generated script with code, filename, and instructions
    """
    return await handle_gateway_delete({
        "gateway_id": gateway_id,
        "region": region
    })


# ============================================================================
# RUNTIME TOOLS
# ============================================================================

@mcp.tool()
async def agentcore_runtime_configure(
    entrypoint: str,
    agent_name: str,
    execution_role: str,
    cognito_client_id: str,
    cognito_discovery_url: str,
    auto_create_ecr: bool = True,
    memory_mode: str = "NO_MEMORY",
    requirements_file: str = "requirements.txt",
    region: str = "us-west-2"
) -> dict:
    """Configure AgentCore Runtime deployment settings.
    
    Runtime eliminates infrastructure management. Your agent runs in a serverless
    environment with auto-scaling, health monitoring, and built-in observability.
    
    Args:
        entrypoint: Python file with @app.entrypoint decorator (e.g., 'agent_runtime.py')
        agent_name: Name for the agent deployment
        execution_role: IAM execution role ARN with Bedrock, Memory, KB permissions
        cognito_client_id: Cognito app client ID for authentication
        cognito_discovery_url: Cognito OIDC discovery URL
        auto_create_ecr: Automatically create ECR repository (default: True)
        memory_mode: Memory mode (default: NO_MEMORY)
        requirements_file: Python requirements file (default: requirements.txt)
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Generated script with code, filename, and instructions
    """
    return await handle_runtime_configure({
        "entrypoint": entrypoint,
        "agent_name": agent_name,
        "execution_role": execution_role,
        "cognito_client_id": cognito_client_id,
        "cognito_discovery_url": cognito_discovery_url,
        "auto_create_ecr": auto_create_ecr,
        "memory_mode": memory_mode,
        "requirements_file": requirements_file,
        "region": region
    })


@mcp.tool()
async def agentcore_runtime_launch(
    env_vars: dict,
    auto_update_on_conflict: bool = True,
    region: str = "us-west-2"
) -> dict:
    """Deploy agent to AgentCore Runtime.
    
    This creates a CodeBuild pipeline, builds Docker container, pushes to ECR,
    and deploys to runtime. Process takes 5-10 minutes.
    
    Args:
        env_vars: Environment variables (MEMORY_ID, KNOWLEDGE_BASE_ID, GATEWAY_URL,
                 COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET, COGNITO_DISCOVERY_URL, etc.)
        auto_update_on_conflict: Automatically update if agent already exists (default: True)
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Generated script with code, filename, and instructions
    """
    return await handle_runtime_launch({
        "env_vars": env_vars,
        "auto_update_on_conflict": auto_update_on_conflict,
        "region": region
    })


@mcp.tool()
async def agentcore_runtime_status(
    region: str = "us-west-2"
) -> dict:
    """Check AgentCore Runtime deployment status.
    
    Monitor deployment progress. Agent goes through stages: CREATING, READY,
    CREATE_FAILED, etc.
    
    Args:
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Generated script with code, filename, and instructions
    """
    return await handle_runtime_status({"region": region})


@mcp.tool()
async def agentcore_runtime_invoke(
    payload: dict,
    bearer_token: str,
    region: str = "us-west-2"
) -> dict:
    """Invoke a deployed AgentCore Runtime agent.
    
    Test the agent with queries. Requires valid OAuth bearer token.
    
    Args:
        payload: Request payload with 'prompt' and optional 'actor_id'
        bearer_token: OAuth bearer token from Cognito
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Generated script with code, filename, and instructions
    """
    return await handle_runtime_invoke({
        "payload": payload,
        "bearer_token": bearer_token,
        "region": region
    })


@mcp.tool()
async def agentcore_runtime_delete(
    region: str = "us-west-2"
) -> dict:
    """Delete an AgentCore Runtime agent deployment.
    
    WARNING: This permanently deletes the agent runtime. The agent will no
    longer be accessible.
    
    Args:
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Generated script with code, filename, and instructions
    """
    return await handle_runtime_delete({"region": region})


# ============================================================================
# OBSERVABILITY TOOLS
# ============================================================================

@mcp.tool()
async def agentcore_observability_get_dashboard_url(
    region: str = "us-west-2"
) -> dict:
    """Get CloudWatch GenAI Observability dashboard URL.
    
    AgentCore Runtime automatically logs traces to CloudWatch, providing:
    - Request Tracing: Complete conversation flow, tool invocations
    - Performance Monitoring: Response times, success rates
    - Debugging: Pattern analysis, bottleneck identification
    
    Args:
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Dashboard URL and monitoring information
    """
    return await handle_observability_get_dashboard_url({"region": region})


@mcp.tool()
async def agentcore_observability_get_logs_info(
    agent_arn: str,
    region: str = "us-west-2"
) -> dict:
    """Get CloudWatch log group information for viewing agent logs.
    
    Provides log group name and AWS CLI commands for tailing and viewing logs.
    Logs include all agent interactions, tool calls, errors, and performance data.
    
    Args:
        agent_arn: Agent ARN (e.g., 'arn:aws:bedrock-agentcore:us-west-2:123:runtime/my_agent-ABC')
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Log group name, agent ARN, and CLI commands
    """
    return await handle_observability_get_logs_info({
        "agent_arn": agent_arn,
        "region": region
    })


@mcp.tool()
async def agentcore_observability_get_recent_logs(
    agent_arn: str,
    hours_back: int = 1,
    limit: int = 50,
    region: str = "us-west-2"
) -> dict:
    """Retrieve recent logs from CloudWatch for the deployed agent.
    
    Fetches the most recent log events from the agent's log group, useful for
    debugging and monitoring.
    
    Args:
        agent_arn: Agent ARN (e.g., 'arn:aws:bedrock-agentcore:us-west-2:123:runtime/my_agent-ABC')
        hours_back: How many hours back to retrieve logs (default: 1)
        limit: Maximum number of log events to retrieve (default: 50)
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Recent log events with timestamps and messages
    """
    return await handle_observability_get_recent_logs({
        "agent_arn": agent_arn,
        "hours_back": hours_back,
        "limit": limit,
        "region": region
    })


# ============================================================================
# STRANDS AGENT CODE GENERATION TOOLS
# ============================================================================

@mcp.tool()
async def generate_strands_agent(
    agent_name: str,
    system_prompt: str,
    tools: Optional[list[str]] = None,
    custom_tools: Optional[list[dict]] = None,
    include_memory: bool = False,
    memory_namespaces: Optional[list[str]] = None,
    include_kb: bool = False,
    include_gateway: bool = False,
    model_id: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    temperature: float = 0.3,
    region: str = "us-west-2"
) -> dict:
    """Generate standalone Strands Agent Python code with specified tools and integrations.
    
    Creates a complete Strands agent with built-in and custom tools using
    @tool decorator pattern. Supports optional integrations with AgentCore Memory,
    Knowledge Base, and Gateway.
    
    Args:
        agent_name: Name for the agent (used in filename)
        system_prompt: System prompt for the agent
        tools: List of built-in tool names (e.g., ['retrieve', 'current_time'])
        custom_tools: List of custom tool definitions with name, description, and code
        include_memory: Enable AgentCore Memory integration (default: False)
        memory_namespaces: Memory namespaces to retrieve from (default: ['semantic', 'preferences', 'summary'])
        include_kb: Enable Knowledge Base integration via retrieve tool (default: False)
        include_gateway: Enable Gateway integration for MCP tools (default: False)
        model_id: Bedrock model ID (default: claude-sonnet-4-5)
        temperature: Model temperature 0.0-1.0 (default: 0.3)
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Generated agent code with filename and instructions
    
    Example:
        # Generate agent with memory and gateway
        generate_strands_agent(
            agent_name="customer_service_agent",
            system_prompt="You are a helpful customer service agent",
            include_memory=True,
            include_gateway=True
        )
    """
    return await handle_generate_strands_agent({
        "agent_name": agent_name,
        "system_prompt": system_prompt,
        "tools": tools or [],
        "custom_tools": custom_tools or [],
        "include_memory": include_memory,
        "memory_namespaces": memory_namespaces or ["semantic", "preferences", "summary"],
        "include_kb": include_kb,
        "include_gateway": include_gateway,
        "model_id": model_id,
        "temperature": temperature,
        "region": region
    })


@mcp.tool()
async def generate_agentcore_runtime_agent(
    agent_name: str,
    system_prompt: str,
    include_memory: bool = True,
    include_gateway: bool = False,
    include_kb: bool = False,
    memory_namespaces: Optional[list[str]] = None,
    additional_tools: Optional[list[str]] = None,
    model_id: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    temperature: float = 0.3,
    region: str = "us-west-2"
) -> dict:
    """Generate AgentCore Runtime-ready Strands Agent with integrations.
    
    Creates a production-ready agent with BedrockAgentCoreApp entrypoint,
    memory integration, and gateway tools.
    
    Args:
        agent_name: Name for the agent (used in filename)
        system_prompt: System prompt for the agent
        include_memory: Include AgentCore Memory integration (default: True)
        include_gateway: Include Gateway MCP tools (default: False)
        include_kb: Include Knowledge Base retrieve tool (default: False)
        memory_namespaces: Memory namespace patterns (default: ['semantic', 'preferences', 'summary'])
        additional_tools: Additional tool names to include (e.g., ['current_time'])
        model_id: Bedrock model ID (default: claude-sonnet-4-5)
        temperature: Model temperature 0.0-1.0 (default: 0.3)
        region: AWS region (default: us-west-2)
    
    Returns:
        dict: Generated agent code with filename and instructions
    """
    return await handle_generate_agentcore_runtime_agent({
        "agent_name": agent_name,
        "system_prompt": system_prompt,
        "include_memory": include_memory,
        "include_gateway": include_gateway,
        "include_kb": include_kb,
        "memory_namespaces": memory_namespaces or ["semantic", "preferences", "summary"],
        "additional_tools": additional_tools or [],
        "model_id": model_id,
        "temperature": temperature,
        "region": region
    })


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    mcp.run()
