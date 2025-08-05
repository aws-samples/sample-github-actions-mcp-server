# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""GitHub Actions MCP Server implementation."""

from awslabs.github_actions_mcp_server.helpers import (
    create_or_update_workflow,
    get_workflow,
    get_workflow_templates,
    list_environments,
    list_secrets,
    list_workflow_runs,
    list_workflows,
    validate_workflow,
)
from loguru import logger
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import Annotated, Any, Dict, Optional, Union


mcp = FastMCP(
    'awslabs.github-actions-mcp-server',
    instructions="""
    GitHub Actions MCP Server provides tools to interact with GitHub Actions workflows.

    This server enables you to:
    - List, view, and manage GitHub Actions workflows
    - Validate workflow YAML syntax
    - Get workflow run history and status
    - Manage GitHub Actions secrets and environments
    - Generate workflow templates for common use cases

    Use these tools to streamline your CI/CD pipeline management with GitHub Actions.
    """,
    dependencies=[
        'pydantic',
        'loguru',
        'pygithub',
        'pyyaml',
    ],
)


@mcp.tool(name='listWorkflows')
async def list_workflows_tool(
    repo_name: Annotated[str, Field(description='Repository name in format "owner/repo"')],
    token: Annotated[
        Optional[str], Field(description='GitHub personal access token (optional)')
    ] = None,
) -> Dict[str, Any]:
    """List GitHub Actions workflows in a repository.

    ## Usage

    Use this tool to retrieve a list of all GitHub Actions workflows defined in a repository.
    This helps you understand what automation is already set up in the project.

    ## Example

    ```python
    # List all workflows in a repository
    workflows = await listWorkflows(repo_name='octocat/Hello-World')
    ```

    ## Output Format

    The output is a list of workflow objects, each containing:
    - `id`: Unique identifier for the workflow
    - `name`: Display name of the workflow
    - `path`: File path of the workflow definition
    - `state`: Current state (active, disabled)
    - `created_at`: Creation timestamp
    - `updated_at`: Last update timestamp
    - `url`: HTML URL to view the workflow

    Args:
        repo_name: Repository name in format "owner/repo".
        token: GitHub personal access token. If not provided, uses GITHUB_TOKEN env var.

    Returns:
        A dictionary containing a list of workflows.
    """
    try:
        workflows = await list_workflows(repo_name, token)
        return {'workflows': workflows}
    except Exception as e:
        logger.error(f'Error listing workflows: {e}')
        raise ValueError(f'Error listing workflows: {str(e)}')


@mcp.tool(name='getWorkflow')
async def get_workflow_tool(
    repo_name: Annotated[str, Field(description='Repository name in format "owner/repo"')],
    workflow_id_or_name: Annotated[
        Union[int, str], Field(description='Workflow ID (int) or filename (str)')
    ],
    token: Annotated[
        Optional[str], Field(description='GitHub personal access token (optional)')
    ] = None,
) -> Dict[str, Any]:
    """Get details and content of a specific GitHub Actions workflow.

    ## Usage

    Use this tool to retrieve detailed information about a specific workflow, including its
    YAML content and configuration. This is useful for understanding or modifying existing workflows.

    ## Example

    ```python
    # Get workflow by ID
    workflow = await getWorkflow(repo_name='octocat/Hello-World', workflow_id_or_name=12345678)

    # Get workflow by filename
    workflow = await getWorkflow(repo_name='octocat/Hello-World', workflow_id_or_name='ci.yml')
    ```

    ## Output Format

    The output is a dictionary containing:
    - Basic workflow metadata (id, name, path, state, etc.)
    - `content`: The raw YAML content of the workflow file
    - `parsed_yaml`: The parsed YAML structure (if valid)

    Args:
        repo_name: Repository name in format "owner/repo".
        workflow_id_or_name: Workflow ID (int) or filename (str).
        token: GitHub personal access token. If not provided, uses GITHUB_TOKEN env var.

    Returns:
        A dictionary containing workflow details and content.
    """
    try:
        workflow = await get_workflow(repo_name, workflow_id_or_name, token)
        return workflow
    except Exception as e:
        logger.error(f'Error getting workflow: {e}')
        raise ValueError(f'Error getting workflow: {str(e)}')


