# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import os
import sys

import boto3

## Python
print("Python Version:", sys.version)

## AWS SDK for Python (boto3)
print("AWS SDK for Python (boto3) Version:", boto3.__version__)

## Create an AWS SDK session
profile = os.environ.get("AWS_PROFILE")
region = os.environ.get("AWS_REGION")
session = boto3.session.Session(profile_name=profile, region_name=region)

# aws sts get-caller-identity
sts_client = session.client(service_name="sts", region_name=region)
response = sts_client.get_caller_identity()
print(json.dumps(response, indent=2))

# aws bedrock get-foundation-model --model-identifier global.anthropic.claude-sonnet-4-20250514-v1:0
MODEL_ID = "global.anthropic.claude-sonnet-4-20250514-v1:0"
bedrock_client = session.client(service_name="bedrock", region_name=region)
response = bedrock_client.get_foundation_model(
    modelIdentifier=MODEL_ID
)
print(json.dumps(response, indent=2))
