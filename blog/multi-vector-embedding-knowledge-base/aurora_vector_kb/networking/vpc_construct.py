"""
VPC Construct for Aurora Vector Knowledge Base

This construct creates a VPC with public and private subnets across multiple AZs,
NAT Gateways for Lambda internet access, and VPC endpoints for AWS services.
"""

from typing import List
from constructs import Construct
from aws_cdk import (
    aws_ec2 as ec2,
    CfnOutput,
    Tags
)


class VpcConstruct(Construct):
    """
    VPC construct that creates networking infrastructure for the vector knowledge base.
    
    Creates:
    - VPC with public and private subnets across 2+ AZs
    - NAT Gateways in public subnets for Lambda internet access
    - VPC endpoints for AWS services (S3, SQS, Secrets Manager, etc.)
    - Route tables and internet gateway
    """

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        # Create VPC with public and private subnets across multiple AZs
        self.vpc = ec2.Vpc(
            self,
            "AuroraVectorKbVpc",
            vpc_name="aurora-vector-kb-vpc",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=3,  # Use up to 3 AZs for high availability
            nat_gateways=2,  # NAT Gateways in 2 AZs for redundancy
            subnet_configuration=[
                # Public subnets for NAT Gateways and load balancers
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,  # /24 gives 256 IPs per subnet
                ),
                # Private subnets for Lambda functions
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=22,  # /22 gives 1024 IPs per subnet
                ),
                # Isolated subnets for Aurora database
                ec2.SubnetConfiguration(
                    name="Database",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,  # /24 gives 256 IPs per subnet
                ),
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True,
        )

        # Create VPC endpoints for AWS services to reduce NAT Gateway costs
        # and improve security by keeping traffic within AWS network
        self._create_vpc_endpoints()

        # Add tags to VPC and subnets
        Tags.of(self.vpc).add("Name", "aurora-vector-kb-vpc")
        Tags.of(self.vpc).add("Purpose", "VectorKnowledgeBase")

        # Store subnet references for easy access
        self.public_subnets = self.vpc.public_subnets
        self.private_subnets = self.vpc.private_subnets
        self.database_subnets = self.vpc.isolated_subnets

        # Create outputs for VPC information
        CfnOutput(
            scope,
            "VpcId",
            value=self.vpc.vpc_id,
            description="ID of the VPC"
        )

        CfnOutput(
            scope,
            "VpcCidr",
            value=self.vpc.vpc_cidr_block,
            description="CIDR block of the VPC"
        )

        CfnOutput(
            scope,
            "PrivateSubnetIds",
            value=",".join([subnet.subnet_id for subnet in self.private_subnets]),
            description="IDs of private subnets for Lambda functions"
        )

        CfnOutput(
            scope,
            "DatabaseSubnetIds",
            value=",".join([subnet.subnet_id for subnet in self.database_subnets]),
            description="IDs of database subnets for Aurora cluster"
        )

    def _create_vpc_endpoints(self) -> None:
        """
        Create VPC endpoints for AWS services to reduce NAT Gateway usage
        and improve security by keeping traffic within AWS network.
        """
        
        # S3 Gateway endpoint (no additional charges)
        self.vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
            subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)]
        )

        # Interface endpoints for other AWS services
        # These reduce NAT Gateway usage and improve security
        
        # Secrets Manager endpoint for Cognito secrets
        self.secrets_manager_endpoint = ec2.InterfaceVpcEndpoint(
            self,
            "SecretsManagerEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            private_dns_enabled=True
        )

        # SQS endpoint for message queuing
        self.sqs_endpoint = ec2.InterfaceVpcEndpoint(
            self,
            "SqsEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.SQS,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            private_dns_enabled=True
        )

        # Lambda endpoint for function invocations
        self.lambda_endpoint = ec2.InterfaceVpcEndpoint(
            self,
            "LambdaEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.LAMBDA_,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            private_dns_enabled=True
        )

        # CloudWatch Logs endpoint for Lambda logging
        self.cloudwatch_logs_endpoint = ec2.InterfaceVpcEndpoint(
            self,
            "CloudWatchLogsEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            private_dns_enabled=True
        )

    def get_vpc(self) -> ec2.Vpc:
        """Return the VPC instance."""
        return self.vpc

    def get_private_subnets(self) -> List[ec2.ISubnet]:
        """Return private subnets for Lambda functions."""
        return self.private_subnets

    def get_database_subnets(self) -> List[ec2.ISubnet]:
        """Return isolated subnets for Aurora database."""
        return self.database_subnets

    def get_public_subnets(self) -> List[ec2.ISubnet]:
        """Return public subnets."""
        return self.public_subnets