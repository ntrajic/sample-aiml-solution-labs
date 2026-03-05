"""
AgentCore MCP Server - Tool Handlers

This package contains all MCP tool handler implementations organized by feature domain.
"""

from .identity_handlers import (
    handle_create_runtime_execution_role_script,
)
from .memory_handlers import (
    handle_memory_create,
    handle_memory_create_event,
    handle_memory_retrieve,
    handle_memory_delete,
)
from .gateway_handlers import (
    handle_gateway_create,
    handle_gateway_add_lambda_target,
    handle_gateway_list_targets,
    handle_gateway_delete_target,
    handle_gateway_delete,
)
from .runtime_handlers import (
    handle_runtime_configure,
    handle_runtime_launch,
    handle_runtime_status,
    handle_runtime_invoke,
    handle_runtime_delete,
)
from .observability_handlers import (
    handle_observability_get_dashboard_url,
    handle_observability_get_logs_info,
    handle_observability_get_recent_logs,
)
from .strands_handlers import (
    handle_generate_strands_agent,
    handle_generate_agentcore_runtime_agent,
)

__all__ = [
    # Identity handlers
    "handle_create_runtime_execution_role_script",
    # Memory handlers
    "handle_memory_create",
    "handle_memory_create_event",
    "handle_memory_retrieve",
    "handle_memory_delete",
    # Gateway handlers
    "handle_gateway_create",
    "handle_gateway_add_lambda_target",
    "handle_gateway_list_targets",
    "handle_gateway_delete_target",
    "handle_gateway_delete",
    # Runtime handlers
    "handle_runtime_configure",
    "handle_runtime_launch",
    "handle_runtime_status",
    "handle_runtime_invoke",
    "handle_runtime_delete",
    # Observability handlers
    "handle_observability_get_dashboard_url",
    "handle_observability_get_logs_info",
    "handle_observability_get_recent_logs",
    # Strands handlers
    "handle_generate_strands_agent",
    "handle_generate_agentcore_runtime_agent",
]
