"""
Custom Resource Lambda for Database Initialization

This Lambda function handles CloudFormation custom resource lifecycle events
to initialize the Aurora PostgreSQL database with pgvector extension,
create the vector_store table, and set up all necessary indexes.
"""

import json
import logging
import os
import urllib3
import psycopg2
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize HTTP client for CloudFormation responses
http = urllib3.PoolManager()

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for CloudFormation custom resource lifecycle events.
    
    Args:
        event: CloudFormation custom resource event
        context: Lambda context object
        
    Returns:
        Response dictionary for CloudFormation
    """
    logger.info(f"Received event: {json.dumps(event, default=str)}")
    
    # Extract event properties
    request_type = event['RequestType']
    response_url = event['ResponseURL']
    stack_id = event['StackId']
    request_id = event['RequestId']
    logical_resource_id = event['LogicalResourceId']
    
    # Initialize response data
    response_data = {}
    physical_resource_id = f"aurora-vector-kb-db-init-{request_id}"
    
    try:
        if request_type == 'Create':
            logger.info("Processing Create request")
            response_data = handle_create(event)
            status = 'SUCCESS'
            
        elif request_type == 'Update':
            logger.info("Processing Update request")
            # For database initialization, we typically don't need to do anything on update
            # unless schema changes are required
            response_data = handle_update(event)
            status = 'SUCCESS'
            
        elif request_type == 'Delete':
            logger.info("Processing Delete request")
            # For database initialization, we typically don't delete the schema on stack deletion
            # as it may contain important data
            response_data = handle_delete(event)
            status = 'SUCCESS'
            
        else:
            logger.error(f"Unknown request type: {request_type}")
            status = 'FAILED'
            response_data = {'Error': f'Unknown request type: {request_type}'}
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        status = 'FAILED'
        response_data = {'Error': str(e)}
    
    # Send response to CloudFormation
    send_response(
        event=event,
        context=context,
        response_status=status,
        response_data=response_data,
        physical_resource_id=physical_resource_id
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'status': status,
            'physicalResourceId': physical_resource_id,
            'data': response_data
        })
    }


def handle_create(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle CloudFormation Create request.
    
    Args:
        event: CloudFormation event
        
    Returns:
        Response data dictionary
    """
    logger.info("Initializing database schema and indexes")
    
    # Get database connection parameters from event properties
    properties = event.get('ResourceProperties', {})
    
    # Connect to database and initialize schema
    connection = get_database_connection(properties)
    
    try:
        with connection:
            with connection.cursor() as cursor:
                # Enable pgvector extension
                enable_pgvector_extension(cursor)
                
                # Create vector_store table
                create_vector_store_table(cursor)
                
                # Create indexes for vector similarity search
                create_vector_indexes(cursor)
                
                # Create indexes for filtering
                create_filter_indexes(cursor)
                
                # Commit all changes
                connection.commit()
                
        logger.info("Database initialization completed successfully")
        
        return {
            'Message': 'Database schema and indexes created successfully',
            'TableCreated': 'vector_store',
            'ExtensionEnabled': 'pgvector',
            'IndexesCreated': [
                'idx_vector_store_embedding_document',
                'idx_vector_store_embedding_metadata',
                'idx_vector_store_embedding_provider',
                'idx_vector_store_embedding_category',
                'idx_vector_store_embedding_type',
                'idx_vector_store_provider',
                'idx_vector_store_category',
                'idx_vector_store_type',
                'idx_vector_store_source_s3_uri'
            ]
        }
        
    finally:
        connection.close()


def handle_update(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle CloudFormation Update request.
    
    Args:
        event: CloudFormation event
        
    Returns:
        Response data dictionary
    """
    logger.info("Processing update request - no action required for database initialization")
    
    return {
        'Message': 'Update completed - no database changes required',
        'Action': 'None'
    }


def handle_delete(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle CloudFormation Delete request.
    
    Args:
        event: CloudFormation event
        
    Returns:
        Response data dictionary
    """
    logger.info("Processing delete request - preserving database schema and data")
    
    return {
        'Message': 'Delete completed - database schema and data preserved',
        'Action': 'None'
    }


def get_database_connection(properties: Dict[str, Any]) -> psycopg2.extensions.connection:
    """
    Establish connection to Aurora PostgreSQL database.
    
    Args:
        properties: CloudFormation resource properties
        
    Returns:
        Database connection object
    """
    # Get database connection parameters
    db_host = properties.get('DatabaseHost')
    db_port = properties.get('DatabasePort', 5432)
    db_name = properties.get('DatabaseName', 'vector_kb')
    credentials_secret_arn = properties.get('CredentialsSecretArn')
    
    if not db_host or not credentials_secret_arn:
        raise ValueError("DatabaseHost and CredentialsSecretArn are required")
    
    # Retrieve database credentials from Secrets Manager
    credentials = get_database_credentials(credentials_secret_arn)
    
    # Establish database connection
    logger.info(f"Connecting to database at {db_host}:{db_port}/{db_name}")
    
    connection = psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=credentials['username'],
        password=credentials['password'],
        connect_timeout=30,
        sslmode='require'
    )
    
    logger.info("Database connection established successfully")
    return connection


