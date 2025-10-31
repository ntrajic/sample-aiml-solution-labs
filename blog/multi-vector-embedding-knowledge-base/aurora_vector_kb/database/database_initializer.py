"""
Database Initializer Construct

This construct creates a Lambda-backed custom resource that initializes
the Aurora PostgreSQL database with pgvector extension, creates the
vector_store table, and sets up all necessary indexes.
"""

import os
import time
from typing import Dict, Any
from constructs import Construct
from aws_cdk import (
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_secretsmanager as secretsmanager,
    aws_logs as logs,
    CustomResource,
    Duration,
    Tags,
    custom_resources as cr
)


class DatabaseInitializerConstruct(Construct):
    """
    Database initializer construct that creates a Lambda-backed custom resource
    for initializing the Aurora PostgreSQL database schema and indexes.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        lambda_subnets: list[ec2.ISubnet],
        lambda_security_group: ec2.SecurityGroup,
        aurora_cluster: rds.DatabaseCluster,
        database_credentials_secret: secretsmanager.Secret,
        postgresql_layer,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = vpc
        self.lambda_subnets = lambda_subnets
        self.lambda_security_group = lambda_security_group
        self.aurora_cluster = aurora_cluster
        self.database_credentials_secret = database_credentials_secret
        self.postgresql_layer = postgresql_layer

        # Create the Lambda function for database initialization
        self._create_initializer_lambda()
        
        # Create the custom resource
        self._create_custom_resource()

    def _create_initializer_lambda(self) -> None:
        """Create the Lambda function for database initialization."""
        
        # Create IAM role for the Lambda function
        lambda_role = iam.Role(
            self,
            "DatabaseInitializerLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="IAM role for Aurora Vector KB database initializer Lambda",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
            ]
        )

        # Grant permissions to access Secrets Manager
        self.database_credentials_secret.grant_read(lambda_role)

        # Grant permissions to connect to Aurora cluster
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "rds-db:connect"
                ],
                resources=[
                    f"arn:aws:rds-db:{self.aurora_cluster.env.region}:{self.aurora_cluster.env.account}:dbuser:{self.aurora_cluster.cluster_identifier}/*"
                ]
            )
        )

        # Create Lambda function
        self.initializer_lambda = lambda_.Function(
            self,
            "DatabaseInitializerLambda",
            function_name="aurora-vector-kb-database-initializer",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="custom_resource_lambda.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(os.path.dirname(__file__)),
                exclude=["*.pyc", "__pycache__", "*.md"]
            ),
            role=lambda_role,
            timeout=Duration.minutes(5),
            memory_size=512,
            
            # Add PostgreSQL layer
            layers=[self.postgresql_layer],
            
            # VPC configuration
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=self.lambda_subnets),
            security_groups=[self.lambda_security_group],
            
            # Environment variables
            environment={
                "LOG_LEVEL": "INFO"
            },
            
            # Logging configuration
            log_retention=logs.RetentionDays.ONE_WEEK,
            
            description="Lambda function to initialize Aurora Vector KB database schema and indexes"
        )

        # Add tags
        Tags.of(self.initializer_lambda).add("Name", "aurora-vector-kb-db-initializer")
        Tags.of(self.initializer_lambda).add("Component", "Database")
        Tags.of(self.initializer_lambda).add("Function", "Initialization")

    def _create_custom_resource(self) -> None:
        """Create the custom resource that triggers database initialization."""
        
        # Create custom resource provider
        provider = cr.Provider(
            self,
            "DatabaseInitializerProvider",
            on_event_handler=self.initializer_lambda,
            log_retention=logs.RetentionDays.ONE_WEEK
        )

        # Create custom resource properties
        properties = {
            "DatabaseHost": self.aurora_cluster.cluster_endpoint.hostname,
            "DatabasePort": str(self.aurora_cluster.cluster_endpoint.port),
            "DatabaseName": "vector_kb",
            "CredentialsSecretArn": self.database_credentials_secret.secret_arn,
            # Add a timestamp to force updates when needed
            "Timestamp": str(int(time.time()))
        }

        # Create the custom resource
        self.custom_resource = CustomResource(
            self,
            "DatabaseInitializerCustomResource",
            service_token=provider.service_token,
            properties=properties
        )

        # Ensure the custom resource depends on the Aurora cluster
        self.custom_resource.node.add_dependency(self.aurora_cluster)

        # Add tags
        Tags.of(self.custom_resource).add("Name", "aurora-vector-kb-db-init")
        Tags.of(self.custom_resource).add("Component", "Database")

    def get_custom_resource(self) -> CustomResource:
        """Return the custom resource instance."""
        return self.custom_resource

    def get_initializer_lambda(self) -> lambda_.Function:
        """Return the initializer Lambda function."""
        return self.initializer_lambda