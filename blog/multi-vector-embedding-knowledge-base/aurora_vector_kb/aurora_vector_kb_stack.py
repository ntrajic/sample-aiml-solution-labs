"""
Aurora Vector Knowledge Base Stack

This stack defines the complete infrastructure for a vector knowledge base system
including Aurora PostgreSQL with pgvector, Lambda functions, SQS queues, 
Cognito authentication, and AgentCore Gateway integration.
"""

from typing import Any
import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    Duration
)

# Import networking constructs
from .networking.vpc_construct import VpcConstruct
from .networking.security_groups import SecurityGroupsConstruct

# Import database constructs
from .database.aurora_cluster import AuroraClusterConstruct

# Import layer constructs
from .layers.psycopg2_layer import DependenciesLayerConstruct

# Import storage constructs
from .storage.s3_construct import S3KnowledgeBaseConstruct

# Import authentication constructs
from .authentication.cognito_construct import CognitoConstruct
from .authentication.secrets_manager import SecretsManagerConstruct

# Import messaging constructs
from .messaging.sqs_construct import SqsConstruct

# Import processing constructs
from .processing.sync_lambda_construct import SyncLambdaConstruct
from .processing.ingestion_lambda_construct import IngestionLambdaConstruct


class AuroraVectorKbStack(Stack):
    """
    Main CDK Stack for Aurora Vector Knowledge Base
    
    This stack orchestrates all the components needed for the vector knowledge base:
    - VPC and networking infrastructure
    - Aurora PostgreSQL cluster with pgvector
    - Lambda functions for sync, ingestion, and retrieval
    - SQS queue for job processing
    - Cognito for authentication
    - IAM roles and policies
    - AgentCore Gateway integration
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Add stack-level tags
        cdk.Tags.of(self).add("Project", "AuroraVectorKnowledgeBase")
        cdk.Tags.of(self).add("Environment", self.node.try_get_context("environment") or "dev")
        
        # Create VPC and networking infrastructure
        self.vpc_construct = VpcConstruct(self, "VpcConstruct")
        self.vpc = self.vpc_construct.get_vpc()
        
        # Create security groups for all components
        self.security_groups = SecurityGroupsConstruct(
            self, 
            "SecurityGroups", 
            vpc=self.vpc
        )
        
        # Store references to networking components for use in other constructs
        self.lambda_security_group = self.security_groups.get_lambda_security_group()
        self.aurora_security_group = self.security_groups.get_aurora_security_group()
        self.vpc_endpoint_security_group = self.security_groups.get_vpc_endpoint_security_group()
        
        # Store subnet references for easy access by other constructs
        self.private_subnets = self.vpc_construct.get_private_subnets()
        self.database_subnets = self.vpc_construct.get_database_subnets()
        self.public_subnets = self.vpc_construct.get_public_subnets()
        
        # Create dependencies Lambda layer
        self.dependencies_layer_construct = DependenciesLayerConstruct(
            self,
            "DependenciesLayer"
        )
        self.dependencies_layer = self.dependencies_layer_construct.get_layer()
        
        # Create S3 bucket for knowledge base documents
        self.s3_construct = S3KnowledgeBaseConstruct(
            self,
            "S3Storage"
        )
        self.knowledge_base_bucket = self.s3_construct.get_bucket()
        self.knowledge_base_bucket_name = self.s3_construct.get_bucket_name()
        
        # Create Aurora PostgreSQL Serverless v2 cluster with pgvector extension
        # Serverless v2 automatically optimizes costs (0.5-16 ACU scaling)
        self.aurora_cluster = AuroraClusterConstruct(
            self,
            "AuroraCluster",
            vpc=self.vpc,
            database_subnets=self.database_subnets,
            private_subnets=self.private_subnets,
            security_group=self.aurora_security_group,
            lambda_security_group=self.lambda_security_group,
            postgresql_layer=self.dependencies_layer
        )
        
        # Store cluster references for use by Lambda functions
        self.cluster = self.aurora_cluster.get_cluster()
        self.database_credentials = self.aurora_cluster.get_credentials_secret()
        self.cluster_endpoint = self.aurora_cluster.get_cluster_endpoint()
        self.cluster_read_endpoint = self.aurora_cluster.get_cluster_read_endpoint()
        
        # Create Cognito User Pool for JWT authentication
        self.cognito_construct = CognitoConstruct(
            self,
            "CognitoAuth"
        )
        
        # Store Cognito references for use by Lambda functions
        self.user_pool = self.cognito_construct.get_user_pool()
        self.user_pool_client = self.cognito_construct.get_user_pool_client()
        self.user_pool_id = self.cognito_construct.get_user_pool_id()
        self.user_pool_client_id = self.cognito_construct.get_user_pool_client_id()
        
        # Create Secrets Manager for storing Cognito client secrets
        self.secrets_manager = SecretsManagerConstruct(
            self,
            "SecretsManager",
            user_pool=self.user_pool,
            user_pool_client=self.user_pool_client
        )
        
        # Store secrets references for use by Lambda functions
        self.cognito_secret = self.secrets_manager.get_cognito_secret()
        self.cognito_config_secret = self.secrets_manager.get_cognito_config_secret()
        self.secrets_access_policy = self.secrets_manager.get_secrets_access_policy()
        
        # Create SQS queue infrastructure for document ingestion
        self.sqs_construct = SqsConstruct(
            self,
            "SqsQueues"
        )
        
        # Store SQS references for use by Lambda functions
        self.ingestion_queue = self.sqs_construct.get_ingestion_queue()
        self.dead_letter_queue = self.sqs_construct.get_dead_letter_queue()
        self.alarm_topic = self.sqs_construct.get_alarm_topic()
        self.ingestion_queue_url = self.sqs_construct.get_queue_url()
        self.ingestion_queue_arn = self.sqs_construct.get_queue_arn()
        
        # Create Sync Lambda function for S3 directory listing
        self.sync_lambda_construct = SyncLambdaConstruct(
            self,
            "SyncLambda",
            vpc=self.vpc,
            lambda_security_group=self.lambda_security_group,
            ingestion_queue=self.ingestion_queue,
            cognito_config_secret=self.cognito_config_secret,
            knowledge_base_bucket=self.knowledge_base_bucket
        )
        
        # Store sync Lambda references
        self.sync_lambda_function = self.sync_lambda_construct.get_lambda_function()
        self.sync_lambda_role = self.sync_lambda_construct.get_lambda_role()
        self.sync_lambda_arn = self.sync_lambda_construct.get_function_arn()
        self.sync_lambda_name = self.sync_lambda_construct.get_function_name()
        
        # Create Ingestion Lambda function for document processing
        self.ingestion_lambda_construct = IngestionLambdaConstruct(
            self,
            "IngestionLambda",
            vpc=self.vpc,
            lambda_security_group=self.lambda_security_group,
            ingestion_queue=self.ingestion_queue,
            cognito_config_secret=self.cognito_config_secret,
            database_credentials_secret=self.database_credentials,
            postgresql_layer=self.dependencies_layer
        )
        
        # Store ingestion Lambda references
        self.ingestion_lambda_function = self.ingestion_lambda_construct.get_lambda_function()
        self.ingestion_lambda_role = self.ingestion_lambda_construct.get_lambda_role()
        self.ingestion_lambda_arn = self.ingestion_lambda_construct.get_function_arn()
        self.ingestion_lambda_name = self.ingestion_lambda_construct.get_function_name()
        
        # Stack-level outputs
        CfnOutput(
            self,
            "StackName",
            value=self.stack_name,
            description="Name of the deployed stack"
        )
        
        CfnOutput(
            self,
            "Region",
            value=self.region,
            description="AWS region where the stack is deployed"
        )
        
        # Authentication-related outputs
        CfnOutput(
            self,
            "CognitoUserPoolId",
            value=self.user_pool_id,
            description="Cognito User Pool ID for authentication"
        )
        
        CfnOutput(
            self,
            "CognitoUserPoolClientId", 
            value=self.user_pool_client_id,
            description="Cognito User Pool Client ID for JWT tokens"
        )
        
        CfnOutput(
            self,
            "CognitoConfigSecretName",
            value=self.cognito_config_secret.secret_name,
            description="Secrets Manager secret name containing Cognito configuration"
        )
        
        # Processing-related outputs
        CfnOutput(
            self,
            "SyncLambdaFunctionName",
            value=self.sync_lambda_name,
            description="Name of the Sync Lambda function for S3 directory listing"
        )
        
        CfnOutput(
            self,
            "SyncLambdaFunctionArn",
            value=self.sync_lambda_arn,
            description="ARN of the Sync Lambda function"
        )
        
        CfnOutput(
            self,
            "IngestionLambdaFunctionName",
            value=self.ingestion_lambda_name,
            description="Name of the Ingestion Lambda function for document processing"
        )
        
        CfnOutput(
            self,
            "IngestionLambdaFunctionArn",
            value=self.ingestion_lambda_arn,
            description="ARN of the Ingestion Lambda function"
        )
        
        CfnOutput(
            self,
            "KnowledgeBaseBucketName",
            value=self.knowledge_base_bucket_name,
            description="Name of the S3 bucket for knowledge base documents"
        )
        
        CfnOutput(
            self,
            "KnowledgeBaseBucketArn",
            value=self.knowledge_base_bucket.bucket_arn,
            description="ARN of the S3 bucket for knowledge base documents"
        )
        
        CfnOutput(
            self,
            "AuroraServerlessStatus",
            value="Aurora Serverless v2 (0.5-16 ACU auto-scaling, pay-per-use)",
            description="Aurora Serverless v2 configuration and cost model"
        )
        
