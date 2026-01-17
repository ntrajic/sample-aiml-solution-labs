import base64
import hashlib
import hmac
import json

import boto3
from boto3.session import Session

sts_client = boto3.client("sts", region_name="us-west-2")

# Get AWS account details
REGION = boto3.session.Session().region_name or "us-west-2"

username = "testuser"
secret_name = "returns_refunds_agent"

role_name = f"ReturnsRefundsAssistantBedrockAgentCoreRole-{REGION}"
policy_name = f"ReturnsRefundsAssistantBedrockAgentCorePolicy-{REGION}"


def get_ssm_parameter(name: str, with_decryption: bool = True) -> str:
    ssm = boto3.client("ssm", region_name=REGION)

    response = ssm.get_parameter(Name=name, WithDecryption=with_decryption)

    return response["Parameter"]["Value"]


def put_ssm_parameter(
    name: str, value: str, parameter_type: str = "String", with_encryption: bool = False
) -> None:
    ssm = boto3.client("ssm", region_name=REGION)

    put_params = {
        "Name": name,
        "Value": value,
        "Type": parameter_type,
        "Overwrite": True,
    }

    if with_encryption:
        put_params["Type"] = "SecureString"

    ssm.put_parameter(**put_params)


def get_aws_account_id() -> str:
    sts = boto3.client("sts", region_name=REGION)
    return sts.get_caller_identity()["Account"]


def save_customer_support_secret(secret_value):
    """Save a secret in AWS Secrets Manager."""
    boto_session = Session()
    region = boto_session.region_name or REGION
    secrets_client = boto3.client("secretsmanager", region_name=region)

    try:
        secrets_client.create_secret(
            Name=secret_name,
            SecretString=secret_value,
            Description="Secret containing the Cognito Configuration for the Returns and Refunds Agent",
        )
        print("✅ Created secret")
    except secrets_client.exceptions.ResourceExistsException:
        secrets_client.update_secret(SecretId=secret_name, SecretString=secret_value)
        print("✅ Updated existing secret")
    except Exception as e:
        print(f"❌ Error saving secret: {str(e)}")
        return False
    return True


def get_customer_support_secret():
    """Get a secret value from AWS Secrets Manager."""
    boto_session = Session()
    region = boto_session.region_name or REGION
    secrets_client = boto3.client("secretsmanager", region_name=region)
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        return response["SecretString"]
    except Exception as e:
        print(f"❌ Error getting secret: {str(e)}")
        return None


