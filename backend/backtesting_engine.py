"""Backtesting Engine for trading strategies"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
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
        """Convert to dictionary with proper JSON serialization"""
        result = asdict(self)
        
        # Convert datetime objects to ISO format strings
        result["start_date"] = self.start_date.isoformat() if self.start_date else None
        result["end_date"] = self.end_date.isoformat() if self.end_date else None
        
        # Convert trade dates to ISO format
        if result.get("trades"):
            for trade in result["trades"]:
                if "entry_date" in trade and trade["entry_date"]:
                    # Handle both datetime and Timestamp objects
                    trade["entry_date"] = trade["entry_date"].isoformat() if hasattr(trade["entry_date"], 'isoformat') else str(trade["entry_date"])
                if "exit_date" in trade and trade["exit_date"]:
                    trade["exit_date"] = trade["exit_date"].isoformat() if hasattr(trade["exit_date"], 'isoformat') else str(trade["exit_date"])
        
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
    
    def to_dict(self) -> Dict:
        """Convert strategy to dictionary"""
        return {
            "name": self.name,
            "parameters": self.parameters
        }


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
    
    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.001, 
                 allow_short: bool = False, min_hold_minutes: int = 1):
        """Initialize backtesting engine
        
        Args:
            initial_capital: Starting capital for backtest
            commission: Commission per trade (decimal, e.g., 0.001 for 0.1%)
            allow_short: Whether to allow short positions
            min_hold_minutes: Minimum minutes to hold a position
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.allow_short = allow_short
        self.min_hold_minutes = min_hold_minutes
    
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
    
    def run_parallel_optimization(self, df: pd.DataFrame, symbol: str, num_iterations: int = 100,
                                 target_return: float = 0.0, num_processes: Optional[int] = None,
                                 progress_callback: Optional[Callable] = None) -> Tuple[Optional[Strategy], Optional[BacktestResult], List[BacktestResult]]:
        """
        Run parallel optimization of trading strategies (sequential fallback if multiprocessing unavailable)
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Stock symbol
            num_iterations: Number of strategies to test
            target_return: Target return (not used, for compatibility)
            num_processes: Number of processes (None = auto-detect)
            progress_callback: Callback for progress (not used)
            
        Returns:
            Tuple of (best_strategy, best_result, all_results)
        """
        generator = StrategyGenerator(target_return=target_return)
        all_results = []
        best_result = None
        best_strategy = None
        best_return = -np.inf
        
        # Run sequential optimization (simple version)
        for i in range(num_iterations):
            try:
                # Generate random strategy
                strategy = generator.generate()
                
                # Run backtest
                result = self.run(strategy, df, symbol)
                all_results.append(result)
                
                # Track best result
                if result.total_return > best_return:
                    best_return = result.total_return
                    best_result = result
                    best_strategy = strategy
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(i + 1, num_iterations, best_return)
                
                # Log progress
                if (i + 1) % 10 == 0:
                    logger.info(f"[{i + 1}/{num_iterations}] Best return: {best_return:.2f}%")
            
            except Exception as e:
                logger.warning(f"Error in iteration {i}: {e}")
                continue
        
        logger.info(f"Optimization complete. Best return: {best_return:.2f}%")
        return best_strategy, best_result, all_results


# Aliases for backward compatibility
MovingAverageCrossover = SimpleMovingAverageStrategy
MultiIndicatorStrategy = EnhancedMovingAverageStrategy


