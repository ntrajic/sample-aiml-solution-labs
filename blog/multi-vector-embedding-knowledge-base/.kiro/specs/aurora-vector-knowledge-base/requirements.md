# Requirements Document

## Introduction

This document specifies the requirements for a custom knowledge base system built on Amazon RDS Aurora PostgreSQL with pgvector extension. The system will provide vector storage capabilities with multiple embedding types, document ingestion, retrieval functionality, and secure access through JWT authentication via Amazon Cognito.

## Glossary

- **Vector_Store_System**: The complete knowledge base system including database, Lambda functions, and authentication
- **Aurora_Database**: Amazon RDS Aurora PostgreSQL instance with pgvector extension
- **Sync_Lambda**: AWS Lambda function that lists files in S3 and queues them for ingestion
- **Ingestion_Lambda**: AWS Lambda function responsible for processing and storing documents with embeddings using Amazon Titan Text Embedding v2
- **Retrieval_Lambda**: AWS Lambda function that handles vector similarity searches and document retrieval
- **Ingestion_Queue**: Amazon SQS queue that triggers ingestion processing with concurrency control
- **Titan_Embedding_Model**: Amazon Titan Text Embedding v2 model used for generating all vector embeddings
- **Custom_Resource_Lambda**: AWS Lambda function that initializes the database schema and indexes during deployment
- **AgentCore_Gateway**: Amazon Bedrock AgentCore Gateway service that exposes the retrieval functionality as MCP
- **Cognito_Auth**: Amazon Cognito service providing JWT-based authentication
- **Secrets_Manager**: AWS Secrets Manager service for storing Cognito client secrets securely
- **Strands_Agent**: Example Strands Agents implementation that uses the multi-vector knowledge base for answering user queries
- **CDK_Stack**: AWS Cloud Development Kit infrastructure as code implementation

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want to deploy a vector database infrastructure, so that I can store and manage document embeddings at scale.

#### Acceptance Criteria

1. THE Aurora_Database SHALL be provisioned with PostgreSQL engine and pgvector extension enabled
2. THE Custom_Resource_Lambda SHALL create a vector_store table with the specified schema including source_s3_uri column during stack deployment
3. THE Custom_Resource_Lambda SHALL create appropriate indexes for vector similarity searches on all embedding columns
4. THE CDK_Stack SHALL configure Aurora_Database with appropriate security groups and subnet configurations
5. THE Aurora_Database SHALL support concurrent connections from multiple Lambda functions

### Requirement 2

**User Story:** As a data engineer, I want to ingest documents from S3 with automatic metadata extraction and multiple embedding types, so that I can enable multi-modal search capabilities.

#### Acceptance Criteria

1. THE Ingestion_Lambda SHALL accept S3 document location as input parameter
2. THE Ingestion_Lambda SHALL read document contents from the specified S3 location
3. THE Ingestion_Lambda SHALL derive metadata including provider (company name), category (list of main topics), and type (content type like news, announcement, technical doc, blog)
4. THE Ingestion_Lambda SHALL split document content into chunks with maximum 500 tokens and 10% overlap between chunks
5. THE Ingestion_Lambda SHALL use Titan_Embedding_Model to generate embeddings for each document chunk (1024 dimensions)
6. THE Ingestion_Lambda SHALL use Titan_Embedding_Model to generate embeddings for individual metadata fields (512 dimensions each)
7. THE Ingestion_Lambda SHALL use Titan_Embedding_Model to generate embeddings for provider information (256 dimensions)
8. THE Ingestion_Lambda SHALL use Titan_Embedding_Model to generate embeddings for category information (256 dimensions)
9. THE Ingestion_Lambda SHALL use Titan_Embedding_Model to generate embeddings for type information (256 dimensions)
10. THE Ingestion_Lambda SHALL create consolidated metadata in JSON format and generate embeddings for it (512 dimensions)
11. THE Ingestion_Lambda SHALL delete existing records with the same source S3 URI before inserting new data
12. THE Ingestion_Lambda SHALL store all chunks and embeddings including source_s3_uri in the vector_store table
13. WHEN ingestion fails, THE Ingestion_Lambda SHALL return appropriate error messages with details

