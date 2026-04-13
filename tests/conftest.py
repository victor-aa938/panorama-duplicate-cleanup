"""
Pytest configuration and fixtures for duplicate service cleanup tests.

Shared fixtures and configuration for all tests.
"""
import pytest
from unittest.mock import MagicMock, patch
from typing import List, Dict

from src.models.service import Service, ServiceGroup


@pytest.fixture
def mock_connection():
    """Create a mock PanOS connection for testing."""
    conn = MagicMock()
    conn.ip = "1.2.3.4"
    conn.username = "admin"
    return conn


@pytest.fixture
def sample_services() -> List[Service]:
    """Create sample services for testing."""
    return [
        Service(name="tcp-443-1", protocol="tcp", port="443"),
        Service(name="tcp-443-2", protocol="tcp", port="443"),
        Service(name="tcp-80-1", protocol="tcp", port="80"),
    ]


@pytest.fixture
def sample_duplicate_groups() -> List[Dict]:
    """Create sample duplicate groups for testing."""
    return [
        {
            "key": "tcp:443",
            "services": [
                Service(name="tcp-443-1", protocol="tcp", port="443"),
                Service(name="tcp-443-2", protocol="tcp", port="443"),
            ],
        },
    ]


@pytest.fixture
def sample_policies() -> List[Dict]:
    """Create sample security policies for testing."""
    return [
        {
            "name": "allow-https-1",
            "service": ["tcp-443-1", "tcp-80-1"],
            "source": ["any"],
            "destination": ["internal"],
        },
        {
            "name": "allow-https-2",
            "service": ["tcp-443-2"],
            "source": ["external"],
            "destination": ["web-servers"],
        },
    ]


@pytest.fixture
def sample_groups() -> List[ServiceGroup]:
    """Create sample service groups for testing."""
    return [
        ServiceGroup(name="https-servers", members=["tcp-443-1", "tcp-443-2"]),
        ServiceGroup(name="web-servers", members=["tcp-80-1"]),
    ]


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def dry_run_config():
    """Get a dry-run configuration for testing."""
    return {"dry_run": True}


@pytest.fixture
def commit_config():
    """Get a commit configuration for testing."""
    return {"dry_run": False}


@pytest.fixture(autouse=True)
def setup_logging():
    """Setup logging for all tests."""
    import logging
    logging.basicConfig(level=logging.DEBUG)