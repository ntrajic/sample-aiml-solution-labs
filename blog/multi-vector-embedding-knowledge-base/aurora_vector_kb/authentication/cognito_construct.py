"""
Amazon Cognito User Pool Construct

This construct creates and configures Amazon Cognito User Pool for JWT-based
authentication with email/password sign-in and secure client configuration.
"""

from typing import Any
import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    aws_cognito as cognito,
    CfnOutput,
    RemovalPolicy,
    Duration
)


class CognitoConstruct(Construct):
    """
    Construct for Amazon Cognito User Pool and App Client
    
    Creates a Cognito User Pool with:
    - Email/password authentication
    - JWT token configuration
    - App Client for secure access
    - Password policies and security settings
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Cognito User Pool with email/password authentication
        self.user_pool = cognito.UserPool(
            self,
            "VectorKbUserPool",
            user_pool_name="aurora-vector-kb-user-pool",
            
            # Sign-in configuration - email as username
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=False,
                phone=False
            ),
            
            # Auto-verified attributes
            auto_verify=cognito.AutoVerifiedAttrs(
                email=True
            ),
            
            # Password policy configuration
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
                temp_password_validity=Duration.days(7)
            ),
            
            # Account recovery settings
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            
            # User invitation settings
            user_invitation=cognito.UserInvitationConfig(
                email_subject="Welcome to Aurora Vector Knowledge Base",
                email_body="Hello {username}, your temporary password is {####}. Please sign in and change your password.",
                sms_message="Hello {username}, your temporary password is {####}"
            ),
            
            # User verification settings
            user_verification=cognito.UserVerificationConfig(
                email_subject="Verify your Aurora Vector KB account",
                email_body="Hello {username}, please verify your account by clicking this link: {##Verify Email##}",
                email_style=cognito.VerificationEmailStyle.LINK,
                sms_message="Hello {username}, your verification code is {####}"
            ),
            
            # Standard attributes configuration
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(
                    required=True,
                    mutable=True
                ),
                given_name=cognito.StandardAttribute(
                    required=False,
                    mutable=True
                ),
                family_name=cognito.StandardAttribute(
                    required=False,
                    mutable=True
                )
            ),
            
            # Deletion protection for development (set to RETAIN for production)
            removal_policy=RemovalPolicy.DESTROY,
            
            # Device tracking configuration
            device_tracking=cognito.DeviceTracking(
                challenge_required_on_new_device=True,
                device_only_remembered_on_user_prompt=True
            ),
            
            # MFA configuration (optional, can be enabled later)
            mfa=cognito.Mfa.OPTIONAL,
            mfa_second_factor=cognito.MfaSecondFactor(
                sms=True,
                otp=True
            )
        )

        # Create App Client for JWT token generation
        self.user_pool_client = cognito.UserPoolClient(
            self,
            "VectorKbAppClient",
            user_pool=self.user_pool,
            user_pool_client_name="aurora-vector-kb-app-client",
            
            # Authentication flows
            auth_flows=cognito.AuthFlow(
                user_password=True,  # Enable USER_PASSWORD_AUTH
                user_srp=True,      # Enable USER_SRP_AUTH (Secure Remote Password)
                admin_user_password=True,  # Enable ADMIN_USER_PASSWORD_AUTH
                custom=False         # Disable custom auth flows
            ),
            
            # OAuth configuration
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=False,  # Disabled for security
                    client_credentials=False    # Not needed for this use case
                ),
                scopes=[
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.PROFILE
                ],
                callback_urls=["https://localhost:3000/callback"],  # Can be updated later
                logout_urls=["https://localhost:3000/logout"]       # Can be updated later
            ),
            
            # Token validity configuration
            access_token_validity=Duration.hours(1),    # 1 hour access token
            id_token_validity=Duration.hours(1),        # 1 hour ID token  
            refresh_token_validity=Duration.days(30),   # 30 days refresh token
            
            # Security settings
            generate_secret=True,  # Generate client secret for secure access
            prevent_user_existence_errors=True,  # Prevent user enumeration attacks
            
            # Token revocation
            enable_token_revocation=True,
            
            # Supported identity providers
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO
            ],
            
            # Read and write attributes
            read_attributes=cognito.ClientAttributes().with_standard_attributes(
                email=True,
                email_verified=True,
                given_name=True,
                family_name=True
            ),
            write_attributes=cognito.ClientAttributes().with_standard_attributes(
                email=True,
                given_name=True,
                family_name=True
            )
        )

        # Create User Pool Domain for hosted UI (optional)
        self.user_pool_domain = cognito.UserPoolDomain(
            self,
            "VectorKbUserPoolDomain",
            user_pool=self.user_pool,
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=f"aurora-vector-kb-{cdk.Aws.ACCOUNT_ID}"
            )
        )

        # Add tags to all Cognito resources
        cdk.Tags.of(self.user_pool).add("Component", "Authentication")
        cdk.Tags.of(self.user_pool_client).add("Component", "Authentication")
        cdk.Tags.of(self.user_pool_domain).add("Component", "Authentication")

        # Stack outputs for integration with other components
        CfnOutput(
            self,
            "UserPoolId",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID for JWT validation",
            export_name=f"{cdk.Aws.STACK_NAME}-UserPoolId"
        )

        CfnOutput(
            self,
            "UserPoolClientId", 
            value=self.user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID for authentication",
            export_name=f"{cdk.Aws.STACK_NAME}-UserPoolClientId"
        )

        CfnOutput(
            self,
            "UserPoolArn",
            value=self.user_pool.user_pool_arn,
            description="Cognito User Pool ARN for IAM policies",
            export_name=f"{cdk.Aws.STACK_NAME}-UserPoolArn"
        )

        CfnOutput(
            self,
            "UserPoolDomain",
            value=self.user_pool_domain.domain_name,
            description="Cognito User Pool Domain for hosted UI",
            export_name=f"{cdk.Aws.STACK_NAME}-UserPoolDomain"
        )

    def get_user_pool(self) -> cognito.UserPool:
        """Returns the Cognito User Pool instance"""
        return self.user_pool

    def get_user_pool_client(self) -> cognito.UserPoolClient:
        """Returns the Cognito User Pool Client instance"""
        return self.user_pool_client

    def get_user_pool_id(self) -> str:
        """Returns the User Pool ID for JWT validation"""
        return self.user_pool.user_pool_id

    def get_user_pool_client_id(self) -> str:
        """Returns the User Pool Client ID for authentication"""
        return self.user_pool_client.user_pool_client_id

    def get_user_pool_arn(self) -> str:
        """Returns the User Pool ARN for IAM policies"""
        return self.user_pool.user_pool_arn

    def get_user_pool_domain(self) -> cognito.UserPoolDomain:
        """Returns the User Pool Domain for hosted UI"""
        return self.user_pool_domain