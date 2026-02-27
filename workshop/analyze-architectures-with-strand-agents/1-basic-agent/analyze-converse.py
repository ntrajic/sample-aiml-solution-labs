# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import loggin
import os

import boto3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s:  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

IMAGE_FILENAME = "apiendpoint.drawio.png"
REPORT_FILENAME = "report-converse.md"
MODEL_ID = "global.anthropic.claude-sonnet-4-20250514-v1:0"
SYSTEM_PROMPT = "You are an expert in AWS services and serverless architecture."
USER_PROMPT = "Describe the key components and services in the attached diagram."


def main():
    logger.info("Analyzing diagram: %s", IMAGE_FILENAME)

    ## Create an AWS SDK session
    profile = os.environ.get("AWS_PROFILE")
    region = os.environ.get("AWS_REGION")
    session = boto3.session.Session(profile_name=profile, region_name=region)

    # Create an Amazon Bedrock client
    bedrock_client = session.client(service_name="bedrock-runtime", region_name=region)

    with open(IMAGE_FILENAME, "rb") as image_file:
        image_bytes = image_file.read()

        # Claude works best when images come before text.
        # https://docs.anthropic.com/en/docs/build-with-claude/vision#prompt-examples
        message_list = [
            {
                "role": "user",
                "content": [
                    {"image": {"format": "png", "source": {"bytes": image_bytes}}},
                    {"text": USER_PROMPT},
                ],
            }
        ]

        converse_request = {
            "modelId": MODEL_ID,
            "system": [{"text": SYSTEM_PROMPT}],
            "messages": message_list,
            "inferenceConfig": {"maxTokens": 4000, "temperature": 0},
        }

        response = bedrock_client.converse(**converse_request)
        content = response["output"]["message"]["content"][0]["text"]

        with open(REPORT_FILENAME, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("architecture report saved to %s", REPORT_FILENAME)


if __name__ == "__main__":
    main()
