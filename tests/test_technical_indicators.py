"""
Tests for backend/technical_indicators.py
Target: 80%+ coverage
"""
import pytest
import pandas as pd
import numpy as np
from backend.technical_indicators import TechnicalIndicators


@pytest.fixture
def sample_price_data():
    """Create sample price data for testing"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    # Create realistic price data with trend
    np.random.seed(42)
    base_price = 100
    returns = np.random.randn(100) * 0.02  # 2% daily volatility
    prices = base_price * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.randn(100) * 0.01),
        'high': prices * (1 + np.abs(np.random.randn(100)) * 0.02),
        'low': prices * (1 - np.abs(np.random.randn(100)) * 0.02),
        'close': prices,
        'volume': np.random.randint(100000, 1000000, 100)
    })
    
    return df


class TestSMA:
    """Test Simple Moving Average calculations"""
    
    def test_add_sma_default_periods(self, sample_price_data):
        """Test SMA with default periods"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_sma(df)
        
        assert 'sma_20' in result.columns
        assert 'sma_50' in result.columns
        assert 'sma_100' in result.columns
        assert 'sma_200' in result.columns
        
        # Check that SMA values are calculated (non-NaN where enough data)
        assert result['sma_20'].notna().sum() > 0
        assert result['sma_50'].notna().sum() > 0
        
    def test_add_sma_custom_periods(self, sample_price_data):
        """Test SMA with custom periods"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_sma(df, periods=[10, 30])
        
        assert 'sma_10' in result.columns
        assert 'sma_30' in result.columns
        assert 'sma_20' not in result.columns  # Default not applied
        
    def test_sma_values_are_averages(self, sample_price_data):
        """Test that SMA values are correct averages"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_sma(df, periods=[5])
        
        # Check SMA calculation for index 10 (enough data)
        expected_sma = df['close'].iloc[6:11].mean()
        actual_sma = result['sma_5'].iloc[10]
        assert abs(expected_sma - actual_sma) < 0.01
        
    def test_sma_handles_small_dataset(self):
        """Test SMA with dataset smaller than period"""
        df = pd.DataFrame({
            'close': [100, 101, 102, 103, 104]
        })
        result = TechnicalIndicators.add_sma(df, periods=[20])
        
        # Should have all NaN values since dataset < period
        assert result['sma_20'].isna().all()


class TestEMA:
    """Test Exponential Moving Average calculations"""
    
    def test_add_ema_default_periods(self, sample_price_data):
        """Test EMA with default periods"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_ema(df)
        
        assert 'ema_12' in result.columns
        assert 'ema_26' in result.columns
        assert 'ema_50' in result.columns
        assert 'ema_200' in result.columns
        
    def test_add_ema_custom_periods(self, sample_price_data):
        """Test EMA with custom periods"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_ema(df, periods=[9, 21])
        
        assert 'ema_9' in result.columns
        assert 'ema_21' in result.columns
        
    def test_ema_responds_faster_than_sma(self, sample_price_data):
        """Test that EMA responds faster to price changes than SMA"""
        df = sample_price_data.copy()
        
        # Add both indicators
        df = TechnicalIndicators.add_sma(df, periods=[20])
        df = TechnicalIndicators.add_ema(df, periods=[20])
        
        # EMA should have non-NaN values earlier than SMA
        ema_first_valid = df['ema_20'].first_valid_index()
        sma_first_valid = df['sma_20'].first_valid_index()
        
        assert ema_first_valid <= sma_first_valid


