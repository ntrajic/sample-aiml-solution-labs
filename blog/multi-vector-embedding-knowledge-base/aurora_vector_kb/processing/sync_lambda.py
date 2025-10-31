"""
Sync Lambda Function for S3 Directory Listing

This Lambda function handles S3 directory synchronization by listing files
in specified S3 locations and queuing them for ingestion processing.
It includes JWT token validation and SQS message publishing functionality.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import base64
import hmac
import hashlib
from urllib.parse import urlparse
from urllib.request import urlopen

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')
secrets_client = boto3.client('secretsmanager')

# Environment variables
COGNITO_CONFIG_SECRET_NAME = os.environ.get('COGNITO_CONFIG_SECRET_NAME')
SQS_QUEUE_URL = os.environ.get('SQS_QUEUE_URL')
DEFAULT_S3_BUCKET = os.environ.get('DEFAULT_S3_BUCKET')

# Cache for Cognito configuration
_cognito_config_cache = None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for S3 directory synchronization.
    
    Args:
        event: Lambda event containing S3 bucket, prefix, and JWT token
        context: Lambda context object
        
    Returns:
        Response dictionary with sync results
    """
    logger.info(f"Received sync request: {json.dumps(event, default=str)}")
    
    try:
        # Extract and validate input parameters
        s3_bucket = event.get('s3_bucket') or DEFAULT_S3_BUCKET
        s3_prefix = event.get('s3_prefix', '')
        jwt_token = event.get('jwt_token')
        
        # Validate required parameters
        if not s3_bucket:
            raise ValueError("s3_bucket parameter is required (either in event or as DEFAULT_S3_BUCKET environment variable)")
        
        # JWT token validation (optional for direct testing)
        user_claims = {}
        if jwt_token:
            # Validate JWT token if provided
            user_claims = validate_jwt_token(jwt_token)
            logger.info(f"JWT validation successful for user: {user_claims.get('sub', 'unknown')}")
        else:
            # Allow direct invocation without JWT for testing
            logger.info("No JWT token provided - assuming direct invocation for testing")
            user_claims = {'sub': 'test-user', 'source': 'direct-invocation'}
        
        # List files in S3 location
        s3_files = list_s3_files(s3_bucket, s3_prefix)
        logger.info(f"Found {len(s3_files)} files in s3://{s3_bucket}/{s3_prefix}")
        
        # Queue files for ingestion
        queued_count = queue_files_for_ingestion(s3_files, jwt_token)
        
        # Return success response
        response = {
            'status': 'success',
            'files_queued': queued_count,
            'message': f'Successfully queued {queued_count} files for ingestion',
            's3_location': f's3://{s3_bucket}/{s3_prefix}',
            'user_id': user_claims.get('sub')
        }
        
        logger.info(f"Sync completed successfully: {response}")
        return response
        
    except ValueError as e:
        error_msg = str(e)
        if "token" in error_msg.lower() or "jwt" in error_msg.lower():
            logger.error(f"JWT validation failed: {error_msg}")
            return {
                'status': 'error',
                'files_queued': 0,
                'message': 'Invalid or expired JWT token'
            }
        else:
            logger.error(f"Validation error: {error_msg}")
            return {
                'status': 'error',
                'files_queued': 0,
                'message': f'Validation error: {error_msg}'
            }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"AWS service error ({error_code}): {str(e)}")
        return {
            'status': 'error',
            'files_queued': 0,
            'message': f'AWS service error: {error_code}'
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'files_queued': 0,
            'message': f'Internal server error: {str(e)}'
        }


