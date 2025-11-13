"""
Unit tests for technical indicators
"""
import pytest
import numpy as np
import pandas as pd
from backend.indicators import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
)


class TestCalculateRSI:
    """Test RSI calculation"""

    def test_rsi_with_valid_data(self):
        """Test RSI calculation with valid price data"""
        prices = [44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 
                 45.89, 46.03, 45.61, 46.28, 46.00, 46.00, 46.00, 46.00]
        rsi = calculate_rsi(prices, period=14)
        
        assert rsi is not None
        assert len(rsi) == len(prices)
        # Check that we have some valid RSI values
        valid_rsi = [v for v in rsi if not pd.isna(v)]
        assert len(valid_rsi) > 0
        assert all(0 <= val <= 100 for val in valid_rsi)

    def test_rsi_insufficient_data(self):
        """Test RSI with insufficient data points"""
        prices = [44, 44.34, 44.09]
        rsi = calculate_rsi(prices, period=14)
        
        assert rsi is None  # Should return None when insufficient data

    def test_rsi_constant_prices(self):
        """Test RSI with constant prices"""
        prices = [44.0] * 20
        rsi = calculate_rsi(prices, period=14)
        
        assert rsi is not None
        assert len(rsi) == len(prices)

    def test_rsi_rising_prices(self):
        """Test RSI with rising prices"""
        prices = [44.0 + i*0.5 for i in range(30)]
        rsi = calculate_rsi(prices, period=14)
        
        assert rsi is not None
        valid_rsi = [v for v in rsi if not pd.isna(v)]
        if len(valid_rsi) > 0:
            # Rising prices should have higher average RSI
            assert np.mean(valid_rsi[-5:]) > 50

    def test_rsi_falling_prices(self):
        """Test RSI with falling prices"""
        prices = [44.0 - i*0.5 for i in range(30)]
        rsi = calculate_rsi(prices, period=14)
        
        assert rsi is not None
        valid_rsi = [v for v in rsi if not pd.isna(v)]
        if len(valid_rsi) > 0:
            # Falling prices should have lower average RSI
            assert np.mean(valid_rsi[-5:]) < 50


class TestCalculateMACD:
    """Test MACD calculation"""

    def test_macd_with_valid_data(self):
        """Test MACD calculation with valid data"""
        prices = [44.0 + i*0.2 for i in range(50)]
        macd_result = calculate_macd(prices, fast=12, slow=26, signal=9)
        
        assert macd_result is not None
        macd_line, signal_line, histogram = macd_result
        assert len(macd_line) == len(prices)
        assert len(signal_line) == len(prices)
        assert len(histogram) == len(prices)

    def test_macd_insufficient_data(self):
        """Test MACD with insufficient data"""
        prices = [44, 44.34, 44.09]
        macd_result = calculate_macd(prices, fast=12, slow=26, signal=9)
        
        assert macd_result is None  # Should return None when insufficient data

    def test_macd_histogram_consistency(self):
        """Test that MACD histogram = MACD line - Signal line"""
        prices = [44.0 + i*0.2 for i in range(50)]
        macd_line, signal_line, histogram = calculate_macd(prices)
        
        # Calculate difference manually
        for i in range(len(histogram)):
            expected = macd_line[i] - signal_line[i]
            # Check alignment (allowing for floating point precision)
            if not pd.isna(expected) and not pd.isna(histogram[i]):
                assert abs(histogram[i] - expected) < 1e-10

    def test_macd_rising_prices(self):
        """Test MACD with rising prices"""
        prices = [44.0 + i*0.5 for i in range(50)]
        macd_line, signal_line, histogram = calculate_macd(prices)
        
        # With rising prices, MACD should generally be positive
        valid_macd = [v for v in macd_line if not pd.isna(v)]
        if len(valid_macd) > 5:
            # Last values should be more positive than earlier
            assert np.mean(valid_macd[-5:]) > np.mean(valid_macd[5:10])


class TestCalculateBollingerBands:
    """Test Bollinger Bands calculation"""

    def test_bollinger_bands_with_valid_data(self):
        """Test Bollinger Bands with valid data"""
        np.random.seed(42)  # For reproducibility
        prices = [44.0 + np.random.randn() for _ in range(50)]
        result = calculate_bollinger_bands(prices, period=20, num_std=2)
        
        assert result is not None
        upper, middle, lower = result
        assert len(upper) == len(prices)
        assert len(middle) == len(prices)
        assert len(lower) == len(prices)

    def test_bollinger_bands_ordering(self):
        """Test that upper band > middle band > lower band"""
        prices = [44.0 + i*0.1 for i in range(50)]
        upper, middle, lower = calculate_bollinger_bands(prices, period=20, num_std=2)
        
        # Check ordering (allowing for NaN values)
        for i in range(len(upper)):
            if not pd.isna(upper[i]) and not pd.isna(middle[i]) and not pd.isna(lower[i]):
                assert upper[i] >= middle[i] >= lower[i]

    def test_bollinger_bands_insufficient_data(self):
        """Test Bollinger Bands with insufficient data"""
        prices = [44, 44.34, 44.09]
        result = calculate_bollinger_bands(prices, period=20, num_std=2)
        
        assert result is None  # Should return None when insufficient data

    def test_bollinger_bands_constant_prices(self):
        """Test Bollinger Bands with constant prices"""
        prices = [44.0] * 50
        upper, middle, lower = calculate_bollinger_bands(prices, period=20, num_std=2)
        
        # With constant prices, middle band should equal all prices
        valid_indices = [i for i, v in enumerate(middle) if not pd.isna(v)]
        if valid_indices:
            for i in valid_indices:
                assert abs(middle[i] - 44.0) < 1e-10
                # Upper and lower should be symmetric around middle (width should be 0)
                assert abs((upper[i] - middle[i]) - (middle[i] - lower[i])) < 1e-10

    def test_bollinger_bands_std_dev_effect(self):
        """Test that larger std dev creates wider bands"""
        prices = [44.0 + i*0.1 for i in range(50)]
        
        upper_2, middle_2, lower_2 = calculate_bollinger_bands(prices, period=20, num_std=2)
        upper_1, middle_1, lower_1 = calculate_bollinger_bands(prices, period=20, num_std=1)
        
        # 2 std dev bands should be wider than 1 std dev
        width_2 = [upper_2[i] - lower_2[i] if not pd.isna(upper_2[i]) else None for i in range(len(upper_2))]
        width_1 = [upper_1[i] - lower_1[i] if not pd.isna(upper_1[i]) else None for i in range(len(upper_1))]
        
        valid_widths_2 = [w for w in width_2 if w is not None]
        valid_widths_1 = [w for w in width_1 if w is not None]
        
        if valid_widths_2 and valid_widths_1:
            assert np.mean(valid_widths_2) > np.mean(valid_widths_1)
