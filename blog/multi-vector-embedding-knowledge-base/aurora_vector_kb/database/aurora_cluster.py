"""
Aurora PostgreSQL Cluster Construct

This construct creates an Aurora PostgreSQL cluster with pgvector extension
configured for vector operations, including proper parameter groups,
subnet groups, and credentials management.
"""

from typing import List
from constructs import Construct
from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_secretsmanager as secretsmanager,
    CfnOutput,
    RemovalPolicy,
    Duration,
    Tags
)
from .database_initializer import DatabaseInitializerConstruct


class AuroraClusterConstruct(Construct):
    """
    Aurora PostgreSQL cluster construct optimized for vector operations.
    
    Creates:
    - Aurora PostgreSQL cluster with pgvector extension support
    - Database parameter group optimized for vector operations
    - Subnet group for database placement
    - Master credentials stored in Secrets Manager
    - Appropriate security group configuration
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        database_subnets: List[ec2.ISubnet],
        private_subnets: List[ec2.ISubnet],
        security_group: ec2.SecurityGroup,
        lambda_security_group: ec2.SecurityGroup,
        postgresql_layer,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = vpc
        self.database_subnets = database_subnets
        self.private_subnets = private_subnets
        self.security_group = security_group
        self.lambda_security_group = lambda_security_group
        self.postgresql_layer = postgresql_layer

        # Create database credentials in Secrets Manager
        self._create_database_credentials()
        
        # Create parameter group for pgvector optimization
        self._create_parameter_group()
        
        # Create subnet group for Aurora cluster
        self._create_subnet_group()
        
        # Create Aurora PostgreSQL cluster
        self._create_aurora_cluster()
        
        # Create database initializer
        self._create_database_initializer()
        
        # Create outputs
        self._create_outputs(scope)

    def _create_database_credentials(self) -> None:
        """Create database master credentials in Secrets Manager."""
        self.database_credentials = secretsmanager.Secret(
            self,
            "DatabaseCredentials",
            secret_name="aurora-vector-kb/database-credentials",
            description="Master credentials for Aurora Vector Knowledge Base cluster",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "postgres"}',
                generate_string_key="password",
                exclude_characters=' %+~`#$&*()|[]{}:;<>?!\'/@"\\',
                password_length=32,
                include_space=False
            ),
            removal_policy=RemovalPolicy.DESTROY  # For development - change for production
        )
        
        Tags.of(self.database_credentials).add("Name", "aurora-vector-kb-credentials")
        Tags.of(self.database_credentials).add("Component", "Database")

    def _create_parameter_group(self) -> None:
        """Create parameter group optimized for pgvector operations."""
        self.parameter_group = rds.ParameterGroup(
            self,
            "AuroraParameterGroup",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_13
            ),
            description="Parameter group for Aurora Vector Knowledge Base with pgvector optimization",
            parameters={
                # Basic optimizations for vector operations (Aurora-compatible)
                "work_mem": "32768",  # 32MB in KB
                "maintenance_work_mem": "65536",  # 64MB in KB
                "default_statistics_target": "100",
                "random_page_cost": "1.1",
                
                # Logging for monitoring
                "log_statement": "mod",
                "log_min_duration_statement": "1000",  # Log slow queries (1 second+)
                "log_connections": "on",
                "log_disconnections": "on",
                "log_lock_waits": "on"
            }
        )
        
        Tags.of(self.parameter_group).add("Name", "aurora-vector-kb-params")
        Tags.of(self.parameter_group).add("Component", "Database")

    def _create_subnet_group(self) -> None:
        """Create subnet group for Aurora cluster placement."""
        self.subnet_group = rds.SubnetGroup(
            self,
            "AuroraSubnetGroup",
            description="Subnet group for Aurora Vector Knowledge Base cluster",
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=self.database_subnets),
            removal_policy=RemovalPolicy.DESTROY
        )
        
        Tags.of(self.subnet_group).add("Name", "aurora-vector-kb-subnet-group")
        Tags.of(self.subnet_group).add("Component", "Database")

    def _create_aurora_cluster(self) -> None:
        """Create Aurora PostgreSQL Serverless v2 cluster with pgvector support."""
        
        # Define the Aurora PostgreSQL engine with pgvector support
        engine = rds.DatabaseClusterEngine.aurora_postgres(
            version=rds.AuroraPostgresEngineVersion.VER_15_13
        )
        
        # Create the Aurora Serverless v2 cluster
        self.cluster = rds.DatabaseCluster(
            self,
            "AuroraCluster",
            cluster_identifier="aurora-vector-kb-cluster",
            engine=engine,
            credentials=rds.Credentials.from_secret(self.database_credentials),
            parameter_group=self.parameter_group,
            subnet_group=self.subnet_group,
            security_groups=[self.security_group],
            
            # Serverless v2 configuration
            writer=rds.ClusterInstance.serverless_v2(
                "Writer",
                publicly_accessible=False,
                auto_minor_version_upgrade=True,
                enable_performance_insights=True,
                performance_insight_retention=rds.PerformanceInsightRetention.DEFAULT
            ),
            
            readers=[
                rds.ClusterInstance.serverless_v2(
                    "Reader1",
                    publicly_accessible=False,
                    auto_minor_version_upgrade=True,
                    enable_performance_insights=True,
                    performance_insight_retention=rds.PerformanceInsightRetention.DEFAULT
                )
            ],
            
            # Serverless v2 scaling configuration
            serverless_v2_min_capacity=0.5,  # Minimum 0.5 ACU for cost efficiency
            serverless_v2_max_capacity=16,   # Maximum 16 ACU for peak performance
            
            # Backup and maintenance configuration
            backup=rds.BackupProps(
                retention=Duration.days(7),
                preferred_window="03:00-04:00"  # UTC
            ),
            preferred_maintenance_window="sun:04:00-sun:05:00",  # UTC
            
            # Monitoring and logging
            monitoring_interval=Duration.seconds(60),
            cloudwatch_logs_exports=["postgresql"],
            
            # Security and networking
            vpc=self.vpc,
            port=5432,
            
            # Deletion protection and removal policy
            deletion_protection=False,  # Set to True for production
            removal_policy=RemovalPolicy.DESTROY,  # Change for production
            
            # Storage configuration
            storage_encrypted=True,
            
            # Data API configuration (enables AWS Console query editor)
            enable_data_api=True,
            
            # Default database name
            default_database_name="vector_kb"
        )
        
        Tags.of(self.cluster).add("Name", "aurora-vector-kb-cluster")
        Tags.of(self.cluster).add("Component", "Database")
        Tags.of(self.cluster).add("Engine", "PostgreSQL")
        Tags.of(self.cluster).add("Extension", "pgvector")
        Tags.of(self.cluster).add("Deployment", "Serverless-v2")



    def _create_database_initializer(self) -> None:
        """Create database initializer Lambda for schema setup."""
        self.database_initializer = DatabaseInitializerConstruct(
            self,
            "DatabaseInitializer",
            vpc=self.vpc,
            lambda_subnets=self.private_subnets,
            lambda_security_group=self.lambda_security_group,
            aurora_cluster=self.cluster,
            database_credentials_secret=self.database_credentials,
            postgresql_layer=self.postgresql_layer
        )

    def _create_outputs(self, scope: Construct) -> None:
        """Create CloudFormation outputs for cluster information."""
        CfnOutput(
            scope,
            "AuroraClusterIdentifier",
            value=self.cluster.cluster_identifier,
            description="Aurora cluster identifier"
        )
        
        CfnOutput(
            scope,
            "AuroraClusterEndpoint",
            value=self.cluster.cluster_endpoint.hostname,
            description="Aurora cluster writer endpoint"
        )
        
        CfnOutput(
            scope,
            "AuroraClusterReadEndpoint",
            value=self.cluster.cluster_read_endpoint.hostname,
            description="Aurora cluster reader endpoint"
        )
        
        CfnOutput(
            scope,
            "AuroraClusterPort",
            value=str(self.cluster.cluster_endpoint.port),
            description="Aurora cluster port"
        )
        
        CfnOutput(
            scope,
            "DatabaseCredentialsSecretArn",
            value=self.database_credentials.secret_arn,
            description="ARN of the database credentials secret"
        )
        
        CfnOutput(
            scope,
            "DatabaseCredentialsSecretName",
            value=self.database_credentials.secret_name,
            description="Name of the database credentials secret"
        )
        
        CfnOutput(
            scope,
            "DatabaseName",
            value="vector_kb",
            description="Default database name"
        )
        
        CfnOutput(
            scope,
            "DataApiEnabled",
            value="True",
            description="Data API is enabled for AWS Console query editor access"
        )

    def get_cluster(self) -> rds.DatabaseCluster:
        """Return the Aurora cluster instance."""
        return self.cluster

    def get_credentials_secret(self) -> secretsmanager.Secret:
        """Return the database credentials secret."""
        return self.database_credentials

    def get_cluster_endpoint(self) -> rds.Endpoint:
        """Return the cluster writer endpoint."""
        return self.cluster.cluster_endpoint

    def get_cluster_read_endpoint(self) -> rds.Endpoint:
        """Return the cluster reader endpoint."""
        return self.cluster.cluster_read_endpoint