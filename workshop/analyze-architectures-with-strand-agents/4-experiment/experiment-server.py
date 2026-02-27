# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from typing import List

from fastmcp import FastMCP
from fastmcp.utilities.logging import configure_logging

# Reconfigure FastMCP logging with custom time format
configure_logging(
    level="INFO",
    log_time_format="%Y-%m-%dT%H:%M:%S",
)
mcp = FastMCP("Experiment Server")

"""
stdio_mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(command="uv", args=["run", "experiment-server.py"])
    )
)
"""

# Idea - create a @mcp.tool

# Idea - create a @mcp.prompt

if __name__ == "__main__":
    mcp.run(show_banner=False)
