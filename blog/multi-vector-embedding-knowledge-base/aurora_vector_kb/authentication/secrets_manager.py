"""
AWS Secrets Manager Construct

This construct creates and manages AWS Secrets Manager secrets for storing
Cognito client secrets and other sensitive authentication configuration.
"""

from typing import Any, Dict
import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    aws_secretsmanager as secretsmanager,
    aws_cognito as cognito,
    aws_iam as iam,
    CfnOutput,
    RemovalPolicy
)


class SecretsManagerConstruct(Construct):
    """
    Construct for AWS Secrets Manager integration
    
    Creates and manages secrets for:
    - Cognito User Pool Client secrets
    - JWT validation configuration
    - Other authentication-related sensitive data
    """

    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        user_pool: cognito.UserPool,
        user_pool_client: cognito.UserPoolClient,
        **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.user_pool = user_pool
        self.user_pool_client = user_pool_client

        # Create secret for Cognito configuration
        self.cognito_secret = secretsmanager.Secret(
            self,
            "CognitoClientSecret",
            secret_name="aurora-vector-kb/cognito-config",
            description="Cognito User Pool and Client configuration for Aurora Vector Knowledge Base",
            
            # Generate secret value with Cognito configuration
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"userPoolId": "' + user_pool.user_pool_id + '", "region": "' + cdk.Aws.REGION + '"}',
                generate_string_key="clientSecret",
                exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/\"\\",
                include_space=False,
                password_length=32
            ),
            
            # Automatic rotation configuration (can be enabled later)
            # automatic_rotation=secretsmanager.RotationSchedule(...),
            
            # Deletion protection for development (set to RETAIN for production)
            removal_policy=RemovalPolicy.DESTROY,
            
            # Replica configuration removed - not needed for single region deployment
        )

        # Create a more comprehensive secret with all Cognito configuration
        self.cognito_config_secret = secretsmanager.Secret(
            self,
            "CognitoFullConfig",
            secret_name="aurora-vector-kb/cognito-full-config",
            description="Complete Cognito configuration including client secret and JWT settings",
            
            # Store complete configuration as JSON
            secret_object_value={
                "user_pool_id": cdk.SecretValue.unsafe_plain_text(user_pool.user_pool_id),
                "client_id": cdk.SecretValue.unsafe_plain_text(user_pool_client.user_pool_client_id),
                "region": cdk.SecretValue.unsafe_plain_text(cdk.Aws.REGION),
                "user_pool_arn": cdk.SecretValue.unsafe_plain_text(user_pool.user_pool_arn),
                "issuer": cdk.SecretValue.unsafe_plain_text(f"https://cognito-idp.{cdk.Aws.REGION}.amazonaws.com/{user_pool.user_pool_id}"),
                "jwks_uri": cdk.SecretValue.unsafe_plain_text(f"https://cognito-idp.{cdk.Aws.REGION}.amazonaws.com/{user_pool.user_pool_id}/.well-known/jwks.json"),
                "token_use": cdk.SecretValue.unsafe_plain_text("access"),
                "client_secret": user_pool_client.user_pool_client_secret
            },
            
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create IAM policy for Lambda functions to access secrets
        self.secrets_access_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret"
                    ],
                    resources=[
                        self.cognito_secret.secret_arn,
                        self.cognito_config_secret.secret_arn
                    ]
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "kms:Decrypt"
                    ],
                    resources=["*"],
                    conditions={
                        "StringEquals": {
                            "kms:ViaService": f"secretsmanager.{cdk.Aws.REGION}.amazonaws.com"
                        }
                    }
                )
            ]
        )

        # Create managed policy for easy attachment to Lambda roles
        self.secrets_managed_policy = iam.ManagedPolicy(
            self,
            "SecretsAccessPolicy",
            managed_policy_name="AuroraVectorKB-SecretsAccess",
            description="Policy for Lambda functions to access Cognito secrets",
            document=self.secrets_access_policy
        )

        # Add tags to secrets
        cdk.Tags.of(self.cognito_secret).add("Component", "Authentication")
        cdk.Tags.of(self.cognito_config_secret).add("Component", "Authentication")
        cdk.Tags.of(self.secrets_managed_policy).add("Component", "Authentication")

        # Stack outputs
        CfnOutput(
            self,
            "CognitoSecretArn",
            value=self.cognito_secret.secret_arn,
            description="ARN of the Cognito client secret in Secrets Manager",
            export_name=f"{cdk.Aws.STACK_NAME}-CognitoSecretArn"
        )

        CfnOutput(
            self,
            "CognitoConfigSecretArn",
            value=self.cognito_config_secret.secret_arn,
            description="ARN of the complete Cognito configuration secret",
            export_name=f"{cdk.Aws.STACK_NAME}-CognitoConfigSecretArn"
        )

        CfnOutput(
            self,
            "SecretsAccessPolicyArn",
            value=self.secrets_managed_policy.managed_policy_arn,
            description="ARN of the IAM policy for accessing Cognito secrets",
            export_name=f"{cdk.Aws.STACK_NAME}-SecretsAccessPolicyArn"
        )

    def get_cognito_secret(self) -> secretsmanager.Secret:
        """Returns the Cognito client secret"""
        return self.cognito_secret

    def get_cognito_config_secret(self) -> secretsmanager.Secret:
        """Returns the complete Cognito configuration secret"""
        return self.cognito_config_secret

    def get_secrets_access_policy(self) -> iam.ManagedPolicy:
        """Returns the IAM managed policy for accessing secrets"""
        return self.secrets_managed_policy

    def get_secrets_policy_document(self) -> iam.PolicyDocument:
        """Returns the IAM policy document for accessing secrets"""
        return self.secrets_access_policy

    def grant_read_access(self, grantee: iam.IGrantable) -> iam.Grant:
        """
        Grant read access to the Cognito secrets for the specified grantee
        
        Args:
            grantee: The IAM principal (role, user, etc.) to grant access to
            
        Returns:
            Grant object representing the permission
        """
        # Grant access to both secrets
        cognito_grant = self.cognito_secret.grant_read(grantee)
        config_grant = self.cognito_config_secret.grant_read(grantee)
        
        return cognito_grant