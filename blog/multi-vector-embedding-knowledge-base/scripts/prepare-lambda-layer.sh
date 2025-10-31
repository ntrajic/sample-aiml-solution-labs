#!/bin/bash
#
# Lambda Layer Preparation Script
#
# This script prepares the Lambda layer dependencies for the Aurora Vector Knowledge Base.
# It installs the required Python packages for PostgreSQL connectivity and other dependencies
# needed by the Lambda functions.
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "app.py" ] || [ ! -d "aurora_vector_kb" ]; then
    print_error "This script must be run from the project root directory"
    print_error "Please run: cd /path/to/multi-vector-embedding-knowledge-base && ./scripts/prepare-lambda-layer.sh"
    exit 1
fi

print_status "Preparing Lambda layer dependencies for Aurora Vector Knowledge Base..."

# Create the layers directory structure
LAYER_DIR="aurora_vector_kb/layers/postgresql"
PYTHON_DIR="$LAYER_DIR/python"

print_status "Creating layer directory structure..."
mkdir -p "$PYTHON_DIR"

# Check if requirements.txt exists
REQUIREMENTS_FILE="$LAYER_DIR/requirements.txt"
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    print_status "Creating requirements.txt for Lambda layer..."
    cat > "$REQUIREMENTS_FILE" << EOF
psycopg2-binary==2.9.7
tiktoken==0.5.1
boto3==1.34.0
botocore==1.34.0
EOF
    print_success "Created $REQUIREMENTS_FILE"
fi

# Check if dependencies are already installed
if [ -d "$PYTHON_DIR/psycopg2" ] && [ -d "$PYTHON_DIR/tiktoken" ]; then
    print_warning "Dependencies appear to already be installed in $PYTHON_DIR"
    read -p "Do you want to reinstall them? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Skipping installation. Using existing dependencies."
        exit 0
    fi
    print_status "Removing existing dependencies..."
    rm -rf "$PYTHON_DIR"
    mkdir -p "$PYTHON_DIR"
fi

# Check if pip3 is available
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed or not in PATH"
    print_error "Please install Python 3 and pip3 first"
    exit 1
fi

print_status "Installing Lambda layer dependencies..."
print_status "This may take a few minutes..."

# Install dependencies for Lambda layer
pip3 install \
    --quiet \
    --platform manylinux2014_x86_64 \
    --target "$PYTHON_DIR" \
    --python-version 3.11 \
    --only-binary=:all: \
    -r "$REQUIREMENTS_FILE"

# Check if installation was successful
if [ $? -eq 0 ] && [ -d "$PYTHON_DIR/psycopg2" ]; then
    print_success "Lambda layer dependencies installed successfully!"
    
    # Show what was installed
    print_status "Installed packages:"
    ls -la "$PYTHON_DIR" | grep -E "^d" | awk '{print "  - " $9}' | grep -v "^\s*-\s*$"
    
    # Show directory size
    LAYER_SIZE=$(du -sh "$PYTHON_DIR" | cut -f1)
    print_status "Layer size: $LAYER_SIZE"
    
    print_success "Lambda layer preparation complete!"
    print_status "You can now run 'cdk deploy' to deploy the stack."
    
else
    print_error "Failed to install Lambda layer dependencies"
    print_error "Please check the error messages above and try again"
    exit 1
fi