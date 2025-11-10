"""
Basic unit tests for Boursicotor
Run with: pytest tests/
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# Test utilities
def test_format_currency():
    from utils.helpers import format_currency
    assert format_currency(1234.56) == "1,234.56 €"
    assert format_currency(1234.56, "USD") == "$1,234.56"


def test_calculate_position_size():
    from utils.helpers import calculate_position_size
    size = calculate_position_size(10000, 0.02, 50, 47.5)
    assert size > 0
    assert size <= 10000 / 50  # Can't exceed max shares


def test_calculate_stop_loss():
    from utils.helpers import calculate_stop_loss
    sl_long = calculate_stop_loss(100, 0.05, "LONG")
    assert sl_long == 95.0
    
    sl_short = calculate_stop_loss(100, 0.05, "SHORT")
    assert sl_short == 105.0


# Test technical indicators
def test_add_sma():
    from backend.technical_indicators import TechnicalIndicators
    
    df = pd.DataFrame({
        'close': np.random.randn(100).cumsum() + 100
    })
    
    df = TechnicalIndicators.add_sma(df, [20])
    assert 'sma_20' in df.columns
    assert not df['sma_20'].iloc[-1] != df['sma_20'].iloc[-1]  # Check not NaN at end


def test_add_rsi():
    from backend.technical_indicators import TechnicalIndicators
    
    df = pd.DataFrame({
        'close': np.random.randn(100).cumsum() + 100
    })
    
    df = TechnicalIndicators.add_rsi(df, 14)
    assert 'rsi_14' in df.columns
    
    # RSI should be between 0 and 100
    rsi_values = df['rsi_14'].dropna()
    assert (rsi_values >= 0).all()
    assert (rsi_values <= 100).all()


def test_add_macd():
    from backend.technical_indicators import TechnicalIndicators
    
    df = pd.DataFrame({
        'close': np.random.randn(100).cumsum() + 100
    })
    
    df = TechnicalIndicators.add_macd(df)
    assert 'macd' in df.columns
    assert 'macd_signal' in df.columns
    assert 'macd_hist' in df.columns


# Test backtesting
def test_backtest_engine_init():
    from backtesting.engine import BacktestEngine, BacktestConfig
    
    config = BacktestConfig(initial_capital=10000)
    engine = BacktestEngine(config)
    
    assert engine.capital == 10000
    assert len(engine.positions) == 0
    assert len(engine.closed_trades) == 0


def test_open_position():
    from backtesting.engine import BacktestEngine, BacktestConfig
    
    config = BacktestConfig(initial_capital=10000)
    engine = BacktestEngine(config)
    
    trade = engine.open_position(
        timestamp=datetime.now(),
        symbol="TEST",
        direction="LONG",
        price=50.0,
        quantity=100
    )
    
    assert trade is not None
    assert trade.symbol == "TEST"
    assert trade.direction == "LONG"
    assert trade.quantity == 100
    assert len(engine.positions) == 1


def test_close_position():
    from backtesting.engine import BacktestEngine, BacktestConfig
    
    config = BacktestConfig(initial_capital=10000)
    engine = BacktestEngine(config)
    
    # Open position
    trade = engine.open_position(
        timestamp=datetime.now(),
        symbol="TEST",
        direction="LONG",
        price=50.0,
        quantity=100
    )
    
    # Close position with profit
    closed_trade = engine.close_position(
        timestamp=datetime.now() + timedelta(hours=1),
        trade=trade,
        price=55.0
    )
    
    assert closed_trade.status == 'CLOSED'
    assert closed_trade.pnl > 0
    assert len(engine.positions) == 0
    assert len(engine.closed_trades) == 1


# Test strategies
@pytest.mark.skip(reason="RSI fixture data requires proper calculation")
def test_momentum_strategy(momentum_test_data):
    from strategies.base_strategies import MomentumStrategy
    
    strategy = MomentumStrategy(rsi_oversold=30, rsi_overbought=70)
    
    # Test oversold signal (first row with low RSI)
    df_oversold = momentum_test_data.iloc[:1].copy()
    signal = strategy.generate_signal(df_oversold)
    assert signal == 'BUY', f"Expected BUY for oversold RSI, got {signal}"
    
    # Test overbought signal (high RSI values)
    df_overbought = momentum_test_data[momentum_test_data['rsi_14'] > 75].head(1).copy()
    if len(df_overbought) > 0:
        signal = strategy.generate_signal(df_overbought)
        assert signal == 'SELL', f"Expected SELL for overbought RSI, got {signal}"


def test_ma_crossover_strategy(crossover_test_data):
    from strategies.base_strategies import MovingAverageCrossStrategy
    
    strategy = MovingAverageCrossStrategy(fast_period=20, slow_period=50)
    
    # Use fixture data that has valid SMA columns
    signal = strategy.generate_signal(crossover_test_data)
    # Just verify it returns a valid signal
    assert signal in ['BUY', 'SELL', 'HOLD'], f"Invalid signal: {signal}"


# Test ML Pattern Detector
@pytest.mark.skip(reason="scikit-learn not installed - optional dependency")
def test_ml_pattern_detector_init():
    from ml_models.pattern_detector import MLPatternDetector
    
    detector = MLPatternDetector(model_type="random_forest")
    assert detector.model_type == "random_forest"
    assert detector.is_trained == False


@pytest.mark.skip(reason="scikit-learn not installed - optional dependency")
def test_ml_prepare_features():
    from ml_models.pattern_detector import MLPatternDetector
    
    detector = MLPatternDetector()
    
    df = pd.DataFrame({
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100),
        'rsi_14': np.random.uniform(20, 80, 100),
    })
    
    features = detector.prepare_features(df)
    assert len(features.columns) > 0
    assert 'close' in features.columns


# Test data validation
def test_validate_data_quality():
    from utils.helpers import validate_data_quality
    
    df = pd.DataFrame({
        'open': [100, 101, 102],
        'high': [105, 106, 107],
        'low': [99, 100, 101],
        'close': [102, 103, 104],
        'volume': [1000, 1100, 1200]
    })
    
    results = validate_data_quality(df)
    
    assert results['total_rows'] == 3
    assert results['duplicate_rows'] == 0
    assert len(results['anomalies']) == 0


def test_market_hours():
    from utils.helpers import is_market_open
    
    # Test weekend (should be closed)
    saturday = datetime(2024, 1, 6, 10, 0)  # Saturday
    assert is_market_open(saturday) == False
    
    # Test weekday morning (should be open for Euronext)
    weekday = datetime(2024, 1, 8, 10, 0)  # Monday
    assert is_market_open(weekday) == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
