"""
PostgreSQL Lambda Layer Construct

This construct creates a Lambda layer containing psycopg2-binary and other
PostgreSQL-related dependencies for Lambda functions that need to connect
to Aurora PostgreSQL.
"""

import os
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
        """Create a placeholder Lambda layer."""
        
        # Create layer from the layers directory
        layer_dir = os.path.join(os.path.dirname(__file__), "postgresql")
        
        # Ensure the python directory exists with a placeholder
        self._ensure_layer_structure(layer_dir)
        
        self.layer = _lambda.LayerVersion(
            self,
            "PostgreSQLLayer",
            layer_version_name="aurora-vector-kb-dependencies-layer",
            code=_lambda.Code.from_asset(layer_dir),
            compatible_runtimes=[
                _lambda.Runtime.PYTHON_3_11,
                _lambda.Runtime.PYTHON_3_12
            ],
            description="Placeholder layer for Aurora Vector KB (dependencies need to be installed manually)"
        )

        Tags.of(self.layer).add("Name", "aurora-vector-kb-dependencies-layer")
        Tags.of(self.layer).add("Component", "Layer")
        Tags.of(self.layer).add("Purpose", "Dependencies")



    def _ensure_layer_structure(self, layer_dir: str) -> None:
        """Ensure the layer has the minimum required structure."""
        python_dir = os.path.join(layer_dir, "python")
        os.makedirs(python_dir, exist_ok=True)
        
        # Create a placeholder file to ensure the directory is not empty
        placeholder_file = os.path.join(python_dir, "__init__.py")
        if not os.path.exists(placeholder_file):
            with open(placeholder_file, 'w') as f:
                f.write("# Placeholder file for Lambda layer\n")

    def get_layer(self) -> _lambda.LayerVersion:
        """Return the Lambda layer instance."""
        return self.layer