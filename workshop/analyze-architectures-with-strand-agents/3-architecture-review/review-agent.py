# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import logging
import sys

from botocore.config import Config
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from strands_tools import file_read, file_write, image_reader

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

REPORT_FILENAME = "architecture.md"
REVIEW_FILENAME = "review.md"
MODEL_ID = "global.anthropic.claude-sonnet-4-20250514-v1:0"
SYSTEM_PROMPT = "You are an expert in software architecture working for a content publishing company."
USER_PROMPT = f"""
The {REPORT_FILENAME} is a software architecture proposal representing a software system.
The document contains architecture diagram, either as images or inline using diagrams-as-code in Mermaid format.

1. Analyze and understand the text of the architecture proposal and any included, linked, or referenced diagrams.  Look for any inconsistencies between the narrative and the diagrams.
2. Recommend any changes to the architecture proposal based on your research.  Look for any markdown based Architecture Decision Records found in the `adr` folder, and favor those decisions.

Save the Recommend into the {REVIEW_FILENAME} file in markdown format.
"""


def main():
    logger.info("Reviewing architecture: %s", REPORT_FILENAME)

    aws_knowledge_mcp_client = MCPClient(
        lambda: streamablehttp_client("https://knowledge-mcp.global.api.aws")
    )

    with aws_knowledge_mcp_client:
        logger.info("Connected to MCP servers")

        knowledge_tools = aws_knowledge_mcp_client.list_tools_sync()

        config = Config(read_timeout=300, connect_timeout=60)
        analyze_agent = Agent(
            model=BedrockModel(model_id=MODEL_ID, boto_client_config=config),
            system_prompt=SYSTEM_PROMPT,
            tools=[image_reader, file_read, file_write, *knowledge_tools],
        )
        analyze_agent(USER_PROMPT)
        print()
        sys.stdout.flush()

        logger.info("✅ Architecture Review Complete!")
        logger.info("📄 Review saved: %s", REVIEW_FILENAME)


if __name__ == "__main__":
    main()
