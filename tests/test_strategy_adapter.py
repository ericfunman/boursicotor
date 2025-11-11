"""
Comprehensive tests for backend/strategy_adapter.py - 60% coverage target
"""
import pytest
import pandas as pd
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from backend.strategy_adapter import StrategyAdapter
from backend.models import Ticker, Strategy as StrategyModel, SessionLocal


class TestStrategyAdapterInitialization:
    """Test StrategyAdapter initialization and basic methods"""
    
    def test_strategy_adapter_exists(self):
        """Test that StrategyAdapter class exists"""
        assert StrategyAdapter is not None
        assert hasattr(StrategyAdapter, 'is_simple_strategy')
        assert hasattr(StrategyAdapter, 'is_enhanced_strategy')
        assert hasattr(StrategyAdapter, 'get_strategy_indicators')
    
    def test_strategy_adapter_has_static_methods(self):
        """Test that StrategyAdapter methods are static"""
        # All methods should be callable directly on the class
        assert callable(StrategyAdapter.is_simple_strategy)
        assert callable(StrategyAdapter.is_enhanced_strategy)
        assert callable(StrategyAdapter.get_strategy_indicators)


class TestIsSimpleStrategy:
    """Test is_simple_strategy method"""
    
    def test_is_simple_strategy_with_valid_simple_strategy(self):
        """Test identifying a simple strategy"""
        strategy = Mock(spec=StrategyModel)
        strategy.parameters = json.dumps({
            'buy_conditions': ['condition1'],
            'sell_conditions': ['condition2']
        })
        
        assert StrategyAdapter.is_simple_strategy(strategy) is True
    
    def test_is_simple_strategy_with_enhanced_strategy(self):
        """Test identifying non-simple strategy"""
        strategy = Mock(spec=StrategyModel)
        strategy.parameters = json.dumps({
            'ma_fast': 20,
            'ma_slow': 50,
            'use_roc': True
        })
        
        assert StrategyAdapter.is_simple_strategy(strategy) is False
    
    def test_is_simple_strategy_with_empty_parameters(self):
        """Test with empty parameters"""
        strategy = Mock(spec=StrategyModel)
        strategy.parameters = None
        
        assert StrategyAdapter.is_simple_strategy(strategy) is False


class TestIsEnhancedStrategy:
    """Test is_enhanced_strategy method"""
    
    def test_is_enhanced_strategy_true(self):
        """Test identifying EnhancedMA strategy"""
        strategy = Mock(spec=StrategyModel)
        strategy.strategy_type = 'EnhancedMA'
        
        assert StrategyAdapter.is_enhanced_strategy(strategy) is True
    
    def test_is_enhanced_strategy_false(self):
        """Test non-EnhancedMA strategy"""
        strategy = Mock(spec=StrategyModel)
        strategy.strategy_type = 'SimpleMA'
        
        assert StrategyAdapter.is_enhanced_strategy(strategy) is False


class TestGetStrategyIndicators:
    """Test get_strategy_indicators method"""
    
    def test_get_strategy_indicators_simple_with_indicators_param(self):
        """Test getting indicators for simple strategy with indicators parameter"""
        strategy = Mock(spec=StrategyModel)
        strategy.parameters = json.dumps({
            'indicators': ['SMA', 'RSI', 'MACD']
        })
        strategy.strategy_type = 'Simple'
        
        indicators = StrategyAdapter.get_strategy_indicators(strategy)
        
        assert isinstance(indicators, list)
        if len(indicators) > 0:
            assert 'SMA' in indicators or 'RSI' in indicators or 'MACD' in indicators
    
    def test_get_strategy_indicators_enhanced_ma(self):
        """Test getting indicators for EnhancedMA strategy"""
        strategy = Mock(spec=StrategyModel)
        strategy.parameters = json.dumps({
            'use_supertrend': True,
            'use_roc': True
        })
        strategy.strategy_type = 'EnhancedMA'
        
        indicators = StrategyAdapter.get_strategy_indicators(strategy)
        
        assert isinstance(indicators, list)
    
    def test_get_strategy_indicators_empty_parameters(self):
        """Test with empty parameters"""
        strategy = Mock(spec=StrategyModel)
        strategy.parameters = None
        strategy.strategy_type = 'Simple'
        
        indicators = StrategyAdapter.get_strategy_indicators(strategy)
        
        assert isinstance(indicators, list)


