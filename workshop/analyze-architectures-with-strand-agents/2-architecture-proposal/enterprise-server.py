# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from typing import List

import marko
from fastmcp import FastMCP
from fastmcp.utilities.logging import configure_logging

# Reconfigure FastMCP logging with custom time format
configure_logging(
    level="INFO",
    log_time_format="%Y-%m-%dT%H:%M:%S",
)
mcp = FastMCP("Enterprise Knowledge Server")

"""
stdio_mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(command="uv", args=["run", "enterprise-server.py"])
    )
)
"""

SERVICE_NAMES_DICT = {}


def load_service_names():
    with open("internal-service-names.md", "r", encoding="utf-8") as f:
        markdown_content = f.read()
        doc = marko.parse(markdown_content)
        current_key = None
        current_content = []

        for element in doc.children:
            if element.__class__.__name__ == "Heading" and element.level == 2:
                if current_key:
                    SERVICE_NAMES_DICT[current_key] = "\n".join(current_content).strip()
                current_key = element.children[0].children
                current_content = []
            elif current_key and element.__class__.__name__ == "Paragraph":
                current_content.append(element.children[0].children)

        if current_key:
            SERVICE_NAMES_DICT[current_key] = "\n".join(current_content).strip()


@mcp.tool
def internal_service_name(service_names: List[str]) -> dict:
    """Gets the description for an internal service name from the proper name.

    Args:
        service_names: The list of internal service names
    """
    result = []
    for item in service_names:
        if item in SERVICE_NAMES_DICT:
            result.append({"name": item, "description": SERVICE_NAMES_DICT[item]})

    return {"service_names": result}


if __name__ == "__main__":
    load_service_names()
    mcp.run(show_banner=False)