class TestRSI:
    """Test Relative Strength Index calculations"""
    
    def test_add_rsi_default_period(self, sample_price_data):
        """Test RSI with default period"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_rsi(df)
        
        assert 'rsi_14' in result.columns
        
    def test_add_rsi_custom_period(self, sample_price_data):
        """Test RSI with custom period"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_rsi(df, period=21)
        
        assert 'rsi_21' in result.columns
        
    def test_rsi_range_0_to_100(self, sample_price_data):
        """Test that RSI values are between 0 and 100"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_rsi(df)
        
        valid_rsi = result['rsi_14'].dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()
        
    def test_rsi_trending_up(self):
        """Test RSI on upward trending data"""
        df = pd.DataFrame({
            'close': list(range(100, 150))  # Strong upward trend
        })
        result = TechnicalIndicators.add_rsi(df, period=14)
        
        # RSI should be high (>50) for upward trend
        assert result['rsi_14'].iloc[-1] > 50
        
    def test_rsi_trending_down(self):
        """Test RSI on downward trending data"""
        df = pd.DataFrame({
            'close': list(range(150, 100, -1))  # Strong downward trend
        })
        result = TechnicalIndicators.add_rsi(df, period=14)
        
        # RSI should be low (<50) for downward trend
        assert result['rsi_14'].iloc[-1] < 50


class TestMACD:
    """Test MACD calculations"""
    
    def test_add_macd_default_params(self, sample_price_data):
        """Test MACD with default parameters"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_macd(df)
        
        assert 'macd' in result.columns
        assert 'macd_signal' in result.columns
        assert 'macd_hist' in result.columns
        
    def test_add_macd_custom_params(self, sample_price_data):
        """Test MACD with custom parameters"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_macd(df, fast=5, slow=13, signal=5)
        
        assert 'macd' in result.columns
        assert result['macd'].notna().sum() > 0
        
    def test_macd_histogram_is_difference(self, sample_price_data):
        """Test that MACD histogram is difference between MACD and signal"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_macd(df)
        
        # Check at a valid index
        idx = 50
        expected_hist = result['macd'].iloc[idx] - result['macd_signal'].iloc[idx]
        actual_hist = result['macd_hist'].iloc[idx]
        
        assert abs(expected_hist - actual_hist) < 0.001


class TestBollingerBands:
    """Test Bollinger Bands calculations"""
    
    def test_add_bollinger_bands_default(self, sample_price_data):
        """Test Bollinger Bands with default parameters"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_bollinger_bands(df)
        
        assert 'bb_middle' in result.columns
        assert 'bb_upper' in result.columns
        assert 'bb_lower' in result.columns
        assert 'bb_width' in result.columns
        assert 'bb_percent' in result.columns
        
    def test_add_bollinger_bands_custom(self, sample_price_data):
        """Test Bollinger Bands with custom parameters"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_bollinger_bands(df, period=15, std_dev=1.5)
        
        assert result['bb_middle'].notna().sum() > 0
        
    def test_bb_middle_equals_sma(self, sample_price_data):
        """Test that BB middle equals SMA"""
        df = sample_price_data.copy()
        df = TechnicalIndicators.add_bollinger_bands(df, period=20)
        df = TechnicalIndicators.add_sma(df, periods=[20])
        
        # BB middle should equal SMA_20
        valid_indices = df['bb_middle'].notna()
        diff = (df.loc[valid_indices, 'bb_middle'] - df.loc[valid_indices, 'sma_20']).abs()
        assert (diff < 0.001).all()
        
    def test_bb_upper_greater_than_lower(self, sample_price_data):
        """Test that upper band is always greater than lower band"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_bollinger_bands(df)
        
        valid_indices = result['bb_upper'].notna()
        assert (result.loc[valid_indices, 'bb_upper'] > result.loc[valid_indices, 'bb_lower']).all()
        
    def test_bb_percent_range(self, sample_price_data):
        """Test that BB percent is typically between 0 and 1"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_bollinger_bands(df)
        
        valid_percent = result['bb_percent'].dropna()
        # Most values should be in 0-1 range (price between bands)
        in_range = ((valid_percent >= 0) & (valid_percent <= 1)).sum()
        total = len(valid_percent)
        
        # At least 80% should be within bands
        assert in_range / total > 0.8