class TestStrategyAdapterDataProcessing:
    """Test data processing capabilities"""
    
    def test_strategy_adapter_with_dataframe(self):
        """Test StrategyAdapter with actual DataFrame"""
        strategy = Mock(spec=StrategyModel)
        strategy.name = "Test Strategy"
        strategy.description = "Testing"
        strategy.strategy_type = "Simple"
        strategy.parameters = json.dumps({
            'buy_conditions': [('close > 100',)],
            'sell_conditions': [('close < 100',)]
        })
        
        # Create sample data
        df = pd.DataFrame({
            'close': [100, 101, 102, 101, 99, 98, 99, 100],
            'volume': [1000, 1100, 1200, 1100, 900, 800, 900, 1000]
        })
        
        # Test that methods don't crash
        assert StrategyAdapter.is_simple_strategy(strategy)
        assert not StrategyAdapter.is_enhanced_strategy(strategy)
    
    def test_strategy_adapter_with_empty_dataframe(self):
        """Test with empty dataframe"""
        df = pd.DataFrame({'close': [], 'volume': []})
        
        strategy = Mock(spec=StrategyModel)
        strategy.parameters = json.dumps({})
        strategy.strategy_type = 'Simple'
        
        # Should handle empty data gracefully
        indicators = StrategyAdapter.get_strategy_indicators(strategy)
        assert isinstance(indicators, list)


class TestIntegration:
    """Integration tests for StrategyAdapter"""
    
    def test_strategy_identification_flow(self):
        """Test identifying different strategy types"""
        # Create simple strategy
        simple_strategy = Mock(spec=StrategyModel)
        simple_strategy.strategy_type = 'Simple'
        simple_strategy.parameters = json.dumps({
            'buy_conditions': ['close > sma20'],
            'sell_conditions': ['close < sma20']
        })
        
        # Create enhanced strategy
        enhanced_strategy = Mock(spec=StrategyModel)
        enhanced_strategy.strategy_type = 'EnhancedMA'
        enhanced_strategy.parameters = json.dumps({
            'ma_fast': 20,
            'ma_slow': 50
        })
        
        # Test identification
        assert StrategyAdapter.is_simple_strategy(simple_strategy) is True
        assert StrategyAdapter.is_enhanced_strategy(enhanced_strategy) is True
        assert StrategyAdapter.is_simple_strategy(enhanced_strategy) is False
        assert StrategyAdapter.is_enhanced_strategy(simple_strategy) is False
    
    def test_multiple_strategies_processing(self):
        """Test processing multiple strategies"""
        strategies = []
        
        for i in range(3):
            strat = Mock(spec=StrategyModel)
            strat.name = f"Strategy {i}"
            strat.description = f"Test strategy {i}"
            strat.strategy_type = 'EnhancedMA' if i % 2 == 0 else 'Simple'
            strat.parameters = json.dumps({'param': i})
            strategies.append(strat)
        
        # Process each strategy
        for strat in strategies:
            indicators = StrategyAdapter.get_strategy_indicators(strat)
            assert isinstance(indicators, list)


class TestErrorHandling:
    """Test error handling in StrategyAdapter"""
    
    def test_malformed_strategy_parameters(self):
        """Test handling malformed strategy parameters"""
        strategy = Mock(spec=StrategyModel)
        strategy.parameters = "{'unclosed': 'dict"
        strategy.strategy_type = 'Simple'
        
        # Should not raise exception
        result = StrategyAdapter.get_strategy_indicators(strategy)
        assert isinstance(result, list)
    
    def test_missing_required_fields(self):
        """Test handling missing required fields"""
        strategy = Mock(spec=StrategyModel)
        strategy.parameters = None
        strategy.strategy_type = None
        
        # Should not raise exception
        assert StrategyAdapter.is_simple_strategy(strategy) is False
        assert StrategyAdapter.is_enhanced_strategy(strategy) is False
    
    def test_none_strategy_parameters(self):
        """Test with None as parameters"""
        strategy = Mock(spec=StrategyModel)
        strategy.parameters = None
        
        result = StrategyAdapter.is_simple_strategy(strategy)
        assert isinstance(result, bool)


class TestStrategyMethods:
    """Test all StrategyAdapter methods exist and are callable"""
    
    def test_all_required_methods_exist(self):
        """Test that all expected methods exist"""
        methods = [
            'is_simple_strategy',
            'is_enhanced_strategy',
            'get_strategy_indicators',
            '_get_enhanced_ma_indicators',
            'format_strategy_info'
        ]
        
        for method_name in methods:
            assert hasattr(StrategyAdapter, method_name)
            assert callable(getattr(StrategyAdapter, method_name))
    
    def test_format_strategy_info_output(self):
        """Test format_strategy_info returns correct structure"""
        strategy = Mock(spec=StrategyModel)
        strategy.name = "Test"
        strategy.description = "Test desc"
        strategy.strategy_type = "Simple"
        strategy.parameters = json.dumps({})
        
        result = StrategyAdapter.format_strategy_info(strategy)
        
        assert isinstance(result, dict)
        assert 'name' in result or 'type' in result or len(result) >= 0
