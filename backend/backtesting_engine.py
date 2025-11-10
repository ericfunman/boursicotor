"""Backtesting Engine for trading strategies"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Backtesting result"""
    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    trades: List[Dict]
    
    def to_dict(self):
        """Convert to dictionary"""
        result = asdict(self)
        result["start_date"] = self.start_date.isoformat() if self.start_date else None
        result["end_date"] = self.end_date.isoformat() if self.end_date else None
        return result


class Strategy:
    """Base strategy class"""
    
    def __init__(self, name: str, parameters: Dict):
        """Initialize strategy"""
        self.name = name
        self.parameters = parameters
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate buy/sell signals"""
        raise NotImplementedError()


class SimpleMovingAverageStrategy(Strategy):
    """SMA Crossover Strategy"""
    
    def __init__(self, fast=10, slow=30):
        """Initialize"""
        super().__init__("SimpleMovingAverage", {
            "fast_period": fast,
            "slow_period": slow
        })
        self.fast_period = fast
        self.slow_period = slow
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate signals"""
        fast_ma = df["close"].rolling(window=self.fast_period).mean()
        slow_ma = df["close"].rolling(window=self.slow_period).mean()
        
        signals = pd.Series(0, index=df.index)
        signals[fast_ma > slow_ma] = 1
        signals[fast_ma < slow_ma] = -1
        
        return signals


class RSIStrategy(Strategy):
    """RSI Strategy"""
    
    def __init__(self, period=14, oversold=30, overbought=70):
        """Initialize"""
        super().__init__("RSIStrategy", {
            "period": period,
            "oversold": oversold,
            "overbought": overbought
        })
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate signals"""
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        signals = pd.Series(0, index=df.index)
        signals[rsi < self.oversold] = 1
        signals[rsi > self.overbought] = -1
        
        return signals


class EnhancedMovingAverageStrategy(Strategy):
    """Enhanced MA Strategy"""
    
    def __init__(self, fast_period=10, slow_period=30, rsi_period=14):
        """Initialize"""
        super().__init__("EnhancedMovingAverage", {
            "fast_period": fast_period,
            "slow_period": slow_period,
            "rsi_period": rsi_period
        })
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.rsi_period = rsi_period
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate signals"""
        fast_ma = df["close"].rolling(window=self.fast_period).mean()
        slow_ma = df["close"].rolling(window=self.slow_period).mean()
        
        signals = pd.Series(0, index=df.index)
        signals[fast_ma > slow_ma] = 1
        signals[fast_ma < slow_ma] = -1
        
        return signals
