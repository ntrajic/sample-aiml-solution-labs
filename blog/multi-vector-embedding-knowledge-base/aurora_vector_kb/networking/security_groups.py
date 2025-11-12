"""
Security Groups for Aurora Vector Knowledge Base

This module creates security groups for different components:
- Aurora PostgreSQL database cluster
- Lambda functions
- VPC endpoints
- Inter-service communication
"""

from constructs import Construct
from aws_cdk import (
    aws_ec2 as ec2,
    CfnOutput,
    Tags
)


class SecurityGroupsConstruct(Construct):
    """
    Security Groups construct that creates security groups for all components
    of the vector knowledge base system with least privilege access.
    """

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc) -> None:
        super().__init__(scope, construct_id)
        
        self.vpc = vpc
        
        # Create security groups for different components
        self._create_lambda_security_group()
        self._create_aurora_security_group()
        self._create_vpc_endpoint_security_group()
        
        # Configure security group rules
        self._configure_security_group_rules()
        
        # Create outputs
        self._create_outputs(scope)

    def _create_lambda_security_group(self) -> None:
        """Create security group for Lambda functions."""
        self.lambda_security_group = ec2.SecurityGroup(
            self,
            "LambdaSecurityGroup",
            vpc=self.vpc,
            description="Security group for Lambda functions in Aurora Vector KB",
            security_group_name="aurora-vector-kb-lambda-sg",
            allow_all_outbound=True  # Lambda needs outbound access for AWS services
        )
        
        Tags.of(self.lambda_security_group).add("Name", "aurora-vector-kb-lambda-sg")
        Tags.of(self.lambda_security_group).add("Component", "Lambda")

    def _create_aurora_security_group(self) -> None:
        """Create security group for Aurora PostgreSQL cluster."""
        self.aurora_security_group = ec2.SecurityGroup(
            self,
            "AuroraSecurityGroup",
            vpc=self.vpc,
            description="Security group for Aurora PostgreSQL cluster",
            security_group_name="aurora-vector-kb-aurora-sg",
            allow_all_outbound=False  # Database should not initiate outbound connections
        )
        
        Tags.of(self.aurora_security_group).add("Name", "aurora-vector-kb-aurora-sg")
        Tags.of(self.aurora_security_group).add("Component", "Aurora")

    def _create_vpc_endpoint_security_group(self) -> None:
        """Create security group for VPC endpoints."""
        self.vpc_endpoint_security_group = ec2.SecurityGroup(
            self,
            "VpcEndpointSecurityGroup",
            vpc=self.vpc,
            description="Security group for VPC endpoints",
            security_group_name="aurora-vector-kb-vpc-endpoint-sg",
            allow_all_outbound=False  # VPC endpoints don't need outbound access
        )
        
        Tags.of(self.vpc_endpoint_security_group).add("Name", "aurora-vector-kb-vpc-endpoint-sg")
        Tags.of(self.vpc_endpoint_security_group).add("Component", "VpcEndpoint")

    def _configure_security_group_rules(self) -> None:
        """Configure security group rules for inter-service communication."""
        
        # Aurora security group rules
        # Allow inbound PostgreSQL connections from Lambda functions
        self.aurora_security_group.add_ingress_rule(
            peer=self.lambda_security_group,
            connection=ec2.Port.tcp(5432),
            description="Allow PostgreSQL access from Lambda functions"
        )
        
        # Allow inbound connections from custom resource Lambda (for database initialization)
        self.aurora_security_group.add_ingress_rule(
            peer=self.lambda_security_group,
            connection=ec2.Port.tcp(5432),
            description="Allow database initialization from custom resource Lambda"
        )
        
        # VPC Endpoint security group rules
        # Allow HTTPS traffic from Lambda functions to VPC endpoints
        self.vpc_endpoint_security_group.add_ingress_rule(
            peer=self.lambda_security_group,
            connection=ec2.Port.tcp(443),
            description="Allow HTTPS access from Lambda to VPC endpoints"
        )
        
        # Lambda security group rules (outbound rules are already allowed by default)
        # Lambda functions need to access:
        # - Aurora database (handled by Aurora SG ingress rule)
        # - VPC endpoints (handled by VPC endpoint SG ingress rule)
        # - Internet via NAT Gateway (allowed by default outbound rule)
        # - Bedrock service (via internet/VPC endpoint)
        
        # Additional rule for Lambda to Lambda communication (if needed for custom resources)
        self.lambda_security_group.add_ingress_rule(
            peer=self.lambda_security_group,
            connection=ec2.Port.all_traffic(),
            description="Allow Lambda to Lambda communication"
        )

    def _create_outputs(self, scope: Construct) -> None:
        """Create CloudFormation outputs for security group IDs."""
        CfnOutput(
            scope,
            "LambdaSecurityGroupId",
            value=self.lambda_security_group.security_group_id,
            description="Security Group ID for Lambda functions"
        )
        
        CfnOutput(
            scope,
            "AuroraSecurityGroupId",
            value=self.aurora_security_group.security_group_id,
            description="Security Group ID for Aurora PostgreSQL cluster"
        )
        
        CfnOutput(
            scope,
            "VpcEndpointSecurityGroupId",
            value=self.vpc_endpoint_security_group.security_group_id,
            description="Security Group ID for VPC endpoints"
        )

    def get_lambda_security_group(self) -> ec2.SecurityGroup:
        """Return the Lambda security group."""
        return self.lambda_security_group

    def get_aurora_security_group(self) -> ec2.SecurityGroup:
        """Return the Aurora security group."""
        return self.aurora_security_group

    def get_vpc_endpoint_security_group(self) -> ec2.SecurityGroup:
        """Return the VPC endpoint security group."""
        return self.vpc_endpoint_security_group