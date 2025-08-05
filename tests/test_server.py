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

"""Tests for GitHub Actions MCP Server."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from awslabs.github_actions_mcp_server.server import (
    list_workflows_tool,
    get_workflow_tool,
    validate_workflow_tool,
    get_workflow_templates_tool,
)


@pytest.mark.asyncio
async def test_list_workflows_tool():
    """Test list_workflows_tool function."""
    mock_workflows = [
        {
            'id': 12345,
            'name': 'CI',
            'path': '.github/workflows/ci.yml',
            'state': 'active',
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-01T00:00:00Z',
            'url': 'https://github.com/test/repo/actions/workflows/ci.yml',
        }
    ]
    
    with patch('awslabs.github_actions_mcp_server.server.list_workflows', new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_workflows
        result = await list_workflows_tool('test/repo')
        
        assert result == {'workflows': mock_workflows}
        mock_list.assert_called_once_with('test/repo', None)


@pytest.mark.asyncio
async def test_get_workflow_tool():
    """Test get_workflow_tool function."""
    mock_workflow = {
        'id': 12345,
        'name': 'CI',
        'path': '.github/workflows/ci.yml',
        'state': 'active',
        'created_at': '2025-01-01T00:00:00Z',
        'updated_at': '2025-01-01T00:00:00Z',
        'url': 'https://github.com/test/repo/actions/workflows/ci.yml',
        'content': 'name: CI\non:\n  push:\n    branches: [ main ]',
        'parsed_yaml': {'name': 'CI', 'on': {'push': {'branches': ['main']}}},
    }
    
    with patch('awslabs.github_actions_mcp_server.server.get_workflow', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_workflow
        result = await get_workflow_tool('test/repo', 'ci.yml')
        
        assert result == mock_workflow
        mock_get.assert_called_once_with('test/repo', 'ci.yml', None)


@pytest.mark.asyncio
async def test_validate_workflow_tool():
    """Test validate_workflow_tool function."""
    mock_validation = {
        'valid': True,
        'warnings': [],
        'suggestions': ['Consider adding actions/checkout step to access repository files'],
    }
    
    with patch('awslabs.github_actions_mcp_server.server.validate_workflow', new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = mock_validation
        content = 'name: CI\non:\n  push:\n    branches: [ main ]'
        result = await validate_workflow_tool(content)
        
        assert result == mock_validation
        mock_validate.assert_called_once_with(content)


@pytest.mark.asyncio
async def test_get_workflow_templates_tool():
    """Test get_workflow_templates_tool function."""
    mock_templates = {
        'python-package': 'name: Python Package\n',
        'node-package': 'name: Node.js Package\n',
    }
    
    with patch('awslabs.github_actions_mcp_server.server.get_workflow_templates', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_templates
        result = await get_workflow_templates_tool()
        
        assert result == mock_templates
        mock_get.assert_called_once()
