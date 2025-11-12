"""
Ingestion Lambda Construct

This construct creates the Lambda function for document ingestion processing,
including IAM roles, environment variables, and SQS event source mapping.
"""

from typing import List
from constructs import Construct
from aws_cdk import (
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_sqs as sqs,
    aws_secretsmanager as secretsmanager,
    aws_rds as rds,
    aws_lambda_event_sources as lambda_event_sources,
    Duration,
    CfnOutput,
    Tags
)


class IngestionLambdaConstruct(Construct):
    """
    Construct for the document ingestion Lambda function.
    
    Creates:
    - Lambda function for document processing and vector storage
    - IAM role with necessary permissions
    - SQS event source mapping
    - Environment variables for configuration
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        lambda_security_group: ec2.SecurityGroup,
        ingestion_queue: sqs.Queue,
        database_credentials_secret: secretsmanager.Secret,
        aurora_cluster: rds.DatabaseCluster,
        postgresql_layer,

        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = vpc
        self.lambda_security_group = lambda_security_group
        self.ingestion_queue = ingestion_queue
        self.database_credentials_secret = database_credentials_secret
        self.aurora_cluster = aurora_cluster
        self.postgresql_layer = postgresql_layer


        # Create IAM role for the ingestion Lambda function
        self._create_lambda_role()
        
        # Create the Lambda function
        self._create_lambda_function()
        
        # Configure SQS event source mapping
        self._configure_event_source()
        
        # Create outputs
        self._create_outputs()

    def _create_lambda_role(self) -> None:
        """Create IAM role for the ingestion Lambda function."""
        self.lambda_role = iam.Role(
            self,
            "IngestionLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="IAM role for Aurora Vector KB Ingestion Lambda function",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                )
            ]
        )

        # Add permissions for S3 access (read documents and list bucket)
        self.lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:GetObjectVersion"
                ],
                resources=[
                    "arn:aws:s3:::*/*"  # Allow access to any S3 object
                ]
            )
        )
        
        # Add permissions for S3 bucket listing
        self.lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:ListBucket"
                ],
                resources=[
                    "arn:aws:s3:::*"  # Allow listing any S3 bucket
                ]
            )
        )

        # Add permissions for SQS queue access
        self.lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes"
                ],
                resources=[self.ingestion_queue.queue_arn]
            )
        )

        # Add permissions for Bedrock access (Titan embeddings)
        self.lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel"
                ],
                resources=[
                    "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0"
                ]
            )
        )

        # Add permissions for Secrets Manager access
        self.lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret"
                ],
                resources=[
                    self.database_credentials_secret.secret_arn
                ]
            )
        )

        # Add permissions for CloudWatch Logs
        self.lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=["arn:aws:logs:*:*:*"]
            )
        )

        Tags.of(self.lambda_role).add("Component", "Processing")

    def _create_lambda_function(self) -> None:
        """Create the ingestion Lambda function."""
        self.lambda_function = _lambda.Function(
            self,
            "IngestionLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="ingestion_lambda.lambda_handler",
            code=_lambda.Code.from_asset("aurora_vector_kb/processing"),
            role=self.lambda_role,
            timeout=Duration.minutes(15),  # Maximum Lambda timeout
            memory_size=3008,  # Maximum memory for better performance
            description="Lambda function for document ingestion, processing, and vector storage",
            
            # Add PostgreSQL layer
            layers=[self.postgresql_layer],
            
            # VPC configuration
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            security_groups=[self.lambda_security_group],
            
            # Environment variables
            environment={
                "DB_SECRET_NAME": self.database_credentials_secret.secret_name,
                "DB_HOST": self.aurora_cluster.cluster_endpoint.hostname,
                "DB_PORT": str(self.aurora_cluster.cluster_endpoint.port),
                "DB_NAME": "vector_kb",
                "LOG_LEVEL": "INFO"
            },
            
            # Reserved concurrency to control costs and database connections
            reserved_concurrent_executions=10,
            
            # Retry configuration
            retry_attempts=0  # SQS will handle retries
        )

        Tags.of(self.lambda_function).add("Component", "Processing")

    def _configure_event_source(self) -> None:
        """Configure SQS event source mapping for the Lambda function."""
        self.event_source_mapping = self.lambda_function.add_event_source(
            lambda_event_sources.SqsEventSource(
                queue=self.ingestion_queue,
                batch_size=1,  # Process one document at a time for better error handling
                max_batching_window=Duration.seconds(5),  # Small batching window
                report_batch_item_failures=True,  # Enable partial batch failure reporting
                max_concurrency=5  # Limit concurrent executions to manage database load
            )
        )

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs for the ingestion Lambda."""
        CfnOutput(
            self,
            "IngestionLambdaFunctionName",
            value=self.lambda_function.function_name,
            description="Name of the Ingestion Lambda function for document processing"
        )
        
        CfnOutput(
            self,
            "IngestionLambdaFunctionArn",
            value=self.lambda_function.function_arn,
            description="ARN of the Ingestion Lambda function"
        )

    def get_lambda_function(self) -> _lambda.Function:
        """Return the Lambda function instance."""
        return self.lambda_function

    def get_lambda_role(self) -> iam.Role:
        """Return the Lambda IAM role."""
        return self.lambda_role

    def get_function_arn(self) -> str:
        """Return the Lambda function ARN."""
        return self.lambda_function.function_arn

    def get_function_name(self) -> str:
        """Return the Lambda function name."""
        return self.lambda_function.function_name