def get_database_credentials(secret_arn: str) -> Dict[str, str]:
    """
    Retrieve database credentials from AWS Secrets Manager.
    
    Args:
        secret_arn: ARN of the secret containing database credentials
        
    Returns:
        Dictionary containing username and password
    """
    try:
        logger.info(f"Retrieving credentials from secret: {secret_arn}")
        
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret_data = json.loads(response['SecretString'])
        
        return {
            'username': secret_data['username'],
            'password': secret_data['password']
        }
        
    except ClientError as e:
        logger.error(f"Error retrieving database credentials: {str(e)}")
        raise
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"Error parsing database credentials: {str(e)}")
        raise


def enable_pgvector_extension(cursor: psycopg2.extensions.cursor) -> None:
    """
    Enable the pgvector extension in the database.
    
    Args:
        cursor: Database cursor
    """
    logger.info("Enabling pgvector extension")
    
    # Check if extension already exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM pg_extension 
            WHERE extname = 'vector'
        );
    """)
    
    extension_exists = cursor.fetchone()[0]
    
    if not extension_exists:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        logger.info("pgvector extension enabled successfully")
    else:
        logger.info("pgvector extension already exists")


def create_vector_store_table(cursor: psycopg2.extensions.cursor) -> None:
    """
    Create the vector_store table with the specified schema.
    
    Args:
        cursor: Database cursor
    """
    logger.info("Creating vector_store table")
    
    # Check if table already exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'vector_store'
        );
    """)
    
    table_exists = cursor.fetchone()[0]
    
    if not table_exists:
        create_table_sql = """
        CREATE TABLE vector_store (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document TEXT NOT NULL,
            embedding_document VECTOR(1024) NOT NULL,
            metadata JSONB NOT NULL,
            embedding_metadata VECTOR(512) NOT NULL,
            provider TEXT NOT NULL,
            embedding_provider VECTOR(256) NOT NULL,
            category TEXT NOT NULL,
            embedding_category VECTOR(256) NOT NULL,
            type TEXT NOT NULL,
            embedding_type VECTOR(256) NOT NULL,
            source_s3_uri TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        cursor.execute(create_table_sql)
        logger.info("vector_store table created successfully")
    else:
        logger.info("vector_store table already exists")


def create_vector_indexes(cursor: psycopg2.extensions.cursor) -> None:
    """
    Create HNSW indexes for vector similarity search.
    
    Args:
        cursor: Database cursor
    """
    logger.info("Creating vector similarity search indexes")
    
    vector_indexes = [
        ("idx_vector_store_embedding_document", "embedding_document"),
        ("idx_vector_store_embedding_metadata", "embedding_metadata"),
        ("idx_vector_store_embedding_provider", "embedding_provider"),
        ("idx_vector_store_embedding_category", "embedding_category"),
        ("idx_vector_store_embedding_type", "embedding_type")
    ]
    
    for index_name, column_name in vector_indexes:
        # Check if index already exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND tablename = 'vector_store' 
                AND indexname = %s
            );
        """, (index_name,))
        
        index_exists = cursor.fetchone()[0]
        
        if not index_exists:
            create_index_sql = f"""
            CREATE INDEX {index_name} ON vector_store 
            USING hnsw ({column_name} vector_cosine_ops);
            """
            
            cursor.execute(create_index_sql)
            logger.info(f"Created vector index: {index_name}")
        else:
            logger.info(f"Vector index already exists: {index_name}")


def create_filter_indexes(cursor: psycopg2.extensions.cursor) -> None:
    """
    Create B-tree indexes for filtering operations.
    
    Args:
        cursor: Database cursor
    """
    logger.info("Creating filter indexes")
    
    filter_indexes = [
        ("idx_vector_store_provider", "provider"),
        ("idx_vector_store_category", "category"),
        ("idx_vector_store_type", "type"),
        ("idx_vector_store_source_s3_uri", "source_s3_uri")
    ]
    
    for index_name, column_name in filter_indexes:
        # Check if index already exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND tablename = 'vector_store' 
                AND indexname = %s
            );
        """, (index_name,))
        
        index_exists = cursor.fetchone()[0]
        
        if not index_exists:
            create_index_sql = f"""
            CREATE INDEX {index_name} ON vector_store ({column_name});
            """
            
            cursor.execute(create_index_sql)
            logger.info(f"Created filter index: {index_name}")
        else:
            logger.info(f"Filter index already exists: {index_name}")


def send_response(
    event: Dict[str, Any],
    context: Any,
    response_status: str,
    response_data: Dict[str, Any],
    physical_resource_id: str,
    no_echo: bool = False
) -> None:
    """
    Send response to CloudFormation.
    
    Args:
        event: CloudFormation event
        context: Lambda context
        response_status: SUCCESS or FAILED
        response_data: Response data dictionary
        physical_resource_id: Physical resource ID
        no_echo: Whether to mask response data in CloudFormation logs
    """
    response_url = event['ResponseURL']
    
    response_body = {
        'Status': response_status,
        'Reason': f'See CloudWatch Log Stream: {context.log_stream_name}',
        'PhysicalResourceId': physical_resource_id,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'NoEcho': no_echo,
        'Data': response_data
    }
    
    json_response_body = json.dumps(response_body)
    
    logger.info(f"Sending response to CloudFormation: {json_response_body}")
    
    headers = {
        'content-type': '',
        'content-length': str(len(json_response_body))
    }
    
    try:
        response = http.request(
            'PUT',
            response_url,
            body=json_response_body,
            headers=headers
        )
        logger.info(f"CloudFormation response sent successfully. Status: {response.status}")
        
    except Exception as e:
        logger.error(f"Error sending response to CloudFormation: {str(e)}")
        raise