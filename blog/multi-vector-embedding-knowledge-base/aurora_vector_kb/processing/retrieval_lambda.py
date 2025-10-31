"""
Vector Retrieval Lambda Function

This Lambda function provides multiple vector search capabilities for the Aurora Vector Knowledge Base:
1. Content similarity search using document embeddings
2. Metadata similarity search using metadata embeddings  
3. Hybrid similarity search combining content and metadata
4. Filter and search using field embeddings followed by content search
"""

import json
import logging
import os
import time
from typing import Dict, Any, List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock_client = boto3.client('bedrock-runtime')
secrets_client = boto3.client('secretsmanager')

# Environment variables
DB_SECRET_NAME = os.environ.get('DB_SECRET_NAME')
BEDROCK_REGION = os.environ.get('BEDROCK_REGION', 'us-west-2')
TITAN_MODEL_ID = "amazon.titan-embed-text-v2:0"

# Cache for configurations
_db_config_cache = None

# Search type constants
SEARCH_TYPES = {
    'content_similarity',
    'metadata_similarity', 
    'hybrid_similarity',
    'filter_and_search'
}

FILTER_TYPES = {'provider', 'category', 'type'}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for vector retrieval operations.
    
    Args:
        event: Lambda event containing search parameters
        context: Lambda context object
        
    Returns:
        Response dictionary with search results
    """
    start_time = time.time()
    
    try:
        logger.info(f"Received retrieval request: {json.dumps(event, default=str)}")
        
        # Validate and extract parameters
        search_params = validate_and_extract_parameters(event)
        
        # Route to appropriate search handler
        search_type = search_params['search_type']
        
        if search_type == 'content_similarity':
            results = handle_content_similarity_search(search_params)
        elif search_type == 'metadata_similarity':
            results = handle_metadata_similarity_search(search_params)
        elif search_type == 'hybrid_similarity':
            results = handle_hybrid_similarity_search(search_params)
        elif search_type == 'filter_and_search':
            results = handle_filter_and_search(search_params)
        else:
            raise ValueError(f"Unsupported search type: {search_type}")
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Format response
        response = {
            'status': 'success',
            'search_type': search_type,
            'total_results': len(results),
            'execution_time_ms': execution_time_ms,
            'results': results
        }
        
        logger.info(f"Search completed successfully: {len(results)} results in {execution_time_ms}ms")
        return response
        
    except ValueError as e:
        error_msg = str(e)
        logger.error(f"Validation error: {error_msg}")
        return {
            'status': 'error',
            'error_type': 'validation_error',
            'message': error_msg,
            'execution_time_ms': int((time.time() - start_time) * 1000)
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"AWS service error ({error_code}): {str(e)}")
        return {
            'status': 'error',
            'error_type': 'aws_service_error',
            'message': f'AWS service error: {error_code}',
            'execution_time_ms': int((time.time() - start_time) * 1000)
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error_type': 'internal_error',
            'message': f'Internal server error: {str(e)}',
            'execution_time_ms': int((time.time() - start_time) * 1000)
        }


def validate_and_extract_parameters(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate input parameters and extract search configuration.
    
    Args:
        event: Lambda event dictionary
        
    Returns:
        Dictionary containing validated search parameters
        
    Raises:
        ValueError: If parameters are invalid
    """
    # Extract and validate search_type
    search_type = event.get('search_type')
    if not search_type:
        raise ValueError("search_type parameter is required")
    
    if search_type not in SEARCH_TYPES:
        raise ValueError(f"Invalid search_type. Must be one of: {', '.join(SEARCH_TYPES)}")
    
    # Extract and validate k parameter
    k = event.get('k', 3)
    if not isinstance(k, int) or k < 1 or k > 100:
        raise ValueError("k parameter must be an integer between 1 and 100")
    
    # Base parameters
    params = {
        'search_type': search_type,
        'k': k
    }
    
    # Validate parameters based on search type
    if search_type == 'content_similarity':
        query = event.get('query')
        if not query or not isinstance(query, str):
            raise ValueError("query parameter is required for content_similarity search")
        params['query'] = query.strip()
        
    elif search_type == 'metadata_similarity':
        metadata_query = event.get('metadata_query')
        if not metadata_query or not isinstance(metadata_query, str):
            raise ValueError("metadata_query parameter is required for metadata_similarity search")
        params['metadata_query'] = metadata_query.strip()
        
    elif search_type == 'hybrid_similarity':
        query = event.get('query')
        metadata_query = event.get('metadata_query')
        
        if not query or not isinstance(query, str):
            raise ValueError("query parameter is required for hybrid_similarity search")
        if not metadata_query or not isinstance(metadata_query, str):
            raise ValueError("metadata_query parameter is required for hybrid_similarity search")
            
        # Validate weights
        content_weight = event.get('content_weight', 0.7)
        metadata_weight = event.get('metadata_weight', 0.3)
        
        if not isinstance(content_weight, (int, float)) or not isinstance(metadata_weight, (int, float)):
            raise ValueError("content_weight and metadata_weight must be numeric")
            
        if abs(content_weight + metadata_weight - 1.0) > 0.001:
            raise ValueError("content_weight + metadata_weight must equal 1.0")
            
        params.update({
            'query': query.strip(),
            'metadata_query': metadata_query.strip(),
            'content_weight': float(content_weight),
            'metadata_weight': float(metadata_weight)
        })
        
    elif search_type == 'filter_and_search':
        query = event.get('query')
        filter_type = event.get('filter_type')
        filter_value = event.get('filter_value')
        
        if not query or not isinstance(query, str):
            raise ValueError("query parameter is required for filter_and_search")
        if not filter_type or filter_type not in FILTER_TYPES:
            raise ValueError(f"filter_type must be one of: {', '.join(FILTER_TYPES)}")
        if not filter_value or not isinstance(filter_value, str):
            raise ValueError("filter_value parameter is required for filter_and_search")
            
        params.update({
            'query': query.strip(),
            'filter_type': filter_type,
            'filter_value': filter_value.strip()
        })
    
    return params


