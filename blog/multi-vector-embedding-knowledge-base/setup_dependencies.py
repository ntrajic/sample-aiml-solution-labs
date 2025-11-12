#!/usr/bin/env python3
"""
Setup script to install Lambda layer dependencies without Docker.

This script installs the required dependencies for the Aurora Vector KB
Lambda functions into a layer structure that can be deployed.
"""

import os
import subprocess
import sys
import shutil
import shlex
from pathlib import Path

def install_dependencies():
    """Install dependencies for the Lambda layer."""
    
    # Define paths
    layer_dir = Path("aurora_vector_kb/layers/postgresql")
    python_dir = layer_dir / "python"
    requirements_file = layer_dir / "requirements.txt"
    
    # Create directories
    python_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if requirements.txt exists
    if not requirements_file.exists():
        print(f"Error: {requirements_file} not found")
        return False
    
    print(f"Installing dependencies from {requirements_file}")
    print(f"Target directory: {python_dir}")
    
    try:
        # Validate paths to ensure they're safe
        if not requirements_file.exists():
            raise FileNotFoundError(f"Requirements file not found: {requirements_file}")
        
        if not python_dir.parent.exists():
            raise FileNotFoundError(f"Parent directory not found: {python_dir.parent}")
        
        # Install dependencies using pip with explicit list of arguments (not shell=True)
        # This prevents command injection as each argument is passed separately
        cmd = [
            sys.executable,           # Trusted: Python interpreter path
            "-m", "pip", "install",   # Hardcoded: pip module and command
            "--target", str(python_dir),  # Validated: local path
            "--platform", "manylinux2014_x86_64",  # Hardcoded: platform string
            "--python-version", "3.11",  # Hardcoded: version string
            "--only-binary=:all:",    # Hardcoded: binary flag
            "-r", str(requirements_file)  # Validated: local file path
        ]
        
        # Use shlex.quote for safe display (not for execution)
        safe_cmd_display = ' '.join(shlex.quote(arg) for arg in cmd)
        print(f"Running: {safe_cmd_display}")
        
        # Execute with shell=False (default) for security
        result = subprocess.run( # pylint: disable=dangerous-subprocess-use-audit
            cmd, 
            check=True, 
            capture_output=True, 
            text=True,
            shell=False  # Explicit: prevents shell injection
        )
        
        print("Dependencies installed successfully!")
        print(f"Output: {result.stdout}")
        
        # List installed packages
        installed_packages = list(python_dir.glob("*"))
        print(f"Installed {len(installed_packages)} packages:")
        for pkg in sorted(installed_packages):
            if pkg.is_dir():
                print(f"  - {pkg.name}/")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def clean_dependencies():
    """Clean existing dependencies."""
    python_dir = Path("aurora_vector_kb/layers/postgresql/python")
    
    if python_dir.exists():
        print(f"Cleaning existing dependencies in {python_dir}")
        shutil.rmtree(python_dir)
        python_dir.mkdir(parents=True, exist_ok=True)

def main():
    """Main function."""
    print("Aurora Vector KB - Dependency Setup")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean_dependencies()
        print("Dependencies cleaned.")
        return
    
    # Check if pip is available
    try:
        subprocess.run( # pylint: disable=dangerous-subprocess-use-audit
            [sys.executable, "-m", "pip", "--version"],
            check=True,
            capture_output=True,
            shell=False  # Explicit: prevents shell injection
        )
    except subprocess.CalledProcessError:
        print("Error: pip is not available")
        sys.exit(1)
    
    # Install dependencies
    success = install_dependencies()
    
    if success:
        print("\n✅ Dependencies installed successfully!")
        print("\nNext steps:")
        print("1. Run 'cdk deploy' to deploy the stack")
        print("2. The Lambda layer will now include the required dependencies")
    else:
        print("\n❌ Failed to install dependencies")
        print("\nTroubleshooting:")
        print("1. Make sure you have pip installed")
        print("2. Try running with --user flag if you get permission errors")
        print("3. Consider using a virtual environment")
        sys.exit(1)

if __name__ == "__main__":
    main()