def validate_jwt_token(token: str) -> Dict[str, Any]:
    """
    Validate JWT token against Cognito User Pool.
    
    Args:
        token: JWT token to validate
        
    Returns:
        Dictionary containing user claims if valid
        
    Raises:
        ValueError: If token is invalid or expired
    """
    try:
        # Get Cognito configuration
        cognito_config = get_cognito_config()
        
        # For now, we'll do basic token structure validation
        # In a production environment, you would want to verify the signature
        # using the Cognito public keys
        
        # Split the token into parts
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT token format")
        
        # Decode the payload (second part)
        payload_encoded = parts[1]
        # Add padding if needed
        payload_encoded += '=' * (4 - len(payload_encoded) % 4)
        
        try:
            payload_bytes = base64.urlsafe_b64decode(payload_encoded)
            payload = json.loads(payload_bytes.decode('utf-8'))
        except Exception as e:
            raise ValueError(f"Failed to decode JWT payload: {str(e)}")
        
        # Basic validation checks
        import time
        current_time = int(time.time())
        
        # Check expiration
        if 'exp' in payload and payload['exp'] < current_time:
            raise ValueError("Token has expired")
        
        # Check not before
        if 'nbf' in payload and payload['nbf'] > current_time:
            raise ValueError("Token not yet valid")
        
        # Check issuer
        expected_issuer = f"https://cognito-idp.{cognito_config['region']}.amazonaws.com/{cognito_config['user_pool_id']}"
        if 'iss' in payload and payload['iss'] != expected_issuer:
            raise ValueError("Invalid token issuer")
        
        # Check audience (client ID)
        if 'aud' in payload and payload['aud'] != cognito_config['client_id']:
            raise ValueError("Invalid token audience")
        
        logger.info("JWT token validated successfully")
        return payload
        
    except ValueError as e:
        logger.error(f"JWT token validation failed: {str(e)}")
        raise
        
    except Exception as e:
        logger.error(f"Error validating JWT token: {str(e)}")
        raise ValueError(f"Token validation error: {str(e)}")


def get_cognito_config() -> Dict[str, str]:
    """
    Get Cognito configuration from Secrets Manager with caching.
    
    Returns:
        Dictionary containing Cognito configuration
    """
    global _cognito_config_cache
    
    if _cognito_config_cache is not None:
        return _cognito_config_cache
    
    try:
        logger.info(f"Retrieving Cognito configuration from secret: {COGNITO_CONFIG_SECRET_NAME}")
        
        response = secrets_client.get_secret_value(SecretId=COGNITO_CONFIG_SECRET_NAME)
        config_data = json.loads(response['SecretString'])
        
        required_fields = ['user_pool_id', 'client_id', 'region']
        for field in required_fields:
            if field not in config_data:
                raise ValueError(f"Missing required field in Cognito config: {field}")
        
        _cognito_config_cache = config_data
        logger.info("Cognito configuration retrieved successfully")
        return _cognito_config_cache
        
    except ClientError as e:
        logger.error(f"Error retrieving Cognito configuration: {str(e)}")
        raise
    except (KeyError, json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing Cognito configuration: {str(e)}")
        raise


def get_cognito_jwks(region: str, user_pool_id: str) -> Dict[str, Any]:
    """
    Get Cognito JSON Web Key Set (JWKS) for token verification.
    
    Args:
        region: AWS region
        user_pool_id: Cognito User Pool ID
        
    Returns:
        JWKS dictionary
    """
    jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
    
    try:
        logger.info(f"Fetching JWKS from: {jwks_url}")
        
        with urlopen(jwks_url) as response:
            if response.status != 200:
                raise ValueError(f"HTTP {response.status}: Failed to fetch JWKS")
            
            jwks_data = response.read().decode('utf-8')
            jwks = json.loads(jwks_data)
        
        logger.info("JWKS retrieved successfully")
        return jwks
        
    except Exception as e:
        logger.error(f"Error fetching JWKS: {str(e)}")
        raise ValueError(f"Failed to fetch JWKS: {str(e)}")


def list_s3_files(bucket: str, prefix: str) -> List[str]:
    """
    List all files in the specified S3 location with pagination support.
    
    Args:
        bucket: S3 bucket name
        prefix: S3 prefix (folder path)
        
    Returns:
        List of S3 URIs for all files found
    """
    s3_files = []
    continuation_token = None
    
    try:
        logger.info(f"Listing files in s3://{bucket}/{prefix}")
        
        while True:
            # Prepare list_objects_v2 parameters
            list_params = {
                'Bucket': bucket,
                'Prefix': prefix,
                'MaxKeys': 1000  # Maximum allowed by AWS
            }
            
            if continuation_token:
                list_params['ContinuationToken'] = continuation_token
            
            # List objects in S3
            response = s3_client.list_objects_v2(**list_params)
            
            # Process objects in current page
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Skip directories (objects ending with '/')
                    if not obj['Key'].endswith('/'):
                        # Skip metadata files - only queue actual documents
                        if not obj['Key'].endswith('.metadata.json'):
                            s3_uri = f"s3://{bucket}/{obj['Key']}"
                            s3_files.append(s3_uri)
                            
                            # Log progress for large directories
                            if len(s3_files) % 100 == 0:
                                logger.info(f"Found {len(s3_files)} files so far...")
            
            # Check if there are more pages
            if response.get('IsTruncated', False):
                continuation_token = response.get('NextContinuationToken')
                logger.info(f"Continuing pagination with token: {continuation_token[:20]}...")
            else:
                break
        
        logger.info(f"Completed S3 listing: found {len(s3_files)} files")
        return s3_files
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"Error listing S3 objects ({error_code}): {str(e)}")
        
        if error_code == 'NoSuchBucket':
            raise ValueError(f"S3 bucket does not exist: {bucket}")
        elif error_code == 'AccessDenied':
            raise ValueError(f"Access denied to S3 bucket: {bucket}")
        else:
            raise
    
    except Exception as e:
        logger.error(f"Unexpected error listing S3 files: {str(e)}")
        raise