def handle_content_similarity_search(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle content similarity search using document embeddings.
    
    Args:
        params: Search parameters including query and k
        
    Returns:
        List of search results with similarity scores
    """
    logger.info(f"Performing content similarity search for: {params['query'][:50]}...")
    
    # Generate query embedding
    query_embedding = generate_embedding(params['query'], dimensions=1024)
    query_vector = format_vector_for_postgres(query_embedding)
    
    # Execute database query
    conn = get_database_connection()
    try:
        with conn.cursor() as cursor:
            query_sql = """
            SELECT id, document, metadata, source_s3_uri,
                   1 - (embedding_document <=> %s::vector) as similarity_score
            FROM vector_store
            ORDER BY embedding_document <=> %s::vector
            LIMIT %s;
            """
            
            cursor.execute(query_sql, (query_vector, query_vector, params['k']))
            rows = cursor.fetchall()
            
            # Format results
            results = []
            for row in rows:
                result = {
                    'id': row['id'],
                    'document': row['document'],
                    'metadata': row['metadata'],
                    'source_s3_uri': row['source_s3_uri'],
                    'similarity_score': float(row['similarity_score'])
                }
                results.append(result)
            
            logger.info(f"Content similarity search returned {len(results)} results")
            return results
            
    finally:
        conn.close()


def handle_metadata_similarity_search(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle metadata similarity search using metadata embeddings.
    
    Args:
        params: Search parameters including metadata_query and k
        
    Returns:
        List of search results with metadata similarity scores
    """
    logger.info(f"Performing metadata similarity search for: {params['metadata_query'][:50]}...")
    
    # Generate metadata query embedding
    metadata_embedding = generate_embedding(params['metadata_query'], dimensions=512)
    metadata_vector = format_vector_for_postgres(metadata_embedding)
    
    # Execute database query
    conn = get_database_connection()
    try:
        with conn.cursor() as cursor:
            query_sql = """
            SELECT id, document, metadata, source_s3_uri,
                   1 - (embedding_metadata <=> %s::vector) as similarity_score
            FROM vector_store
            ORDER BY embedding_metadata <=> %s::vector
            LIMIT %s;
            """
            
            cursor.execute(query_sql, (metadata_vector, metadata_vector, params['k']))
            rows = cursor.fetchall()
            
            # Format results
            results = []
            for row in rows:
                result = {
                    'id': row['id'],
                    'document': row['document'],
                    'metadata': row['metadata'],
                    'source_s3_uri': row['source_s3_uri'],
                    'similarity_score': float(row['similarity_score'])
                }
                results.append(result)
            
            logger.info(f"Metadata similarity search returned {len(results)} results")
            return results
            
    finally:
        conn.close()


def handle_hybrid_similarity_search(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle hybrid similarity search combining content and metadata embeddings.
    
    Args:
        params: Search parameters including query, metadata_query, weights, and k
        
    Returns:
        List of search results with combined similarity scores
    """
    logger.info(f"Performing hybrid similarity search...")
    
    # Generate embeddings for both content and metadata
    content_embedding = generate_embedding(params['query'], dimensions=1024)
    metadata_embedding = generate_embedding(params['metadata_query'], dimensions=512)
    content_vector = format_vector_for_postgres(content_embedding)
    metadata_vector = format_vector_for_postgres(metadata_embedding)
    
    # Execute database query with weighted combination
    conn = get_database_connection()
    try:
        with conn.cursor() as cursor:
            query_sql = """
            SELECT id, document, metadata, source_s3_uri,
                   (%s * (1 - (embedding_document <=> %s::vector))) + 
                   (%s * (1 - (embedding_metadata <=> %s::vector))) as combined_score,
                   1 - (embedding_document <=> %s::vector) as content_score,
                   1 - (embedding_metadata <=> %s::vector) as metadata_score
            FROM vector_store
            ORDER BY combined_score DESC
            LIMIT %s;
            """
            
            cursor.execute(query_sql, (
                params['content_weight'], content_vector,
                params['metadata_weight'], metadata_vector,
                content_vector, metadata_vector,
                params['k']
            ))
            rows = cursor.fetchall()
            
            # Format results
            results = []
            for row in rows:
                result = {
                    'id': row['id'],
                    'document': row['document'],
                    'metadata': row['metadata'],
                    'source_s3_uri': row['source_s3_uri'],
                    'similarity_score': float(row['combined_score']),
                    'content_score': float(row['content_score']),
                    'metadata_score': float(row['metadata_score'])
                }
                results.append(result)
            
            logger.info(f"Hybrid similarity search returned {len(results)} results")
            return results
            
    finally:
        conn.close()


def handle_filter_and_search(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle filter and search using field embeddings followed by content search.
    
    Args:
        params: Search parameters including query, filter_type, filter_value, and k
        
    Returns:
        List of search results with both filter and content scores
    """
    logger.info(f"Performing filter and search: {params['filter_type']}={params['filter_value'][:30]}...")
    
    # Generate embeddings
    filter_embedding = generate_embedding(params['filter_value'], dimensions=256)
    content_embedding = generate_embedding(params['query'], dimensions=1024)
    filter_vector = format_vector_for_postgres(filter_embedding)
    content_vector = format_vector_for_postgres(content_embedding)
    
    # Calculate k*5 for initial filtering
    filter_limit = params['k'] * 5
    
    # Execute two-stage query
    conn = get_database_connection()
    try:
        with conn.cursor() as cursor:
            # Build the field column name
            field_column = f"embedding_{params['filter_type']}"
            
            query_sql = f"""
            WITH filtered_docs AS (
              SELECT id, document, metadata, source_s3_uri, embedding_document,
                     1 - ({field_column} <=> %s::vector) as filter_score
              FROM vector_store
              ORDER BY {field_column} <=> %s::vector
              LIMIT %s
            )
            SELECT id, document, metadata, source_s3_uri,
                   1 - (embedding_document <=> %s::vector) as content_score,
                   filter_score
            FROM filtered_docs
            ORDER BY embedding_document <=> %s::vector
            LIMIT %s;
            """
            
            cursor.execute(query_sql, (
                filter_vector, filter_vector, filter_limit,
                content_vector, content_vector, params['k']
            ))
            rows = cursor.fetchall()
            
            # Format results
            results = []
            for row in rows:
                result = {
                    'id': row['id'],
                    'document': row['document'],
                    'metadata': row['metadata'],
                    'source_s3_uri': row['source_s3_uri'],
                    'similarity_score': float(row['content_score']),
                    'content_score': float(row['content_score']),
                    'filter_score': float(row['filter_score'])
                }
                results.append(result)
            
            logger.info(f"Filter and search returned {len(results)} results")
            return results
            
    finally:
        conn.close()


def format_vector_for_postgres(embedding: List[float]) -> str:
    """
    Format embedding vector for PostgreSQL pgvector insertion.
    
    Args:
        embedding: Embedding vector as list of floats
        
    Returns:
        Formatted string for pgvector
    """
    # pgvector expects format like '[1.0,2.0,3.0]'
    return '[' + ','.join(map(str, embedding)) + ']'


def generate_embedding(text: str, dimensions: int) -> List[float]:
    """
    Generate embedding for text using Amazon Titan v2.
    
    Args:
        text: Text to embed
        dimensions: Target embedding dimensions (256, 512, or 1024)
        
    Returns:
        Embedding vector as list of floats
        
    Raises:
        ValueError: If dimensions are not supported
        ClientError: If Bedrock API call fails
    """
    if dimensions not in [256, 512, 1024]:
        raise ValueError(f"Unsupported embedding dimensions: {dimensions}")
    
    try:
        # Prepare request for Titan Text Embedding v2
        request_body = {
            "inputText": text,
            "dimensions": dimensions,
            "normalize": True
        }
        
        # Call Bedrock
        response = bedrock_client.invoke_model(
            modelId=TITAN_MODEL_ID,
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        embedding = response_body['embedding']
        
        # Validate embedding dimensions
        if len(embedding) != dimensions:
            raise ValueError(f"Expected {dimensions} dimensions, got {len(embedding)}")
        
        return embedding
        
    except ClientError as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating embedding: {str(e)}")
        raise ValueError(f"Failed to generate embedding: {str(e)}")


def get_database_connection():
    """
    Get database connection with connection pooling support.
    
    Returns:
        psycopg2 database connection
    """
    db_config = get_database_config()
    
    try:
        # Create connection
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['username'],
            password=db_config['password'],
            sslmode='require',
            connect_timeout=30,
            cursor_factory=RealDictCursor
        )
        
        logger.debug("Database connection established")
        return conn
        
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise


def get_database_config() -> Dict[str, str]:
    """
    Get database configuration from Secrets Manager with caching.
    
    Returns:
        Dictionary containing database configuration
    """
    global _db_config_cache
    
    if _db_config_cache is not None:
        return _db_config_cache
    
    try:
        logger.info(f"Retrieving database configuration from secret: {DB_SECRET_NAME}")
        
        response = secrets_client.get_secret_value(SecretId=DB_SECRET_NAME)
        config_data = json.loads(response['SecretString'])
        
        # Aurora credentials secret only contains username and password
        # We need to add the other required fields from environment or defaults
        required_fields = ['username', 'password']
        for field in required_fields:
            if field not in config_data:
                raise ValueError(f"Missing required field in database config: {field}")
        
        # Add missing fields from environment variables
        # These are provided by the Lambda construct from Aurora cluster configuration
        config_data['database'] = os.environ.get('DB_NAME', 'vector_kb')
        config_data['host'] = os.environ.get('DB_HOST')
        config_data['port'] = int(os.environ.get('DB_PORT', '5432'))
        
        # Validate that required environment variables are present
        if not config_data['host']:
            raise ValueError("DB_HOST environment variable is required")
        if not config_data['database']:
            raise ValueError("DB_NAME environment variable is required")
        
        _db_config_cache = config_data
        logger.info("Database configuration retrieved successfully")
        return _db_config_cache
        
    except ClientError as e:
        logger.error(f"Error retrieving database configuration: {str(e)}")
        raise
    except (KeyError, json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing database configuration: {str(e)}")
        raise