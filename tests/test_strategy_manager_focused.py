"""
Focused tests for strategy_manager.py (35 tests)
Coverage target: 25% -> 60%+
Tests: StrategyManager static methods, utility functions, numpy conversion
"""
import pytest
from unittest.mock import Mock, patch
import json
import numpy as np

from backend.strategy_manager import StrategyManager


class TestStrategyManagerImport:
    """Test 1-3: Import and basic utilities"""
    
    def test_import_strategy_manager(self):
        """Test 1: StrategyManager can be imported"""
        assert StrategyManager is not None
    
    def test_convert_numpy_types_dict(self):
        """Test 2: Convert numpy types in dict"""
        data = {
            'int_val': np.int64(42),
            'float_val': np.float32(3.14),
            'nested': {'bool_val': np.bool_(True)}
        }
        result = StrategyManager._convert_numpy_types(data)
        assert isinstance(result['int_val'], int)
        assert isinstance(result['float_val'], float)
        assert isinstance(result['nested']['bool_val'], bool)
        assert result['int_val'] == 42
    
    def test_convert_numpy_types_list(self):
        """Test 3: Convert numpy types in list"""
        data = [np.int64(1), np.float32(2.5), [np.int32(3)]]
        result = StrategyManager._convert_numpy_types(data)
        assert isinstance(result[0], int)
        assert isinstance(result[1], float)
        assert isinstance(result[2][0], int)


class TestStrategyManagerInit:
    """Test 4-10: Static method testing"""
    
    def test_convert_numpy_array(self):
        """Test 4: Convert numpy array to list"""
        arr = np.array([1, 2, 3])
        result = StrategyManager._convert_numpy_types(arr)
        assert isinstance(result, list)
        assert result == [1, 2, 3]
    
    def test_convert_numpy_types_scalar_int(self):
        """Test 5: Convert numpy scalar int"""
        val = np.int32(100)
        result = StrategyManager._convert_numpy_types(val)
        assert isinstance(result, int)
        assert result == 100
    
    def test_convert_numpy_types_scalar_float(self):
        """Test 6: Convert numpy scalar float"""
        val = np.float64(2.718)
        result = StrategyManager._convert_numpy_types(val)
        assert isinstance(result, float)
        assert abs(result - 2.718) < 0.001
    
    def test_convert_numpy_types_scalar_bool(self):
        """Test 7: Convert numpy scalar bool"""
        val = np.bool_(False)
        result = StrategyManager._convert_numpy_types(val)
        assert isinstance(result, bool)
        assert result == False
    
    def test_convert_numpy_types_nested_complex(self):
        """Test 8: Convert complex nested structure"""
        data = {
            'arrays': [np.array([1, 2]), np.array([3.5, 4.5])],
            'mixed': (np.int16(5), np.float32(6.0))
        }
        result = StrategyManager._convert_numpy_types(data)
        assert result['arrays'][0] == [1, 2]
        assert abs(result['arrays'][1][0] - 3.5) < 0.01


class TestStrategyTypeDetection:
    """Test 9-15: Strategy type detection"""
    
    def test_get_strategy_type_moving_average_crossover(self):
        """Test 9: Detect MovingAverageCrossover strategy"""
        mock_strategy = Mock()
        mock_strategy.__class__.__name__ = 'MovingAverageCrossover'
        result = StrategyManager._get_strategy_type(mock_strategy)
        assert result == 'MA'
    
    def test_get_strategy_type_rsi(self):
        """Test 10: Detect RSI strategy"""
        mock_strategy = Mock()
        mock_strategy.__class__.__name__ = 'RSIStrategy'
        result = StrategyManager._get_strategy_type(mock_strategy)
        assert result == 'RSI'
    
    def test_get_strategy_type_multi_indicator(self):
        """Test 11: Detect MultiIndicatorStrategy"""
        mock_strategy = Mock()
        mock_strategy.__class__.__name__ = 'MultiIndicatorStrategy'
        result = StrategyManager._get_strategy_type(mock_strategy)
        assert result == 'Multi'
    
    def test_get_strategy_type_enhanced_ma(self):
        """Test 12: Detect EnhancedMovingAverageStrategy"""
        mock_strategy = Mock()
        mock_strategy.__class__.__name__ = 'EnhancedMovingAverageStrategy'
        result = StrategyManager._get_strategy_type(mock_strategy)
        assert result == 'EnhancedMA'
    
    def test_get_strategy_type_unknown(self):
        """Test 13: Unknown strategy returns class name"""
        mock_strategy = Mock()
        mock_strategy.__class__.__name__ = 'UnknownStrategy'
        result = StrategyManager._get_strategy_type(mock_strategy)
        assert result == 'UnknownStrategy'


