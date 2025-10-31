"""
PostgreSQL Lambda Layer Construct

This construct creates a Lambda layer containing psycopg2-binary and other
PostgreSQL-related dependencies for Lambda functions that need to connect
to Aurora PostgreSQL.
"""

import os
import subprocess
import tempfile
from constructs import Construct
from aws_cdk import (
    aws_lambda as _lambda,
    BundlingOptions,
    Tags
)


class DependenciesLayerConstruct(Construct):
    """
    Construct for creating a Lambda layer with all required dependencies.
    
    Creates a layer containing:
    - psycopg2-binary (PostgreSQL connectivity)
    - tiktoken (document tokenization)
    - boto3/botocore (AWS SDK)
    - Other required dependencies
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create the Lambda layer
        self._create_layer()

    def _create_layer(self) -> None:
        """Create the Lambda layer with all required dependencies."""
        
        # Create layer from the layers directory
        layer_dir = os.path.join(os.path.dirname(__file__), "postgresql")
        
        # Create the python directory and install dependencies locally
        self._prepare_layer_assets(layer_dir)
        
        self.layer = _lambda.LayerVersion(
            self,
            "PostgreSQLLayer",
            layer_version_name="aurora-vector-kb-dependencies-layer",
            code=_lambda.Code.from_asset(layer_dir),
            compatible_runtimes=[
                _lambda.Runtime.PYTHON_3_11,
                _lambda.Runtime.PYTHON_3_12
            ],
            description="Dependencies layer with psycopg2-binary, tiktoken, boto3 for Aurora Vector KB"
        )

        Tags.of(self.layer).add("Name", "aurora-vector-kb-dependencies-layer")
        Tags.of(self.layer).add("Component", "Layer")
        Tags.of(self.layer).add("Purpose", "Dependencies")

    def _prepare_layer_assets(self, layer_dir: str) -> None:
        """Prepare layer assets by installing dependencies locally."""
        python_dir = os.path.join(layer_dir, "python")
        
        # Create python directory if it doesn't exist
        os.makedirs(python_dir, exist_ok=True)
        
        # Check if dependencies are already installed
        psycopg2_path = os.path.join(python_dir, "psycopg2")
        if not os.path.exists(psycopg2_path):
            print("Installing PostgreSQL dependencies for Lambda layer...")
            
            # Install dependencies using pip
            requirements_file = os.path.join(layer_dir, "requirements.txt")
            if os.path.exists(requirements_file):
                try:
                    subprocess.run([
                        "pip3", "install", 
                        "--quiet",
                        "--platform", "manylinux2014_x86_64",
                        "--target", python_dir,
                        "--python-version", "3.11",
                        "--only-binary=:all:",
                        "-r", requirements_file
                    ], check=True, capture_output=True, text=True)
                    print("PostgreSQL dependencies installed successfully")
                except subprocess.CalledProcessError as e:
                    print(f"Warning: Failed to install dependencies: {e}")
                    print("Layer will be created without pre-installed dependencies")

    def get_layer(self) -> _lambda.LayerVersion:
        """Return the Lambda layer instance."""
        return self.layer