@mcp.tool(name='listWorkflowRuns')
async def list_workflow_runs_tool(
    repo_name: Annotated[str, Field(description='Repository name in format "owner/repo"')],
    workflow_id_or_name: Annotated[
        Optional[Union[int, str]], Field(description='Optional workflow ID or name to filter runs')
    ] = None,
    status: Annotated[
        Optional[str],
        Field(description='Optional status to filter runs (e.g., "completed", "in_progress")'),
    ] = None,
    limit: Annotated[int, Field(description='Maximum number of runs to return')] = 10,
    token: Annotated[
        Optional[str], Field(description='GitHub personal access token (optional)')
    ] = None,
) -> Dict[str, Any]:
    """List GitHub Actions workflow runs.

    ## Usage

    Use this tool to retrieve the execution history of workflows in a repository.
    You can filter by specific workflow and status, and limit the number of results.

    ## Example

    ```python
    # List recent workflow runs for a specific workflow
    runs = await listWorkflowRuns(
        repo_name='octocat/Hello-World', workflow_id_or_name='ci.yml', status='completed', limit=5
    )
    ```

    ## Output Format

    The output is a list of workflow run objects, each containing:
    - `id`: Unique identifier for the run
    - `name`: Name of the workflow
    - `status`: Current status (queued, in_progress, completed)
    - `conclusion`: Result (success, failure, cancelled, etc.)
    - `created_at`: When the run was created
    - `updated_at`: When the run was last updated
    - `run_number`: Sequential run number
    - `event`: Triggering event (push, pull_request, etc.)
    - `url`: HTML URL to view the run

    Args:
        repo_name: Repository name in format "owner/repo".
        workflow_id_or_name: Optional workflow ID or name to filter runs.
        status: Optional status to filter runs.
        limit: Maximum number of runs to return.
        token: GitHub personal access token. If not provided, uses GITHUB_TOKEN env var.

    Returns:
        A dictionary containing a list of workflow runs.
    """
    try:
        runs = await list_workflow_runs(repo_name, workflow_id_or_name, status, limit, token)
        return {'runs': runs}
    except Exception as e:
        logger.error(f'Error listing workflow runs: {e}')
        raise ValueError(f'Error listing workflow runs: {str(e)}')


@mcp.tool(name='createOrUpdateWorkflow')
async def create_or_update_workflow_tool(
    repo_name: Annotated[str, Field(description='Repository name in format "owner/repo"')],
    workflow_path: Annotated[
        str, Field(description='Path to workflow file (e.g., ".github/workflows/ci.yml")')
    ],
    content: Annotated[str, Field(description='Workflow file content (YAML)')],
    commit_message: Annotated[
        str, Field(description='Commit message for the change')
    ] = 'Update workflow via GitHub Actions MCP Server',
    token: Annotated[
        Optional[str], Field(description='GitHub personal access token (optional)')
    ] = None,
) -> Dict[str, Any]:
    """Create or update a GitHub Actions workflow file.

    ## Usage

    Use this tool to create a new workflow file or update an existing one in a repository.
    The content should be valid GitHub Actions workflow YAML.

    ## Example

    ```python
    # Create a new workflow
    result = await createOrUpdateWorkflow(
        repo_name='octocat/Hello-World',
        workflow_path='.github/workflows/deploy.yml',
        content='''name: Deploy
    on:
    push:
    branches: [ main ]
    jobs:
    deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy
        run: echo "Deploying..."
    ''',
        commit_message='Add deployment workflow',
    )
    ```

    ## Output Format

    The output is a dictionary containing:
    - Basic workflow metadata if available
    - A message indicating success

    Args:
        repo_name: Repository name in format "owner/repo".
        workflow_path: Path to workflow file (e.g., ".github/workflows/ci.yml").
        content: Workflow file content (YAML).
        commit_message: Commit message for the change.
        token: GitHub personal access token. If not provided, uses GITHUB_TOKEN env var.

    Returns:
        A dictionary containing the result of the operation.
    """
    try:
        result = await create_or_update_workflow(
            repo_name, workflow_path, content, commit_message, token
        )
        return result
    except Exception as e:
        logger.error(f'Error creating/updating workflow: {e}')
        raise ValueError(f'Error creating/updating workflow: {str(e)}')