class TestCreateStrategyModel:
    """Test 14-20: Strategy model creation"""
    
    def test_create_strategy_model_with_description(self):
        """Test 14: Create strategy model with custom description"""
        mock_strategy = Mock()
        mock_strategy.name = 'TestStrat'
        mock_strategy.__class__.__name__ = 'RSIStrategy'
        mock_strategy.parameters = {'period': 14}
        mock_strategy.description = 'Custom description'
        
        mock_backtest = Mock()
        mock_backtest.total_return = 15.5
        mock_backtest.symbol = 'AAPL'
        
        result = StrategyManager._create_strategy_model(mock_strategy, mock_backtest)
        assert result is not None
        assert result.name == 'TestStrat'
        assert 'Custom description' in result.description
    
    def test_create_strategy_model_default_description(self):
        """Test 15: Create strategy model with default description"""
        mock_strategy = Mock()
        mock_strategy.name = 'TestStrat2'
        mock_strategy.__class__.__name__ = 'MovingAverageCrossover'
        mock_strategy.parameters = {'fast': 10, 'slow': 20}
        mock_strategy.description = None
        
        mock_backtest = Mock()
        mock_backtest.total_return = -5.2
        mock_backtest.symbol = 'MSFT'
        
        result = StrategyManager._create_strategy_model(mock_strategy, mock_backtest)
        assert result is not None
        assert 'return' in result.description.lower()
        assert 'MSFT' in result.description
    
    def test_create_strategy_model_strategy_type(self):
        """Test 16: Strategy model gets correct type"""
        mock_strategy = Mock()
        mock_strategy.name = 'TestStrat3'
        mock_strategy.__class__.__name__ = 'MultiIndicatorStrategy'
        mock_strategy.parameters = {}
        mock_strategy.description = 'Test'
        
        mock_backtest = Mock()
        mock_backtest.total_return = 0
        mock_backtest.symbol = 'TEST'
        
        result = StrategyManager._create_strategy_model(mock_strategy, mock_backtest)
        assert result.strategy_type == 'Multi'
    
    def test_create_strategy_model_is_active_default(self):
        """Test 17: Strategy model is active by default"""
        mock_strategy = Mock()
        mock_strategy.name = 'TestStrat4'
        mock_strategy.__class__.__name__ = 'RSIStrategy'
        mock_strategy.parameters = {}
        mock_strategy.description = 'Test'
        
        mock_backtest = Mock()
        mock_backtest.total_return = 10
        mock_backtest.symbol = 'XYZ'
        
        result = StrategyManager._create_strategy_model(mock_strategy, mock_backtest)
        assert result.is_active == True


