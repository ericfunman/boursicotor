"""
Unit tests for backend constants
"""
import pytest
from backend.constants import (
    CONST_TIMESTAMP,
    CONST_CLOSE,
    CONST_VOLUME,
    CONST_1MIN,
    CONST_5MIN,
    CONST_1HOUR,
    CONST_1DAY,
    STATUS_ACTIVE,
    STATUS_INACTIVE,
    ACTION_BUY,
    ACTION_SELL,
    ORDER_TYPE_MARKET,
    ORDER_TYPE_LIMIT,
)


class TestDataFrameColumnConstants:
    """Test DataFrame column name constants"""
    
    def test_timestamp_constant(self):
        """Test CONST_TIMESTAMP is defined"""
        assert CONST_TIMESTAMP is not None
        assert isinstance(CONST_TIMESTAMP, str)
        assert CONST_TIMESTAMP == "timestamp"
    
    def test_close_constant(self):
        """Test CONST_CLOSE is defined"""
        assert CONST_CLOSE is not None
        assert isinstance(CONST_CLOSE, str)
    
    def test_volume_constant(self):
        """Test CONST_VOLUME is defined"""
        assert CONST_VOLUME is not None
        assert isinstance(CONST_VOLUME, str)


class TestTimeIntervalConstants:
    """Test time interval constants"""
    
    def test_1min_constant(self):
        """Test CONST_1MIN is defined"""
        assert CONST_1MIN is not None
        assert isinstance(CONST_1MIN, str)
        assert CONST_1MIN == "1min"
    
    def test_5min_constant(self):
        """Test CONST_5MIN is defined"""
        assert CONST_5MIN is not None
        assert isinstance(CONST_5MIN, str)
    
    def test_1hour_constant(self):
        """Test CONST_1HOUR is defined"""
        assert CONST_1HOUR is not None
        assert isinstance(CONST_1HOUR, str)
    
    def test_1day_constant(self):
        """Test CONST_1DAY is defined"""
        assert CONST_1DAY is not None
        assert isinstance(CONST_1DAY, str)


class TestStatusConstants:
    """Test status constants"""
    
    def test_status_active(self):
        """Test STATUS_ACTIVE constant"""
        assert STATUS_ACTIVE is not None
        assert isinstance(STATUS_ACTIVE, str)
        assert STATUS_ACTIVE == "ACTIVE"
    
    def test_status_inactive(self):
        """Test STATUS_INACTIVE constant"""
        assert STATUS_INACTIVE is not None
        assert isinstance(STATUS_INACTIVE, str)
        assert STATUS_INACTIVE == "INACTIVE"


class TestActionConstants:
    """Test action constants"""
    
    def test_action_buy(self):
        """Test ACTION_BUY constant"""
        assert ACTION_BUY is not None
        assert isinstance(ACTION_BUY, str)
        assert ACTION_BUY == "BUY"
    
    def test_action_sell(self):
        """Test ACTION_SELL constant"""
        assert ACTION_SELL is not None
        assert isinstance(ACTION_SELL, str)
        assert ACTION_SELL == "SELL"


class TestOrderTypeConstants:
    """Test order type constants"""
    
    def test_order_type_market(self):
        """Test ORDER_TYPE_MARKET constant"""
        assert ORDER_TYPE_MARKET is not None
        assert isinstance(ORDER_TYPE_MARKET, str)
        assert ORDER_TYPE_MARKET == "MARKET"
    
    def test_order_type_limit(self):
        """Test ORDER_TYPE_LIMIT constant"""
        assert ORDER_TYPE_LIMIT is not None
        assert isinstance(ORDER_TYPE_LIMIT, str)
        assert ORDER_TYPE_LIMIT == "LIMIT"


class TestAllConstantsExist:
    """Test that all expected constants are defined"""
    
    def test_all_constants_are_strings(self):
        """Test that all constants are strings"""
        constants = [
            CONST_TIMESTAMP,
            CONST_CLOSE,
            CONST_VOLUME,
            CONST_1MIN,
            STATUS_ACTIVE,
            ACTION_BUY,
            ORDER_TYPE_MARKET,
        ]
        for const in constants:
            assert isinstance(const, str)
            assert len(const) > 0
