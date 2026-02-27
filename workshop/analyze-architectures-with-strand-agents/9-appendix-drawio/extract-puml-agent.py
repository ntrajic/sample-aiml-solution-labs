# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import logging
import sys

from botocore.config import Config
from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from strands_tools import file_read, file_write

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s:  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# https://strandsagents.com/latest/documentation/docs/user-guide/observability-evaluation/logs/
logging.getLogger("strands").setLevel(logging.INFO)
logging.getLogger("strands_tools").setLevel(logging.INFO)

IMAGE_FILENAME = "CRUD-PlantUML.drawio"
MODEL_ID = "global.anthropic.claude-sonnet-4-20250514-v1:0"
SYSTEM_PROMPT = "You are an expert in creating architecture diagrams."


def main():
    logger.info("Analyzing diagram: %s", IMAGE_FILENAME)

    drawio_mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(command="uv", args=["run", "drawio-server.py"])
        )
    )

    with drawio_mcp_client:
        logger.info("Connected to MCP servers")

        tools = drawio_mcp_client.list_tools_sync()
        config = Config(read_timeout=300, connect_timeout=60)
        analyze_agent = Agent(
            model=BedrockModel(model_id=MODEL_ID, boto_client_config=config),
            system_prompt=SYSTEM_PROMPT,
            tools=[file_read, file_write, *tools],
        )

        logger.info("Starting agent execution")
        # directly invoke tool.file_read as a method
        file_result = analyze_agent.tool.file_read(path=IMAGE_FILENAME, mode="lines")
        if file_result["status"] == "success":
            drawio_xml = file_result["content"][0]["text"]
            # directly invoke tool.extract_plantuml_from_drawio as a method
            plantuml_result = analyze_agent.tool.extract_plantuml_from_drawio(
                drawio_xml_string=drawio_xml
            )
            if plantuml_result["status"] == "success":
                # the agent loop will use tool file_write
                analyze_agent(
                    f"save any PlantUML content to a file with the format <id>.puml. Context: {plantuml_result}"
                )
                print()
                sys.stdout.flush()

                logger.info("✅ Extraction Complete!")


if __name__ == "__main__":
    main()
