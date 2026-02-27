# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import logging
import sys
from typing import List

from botocore.config import Config
from strands import Agent, tool
from strands.models import BedrockModel
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
REPORT_FILENAME = "proposal1.md"
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
4. In the forth section, recommend AWS services for any databases based on any implied requirements.

Save the analysis into the {REPORT_FILENAME} file in markdown format.
- Include an image link to {IMAGE_FILENAME} (e.g. `![whiteboard image]({IMAGE_FILENAME})`)
- Include an inline version of the sequence diagram inside a `mermaid` code fence.
"""

SERVICE_NAMES_DICT = {
    "Shakespeare": "The editorial service where textbooks are authored.",
    "Gutenberg": "The publishing service that converts textbooks into output formats likes PDF or ePub.",
    "Alexandria": "The library service where published textbooks are stored.",
}


@tool
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


def main():
    logger.info("Analyzing diagram: %s", IMAGE_FILENAME)

    config = Config(read_timeout=300, connect_timeout=60)
    analyze_agent = Agent(
        model=BedrockModel(model_id=MODEL_ID, boto_client_config=config),
        system_prompt=SYSTEM_PROMPT,
        tools=[image_reader, file_write, internal_service_name],
    )
    analyze_agent(USER_PROMPT)
    print()
    sys.stdout.flush()

    logger.info("✅ Basic Analysis Complete!")
    logger.info("📄 Report saved: %s", REPORT_FILENAME)


if __name__ == "__main__":
    main()
