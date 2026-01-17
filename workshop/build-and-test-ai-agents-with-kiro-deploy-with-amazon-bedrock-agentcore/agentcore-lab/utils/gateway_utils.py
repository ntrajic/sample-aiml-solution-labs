"""Utility functions for AWS and Cognito operations."""

import os
import json
import base64
import boto3
import requests
from typing import Optional


def get_param_value(parameter_name: str) -> str:
    """Return str parameter value from SSM Parameter Store.
    
    Args:
        parameter_name: Name of the SSM parameter
        
    Returns:
        Parameter value as string
    """
    ssm = boto3.client('ssm')
    response = ssm.get_parameter(Name=parameter_name)
    return response['Parameter']['Value']


def put_ssm_parameter(
    name: str, 
    value: str, 
    parameter_type: str = "String", 
    with_encryption: bool = False
) -> None:
    """Store a parameter in SSM Parameter Store.
    
    Args:
        name: Parameter name
        value: Parameter value
        parameter_type: Type of parameter (String, StringList, SecureString)
        with_encryption: Whether to encrypt the parameter
    """
    region = boto3.Session().region_name or 'us-west-2'
    ssm = boto3.client("ssm", region)

    put_params = {
        "Name": name,
        "Value": value,
        "Type": parameter_type,
        "Overwrite": True,
    }

    if with_encryption:
        put_params["Type"] = "SecureString"

    ssm.put_parameter(**put_params)


def get_cfn_export(export_name: str, region: str = 'us-west-2') -> str:
    """Get CloudFormation export value by name.
    
    Args:
        export_name: Name of the CloudFormation export
        region: AWS region (default: us-west-2)
    
    Returns:
        Export value as string
    
    Raises:
        ValueError: If export not found
    
    Example:
        lambda_arn = get_cfn_export('lambda-CreateRefundRequestLambdaArn')
    """
    cfn = boto3.client('cloudformation', region_name=region)
    
    # Paginate through all exports to find the matching name
    for page in cfn.get_paginator('list_exports').paginate():
        for export in page['Exports']:
            if export['Name'] == export_name:
                return export['Value']
    
    raise ValueError(f"CloudFormation export '{export_name}' not found")


def get_role_arn(role_name: str, region: str = 'us-west-2') -> str:
    """Get IAM role ARN by role name.
    
    Args:
        role_name: Name of the IAM role
        region: AWS region (default: us-west-2)
    
    Returns:
        Role ARN as string
    
    Raises:
        ValueError: If role not found
    
    Example:
        role_arn = get_role_arn('RefundManagementGatewayExecutionRole')
    """
    iam = boto3.client('iam', region_name=region)
    
    try:
        response = iam.get_role(RoleName=role_name)
        return response['Role']['Arn']
    except iam.exceptions.NoSuchEntityException:
        raise ValueError(f"IAM role '{role_name}' not found")
    except Exception as e:
        raise Exception(f"Error retrieving role ARN: {str(e)}")


def get_cognito_bearer_token(scope: str, session: Optional[boto3.Session] = None) -> str:
    """Fetch Cognito M2M credentials and return a bearer token.
    
    Retrieves client credentials from CloudFormation exports and Secrets Manager,
    then exchanges them for an OAuth2 bearer token using client credentials flow.
    
    Args:
        scope: OAuth scope to request (e.g., 'workshop-api/write')
        session: Optional boto3 session (creates default if not provided)
        
    Returns:
        Bearer token as string
        
    Example:
        token = get_cognito_bearer_token('workshop-api/write')
        headers = {'Authorization': f'Bearer {token}'}
    """
    session = session or boto3.Session()
    region_name = session.region_name or 'us-west-2'
    
    secrets_manager = session.client("secretsmanager", region_name=region_name)
    
    # Get configuration from CloudFormation exports
    token_endpoint = get_cfn_export("cognito-TokenEndpoint", region_name)
    client_id = get_cfn_export("cognito-M2MClientId", region_name)
    secret_arn = get_cfn_export("cognito-M2MClientSecretArn", region_name)
    
    # Fetch and parse the secret
    secret_value = secrets_manager.get_secret_value(SecretId=secret_arn)["SecretString"]
    secret_data = json.loads(secret_value)
    client_secret = secret_data['ClientSecret']

    # Create Basic auth header
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    # Request token using client credentials flow
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
