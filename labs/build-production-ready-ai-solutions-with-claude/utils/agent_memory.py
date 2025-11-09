#!/usr/bin/python
"""AgentCore Memory integration for Strands agents."""

import logging
import os
import sys
import uuid
from typing import Dict

import boto3
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.constants import StrategyType
from boto3.session import Session
from botocore.exceptions import ClientError

boto_session = Session()
REGION = boto_session.region_name

logger = logging.getLogger(__name__)
from utils.identity_ssm_utils import get_ssm_parameter, put_ssm_parameter

ACTOR_ID = "customer_001"
SESSION_ID = str(uuid.uuid4())

memory_client = MemoryClient(region_name=REGION)
memory_name = "AmazonReturnsRefundsMemory"


def create_or_get_memory_resource():
    try:
        memory_id = get_ssm_parameter("/app/returnsrefunds/agentcore/memory_id")
        memory_client.gmcp_client.get_memory(memoryId=memory_id)
        return memory_id
    except:
        try:
            strategies = [
                {
                    StrategyType.USER_PREFERENCE.value: {
                        "name": "CustomerPreferences",
                        "description": "Captures customer preferences and behavior",
                        "namespaces": ["returns/customer/{actorId}/preferences"],
                    }
                },
                {
                    StrategyType.SEMANTIC.value: {
                        "name": "CustomerSupportSemantic",
                        "description": "Stores facts from conversations",
                        "namespaces": ["returns/customer/{actorId}/semantic"],
                    }
                },
            ]
            print("Creating AgentCore Memory resources. This can a couple of minutes..")
            # *** AGENTCORE MEMORY USAGE *** - Create memory resource with semantic and user_pref strategy
            response = memory_client.create_memory_and_wait(
                name=memory_name,
                description="Returns and refunds agent memory",
                strategies=strategies,
                event_expiry_days=90,  # Memories expire after 90 days
            )
            memory_id = response["id"]
            try:
                put_ssm_parameter("/app/returnsrefunds/agentcore/memory_id", memory_id)
            except:
                raise
            return memory_id
        except:
            return None