def setup_cognito_user_pool():
    boto_session = Session()
    region = boto_session.region_name or REGION
    # Initialize Cognito client
    cognito_client = boto3.client("cognito-idp", region_name=region)
    try:
        # Create User Pool
        user_pool_response = cognito_client.create_user_pool(
            PoolName="ReturnsRefundsAgentPool", Policies={"PasswordPolicy": {"MinimumLength": 8}}
        )
        pool_id = user_pool_response["UserPool"]["Id"]
        
        # Create Resource Server for OAuth scopes
        print("Creating resource server for OAuth...")
        cognito_client.create_resource_server(
            UserPoolId=pool_id,
            Identifier="workshop-api",
            Name="Workshop API Resource Server",
            Scopes=[
                {
                    "ScopeName": "read",
                    "ScopeDescription": "Read access to workshop API"
                },
                {
                    "ScopeName": "write",
                    "ScopeDescription": "Write access to workshop API"
                }
            ]
        )
        print("✅ Resource server created")
        
        # Create User Pool Domain (required for OAuth)
        import time
        domain_name = f"returns-refunds-agent-{int(time.time())}"
        print(f"Creating user pool domain: {domain_name}")
        cognito_client.create_user_pool_domain(
            Domain=domain_name,
            UserPoolId=pool_id
        )
        print("✅ User pool domain created")
        
        # Create App Client with OAuth enabled
        app_client_response = cognito_client.create_user_pool_client(
            UserPoolId=pool_id,
            ClientName="ReturnsRefundsAgentPoolClient",
            GenerateSecret=True,
            ExplicitAuthFlows=[
                "ALLOW_USER_PASSWORD_AUTH",
                "ALLOW_REFRESH_TOKEN_AUTH",
                "ALLOW_USER_SRP_AUTH",
            ],
            AllowedOAuthFlows=["client_credentials"],
            AllowedOAuthScopes=["workshop-api/read", "workshop-api/write"],
            AllowedOAuthFlowsUserPoolClient=True,
            SupportedIdentityProviders=["COGNITO"]
        )
        print(app_client_response["UserPoolClient"])
        client_id = app_client_response["UserPoolClient"]["ClientId"]
        client_secret = app_client_response["UserPoolClient"]["ClientSecret"]
        print("✅ App client created with OAuth enabled")

        # Create User
        cognito_client.admin_create_user(
            UserPoolId=pool_id,
            Username=username,
            TemporaryPassword="Temp123!",
            MessageAction="SUPPRESS",
        )

        # Set Permanent Password
        cognito_client.admin_set_user_password(
            UserPoolId=pool_id,
            Username=username,
            Password="MyPassword123!",
            Permanent=True,
        )

        app_client_id = client_id
        key = client_secret
        message = bytes(username + app_client_id, "utf-8")
        key = bytes(key, "utf-8")
        secret_hash = base64.b64encode(
            hmac.new(key, message, digestmod=hashlib.sha256).digest()
        ).decode()

        # Authenticate User and get Access Token
        auth_response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": "testuser",
                "PASSWORD": "MyPassword123!",
                "SECRET_HASH": secret_hash,
            },
        )
        bearer_token = auth_response["AuthenticationResult"]["AccessToken"]
        # Output the required values
        print(f"Pool id: {pool_id}")
        print(
            f"Discovery URL: https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/openid-configuration"
        )
        print(f"Client ID: {client_id}")
        print(f"Bearer Token: {bearer_token}")

        # Return values if needed for further processing
        cognito_config = {
            "pool_id": pool_id,
            "client_id": client_id,
            "client_secret": client_secret,
            "secret_hash": secret_hash,
            "bearer_token": bearer_token,
            "discovery_url": f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/openid-configuration",
        }

        save_customer_support_secret(json.dumps(cognito_config))

        return cognito_config
    except Exception as e:
        print(f"Error: {e}")
        return None


def reauthenticate_user(client_id, client_secret):
    boto_session = Session()
    region = boto_session.region_name or REGION
    # Initialize Cognito client
    cognito_client = boto3.client("cognito-idp", region_name=region)
    # Authenticate User and get Access Token

    message = bytes(username + client_id, "utf-8")
    key = bytes(client_secret, "utf-8")
    secret_hash = base64.b64encode(
        hmac.new(key, message, digestmod=hashlib.sha256).digest()
    ).decode()

    auth_response = cognito_client.initiate_auth(
        ClientId=client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": username,
            "PASSWORD": "MyPassword123!",
            "SECRET_HASH": secret_hash,
        },
    )
    bearer_token = auth_response["AuthenticationResult"]["AccessToken"]
    return bearer_token


