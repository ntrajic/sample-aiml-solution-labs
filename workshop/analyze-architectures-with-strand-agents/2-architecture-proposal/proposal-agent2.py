# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import logging
import sys

from botocore.config import Config
from mcp import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from strands_tools import file_write, image_reader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s:  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# https://strandsagents.com/latest/documentation/docs/user-guide/observability-evaluation/logs/
logging.getLogger("strands").setLevel(logging.INFO)
logging.getLogger("strands_tools").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.INFO)
logging.getLogger("boto3").setLevel(logging.INFO)

IMAGE_FILENAME = "whiteboard.jpg"
REPORT_FILENAME = "proposal2.md"
MODEL_ID = "global.anthropic.claude-sonnet-4-20250514-v1:0"
SYSTEM_PROMPT = "You are an expert in software architecture working for a content publishing company."
USER_PROMPT = f"""
The {IMAGE_FILENAME} diagram image is a photograph of a whiteboard representing an architecture diagram of a software system.
The diagram includes numbers inside circles which indicate the order of operations.

Use the internal_service_name tool to find descriptions of the content publishing company's internal services.

Use markdown to apply header 2 to section titles.
1. In the first section, describe the key components and services in the attached diagram.
2. In the second section, describe the data flow of this diagram based on the order of the numbered circles.
3. In the third section, convert the Data Flow Description section into a Mermaid formatted sequence diagram.  Favor `actor` over `participant` for any user or person.
4. In the forth section, recommend AWS services for any databases based on any implied requirements.  When researching, include specifics on how capabilities (like search) are supported by your recommendation.
5. In the fifth section, create a Mermaid formatted C4 model diagram representing the system.  Ensure you treat items found using the internal_service_name tool as external services (`System_Ext`) and any person directly interacting with external services as `Person_Ext`.  Include the other services inside a `System_Boundary`.  Leave default styles - DO NOT use `UpdateElementStyle`.

Save the analysis into the {REPORT_FILENAME} file in markdown format.
- Include an image link to {IMAGE_FILENAME} (e.g. `![whiteboard image]({IMAGE_FILENAME})`)
- Include an inline version of any diagrams inside a `mermaid` code fence.
"""


def main():
    logger.info("Analyzing diagram: %s", IMAGE_FILENAME)

    enterprise_mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(command="uv", args=["run", "enterprise-server.py"])
        )
    )
    aws_knowledge_mcp_client = MCPClient(
        lambda: streamablehttp_client("https://knowledge-mcp.global.api.aws")
    )

    with enterprise_mcp_client, aws_knowledge_mcp_client:
        logger.info("Connected to MCP servers")

        proposal_tools = enterprise_mcp_client.list_tools_sync()
        knowledge_tools = aws_knowledge_mcp_client.list_tools_sync()

        config = Config(read_timeout=300, connect_timeout=60)
        analyze_agent = Agent(
            model=BedrockModel(model_id=MODEL_ID, boto_client_config=config),
            system_prompt=SYSTEM_PROMPT,
            tools=[image_reader, file_write, *proposal_tools, *knowledge_tools],
        )
        analyze_agent(USER_PROMPT)
        print()
        sys.stdout.flush()

        logger.info("✅ Advanced Analysis Complete!")
        logger.info("📄 Report saved: %s", REPORT_FILENAME)


if __name__ == "__main__":
    main()