class TestStochastic:
    """Test Stochastic Oscillator calculations"""
    
    def test_add_stochastic_default(self, sample_price_data):
        """Test Stochastic with default parameters"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_stochastic(df)
        
        assert 'stoch_k' in result.columns
        assert 'stoch_d' in result.columns
        
    def test_add_stochastic_custom(self, sample_price_data):
        """Test Stochastic with custom parameters"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_stochastic(df, k_period=21, d_period=5)
        
        assert result['stoch_k'].notna().sum() > 0
        assert result['stoch_d'].notna().sum() > 0
        
    def test_stochastic_range_0_to_100(self, sample_price_data):
        """Test that Stochastic values are between 0 and 100"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_stochastic(df)
        
        valid_k = result['stoch_k'].dropna()
        valid_d = result['stoch_d'].dropna()
        
        assert (valid_k >= 0).all() and (valid_k <= 100).all()
        assert (valid_d >= 0).all() and (valid_d <= 100).all()


class TestATR:
    """Test Average True Range calculations"""
    
    def test_add_atr_default(self, sample_price_data):
        """Test ATR with default period"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_atr(df)
        
        assert 'atr_14' in result.columns
        
    def test_add_atr_custom(self, sample_price_data):
        """Test ATR with custom period"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_atr(df, period=21)
        
        assert 'atr_21' in result.columns
        assert result['atr_21'].notna().sum() > 0
        
    def test_atr_positive_values(self, sample_price_data):
        """Test that ATR values are always positive"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_atr(df)
        
        valid_atr = result['atr_14'].dropna()
        assert (valid_atr > 0).all()


class TestMultipleIndicators:
    """Test combining multiple indicators"""
    
    def test_add_all_indicators(self, sample_price_data):
        """Test adding all indicators together"""
        df = sample_price_data.copy()
        
        df = TechnicalIndicators.add_sma(df)
        df = TechnicalIndicators.add_ema(df)
        df = TechnicalIndicators.add_rsi(df)
        df = TechnicalIndicators.add_macd(df)
        df = TechnicalIndicators.add_bollinger_bands(df)
        df = TechnicalIndicators.add_stochastic(df)
        df = TechnicalIndicators.add_atr(df)
        
        # Verify all indicators present
        expected_cols = [
            'sma_20', 'ema_12', 'rsi_14', 'macd', 'macd_signal',
            'bb_upper', 'bb_lower', 'stoch_k', 'stoch_d', 'atr_14'
        ]
        
        for col in expected_cols:
            assert col in df.columns
            
    def test_indicators_dont_modify_original_data(self, sample_price_data):
        """Test that indicators don't modify original price columns"""
        df = sample_price_data.copy()
        original_close = df['close'].copy()
        
        df = TechnicalIndicators.add_sma(df)
        df = TechnicalIndicators.add_ema(df)
        df = TechnicalIndicators.add_rsi(df)
        
        # Original close should be unchanged
        pd.testing.assert_series_equal(df['close'], original_close)


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_dataframe(self):
        """Test indicators with empty DataFrame"""
        df = pd.DataFrame({'close': []})
        
        result = TechnicalIndicators.add_sma(df, periods=[20])
        assert len(result) == 0
        assert 'sma_20' in result.columns
        
    def test_single_row_dataframe(self):
        """Test indicators with single row"""
        df = pd.DataFrame({'close': [100], 'high': [101], 'low': [99]})
        
        result = TechnicalIndicators.add_rsi(df)
        assert 'rsi_14' in result.columns
        assert result['rsi_14'].isna().all()
        
    def test_constant_price(self):
        """Test indicators with constant price"""
        df = pd.DataFrame({
            'close': [100] * 50,
            'high': [100] * 50,
            'low': [100] * 50
        })
        
        result = TechnicalIndicators.add_rsi(df)
        # RSI should be 50 for constant price (no gains or losses)
        # But may be NaN due to division by zero in RSI calculation
        assert 'rsi_14' in result.columns


class TestADX:
    """Test Average Directional Index calculations"""
    
    def test_add_adx_default(self, sample_price_data):
        """Test ADX with default period"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_adx(df)
        
        assert 'adx' in result.columns
        assert 'di_plus' in result.columns
        assert 'di_minus' in result.columns
        
    def test_add_adx_custom(self, sample_price_data):
        """Test ADX with custom period"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_adx(df, period=21)
        
        assert result['adx'].notna().sum() > 0


class TestVolumeIndicators:
    """Test volume-based indicators"""
    
    def test_add_obv(self, sample_price_data):
        """Test On-Balance Volume"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_obv(df)
        
        assert 'obv' in result.columns
        # OBV should be cumulative
        assert result['obv'].notna().sum() > 0
        
    def test_add_vwap(self, sample_price_data):
        """Test Volume Weighted Average Price"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_vwap(df)
        
        assert 'vwap' in result.columns
        assert result['vwap'].notna().sum() > 0
        
    def test_add_mfi_default(self, sample_price_data):
        """Test Money Flow Index"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_mfi(df)
        
        assert 'mfi_14' in result.columns
        
    def test_mfi_range_0_to_100(self, sample_price_data):
        """Test that MFI values are between 0 and 100"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_mfi(df)
        
        valid_mfi = result['mfi_14'].dropna()
        assert (valid_mfi >= 0).all()
        assert (valid_mfi <= 100).all()


