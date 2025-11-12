"""
Pytest configuration and fixtures
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pandas as pd
import numpy as np


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


# Test Data Fixtures

@pytest.fixture
def sample_ohlcv_data():
    """Sample OHLCV data for testing"""
    return pd.DataFrame({
        'open': [100, 101, 102, 103, 104] * 20,
        'high': [101, 102, 103, 104, 105] * 20,
        'low': [99, 100, 101, 102, 103] * 20,
        'close': [100, 101, 102, 103, 104] * 20,
        'volume': [1000, 1100, 1200, 1300, 1400] * 20,
    })


@pytest.fixture
def momentum_test_data():
    """Test data for momentum strategy"""
    df = pd.DataFrame({
        'close': np.linspace(100, 150, 50),
        'rsi_14': np.concatenate([
            np.linspace(20, 30, 10),  # Oversold
            np.linspace(30, 50, 15),  # Normal
            np.linspace(50, 75, 15),  # Overbought
            np.linspace(75, 80, 10),  # Extreme overbought
        ])
    })
    return df


@pytest.fixture
def crossover_test_data():
    """Test data for MA crossover strategy"""
    df = pd.DataFrame({
        'close': [100, 101, 102, 101, 100] * 4,
        'sma_20': [100, 100.5, 101, 100.8, 100.5] * 4,
        'sma_50': [100, 100.2, 100.4, 100.6, 100.8] * 4,
    })
    return df


@pytest.fixture
def config_tickers():
    """Sample tickers configuration"""
    return {
        'TTE': {'name': 'TotalEnergies', 'isin': 'FR0000120271'},
        'WLN': {'name': 'Worldline', 'isin': 'FR0011981968'},
        'BNP': {'name': 'BNP Paribas', 'isin': 'FR0000131104'},
    }

