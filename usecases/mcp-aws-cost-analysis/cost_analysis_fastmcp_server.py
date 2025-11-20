#!/usr/bin/env python3
"""
FastMCP HTTP Server for AWS Cost Analysis Tools

This server exposes the Strands-based cost calculation tools via HTTP MCP protocol,
providing streamable responses and better web integration capabilities.
"""

import os
import json
import logging
import inspect
from typing import Dict, Any, List, Optional

from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

# Set up environment for tools
os.environ["BYPASS_TOOL_CONSENT"] = "true"
os.environ["PYTHON_REPL_INTERACTIVE"] = "false"

# Import the Strands tools
from utils.pricing_util import get_bedrock_pricing, get_agentcore_pricing, get_aws_pricing, get_attribute_values
from utils.use_bedrock_calculator import use_bedrock_calculator, bedrock_what_if_analysis
from utils.use_agentcore_calculator import use_agentcore_calculator, agentcore_what_if_analysis
from utils.bva_calculator import bva_calculator, bva_what_if_analysis

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Set the desired logging level (e.g., INFO, DEBUG, WARNING, ERROR)

# Create a console handler and set its level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Create a formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add formatter to handler
ch.setFormatter(formatter)

# Add handler to logger
logger.addHandler(ch)

# Create FastMCP application
mcp = FastMCP(host="0.0.0.0", stateless_http=True)

# Helper function to create tools with original docstrings
def create_tool_with_docstring(original_func, tool_func):
    """Copy docstring from original function to MCP tool function"""
    if original_func.__doc__:
        tool_func.__doc__ = original_func.__doc__
    return tool_func

@mcp.tool(description=get_bedrock_pricing.__doc__ or "Get pricing information for Amazon Bedrock models")
def get_bedrock_pricing_tool_read_only(
    model_name: str,
    region: str = "us-west-2"
) -> Dict[str, Any]:
    try:
        logger.info(f"Getting Bedrock pricing for {model_name} in {region}")
        result = get_bedrock_pricing(model_name, region)
        # Wrap list result in a dict for FastMCP compatibility
        return {"pricing_data": result, "count": len(result) if isinstance(result, list) else 0}
    except Exception as e:
        logger.error(f"Error getting Bedrock pricing: {str(e)}")
        return {"error": f"Failed to get Bedrock pricing: {str(e)}"}


@mcp.tool(description=get_aws_pricing.__doc__ or "Get pricing information for AWS components")
def get_aws_pricing_tool_read_only(
    service_code: str,
    region: str = "us-west-2"
) -> Dict[str, Any]:
    try:
        logger.info(f"Getting AWS pricing for {service_code} in {region}")
        result = get_aws_pricing(service_code, None, region)
        # Wrap list result in a dict for FastMCP compatibility
        return {"pricing_data": result, "count": len(result) if isinstance(result, list) else 0}
    except Exception as e:
        logger.error(f"Error getting AWS pricing: {str(e)}")
        return {"error": f"Failed to get AWS pricing: {str(e)}"}

@mcp.tool(description=get_attribute_values.__doc__ or "Get attribute values")
def get_attribute_values_tool_read_only(
    service_code: str ,
    attribute_name: str
) -> Dict[str, Any]:
    try:
        logger.info(f"Getting attribute values for {service_code}, {attribute_name}")
        result = get_attribute_values(service_code, attribute_name)
        # Wrap list result in a dict for FastMCP compatibility
        return {"attribute_values": result, "count": len(result) if isinstance(result, list) else 0}
    except Exception as e:
        logger.error(f"Error getting attribute values: {str(e)}")
        return {"error": f"Failed to get attribute values: {str(e)}"}



@mcp.tool(description=get_agentcore_pricing.__doc__ or "Get pricing information for AWS AgentCore components")
def get_agentcore_pricing_tool_read_only(
    region: str = "us-west-2"
) -> Dict[str, Any]:
    try:
        logger.info(f"Getting AgentCore pricing for all components in {region}")
        result = get_agentcore_pricing(region)
        # Wrap list result in a dict for FastMCP compatibility
        return {"pricing_data": result, "count": len(result) if isinstance(result, list) else 0}
    except Exception as e:
        logger.error(f"Error getting AgentCore pricing: {str(e)}")
        return {"error": f"Failed to get AgentCore pricing: {str(e)}"}

