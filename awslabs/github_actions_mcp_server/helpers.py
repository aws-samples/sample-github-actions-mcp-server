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

"""Helper functions for GitHub Actions MCP Server."""

import os
import yaml
from github import Github
from github.Repository import Repository
from loguru import logger
from typing import Any, Dict, List, Optional, Union


def get_github_client(token: Optional[str] = None) -> Github:
    """Get a GitHub client instance.

    Args:
        token: GitHub personal access token. If not provided, will try to use GITHUB_TOKEN env var.

    Returns:
        A GitHub client instance.

    Raises:
        ValueError: If no token is provided and GITHUB_TOKEN env var is not set.
    """
    if token is None:
        token = os.environ.get('GITHUB_TOKEN')

    if not token:
        raise ValueError(
            'GitHub token not provided. Set GITHUB_TOKEN env var or provide token parameter.'
        )

    return Github(token)


async def get_repository(repo_name: str, token: Optional[str] = None) -> Repository:
    """Get a GitHub repository.

    Args:
        repo_name: Repository name in format 'owner/repo'.
        token: GitHub personal access token.

    Returns:
        A GitHub Repository object.

    Raises:
        ValueError: If repository not found or access denied.
    """
    try:
        client = get_github_client(token)
        return client.get_repo(repo_name)
    except Exception as e:
        logger.error(f'Error accessing repository {repo_name}: {e}')
        raise ValueError(f'Error accessing repository {repo_name}: {str(e)}')


