"""
Trading strategy implementations
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from backend.config import logger


class BaseStrategy:
    """Base class for trading strategies"""
    
    def __init__(self, name: str, parameters: Dict[str, Any] = None):
        self.name = name
        self.parameters = parameters or {}
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        """
        Generate trading signal
        
        Args:
            data: DataFrame with OHLCV and indicators
            
        Returns:
            'BUY', 'SELL', or 'HOLD'
        """
        raise NotImplementedError("Subclasses must implement generate_signal")


class MomentumStrategy(BaseStrategy):
    """Simple momentum strategy based on RSI"""
    
    def __init__(self, rsi_oversold: int = 30, rsi_overbought: int = 70):
        super().__init__(
            name="Momentum RSI",
            parameters={
                'rsi_oversold': rsi_oversold,
                'rsi_overbought': rsi_overbought
            }
        )
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < 2 or 'rsi_14' not in data.columns:
            return 'HOLD'
        
        current_rsi = data['rsi_14'].iloc[-1]
        
        # Buy when RSI crosses above oversold level
        if current_rsi < self.parameters['rsi_oversold']:
            return 'BUY'
        
        # Sell when RSI crosses above overbought level
        if current_rsi > self.parameters['rsi_overbought']:
            return 'SELL'
        
        return 'HOLD'


class MovingAverageCrossStrategy(BaseStrategy):
    """Moving average crossover strategy"""
    
    def __init__(self, fast_period: int = 20, slow_period: int = 50):
        super().__init__(
            name="MA Crossover",
            parameters={
                'fast_period': fast_period,
                'slow_period': slow_period
            }
        )
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < 2:
            return 'HOLD'
        
        fast_col = f'sma_{self.parameters["fast_period"]}'
        slow_col = f'sma_{self.parameters["slow_period"]}'
        
        if fast_col not in data.columns or slow_col not in data.columns:
            return 'HOLD'
        
        current_fast = data[fast_col].iloc[-1]
        current_slow = data[slow_col].iloc[-1]
        previous_fast = data[fast_col].iloc[-2]
        previous_slow = data[slow_col].iloc[-2]
        
        # Golden cross: fast MA crosses above slow MA
        if previous_fast <= previous_slow and current_fast > current_slow:
            return 'BUY'
        
        # Death cross: fast MA crosses below slow MA
        if previous_fast >= previous_slow and current_fast < current_slow:
            return 'SELL'
        
        return 'HOLD'


class MACDStrategy(BaseStrategy):
    """MACD crossover strategy"""
    
    def __init__(self):
        super().__init__(name="MACD Crossover")
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < 2 or 'macd' not in data.columns or 'macd_signal' not in data.columns:
            return 'HOLD'
        
        current_macd = data['macd'].iloc[-1]
        current_signal = data['macd_signal'].iloc[-1]
        previous_macd = data['macd'].iloc[-2]
        previous_signal = data['macd_signal'].iloc[-2]
        
        # MACD crosses above signal line
        if previous_macd <= previous_signal and current_macd > current_signal:
            return 'BUY'
        
        # MACD crosses below signal line
        if previous_macd >= previous_signal and current_macd < current_signal:
            return 'SELL'
        
        return 'HOLD'


class BollingerBandsStrategy(BaseStrategy):
    """Bollinger Bands mean reversion strategy"""
    
    def __init__(self):
        super().__init__(name="Bollinger Bands")
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < 2:
            return 'HOLD'
        
        if 'bb_lower' not in data.columns or 'bb_upper' not in data.columns:
            return 'HOLD'
        
        current_close = data['close'].iloc[-1]
        bb_lower = data['bb_lower'].iloc[-1]
        bb_upper = data['bb_upper'].iloc[-1]
        bb_middle = data['bb_middle'].iloc[-1]
        
        # Buy when price touches lower band
        if current_close <= bb_lower:
            return 'BUY'
        
        # Sell when price reaches middle or upper band
        if current_close >= bb_middle:
            return 'SELL'
        
        return 'HOLD'


class MultiIndicatorStrategy(BaseStrategy):
    """Strategy combining multiple indicators"""
    
    def __init__(self):
        super().__init__(name="Multi-Indicator")
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < 2:
            return 'HOLD'
        
        signals = []
        
        # RSI signal
        if 'rsi_14' in data.columns:
            rsi = data['rsi_14'].iloc[-1]
            if rsi < 30:
                signals.append(1)  # Buy signal
            elif rsi > 70:
                signals.append(-1)  # Sell signal
            else:
                signals.append(0)
        
        # MACD signal
        if 'macd' in data.columns and 'macd_signal' in data.columns:
            macd = data['macd'].iloc[-1]
            macd_signal = data['macd_signal'].iloc[-1]
            if macd > macd_signal:
                signals.append(1)
            elif macd < macd_signal:
                signals.append(-1)
            else:
                signals.append(0)
        
        # Moving average signal
        if 'sma_20' in data.columns and 'sma_50' in data.columns:
            sma_20 = data['sma_20'].iloc[-1]
            sma_50 = data['sma_50'].iloc[-1]
            if sma_20 > sma_50:
                signals.append(1)
            elif sma_20 < sma_50:
                signals.append(-1)
            else:
                signals.append(0)
        
        # Aggregate signals
        if not signals:
            return 'HOLD'
        
        avg_signal = np.mean(signals)
        
        # Buy if majority of indicators are bullish
        if avg_signal > 0.5:
            return 'BUY'
        # Sell if majority of indicators are bearish
        elif avg_signal < -0.5:
            return 'SELL'
        
        return 'HOLD'


class TrendFollowingStrategy(BaseStrategy):
    """Trend following strategy using ADX and moving averages"""
    
    def __init__(self, adx_threshold: int = 25):
        super().__init__(
            name="Trend Following",
            parameters={'adx_threshold': adx_threshold}
        )
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < 2:
            return 'HOLD'
        
        # Check if we have a strong trend (ADX > threshold)
        if 'adx' in data.columns:
            adx = data['adx'].iloc[-1]
            if adx < self.parameters['adx_threshold']:
                return 'HOLD'  # No strong trend
        
        # Use EMA crossover in trending market
        if 'ema_12' in data.columns and 'ema_26' in data.columns:
            ema_12 = data['ema_12'].iloc[-1]
            ema_26 = data['ema_26'].iloc[-1]
            prev_ema_12 = data['ema_12'].iloc[-2]
            prev_ema_26 = data['ema_26'].iloc[-2]
            
            # Bullish crossover
            if prev_ema_12 <= prev_ema_26 and ema_12 > ema_26:
                return 'BUY'
            
            # Bearish crossover
            if prev_ema_12 >= prev_ema_26 and ema_12 < ema_26:
                return 'SELL'
        
        return 'HOLD'


class MeanReversionStrategy(BaseStrategy):
    """Mean reversion strategy using Bollinger Bands and RSI"""
    
    def __init__(self, rsi_oversold: int = 25, rsi_overbought: int = 75):
        super().__init__(
            name="Mean Reversion",
            parameters={
                'rsi_oversold': rsi_oversold,
                'rsi_overbought': rsi_overbought
            }
        )
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < 2:
            return 'HOLD'
        
        buy_signals = 0
        sell_signals = 0
        
        # RSI condition
        if 'rsi_14' in data.columns:
            rsi = data['rsi_14'].iloc[-1]
            if rsi < self.parameters['rsi_oversold']:
                buy_signals += 1
            elif rsi > self.parameters['rsi_overbought']:
                sell_signals += 1
        
        # Bollinger Bands condition
        if 'bb_lower' in data.columns and 'bb_upper' in data.columns:
            close = data['close'].iloc[-1]
            bb_lower = data['bb_lower'].iloc[-1]
            bb_upper = data['bb_upper'].iloc[-1]
            
            # Price touches lower band
            if close <= bb_lower * 1.01:  # 1% tolerance
                buy_signals += 1
            # Price touches upper band
            elif close >= bb_upper * 0.99:  # 1% tolerance
                sell_signals += 1
        
        # Need confirmation from multiple indicators
        if buy_signals >= 2:
            return 'BUY'
        elif sell_signals >= 2:
            return 'SELL'
        
        return 'HOLD'


# Strategy registry
STRATEGIES = {
    'momentum': MomentumStrategy,
    'ma_crossover': MovingAverageCrossStrategy,
    'macd': MACDStrategy,
    'bollinger_bands': BollingerBandsStrategy,
    'multi_indicator': MultiIndicatorStrategy,
    'trend_following': TrendFollowingStrategy,
    'mean_reversion': MeanReversionStrategy,
}


def get_strategy(strategy_name: str, **kwargs) -> BaseStrategy:
    """
    Get strategy instance by name
    
    Args:
        strategy_name: Name of the strategy
        **kwargs: Strategy parameters
        
    Returns:
        Strategy instance
    """
    if strategy_name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy_name}. Available: {list(STRATEGIES.keys())}")
    
    return STRATEGIES[strategy_name](**kwargs)


if __name__ == "__main__":
    # Test strategies
    dates = pd.date_range('2024-01-01', periods=100, freq='1H')
    df = pd.DataFrame({
        'close': np.random.randn(100).cumsum() + 100,
        'rsi_14': np.random.uniform(20, 80, 100),
        'sma_20': np.random.randn(100).cumsum() + 99,
        'sma_50': np.random.randn(100).cumsum() + 98,
    }, index=dates)
    
    # Test momentum strategy
    strategy = get_strategy('momentum')
    signal = strategy.generate_signal(df)
    print(f"Momentum strategy signal: {signal}")
    
    # Test MA crossover
    strategy = get_strategy('ma_crossover', fast_period=20, slow_period=50)
    signal = strategy.generate_signal(df)
    print(f"MA Crossover signal: {signal}")
