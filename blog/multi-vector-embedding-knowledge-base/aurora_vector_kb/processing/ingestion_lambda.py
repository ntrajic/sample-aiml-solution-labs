"""
Ingestion Lambda Function for Document Processing and Vector Storage

This Lambda function handles document ingestion by processing SQS messages,
downloading documents from S3, extracting metadata, chunking content,
generating embeddings, and storing everything in Aurora PostgreSQL with pgvector.
"""

import json
import logging
import os
import re
from typing import Dict, Any, List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError, BotoCoreError

import psycopg2
from psycopg2.extras import RealDictCursor
import tiktoken
from datetime import datetime
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
bedrock_client = boto3.client('bedrock-runtime')
secrets_client = boto3.client('secretsmanager')

# Environment variables
DB_SECRET_NAME = os.environ.get('DB_SECRET_NAME')
TITAN_MODEL_ID = "amazon.titan-embed-text-v2:0"

# Cache for configurations
_db_config_cache = None
_tokenizer_cache = None

# Chunking configuration
CHUNK_SIZE = 500  # tokens
CHUNK_OVERLAP_PERCENT = 10  # 10% overlap
CHUNK_OVERLAP_SIZE = int(CHUNK_SIZE * CHUNK_OVERLAP_PERCENT / 100)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for document ingestion processing.
    
    Args:
        event: SQS event containing messages with S3 URIs and JWT tokens
        context: Lambda context object
        
    Returns:
        Response dictionary with processing results
    """
    logger.info(f"Received ingestion request with {len(event.get('Records', []))} messages")
    
    processed_count = 0
    failed_count = 0
    
    for record in event.get('Records', []):
        try:
            # Parse SQS message
            message_body = json.loads(record['body'])
            s3_uri = message_body.get('s3_uri')
            
            logger.info(f"Processing document: {s3_uri}")
            
            # Validate required parameters
            if not s3_uri:
                raise ValueError("s3_uri parameter is required")
            
            # Create default user claims for audit trail
            user_claims = {
                'sub': 'system',
                'username': 'ingestion-lambda',
                'aud': 'aurora-vector-kb'
            }
            
            # Process the document
            process_document(s3_uri, user_claims)
            processed_count += 1
            
            logger.info(f"Successfully processed document: {s3_uri}")
            
        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to process message: {str(e)}", exc_info=True)
            # Continue processing other messages
    
    # Return processing summary
    response = {
        'processed_count': processed_count,
        'failed_count': failed_count,
        'total_messages': len(event.get('Records', []))
    }
    
    logger.info(f"Ingestion batch completed: {response}")
    return response


def process_document(s3_uri: str, user_claims: Dict[str, Any]) -> None:
    """
    Process a single document: download, chunk, generate embeddings, and store.
    
    Args:
        s3_uri: S3 URI of the document to process
        user_claims: JWT user claims for audit trail
    """
    # Parse S3 URI
    bucket, key = parse_s3_uri(s3_uri)
    
    # Download document content
    document_content = download_s3_document(bucket, key)
    
    # Read metadata from companion JSON file
    metadata = read_metadata_file(bucket, key)
    
    # Chunk the document
    chunks = chunk_document(document_content)
    
    logger.info(f"Document chunked into {len(chunks)} pieces")
    
    # Generate embeddings for all content
    embeddings_data = generate_all_embeddings(chunks, metadata)
    
    # Store in database
    store_document_data(s3_uri, chunks, metadata, embeddings_data, user_claims)


def download_s3_document(bucket: str, key: str) -> str:
    """
    Download document content from S3.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        
    Returns:
        Document content as string
    """
    try:
        logger.info(f"Downloading document from s3://{bucket}/{key}")
        
        response = s3_client.get_object(Bucket=bucket, Key=key)
        
        # Read content based on content type
        content_type = response.get('ContentType', 'text/plain')
        content_bytes = response['Body'].read()
        
        # Handle different content types
        # Try to decode as text regardless of content type
        # This handles cases where S3 sets content-type to binary/octet-stream for text files
        try:
            content = content_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # Try other common encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    content = content_bytes.decode(encoding)
                    logger.info(f"Successfully decoded document using {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # If all text decodings fail, this is likely a binary file
                raise ValueError(
                    f"Unable to decode document as text. Content type: {content_type}. "
                    f"Only text-based documents are supported. File: {key}"
                )
        
        logger.info(f"Downloaded document: {len(content)} characters")
        return content
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"Error downloading S3 object ({error_code}): {str(e)}")
        
        if error_code == 'NoSuchKey':
            raise ValueError(f"S3 object does not exist: s3://{bucket}/{key}")
        elif error_code == 'AccessDenied':
            raise ValueError(f"Access denied to S3 object: s3://{bucket}/{key}")
        else:
            raise
    
    except Exception as e:
        logger.error(f"Unexpected error downloading document: {str(e)}")
        raise


def read_metadata_file(bucket: str, key: str) -> Dict[str, Any]:
    """
    Read metadata from companion JSON file in the same S3 location.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key of the document
        
    Returns:
        Dictionary containing metadata from JSON file
    """
    logger.info(f"Reading metadata file for document: {key}")
    
    # Construct metadata file path
    # For document "example.txt", look for "example.txt.metadata.json"
    metadata_key = f"{key}.metadata.json"
    
    try:
        # Download metadata file
        logger.info(f"Downloading metadata from s3://{bucket}/{metadata_key}")
        
        response = s3_client.get_object(Bucket=bucket, Key=metadata_key)
        metadata_content = response['Body'].read().decode('utf-8')
        
        # Parse JSON metadata
        metadata_json = json.loads(metadata_content)
        
        # Validate required fields
        required_fields = ['category', 'industry']
        for field in required_fields:
            if field not in metadata_json:
                raise ValueError(f"Missing required field in metadata: {field}")
        
        # Process category field - ensure it's a list
        category = metadata_json['category']
        if isinstance(category, str):
            # Split comma-separated string into list
            category = [cat.strip() for cat in category.split(',')]
        elif not isinstance(category, list):
            category = [str(category)]
        
        # Get file information
        filename = key.split('/')[-1]
        file_extension = filename.split('.')[-1].lower() if '.' in filename else ''
        
        # Create consolidated metadata with additional system fields
        metadata = {
            "category": category,
            "industry": metadata_json['industry'],
            "source_file": filename,
            "file_extension": file_extension,
            "processed_at": datetime.utcnow().isoformat()
        }
        
        # Add any additional fields from the metadata file
        for key_name, value in metadata_json.items():
            if key_name not in ['category', 'industry']:
                metadata[key_name] = value
        
        logger.info(f"Read metadata: category={metadata['category']}, industry={metadata['industry']}")
        return metadata
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"Error reading metadata file ({error_code}): {str(e)}")
        
        if error_code == 'NoSuchKey':
            raise ValueError(f"Metadata file not found: s3://{bucket}/{metadata_key}. Each document must have a companion .metadata.json file.")
        elif error_code == 'AccessDenied':
            raise ValueError(f"Access denied to metadata file: s3://{bucket}/{metadata_key}")
        else:
            raise ValueError(f"Error accessing metadata file: {error_code}")
    
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing metadata JSON: {str(e)}")
        raise ValueError(f"Invalid JSON in metadata file s3://{bucket}/{metadata_key}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error reading metadata: {str(e)}")
        raise ValueError(f"Error reading metadata file: {str(e)}")





def chunk_document(document_content: str) -> List[str]:
    """
    Split document content into chunks with fixed size and overlap.
    
    Args:
        document_content: Document text content to chunk
        
    Returns:
        List of text chunks
    """
    logger.info(f"Chunking document of {len(document_content)} characters")
    
    # Get tokenizer
    tokenizer = get_tokenizer()
    
    # Tokenize the entire document
    tokens = tokenizer.encode(document_content)
    total_tokens = len(tokens)
    
    logger.info(f"Document contains {total_tokens} tokens")
    
    if total_tokens <= CHUNK_SIZE:
        # Document is small enough to be a single chunk
        return [document_content]
    
    chunks = []
    start_idx = 0
    
    while start_idx < total_tokens:
        # Calculate end index for this chunk
        end_idx = min(start_idx + CHUNK_SIZE, total_tokens)
        
        # Extract tokens for this chunk
        chunk_tokens = tokens[start_idx:end_idx]
        
        # Decode tokens back to text
        chunk_text = tokenizer.decode(chunk_tokens)
        
        # Try to break at sentence boundaries for better readability
        if end_idx < total_tokens:  # Not the last chunk
            chunk_text = break_at_sentence_boundary(chunk_text)
        
        chunks.append(chunk_text.strip())
        
        # Move start index for next chunk (with overlap)
        if end_idx >= total_tokens:
            break  # This was the last chunk
        
        start_idx = end_idx - CHUNK_OVERLAP_SIZE
    
    logger.info(f"Created {len(chunks)} chunks")
    return chunks


def break_at_sentence_boundary(text: str) -> str:
    """
    Try to break text at a sentence boundary for better chunk readability.
    
    Args:
        text: Text to break
        
    Returns:
        Text broken at sentence boundary if possible
    """
    # Look for sentence endings in the last 20% of the text
    break_point = int(len(text) * 0.8)
    search_text = text[break_point:]
    
    # Sentence ending patterns
    sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
    
    # Find the last sentence ending
    last_ending = -1
    for ending in sentence_endings:
        pos = search_text.rfind(ending)
        if pos > last_ending:
            last_ending = pos
    
    if last_ending > 0:
        # Break at sentence boundary
        actual_pos = break_point + last_ending + 1
        return text[:actual_pos].strip()
    
    # No good break point found, return original text
    return text


def get_tokenizer():
    """
    Get cached tokenizer instance.
    
    Returns:
        tiktoken tokenizer instance
    """
    global _tokenizer_cache
    
    if _tokenizer_cache is None:
        # Use cl100k_base encoding (used by GPT-3.5/4 and similar models)
        _tokenizer_cache = tiktoken.get_encoding("cl100k_base")
    
    return _tokenizer_cache


def parse_s3_uri(s3_uri: str) -> Tuple[str, str]:
    """
    Parse S3 URI into bucket and key components.
    
    Args:
        s3_uri: S3 URI to parse
        
    Returns:
        Tuple of (bucket, key)
    """
    if not s3_uri.startswith('s3://'):
        raise ValueError(f"Invalid S3 URI format: {s3_uri}")
    
    # Remove s3:// prefix and split
    path = s3_uri[5:]
    parts = path.split('/', 1)
    
    if len(parts) != 2:
        raise ValueError(f"Invalid S3 URI format: {s3_uri}")
    
    bucket, key = parts
    
    if not bucket or not key:
        raise ValueError(f"Invalid S3 URI format: {s3_uri}")
    
    return bucket, key





def generate_all_embeddings(chunks: List[str], metadata: Dict[str, Any]) -> Dict[str, List[List[float]]]:
    """
    Generate embeddings for document chunks and metadata using Titan v2.
    
    Args:
        chunks: List of document text chunks
        metadata: Document metadata dictionary
        
    Returns:
        Dictionary containing all generated embeddings
    """
    logger.info(f"Generating embeddings for {len(chunks)} chunks and metadata")
    
    embeddings_data = {
        'document_embeddings': [],
        'metadata_embedding': None,
        'category_embedding': None,
        'industry_embedding': None
    }
    
    # Generate embeddings for document chunks (1024 dimensions)
    embeddings_data['document_embeddings'] = generate_document_embeddings(chunks)
    
    # Generate embedding for consolidated metadata (512 dimensions)
    metadata_text = json.dumps(metadata, sort_keys=True)
    embeddings_data['metadata_embedding'] = generate_metadata_embedding(metadata_text)
    
    # Generate embeddings for individual metadata fields (256 dimensions each)
    # Handle category as list - join with commas
    category_text = ', '.join(metadata['category']) if isinstance(metadata['category'], list) else str(metadata['category'])
    embeddings_data['category_embedding'] = generate_field_embedding(category_text)
    
    embeddings_data['industry_embedding'] = generate_field_embedding(metadata['industry'])
    
    logger.info("All embeddings generated successfully")
    return embeddings_data


def generate_document_embeddings(chunks: List[str]) -> List[List[float]]:
    """
    Generate embeddings for document chunks using Titan v2 (1024 dimensions).
    
    Args:
        chunks: List of text chunks
        
    Returns:
        List of embedding vectors (1024 dimensions each)
    """
    logger.info(f"Generating document embeddings for {len(chunks)} chunks")
    
    embeddings = []
    batch_size = 10  # Process in batches to avoid timeouts
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        batch_embeddings = []
        
        for chunk in batch:
            try:
                # Prepare request for Titan Text Embedding v2
                request_body = {
                    "inputText": chunk,
                    "dimensions": 1024,
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
                if len(embedding) != 1024:
                    raise ValueError(f"Expected 1024 dimensions, got {len(embedding)}")
                
                batch_embeddings.append(embedding)
                
            except Exception as e:
                logger.error(f"Error generating embedding for chunk: {str(e)}")
                raise
        
        embeddings.extend(batch_embeddings)
        logger.info(f"Generated embeddings for batch {i // batch_size + 1}/{(len(chunks) + batch_size - 1) // batch_size}")
    
    logger.info(f"Generated {len(embeddings)} document embeddings")
    return embeddings


def generate_metadata_embedding(metadata_text: str) -> List[float]:
    """
    Generate embedding for consolidated metadata using Titan v2 (512 dimensions).
    
    Args:
        metadata_text: JSON string of metadata
        
    Returns:
        Embedding vector (512 dimensions)
    """
    logger.info("Generating metadata embedding")
    
    try:
        # Prepare request for Titan Text Embedding v2
        request_body = {
            "inputText": metadata_text,
            "dimensions": 512,
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
        if len(embedding) != 512:
            raise ValueError(f"Expected 512 dimensions, got {len(embedding)}")
        
        logger.info("Metadata embedding generated successfully")
        return embedding
        
    except Exception as e:
        logger.error(f"Error generating metadata embedding: {str(e)}")
        raise


def generate_field_embedding(field_text: str) -> List[float]:
    """
    Generate embedding for individual metadata field using Titan v2 (256 dimensions).
    
    Args:
        field_text: Text content of the field
        
    Returns:
        Embedding vector (256 dimensions)
    """
    logger.info(f"Generating field embedding for: {field_text[:50]}...")
    
    try:
        # Prepare request for Titan Text Embedding v2
        request_body = {
            "inputText": field_text,
            "dimensions": 256,
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
        if len(embedding) != 256:
            raise ValueError(f"Expected 256 dimensions, got {len(embedding)}")
        
        logger.info("Field embedding generated successfully")
        return embedding
        
    except Exception as e:
        logger.error(f"Error generating field embedding: {str(e)}")
        raise


def generate_embeddings_batch(texts: List[str], dimensions: int) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in batch for efficiency.
    
    Args:
        texts: List of text strings to embed
        dimensions: Target embedding dimensions (256, 512, or 1024)
        
    Returns:
        List of embedding vectors
    """
    logger.info(f"Generating batch embeddings for {len(texts)} texts ({dimensions}D)")
    
    embeddings = []
    
    for text in texts:
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
            
            embeddings.append(embedding)
            
        except Exception as e:
            logger.error(f"Error generating embedding for text: {str(e)}")
            raise
    
    logger.info(f"Generated {len(embeddings)} batch embeddings")
    return embeddings


