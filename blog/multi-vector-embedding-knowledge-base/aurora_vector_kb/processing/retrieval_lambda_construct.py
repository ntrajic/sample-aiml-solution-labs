"""
Vector Retrieval Lambda Construct

This construct creates the Lambda function for vector search and retrieval operations,
including IAM roles, environment variables, and performance optimizations.
"""

from typing import List
from constructs import Construct
from aws_cdk import (
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_secretsmanager as secretsmanager,
    aws_rds as rds,
    Duration,
    CfnOutput,
    Tags
)


class RetrievalLambdaConstruct(Construct):
    """
    Construct for the vector retrieval Lambda function.
    
    Creates:
    - Lambda function for vector search and retrieval operations
    - IAM role with necessary permissions
    - Environment variables for configuration
    - Performance optimizations for vector operations
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        lambda_security_group: ec2.SecurityGroup,
        database_credentials_secret: secretsmanager.Secret,
        aurora_cluster: rds.DatabaseCluster,
        postgresql_layer,

        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = vpc
        self.lambda_security_group = lambda_security_group
        self.database_credentials_secret = database_credentials_secret
        self.aurora_cluster = aurora_cluster
        self.postgresql_layer = postgresql_layer


        # Create IAM role for the retrieval Lambda function
        self._create_lambda_role()
        
        # Create the Lambda function
        self._create_lambda_function()
        
        # Create outputs
        self._create_outputs()

    def _create_lambda_role(self) -> None:
        """Create IAM role for the retrieval Lambda function."""
        self.lambda_role = iam.Role(
            self,
            "RetrievalLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="IAM role for Aurora Vector KB Retrieval Lambda function",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                )
            ]
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

        Tags.of(self.lambda_role).add("Component", "Retrieval")

    def _create_lambda_function(self) -> None:
        """Create the retrieval Lambda function."""
        self.lambda_function = _lambda.Function(
            self,
            "RetrievalLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="retrieval_lambda.lambda_handler",
            code=_lambda.Code.from_asset("aurora_vector_kb/processing"),
            role=self.lambda_role,
            timeout=Duration.minutes(5),  # 5 minutes for complex searches
            memory_size=3008,  # Maximum memory for optimal performance
            description="Lambda function for vector search and retrieval operations",
            
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
                "BEDROCK_REGION": "us-west-2",
                "LOG_LEVEL": "INFO"
            },
            
            # Reserved concurrency for performance management
            reserved_concurrent_executions=50,
            
            # Retry configuration
            retry_attempts=0  # Let applications handle retries
        )

        Tags.of(self.lambda_function).add("Component", "Retrieval")

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs for the retrieval Lambda."""
        CfnOutput(
            self,
            "RetrievalLambdaFunctionName",
            value=self.lambda_function.function_name,
            description="Name of the Retrieval Lambda function for vector search operations"
        )
        
        CfnOutput(
            self,
            "RetrievalLambdaFunctionArn",
            value=self.lambda_function.function_arn,
            description="ARN of the Retrieval Lambda function"
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