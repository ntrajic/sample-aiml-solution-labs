"""
S3 Bucket Construct for Knowledge Base Document Storage

This construct creates an S3 bucket optimized for storing knowledge base documents
with proper lifecycle policies, versioning, and access controls.
"""

from constructs import Construct
from aws_cdk import (
    aws_s3 as s3,
    aws_iam as iam,
    CfnOutput,
    RemovalPolicy,
    Duration,
    Tags
)


class S3KnowledgeBaseConstruct(Construct):
    """
    S3 bucket construct for knowledge base document storage.
    
    Creates:
    - S3 bucket with versioning and lifecycle policies
    - Bucket policies for secure access
    - CloudFormation outputs for bucket information
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create the S3 bucket for knowledge base documents
        self._create_knowledge_base_bucket()
        
        # Create bucket policies
        self._create_bucket_policies()
        
        # Create outputs
        self._create_outputs()

    def _create_knowledge_base_bucket(self) -> None:
        """Create S3 bucket for knowledge base document storage."""
        
        self.knowledge_base_bucket = s3.Bucket(
            self,
            "KnowledgeBaseBucket",
            bucket_name=None,  # Let CDK generate unique name
            versioned=True,
            
            # Lifecycle configuration
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="knowledge-base-lifecycle",
                    enabled=True,
                    
                    # Transition to IA after 30 days
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        )
                    ],
                    
                    # Delete old versions after 90 days
                    noncurrent_version_expiration=Duration.days(90),
                    
                    # Clean up incomplete multipart uploads
                    abort_incomplete_multipart_upload_after=Duration.days(7)
                )
            ],
            
            # Security configuration
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            
            # CORS configuration for web uploads (if needed)
            cors=[
                s3.CorsRule(
                    allowed_methods=[
                        s3.HttpMethods.GET,
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.POST
                    ],
                    allowed_origins=["*"],  # Restrict in production
                    allowed_headers=["*"],
                    max_age=3000
                )
            ],
            
            # Notification configuration (can be extended for real-time processing)
            # event_bridge_enabled=True,
            
            # Removal policy for development
            removal_policy=RemovalPolicy.DESTROY,  # Change to RETAIN for production
            auto_delete_objects=True  # Only for development
        )
        
        # Add tags
        Tags.of(self.knowledge_base_bucket).add("Name", "aurora-vector-kb-documents")
        Tags.of(self.knowledge_base_bucket).add("Component", "Storage")
        Tags.of(self.knowledge_base_bucket).add("Purpose", "KnowledgeBase")

    def _create_bucket_policies(self) -> None:
        """Create IAM policies for bucket access."""
        
        # Policy for Lambda functions to access the bucket
        self.lambda_access_policy = iam.PolicyDocument(
            statements=[
                # Read access for ingestion Lambda
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:GetObject",
                        "s3:GetObjectVersion",
                        "s3:GetObjectMetadata"
                    ],
                    resources=[
                        f"{self.knowledge_base_bucket.bucket_arn}/*"
                    ]
                ),
                
                # List access for sync Lambda
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:ListBucket",
                        "s3:ListBucketVersions",
                        "s3:GetBucketLocation"
                    ],
                    resources=[
                        self.knowledge_base_bucket.bucket_arn
                    ]
                ),
                
                # Write access for document uploads (optional)
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:PutObject",
                        "s3:PutObjectAcl",
                        "s3:DeleteObject"
                    ],
                    resources=[
                        f"{self.knowledge_base_bucket.bucket_arn}/*"
                    ]
                )
            ]
        )
        
        # Create managed policy for easy attachment
        self.lambda_managed_policy = iam.ManagedPolicy(
            self,
            "KnowledgeBaseBucketAccessPolicy",
            managed_policy_name="AuroraVectorKB-S3Access",
            description="Policy for Lambda functions to access knowledge base S3 bucket",
            document=self.lambda_access_policy
        )

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs for bucket information."""
        
        CfnOutput(
            self,
            "KnowledgeBaseBucketName",
            value=self.knowledge_base_bucket.bucket_name,
            description="Name of the S3 bucket for knowledge base documents",
            export_name=f"{self.node.scope.stack_name}-KnowledgeBaseBucketName"
        )
        
        CfnOutput(
            self,
            "KnowledgeBaseBucketArn",
            value=self.knowledge_base_bucket.bucket_arn,
            description="ARN of the S3 bucket for knowledge base documents",
            export_name=f"{self.node.scope.stack_name}-KnowledgeBaseBucketArn"
        )
        
        CfnOutput(
            self,
            "KnowledgeBaseBucketDomainName",
            value=self.knowledge_base_bucket.bucket_domain_name,
            description="Domain name of the S3 bucket for knowledge base documents"
        )
        
        CfnOutput(
            self,
            "KnowledgeBaseBucketRegionalDomainName",
            value=self.knowledge_base_bucket.bucket_regional_domain_name,
            description="Regional domain name of the S3 bucket"
        )

    def get_bucket(self) -> s3.Bucket:
        """Return the S3 bucket instance."""
        return self.knowledge_base_bucket

    def get_bucket_name(self) -> str:
        """Return the S3 bucket name."""
        return self.knowledge_base_bucket.bucket_name

    def get_bucket_arn(self) -> str:
        """Return the S3 bucket ARN."""
        return self.knowledge_base_bucket.bucket_arn

    def get_lambda_access_policy(self) -> iam.ManagedPolicy:
        """Return the managed policy for Lambda access."""
        return self.lambda_managed_policy

    def grant_read_access(self, grantee: iam.IGrantable) -> iam.Grant:
        """
        Grant read access to the knowledge base bucket.
        
        Args:
            grantee: The IAM principal to grant access to
            
        Returns:
            Grant object representing the permission
        """
        return self.knowledge_base_bucket.grant_read(grantee)

    def grant_read_write_access(self, grantee: iam.IGrantable) -> iam.Grant:
        """
        Grant read/write access to the knowledge base bucket.
        
        Args:
            grantee: The IAM principal to grant access to
            
        Returns:
            Grant object representing the permission
        """
        return self.knowledge_base_bucket.grant_read_write(grantee)