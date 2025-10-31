@echo off
REM Lambda Layer Preparation Script for Windows
REM
REM This script prepares the Lambda layer dependencies for the Aurora Vector Knowledge Base.
REM It installs the required Python packages for PostgreSQL connectivity and other dependencies
REM needed by the Lambda functions.

setlocal enabledelayedexpansion

echo [INFO] Preparing Lambda layer dependencies for Aurora Vector Knowledge Base...

REM Check if we're in the right directory
if not exist "app.py" (
    echo [ERROR] This script must be run from the project root directory
    echo [ERROR] Please run from the directory containing app.py
    exit /b 1
)

if not exist "aurora_vector_kb" (
    echo [ERROR] aurora_vector_kb directory not found
    echo [ERROR] Please run from the project root directory
    exit /b 1
)

REM Create the layers directory structure
set LAYER_DIR=aurora_vector_kb\layers\postgresql
set PYTHON_DIR=%LAYER_DIR%\python

echo [INFO] Creating layer directory structure...
if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"

REM Create requirements.txt if it doesn't exist
set REQUIREMENTS_FILE=%LAYER_DIR%\requirements.txt
if not exist "%REQUIREMENTS_FILE%" (
    echo [INFO] Creating requirements.txt for Lambda layer...
    (
        echo psycopg2-binary==2.9.7
        echo tiktoken==0.5.1
        echo boto3==1.34.0
        echo botocore==1.34.0
    ) > "%REQUIREMENTS_FILE%"
    echo [SUCCESS] Created %REQUIREMENTS_FILE%
)

REM Check if dependencies are already installed
if exist "%PYTHON_DIR%\psycopg2" if exist "%PYTHON_DIR%\tiktoken" (
    echo [WARNING] Dependencies appear to already be installed in %PYTHON_DIR%
    set /p REINSTALL="Do you want to reinstall them? (y/N): "
    if /i not "!REINSTALL!"=="y" (
        echo [INFO] Skipping installation. Using existing dependencies.
        exit /b 0
    )
    echo [INFO] Removing existing dependencies...
    rmdir /s /q "%PYTHON_DIR%"
    mkdir "%PYTHON_DIR%"
)

REM Check if pip3 is available
pip3 --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip3 is not installed or not in PATH
    echo [ERROR] Please install Python 3 and ensure pip3 is available
    exit /b 1
)

echo [INFO] Installing Lambda layer dependencies...
echo [INFO] This may take a few minutes...

REM Install dependencies for Lambda layer
pip3 install --quiet --platform manylinux2014_x86_64 --target "%PYTHON_DIR%" --python-version 3.11 --only-binary=:all: -r "%REQUIREMENTS_FILE%"

if errorlevel 1 (
    echo [ERROR] Failed to install Lambda layer dependencies
    echo [ERROR] Please check the error messages above and try again
    exit /b 1
)

REM Check if installation was successful
if exist "%PYTHON_DIR%\psycopg2" (
    echo [SUCCESS] Lambda layer dependencies installed successfully!
    echo [INFO] Installed packages:
    dir /b "%PYTHON_DIR%" | findstr /v "__pycache__"
    echo [SUCCESS] Lambda layer preparation complete!
    echo [INFO] You can now run 'cdk deploy' to deploy the stack.
) else (
    echo [ERROR] Installation verification failed
    echo [ERROR] psycopg2 directory not found in %PYTHON_DIR%
    exit /b 1
)

endlocal