def create_agentcore_runtime_execution_role():
    iam = boto3.client("iam", region_name=REGION)
    boto_session = Session()
    region = boto_session.region_name or REGION
    account_id = get_aws_account_id()

    # Trust relationship policy
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AssumeRolePolicy",
                "Effect": "Allow",
                "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {"aws:SourceAccount": account_id},
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:bedrock-agentcore:{region}:{account_id}:*"
                    },
                },
            }
        ],
    }

    # IAM policy document
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "ECRImageAccess",
                "Effect": "Allow",
                "Action": ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"],
                "Resource": [f"arn:aws:ecr:{region}:{account_id}:repository/*"],
            },
            {
                "Effect": "Allow",
                "Action": ["logs:DescribeLogStreams", "logs:CreateLogGroup"],
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*"
                ],
            },
            {
                "Effect": "Allow",
                "Action": ["logs:DescribeLogGroups"],
                "Resource": [f"arn:aws:logs:{region}:{account_id}:log-group:*"],
            },
            {
                "Effect": "Allow",
                "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
                ],
            },
            {
                "Sid": "ECRTokenAccess",
                "Effect": "Allow",
                "Action": ["ecr:GetAuthorizationToken"],
                "Resource": "*",
            },
            {
                "Effect": "Allow",
                "Action": [
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets",
                ],
                "Resource": ["*"],
            },
            {
                "Effect": "Allow",
                "Resource": "*",
                "Action": "cloudwatch:PutMetricData",
                "Condition": {
                    "StringEquals": {"cloudwatch:namespace": "bedrock-agentcore"}
                },
            },
            {
                "Sid": "GetAgentAccessToken",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:GetWorkloadAccessToken",
                    "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                    "bedrock-agentcore:GetWorkloadAccessTokenForUserId",
                ],
                "Resource": [
                    f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/default",
                    f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/default/workload-identity/returns_refunds_agent-*",
                ],
            },
            {
                "Sid": "BedrockModelInvocation",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:ApplyGuardrail",
                    "bedrock:Retrieve",
                ],
                "Resource": [
                    "arn:aws:bedrock:*::foundation-model/*",
                    f"arn:aws:bedrock:{region}:{account_id}:*",
                ],
            },
            {
                "Sid": "AWSMarketplaceAccess",
                "Effect": "Allow",
                "Action": [
                    "aws-marketplace:ViewSubscriptions",
                    "aws-marketplace:Subscribe",
                ],
                "Resource": "*",
            },
            {
                "Sid": "AllowAgentToUseMemory",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:CreateEvent",
                    "bedrock-agentcore:ListEvents",
                    "bedrock-agentcore:GetMemoryRecord",
                    "bedrock-agentcore:GetMemory",
                    "bedrock-agentcore:RetrieveMemoryRecords",
                    "bedrock-agentcore:ListMemoryRecords",
                ],
                "Resource": [f"arn:aws:bedrock-agentcore:{region}:{account_id}:*"],
            },
            {
                "Sid": "GetMemoryId",
                "Effect": "Allow",
                "Action": ["ssm:GetParameter"],
                "Resource": [f"arn:aws:ssm:{region}:{account_id}:parameter/app/*"],
            },
        ],
    }

    try:
        # Check if role already exists
        role_exists = False
        role_arn = None
        try:
            existing_role = iam.get_role(RoleName=role_name)
            print(f"ℹ️ Role {role_name} already exists")
            print(f"Role ARN: {existing_role['Role']['Arn']}")
            role_exists = True
            role_arn = existing_role["Role"]["Arn"]
        except iam.exceptions.NoSuchEntityException:
            # Create IAM role
            role_response = iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="IAM role for Amazon Bedrock AgentCore with required permissions",
            )
            print(f"✅ Created IAM role: {role_name}")
            print(f"Role ARN: {role_response['Role']['Arn']}")
            role_arn = role_response["Role"]["Arn"]

        # Check if policy already exists
        policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"

        try:
            iam.get_policy(PolicyArn=policy_arn)
            print(f"ℹ️ Policy {policy_name} already exists")
        except iam.exceptions.NoSuchEntityException:
            # Create policy
            policy_response = iam.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
                Description="Policy for Amazon Bedrock AgentCore permissions",
            )
            print(f"✅ Created policy: {policy_name}")
            policy_arn = policy_response["Policy"]["Arn"]

        # Attach policy to role
        try:
            iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
            print("✅ Attached policy to role")
        except Exception as e:
            if "already attached" in str(e).lower():
                print("ℹ️ Policy already attached to role")
            else:
                raise

        print(f"Policy ARN: {policy_arn}")

        put_ssm_parameter(
            "/app/returnsrefunds/agentcore/runtime_execution_role_arn",
            role_arn,
        )
        return role_arn

    except Exception as e:
        print(f"❌ Error creating IAM role: {str(e)}")
        return None


def get_cognito_token_with_scope(client_id, client_secret, discovery_url, scope):
    """
    Get Cognito bearer token with a specific OAuth scope.
    
    Args:
        client_id: Cognito client ID
        client_secret: Cognito client secret
        discovery_url: Cognito discovery URL
        scope: OAuth scope (e.g., 'workshop-api/write' or 'workshop-api/read')
        
    Returns:
        Bearer token string
    """
    import requests
    import base64
    
    # Extract token endpoint from discovery URL
    discovery_response = requests.get(discovery_url)
    token_endpoint = discovery_response.json()['token_endpoint']
    
    # Get token using client credentials with scope
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    response = requests.post(
        token_endpoint,
        headers={
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "client_credentials",
            "scope": scope
        }
    )
    response.raise_for_status()
    
    return response.json()["access_token"]
