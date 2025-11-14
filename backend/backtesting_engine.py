"""Backtesting Engine for trading strategies"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import logging
from backend.constants import CONST_CLOSE

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
        fast_ma = df[CONST_CLOSE].rolling(window=self.fast_period).mean()
        slow_ma = df[CONST_CLOSE].rolling(window=self.slow_period).mean()
        
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
        delta = df[CONST_CLOSE].diff()
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
        fast_ma = df[CONST_CLOSE].rolling(window=self.fast_period).mean()
        slow_ma = df[CONST_CLOSE].rolling(window=self.slow_period).mean()
        
        signals = pd.Series(0, index=df.index)
        signals[fast_ma > slow_ma] = 1
        signals[fast_ma < slow_ma] = -1
        
        return signals


class StrategyGenerator:
    """Generate trading strategies"""
    
    def __init__(self, target_return: float = 0.0):
        """Initialize strategy generator"""
        self.target_return = target_return
    
    def generate(self) -> Strategy:
        """Generate a random strategy"""
        strategy_type = np.random.choice(['ma', 'rsi', 'enhanced'])
        
        if strategy_type == 'ma':
            return SimpleMovingAverageStrategy(
                fast=np.random.randint(5, 20),
                slow=np.random.randint(20, 50)
            )
        elif strategy_type == 'rsi':
            return RSIStrategy(
                period=np.random.randint(10, 20),
                oversold=np.random.randint(20, 35),
                overbought=np.random.randint(65, 80)
            )
        else:
            return EnhancedMovingAverageStrategy(
                fast_period=np.random.randint(5, 20),
                slow_period=np.random.randint(20, 50),
                rsi_period=np.random.randint(10, 20)
            )


class BacktestingEngine:
    """Backtesting engine for trading strategies"""
    
    def __init__(self, initial_capital: float = 10000.0):
        """Initialize backtesting engine"""
        self.initial_capital = initial_capital
    
    def run(self, strategy: Strategy, df: pd.DataFrame, symbol: str = "UNKNOWN") -> BacktestResult:
        """
        Run backtesting on a strategy
        
        Args:
            strategy: Strategy instance
            df: DataFrame with OHLCV data
            symbol: Stock symbol
            
        Returns:
            BacktestResult object
        """
        if df.empty:
            raise ValueError("DataFrame is empty")
        
        # Generate signals
        signals = strategy.generate_signals(df)
        
        # Initialize variables
        capital = self.initial_capital
        position = 0  # 0 = no position, 1 = long
        entry_price = 0
        trades = []
        prices = df[CONST_CLOSE].values
        
        # Simulate trading
        for i in range(len(signals)):
            signal = signals.iloc[i]
            price = prices[i]
            
            if signal == 1 and position == 0:
                # Buy signal
                position = 1
                entry_price = price
                entry_date = df.index[i]
            
            elif signal == -1 and position == 1:
                # Sell signal
                exit_price = price
                exit_date = df.index[i]
                profit = (exit_price - entry_price) * (capital / entry_price)
                capital += profit
                
                trades.append({
                    "entry_date": entry_date,
                    "exit_date": exit_date,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "profit": profit,
                    "profit_pct": (exit_price - entry_price) / entry_price * 100
                })
                
                position = 0
        
        # Close position if still open
        if position == 1:
            exit_price = prices[-1]
            exit_date = df.index[-1]
            profit = (exit_price - entry_price) * (capital / entry_price)
            capital += profit
            
            trades.append({
                "entry_date": entry_date,
                "exit_date": exit_date,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "profit": profit,
                "profit_pct": (exit_price - entry_price) / entry_price * 100
            })
        
        # Calculate metrics
        total_return = (capital - self.initial_capital) / self.initial_capital * 100
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t["profit"] > 0)
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown(prices)
        
        # Calculate Sharpe ratio
        sharpe_ratio = self._calculate_sharpe_ratio(prices)
        
        return BacktestResult(
            strategy_name=strategy.name,
            symbol=symbol,
            start_date=df.index[0],
            end_date=df.index[-1],
            initial_capital=self.initial_capital,
            final_capital=capital,
            total_return=total_return,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            trades=trades
        )
    
    @staticmethod
    def _calculate_max_drawdown(prices: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        cummax = np.maximum.accumulate(prices)
        drawdown = (prices - cummax) / cummax
        return float(np.min(drawdown) * 100)
    
    @staticmethod
    def _calculate_sharpe_ratio(prices: np.ndarray, risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio"""
        returns = np.diff(prices) / prices[:-1]
        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        
        if len(excess_returns) == 0 or np.std(excess_returns) == 0:
            return 0.0
        
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        return float(sharpe)


# Aliases for backward compatibility
MovingAverageCrossover = SimpleMovingAverageStrategy
MultiIndicatorStrategy = EnhancedMovingAverageStrategy


