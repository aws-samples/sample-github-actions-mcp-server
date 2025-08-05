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

"""Tests for GitHub Actions MCP Server helpers."""

import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from awslabs.github_actions_mcp_server.helpers import (
    get_github_client,
    get_repository,
    validate_workflow,
    get_workflow_templates,
)


def test_get_github_client_with_token():
    """Test get_github_client with token parameter."""
    with patch('awslabs.github_actions_mcp_server.helpers.Github') as mock_github:
        get_github_client('test-token')
        mock_github.assert_called_once_with('test-token')


def test_get_github_client_with_env_var():
    """Test get_github_client with environment variable."""
    with patch('awslabs.github_actions_mcp_server.helpers.Github') as mock_github:
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'env-token'}):
            get_github_client()
            mock_github.assert_called_once_with('env-token')


def test_get_github_client_no_token():
    """Test get_github_client with no token."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match='GitHub token not provided'):
            get_github_client()


@pytest.mark.asyncio
async def test_get_repository():
    """Test get_repository function."""
    mock_repo = MagicMock()
    mock_client = MagicMock()
    mock_client.get_repo.return_value = mock_repo
    
    with patch('awslabs.github_actions_mcp_server.helpers.get_github_client', return_value=mock_client):
        result = await get_repository('test/repo', 'test-token')
        
        assert result == mock_repo
        mock_client.get_repo.assert_called_once_with('test/repo')


@pytest.mark.asyncio
async def test_validate_workflow_valid():
    """Test validate_workflow with valid YAML."""
    content = '''name: CI
on:
  push:
    branches: [ main ]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Hello"
'''
    
    result = await validate_workflow(content)
    
    assert result['valid'] is True
    assert len(result['warnings']) == 0


@pytest.mark.asyncio
async def test_validate_workflow_invalid():
    """Test validate_workflow with invalid YAML."""
    content = '''name: CI
on:
  push:
    branches: [ main
jobs:
  build:
'''
    
    result = await validate_workflow(content)
    
    assert result['valid'] is False
    assert len(result['warnings']) > 0
    assert any('Invalid YAML' in warning for warning in result['warnings'])


@pytest.mark.asyncio
async def test_validate_workflow_missing_required():
    """Test validate_workflow with missing required fields."""
    content = '''name: CI
'''
    
    result = await validate_workflow(content)
    
    assert result['valid'] is False
    assert any('Missing trigger events' in warning for warning in result['warnings'])
    assert any('Missing jobs section' in warning for warning in result['warnings'])


@pytest.mark.asyncio
async def test_get_workflow_templates():
    """Test get_workflow_templates function."""
    templates = await get_workflow_templates()
    
    assert 'python-package' in templates
    assert 'node-package' in templates
    assert 'docker-image' in templates
    assert 'aws-deploy' in templates
    assert 'terraform' in templates