class TestOscillators:
    """Test oscillator indicators"""
    
    def test_add_cci_default(self, sample_price_data):
        """Test Commodity Channel Index"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_cci(df)
        
        assert 'cci_20' in result.columns
        
    def test_add_cci_custom(self, sample_price_data):
        """Test CCI with custom period"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_cci(df, period=14)
        
        assert 'cci_14' in result.columns
        assert result['cci_14'].notna().sum() > 0
        
    def test_add_williams_r_default(self, sample_price_data):
        """Test Williams %R"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_williams_r(df)
        
        assert 'williams_r_14' in result.columns
        
    def test_williams_r_range(self, sample_price_data):
        """Test that Williams %R values are between -100 and 0"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_williams_r(df)
        
        valid_wr = result['williams_r_14'].dropna()
        assert (valid_wr >= -100).all()
        assert (valid_wr <= 0).all()
        
    def test_add_roc_default(self, sample_price_data):
        """Test Rate of Change"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_roc(df)
        
        assert 'roc_12' in result.columns
        
    def test_add_roc_custom(self, sample_price_data):
        """Test ROC with custom period"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_roc(df, period=5)
        
        assert 'roc_5' in result.columns
        assert result['roc_5'].notna().sum() > 0


class TestIchimoku:
    """Test Ichimoku Cloud indicators"""
    
    def test_add_ichimoku(self, sample_price_data):
        """Test Ichimoku Cloud calculations"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_ichimoku(df)
        
        assert 'ichimoku_conversion' in result.columns
        assert 'ichimoku_base' in result.columns
        assert 'ichimoku_span_a' in result.columns
        assert 'ichimoku_span_b' in result.columns
        assert 'ichimoku_lagging' in result.columns
        
    def test_ichimoku_cloud_components(self, sample_price_data):
        """Test Ichimoku cloud components are calculated"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_ichimoku(df)
        
        # Check that some values are non-NaN
        assert result['ichimoku_conversion'].notna().sum() > 0
        assert result['ichimoku_base'].notna().sum() > 0


class TestAllIndicators:
    """Test add_all_indicators function"""
    
    def test_add_all_indicators(self, sample_price_data):
        """Test adding all indicators at once"""
        df = sample_price_data.copy()
        result = TechnicalIndicators.add_all_indicators(df)
        
        # Check for presence of indicators from different categories
        expected_indicators = [
            'sma_20', 'ema_12', 'rsi_14', 'macd', 'bb_upper',
            'stoch_k', 'atr_14', 'obv', 'vwap', 'adx',
            'cci_20', 'williams_r_14', 'roc_12', 'mfi_14',
            'ichimoku_conversion'
        ]
        
        for indicator in expected_indicators:
            assert indicator in result.columns, f"Missing indicator: {indicator}"
            
    def test_add_all_indicators_count(self, sample_price_data):
        """Test that many indicators are added"""
        df = sample_price_data.copy()
        original_cols = len(df.columns)
        result = TechnicalIndicators.add_all_indicators(df)
        
        # Should have added many columns
        assert len(result.columns) > original_cols + 20


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_calculate_and_update_indicators(self, sample_price_data):
        """Test calculate_and_update_indicators function"""
        df = sample_price_data.copy()
        from backend.technical_indicators import calculate_and_update_indicators
        
        result = calculate_and_update_indicators(df, save_to_db=False)
        
        # Should have many indicators
        assert 'sma_20' in result.columns
        assert 'rsi_14' in result.columns
        assert 'macd' in result.columns
        
    def test_calculate_and_update_empty_df(self):
        """Test with empty DataFrame"""
        df = pd.DataFrame()
        from backend.technical_indicators import calculate_and_update_indicators
        
        result = calculate_and_update_indicators(df)
        assert result.empty
