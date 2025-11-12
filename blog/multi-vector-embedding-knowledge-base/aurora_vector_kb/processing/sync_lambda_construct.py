"""
Sync Lambda Construct

This construct defines the AWS Lambda function for S3 directory synchronization
including IAM roles, environment variables, and integration with other services.
"""

import os
from typing import Any
from constructs import Construct
from aws_cdk import (
    Duration,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_sqs as sqs,
    aws_secretsmanager as secretsmanager,
    aws_logs as logs
)


class SyncLambdaConstruct(Construct):
    """
    Construct for the Sync Lambda function that handles S3 directory listing
    and queues files for ingestion processing.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        lambda_security_group: ec2.SecurityGroup,
        ingestion_queue: sqs.Queue,
        cognito_config_secret: secretsmanager.Secret,
        knowledge_base_bucket,
        **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Store references
        self._vpc = vpc
        self._lambda_security_group = lambda_security_group
        self._ingestion_queue = ingestion_queue
        self._cognito_config_secret = cognito_config_secret
        self._knowledge_base_bucket = knowledge_base_bucket

        # Create IAM role for the Lambda function
        self._create_lambda_role()

        # Create the Lambda function
        self._create_lambda_function()

        # Configure Lambda permissions
        self._configure_permissions()

    def _create_lambda_role(self) -> None:
        """Create IAM role for the Sync Lambda function."""
        self._lambda_role = iam.Role(
            self,
            "SyncLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="IAM role for Aurora Vector KB Sync Lambda function",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                )
            ]
        )

        # Add S3 read permissions
        s3_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:ListBucket",
                "s3:ListBucketVersions"
            ],
            resources=[
                "arn:aws:s3:::*",
                "arn:aws:s3:::*/*"
            ]
        )

        # Add SQS send message permissions
        sqs_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "sqs:SendMessage",
                "sqs:SendMessageBatch",
                "sqs:GetQueueAttributes"
            ],
            resources=[self._ingestion_queue.queue_arn]
        )

        # Add Secrets Manager read permissions
        secrets_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "secretsmanager:GetSecretValue"
            ],
            resources=[self._cognito_config_secret.secret_arn]
        )

        # Add CloudWatch Logs permissions
        logs_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            resources=["arn:aws:logs:*:*:*"]
        )

        # Attach policies to role
        self._lambda_role.add_to_policy(s3_policy)
        self._lambda_role.add_to_policy(sqs_policy)
        self._lambda_role.add_to_policy(secrets_policy)
        self._lambda_role.add_to_policy(logs_policy)

    def _create_lambda_function(self) -> None:
        """Create the Sync Lambda function."""
        # Get the directory containing this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        self._lambda_function = _lambda.Function(
            self,
            "SyncLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="sync_lambda.lambda_handler",
            code=_lambda.Code.from_asset(current_dir),
            role=self._lambda_role,
            timeout=Duration.minutes(15),
            memory_size=1024,
            environment={
                "COGNITO_CONFIG_SECRET_NAME": self._cognito_config_secret.secret_name,
                "SQS_QUEUE_URL": self._ingestion_queue.queue_url,
                "DEFAULT_S3_BUCKET": self._knowledge_base_bucket.bucket_name,
                "LOG_LEVEL": "INFO"
            },
            vpc=self._vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            security_groups=[self._lambda_security_group],
            description="Lambda function for S3 directory synchronization and file queuing",
            retry_attempts=0  # Disable automatic retries for this function
        )

    def _configure_permissions(self) -> None:
        """Configure additional permissions and integrations."""
        # Grant the Lambda function permission to read from Secrets Manager
        self._cognito_config_secret.grant_read(self._lambda_function)

        # Grant the Lambda function permission to send messages to SQS
        self._ingestion_queue.grant_send_messages(self._lambda_function)

    def get_lambda_function(self) -> _lambda.Function:
        """
        Get the Sync Lambda function.
        
        Returns:
            The Lambda function construct
        """
        return self._lambda_function

    def get_lambda_role(self) -> iam.Role:
        """
        Get the IAM role for the Sync Lambda function.
        
        Returns:
            The IAM role construct
        """
        return self._lambda_role

    def get_function_arn(self) -> str:
        """
        Get the ARN of the Sync Lambda function.
        
        Returns:
            The Lambda function ARN
        """
        return self._lambda_function.function_arn

    def get_function_name(self) -> str:
        """
        Get the name of the Sync Lambda function.
        
        Returns:
            The Lambda function name
        """
        return self._lambda_function.function_name