@mcp.tool(description=use_bedrock_calculator.__doc__ or "Calculate costs for Amazon Bedrock usage based on input parameters")
def bedrock_calculator_tool_read_only(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        logger.info("Calculating Bedrock costs")
        result = use_bedrock_calculator(params)
        return result
    except Exception as e:
        logger.error(f"Error calculating Bedrock costs: {str(e)}")
        return {"error": f"Bedrock calculation failed: {str(e)}"}

@mcp.tool(description=bedrock_what_if_analysis.__doc__ or "Perform what-if analysis for Amazon Bedrock costs by varying parameters")
def bedrock_what_if_tool_read_only(
    base_params: Dict[str, Any],
    primary_variable: str,
    primary_range: List[Any],
    secondary_variable: Optional[str] = None,
    secondary_range: Optional[List[Any]] = None
) -> Dict[str, Any]:
    try:
        logger.info(f"Running Bedrock what-if analysis: {primary_variable}")
        result = bedrock_what_if_analysis(
            base_params, primary_variable, primary_range, 
            secondary_variable, secondary_range
        )
        return result
    except Exception as e:
        logger.error(f"Error in Bedrock what-if analysis: {str(e)}")
        return {"error": f"Bedrock what-if analysis failed: {str(e)}"}

@mcp.tool(description=use_agentcore_calculator.__doc__ or "Calculate costs for AWS AgentCore usage based on input parameters")
def agentcore_calculator_tool_read_only(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        logger.info("Calculating AgentCore costs")
        result = use_agentcore_calculator(params)
        return result
    except Exception as e:
        logger.error(f"Error calculating AgentCore costs: {str(e)}")
        return {"error": f"AgentCore calculation failed: {str(e)}"}

@mcp.tool(description=agentcore_what_if_analysis.__doc__ or "Perform what-if analysis for AWS AgentCore costs by varying parameters")
def agentcore_what_if_tool_read_only(
    base_params: Dict[str, Any],
    primary_variable: str,
    primary_range: List[Any],
    secondary_variable: Optional[str] = None,
    secondary_range: Optional[List[Any]] = None
) -> Dict[str, Any]:
    try:
        logger.info(f"Running AgentCore what-if analysis: {primary_variable}")
        result = agentcore_what_if_analysis(
            base_params, primary_variable, primary_range,
            secondary_variable, secondary_range
        )
        return result
    except Exception as e:
        logger.error(f"Error in AgentCore what-if analysis: {str(e)}")
        return {"error": f"AgentCore what-if analysis failed: {str(e)}"}

@mcp.tool(description=bva_calculator.__doc__ or "Calculate business value analysis including ROI and cost-benefit metrics")
def business_value_calculator_tool_read_only(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        logger.info("Calculating business value analysis")
        result = bva_calculator(params)
        return result
    except Exception as e:
        logger.error(f"Error calculating business value: {str(e)}")
        return {"error": f"Business value calculation failed: {str(e)}"}

@mcp.tool(description=bva_what_if_analysis.__doc__ or "Perform what-if analysis for business value calculations by varying parameters")
def business_value_what_if_tool_read_only(
    base_params: Dict[str, Any],
    primary_variable: str,
    primary_range: List[Any],
    secondary_variable: Optional[str] = None,
    secondary_range: Optional[List[Any]] = None
) -> Dict[str, Any]:
    try:
        logger.info(f"Running business value what-if analysis: {primary_variable}")
        result = bva_what_if_analysis(
            base_params, primary_variable, primary_range,
            secondary_variable, secondary_range
        )
        return result
    except Exception as e:
        logger.error(f"Error in business value what-if analysis: {str(e)}")
        return {"error": f"Business value what-if analysis failed: {str(e)}"}

@mcp.tool(description="Health check endpoint to verify server status and tool availability")
def health_check() -> Dict[str, Any]:
    """
    Health check endpoint to verify server status and tool availability.
    
    Returns:
        Dict with server status and available tools
    """
    try:
        return {
            "status": "healthy",
            "server": "AWS Cost Analysis FastMCP Server",
            "version": "1.0.0",
            "available_tools": [
                "get_bedrock_pricing_tool",
                "get_agentcore_pricing_tool", 
                "bedrock_calculator_tool",
                "bedrock_what_if_tool",
                "agentcore_calculator_tool",
                "agentcore_what_if_tool",
                "business_value_calculator_tool",
                "business_value_what_if_tool",
                "get_aws_pricing_tool",
                "get_attribute_values_tool"
                ""
            ],
            "environment": {
                "bypass_tool_consent": os.environ.get("BYPASS_TOOL_CONSENT"),
                "python_repl_interactive": os.environ.get("PYTHON_REPL_INTERACTIVE")
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Copy docstrings from original functions to MCP tools
get_bedrock_pricing_tool_read_only.__doc__ = get_bedrock_pricing.__doc__
get_agentcore_pricing_tool_read_only.__doc__ = get_agentcore_pricing.__doc__
bedrock_calculator_tool_read_only.__doc__ = use_bedrock_calculator.__doc__
bedrock_what_if_tool_read_only.__doc__ = bedrock_what_if_analysis.__doc__
agentcore_calculator_tool_read_only.__doc__ = use_agentcore_calculator.__doc__
agentcore_what_if_tool_read_only.__doc__ = agentcore_what_if_analysis.__doc__
business_value_calculator_tool_read_only.__doc__ = bva_calculator.__doc__
business_value_what_if_tool_read_only.__doc__ = bva_what_if_analysis.__doc__
get_aws_pricing_tool_read_only.__doc__ = get_aws_pricing.__doc__
get_attribute_values_tool_read_only.__doc__ = get_attribute_values.__doc__


def main():
    """
    Start the FastMCP HTTP server.
    """
    logger.info("Starting AWS Cost Analysis FastMCP Server...")
    mcp.run(transport="streamable-http")
    # import uvicorn
    
    # logger.info("Starting AWS Cost Analysis FastMCP Server...")
    # logger.info("Available at: http://localhost:8000")
    # logger.info("Health check: http://localhost:8000/health")
    
    # # Create the FastAPI app
    # app = mcp.create_app()
    
    # # Run the server
    # uvicorn.run(
    #     app,
    #     host="0.0.0.0",
    #     port=8000,
    #     log_level="info",
    #     access_log=True
    # )

if __name__ == "__main__":
    main()