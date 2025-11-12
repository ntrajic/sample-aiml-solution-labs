#!/usr/bin/env python3
"""
Aurora Vector Knowledge Base CDK Application

This application deploys a complete vector knowledge base system using:
- Amazon RDS Aurora PostgreSQL with pgvector extension
- AWS Lambda functions for document processing and retrieval
- Amazon SQS for job queuing
- Amazon Cognito for authentication
- Amazon Bedrock AgentCore Gateway integration
"""

import aws_cdk as cdk
from aurora_vector_kb.aurora_vector_kb_stack import AuroraVectorKbStack


app = cdk.App()

# Get environment configuration
env = cdk.Environment(
    account=app.node.try_get_context("account") or "123456789012",
    region=app.node.try_get_context("region") or "us-east-1"
)

# Deploy the main stack
AuroraVectorKbStack(
    app, 
    "AuroraVectorKbStack",
    env=env,
    description="Aurora PostgreSQL Vector Knowledge Base with multi-embedding support"
)

app.synth()