async def list_workflows(repo_name: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
    """List GitHub Actions workflows in a repository.

    Args:
        repo_name: Repository name in format 'owner/repo'.
        token: GitHub personal access token.

    Returns:
        List of workflow details.
    """
    try:
        repo = await get_repository(repo_name, token)
        workflows = repo.get_workflows()

        result = []
        for workflow in workflows:
            result.append(
                {
                    'id': workflow.id,
                    'name': workflow.name,
                    'path': workflow.path,
                    'state': workflow.state,
                    'created_at': workflow.created_at.isoformat() if workflow.created_at else None,
                    'updated_at': workflow.updated_at.isoformat() if workflow.updated_at else None,
                    'url': workflow.html_url,
                }
            )

        return result
    except Exception as e:
        logger.error(f'Error listing workflows for {repo_name}: {e}')
        raise ValueError(f'Error listing workflows for {repo_name}: {str(e)}')


async def get_workflow(
    repo_name: str, workflow_id_or_name: Union[int, str], token: Optional[str] = None
) -> Dict[str, Any]:
    """Get a specific GitHub Actions workflow.

    Args:
        repo_name: Repository name in format 'owner/repo'.
        workflow_id_or_name: Workflow ID (int) or filename (str).
        token: GitHub personal access token.

    Returns:
        Workflow details and content.
    """
    try:
        repo = await get_repository(repo_name, token)

        # Get workflow by ID or filename
        if isinstance(workflow_id_or_name, int):
            workflow = repo.get_workflow(workflow_id_or_name)
        else:
            workflows = repo.get_workflows()
            workflow = None
            for wf in workflows:
                if wf.name == workflow_id_or_name or wf.path.endswith(workflow_id_or_name):
                    workflow = wf
                    break

        if not workflow:
            raise ValueError(f'Workflow {workflow_id_or_name} not found')

        # Get workflow content
        content_file = repo.get_contents(workflow.path)
        content = content_file.decoded_content.decode('utf-8')

        # Parse YAML content
        try:
            yaml_content = yaml.safe_load(content)
        except Exception as yaml_err:
            logger.warning(f'Error parsing workflow YAML: {yaml_err}')
            yaml_content = None

        return {
            'id': workflow.id,
            'name': workflow.name,
            'path': workflow.path,
            'state': workflow.state,
            'created_at': workflow.created_at.isoformat() if workflow.created_at else None,
            'updated_at': workflow.updated_at.isoformat() if workflow.updated_at else None,
            'url': workflow.html_url,
            'content': content,
            'parsed_yaml': yaml_content,
        }
    except Exception as e:
        logger.error(f'Error getting workflow {workflow_id_or_name} for {repo_name}: {e}')
        raise ValueError(f'Error getting workflow {workflow_id_or_name} for {repo_name}: {str(e)}')


async def list_workflow_runs(
    repo_name: str,
    workflow_id_or_name: Optional[Union[int, str]] = None,
    status: Optional[str] = None,
    limit: int = 10,
    token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List GitHub Actions workflow runs.

    Args:
        repo_name: Repository name in format 'owner/repo'.
        workflow_id_or_name: Optional workflow ID or name to filter runs.
        status: Optional status to filter runs (e.g., 'completed', 'in_progress').
        limit: Maximum number of runs to return.
        token: GitHub personal access token.

    Returns:
        List of workflow run details.
    """
    try:
        repo = await get_repository(repo_name, token)

        # Get workflow if specified
        workflow = None
        if workflow_id_or_name:
            if isinstance(workflow_id_or_name, int):
                workflow = repo.get_workflow(workflow_id_or_name)
            else:
                workflows = repo.get_workflows()
                for wf in workflows:
                    if wf.name == workflow_id_or_name or wf.path.endswith(workflow_id_or_name):
                        workflow = wf
                        break

                if not workflow:
                    raise ValueError(f'Workflow {workflow_id_or_name} not found')

        # Get runs
        if workflow:
            runs = workflow.get_runs(status=status)
        else:
            runs = repo.get_workflow_runs(status=status)

        result = []
        for run in runs[:limit]:
            result.append(
                {
                    'id': run.id,
                    'name': run.name,
                    'status': run.status,
                    'conclusion': run.conclusion,
                    'workflow_id': run.workflow_id,
                    'created_at': run.created_at.isoformat() if run.created_at else None,
                    'updated_at': run.updated_at.isoformat() if run.updated_at else None,
                    'run_number': run.run_number,
                    'event': run.event,
                    'url': run.html_url,
                }
            )

        return result
    except Exception as e:
        logger.error(f'Error listing workflow runs for {repo_name}: {e}')
        raise ValueError(f'Error listing workflow runs for {repo_name}: {str(e)}')


async def create_or_update_workflow(
    repo_name: str,
    workflow_path: str,
    content: str,
    commit_message: str = 'Update workflow via GitHub Actions MCP Server',
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """Create or update a GitHub Actions workflow file.

    Args:
        repo_name: Repository name in format 'owner/repo'.
        workflow_path: Path to workflow file (e.g., '.github/workflows/ci.yml').
        content: Workflow file content.
        commit_message: Commit message for the change.
        token: GitHub personal access token.

    Returns:
        Details of the created/updated workflow.
    """
    try:
        # Validate YAML content
        try:
            yaml.safe_load(content)
        except Exception as yaml_err:
            raise ValueError(f'Invalid YAML content: {str(yaml_err)}')

        repo = await get_repository(repo_name, token)

        # Check if file exists
        file = None
        try:
            file = repo.get_contents(workflow_path)
            # Update existing file
            repo.update_file(
                path=workflow_path, message=commit_message, content=content, sha=file.sha
            )
            logger.info(f'Updated workflow file {workflow_path} in {repo_name}')
        except Exception:
            # Create new file
            repo.create_file(path=workflow_path, message=commit_message, content=content)
            logger.info(f'Created workflow file {workflow_path} in {repo_name}')

        # Get the updated workflow
        workflows = repo.get_workflows()
        for workflow in workflows:
            if workflow.path == workflow_path:
                return {
                    'id': workflow.id,
                    'name': workflow.name,
                    'path': workflow.path,
                    'state': workflow.state,
                    'url': workflow.html_url,
                    'message': f'Successfully {"updated" if file else "created"} workflow file',
                }

        # If workflow not found in workflows list (might be processing)
        return {
            'path': workflow_path,
            'message': f'Workflow file {"updated" if file else "created"}, but not yet available as a workflow',
        }
    except Exception as e:
        logger.error(f'Error creating/updating workflow {workflow_path} for {repo_name}: {e}')
        raise ValueError(
            f'Error creating/updating workflow {workflow_path} for {repo_name}: {str(e)}'
        )


async def list_secrets(repo_name: str, token: Optional[str] = None) -> Dict[str, Any]:
    """List GitHub Actions secrets (names only, not values).

    Args:
        repo_name: Repository name in format 'owner/repo'.
        token: GitHub personal access token.

    Returns:
        Dictionary with repository secrets information.
    """
    try:
        repo = await get_repository(repo_name, token)
        secrets = repo.get_secrets()

        result = {'total_count': secrets.totalCount, 'secrets': []}

        for secret in secrets:
            result['secrets'].append(
                {
                    'name': secret.name,
                    'created_at': secret.created_at.isoformat() if secret.created_at else None,
                    'updated_at': secret.updated_at.isoformat() if secret.updated_at else None,
                }
            )

        return result
    except Exception as e:
        logger.error(f'Error listing secrets for {repo_name}: {e}')
        raise ValueError(f'Error listing secrets for {repo_name}: {str(e)}')


async def list_environments(repo_name: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
    """List GitHub Actions environments.

    Args:
        repo_name: Repository name in format 'owner/repo'.
        token: GitHub personal access token.

    Returns:
        List of environment details.
    """
    try:
        repo = await get_repository(repo_name, token)
        environments = repo.get_environments()

        result = []
        for env in environments.environments:
            result.append(
                {
                    'name': env.name,
                    'created_at': env.created_at.isoformat() if env.created_at else None,
                    'updated_at': env.updated_at.isoformat() if env.updated_at else None,
                    'protection_rules': {
                        'required_reviewers': bool(env.protection_rules.required_reviewers),
                        'wait_timer': env.protection_rules.wait_timer
                        if hasattr(env.protection_rules, 'wait_timer')
                        else None,
                    },
                }
            )

        return result
    except Exception as e:
        logger.error(f'Error listing environments for {repo_name}: {e}')
        raise ValueError(f'Error listing environments for {repo_name}: {str(e)}')


async def validate_workflow(content: str) -> Dict[str, Any]:
    """Validate GitHub Actions workflow YAML content.

    Args:
        content: Workflow YAML content.

    Returns:
        Validation results.
    """
    try:
        # Parse YAML - handle 'on' keyword which is a Python keyword
        yaml_content = yaml.safe_load(content)

        # Basic validation checks
        validation_results = {
            'valid': True,
            'warnings': [],
            'suggestions': [],
        }

        # Check for required fields
        if not yaml_content:
            validation_results['valid'] = False
            validation_results['warnings'].append('Empty workflow file')
            return validation_results

        if 'name' not in yaml_content:
            validation_results['warnings'].append('Missing workflow name')

        # Check for 'on' which might be parsed as True (boolean)
        has_on = False
        for key in yaml_content:
            if key is True or key == 'on':
                has_on = True
                break

        if not has_on:
            validation_results['valid'] = False
            validation_results['warnings'].append('Missing trigger events (on:)')

        if 'jobs' not in yaml_content:
            validation_results['valid'] = False
            validation_results['warnings'].append('Missing jobs section')
            return validation_results

        # Check jobs
        for job_id, job in yaml_content.get('jobs', {}).items():
            if not job:
                validation_results['warnings'].append(f'Empty job: {job_id}')
                continue

            if 'runs-on' not in job:
                validation_results['warnings'].append(f'Missing runs-on in job: {job_id}')

            if 'steps' not in job:
                validation_results['warnings'].append(f'Missing steps in job: {job_id}')

        # Check for best practices
        if yaml_content.get('jobs'):
            # Check for checkout action
            has_checkout = False
            for job_id, job in yaml_content['jobs'].items():
                for step in job.get('steps', []):
                    if step.get('uses', '').startswith('actions/checkout@'):
                        has_checkout = True
                        break
                if has_checkout:
                    break

            if not has_checkout:
                validation_results['suggestions'].append(
                    'Consider adding actions/checkout step to access repository files'
                )

        return validation_results
    except yaml.YAMLError as e:
        return {
            'valid': False,
            'warnings': [f'Invalid YAML: {str(e)}'],
            'suggestions': [],
        }
    except Exception as e:
        logger.error(f'Error validating workflow: {e}')
        return {
            'valid': False,
            'warnings': [f'Validation error: {str(e)}'],
            'suggestions': [],
        }


async def get_workflow_templates() -> Dict[str, str]:
    """Get common GitHub Actions workflow templates.

    Returns:
        Dictionary of template names and their YAML content.
    """
    templates = {
        'python-package': """name: Python Package

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        python -m pip install flake8 pytest
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    - name: Test with pytest
      run: |
        pytest
""",
        'node-package': """name: Node.js Package

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [14.x, 16.x, 18.x]

    steps:
    - uses: actions/checkout@v3
    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
    - run: npm ci
    - run: npm run build --if-present
    - run: npm test
""",
        'docker-image': """name: Docker Image CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build the Docker image
      run: docker build . --file Dockerfile --tag my-image:$(date +%s)
""",
        'aws-deploy': """name: Deploy to AWS

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1

    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1

    - name: Build, tag, and push image to Amazon ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: my-app
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
""",
        'terraform': """name: Terraform

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2

    - name: Terraform Init
      run: terraform init

    - name: Terraform Format
      run: terraform fmt -check

    - name: Terraform Plan
      run: terraform plan

    - name: Terraform Apply
      if: github.ref == 'refs/heads/main' && github.event_name == 'push'
      run: terraform apply -auto-approve
""",
    }

    return templates
