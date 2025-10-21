"""
Backtesting Engine - Moteur de test de stratégies de trading
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json

from backend.config import logger
from backend.models import SessionLocal, Ticker, HistoricalData, Base
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean


@dataclass
class BacktestResult:
    """Résultat d'un backtest"""
    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float  # En pourcentage
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float  # En pourcentage
    max_drawdown: float  # En pourcentage
    sharpe_ratio: float
    trades: List[Dict]  # Liste des trades
    
    def to_dict(self):
        """Convert to dictionary"""
        result = asdict(self)
        result['start_date'] = self.start_date.isoformat() if self.start_date else None
        result['end_date'] = self.end_date.isoformat() if self.end_date else None
        return result


@dataclass
class Trade:
    """Représente un trade (achat/vente)"""
    entry_date: datetime
    entry_price: float
    exit_date: datetime
    exit_price: float
    quantity: int
    profit: float
    profit_pct: float
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'entry_date': self.entry_date.isoformat(),
            'entry_price': self.entry_price,
            'exit_date': self.exit_date.isoformat(),
            'exit_price': self.exit_price,
            'quantity': self.quantity,
            'profit': self.profit,
            'profit_pct': self.profit_pct
        }


class Strategy:
    """Classe de base pour les stratégies de trading"""
    
    def __init__(self, name: str, parameters: Dict):
        self.name = name
        self.parameters = parameters
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Génère les signaux d'achat/vente
        
        Returns:
            Series with values: 1 (buy), -1 (sell), 0 (hold)
        """
        raise NotImplementedError("Subclasses must implement generate_signals")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'name': self.name,
            'parameters': self.parameters
        }
    
    @staticmethod
    def from_dict(data: Dict):
        """Create strategy from dictionary"""
        if data['name'] == 'RandomStrategy':
            return RandomStrategy(**data['parameters'])
        elif data['name'] == 'MovingAverageCrossover':
            return MovingAverageCrossover(**data['parameters'])
        elif data['name'] == 'RSIStrategy':
            return RSIStrategy(**data['parameters'])
        elif data['name'] == 'MultiIndicatorStrategy':
            return MultiIndicatorStrategy(**data['parameters'])
        else:
            raise ValueError(f"Unknown strategy: {data['name']}")


class RandomStrategy(Strategy):
    """Stratégie aléatoire pour tester le moteur"""
    
    def __init__(self, seed: int = 42):
        super().__init__('RandomStrategy', {'seed': seed})
        self.seed = seed
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        np.random.seed(self.seed)
        signals = np.random.choice([0, 1, -1], size=len(df), p=[0.8, 0.1, 0.1])
        return pd.Series(signals, index=df.index)


class MovingAverageCrossover(Strategy):
    """Stratégie de croisement de moyennes mobiles"""
    
    def __init__(self, fast_period: int = 10, slow_period: int = 30):
        super().__init__('MovingAverageCrossover', {
            'fast_period': fast_period,
            'slow_period': slow_period
        })
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        # Calculate moving averages
        fast_ma = df['close'].rolling(window=self.fast_period).mean()
        slow_ma = df['close'].rolling(window=self.slow_period).mean()
        
        # Generate signals
        signals = pd.Series(0, index=df.index)
        signals[fast_ma > slow_ma] = 1  # Buy signal
        signals[fast_ma < slow_ma] = -1  # Sell signal
        
        # Only trigger on crossover
        signals = signals.diff()
        signals[signals > 0] = 1
        signals[signals < 0] = -1
        
        return signals


class RSIStrategy(Strategy):
    """Stratégie basée sur le RSI"""
    
    def __init__(self, rsi_period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__('RSIStrategy', {
            'rsi_period': rsi_period,
            'oversold': oversold,
            'overbought': overbought
        })
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Generate signals
        signals = pd.Series(0, index=df.index)
        signals[rsi < self.oversold] = 1  # Buy when oversold
        signals[rsi > self.overbought] = -1  # Sell when overbought
        
        return signals


class MultiIndicatorStrategy(Strategy):
    """Stratégie combinant plusieurs indicateurs"""
    
    def __init__(
        self,
        ma_fast: int = 10,
        ma_slow: int = 30,
        rsi_period: int = 14,
        rsi_oversold: int = 30,
        rsi_overbought: int = 70,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9
    ):
        super().__init__('MultiIndicatorStrategy', {
            'ma_fast': ma_fast,
            'ma_slow': ma_slow,
            'rsi_period': rsi_period,
            'rsi_oversold': rsi_oversold,
            'rsi_overbought': rsi_overbought,
            'macd_fast': macd_fast,
            'macd_slow': macd_slow,
            'macd_signal': macd_signal
        })
        self.ma_fast = ma_fast
        self.ma_slow = ma_slow
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        # Moving averages
        fast_ma = df['close'].rolling(window=self.ma_fast).mean()
        slow_ma = df['close'].rolling(window=self.ma_slow).mean()
        ma_signal = (fast_ma > slow_ma).astype(int) - (fast_ma < slow_ma).astype(int)
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_signal = (rsi < self.rsi_oversold).astype(int) - (rsi > self.rsi_overbought).astype(int)
        
        # MACD
        ema_fast = df['close'].ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=self.macd_slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()
        macd_signal = (macd_line > signal_line).astype(int) - (macd_line < signal_line).astype(int)
        
        # Combine signals (majority vote)
        combined = ma_signal + rsi_signal + macd_signal
        signals = pd.Series(0, index=df.index)
        signals[combined >= 2] = 1  # Buy if at least 2 indicators agree
        signals[combined <= -2] = -1  # Sell if at least 2 indicators agree
        
        return signals


class BacktestingEngine:
    """Moteur de backtesting"""
    
    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.001):
        """
        Args:
            initial_capital: Capital initial
            commission: Commission par trade (0.001 = 0.1%)
        """
        self.initial_capital = initial_capital
        self.commission = commission
    
    def run_backtest(
        self,
        df: pd.DataFrame,
        strategy: Strategy,
        symbol: str
    ) -> BacktestResult:
        """
        Exécute un backtest
        
        Args:
            df: DataFrame avec les données OHLCV
            strategy: Stratégie à tester
            symbol: Symbole du ticker
            
        Returns:
            Résultat du backtest
        """
        logger.info(f"🔄 Running backtest for {symbol} with strategy: {strategy.name}")
        
        # Generate signals
        signals = strategy.generate_signals(df)
        
        # Initialize
        capital = self.initial_capital
        position = 0  # Number of shares held
        trades = []
        equity_curve = [capital]
        
        entry_price = None
        entry_date = None
        
        # Simulate trading
        for i in range(len(df)):
            current_price = df['close'].iloc[i]
            current_date = df.index[i]
            signal = signals.iloc[i]
            
            # Buy signal
            if signal == 1 and position == 0:
                # Calculate shares to buy (use 95% of capital to keep some cash)
                shares_to_buy = int((capital * 0.95) / current_price)
                if shares_to_buy > 0:
                    cost = shares_to_buy * current_price * (1 + self.commission)
                    if cost <= capital:
                        position = shares_to_buy
                        capital -= cost
                        entry_price = current_price
                        entry_date = current_date
                        logger.debug(f"  BUY: {shares_to_buy} shares @ {current_price:.2f} on {current_date}")
            
            # Sell signal
            elif signal == -1 and position > 0:
                # Sell all shares
                revenue = position * current_price * (1 - self.commission)
                profit = revenue - (position * entry_price * (1 + self.commission))
                profit_pct = (profit / (position * entry_price)) * 100
                
                capital += revenue
                
                trade = Trade(
                    entry_date=entry_date,
                    entry_price=entry_price,
                    exit_date=current_date,
                    exit_price=current_price,
                    quantity=position,
                    profit=profit,
                    profit_pct=profit_pct
                )
                trades.append(trade)
                
                logger.debug(f"  SELL: {position} shares @ {current_price:.2f} on {current_date} | Profit: {profit:.2f}€ ({profit_pct:.2f}%)")
                
                position = 0
                entry_price = None
                entry_date = None
            
            # Update equity curve
            total_equity = capital + (position * current_price if position > 0 else 0)
            equity_curve.append(total_equity)
        
        # Close any remaining position
        if position > 0:
            current_price = df['close'].iloc[-1]
            current_date = df.index[-1]
            revenue = position * current_price * (1 - self.commission)
            profit = revenue - (position * entry_price * (1 + self.commission))
            profit_pct = (profit / (position * entry_price)) * 100
            
            capital += revenue
            
            trade = Trade(
                entry_date=entry_date,
                entry_price=entry_price,
                exit_date=current_date,
                exit_price=current_price,
                quantity=position,
                profit=profit,
                profit_pct=profit_pct
            )
            trades.append(trade)
            
            logger.debug(f"  CLOSE POSITION: {position} shares @ {current_price:.2f} | Profit: {profit:.2f}€ ({profit_pct:.2f}%)")
        
        # Calculate statistics
        final_capital = capital
        total_return = ((final_capital - self.initial_capital) / self.initial_capital) * 100
        
        winning_trades = sum(1 for t in trades if t.profit > 0)
        losing_trades = sum(1 for t in trades if t.profit <= 0)
        win_rate = (winning_trades / len(trades) * 100) if trades else 0
        
        # Max drawdown
        equity_series = pd.Series(equity_curve)
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        
        # Sharpe ratio (simplified)
        if len(equity_curve) > 1:
            returns = pd.Series(equity_curve).pct_change().dropna()
            sharpe_ratio = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
        else:
            sharpe_ratio = 0
        
        result = BacktestResult(
            strategy_name=strategy.name,
            symbol=symbol,
            start_date=df.index[0],
            end_date=df.index[-1],
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_trades=len(trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            trades=[t.to_dict() for t in trades]
        )
        
        logger.info(f"✅ Backtest complete: Return={total_return:.2f}%, Trades={len(trades)}, Win Rate={win_rate:.1f}%")
        
        return result


class StrategyGenerator:
    """Générateur de stratégies par recherche aléatoire"""
    
    def __init__(self, target_return: float = 10.0):
        """
        Args:
            target_return: Retour cible en pourcentage
        """
        self.target_return = target_return
    
    def generate_random_ma_strategy(self) -> MovingAverageCrossover:
        """Génère une stratégie MA aléatoire"""
        fast = np.random.randint(5, 20)
        slow = np.random.randint(fast + 5, 50)
        return MovingAverageCrossover(fast_period=fast, slow_period=slow)
    
    def generate_random_rsi_strategy(self) -> RSIStrategy:
        """Génère une stratégie RSI aléatoire"""
        period = np.random.randint(10, 20)
        oversold = np.random.randint(20, 35)
        overbought = np.random.randint(65, 80)
        return RSIStrategy(rsi_period=period, oversold=oversold, overbought=overbought)
    
    def generate_random_multi_strategy(self) -> MultiIndicatorStrategy:
        """Génère une stratégie multi-indicateurs aléatoire"""
        return MultiIndicatorStrategy(
            ma_fast=np.random.randint(5, 15),
            ma_slow=np.random.randint(20, 40),
            rsi_period=np.random.randint(10, 20),
            rsi_oversold=np.random.randint(20, 35),
            rsi_overbought=np.random.randint(65, 80),
            macd_fast=np.random.randint(10, 15),
            macd_slow=np.random.randint(20, 30),
            macd_signal=np.random.randint(7, 12)
        )
    
    def search_profitable_strategy(
        self,
        df: pd.DataFrame,
        symbol: str,
        max_iterations: int = 100,
        initial_capital: float = 10000.0
    ) -> Tuple[Optional[Strategy], Optional[BacktestResult]]:
        """
        Cherche une stratégie profitable
        
        Args:
            df: DataFrame avec les données
            symbol: Symbole du ticker
            max_iterations: Nombre maximum d'itérations
            initial_capital: Capital initial
            
        Returns:
            (strategy, result) ou (None, None) si aucune stratégie trouvée
        """
        logger.info(f"🔍 Searching for profitable strategy (target: {self.target_return}%)")
        
        engine = BacktestingEngine(initial_capital=initial_capital)
        best_strategy = None
        best_result = None
        best_return = -np.inf
        
        for i in range(max_iterations):
            # Generate random strategy
            strategy_type = np.random.choice(['ma', 'rsi', 'multi'])
            
            if strategy_type == 'ma':
                strategy = self.generate_random_ma_strategy()
            elif strategy_type == 'rsi':
                strategy = self.generate_random_rsi_strategy()
            else:
                strategy = self.generate_random_multi_strategy()
            
            # Run backtest
            result = engine.run_backtest(df, strategy, symbol)
            
            # Check if target reached
            if result.total_return >= self.target_return:
                logger.info(f"🎯 Found profitable strategy! Return: {result.total_return:.2f}%")
                return strategy, result
            
            # Keep track of best so far
            if result.total_return > best_return:
                best_return = result.total_return
                best_strategy = strategy
                best_result = result
                logger.info(f"  Iteration {i+1}/{max_iterations}: New best = {best_return:.2f}%")
        
        logger.warning(f"⚠️ Target not reached after {max_iterations} iterations. Best: {best_return:.2f}%")
        
        if best_return >= 0:  # Return best strategy if it's profitable
            return best_strategy, best_result
        
        return None, None