def queue_files_for_ingestion(s3_files: List[str], jwt_token: Optional[str] = None) -> int:
    """
    Queue S3 files for ingestion processing via SQS.
    
    Args:
        s3_files: List of S3 URIs to queue for ingestion
        jwt_token: JWT token to include in messages (optional)
        
    Returns:
        Number of files successfully queued
    """
    if not s3_files:
        logger.info("No files to queue for ingestion")
        return 0
    
    queued_count = 0
    batch_size = 10  # SQS batch limit
    
    try:
        logger.info(f"Queuing {len(s3_files)} files for ingestion")
        
        # Process files in batches
        for i in range(0, len(s3_files), batch_size):
            batch = s3_files[i:i + batch_size]
            
            # Prepare batch messages
            entries = []
            for j, s3_uri in enumerate(batch):
                message_body = {
                    's3_uri': s3_uri
                }
                
                # Only include JWT token if provided
                if jwt_token:
                    message_body['jwt_token'] = jwt_token
                
                entries.append({
                    'Id': str(i + j),
                    'MessageBody': json.dumps(message_body),
                    'MessageAttributes': {
                        'source': {
                            'StringValue': 'sync_lambda',
                            'DataType': 'String'
                        },
                        's3_uri': {
                            'StringValue': s3_uri,
                            'DataType': 'String'
                        }
                    }
                })
            
            # Send batch to SQS
            response = sqs_client.send_message_batch(
                QueueUrl=SQS_QUEUE_URL,
                Entries=entries
            )
            
            # Check for failures
            successful_count = len(response.get('Successful', []))
            failed_count = len(response.get('Failed', []))
            
            queued_count += successful_count
            
            if failed_count > 0:
                logger.warning(f"Failed to queue {failed_count} messages in batch {i // batch_size + 1}")
                for failure in response.get('Failed', []):
                    logger.warning(f"Failed message ID {failure['Id']}: {failure['Message']}")
            
            logger.info(f"Batch {i // batch_size + 1}: queued {successful_count}/{len(batch)} files")
        
        logger.info(f"Successfully queued {queued_count}/{len(s3_files)} files for ingestion")
        return queued_count
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"Error sending messages to SQS ({error_code}): {str(e)}")
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error queuing files: {str(e)}")
        raise


def validate_s3_uri(s3_uri: str) -> tuple[str, str]:
    """
    Validate and parse S3 URI.
    
    Args:
        s3_uri: S3 URI to validate
        
    Returns:
        Tuple of (bucket, key)
        
    Raises:
        ValueError: If URI is invalid
    """
    try:
        parsed = urlparse(s3_uri)
        
        if parsed.scheme != 's3':
            raise ValueError(f"Invalid S3 URI scheme: {parsed.scheme}")
        
        bucket = parsed.netloc
        key = parsed.path.lstrip('/')
        
        if not bucket:
            raise ValueError("S3 URI missing bucket name")
        
        if not key:
            raise ValueError("S3 URI missing object key")
        
        return bucket, key
        
    except Exception as e:
        raise ValueError(f"Invalid S3 URI format: {s3_uri} - {str(e)}")