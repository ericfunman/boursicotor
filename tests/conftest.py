"""
Pytest configuration and fixtures
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


@pytest.fixture
def project_root():
    """Return project root directory"""
    return Path(__file__).parent.parent


@pytest.fixture
def backend_path(project_root):
    """Return backend directory path"""
    return project_root / "backend"


@pytest.fixture
def frontend_path(project_root):
    """Return frontend directory path"""
    return project_root / "frontend"
