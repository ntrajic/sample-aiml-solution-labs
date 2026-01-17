"""Agent memory configuration constants"""

import boto3
import uuid

# Get AWS region
REGION = boto3.session.Session().region_name or "us-west-2"

# Default session and actor IDs for local testing
SESSION_ID = str(uuid.uuid4())
ACTOR_ID = "customer_001"
