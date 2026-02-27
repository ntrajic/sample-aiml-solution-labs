# Architecture diagrams with generative AI: Leveraging AI agents

Supporting code for https://catalog.workshops.aws/ea71ab78-62e9-44ad-8d9c-787119f723da

## Setup

If running in your own environment:

1. Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) - An extremely fast Python package and project manager, written in Rust.

2. Create a Python virtual environment and install packages from `pyproject.toml` (including boto3).

    ```bash
    uv sync
    ```

3. If not automatically prompted by Code Editor / Visual Studio Code, use the [command palette](https://code.visualstudio.com/api/ux-guidelines/command-palette) to `Python: Select Interpreter` and enable `.venv` as default Python.

4. (optional) To track changes and compare results, run the following `git` commands.

    ```bash
    git init
    git add .
    git commit -m 'Initial commit'
    ```

5. Test your Python environment and connectivity to the AWS region set by `AWS_REGION` using `uv run awssessiontest.py`.