class TestStrategyManagerAdvanced:
    """Test 18-35: Advanced utility scenarios"""
    
    def test_convert_numpy_with_none(self):
        """Test 18: None values pass through unchanged"""
        result = StrategyManager._convert_numpy_types(None)
        assert result is None
    
    def test_convert_numpy_with_string(self):
        """Test 19: String values pass through unchanged"""
        result = StrategyManager._convert_numpy_types('test string')
        assert result == 'test string'
    
    def test_convert_numpy_deeply_nested(self):
        """Test 20: Deeply nested structures"""
        data = {
            'level1': {
                'level2': {
                    'level3': [np.int64(42), {'val': np.float32(3.14)}]
                }
            }
        }
        result = StrategyManager._convert_numpy_types(data)
        assert isinstance(result['level1']['level2']['level3'][0], int)
        assert isinstance(result['level1']['level2']['level3'][1]['val'], float)
    
    def test_convert_numpy_empty_containers(self):
        """Test 21: Empty containers"""
        assert StrategyManager._convert_numpy_types({}) == {}
        assert StrategyManager._convert_numpy_types([]) == []
        assert StrategyManager._convert_numpy_types(()) == []
    
    def test_convert_numpy_mixed_types(self):
        """Test 22: Mixed native and numpy types"""
        data = {
            'native_int': 5,
            'numpy_int': np.int64(10),
            'native_float': 3.14,
            'numpy_float': np.float32(2.71),
            'string': 'value'
        }
        result = StrategyManager._convert_numpy_types(data)
        assert result['native_int'] == 5
        assert result['numpy_int'] == 10
        assert isinstance(result['native_float'], float)
        assert isinstance(result['numpy_float'], float)
        assert result['string'] == 'value'
    
    def test_strategy_type_detection_case_sensitive(self):
        """Test 23: Strategy type detection is case-sensitive for class names"""
        mock_strategy = Mock()
        mock_strategy.__class__.__name__ = 'movingaveragecrossover'
        result = StrategyManager._get_strategy_type(mock_strategy)
        assert result == 'movingaveragecrossover'
    
    def test_create_strategy_with_numpy_parameters(self):
        """Test 24: Strategy model creation with numpy parameters"""
        mock_strategy = Mock()
        mock_strategy.name = 'NumpyStrat'
        mock_strategy.__class__.__name__ = 'RSIStrategy'
        mock_strategy.parameters = {
            'period': np.int64(14),
            'threshold': np.float32(70.0)
        }
        mock_strategy.description = 'Numpy params'
        
        mock_backtest = Mock()
        mock_backtest.total_return = 5.0
        mock_backtest.symbol = 'TEST'
        
        result = StrategyManager._create_strategy_model(mock_strategy, mock_backtest)
        assert result is not None
        params = json.loads(result.parameters)
        assert params['period'] == 14
        assert params['threshold'] == 70.0
    
    def test_multiple_strategy_detection(self):
        """Test 25: Multiple strategy types"""
        strategies = [
            ('MovingAverageCrossover', 'MA'),
            ('RSIStrategy', 'RSI'),
            ('MultiIndicatorStrategy', 'Multi'),
            ('EnhancedMovingAverageStrategy', 'EnhancedMA'),
            ('OtherStrategy', 'OtherStrategy')
        ]
        
        for class_name, expected_type in strategies:
            mock_strategy = Mock()
            mock_strategy.__class__.__name__ = class_name
            result = StrategyManager._get_strategy_type(mock_strategy)
            assert result == expected_type
    
    def test_convert_numpy_int8(self):
        """Test 26: Convert numpy int8"""
        val = np.int8(127)
        result = StrategyManager._convert_numpy_types(val)
        assert isinstance(result, int)
        assert result == 127
    
    def test_convert_numpy_int16(self):
        """Test 27: Convert numpy int16"""
        val = np.int16(32000)
        result = StrategyManager._convert_numpy_types(val)
        assert isinstance(result, int)
        assert result == 32000
    
    def test_convert_numpy_float16(self):
        """Test 28: Convert numpy float16"""
        val = np.float16(1.5)
        result = StrategyManager._convert_numpy_types(val)
        assert isinstance(result, float)
    
    def test_create_strategy_model_parameters_json(self):
        """Test 29: Strategy parameters are JSON-serializable"""
        mock_strategy = Mock()
        mock_strategy.name = 'JsonStrat'
        mock_strategy.__class__.__name__ = 'RSIStrategy'
        mock_strategy.parameters = {
            'period': 14,
            'list_param': [1, 2, 3],
            'nested': {'key': 'value'}
        }
        mock_strategy.description = 'JSON test'
        
        mock_backtest = Mock()
        mock_backtest.total_return = 0
        mock_backtest.symbol = 'JSON'
        
        result = StrategyManager._create_strategy_model(mock_strategy, mock_backtest)
        json.loads(result.parameters)
    
    def test_convert_numpy_tuple_conversion(self):
        """Test 30: Tuples are converted to lists"""
        data = (np.int64(1), np.int64(2), np.int64(3))
        result = StrategyManager._convert_numpy_types(data)
        assert isinstance(result, list)
        assert all(isinstance(x, int) for x in result)
    
    def test_convert_numpy_large_array(self):
        """Test 31: Handle large numpy arrays"""
        arr = np.arange(1000)
        result = StrategyManager._convert_numpy_types(arr)
        assert isinstance(result, list)
        assert len(result) == 1000
        assert result[0] == 0
        assert result[999] == 999
    
    def test_get_strategy_type_all_mapped_types(self):
        """Test 32: All mapped strategy types work correctly"""
        type_map = {
            'MovingAverageCrossover': 'MA',
            'RSIStrategy': 'RSI',
            'MultiIndicatorStrategy': 'Multi',
            'EnhancedMovingAverageStrategy': 'EnhancedMA'
        }
        
        for class_name, expected in type_map.items():
            mock = Mock()
            mock.__class__.__name__ = class_name
            assert StrategyManager._get_strategy_type(mock) == expected
    
    def test_convert_numpy_edge_numpy_types(self):
        """Test 33: Edge case numpy dtypes"""
        data = {
            'uint8': np.uint8(255),
            'uint16': np.uint16(65535),
            'uint32': np.uint32(4000000000),
            'uint64': np.uint64(18000000000000000000)
        }
        result = StrategyManager._convert_numpy_types(data)
        assert all(isinstance(v, int) for v in result.values())
    
    def test_create_strategy_model_all_fields_populated(self):
        """Test 34: All strategy model fields are populated"""
        mock_strategy = Mock()
        mock_strategy.name = 'CompleteStrat'
        mock_strategy.__class__.__name__ = 'MultiIndicatorStrategy'
        mock_strategy.parameters = {'p1': 1, 'p2': 2}
        mock_strategy.description = 'Complete test'
        
        mock_backtest = Mock()
        mock_backtest.total_return = 25.5
        mock_backtest.symbol = 'COMPLETE'
        
        result = StrategyManager._create_strategy_model(mock_strategy, mock_backtest)
        assert result.name == 'CompleteStrat'
        assert result.strategy_type == 'Multi'
        assert result.is_active == True
        assert 'Complete test' in result.description
    
    def test_convert_numpy_mixed_nested_structures(self):
        """Test 35: Complex nested structure with mixed types"""
        data = {
            'simple': np.int64(42),
            'list': [1, np.float32(2.5), 'string'],
            'dict': {'nested': np.int16(100), 'other': None},
            'tuple': (np.int32(5), np.float64(3.14), [np.int8(1)])
        }
        result = StrategyManager._convert_numpy_types(data)
        assert result['simple'] == 42
        assert isinstance(result['list'][1], float)
        assert result['dict']['nested'] == 100
        assert result['dict']['other'] is None
        assert isinstance(result['tuple'], list)