def store_document_data(s3_uri: str, chunks: List[str], metadata: Dict[str, Any], 
                       embeddings_data: Dict[str, Any], user_claims: Dict[str, Any]) -> None:
    """
    Store document chunks and embeddings in the database.
    
    Args:
        s3_uri: Source S3 URI of the document
        chunks: List of document text chunks
        metadata: Document metadata
        embeddings_data: All generated embeddings
        user_claims: JWT user claims for audit
    """
    logger.info(f"Storing document data for {len(chunks)} chunks")
    
    # Get database connection
    conn = get_database_connection()
    
    try:
        with conn.cursor() as cursor:
            # Start transaction
            conn.autocommit = False
            
            # Delete existing records with the same S3 URI
            delete_existing_records(cursor, s3_uri)
            
            # Insert new records
            insert_document_chunks(cursor, s3_uri, chunks, metadata, embeddings_data, user_claims)
            
            # Commit transaction
            conn.commit()
            logger.info(f"Successfully stored {len(chunks)} chunks for {s3_uri}")
            
    except Exception as e:
        # Rollback on error
        conn.rollback()
        logger.error(f"Error storing document data: {str(e)}")
        raise
    finally:
        conn.close()


def store_document_data(s3_uri: str, chunks: List[str], metadata: Dict[str, Any], 
                       embeddings_data: Dict[str, Any], user_claims: Dict[str, Any]) -> None:
    """
    Store document chunks and embeddings in the database.
    
    Args:
        s3_uri: Source S3 URI of the document
        chunks: List of document text chunks
        metadata: Document metadata
        embeddings_data: All generated embeddings
        user_claims: JWT user claims for audit
    """
    logger.info(f"Storing document data for {len(chunks)} chunks")
    
    # Calculate file size from chunks
    total_content = ''.join(chunks)
    file_size = len(total_content.encode('utf-8'))
    metadata['file_size'] = file_size
    
    # Get database connection
    conn = get_database_connection()
    
    try:
        with conn.cursor() as cursor:
            # Start transaction
            conn.autocommit = False
            
            # Delete existing records with the same S3 URI
            delete_existing_records(cursor, s3_uri)
            
            # Insert new records
            insert_document_chunks(cursor, s3_uri, chunks, metadata, embeddings_data, user_claims)
            
            # Commit transaction
            conn.commit()
            logger.info(f"Successfully stored {len(chunks)} chunks for {s3_uri}")
            
    except Exception as e:
        # Rollback on error
        conn.rollback()
        logger.error(f"Error storing document data: {str(e)}")
        raise
    finally:
        conn.close()


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
        
        logger.info("Database connection established")
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