### Requirement 3

**User Story:** As a data engineer, I want to synchronize entire S3 directories to the knowledge base, so that I can efficiently process large document collections.

#### Acceptance Criteria

1. THE Sync_Lambda SHALL accept S3 bucket and prefix parameters as input
2. THE Sync_Lambda SHALL list all files in the specified S3 location
3. THE Sync_Lambda SHALL send S3 file locations as messages to the Ingestion_Queue
4. THE Ingestion_Queue SHALL trigger Ingestion_Lambda with maximum 10 concurrent executions
5. THE Ingestion_Lambda SHALL process SQS messages containing S3 file locations
6. WHEN synchronization completes, THE Sync_Lambda SHALL return summary statistics of queued files
7. THE Ingestion_Queue SHALL implement dead letter queue for failed ingestion attempts

### Requirement 4

**User Story:** As an application developer, I want to retrieve relevant documents through vector similarity search, so that I can build intelligent applications.

#### Acceptance Criteria

1. THE Retrieval_Lambda SHALL accept query parameters including search text and similarity thresholds
2. THE Retrieval_Lambda SHALL perform vector similarity searches across specified embedding types
3. THE Retrieval_Lambda SHALL return ranked results based on cosine similarity scores
4. THE Retrieval_Lambda SHALL support filtering by provider, category, and type fields
5. THE Retrieval_Lambda SHALL limit result sets to configurable maximum counts
6. THE AgentCore_Gateway SHALL expose Retrieval_Lambda functionality as MCP endpoints
7. WHEN no results meet the similarity threshold, THE Retrieval_Lambda SHALL return an empty result set

### Requirement 5

**User Story:** As a security administrator, I want to secure access to the knowledge base, so that only authorized users can access the system.

#### Acceptance Criteria

1. THE Cognito_Auth SHALL provide JWT token generation for authenticated users
2. THE Secrets_Manager SHALL store Cognito client secrets securely
3. THE Retrieval_Lambda SHALL validate JWT tokens before processing requests
4. THE Ingestion_Lambda SHALL validate JWT tokens before processing requests
5. THE Sync_Lambda SHALL validate JWT tokens before processing requests
6. WHEN JWT validation fails, THE Vector_Store_System SHALL return HTTP 401 Unauthorized
7. THE AgentCore_Gateway SHALL pass JWT tokens to the Retrieval_Lambda for validation

### Requirement 6

**User Story:** As a DevOps engineer, I want to deploy the entire system through infrastructure as code, so that I can ensure consistent and repeatable deployments.

#### Acceptance Criteria

1. THE CDK_Stack SHALL define all AWS resources including Aurora_Database, Lambda functions, Cognito_Auth, Secrets_Manager, and Ingestion_Queue
2. THE CDK_Stack SHALL configure proper IAM roles and policies for all components
3. THE CDK_Stack SHALL set up VPC networking with appropriate security groups
4. THE Custom_Resource_Lambda SHALL execute database initialization only during initial deployment
5. THE CDK_Stack SHALL configure SQS concurrency limits for Ingestion_Lambda
6. THE CDK_Stack SHALL output necessary connection strings and endpoint URLs for integration

### Requirement 7

**User Story:** As a developer, I want an example Strands Agent implementation, so that I can understand how to integrate with the multi-vector knowledge base.

#### Acceptance Criteria

1. THE Strands_Agent SHALL demonstrate integration with the Retrieval_Lambda through AgentCore_Gateway
2. THE Strands_Agent SHALL accept user queries and retrieve relevant documents from the knowledge base
3. THE Strands_Agent SHALL use multiple embedding types for comprehensive search results
4. THE Strands_Agent SHALL provide contextual responses based on retrieved document content
5. THE Strands_Agent SHALL handle authentication through Cognito_Auth integration