# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import logging
import sys

from botocore.config import Config
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

IMAGE_FILENAME = "apiendpoint.drawio.png"
REPORT_FILENAME = "report-agent.md"
MODEL_ID = "global.anthropic.claude-sonnet-4-20250514-v1:0"
SYSTEM_PROMPT = "You are an expert in AWS services and serverless architecture."
USER_PROMPT = f"""
Describe the key components and services in the {IMAGE_FILENAME} diagram image.  
Use available knowledge base tools to research AWS services.
Save the analysis into the {REPORT_FILENAME} file.
"""


def main():
    logger.info("Analyzing diagram: %s", IMAGE_FILENAME)

    aws_knowledge_mcp_client = MCPClient(
        lambda: streamablehttp_client("https://knowledge-mcp.global.api.aws")
    )

    with aws_knowledge_mcp_client:
        logger.info("Connected to MCP servers")

        tools = aws_knowledge_mcp_client.list_tools_sync()
        config = Config(read_timeout=300, connect_timeout=60)
        analyze_agent = Agent(
            model=BedrockModel(model_id=MODEL_ID, boto_client_config=config),
            system_prompt=SYSTEM_PROMPT,
            tools=[image_reader, file_write, *tools],
        )
        analyze_agent(USER_PROMPT)

        print()
        sys.stdout.flush()

    logger.info("✅ Analysis Complete!")
    logger.info("📄 Report saved: %s", REPORT_FILENAME)


if __name__ == "__main__":
    main()