def delete_existing_records(cursor, s3_uri: str) -> None:
    """
    Delete existing records with the same source S3 URI.
    
    Args:
        cursor: Database cursor
        s3_uri: S3 URI to delete records for
    """
    logger.info(f"Deleting existing records for {s3_uri}")
    
    try:
        # Delete query
        delete_query = """
        DELETE FROM vector_store 
        WHERE source_s3_uri = %s
        """
        
        cursor.execute(delete_query, (s3_uri,))
        deleted_count = cursor.rowcount
        
        logger.info(f"Deleted {deleted_count} existing records for {s3_uri}")
        
    except Exception as e:
        logger.error(f"Error deleting existing records: {str(e)}")
        raise


def insert_document_chunks(cursor, s3_uri: str, chunks: List[str], metadata: Dict[str, Any],
                          embeddings_data: Dict[str, Any], user_claims: Dict[str, Any]) -> None:
    """
    Insert document chunks and embeddings using batch operations.
    
    Args:
        cursor: Database cursor
        s3_uri: Source S3 URI
        chunks: Document text chunks
        metadata: Document metadata
        embeddings_data: All generated embeddings
        user_claims: JWT user claims
    """
    logger.info(f"Inserting {len(chunks)} document chunks")
    
    try:
        # Prepare insert query
        insert_query = """
        INSERT INTO vector_store (
            id,
            document,
            embedding_document,
            metadata,
            embedding_metadata,
            category,
            embedding_category,
            industry,
            embedding_industry,
            source_s3_uri,
            created_at,
            updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        # Prepare batch data
        batch_data = []
        current_time = datetime.utcnow()
        
        # Get embeddings
        document_embeddings = embeddings_data['document_embeddings']
        metadata_embedding = embeddings_data['metadata_embedding']
        category_embedding = embeddings_data['category_embedding']
        industry_embedding = embeddings_data['industry_embedding']
        
        # Prepare category as string
        category_str = ', '.join(metadata['category']) if isinstance(metadata['category'], list) else str(metadata['category'])
        
        for i, chunk in enumerate(chunks):
            # Generate unique ID for this chunk
            chunk_id = str(uuid.uuid4())
            
            # Get corresponding document embedding
            doc_embedding = document_embeddings[i]
            
            # Prepare row data
            row_data = (
                chunk_id,                           # id
                chunk,                              # document
                doc_embedding,                      # embedding_document
                json.dumps(metadata),               # metadata (JSONB)
                metadata_embedding,                 # embedding_metadata
                category_str,                       # category
                category_embedding,                 # embedding_category
                metadata['industry'],               # industry
                industry_embedding,                 # embedding_industry
                s3_uri,                            # source_s3_uri
                current_time,                      # created_at
                current_time                       # updated_at
            )
            
            batch_data.append(row_data)
        
        # Execute batch insert
        cursor.executemany(insert_query, batch_data)
        
        logger.info(f"Successfully inserted {len(batch_data)} chunks into database")
        
    except Exception as e:
        logger.error(f"Error inserting document chunks: {str(e)}")
        raise


def create_connection_pool():
    """
    Create a connection pool for better performance (for future enhancement).
    This is a placeholder for connection pooling implementation.
    """
    # Connection pooling would be implemented here for production use
    # For Lambda functions, simple connections are often sufficient
    # due to the stateless nature and AWS RDS Proxy availability
    pass


def validate_embedding_dimensions(embedding: List[float], expected_dims: int) -> None:
    """
    Validate that embedding has the expected number of dimensions.
    
    Args:
        embedding: Embedding vector to validate
        expected_dims: Expected number of dimensions
        
    Raises:
        ValueError: If dimensions don't match
    """
    if len(embedding) != expected_dims:
        raise ValueError(f"Expected {expected_dims} dimensions, got {len(embedding)}")


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


def test_database_connection() -> bool:
    """
    Test database connectivity and basic operations.
    
    Returns:
        True if connection test passes
    """
    try:
        conn = get_database_connection()
        
        with conn.cursor() as cursor:
            # Test basic query
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            
            if result and result['test'] == 1:
                logger.info("Database connection test passed")
                return True
            else:
                logger.error("Database connection test failed: unexpected result")
                return False
                
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


# Update requirements.txt to include necessary dependencies
def update_requirements():
    """
    This function documents the required dependencies for the ingestion Lambda.
    The actual requirements.txt file should include:
    
    boto3==1.34.0
    botocore==1.34.0
    psycopg2-binary==2.9.7
    tiktoken==0.5.1
    """
    pass