@mcp.tool(name='listSecrets')
async def list_secrets_tool(
    repo_name: Annotated[str, Field(description='Repository name in format "owner/repo"')],
    token: Annotated[
        Optional[str], Field(description='GitHub personal access token (optional)')
    ] = None,
) -> Dict[str, Any]:
    """List GitHub Actions secrets (names only, not values).

    ## Usage

    Use this tool to retrieve a list of all secrets configured for GitHub Actions in a repository.
    For security reasons, only secret names are returned, not their values.

    ## Example

    ```python
    # List all secrets in a repository
    secrets = await listSecrets(repo_name='octocat/Hello-World')
    ```

    ## Output Format

    The output is a dictionary containing:
    - `total_count`: Total number of secrets
    - `secrets`: List of secret objects, each with:
      - `name`: Secret name
      - `created_at`: When the secret was created
      - `updated_at`: When the secret was last updated

    Args:
        repo_name: Repository name in format "owner/repo".
        token: GitHub personal access token. If not provided, uses GITHUB_TOKEN env var.

    Returns:
        A dictionary containing information about repository secrets.
    """
    try:
        secrets = await list_secrets(repo_name, token)
        return secrets
    except Exception as e:
        logger.error(f'Error listing secrets: {e}')
        raise ValueError(f'Error listing secrets: {str(e)}')


@mcp.tool(name='listEnvironments')
async def list_environments_tool(
    repo_name: Annotated[str, Field(description='Repository name in format "owner/repo"')],
    token: Annotated[
        Optional[str], Field(description='GitHub personal access token (optional)')
    ] = None,
) -> Dict[str, Any]:
    """List GitHub Actions environments.

    ## Usage

    Use this tool to retrieve a list of all environments configured for GitHub Actions in a repository.
    Environments are used for deployment targets and can have protection rules.

    ## Example

    ```python
    # List all environments in a repository
    environments = await listEnvironments(repo_name='octocat/Hello-World')
    ```

    ## Output Format

    The output is a list of environment objects, each containing:
    - `name`: Environment name
    - `created_at`: When the environment was created
    - `updated_at`: When the environment was last updated
    - `protection_rules`: Protection rules configured for the environment

    Args:
        repo_name: Repository name in format "owner/repo".
        token: GitHub personal access token. If not provided, uses GITHUB_TOKEN env var.

    Returns:
        A dictionary containing a list of environments.
    """
    try:
        environments = await list_environments(repo_name, token)
        return {'environments': environments}
    except Exception as e:
        logger.error(f'Error listing environments: {e}')
        raise ValueError(f'Error listing environments: {str(e)}')


@mcp.tool(name='validateWorkflow')
async def validate_workflow_tool(
    content: Annotated[str, Field(description='Workflow YAML content to validate')],
) -> Dict[str, Any]:
    """Validate GitHub Actions workflow YAML content.

    ## Usage

    Use this tool to check if a GitHub Actions workflow YAML is valid and follows best practices.
    This helps catch errors before committing workflows to a repository.

    ## Example

    ```python
    # Validate workflow YAML
    validation = await validateWorkflow(
        content='''name: CI
    on:
    push:
    branches: [ main ]
    jobs:
    build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build
        run: echo "Building..."
    '''
    )
    ```

    ## Output Format

    The output is a dictionary containing:
    - `valid`: Boolean indicating if the YAML is valid
    - `warnings`: List of warnings about potential issues
    - `suggestions`: List of suggestions for improvements

    Args:
        content: Workflow YAML content to validate.

    Returns:
        A dictionary containing validation results.
    """
    try:
        validation = await validate_workflow(content)
        return validation
    except Exception as e:
        logger.error(f'Error validating workflow: {e}')
        raise ValueError(f'Error validating workflow: {str(e)}')


@mcp.tool(name='getWorkflowTemplates')
async def get_workflow_templates_tool() -> Dict[str, str]:
    """Get common GitHub Actions workflow templates.

    ## Usage

    Use this tool to retrieve pre-defined templates for common GitHub Actions workflows.
    These templates can be used as a starting point for creating new workflows.

    ## Example

    ```python
    # Get all available workflow templates
    templates = await getWorkflowTemplates()

    # Use a specific template
    python_template = templates['python-package']
    ```

    ## Available Templates

    - `python-package`: Python package CI workflow
    - `node-package`: Node.js package CI workflow
    - `docker-image`: Docker image build workflow
    - `aws-deploy`: AWS deployment workflow
    - `terraform`: Terraform infrastructure workflow

    Returns:
        A dictionary of template names and their YAML content.
    """
    try:
        templates = await get_workflow_templates()
        return templates
    except Exception as e:
        logger.error(f'Error getting workflow templates: {e}')
        raise ValueError(f'Error getting workflow templates: {str(e)}')


def main():
    """Run the MCP server with CLI argument support."""
    logger.info('Starting GitHub Actions MCP Server')
    mcp.run()


if __name__ == '__main__':
    main()
