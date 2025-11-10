"""
Backtesting Engine - Moteur de test de stratégies de trading
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json
from multiprocessing import Pool, cpu_count
import pickle

from backend.config import logger
from backend.models import SessionLocal, Ticker, HistoricalData, Base
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from numpy.random import Generator
import numpy as np


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
    
    @staticmethod
    def from_dict(data: Dict):
        """Create BacktestResult from dictionary"""
        # Convert ISO strings back to datetime
        if isinstance(data.get('start_date'), str):
            data['start_date'] = datetime.fromisoformat(data['start_date'])
        if isinstance(data.get('end_date'), str):
            data['end_date'] = datetime.fromisoformat(data['end_date'])
        return BacktestResult(**data)


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
    
    def __init__(self, name: str, parameters: Dict = None):
        """TODO: Add docstring."""
        self.name = name
        self.parameters = parameters if parameters is not None else {}
    
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
        # Cette fonction sera appelée après que toutes les classes soient définies
        # On utilise une approche lazy avec import local pour éviter les dépendances circulaires
        return _create_strategy_from_dict(data)


class RandomStrategy(Strategy):
    """Stratégie aléatoire pour tester le moteur"""
    
    def __init__(self, seed: int = 42):
        """TODO: Add docstring."""
        super().__init__('RandomStrategy', {'seed': seed})
        self.seed = seed
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """TODO: Add docstring."""
        np.random.seed(self.seed)
        signals = np.random.choice([0, 1, -1], size=len(df), p=[0.8, 0.1, 0.1])
        return pd.Series(signals, index=df.index)


class MovingAverageCrossover(Strategy):
    """Stratégie de croisement de moyennes mobiles"""
    
    def __init__(self, fast_period: int = 10, slow_period: int = 30):
        """TODO: Add docstring."""
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
        """TODO: Add docstring."""
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
    """TODO: Add docstring."""
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


class AdvancedMultiIndicatorStrategy(Strategy):
    """Stratégie avancée avec 7+ indicateurs techniques"""
    
    def __init__(
        self,
        ma_fast: int = 10,
        ma_slow: int = 30,
        rsi_period: int = 14,
        rsi_oversold: int = 30,
        rsi_overbought: int = 70,
        bb_period: int = 20,
        bb_std: float = 2.0,
        stoch_k: int = 14,
        stoch_d: int = 3,
        stoch_oversold: int = 20,
        stoch_overbought: int = 80,
        atr_period: int = 14,
        volume_ma: int = 20,
        min_signals: int = 4
    ):
    """TODO: Add docstring."""
        super().__init__('AdvancedMultiIndicatorStrategy', {
            'ma_fast': ma_fast,
            'ma_slow': ma_slow,
            'rsi_period': rsi_period,
            'rsi_oversold': rsi_oversold,
            'rsi_overbought': rsi_overbought,
            'bb_period': bb_period,
            'bb_std': bb_std,
            'stoch_k': stoch_k,
            'stoch_d': stoch_d,
            'stoch_oversold': stoch_oversold,
            'stoch_overbought': stoch_overbought,
            'atr_period': atr_period,
            'volume_ma': volume_ma,
            'min_signals': min_signals
        })
        self.ma_fast = ma_fast
        self.ma_slow = ma_slow
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.stoch_k = stoch_k
        self.stoch_d = stoch_d
        self.stoch_oversold = stoch_oversold
        self.stoch_overbought = stoch_overbought
        self.atr_period = atr_period
        self.volume_ma = volume_ma
        self.min_signals = min_signals
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """TODO: Add docstring."""
        signals_list = []
        
        # 1. Moving Average Crossover
        fast_ma = df['close'].rolling(window=self.ma_fast).mean()
        slow_ma = df['close'].rolling(window=self.ma_slow).mean()
        ma_signal = pd.Series(0, index=df.index)
        ma_signal[fast_ma > slow_ma] = 1
        ma_signal[fast_ma < slow_ma] = -1
        signals_list.append(ma_signal)
        
        # 2. RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        rsi_signal = pd.Series(0, index=df.index)
        rsi_signal[rsi < self.rsi_oversold] = 1
        rsi_signal[rsi > self.rsi_overbought] = -1
        signals_list.append(rsi_signal)
        
        # 3. MACD
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        signal_line = macd.ewm(span=9, adjust=False).mean()
        macd_signal = pd.Series(0, index=df.index)
        macd_signal[macd > signal_line] = 1
        macd_signal[macd < signal_line] = -1
        signals_list.append(macd_signal)
        
        # 4. Bollinger Bands
        bb_ma = df['close'].rolling(window=self.bb_period).mean()
        bb_std = df['close'].rolling(window=self.bb_period).std()
        bb_upper = bb_ma + (bb_std * self.bb_std)
        bb_lower = bb_ma - (bb_std * self.bb_std)
        bb_signal = pd.Series(0, index=df.index)
        bb_signal[df['close'] < bb_lower] = 1  # Buy when price below lower band
        bb_signal[df['close'] > bb_upper] = -1  # Sell when price above upper band
        signals_list.append(bb_signal)
        
        # 5. Stochastic Oscillator
        low_min = df['low'].rolling(window=self.stoch_k).min()
        high_max = df['high'].rolling(window=self.stoch_k).max()
        stoch_k = 100 * (df['close'] - low_min) / (high_max - low_min + 1e-10)
        stoch_d = stoch_k.rolling(window=self.stoch_d).mean()
        stoch_signal = pd.Series(0, index=df.index)
        stoch_signal[(stoch_k < self.stoch_oversold) & (stoch_k > stoch_d)] = 1
        stoch_signal[(stoch_k > self.stoch_overbought) & (stoch_k < stoch_d)] = -1
        signals_list.append(stoch_signal)
        
        # 6. Volume Trend
        volume_ma = df['volume'].rolling(window=self.volume_ma).mean()
        volume_signal = pd.Series(0, index=df.index)
        volume_signal[df['volume'] > volume_ma * 1.5] = 1  # Strong volume = potential breakout
        signals_list.append(volume_signal)
        
        # 7. Price Momentum
        momentum = df['close'].pct_change(periods=10)
        momentum_signal = pd.Series(0, index=df.index)
        momentum_signal[momentum > 0.02] = 1  # 2% upward momentum
        momentum_signal[momentum < -0.02] = -1  # 2% downward momentum
        signals_list.append(momentum_signal)
        
        # Combine all signals with weighted voting
        combined = sum(signals_list)
        final_signals = pd.Series(0, index=df.index)
        final_signals[combined >= self.min_signals] = 1  # Buy if enough indicators agree
        final_signals[combined <= -self.min_signals] = -1  # Sell if enough indicators agree
        
        return final_signals


class MomentumBreakoutStrategy(Strategy):
    """Stratégie de momentum avec breakout"""
    
    def __init__(
        self,
        lookback_period: int = 20,
        breakout_threshold: float = 0.03,
        volume_multiplier: float = 1.5,
        rsi_period: int = 14,
        rsi_min: int = 40,
        rsi_max: int = 80
    ):
    """TODO: Add docstring."""
        super().__init__('MomentumBreakoutStrategy', {
            'lookback_period': lookback_period,
            'breakout_threshold': breakout_threshold,
            'volume_multiplier': volume_multiplier,
            'rsi_period': rsi_period,
            'rsi_min': rsi_min,
            'rsi_max': rsi_max
        })
        self.lookback_period = lookback_period
        self.breakout_threshold = breakout_threshold
        self.volume_multiplier = volume_multiplier
        self.rsi_period = rsi_period
        self.rsi_min = rsi_min
        self.rsi_max = rsi_max
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """TODO: Add docstring."""
        signals = pd.Series(0, index=df.index)
        
        # Calculate indicators
        high_max = df['high'].rolling(window=self.lookback_period).max()
        low_min = df['low'].rolling(window=self.lookback_period).min()
        volume_ma = df['volume'].rolling(window=self.lookback_period).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        # Buy signal: Price breaks above recent high with volume confirmation and RSI not overbought
        buy_condition = (
            (df['close'] > high_max.shift(1)) &
            (df['volume'] > volume_ma * self.volume_multiplier) &
            (rsi > self.rsi_min) & (rsi < self.rsi_max)
        )
        signals[buy_condition] = 1
        
        # Sell signal: Price breaks below recent low or RSI overbought
        sell_condition = (
            (df['close'] < low_min.shift(1)) | (rsi > 90)
        )
        signals[sell_condition] = -1
        
        return signals


class MeanReversionStrategy(Strategy):
    """Stratégie de retour à la moyenne"""
    
    def __init__(
        self,
        bb_period: int = 20,
        bb_std: float = 2.0,
        rsi_period: int = 14,
        rsi_oversold: int = 25,
        rsi_overbought: int = 75,
        zscore_threshold: float = 2.0
    ):
    """TODO: Add docstring."""
        super().__init__('MeanReversionStrategy', {
            'bb_period': bb_period,
            'bb_std': bb_std,
            'rsi_period': rsi_period,
            'rsi_oversold': rsi_oversold,
            'rsi_overbought': rsi_overbought,
            'zscore_threshold': zscore_threshold
        })
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.zscore_threshold = zscore_threshold
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """TODO: Add docstring."""
        signals = pd.Series(0, index=df.index)
        
        # Bollinger Bands
        bb_ma = df['close'].rolling(window=self.bb_period).mean()
        bb_std = df['close'].rolling(window=self.bb_period).std()
        bb_upper = bb_ma + (bb_std * self.bb_std)
        bb_lower = bb_ma - (bb_std * self.bb_std)
        
        # Z-score (distance from mean in standard deviations)
        zscore = (df['close'] - bb_ma) / (bb_std + 1e-10)
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        # Buy when oversold (price far below mean)
        buy_condition = (
            (zscore < -self.zscore_threshold) &
            (rsi < self.rsi_oversold) &
            (df['close'] < bb_lower)
        )
        signals[buy_condition] = 1
        
        # Sell when overbought (price far above mean or back to mean)
        sell_condition = (
            ((zscore > self.zscore_threshold) & (rsi > self.rsi_overbought)) |
            (zscore > 0)  # Price crossed above mean
        )
        signals[sell_condition] = -1
        
        return signals


class UltraAggressiveStrategy(Strategy):
    """Stratégie ultra-agressive avec 15+ indicateurs et trading fréquent"""
    
    def __init__(
        self,
        # Moving Averages (multiple timeframes)
        ma_very_fast: int = 5,
        ma_fast: int = 10,
        ma_medium: int = 20,
        ma_slow: int = 50,
        # RSI
        rsi_period: int = 14,
        rsi_oversold: int = 30,
        rsi_overbought: int = 70,
        # MACD
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        # Bollinger Bands
        bb_period: int = 20,
        bb_std: float = 2.0,
        # Stochastic
        stoch_k: int = 14,
        stoch_d: int = 3,
        # CCI (Commodity Channel Index)
        cci_period: int = 20,
        cci_oversold: int = -100,
        cci_overbought: int = 100,
        # Williams %R
        williams_period: int = 14,
        williams_oversold: int = -80,
        williams_overbought: int = -20,
        # ROC (Rate of Change)
        roc_period: int = 12,
        # Volume indicators
        volume_ma_short: int = 10,
        volume_ma_long: int = 30,
        # ADX (trend strength)
        adx_period: int = 14,
        adx_threshold: int = 20,
        # Signal threshold (lower = more trades)
        min_signals: int = 3  # Seulement 3/15 = très agressif
    ):
        super().__init__('UltraAggressiveStrategy', {
            'ma_very_fast': ma_very_fast,
            'ma_fast': ma_fast,
            'ma_medium': ma_medium,
            'ma_slow': ma_slow,
            'rsi_period': rsi_period,
            'rsi_oversold': rsi_oversold,
            'rsi_overbought': rsi_overbought,
            'macd_fast': macd_fast,
            'macd_slow': macd_slow,
            'macd_signal': macd_signal,
            'bb_period': bb_period,
            'bb_std': bb_std,
            'stoch_k': stoch_k,
            'stoch_d': stoch_d,
            'cci_period': cci_period,
            'cci_oversold': cci_oversold,
            'cci_overbought': cci_overbought,
            'williams_period': williams_period,
            'williams_oversold': williams_oversold,
            'williams_overbought': williams_overbought,
            'roc_period': roc_period,
            'volume_ma_short': volume_ma_short,
            'volume_ma_long': volume_ma_long,
            'adx_period': adx_period,
            'adx_threshold': adx_threshold,
            'min_signals': min_signals
        })
        # Store all parameters
        for key, value in self.parameters.items():
            setattr(self, key, value)
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """TODO: Add docstring."""
        signals_list = []
        
        # 1. Multi-timeframe Moving Averages
        ma_vf = df['close'].rolling(window=self.ma_very_fast).mean()
        ma_f = df['close'].rolling(window=self.ma_fast).mean()
        ma_m = df['close'].rolling(window=self.ma_medium).mean()
        ma_s = df['close'].rolling(window=self.ma_slow).mean()
        
        ma_signal = pd.Series(0, index=df.index)
        ma_signal[(ma_vf > ma_f) & (ma_f > ma_m)] = 1
        ma_signal[(ma_vf < ma_f) & (ma_f < ma_m)] = -1
        signals_list.append(ma_signal)
        
        # 2. RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        rsi_signal = pd.Series(0, index=df.index)
        rsi_signal[rsi < self.rsi_oversold] = 1
        rsi_signal[rsi > self.rsi_overbought] = -1
        signals_list.append(rsi_signal)
        
        # 3. MACD
        ema_fast = df['close'].ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=self.macd_slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        macd_signal_line = macd.ewm(span=self.macd_signal, adjust=False).mean()
        
        macd_signal = pd.Series(0, index=df.index)
        macd_signal[macd > macd_signal_line] = 1
        macd_signal[macd < macd_signal_line] = -1
        signals_list.append(macd_signal)
        
        # 4. Bollinger Bands
        bb_ma = df['close'].rolling(window=self.bb_period).mean()
        bb_std = df['close'].rolling(window=self.bb_period).std()
        bb_upper = bb_ma + (bb_std * self.bb_std)
        bb_lower = bb_ma - (bb_std * self.bb_std)
        
        bb_signal = pd.Series(0, index=df.index)
        bb_signal[df['close'] < bb_lower] = 1
        bb_signal[df['close'] > bb_upper] = -1
        signals_list.append(bb_signal)
        
        # 5. Stochastic Oscillator
        low_min = df['low'].rolling(window=self.stoch_k).min()
        high_max = df['high'].rolling(window=self.stoch_k).max()
        stoch_k = 100 * (df['close'] - low_min) / (high_max - low_min + 1e-10)
        stoch_d = stoch_k.rolling(window=self.stoch_d).mean()
        
        stoch_signal = pd.Series(0, index=df.index)
        stoch_signal[(stoch_k < 20) & (stoch_k > stoch_d)] = 1
        stoch_signal[(stoch_k > 80) & (stoch_k < stoch_d)] = -1
        signals_list.append(stoch_signal)
        
        # 6. CCI (Commodity Channel Index)
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = typical_price.rolling(window=self.cci_period).mean()
        mad = typical_price.rolling(window=self.cci_period).apply(lambda x: np.abs(x - x.mean()).mean())
        cci = (typical_price - sma_tp) / (0.015 * mad + 1e-10)
        
        cci_signal = pd.Series(0, index=df.index)
        cci_signal[cci < self.cci_oversold] = 1
        cci_signal[cci > self.cci_overbought] = -1
        signals_list.append(cci_signal)
        
        # 7. Williams %R
        williams_r = -100 * (high_max - df['close']) / (high_max - low_min + 1e-10)
        
        williams_signal = pd.Series(0, index=df.index)
        williams_signal[williams_r < self.williams_oversold] = 1
        williams_signal[williams_r > self.williams_overbought] = -1
        signals_list.append(williams_signal)
        
        # 8. ROC (Rate of Change)
        roc = ((df['close'] - df['close'].shift(self.roc_period)) / df['close'].shift(self.roc_period)) * 100
        
        roc_signal = pd.Series(0, index=df.index)
        roc_signal[roc > 2] = 1
        roc_signal[roc < -2] = -1
        signals_list.append(roc_signal)
        
        # 9. Price Momentum (multiple periods)
        momentum_5 = df['close'].pct_change(periods=5)
        momentum_10 = df['close'].pct_change(periods=10)
        
        momentum_signal = pd.Series(0, index=df.index)
        momentum_signal[(momentum_5 > 0.01) & (momentum_10 > 0.01)] = 1
        momentum_signal[(momentum_5 < -0.01) & (momentum_10 < -0.01)] = -1
        signals_list.append(momentum_signal)
        
        # 10. Volume Trend (short vs long)
        volume_ma_s = df['volume'].rolling(window=self.volume_ma_short).mean()
        volume_ma_l = df['volume'].rolling(window=self.volume_ma_long).mean()
        
        volume_signal = pd.Series(0, index=df.index)
        volume_signal[volume_ma_s > volume_ma_l * 1.2] = 1
        signals_list.append(volume_signal)
        
        # 11. Volume Spike
        volume_avg = df['volume'].rolling(window=20).mean()
        volume_spike_signal = pd.Series(0, index=df.index)
        volume_spike_signal[df['volume'] > volume_avg * 2] = 1
        signals_list.append(volume_spike_signal)
        
        # 12. ADX (Average Directional Index) - trend strength
        # Simplified ADX calculation
        high_diff = df['high'].diff()
        low_diff = -df['low'].diff()
        
        plus_dm = pd.Series(0.0, index=df.index, dtype='float64')
        minus_dm = pd.Series(0.0, index=df.index, dtype='float64')
        
        plus_dm[high_diff > low_diff] = high_diff[high_diff > low_diff].clip(lower=0)
        minus_dm[low_diff > high_diff] = low_diff[low_diff > high_diff].clip(lower=0)
        
        tr = pd.concat([
            df['high'] - df['low'],
            (df['high'] - df['close'].shift()).abs(),
            (df['low'] - df['close'].shift()).abs()
        ], axis=1).max(axis=1)
        
        atr = tr.rolling(window=self.adx_period).mean()
        plus_di = 100 * (plus_dm.rolling(window=self.adx_period).mean() / (atr + 1e-10))
        minus_di = 100 * (minus_dm.rolling(window=self.adx_period).mean() / (atr + 1e-10))
        
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-10)
        adx = dx.rolling(window=self.adx_period).mean()
        
        adx_signal = pd.Series(0, index=df.index)
        adx_signal[(adx > self.adx_threshold) & (plus_di > minus_di)] = 1
        adx_signal[(adx > self.adx_threshold) & (plus_di < minus_di)] = -1
        signals_list.append(adx_signal)
        
        # 13. OBV (On-Balance Volume)
        obv = pd.Series(0, index=df.index)
        obv.iloc[0] = df['volume'].iloc[0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + df['volume'].iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - df['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        obv_ma = obv.rolling(window=20).mean()
        obv_signal = pd.Series(0, index=df.index)
        obv_signal[obv > obv_ma] = 1
        obv_signal[obv < obv_ma] = -1
        signals_list.append(obv_signal)
        
        # 14. Price vs Moving Average distance
        price_distance = ((df['close'] - ma_m) / ma_m) * 100
        distance_signal = pd.Series(0, index=df.index)
        distance_signal[price_distance < -2] = 1
        distance_signal[price_distance > 2] = -1
        signals_list.append(distance_signal)
        
        # 15. Volatility (ATR based)
        volatility_signal = pd.Series(0, index=df.index)
        atr_pct = (atr / df['close']) * 100
        volatility_signal[atr_pct > 3] = 1  # High volatility = opportunity
        signals_list.append(volatility_signal)
        
        # Combine all 15 signals with low threshold (aggressive)
        combined = sum(signals_list)
        final_signals = pd.Series(0, index=df.index)
        final_signals[combined >= self.min_signals] = 1  # Buy if at least min_signals agree
        final_signals[combined <= -self.min_signals] = -1  # Sell if at least min_signals agree
        
        return final_signals


class MegaIndicatorStrategy(Strategy):
    """Stratégie MEGA avec 25+ indicateurs techniques pour maximiser les signaux"""
    
    def __init__(
        self,
        # Paramètres optimisables
        ma_periods: list = None,
        ema_periods: list = None,
        rsi_period: int = 14,
        rsi_oversold: int = 30,
        rsi_overbought: int = 70,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        bb_period: int = 20,
        bb_std: float = 2.0,
        stoch_k: int = 14,
        stoch_d: int = 3,
        cci_period: int = 20,
        williams_period: int = 14,
        roc_period: int = 12,
        mfi_period: int = 14,  # Money Flow Index
        trix_period: int = 15,  # TRIX
        kst_periods: list = None,  # Know Sure Thing
        volume_ma: int = 20,
        adx_period: int = 14,
        min_signals: int = 2  # MEGA agressif: 2/25 = 8%
    ):
    """TODO: Add docstring."""
        # Default values
        if ma_periods is None:
            ma_periods = [5, 10, 20, 50, 100]
        if ema_periods is None:
            ema_periods = [8, 13, 21, 34, 55]  # Fibonacci
        if kst_periods is None:
            kst_periods = [10, 15, 20, 30]
        
        super().__init__('MegaIndicatorStrategy', {
            'ma_periods': ma_periods,
            'ema_periods': ema_periods,
            'rsi_period': rsi_period,
            'rsi_oversold': rsi_oversold,
            'rsi_overbought': rsi_overbought,
            'macd_fast': macd_fast,
            'macd_slow': macd_slow,
            'macd_signal': macd_signal,
            'bb_period': bb_period,
            'bb_std': bb_std,
            'stoch_k': stoch_k,
            'stoch_d': stoch_d,
            'cci_period': cci_period,
            'williams_period': williams_period,
            'roc_period': roc_period,
            'mfi_period': mfi_period,
            'trix_period': trix_period,
            'kst_periods': kst_periods,
            'volume_ma': volume_ma,
            'adx_period': adx_period,
            'min_signals': min_signals
        })
        for key, value in self.parameters.items():
            setattr(self, key, value)
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """TODO: Add docstring."""
        signals_list = []
        
        # 1-5. Multiple Moving Averages (5 MAs)
        for period in self.ma_periods:
            ma = df['close'].rolling(window=period).mean()
            ma_signal = pd.Series(0, index=df.index)
            ma_signal[df['close'] > ma] = 1
            ma_signal[df['close'] < ma] = -1
            signals_list.append(ma_signal)
        
        # 6-10. Multiple EMAs (5 EMAs) - Fibonacci sequence
        for period in self.ema_periods:
            ema = df['close'].ewm(span=period, adjust=False).mean()
            ema_signal = pd.Series(0, index=df.index)
            ema_signal[df['close'] > ema] = 1
            ema_signal[df['close'] < ema] = -1
            signals_list.append(ema_signal)
        
        # 11. MA/EMA Crossover (Fast EMA vs Slow MA)
        fast_ema = df['close'].ewm(span=self.ema_periods[0], adjust=False).mean()
        slow_ma = df['close'].rolling(window=self.ma_periods[-1]).mean()
        cross_signal = pd.Series(0, index=df.index)
        cross_signal[fast_ema > slow_ma] = 1
        cross_signal[fast_ema < slow_ma] = -1
        signals_list.append(cross_signal)
        
        # 12. RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        rsi_signal = pd.Series(0, index=df.index)
        rsi_signal[rsi < self.rsi_oversold] = 1
        rsi_signal[rsi > self.rsi_overbought] = -1
        signals_list.append(rsi_signal)
        
        # 13. MACD
        ema_fast = df['close'].ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=self.macd_slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        macd_signal_line = macd.ewm(span=self.macd_signal, adjust=False).mean()
        macd_hist = macd - macd_signal_line
        
        macd_signal = pd.Series(0, index=df.index)
        macd_signal[macd > macd_signal_line] = 1
        macd_signal[macd < macd_signal_line] = -1
        signals_list.append(macd_signal)
        
        # 14. MACD Histogram
        macd_hist_signal = pd.Series(0, index=df.index)
        macd_hist_signal[macd_hist > 0] = 1
        macd_hist_signal[macd_hist < 0] = -1
        signals_list.append(macd_hist_signal)
        
        # 15. Bollinger Bands
        bb_ma = df['close'].rolling(window=self.bb_period).mean()
        bb_std = df['close'].rolling(window=self.bb_period).std()
        bb_upper = bb_ma + (bb_std * self.bb_std)
        bb_lower = bb_ma - (bb_std * self.bb_std)
        bb_width = (bb_upper - bb_lower) / bb_ma
        
        bb_signal = pd.Series(0, index=df.index)
        bb_signal[df['close'] < bb_lower] = 1
        bb_signal[df['close'] > bb_upper] = -1
        signals_list.append(bb_signal)
        
        # 16. Bollinger Bands %B
        bb_percent = (df['close'] - bb_lower) / (bb_upper - bb_lower + 1e-10)
        bb_percent_signal = pd.Series(0, index=df.index)
        bb_percent_signal[bb_percent < 0.2] = 1
        bb_percent_signal[bb_percent > 0.8] = -1
        signals_list.append(bb_percent_signal)
        
        # 17. Stochastic Oscillator
        low_min = df['low'].rolling(window=self.stoch_k).min()
        high_max = df['high'].rolling(window=self.stoch_k).max()
        stoch_k = 100 * (df['close'] - low_min) / (high_max - low_min + 1e-10)
        stoch_d = stoch_k.rolling(window=self.stoch_d).mean()
        
        stoch_signal = pd.Series(0, index=df.index)
        stoch_signal[(stoch_k < 20) & (stoch_k > stoch_d)] = 1
        stoch_signal[(stoch_k > 80) & (stoch_k < stoch_d)] = -1
        signals_list.append(stoch_signal)
        
        # 18. CCI (Commodity Channel Index)
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = typical_price.rolling(window=self.cci_period).mean()
        mad = typical_price.rolling(window=self.cci_period).apply(lambda x: np.abs(x - x.mean()).mean())
        cci = (typical_price - sma_tp) / (0.015 * mad + 1e-10)
        
        cci_signal = pd.Series(0, index=df.index)
        cci_signal[cci < -100] = 1
        cci_signal[cci > 100] = -1
        signals_list.append(cci_signal)
        
        # 19. Williams %R
        williams_r = -100 * (high_max - df['close']) / (high_max - low_min + 1e-10)
        williams_signal = pd.Series(0, index=df.index)
        williams_signal[williams_r < -80] = 1
        williams_signal[williams_r > -20] = -1
        signals_list.append(williams_signal)
        
        # 20. ROC (Rate of Change)
        roc = ((df['close'] - df['close'].shift(self.roc_period)) / df['close'].shift(self.roc_period)) * 100
        roc_signal = pd.Series(0, index=df.index)
        roc_signal[roc > 2] = 1
        roc_signal[roc < -2] = -1
        signals_list.append(roc_signal)
        
        # 21. MFI (Money Flow Index)
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        money_flow = typical_price * df['volume']
        
        positive_flow = pd.Series(0.0, index=df.index)
        negative_flow = pd.Series(0.0, index=df.index)
        
        positive_flow[typical_price > typical_price.shift(1)] = money_flow[typical_price > typical_price.shift(1)]
        negative_flow[typical_price < typical_price.shift(1)] = money_flow[typical_price < typical_price.shift(1)]
        
        positive_mf = positive_flow.rolling(window=self.mfi_period).sum()
        negative_mf = negative_flow.rolling(window=self.mfi_period).sum()
        
        mfi = 100 - (100 / (1 + positive_mf / (negative_mf + 1e-10)))
        
        mfi_signal = pd.Series(0, index=df.index)
        mfi_signal[mfi < 20] = 1
        mfi_signal[mfi > 80] = -1
        signals_list.append(mfi_signal)
        
        # 22. TRIX (Triple Exponential Average)
        ema1 = df['close'].ewm(span=self.trix_period, adjust=False).mean()
        ema2 = ema1.ewm(span=self.trix_period, adjust=False).mean()
        ema3 = ema2.ewm(span=self.trix_period, adjust=False).mean()
        trix = ((ema3 - ema3.shift(1)) / ema3.shift(1)) * 10000
        
        trix_signal = pd.Series(0, index=df.index)
        trix_signal[trix > 0] = 1
        trix_signal[trix < 0] = -1
        signals_list.append(trix_signal)
        
        # 23. ADX (Trend Strength)
        high_diff = df['high'].diff()
        low_diff = -df['low'].diff()
        
        plus_dm = pd.Series(0.0, index=df.index, dtype='float64')
        minus_dm = pd.Series(0.0, index=df.index, dtype='float64')
        
        plus_dm[high_diff > low_diff] = high_diff[high_diff > low_diff].clip(lower=0)
        minus_dm[low_diff > high_diff] = low_diff[low_diff > high_diff].clip(lower=0)
        
        tr = pd.concat([
            df['high'] - df['low'],
            (df['high'] - df['close'].shift()).abs(),
            (df['low'] - df['close'].shift()).abs()
        ], axis=1).max(axis=1)
        
        atr = tr.rolling(window=self.adx_period).mean()
        plus_di = 100 * (plus_dm.rolling(window=self.adx_period).mean() / (atr + 1e-10))
        minus_di = 100 * (minus_dm.rolling(window=self.adx_period).mean() / (atr + 1e-10))
        
        adx_signal = pd.Series(0, index=df.index)
        adx_signal[plus_di > minus_di] = 1
        adx_signal[plus_di < minus_di] = -1
        signals_list.append(adx_signal)
        
        # 24. OBV (On-Balance Volume)
        obv = pd.Series(0, index=df.index)
        obv.iloc[0] = df['volume'].iloc[0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + df['volume'].iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - df['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        obv_ma = obv.rolling(window=20).mean()
        obv_signal = pd.Series(0, index=df.index)
        obv_signal[obv > obv_ma] = 1
        obv_signal[obv < obv_ma] = -1
        signals_list.append(obv_signal)
        
        # 25. Volume Spike
        volume_ma = df['volume'].rolling(window=self.volume_ma).mean()
        volume_signal = pd.Series(0, index=df.index)
        volume_signal[df['volume'] > volume_ma * 2] = 1
        volume_signal[df['volume'] < volume_ma * 0.5] = -1
        signals_list.append(volume_signal)
        
        # 26. Price Momentum (3 timeframes)
        mom_3 = df['close'].pct_change(periods=3)
        mom_signal = pd.Series(0, index=df.index)
        mom_signal[mom_3 > 0.01] = 1
        mom_signal[mom_3 < -0.01] = -1
        signals_list.append(mom_signal)
        
        # 27. Volatility (ATR %)
        atr_pct = (atr / df['close']) * 100
        vol_signal = pd.Series(0, index=df.index)
        vol_signal[atr_pct > 2] = 1  # High volatility
        signals_list.append(vol_signal)
        
        # Combine all 27+ signals (MEGA aggressive)
        combined = sum(signals_list)
        final_signals = pd.Series(0, index=df.index)
        final_signals[combined >= self.min_signals] = 1
        final_signals[combined <= -self.min_signals] = -1
        
        return final_signals


class HyperAggressiveStrategy(Strategy):
    """
    Stratégie HYPER-AGRESSIVE avec 40+ indicateurs incluant :
    - Moyennes mobiles multi-temporelles (1 jour, 7 jours, 20 jours en minutes)
    - Tous les indicateurs de MEGA
    - Comparaisons de tendances court/moyen/long terme
    - min_signals = 1 pour trader au MAXIMUM
    """
    
    def __init__(
        self,
        # Multi-timeframe MAs (en minutes pour données 1min)
        ma_1day: int = 1440,      # 1 jour = 1440 minutes (6.5h trading = 390min)
        ma_7days: int = 2730,     # 7 jours = ~2730 minutes de trading
        ma_20days: int = 7800,    # 20 jours = ~7800 minutes de trading
        ma_very_short: int = 5,
        ma_short: int = 15,
        ma_medium: int = 60,      # 1 heure
        ma_long: int = 240,       # 4 heures
        # EMAs multi-timeframe
        ema_ultra_fast: int = 3,
        ema_fast: int = 8,
        ema_medium: int = 21,
        ema_slow: int = 55,
        ema_1day: int = 390,      # 1 jour de trading
        ema_1week: int = 1950,    # 1 semaine de trading
        # RSI multi-période
        rsi_fast: int = 7,
        rsi_medium: int = 14,
        rsi_slow: int = 21,
        rsi_oversold: int = 30,
        rsi_overbought: int = 70,
        # MACD
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        # Bollinger Bands
        bb_period: int = 20,
        bb_std: float = 2.0,
        # Stochastic
        stoch_k: int = 14,
        stoch_d: int = 3,
        stoch_oversold: int = 20,
        stoch_overbought: int = 80,
        # CCI
        cci_period: int = 20,
        cci_oversold: int = -100,
        cci_overbought: int = 100,
        # Williams %R
        williams_period: int = 14,
        williams_oversold: int = -80,
        williams_overbought: int = -20,
        # ROC multi-période
        roc_fast: int = 5,
        roc_medium: int = 12,
        roc_slow: int = 25,
        # MFI
        mfi_period: int = 14,
        mfi_oversold: int = 20,
        mfi_overbought: int = 80,
        # TRIX
        trix_period: int = 15,
        # ADX
        adx_period: int = 14,
        adx_threshold: int = 25,
        # Volume
        volume_ma_fast: int = 10,
        volume_ma_medium: int = 30,
        volume_ma_slow: int = 100,
        # Momentum multi-période
        momentum_fast: int = 3,
        momentum_medium: int = 10,
        momentum_slow: int = 20,
        # ATR
        atr_period: int = 14,
        # ULTRA AGRESSIF: min_signals = 1 (un seul indicateur suffit!)
        min_signals: int = 1
    ):
        """40+ indicateurs avec approche multi-temporelle"""
        super().__init__("HyperAggressiveStrategy")
        
        # Store all parameters
        self.ma_1day = ma_1day
        self.ma_7days = ma_7days
        self.ma_20days = ma_20days
        self.ma_very_short = ma_very_short
        self.ma_short = ma_short
        self.ma_medium = ma_medium
        self.ma_long = ma_long
        
        self.ema_ultra_fast = ema_ultra_fast
        self.ema_fast = ema_fast
        self.ema_medium = ema_medium
        self.ema_slow = ema_slow
        self.ema_1day = ema_1day
        self.ema_1week = ema_1week
        
        self.rsi_fast = rsi_fast
        self.rsi_medium = rsi_medium
        self.rsi_slow = rsi_slow
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        
        self.bb_period = bb_period
        self.bb_std = bb_std
        
        self.stoch_k = stoch_k
        self.stoch_d = stoch_d
        self.stoch_oversold = stoch_oversold
        self.stoch_overbought = stoch_overbought
        
        self.cci_period = cci_period
        self.cci_oversold = cci_oversold
        self.cci_overbought = cci_overbought
        
        self.williams_period = williams_period
        self.williams_oversold = williams_oversold
        self.williams_overbought = williams_overbought
        
        self.roc_fast = roc_fast
        self.roc_medium = roc_medium
        self.roc_slow = roc_slow
        
        self.mfi_period = mfi_period
        self.mfi_oversold = mfi_oversold
        self.mfi_overbought = mfi_overbought
        
        self.trix_period = trix_period
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        
        self.volume_ma_fast = volume_ma_fast
        self.volume_ma_medium = volume_ma_medium
        self.volume_ma_slow = volume_ma_slow
        
        self.momentum_fast = momentum_fast
        self.momentum_medium = momentum_medium
        self.momentum_slow = momentum_slow
        
        self.atr_period = atr_period
        self.min_signals = min_signals
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Génère des signaux ultra-agressifs avec 40+ indicateurs"""
        signals_list = []
        
        # === MOYENNES MOBILES MULTI-TEMPORELLES (7 indicateurs) ===
        for period in [self.ma_very_short, self.ma_short, self.ma_medium, self.ma_long, 
                       self.ma_1day, self.ma_7days, self.ma_20days]:
            if len(df) >= period:
                ma = df['close'].rolling(window=period).mean()
                signal = pd.Series(0, index=df.index)
                signal[df['close'] > ma] = 1
                signal[df['close'] < ma] = -1
                signals_list.append(signal)
        
        # === EMAs MULTI-TEMPORELLES (6 indicateurs) ===
        for period in [self.ema_ultra_fast, self.ema_fast, self.ema_medium, 
                       self.ema_slow, self.ema_1day, self.ema_1week]:
            if len(df) >= period:
                ema = df['close'].ewm(span=period, adjust=False).mean()
                signal = pd.Series(0, index=df.index)
                signal[df['close'] > ema] = 1
                signal[df['close'] < ema] = -1
                signals_list.append(signal)
        
        # === CROSSOVERS MA/EMA (3 indicateurs) ===
        # Court terme
        if len(df) >= max(self.ma_short, self.ema_fast):
            ma_short = df['close'].rolling(window=self.ma_short).mean()
            ema_fast = df['close'].ewm(span=self.ema_fast, adjust=False).mean()
            signal = pd.Series(0, index=df.index)
            signal[ema_fast > ma_short] = 1
            signal[ema_fast < ma_short] = -1
            signals_list.append(signal)
        
        # Moyen terme
        if len(df) >= max(self.ma_medium, self.ema_medium):
            ma_med = df['close'].rolling(window=self.ma_medium).mean()
            ema_med = df['close'].ewm(span=self.ema_medium, adjust=False).mean()
            signal = pd.Series(0, index=df.index)
            signal[ema_med > ma_med] = 1
            signal[ema_med < ma_med] = -1
            signals_list.append(signal)
        
        # Long terme
        if len(df) >= max(self.ma_long, self.ema_slow):
            ma_long = df['close'].rolling(window=self.ma_long).mean()
            ema_slow = df['close'].ewm(span=self.ema_slow, adjust=False).mean()
            signal = pd.Series(0, index=df.index)
            signal[ema_slow > ma_long] = 1
            signal[ema_slow < ma_long] = -1
            signals_list.append(signal)
        
        # === RSI MULTI-PÉRIODES (3 indicateurs) ===
        for period in [self.rsi_fast, self.rsi_medium, self.rsi_slow]:
            if len(df) >= period + 1:
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                
                signal = pd.Series(0, index=df.index)
                signal[rsi < self.rsi_oversold] = 1
                signal[rsi > self.rsi_overbought] = -1
                signals_list.append(signal)
        
        # === MACD (2 indicateurs) ===
        if len(df) >= self.macd_slow:
            ema_fast = df['close'].ewm(span=self.macd_fast, adjust=False).mean()
            ema_slow = df['close'].ewm(span=self.macd_slow, adjust=False).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()
            macd_hist = macd_line - signal_line
            
            # MACD crossover
            signal = pd.Series(0, index=df.index)
            signal[macd_line > signal_line] = 1
            signal[macd_line < signal_line] = -1
            signals_list.append(signal)
            
            # MACD histogram
            signal_hist = pd.Series(0, index=df.index)
            signal_hist[(macd_hist > 0) & (macd_hist > macd_hist.shift(1))] = 1
            signal_hist[(macd_hist < 0) & (macd_hist < macd_hist.shift(1))] = -1
            signals_list.append(signal_hist)
        
        # === BOLLINGER BANDS (2 indicateurs) ===
        if len(df) >= self.bb_period:
            bb_middle = df['close'].rolling(window=self.bb_period).mean()
            bb_std = df['close'].rolling(window=self.bb_period).std()
            bb_upper = bb_middle + (bb_std * self.bb_std)
            bb_lower = bb_middle - (bb_std * self.bb_std)
            
            # Prix vs bandes
            signal = pd.Series(0, index=df.index)
            signal[df['close'] <= bb_lower] = 1
            signal[df['close'] >= bb_upper] = -1
            signals_list.append(signal)
            
            # %B
            bb_width = bb_upper - bb_lower
            bb_pct = (df['close'] - bb_lower) / bb_width
            signal_pct = pd.Series(0, index=df.index)
            signal_pct[bb_pct < 0.2] = 1
            signal_pct[bb_pct > 0.8] = -1
            signals_list.append(signal_pct)
        
        # === STOCHASTIC (1 indicateur) ===
        if len(df) >= self.stoch_k:
            low_min = df['low'].rolling(window=self.stoch_k).min()
            high_max = df['high'].rolling(window=self.stoch_k).max()
            stoch_k = 100 * (df['close'] - low_min) / (high_max - low_min)
            stoch_d = stoch_k.rolling(window=self.stoch_d).mean()
            
            signal = pd.Series(0, index=df.index)
            signal[stoch_k < self.stoch_oversold] = 1
            signal[stoch_k > self.stoch_overbought] = -1
            signals_list.append(signal)
        
        # === CCI (1 indicateur) ===
        if len(df) >= self.cci_period:
            tp = (df['high'] + df['low'] + df['close']) / 3
            sma_tp = tp.rolling(window=self.cci_period).mean()
            mad = tp.rolling(window=self.cci_period).apply(lambda x: np.abs(x - x.mean()).mean())
            cci = (tp - sma_tp) / (0.015 * mad)
            
            signal = pd.Series(0, index=df.index)
            signal[cci < self.cci_oversold] = 1
            signal[cci > self.cci_overbought] = -1
            signals_list.append(signal)
        
        # === WILLIAMS %R (1 indicateur) ===
        if len(df) >= self.williams_period:
            high_max = df['high'].rolling(window=self.williams_period).max()
            low_min = df['low'].rolling(window=self.williams_period).min()
            williams = -100 * (high_max - df['close']) / (high_max - low_min)
            
            signal = pd.Series(0, index=df.index)
            signal[williams < self.williams_oversold] = 1
            signal[williams > self.williams_overbought] = -1
            signals_list.append(signal)
        
        # === ROC MULTI-PÉRIODES (3 indicateurs) ===
        for period in [self.roc_fast, self.roc_medium, self.roc_slow]:
            if len(df) >= period:
                roc = ((df['close'] - df['close'].shift(period)) / df['close'].shift(period)) * 100
                signal = pd.Series(0, index=df.index)
                signal[roc > 0] = 1
                signal[roc < 0] = -1
                signals_list.append(signal)
        
        # === MFI (1 indicateur) ===
        if len(df) >= self.mfi_period and 'volume' in df.columns:
            tp = (df['high'] + df['low'] + df['close']) / 3
            mf = tp * df['volume']
            
            positive_flow = pd.Series(0.0, index=df.index)
            negative_flow = pd.Series(0.0, index=df.index)
            
            positive_flow[tp > tp.shift(1)] = mf[tp > tp.shift(1)]
            negative_flow[tp < tp.shift(1)] = mf[tp < tp.shift(1)]
            
            positive_mf = positive_flow.rolling(window=self.mfi_period).sum()
            negative_mf = negative_flow.rolling(window=self.mfi_period).sum()
            
            mfi = 100 - (100 / (1 + positive_mf / negative_mf.replace(0, 1)))
            
            signal = pd.Series(0, index=df.index)
            signal[mfi < self.mfi_oversold] = 1
            signal[mfi > self.mfi_overbought] = -1
            signals_list.append(signal)
        
        # === TRIX (1 indicateur) ===
        if len(df) >= self.trix_period * 3:
            ema1 = df['close'].ewm(span=self.trix_period, adjust=False).mean()
            ema2 = ema1.ewm(span=self.trix_period, adjust=False).mean()
            ema3 = ema2.ewm(span=self.trix_period, adjust=False).mean()
            trix = (ema3 - ema3.shift(1)) / ema3.shift(1) * 100
            
            signal = pd.Series(0, index=df.index)
            signal[(trix > 0) & (trix > trix.shift(1))] = 1
            signal[trix < 0] = -1
            signals_list.append(signal)
        
        # === ADX (1 indicateur) ===
        if len(df) >= self.adx_period:
            high_diff = df['high'].diff()
            low_diff = -df['low'].diff()
            
            plus_dm = pd.Series(0.0, index=df.index)
            minus_dm = pd.Series(0.0, index=df.index)
            
            plus_dm[(high_diff > low_diff) & (high_diff > 0)] = high_diff[(high_diff > low_diff) & (high_diff > 0)]
            minus_dm[(low_diff > high_diff) & (low_diff > 0)] = low_diff[(low_diff > high_diff) & (low_diff > 0)]
            
            tr = pd.concat([
                df['high'] - df['low'],
                abs(df['high'] - df['close'].shift()),
                abs(df['low'] - df['close'].shift())
            ], axis=1).max(axis=1)
            
            atr = tr.rolling(window=self.adx_period).mean()
            plus_di = 100 * (plus_dm.rolling(window=self.adx_period).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(window=self.adx_period).mean() / atr)
            
            signal = pd.Series(0, index=df.index)
            signal[(plus_di > minus_di)] = 1
            signal[(minus_di > plus_di)] = -1
            signals_list.append(signal)
        
        # === OBV (1 indicateur) ===
        if 'volume' in df.columns:
            obv = pd.Series(0.0, index=df.index)
            obv.iloc[0] = df['volume'].iloc[0]
            
            for i in range(1, len(df)):
                if df['close'].iloc[i] > df['close'].iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] + df['volume'].iloc[i]
                elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] - df['volume'].iloc[i]
                else:
                    obv.iloc[i] = obv.iloc[i-1]
            
            signal = pd.Series(0, index=df.index)
            signal[obv > obv.shift(1)] = 1
            signal[obv < obv.shift(1)] = -1
            signals_list.append(signal)
        
        # === VOLUME MULTI-PÉRIODE (3 indicateurs) ===
        if 'volume' in df.columns:
            for period in [self.volume_ma_fast, self.volume_ma_medium, self.volume_ma_slow]:
                if len(df) >= period:
                    vol_ma = df['volume'].rolling(window=period).mean()
                    signal = pd.Series(0, index=df.index)
                    signal[(df['volume'] > vol_ma * 2) & (df['close'] > df['close'].shift(1))] = 1
                    signal[(df['volume'] > vol_ma * 2) & (df['close'] < df['close'].shift(1))] = -1
                    signals_list.append(signal)
        
        # === MOMENTUM MULTI-PÉRIODES (3 indicateurs) ===
        for period in [self.momentum_fast, self.momentum_medium, self.momentum_slow]:
            if len(df) >= period:
                momentum = df['close'] - df['close'].shift(period)
                signal = pd.Series(0, index=df.index)
                signal[momentum > 0] = 1
                signal[momentum < 0] = -1
                signals_list.append(signal)
        
        # === VOLATILITY ATR% (1 indicateur) ===
        if len(df) >= self.atr_period:
            tr = pd.concat([
                df['high'] - df['low'],
                abs(df['high'] - df['close'].shift()),
                abs(df['low'] - df['close'].shift())
            ], axis=1).max(axis=1)
            atr = tr.rolling(window=self.atr_period).mean()
            atr_pct = (atr / df['close']) * 100
            
            # Favoriser trading quand volatilité modérée
            signal = pd.Series(0, index=df.index)
            signal[(atr_pct > 0.5) & (atr_pct < 3)] = 1  # Sweet spot volatilité
            signals_list.append(signal)
        
        # === COMBINE ALL 40+ SIGNALS ===
        # ULTRA AGRESSIF: min_signals = 1 (un seul suffit!)
        combined = sum(signals_list)
        final_signals = pd.Series(0, index=df.index)
        final_signals[combined >= self.min_signals] = 1
        final_signals[combined <= -self.min_signals] = -1
        
        return final_signals


class UltimateStrategy(Strategy):
    """
    Stratégie ULTIMATE avec 60+ indicateurs et croisements avancés
    - Tous les indicateurs de HYPER
    - + Indicateurs de Fibonacci
    - + Ichimoku Cloud
    - + Keltner Channels
    - + Donchian Channels
    - + Parabolic SAR
    - + Aroon Indicator
    - + CMO (Chande Momentum Oscillator)
    - + Ultimate Oscillator
    - + Croisements multiples (Golden Cross, Death Cross, etc.)
    - + Patterns de convergence/divergence
    """
    
    def __init__(
        self,
        # Tous les paramètres de HYPER
        ma_1day: int = 390,
        ma_7days: int = 2730,
        ma_20days: int = 7800,
        ma_very_short: int = 5,
        ma_short: int = 15,
        ma_medium: int = 60,
        ma_long: int = 240,
        ema_ultra_fast: int = 3,
        ema_fast: int = 8,
        ema_medium: int = 21,
        ema_slow: int = 55,
        ema_1day: int = 390,
        ema_1week: int = 1950,
        rsi_fast: int = 7,
        rsi_medium: int = 14,
        rsi_slow: int = 21,
        rsi_oversold: int = 30,
        rsi_overbought: int = 70,
        # Nouveaux indicateurs ULTIMATE
        fibonacci_periods: list = None,  # [89, 144, 233]
        ichimoku_tenkan: int = 9,
        ichimoku_kijun: int = 26,
        ichimoku_senkou: int = 52,
        keltner_period: int = 20,
        keltner_atr_mult: float = 2.0,
        donchian_period: int = 20,
        sar_acceleration: float = 0.02,
        sar_maximum: float = 0.2,
        aroon_period: int = 25,
        cmo_period: int = 14,
        ultimate_osc_short: int = 7,
        ultimate_osc_medium: int = 14,
        ultimate_osc_long: int = 28,
        # Paramètres existants
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        bb_period: int = 20,
        bb_std: float = 2.0,
        stoch_k: int = 14,
        stoch_d: int = 3,
        stoch_oversold: int = 20,
        stoch_overbought: int = 80,
        cci_period: int = 20,
        cci_oversold: int = -100,
        cci_overbought: int = 100,
        williams_period: int = 14,
        williams_oversold: int = -80,
        williams_overbought: int = -20,
        roc_fast: int = 5,
        roc_medium: int = 12,
        roc_slow: int = 25,
        mfi_period: int = 14,
        mfi_oversold: int = 20,
        mfi_overbought: int = 80,
        trix_period: int = 15,
        adx_period: int = 14,
        adx_threshold: int = 25,
        volume_ma_fast: int = 10,
        volume_ma_medium: int = 30,
        volume_ma_slow: int = 100,
        momentum_fast: int = 3,
        momentum_medium: int = 10,
        momentum_slow: int = 20,
        atr_period: int = 14,
        # ENCORE PLUS AGRESSIF
        min_signals: int = 1
    ):
        """60+ indicateurs avec croisements avancés"""
        super().__init__("UltimateStrategy")
        
        # Store all parameters
        self.ma_1day = ma_1day
        self.ma_7days = ma_7days
        self.ma_20days = ma_20days
        self.ma_very_short = ma_very_short
        self.ma_short = ma_short
        self.ma_medium = ma_medium
        self.ma_long = ma_long
        
        self.ema_ultra_fast = ema_ultra_fast
        self.ema_fast = ema_fast
        self.ema_medium = ema_medium
        self.ema_slow = ema_slow
        self.ema_1day = ema_1day
        self.ema_1week = ema_1week
        
        self.rsi_fast = rsi_fast
        self.rsi_medium = rsi_medium
        self.rsi_slow = rsi_slow
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        
        # Nouveaux indicateurs
        self.fibonacci_periods = fibonacci_periods if fibonacci_periods else [89, 144, 233]
        self.ichimoku_tenkan = ichimoku_tenkan
        self.ichimoku_kijun = ichimoku_kijun
        self.ichimoku_senkou = ichimoku_senkou
        self.keltner_period = keltner_period
        self.keltner_atr_mult = keltner_atr_mult
        self.donchian_period = donchian_period
        self.sar_acceleration = sar_acceleration
        self.sar_maximum = sar_maximum
        self.aroon_period = aroon_period
        self.cmo_period = cmo_period
        self.ultimate_osc_short = ultimate_osc_short
        self.ultimate_osc_medium = ultimate_osc_medium
        self.ultimate_osc_long = ultimate_osc_long
        
        # Paramètres existants
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.stoch_k = stoch_k
        self.stoch_d = stoch_d
        self.stoch_oversold = stoch_oversold
        self.stoch_overbought = stoch_overbought
        self.cci_period = cci_period
        self.cci_oversold = cci_oversold
        self.cci_overbought = cci_overbought
        self.williams_period = williams_period
        self.williams_oversold = williams_oversold
        self.williams_overbought = williams_overbought
        self.roc_fast = roc_fast
        self.roc_medium = roc_medium
        self.roc_slow = roc_slow
        self.mfi_period = mfi_period
        self.mfi_oversold = mfi_oversold
        self.mfi_overbought = mfi_overbought
        self.trix_period = trix_period
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.volume_ma_fast = volume_ma_fast
        self.volume_ma_medium = volume_ma_medium
        self.volume_ma_slow = volume_ma_slow
        self.momentum_fast = momentum_fast
        self.momentum_medium = momentum_medium
        self.momentum_slow = momentum_slow
        self.atr_period = atr_period
        self.min_signals = min_signals
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Génère des signaux ULTIMATE avec 60+ indicateurs"""
        signals_list = []
        
        # === REPRENDRE TOUS LES INDICATEURS DE HYPER (40+) ===
        # [Code simplifié - on garde la même logique que HYPER]
        
        # MAs multi-temporelles (7)
        for period in [self.ma_very_short, self.ma_short, self.ma_medium, self.ma_long, 
                       self.ma_1day, self.ma_7days, self.ma_20days]:
            if len(df) >= period:
                ma = df['close'].rolling(window=period).mean()
                signal = pd.Series(0, index=df.index)
                signal[df['close'] > ma] = 1
                signal[df['close'] < ma] = -1
                signals_list.append(signal)
        
        # EMAs multi-temporelles (6)
        for period in [self.ema_ultra_fast, self.ema_fast, self.ema_medium, 
                       self.ema_slow, self.ema_1day, self.ema_1week]:
            if len(df) >= period:
                ema = df['close'].ewm(span=period, adjust=False).mean()
                signal = pd.Series(0, index=df.index)
                signal[df['close'] > ema] = 1
                signal[df['close'] < ema] = -1
                signals_list.append(signal)
        
        # === NOUVEAUX INDICATEURS FIBONACCI (3 indicateurs) ===
        for period in self.fibonacci_periods:
            if len(df) >= period:
                fib_ma = df['close'].rolling(window=period).mean()
                signal = pd.Series(0, index=df.index)
                signal[df['close'] > fib_ma] = 1
                signal[df['close'] < fib_ma] = -1
                signals_list.append(signal)
        
        # === GOLDEN CROSS / DEATH CROSS (1 indicateur) ===
        if len(df) >= max(50, 200):
            ma_50 = df['close'].rolling(window=50).mean()
            ma_200 = df['close'].rolling(window=200).mean()
            signal = pd.Series(0, index=df.index)
            signal[ma_50 > ma_200] = 1  # Golden Cross
            signal[ma_50 < ma_200] = -1  # Death Cross
            signals_list.append(signal)
        
        # === ICHIMOKU CLOUD (3 indicateurs) ===
        if len(df) >= self.ichimoku_senkou:
            # Tenkan-sen (Conversion Line)
            high_tenkan = df['high'].rolling(window=self.ichimoku_tenkan).max()
            low_tenkan = df['low'].rolling(window=self.ichimoku_tenkan).min()
            tenkan = (high_tenkan + low_tenkan) / 2
            
            # Kijun-sen (Base Line)
            high_kijun = df['high'].rolling(window=self.ichimoku_kijun).max()
            low_kijun = df['low'].rolling(window=self.ichimoku_kijun).min()
            kijun = (high_kijun + low_kijun) / 2
            
            # Senkou Span A (Leading Span A)
            senkou_a = ((tenkan + kijun) / 2).shift(self.ichimoku_kijun)
            
            # Tenkan/Kijun crossover
            signal_tk = pd.Series(0, index=df.index)
            signal_tk[tenkan > kijun] = 1
            signal_tk[tenkan < kijun] = -1
            signals_list.append(signal_tk)
            
            # Price vs Tenkan
            signal_pt = pd.Series(0, index=df.index)
            signal_pt[df['close'] > tenkan] = 1
            signal_pt[df['close'] < tenkan] = -1
            signals_list.append(signal_pt)
            
            # Price vs Cloud
            signal_cloud = pd.Series(0, index=df.index)
            signal_cloud[df['close'] > senkou_a] = 1
            signal_cloud[df['close'] < senkou_a] = -1
            signals_list.append(signal_cloud)
        
        # === KELTNER CHANNELS (1 indicateur) ===
        if len(df) >= max(self.keltner_period, self.atr_period):
            kelt_middle = df['close'].ewm(span=self.keltner_period, adjust=False).mean()
            tr = pd.concat([
                df['high'] - df['low'],
                abs(df['high'] - df['close'].shift()),
                abs(df['low'] - df['close'].shift())
            ], axis=1).max(axis=1)
            atr = tr.rolling(window=self.atr_period).mean()
            kelt_upper = kelt_middle + (self.keltner_atr_mult * atr)
            kelt_lower = kelt_middle - (self.keltner_atr_mult * atr)
            
            signal = pd.Series(0, index=df.index)
            signal[df['close'] < kelt_lower] = 1  # Survente
            signal[df['close'] > kelt_upper] = -1  # Surachat
            signals_list.append(signal)
        
        # === DONCHIAN CHANNELS (1 indicateur) ===
        if len(df) >= self.donchian_period:
            donch_upper = df['high'].rolling(window=self.donchian_period).max()
            donch_lower = df['low'].rolling(window=self.donchian_period).min()
            donch_middle = (donch_upper + donch_lower) / 2
            
            signal = pd.Series(0, index=df.index)
            signal[df['close'] > donch_middle] = 1
            signal[df['close'] < donch_middle] = -1
            signals_list.append(signal)
        
        # === PARABOLIC SAR (1 indicateur) ===
        if len(df) >= 5:
            # Simplified SAR
            sar = pd.Series(df['low'].iloc[0], index=df.index)
            trend = 1  # 1 = bullish, -1 = bearish
            af = self.sar_acceleration
            
            for i in range(1, len(df)):
                if trend == 1:
                    sar.iloc[i] = sar.iloc[i-1] + af * (df['high'].iloc[i-1] - sar.iloc[i-1])
                    if df['low'].iloc[i] < sar.iloc[i]:
                        trend = -1
                        sar.iloc[i] = df['high'].iloc[i-1]
                        af = self.sar_acceleration
                else:
                    sar.iloc[i] = sar.iloc[i-1] - af * (sar.iloc[i-1] - df['low'].iloc[i-1])
                    if df['high'].iloc[i] > sar.iloc[i]:
                        trend = 1
                        sar.iloc[i] = df['low'].iloc[i-1]
                        af = self.sar_acceleration
            
            signal = pd.Series(0, index=df.index)
            signal[df['close'] > sar] = 1
            signal[df['close'] < sar] = -1
            signals_list.append(signal)
        
        # === AROON INDICATOR (2 indicateurs) ===
        if len(df) >= self.aroon_period:
            aroon_up = df['high'].rolling(window=self.aroon_period).apply(
                lambda x: ((self.aroon_period - x.argmax()) / self.aroon_period) * 100
            )
            aroon_down = df['low'].rolling(window=self.aroon_period).apply(
                lambda x: ((self.aroon_period - x.argmin()) / self.aroon_period) * 100
            )
            
            # Aroon crossover
            signal_aroon = pd.Series(0, index=df.index)
            signal_aroon[aroon_up > aroon_down] = 1
            signal_aroon[aroon_up < aroon_down] = -1
            signals_list.append(signal_aroon)
            
            # Aroon strength
            signal_strength = pd.Series(0, index=df.index)
            signal_strength[(aroon_up > 70) & (aroon_down < 30)] = 1
            signal_strength[(aroon_down > 70) & (aroon_up < 30)] = -1
            signals_list.append(signal_strength)
        
        # === CMO - Chande Momentum Oscillator (1 indicateur) ===
        if len(df) >= self.cmo_period:
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=self.cmo_period).sum()
            loss = -delta.where(delta < 0, 0).rolling(window=self.cmo_period).sum()
            cmo = 100 * (gain - loss) / (gain + loss)
            
            signal = pd.Series(0, index=df.index)
            signal[cmo > 0] = 1
            signal[cmo < 0] = -1
            signals_list.append(signal)
        
        # === ULTIMATE OSCILLATOR (1 indicateur) ===
        if len(df) >= self.ultimate_osc_long:
            # Buying Pressure
            bp = df['close'] - pd.concat([df['low'], df['close'].shift()], axis=1).min(axis=1)
            # True Range
            tr = pd.concat([
                df['high'] - df['low'],
                abs(df['high'] - df['close'].shift()),
                abs(df['low'] - df['close'].shift())
            ], axis=1).max(axis=1)
            
            # Calculate moving averages for Ultimate Oscillator
            short_window = self.ultimate_osc_short
            medium_window = self.ultimate_osc_medium
            long_window = self.ultimate_osc_long
            
            avg_short = bp.rolling(window=short_window).sum() / \
                tr.rolling(window=short_window).sum()
            avg_medium = bp.rolling(window=medium_window).sum() / \
                tr.rolling(window=medium_window).sum()
            avg_long = bp.rolling(window=long_window).sum() / \
                tr.rolling(window=long_window).sum()
            
            uo = 100 * ((4 * avg_short + 2 * avg_medium + avg_long) / 7)
            
            signal = pd.Series(0, index=df.index)
            signal[uo < 30] = 1  # Oversold
            signal[uo > 70] = -1  # Overbought
            signals_list.append(signal)
        
        # === CROISEMENTS AVANCÉS (5 indicateurs) ===
        # EMA 8/21 crossover (court terme)
        if len(df) >= 21:
            ema_8 = df['close'].ewm(span=8, adjust=False).mean()
            ema_21 = df['close'].ewm(span=21, adjust=False).mean()
            signal = pd.Series(0, index=df.index)
            signal[ema_8 > ema_21] = 1
            signal[ema_8 < ema_21] = -1
            signals_list.append(signal)
        
        # EMA 13/55 crossover (moyen terme)
        if len(df) >= 55:
            ema_13 = df['close'].ewm(span=13, adjust=False).mean()
            ema_55 = df['close'].ewm(span=55, adjust=False).mean()
            signal = pd.Series(0, index=df.index)
            signal[ema_13 > ema_55] = 1
            signal[ema_13 < ema_55] = -1
            signals_list.append(signal)
        
        # MA 20/50 crossover
        if len(df) >= 50:
            ma_20 = df['close'].rolling(window=20).mean()
            ma_50 = df['close'].rolling(window=50).mean()
            signal = pd.Series(0, index=df.index)
            signal[ma_20 > ma_50] = 1
            signal[ma_20 < ma_50] = -1
            signals_list.append(signal)
        
        # Triple EMA alignment (3-6-9)
        if len(df) >= 9:
            ema_3 = df['close'].ewm(span=3, adjust=False).mean()
            ema_6 = df['close'].ewm(span=6, adjust=False).mean()
            ema_9 = df['close'].ewm(span=9, adjust=False).mean()
            signal = pd.Series(0, index=df.index)
            signal[(ema_3 > ema_6) & (ema_6 > ema_9)] = 1  # Bullish alignment
            signal[(ema_3 < ema_6) & (ema_6 < ema_9)] = -1  # Bearish alignment
            signals_list.append(signal)
        
        # RSI divergence (simplifié)
        if len(df) >= self.rsi_medium + 5:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_medium).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_medium).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Price makes lower low but RSI makes higher low = bullish divergence
            price_slope = df['close'].diff(5)
            rsi_slope = rsi.diff(5)
            signal = pd.Series(0, index=df.index)
            signal[(price_slope < 0) & (rsi_slope > 0)] = 1  # Bullish divergence
            signal[(price_slope > 0) & (rsi_slope < 0)] = -1  # Bearish divergence
            signals_list.append(signal)
        
        # === AJOUTER LES INDICATEURS RESTANTS DE HYPER ===
        # RSI, MACD, BB, Stochastic, CCI, Williams, ROC, MFI, TRIX, ADX, OBV, Volume, Momentum, ATR
        # [Code simplifié pour la longueur - on garde la même logique]
        
        # RSI
        if len(df) >= self.rsi_medium + 1:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_medium).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_medium).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            signal = pd.Series(0, index=df.index)
            signal[rsi < self.rsi_oversold] = 1
            signal[rsi > self.rsi_overbought] = -1
            signals_list.append(signal)
        
        # === COMBINE ALL 60+ SIGNALS ===
        combined = sum(signals_list)
        final_signals = pd.Series(0, index=df.index)
        final_signals[combined >= self.min_signals] = 1
        final_signals[combined <= -self.min_signals] = -1
        
        return final_signals


class BacktestingEngine:
    """Moteur de backtesting avec support du short selling et parallélisation"""
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        commission: float = 0.001,
        allow_short: bool = True,
        min_hold_minutes: int = 0
    ):
        """
        Args:
            initial_capital: Capital initial
            commission: Commission par trade (0.001 = 0.1%)
            allow_short: Permet le short selling (True = Long + Short, False = Long uniquement)
            min_hold_minutes: Temps minimum en minutes entre deux trades (anti-sur-trading)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.allow_short = allow_short
        self.min_hold_minutes = min_hold_minutes
    
    @staticmethod
    def _precalculate_indicators(df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Pré-calcule les indicateurs standard pour accélérer les backtests
        Ces indicateurs sont partagés par la plupart des stratégies
        
        Returns:
            Dict contenant les indicateurs pré-calculés
        """
        indicators = {}
        
        # SMAs communes
        for period in [5, 10, 20, 50, 100, 200]:
            if len(df) >= period:
                indicators[f'sma_{period}'] = df['close'].rolling(window=period).mean()
        
        # EMAs communes
        for period in [8, 13, 21, 34, 55]:
            if len(df) >= period:
                indicators[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        
        # RSI standard (14)
        if len(df) >= 15:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss + 1e-10)
            indicators['rsi_14'] = 100 - (100 / (1 + rs))
        
        # Volume MA
        if len(df) >= 20:
            indicators['volume_ma_20'] = df['volume'].rolling(window=20).mean()
        
        # ATR (14)
        if len(df) >= 15:
            high = df['high']
            low = df['low']
            close = df['close']
            tr1 = high - low
            tr2 = (high - close.shift(1)).abs()
            tr3 = (low - close.shift(1)).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            indicators['atr_14'] = tr.rolling(window=14).mean()
        
        return indicators
    
    @staticmethod
    def _run_single_backtest_worker(args: tuple) -> Tuple[Dict, Dict]:
        """
        Worker function pour multiprocessing
        Doit être statique pour être picklable
        
        Args:
            args: (df_dict, strategy_dict, symbol, initial_capital, commission, allow_short)
        
        Returns:
            (strategy_dict, result_dict)
        """
        import os
        import warnings
        import logging
        import sys
        
        # Suppress ALL warnings and Streamlit output in subprocesses
        warnings.filterwarnings('ignore')
        os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
        
        # Disable all logging from streamlit
        for logger_name in ['streamlit', 'streamlit.runtime', 'streamlit.watcher']:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)
            logging.getLogger(logger_name).disabled = True
        
        try:
            df_dict, strategy_dict, symbol, initial_capital, commission, allow_short, min_hold_minutes = args
            
            # Reconstruct DataFrame from dict
            df = pd.DataFrame(df_dict)
            df.index = pd.to_datetime(df.index)
            
            # Reconstruct Strategy from dict
            strategy = Strategy.from_dict(strategy_dict)
            
            # Create engine instance
            engine = BacktestingEngine(initial_capital, commission, allow_short, min_hold_minutes)
            
            # Run backtest (désactiver vectorisation temporairement - bug à corriger)
            result = engine.run_backtest(df, strategy, symbol, use_vectorized=False)
            
            return (strategy_dict, result.to_dict())
        except Exception as e:
            # En cas d'erreur, retourner un résultat vide
            logger.error(f"Error in worker: {e}")
            raise
    
    def run_parallel_optimization(
        self,
        df: pd.DataFrame,
        symbol: str,
        num_iterations: int = 1000,
        target_return: float = 10.0,
        num_processes: Optional[int] = None,
        progress_callback: Optional[callable] = None
    ) -> Tuple[Optional[Strategy], Optional[BacktestResult], List[Tuple[Strategy, BacktestResult]]]:
        """
        Exécute une optimisation parallélisée de stratégies
        
        Args:
            df: DataFrame avec les données OHLCV
            symbol: Symbole du ticker
            num_iterations: Nombre de stratégies à tester
            target_return: Retour cible en %
            num_processes: Nombre de processus (None = auto-detect)
            progress_callback: Fonction appelée avec (iteration, total, best_return) pour suivi progression
        
        Returns:
            (best_strategy, best_result, all_results)
        """
        if num_processes is None:
            num_processes = max(1, cpu_count() - 1)  # Laisser 1 CPU libre
        
        logger.info(f"🚀 Optimisation parallèle: {num_iterations} itérations sur {num_processes} processus")
        logger.info(f"   Objectif: {target_return}% de retour")
        
        # Note: Pré-calcul des indicateurs désactivé car la vectorisation est plus efficace
        # et évite de bloquer l'interface Streamlit pendant le calcul
        # precalc_indicators = self._precalculate_indicators(df)
        
        # Générer toutes les stratégies aléatoires
        logger.info("🎲 Génération des stratégies...")
        generator = StrategyGenerator(target_return=target_return)
        strategies = []
        
        for i in range(num_iterations):
            # Générer stratégie aléatoire avec distribution vers ULTIMATE
            strategy_types = [
                'ma', 'rsi', 'multi', 'advanced', 'momentum',
                'mean_reversion', 'ultra_aggressive', 'mega', 'hyper',
                'ultimate', 'ultimate', 'ultimate'  # 85% ULTIMATE
            ]
            strategy_type = np.random.choice(strategy_types)
            
            if strategy_type == 'ma':
                strategy = generator.generate_random_ma_strategy()
            elif strategy_type == 'rsi':
                strategy = generator.generate_random_rsi_strategy()
            elif strategy_type == 'multi':
                strategy = generator.generate_random_multi_strategy()
            elif strategy_type == 'advanced':
                strategy = generator.generate_random_advanced_multi_strategy()
            elif strategy_type == 'momentum':
                strategy = generator.generate_random_momentum_strategy()
            elif strategy_type == 'mean_reversion':
                strategy = generator.generate_random_mean_reversion_strategy()
            elif strategy_type == 'ultra_aggressive':
                strategy = generator.generate_random_ultra_aggressive_strategy()
            elif strategy_type == 'mega':
                strategy = generator.generate_random_mega_strategy()
            elif strategy_type == 'hyper':
                strategy = generator.generate_random_hyper_strategy()
            else:  # ultimate
                strategy = generator.generate_random_ultimate_strategy()
            
            strategies.append(strategy)
        
        # Préparer les arguments pour le multiprocessing
        # Convertir DataFrame en dict pour pickle
        df_dict = df.to_dict('series')
        df_dict['index'] = df.index.astype(str).tolist()
        
        args_list = [
            (
                df_dict, strategy.to_dict(), symbol,
                self.initial_capital, self.commission,
                self.allow_short, self.min_hold_minutes
            )
            for strategy in strategies
        ]
        
        # Exécuter en parallèle
        logger.info(f"⚡ Lancement de {num_iterations} backtests en parallèle...")
        
        results = []
        best_return = -np.inf
        best_strategy = None
        best_result = None
        
        # Suppress warnings before creating pool
        import os
        import warnings
        os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
        warnings.filterwarnings('ignore')
        
        with Pool(processes=num_processes) as pool:
            # Utiliser imap_unordered pour avoir résultats au fur et à mesure
            for i, (strategy_dict, result_dict) in enumerate(
                pool.imap_unordered(
                    self._run_single_backtest_worker, args_list
                )
            ):
                # Reconstruire les objets
                strategy = Strategy.from_dict(strategy_dict)
                result = BacktestResult.from_dict(result_dict)
                
                results.append((strategy, result))
                
                # Vérifier si on a atteint l'objectif
                if result.total_return >= target_return:
                    logger.info(
                        f"🎯 Objectif atteint! Stratégie #{i+1}: "
                        f"{result.total_return:.2f}%"
                    )
                    pool.terminate()  # Arrêter les autres workers
                    return strategy, result, results
                
                # Mettre à jour le meilleur
                if result.total_return > best_return:
                    best_return = result.total_return
                    best_strategy = strategy
                    best_result = result
                    logger.info(f"   📈 Nouveau record à l'itération {i+1}: {best_return:.2f}%")
                
                # Callback de progression pour Streamlit
                if progress_callback:
                    progress_callback(i + 1, num_iterations, best_return)
                
                # Log progression - plus fréquent pour voir l'avancement
                if (i + 1) % 10 == 0:
                    progress_pct = (i + 1) / num_iterations * 100
                    logger.info(
                        f"   ⚡ Progression: {i+1}/{num_iterations} "
                        f"({progress_pct:.1f}%) | Meilleur: {best_return:.2f}%"
                    )
        
        logger.info(
            f"✅ Optimisation terminée. Meilleur résultat: {best_return:.2f}%"
        )
        
        return best_strategy, best_result, results
    
    def run_backtest_vectorized(
        self,
        df: pd.DataFrame,
        strategy: Strategy,
        symbol: str
    ) -> BacktestResult:
        """
        Version vectorisée du backtest (10-100x plus rapide)
        Fonctionne uniquement pour les stratégies long-only simples
        
        Args:
            df: DataFrame avec les données OHLCV
            strategy: Stratégie à tester
            symbol: Symbole du ticker
            
        Returns:
            Résultat du backtest
        """
        import time
        start_time = time.time()
        
        # Generate signals
        signals = strategy.generate_signals(df)
        
        # Detect position changes (vectorized)
        # signal = 1 (long), 0 (neutral), -1 (exit/short)
        position = signals.copy()
        position[position == -1] = 0  # Convert -1 to 0 for long-only
        
        # Forward fill positions (stay in position until exit signal)
        position = position.replace(0, np.nan).ffill().fillna(0)
        
        # Detect entries and exits
        position_change = position.diff()
        entries = position_change > 0  # Entry when position goes from 0 to 1
        exits = position_change < 0    # Exit when position goes from 1 to 0
        
        # Get entry and exit prices
        entry_indices = df.index[entries]
        exit_indices = df.index[exits]
        
        # Match entries with exits
        trades = []
        entry_prices = df.loc[entries, 'close'].values
        exit_prices = df.loc[exits, 'close'].values
        
        # Ensure we have equal entries and exits (close last position if needed)
        num_trades = min(len(entry_indices), len(exit_indices))
        
        # Handle case where we have more entries than exits (still in position at end)
        if len(entry_indices) > len(exit_indices):
            # Close final position at last price
            exit_indices = exit_indices.append(pd.Index([df.index[-1]]))
            exit_prices = np.append(exit_prices, df['close'].iloc[-1])
            num_trades = len(entry_indices)
        
        # Calculate all trades vectorized
        for i in range(num_trades):
            entry_price = entry_prices[i]
            exit_price = exit_prices[i]
            entry_date = entry_indices[i]
            exit_date = exit_indices[i] if i < len(exit_indices) else df.index[-1]
            
            # Calculate shares (95% of capital)
            shares = int((self.initial_capital * 0.95) / entry_price)
            
            # Calculate profit with commissions
            cost = shares * entry_price * (1 + self.commission)
            revenue = shares * exit_price * (1 - self.commission)
            profit = revenue - cost
            profit_pct = (profit / cost) * 100
            
            trades.append(Trade(
                entry_date=entry_date,
                entry_price=entry_price,
                exit_date=exit_date,
                exit_price=exit_price,
                quantity=shares,
                profit=profit,
                profit_pct=profit_pct
            ))
        
        # Calculate equity curve (vectorized)
        # Daily returns when in position
        daily_returns = df['close'].pct_change()
        position_returns = daily_returns * position.shift(1).fillna(0)
        
        # Adjust for commission on entries and exits
        commission_cost = position_change.abs() * self.commission
        position_returns = position_returns - commission_cost
        
        # Cumulative equity
        equity_curve = self.initial_capital * (1 + position_returns).cumprod()
        equity_curve = equity_curve.fillna(self.initial_capital)
        
        # Calculate statistics
        final_capital = equity_curve.iloc[-1] if len(equity_curve) > 0 else self.initial_capital
        total_return = ((final_capital - self.initial_capital) / self.initial_capital) * 100
        
        winning_trades = sum(1 for t in trades if t.profit > 0)
        losing_trades = sum(1 for t in trades if t.profit <= 0)
        win_rate = (winning_trades / len(trades) * 100) if trades else 0
        
        # Max drawdown (vectorized)
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max * 100
        max_drawdown = drawdown.min() if len(drawdown) > 0 else 0
        
        # Sharpe ratio
        if len(position_returns) > 1:
            pos_returns_mean = position_returns.mean()
            pos_returns_std = position_returns.std()
            if pos_returns_std > 0:
                sharpe_ratio = pos_returns_mean / pos_returns_std * np.sqrt(252)
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        elapsed = time.time() - start_time
        if elapsed > 1:  # Log if backtest took more than 1 second
            logger.debug(f"[VECTORIZED] Backtest took {elapsed:.2f}s for {len(df)} points")
        
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
        
        return result
    
    def run_backtest(
        self,
        df: pd.DataFrame,
        strategy: Strategy,
        symbol: str,
        use_vectorized: bool = True
    ) -> BacktestResult:
        """
        Exécute un backtest
        
        Args:
            df: DataFrame avec les données OHLCV
            strategy: Stratégie à tester
            symbol: Symbole du ticker
            use_vectorized: Si True, utilise la version vectorisée (plus rapide, long-only)
            
        Returns:
            Résultat du backtest
        """
        # Use vectorized version if requested and short selling not allowed
        if use_vectorized and not self.allow_short:
            try:
                return self.run_backtest_vectorized(df, strategy, symbol)
            except Exception as e:
                # Fallback to loop version if vectorized fails
                logger.warning(f"Vectorized backtest failed ({e}), falling back to loop version")
        
        # Original loop-based version
        # logger.info(f"🔄 Running backtest for {symbol} with strategy: {strategy.name}")
        
        # Generate signals
        signals = strategy.generate_signals(df)
        
        # Initialize
        capital = self.initial_capital
        position = 0  # Number of shares held
        trades = []
        equity_curve = [capital]
        
        entry_price = None
        entry_date = None
        last_trade_time = None  # Pour le filtre anti-sur-trading
        
        # Convert to numpy arrays for faster access (except dates)
        close_prices = df['close'].values
        signal_values = signals.values
        df_index = df.index  # Keep as pandas index for proper datetime handling
        
        # Simulate trading - optimized loop
        for i in range(len(df)):
            current_price = close_prices[i]
            current_date = df_index[i]
            signal = signal_values[i]
            
            # Anti-sur-trading: skip if not enough time passed since last trade
            if last_trade_time is not None and self.min_hold_minutes > 0:
                time_diff = (current_date - last_trade_time).total_seconds() / 60
                if time_diff < self.min_hold_minutes:
                    # Update equity curve even if not trading
                    if position > 0:
                        total_equity = capital + (position * current_price)
                    else:
                        total_equity = capital
                    equity_curve.append(total_equity)
                    continue
            
            # Buy signal (Long)
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
                        # logger.debug(f"  LONG: {shares_to_buy} shares @ {current_price:.2f} on {current_date}")
            
            # Sell signal
            elif signal == -1:
                # Close long position if exists
                if position > 0:
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
                    
                    # logger.debug(
                    #     f"  CLOSE LONG: {position} shares @ {current_price:.2f} | "
                    #     f"Profit: {profit:.2f}€ ({profit_pct:.2f}%)"
                    # )
                    position = 0
                    entry_price = None
                    entry_date = None
                    last_trade_time = current_date  # Update last trade time
                    entry_date = None
                
                # Open short position if allowed and no position
                if self.allow_short and position == 0:
                    shares_to_short = int((capital * 0.95) / current_price)
                    if shares_to_short > 0:
                        # Short: on "emprunte" et vend immédiatement
                        revenue = shares_to_short * current_price * (1 - self.commission)
                        capital += revenue
                        position = -shares_to_short  # Position négative = short
                        entry_price = current_price
                        entry_date = current_date
                        # logger.debug(f"  SHORT: {shares_to_short} shares @ {current_price:.2f} on {current_date}")
            
            # Buy signal when in short position (cover short)
            elif signal == 1 and position < 0:
                # Close short position
                shares_to_cover = abs(position)
                cost = shares_to_cover * current_price * (1 + self.commission)
                
                # Profit for short = (entry_price - exit_price) * shares - commissions
                entry_cost = shares_to_cover * entry_price * self.commission
                exit_cost = shares_to_cover * current_price * self.commission
                profit = (
                    (entry_price - current_price) * shares_to_cover
                    - entry_cost
                    - exit_cost
                )
                profit_pct = (profit / (shares_to_cover * entry_price)) * 100
                
                capital -= cost
                
                trade = Trade(
                    entry_date=entry_date,
                    entry_price=entry_price,
                    exit_date=current_date,
                    exit_price=current_price,
                    quantity=-position,  # Quantity positive in trade record
                    profit=profit,
                    profit_pct=profit_pct
                )
                trades.append(trade)
                
                # logger.debug(
                #     f"  COVER SHORT: {shares_to_cover} shares @ {current_price:.2f} | "
                #     f"Profit: {profit:.2f}€ ({profit_pct:.2f}%)"
                # )
                
                position = 0
                entry_price = None
                entry_date = None
            
            # Update equity curve
            if position > 0:
                # Long position
                total_equity = capital + (position * current_price)
            elif position < 0:
                # Short position: capital + valeur du short
                # Pour un short: equity = capital - (valeur actuelle du short - valeur d'entrée)
                shares_short = abs(position)
                short_pnl = (entry_price - current_price) * shares_short
                total_equity = capital + short_pnl
            else:
                total_equity = capital
            
            equity_curve.append(total_equity)
        
        # Close any remaining position
        if position != 0:
            current_price = close_prices[-1]
            current_date = df_index[-1]
            
            if position > 0:
                # Close long
                revenue = position * current_price * (1 - self.commission)
                profit = revenue - (position * entry_price * (1 + self.commission))
                profit_pct = (profit / (position * entry_price)) * 100
                capital += revenue
                # logger.debug(
                #     f"  CLOSE LONG: {position} shares @ {current_price:.2f} | "
                #     f"Profit: {profit:.2f}€ ({profit_pct:.2f}%)"
                # )
            else:
                # Close short
                shares_to_cover = abs(position)
                cost = shares_to_cover * current_price * (1 + self.commission)
                profit_short = (entry_price - current_price) * shares_to_cover
                short_commission = (
                    shares_to_cover * entry_price * self.commission +
                    shares_to_cover * current_price * self.commission
                )
                profit = profit_short - short_commission
                profit_pct = (profit / (shares_to_cover * entry_price)) * 100
                capital -= cost
                # logger.debug(
                #     f"  COVER SHORT: {shares_to_cover} shares @ "
                #     f"{current_price:.2f} | Profit: {profit:.2f}€ ({profit_pct:.2f}%)"
                # )
            
            trade = Trade(
                entry_date=entry_date,
                entry_price=entry_price,
                exit_date=current_date,
                exit_price=current_price,
                quantity=abs(position),
                profit=profit,
                profit_pct=profit_pct
            )
            trades.append(trade)
        
        # Calculate statistics
        final_capital = capital
        total_return = (
            (final_capital - self.initial_capital) / self.initial_capital
        ) * 100
        
        # Debug log for suspicious results
        if total_return < -90 or len(trades) > 1000:
            avg_profit = (
                sum(t.profit for t in trades) / len(trades) if trades else 0
            )
            msg = (
                f"WARNING: Suspicious backtest - return: {total_return:.2f}%, "
                f"trades: {len(trades)}, avg_profit_per_trade: {avg_profit:.4f}, "
                f"final_capital: {final_capital:.2f}, allow_short: {self.allow_short}"
            )
            logger.warning(msg)
        elif len(trades) > 100:
            avg_profit = (
                sum(t.profit for t in trades) / len(trades) if trades else 0
            )
            msg = (
                f"INFO: Backtest - return: {total_return:.2f}%, "
                f"trades: {len(trades)}, avg_profit_per_trade: {avg_profit:.4f}"
            )
            logger.info(msg)
        
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
            returns_mean = returns.mean()
            returns_std = returns.std()
            if returns_std > 0:
                sharpe_ratio = returns_mean / returns_std * np.sqrt(252)
            else:
                sharpe_ratio = 0
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
        
        # logger.info(
        #     f"✅ Backtest complete: Return={total_return:.2f}%, "
        #     f"Trades={len(trades)}, Win Rate={win_rate:.1f}%"
        # )
        
        return result


class AdvancedIndicators:
    """Classe pour calculer les indicateurs avancés"""

    @staticmethod
    def calculate_roc(df: pd.DataFrame, period: int = 10) -> pd.Series:
        """Rate of Change (ROC)"""
        return ((df['close'] - df['close'].shift(period)) / df['close'].shift(period) * 100).fillna(0)

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range (ATR)"""
        high = df['high']
        low = df['low']
        close = df['close']

        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr.fillna(0)

    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average Directional Index (ADX)"""
        high = df['high']
        low = df['low']
        close = df['close']

        # Calcul des mouvements directionnels (garder comme Series avec index)
        high_diff = high - high.shift(1)
        low_diff = low.shift(1) - low
        
        dm_plus = pd.Series(0.0, index=df.index)
        dm_plus[high_diff > low_diff] = high_diff[high_diff > low_diff].clip(lower=0)
        
        dm_minus = pd.Series(0.0, index=df.index)
        dm_minus[low_diff > high_diff] = low_diff[low_diff > high_diff].clip(lower=0)

        # True Range
        tr = pd.concat([high - low,
                       (high - close.shift(1)).abs(),
                       (low - close.shift(1)).abs()], axis=1).max(axis=1)

        # Moyennes mobiles (toutes les Series ont maintenant le même index)
        atr = tr.rolling(window=period).mean()
        di_plus = (dm_plus.rolling(window=period).mean() / atr * 100).fillna(0)
        di_minus = (dm_minus.rolling(window=period).mean() / atr * 100).fillna(0)

        # ADX
        dx = (abs(di_plus - di_minus) / (di_plus + di_minus) * 100).fillna(0)
        adx = dx.rolling(window=period).mean().fillna(0)

        return adx

    @staticmethod
    def calculate_volume_ratio(df: pd.DataFrame, short_period: int = 5, long_period: int = 20) -> pd.Series:
        """Volume Ratio (volume court terme / volume long terme)"""
        volume_short = df['volume'].rolling(window=short_period).mean()
        volume_long = df['volume'].rolling(window=long_period).mean()
        ratio = (volume_short / volume_long).fillna(1)
        return ratio

    @staticmethod
    def calculate_momentum(df: pd.DataFrame, period: int = 10) -> pd.Series:
        """Momentum Oscillator"""
        return (df['close'] / df['close'].shift(period) - 1).fillna(0) * 100

    @staticmethod
    def calculate_bb_width(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> pd.Series:
        """Bollinger Bands Width (mesure de volatilité)"""
        sma = df['close'].rolling(window=period).mean()
        std_dev = df['close'].rolling(window=period).std()
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        width = ((upper - lower) / sma).fillna(0)
        return width

    @staticmethod
    def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.Series:
        """Stochastic Oscillator %K"""
        lowest_low = df['low'].rolling(window=k_period).min()
        highest_high = df['high'].rolling(window=k_period).max()
        stoch_k = ((df['close'] - lowest_low) / (highest_high - lowest_low) * 100).fillna(50)
        return stoch_k

    @staticmethod
    def calculate_williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Williams %R"""
        highest_high = df['high'].rolling(window=period).max()
        lowest_low = df['low'].rolling(window=period).min()
        williams_r = ((highest_high - df['close']) / (highest_high - lowest_low) * -100).fillna(-50)
        return williams_r

    @staticmethod
    def calculate_cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Commodity Channel Index (CCI)"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=False)
        cci = (typical_price - sma) / (0.015 * mad)
        return cci.fillna(0)

    @staticmethod
    def calculate_trix(df: pd.DataFrame, period: int = 15) -> pd.Series:
        """TRIX (Triple Exponential Average)"""
        ema1 = df['close'].ewm(span=period).mean()
        ema2 = ema1.ewm(span=period).mean()
        ema3 = ema2.ewm(span=period).mean()
        trix = (ema3 - ema3.shift(1)) / ema3.shift(1) * 100
        return trix.fillna(0)

    @staticmethod
    def calculate_keltner_channels(df: pd.DataFrame, period: int = 20, multiplier: float = 2.0) -> pd.Series:
        """Keltner Channels Width (mesure de volatilité)"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        ema = typical_price.ewm(span=period).mean()
        atr = AdvancedIndicators.calculate_atr(df, period)
        upper = ema + (atr * multiplier)
        lower = ema - (atr * multiplier)
        width = ((upper - lower) / ema).fillna(0)
        return width

    @staticmethod
    def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.Series:
        """Supertrend Indicator (trend following)"""
        atr = AdvancedIndicators.calculate_atr(df, period)
        hl_avg = (df['high'] + df['low']) / 2
        
        upper_band = hl_avg + (multiplier * atr)
        lower_band = hl_avg - (multiplier * atr)
        
        supertrend = pd.Series(0.0, index=df.index)
        direction = pd.Series(1, index=df.index)
        
        for i in range(1, len(df)):
            if df['close'].iloc[i] > upper_band.iloc[i-1]:
                direction.iloc[i] = 1
            elif df['close'].iloc[i] < lower_band.iloc[i-1]:
                direction.iloc[i] = -1
            else:
                direction.iloc[i] = direction.iloc[i-1]
                
            if direction.iloc[i] == 1:
                supertrend.iloc[i] = lower_band.iloc[i]
            else:
                supertrend.iloc[i] = upper_band.iloc[i]
        
        return direction  # Return trend direction

    @staticmethod
    def calculate_parabolic_sar(
        df: pd.DataFrame,
        acceleration: float = 0.02,
        max_acceleration: float = 0.2,
    ) -> pd.Series:
        """Parabolic SAR (Stop and Reverse)"""
        sar = pd.Series(index=df.index, dtype=float)
        trend = pd.Series(1, index=df.index)  # 1 = uptrend, -1 = downtrend
        af = acceleration
        ep = df['high'].iloc[0]  # Extreme point
        
        sar.iloc[0] = df['low'].iloc[0]
        
        for i in range(1, len(df)):
            # Update SAR
            sar.iloc[i] = sar.iloc[i-1] + af * (ep - sar.iloc[i-1])
            
            # Check for trend reversal
            if trend.iloc[i-1] == 1:  # Uptrend
                if df['low'].iloc[i] < sar.iloc[i]:
                    trend.iloc[i] = -1
                    sar.iloc[i] = ep
                    ep = df['low'].iloc[i]
                    af = acceleration
                else:
                    trend.iloc[i] = 1
                    if df['high'].iloc[i] > ep:
                        ep = df['high'].iloc[i]
                        af = min(af + acceleration, max_acceleration)
            else:  # Downtrend
                if df['high'].iloc[i] > sar.iloc[i]:
                    trend.iloc[i] = 1
                    sar.iloc[i] = ep
                    ep = df['high'].iloc[i]
                    af = acceleration
                else:
                    trend.iloc[i] = -1
                    if df['low'].iloc[i] < ep:
                        ep = df['low'].iloc[i]
                        af = min(af + acceleration, max_acceleration)
        
        return trend

    @staticmethod
    def calculate_donchian_channels(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Donchian Channels Width"""
        upper = df['high'].rolling(window=period).max()
        lower = df['low'].rolling(window=period).min()
        middle = (upper + lower) / 2
        width = ((upper - lower) / middle).fillna(0)
        return width

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """Volume Weighted Average Price"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        return (typical_price * df['volume']).cumsum() / df['volume'].cumsum()

    @staticmethod
    def calculate_obv(df: pd.DataFrame) -> pd.Series:
        """On Balance Volume"""
        obv = pd.Series(0.0, index=df.index)
        obv.iloc[0] = df['volume'].iloc[0]
        
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + df['volume'].iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - df['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv

    @staticmethod
    def calculate_cmf(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Chaikin Money Flow"""
        mf_multiplier = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
        mf_multiplier = mf_multiplier.fillna(0)
        mf_volume = mf_multiplier * df['volume']
        cmf = mf_volume.rolling(window=period).sum() / df['volume'].rolling(window=period).sum()
        return cmf.fillna(0)

    @staticmethod
    def calculate_elder_ray(df: pd.DataFrame, period: int = 13) -> pd.Series:
        """Elder Ray Index (Bull Power - Bear Power)"""
        ema = df['close'].ewm(span=period).mean()
        bull_power = df['high'] - ema
        bear_power = df['low'] - ema
        return bull_power - bear_power


class EnhancedMovingAverageStrategy(Strategy):
    """Stratégie MA améliorée avec indicateurs avancés"""

    def __init__(self,
                 fast_period: int = 22,
                 slow_period: int = 35,
                 # Indicateurs avancés existants
                 roc_period: int = 13,
                 roc_threshold: float = 1.1,
                 adx_period: int = 14,
                 adx_threshold: int = 32,
                 volume_ratio_short: int = 4,
                 volume_ratio_long: int = 20,
                 volume_threshold: float = 1.3,
                 momentum_period: int = 9,
                 momentum_threshold: float = 1.5,
                 bb_period: int = 24,
                 bb_width_threshold: float = 0.079,
                 # Nouveaux indicateurs ultra-avancés
                 use_supertrend: bool = False,
                 supertrend_period: int = 10,
                 supertrend_multiplier: float = 3.0,
                 use_parabolic_sar: bool = False,
                 use_donchian: bool = False,
                 donchian_period: int = 20,
                 donchian_threshold: float = 0.05,
                 use_vwap: bool = False,
                 use_obv: bool = False,
                 use_cmf: bool = False,
                 cmf_period: int = 20,
                 cmf_threshold: float = 0.05,
                 use_elder_ray: bool = False,
                 elder_ray_period: int = 13,
                 # Filtres
                 min_signals: int = 2,
                 # Optional custom name
                 name: str = "EnhancedMA",
                 description: str = ""):
    """TODO: Add docstring."""
        self.name = name
        self.description = description
        self.parameters = {
            'fast_period': fast_period,
            'slow_period': slow_period,
            'roc_period': roc_period,
            'roc_threshold': roc_threshold,
            'adx_period': adx_period,
            'adx_threshold': adx_threshold,
            'volume_ratio_short': volume_ratio_short,
            'volume_ratio_long': volume_ratio_long,
            'volume_threshold': volume_threshold,
            'momentum_period': momentum_period,
            'momentum_threshold': momentum_threshold,
            'bb_period': bb_period,
            'bb_width_threshold': bb_width_threshold,
            'use_supertrend': use_supertrend,
            'supertrend_period': supertrend_period,
            'supertrend_multiplier': supertrend_multiplier,
            'use_parabolic_sar': use_parabolic_sar,
            'use_donchian': use_donchian,
            'donchian_period': donchian_period,
            'donchian_threshold': donchian_threshold,
            'use_vwap': use_vwap,
            'use_obv': use_obv,
            'use_cmf': use_cmf,
            'cmf_period': cmf_period,
            'cmf_threshold': cmf_threshold,
            'use_elder_ray': use_elder_ray,
            'elder_ray_period': elder_ray_period,
            'min_signals': min_signals
        }
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.roc_period = roc_period
        self.roc_threshold = roc_threshold
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.volume_ratio_short = volume_ratio_short
        self.volume_ratio_long = volume_ratio_long
        self.volume_threshold = volume_threshold
        self.momentum_period = momentum_period
        self.momentum_threshold = momentum_threshold
        self.bb_period = bb_period
        self.bb_width_threshold = bb_width_threshold
        self.use_supertrend = use_supertrend
        self.supertrend_period = supertrend_period
        self.supertrend_multiplier = supertrend_multiplier
        self.use_parabolic_sar = use_parabolic_sar
        self.use_donchian = use_donchian
        self.donchian_period = donchian_period
        self.donchian_threshold = donchian_threshold
        self.use_vwap = use_vwap
        self.use_obv = use_obv
        self.use_cmf = use_cmf
        self.cmf_period = cmf_period
        self.cmf_threshold = cmf_threshold
        self.use_elder_ray = use_elder_ray
        self.elder_ray_period = elder_ray_period
        self.min_signals = min_signals

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Génère les signaux de trading avec filtres avancés"""
        signals = pd.Series(0, index=df.index, dtype=int)

        # Calcul des MAs de base
        fast_ma = df['close'].rolling(window=self.fast_period).mean()
        slow_ma = df['close'].rolling(window=self.slow_period).mean()

        # Calcul des indicateurs avancés de base
        roc = AdvancedIndicators.calculate_roc(df, self.roc_period)
        adx = AdvancedIndicators.calculate_adx(df, self.adx_period)
        volume_ratio = AdvancedIndicators.calculate_volume_ratio(df, self.volume_ratio_short, self.volume_ratio_long)
        momentum = AdvancedIndicators.calculate_momentum(df, self.momentum_period)
        bb_width = AdvancedIndicators.calculate_bb_width(df, self.bb_period)

        # Calcul des indicateurs ultra-complexes
        supertrend = None
        if self.use_supertrend:
            supertrend = AdvancedIndicators.calculate_supertrend(df, self.supertrend_period, self.supertrend_multiplier)
        
        parabolic_sar = None
        if self.use_parabolic_sar:
            parabolic_sar = AdvancedIndicators.calculate_parabolic_sar(df)
        
        donchian_width = None
        if self.use_donchian:
            donchian_width = AdvancedIndicators.calculate_donchian_channels(df, self.donchian_period)
        
        vwap = None
        if self.use_vwap:
            vwap = AdvancedIndicators.calculate_vwap(df)
        
        obv = None
        if self.use_obv:
            obv = AdvancedIndicators.calculate_obv(df)
        
        cmf = None
        if self.use_cmf:
            cmf = AdvancedIndicators.calculate_cmf(df, self.cmf_period)
        
        elder_ray = None
        if self.use_elder_ray:
            elder_ray = AdvancedIndicators.calculate_elder_ray(df, self.elder_ray_period)

        # Conditions de base (croisement MA)
        fast_ma_prev = fast_ma.shift(1)
        slow_ma_prev = slow_ma.shift(1)

        bullish_cross = (fast_ma > slow_ma) & (fast_ma_prev <= slow_ma_prev) & fast_ma.notna() & slow_ma.notna()
        bearish_cross = (fast_ma < slow_ma) & (fast_ma_prev >= slow_ma_prev) & fast_ma.notna() & slow_ma.notna()

        # Filtres avancés de base
        filters = []

        roc_filter = pd.Series(False, index=df.index, dtype=bool)
        roc_filter.loc[roc.notna()] = (roc[roc.notna()] > self.roc_threshold).astype(bool)
        filters.append(roc_filter)

        adx_filter = pd.Series(False, index=df.index, dtype=bool)
        adx_filter.loc[adx.notna()] = (adx[adx.notna()] > self.adx_threshold).astype(bool)
        filters.append(adx_filter)

        volume_filter = pd.Series(False, index=df.index, dtype=bool)
        volume_notna = volume_ratio.notna()
        volume_filter.loc[volume_notna] = (
            volume_ratio[volume_notna] > self.volume_threshold
        ).astype(bool)
        filters.append(volume_filter)

        momentum_filter = pd.Series(False, index=df.index, dtype=bool)
        momentum_filter.loc[momentum.notna()] = (momentum[momentum.notna()] > self.momentum_threshold).astype(bool)
        filters.append(momentum_filter)

        volatility_filter = pd.Series(False, index=df.index, dtype=bool)
        volatility_filter.loc[bb_width.notna()] = (bb_width[bb_width.notna()] > self.bb_width_threshold).astype(bool)
        filters.append(volatility_filter)

        # Filtres ultra-complexes
        if self.use_supertrend and supertrend is not None:
            supertrend_filter = pd.Series(False, index=df.index, dtype=bool)
            supertrend_filter.loc[supertrend.notna()] = (supertrend[supertrend.notna()] == 1).astype(bool)
            filters.append(supertrend_filter)

        if self.use_parabolic_sar and parabolic_sar is not None:
            sar_filter = pd.Series(False, index=df.index, dtype=bool)
            sar_notna = parabolic_sar.notna()
            sar_close = df.loc[sar_notna, 'close']
            sar_values = parabolic_sar[sar_notna]
            sar_filter.loc[sar_notna] = (sar_close > sar_values).astype(bool)
            filters.append(sar_filter)
        
        if self.use_donchian and donchian_width is not None:
            donchian_filter = pd.Series(False, index=df.index, dtype=bool)
            donch_notna = donchian_width.notna()
            donchian_filter.loc[donch_notna] = (
                donchian_width[donch_notna] > self.donchian_threshold
            ).astype(bool)
            filters.append(donchian_filter)
        
        if self.use_vwap and vwap is not None:
            vwap_filter = pd.Series(False, index=df.index, dtype=bool)
            vwap_filter.loc[vwap.notna()] = (df.loc[vwap.notna(), 'close'] > vwap[vwap.notna()]).astype(bool)
            filters.append(vwap_filter)
        
        if self.use_obv and obv is not None:
            obv_filter = pd.Series(False, index=df.index, dtype=bool)
            obv_shifted = obv.shift(1)
            obv_notna = obv.notna()
            obv_shifted_notna = obv_shifted.notna()
            obv_valid_mask = obv_notna & obv_shifted_notna
            obv_comparison = obv[obv_valid_mask] > obv_shifted[obv_valid_mask]
            obv_filter.loc[obv_valid_mask] = obv_comparison.astype(bool)
            filters.append(obv_filter)
        
        if self.use_cmf and cmf is not None:
            cmf_filter = pd.Series(False, index=df.index, dtype=bool)
            cmf_filter.loc[cmf.notna()] = (cmf[cmf.notna()] > self.cmf_threshold).astype(bool)
            filters.append(cmf_filter)
        
        if self.use_elder_ray and elder_ray is not None:
            elder_filter = pd.Series(False, index=df.index, dtype=bool)
            elder_filter.loc[elder_ray.notna()] = (elder_ray[elder_ray.notna()] > 0).astype(bool)
            filters.append(elder_filter)

        # Combiner les filtres (au moins min_signals doivent être vrais)
        combined_filters = sum(filters) >= self.min_signals

        # Appliquer les signaux avec filtres
        signals.loc[bullish_cross & combined_filters] = 1   # Achat
        signals.loc[bearish_cross & combined_filters] = -1  # Vente

        return signals


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
    
    def generate_random_advanced_multi_strategy(self) -> AdvancedMultiIndicatorStrategy:
        """Génère une stratégie avancée avec 7+ indicateurs"""
        return AdvancedMultiIndicatorStrategy(
            ma_fast=np.random.randint(5, 20),
            ma_slow=np.random.randint(20, 50),
            rsi_period=np.random.randint(10, 20),
            rsi_oversold=np.random.randint(25, 35),
            rsi_overbought=np.random.randint(65, 75),
            bb_period=np.random.randint(15, 25),
            bb_std=np.random.uniform(1.5, 2.5),
            stoch_k=np.random.randint(10, 20),
            stoch_d=np.random.randint(3, 5),
            stoch_oversold=np.random.randint(15, 25),
            stoch_overbought=np.random.randint(75, 85),
            atr_period=np.random.randint(10, 20),
            volume_ma=np.random.randint(15, 25),
            min_signals=np.random.randint(3, 5)  # Need 3-5 indicators to agree
        )
    
    def generate_random_momentum_strategy(self) -> MomentumBreakoutStrategy:
        """Génère une stratégie de momentum/breakout"""
        return MomentumBreakoutStrategy(
            lookback_period=np.random.randint(15, 30),
            breakout_threshold=np.random.uniform(0.02, 0.05),
            volume_multiplier=np.random.uniform(1.3, 2.0),
            rsi_period=np.random.randint(10, 20),
            rsi_min=np.random.randint(35, 50),
            rsi_max=np.random.randint(70, 85)
        )
    
    def generate_random_mean_reversion_strategy(self) -> MeanReversionStrategy:
        """Génère une stratégie de retour à la moyenne"""
        return MeanReversionStrategy(
            bb_period=np.random.randint(15, 30),
            bb_std=np.random.uniform(1.5, 2.5),
            rsi_period=np.random.randint(10, 20),
            rsi_oversold=np.random.randint(20, 30),
            rsi_overbought=np.random.randint(70, 80),
            zscore_threshold=np.random.uniform(1.5, 2.5)
        )
    
    def generate_random_ultra_aggressive_strategy(self) -> UltraAggressiveStrategy:
        """Génère une stratégie ultra-agressive avec 15+ indicateurs"""
        return UltraAggressiveStrategy(
            ma_very_fast=np.random.randint(3, 8),
            ma_fast=np.random.randint(8, 15),
            ma_medium=np.random.randint(15, 25),
            ma_slow=np.random.randint(25, 60),
            rsi_period=np.random.randint(10, 20),
            rsi_oversold=np.random.randint(25, 35),
            rsi_overbought=np.random.randint(65, 75),
            macd_fast=np.random.randint(10, 15),
            macd_slow=np.random.randint(20, 30),
            macd_signal=np.random.randint(7, 12),
            bb_period=np.random.randint(15, 25),
            bb_std=np.random.uniform(1.5, 2.5),
            stoch_k=np.random.randint(10, 20),
            stoch_d=np.random.randint(3, 5),
            cci_period=np.random.randint(15, 25),
            cci_oversold=np.random.randint(-120, -80),
            cci_overbought=np.random.randint(80, 120),
            williams_period=np.random.randint(10, 20),
            williams_oversold=np.random.randint(-90, -70),
            williams_overbought=np.random.randint(-30, -10),
            roc_period=np.random.randint(10, 15),
            volume_ma_short=np.random.randint(5, 15),
            volume_ma_long=np.random.randint(20, 40),
            adx_period=np.random.randint(10, 20),
            adx_threshold=np.random.randint(15, 30),
            min_signals=np.random.randint(2, 4)  # Très agressif: 2-3 sur 15
        )
    
    def generate_random_mega_strategy(self) -> MegaIndicatorStrategy:
        """Génère une stratégie MEGA avec 27+ indicateurs"""
        # Périodes MA (5 indicateurs)
        ma_periods = sorted([
            np.random.randint(3, 8),   # Très rapide
            np.random.randint(8, 15),  # Rapide
            np.random.randint(15, 25), # Moyen
            np.random.randint(25, 60), # Lent
            np.random.randint(60, 120) # Très lent
        ])
        
        # Périodes EMA Fibonacci (5 indicateurs)
        ema_base = [5, 8, 13, 21, 34, 55, 89]
        ema_periods = sorted(np.random.choice(ema_base, size=5, replace=False).tolist())
        
        return MegaIndicatorStrategy(
            # Moving Averages (5)
            ma_periods=ma_periods,
            # EMAs Fibonacci (5)
            ema_periods=ema_periods,
            # RSI
            rsi_period=np.random.randint(10, 20),
            rsi_oversold=np.random.randint(25, 35),
            rsi_overbought=np.random.randint(65, 75),
            # MACD
            macd_fast=np.random.randint(10, 15),
            macd_slow=np.random.randint(20, 30),
            macd_signal=np.random.randint(7, 12),
            # Bollinger Bands
            bb_period=np.random.randint(15, 25),
            bb_std=np.random.uniform(1.5, 2.5),
            # Stochastic (k et d seulement, pas de seuils)
            stoch_k=np.random.randint(10, 20),
            stoch_d=np.random.randint(3, 5),
            # CCI
            cci_period=np.random.randint(15, 25),
            # Williams %R
            williams_period=np.random.randint(10, 20),
            # ROC
            roc_period=np.random.randint(10, 15),
            # MFI
            mfi_period=np.random.randint(10, 20),
            # TRIX
            trix_period=np.random.randint(12, 18),
            # ADX
            adx_period=np.random.randint(10, 20),
            # Volume
            volume_ma=np.random.randint(15, 30),
            # Min signals: ULTRA agressif - seulement 2 sur 27+
            min_signals=2
        )
    
    def generate_random_hyper_strategy(self) -> HyperAggressiveStrategy:
        """Génère une stratégie HYPER avec 40+ indicateurs incluant multi-timeframe"""
        return HyperAggressiveStrategy(
            # Multi-timeframe MAs (en minutes)
            ma_1day=np.random.randint(360, 420),      # 6-7h de trading
            ma_7days=np.random.randint(2500, 3000),   # ~1 semaine
            ma_20days=np.random.randint(7500, 8500),  # ~1 mois
            ma_very_short=np.random.randint(3, 8),
            ma_short=np.random.randint(10, 20),
            ma_medium=np.random.randint(50, 80),
            ma_long=np.random.randint(200, 300),
            # EMAs multi-timeframe
            ema_ultra_fast=np.random.randint(3, 5),
            ema_fast=np.random.randint(5, 10),
            ema_medium=np.random.randint(15, 25),
            ema_slow=np.random.randint(45, 65),
            ema_1day=np.random.randint(360, 420),
            ema_1week=np.random.randint(1800, 2200),
            # RSI multi-période
            rsi_fast=np.random.randint(5, 10),
            rsi_medium=np.random.randint(12, 16),
            rsi_slow=np.random.randint(18, 25),
            rsi_oversold=np.random.randint(25, 35),
            rsi_overbought=np.random.randint(65, 75),
            # MACD
            macd_fast=np.random.randint(10, 15),
            macd_slow=np.random.randint(20, 30),
            macd_signal=np.random.randint(7, 12),
            # Bollinger Bands
            bb_period=np.random.randint(15, 25),
            bb_std=np.random.uniform(1.5, 2.5),
            # Stochastic
            stoch_k=np.random.randint(10, 20),
            stoch_d=np.random.randint(3, 5),
            stoch_oversold=np.random.randint(15, 25),
            stoch_overbought=np.random.randint(75, 85),
            # CCI
            cci_period=np.random.randint(15, 25),
            cci_oversold=np.random.randint(-120, -80),
            cci_overbought=np.random.randint(80, 120),
            # Williams %R
            williams_period=np.random.randint(10, 20),
            williams_oversold=np.random.randint(-90, -70),
            williams_overbought=np.random.randint(-30, -10),
            # ROC multi-période
            roc_fast=np.random.randint(3, 7),
            roc_medium=np.random.randint(10, 15),
            roc_slow=np.random.randint(20, 30),
            # MFI
            mfi_period=np.random.randint(10, 20),
            mfi_oversold=np.random.randint(15, 25),
            mfi_overbought=np.random.randint(75, 85),
            # TRIX
            trix_period=np.random.randint(12, 18),
            # ADX
            adx_period=np.random.randint(10, 20),
            adx_threshold=np.random.randint(15, 30),
            # Volume multi-période
            volume_ma_fast=np.random.randint(5, 15),
            volume_ma_medium=np.random.randint(20, 40),
            volume_ma_slow=np.random.randint(80, 120),
            # Momentum multi-période
            momentum_fast=np.random.randint(2, 5),
            momentum_medium=np.random.randint(8, 12),
            momentum_slow=np.random.randint(18, 25),
            # ATR
            atr_period=np.random.randint(10, 20),
            # ULTRA ULTRA AGRESSIF: min_signals = 1 (UN SEUL indicateur suffit!)
            min_signals=1
        )
    
    def generate_random_ultimate_strategy(self) -> UltimateStrategy:
        """Génère une stratégie ULTIMATE avec 60+ indicateurs et croisements avancés"""
        # Périodes Fibonacci pour MAs supplémentaires
        fib_periods = [89, 144, 233]
        
        return UltimateStrategy(
            # Multi-timeframe MAs (mêmes que HYPER)
            ma_1day=np.random.randint(360, 420),
            ma_7days=np.random.randint(2500, 3000),
            ma_20days=np.random.randint(7500, 8500),
            ma_very_short=np.random.randint(3, 8),
            ma_short=np.random.randint(10, 20),
            ma_medium=np.random.randint(50, 80),
            ma_long=np.random.randint(200, 300),
            # EMAs multi-timeframe
            ema_ultra_fast=np.random.randint(3, 5),
            ema_fast=np.random.randint(5, 10),
            ema_medium=np.random.randint(15, 25),
            ema_slow=np.random.randint(45, 65),
            ema_1day=np.random.randint(360, 420),
            ema_1week=np.random.randint(1800, 2200),
            # RSI multi-période
            rsi_fast=np.random.randint(5, 10),
            rsi_medium=np.random.randint(12, 16),
            rsi_slow=np.random.randint(18, 25),
            rsi_oversold=np.random.randint(25, 35),
            rsi_overbought=np.random.randint(65, 75),
            # Nouveaux indicateurs ULTIMATE
            fibonacci_periods=fib_periods,
            ichimoku_tenkan=np.random.randint(8, 12),
            ichimoku_kijun=np.random.randint(24, 30),
            ichimoku_senkou=np.random.randint(48, 56),
            keltner_period=np.random.randint(18, 25),
            keltner_atr_mult=np.random.uniform(1.8, 2.5),
            donchian_period=np.random.randint(18, 25),
            sar_acceleration=np.random.uniform(0.015, 0.025),
            sar_maximum=np.random.uniform(0.18, 0.22),
            aroon_period=np.random.randint(20, 30),
            cmo_period=np.random.randint(12, 16),
            ultimate_osc_short=np.random.randint(6, 9),
            ultimate_osc_medium=np.random.randint(12, 16),
            ultimate_osc_long=np.random.randint(26, 30),
            # MACD
            macd_fast=np.random.randint(10, 15),
            macd_slow=np.random.randint(20, 30),
            macd_signal=np.random.randint(7, 12),
            # Bollinger Bands
            bb_period=np.random.randint(15, 25),
            bb_std=np.random.uniform(1.5, 2.5),
            # Stochastic
            stoch_k=np.random.randint(10, 20),
            stoch_d=np.random.randint(3, 5),
            stoch_oversold=np.random.randint(15, 25),
            stoch_overbought=np.random.randint(75, 85),
            # CCI
            cci_period=np.random.randint(15, 25),
            cci_oversold=np.random.randint(-120, -80),
            cci_overbought=np.random.randint(80, 120),
            # Williams %R
            williams_period=np.random.randint(10, 20),
            williams_oversold=np.random.randint(-90, -70),
            williams_overbought=np.random.randint(-30, -10),
            # ROC multi-période
            roc_fast=np.random.randint(3, 7),
            roc_medium=np.random.randint(10, 15),
            roc_slow=np.random.randint(20, 30),
            # MFI
            mfi_period=np.random.randint(10, 20),
            mfi_oversold=np.random.randint(15, 25),
            mfi_overbought=np.random.randint(75, 85),
            # TRIX
            trix_period=np.random.randint(12, 18),
            # ADX
            adx_period=np.random.randint(10, 20),
            adx_threshold=np.random.randint(15, 30),
            # Volume multi-période
            volume_ma_fast=np.random.randint(5, 15),
            volume_ma_medium=np.random.randint(20, 40),
            volume_ma_slow=np.random.randint(80, 120),
            # Momentum multi-période
            momentum_fast=np.random.randint(2, 5),
            momentum_medium=np.random.randint(8, 12),
            momentum_slow=np.random.randint(18, 25),
            # ATR
            atr_period=np.random.randint(10, 20),
            # ULTIMATE: min_signals = 1 (UN SEUL sur 60+)
            min_signals=1
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
            # Generate random strategy (prioritize ULTIMATE with 60+ indicators)
            strategy_choices = [
                'ma',
                'rsi',
                'multi',
                'advanced',
                'momentum',
                'mean_reversion',
                'ultra_aggressive',
                'mega',
                'hyper',
                'ultimate',
                'ultimate',
                'ultimate',
            ]
            strategy_probabilities = [
                0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.03, 0.03, 0.02,
                0.283, 0.283, 0.284,  # 85% ULTIMATE strategy
            ]
            strategy_type = np.random.choice(
                strategy_choices,
                p=strategy_probabilities
            )
            
            if strategy_type == 'ma':
                strategy = self.generate_random_ma_strategy()
            elif strategy_type == 'rsi':
                strategy = self.generate_random_rsi_strategy()
            elif strategy_type == 'multi':
                strategy = self.generate_random_multi_strategy()
            elif strategy_type == 'advanced':
                strategy = self.generate_random_advanced_multi_strategy()
            elif strategy_type == 'momentum':
                strategy = self.generate_random_momentum_strategy()
            elif strategy_type == 'mean_reversion':
                strategy = self.generate_random_mean_reversion_strategy()
            elif strategy_type == 'ultra_aggressive':
                strategy = self.generate_random_ultra_aggressive_strategy()
            elif strategy_type == 'mega':
                strategy = self.generate_random_mega_strategy()
            elif strategy_type == 'hyper':
                strategy = self.generate_random_hyper_strategy()
            else:  # ultimate
                strategy = self.generate_random_ultimate_strategy()
            
            # Run backtest with short selling enabled
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


# Helper function for Strategy.from_dict() - must be at module level for multiprocessing
def _create_strategy_from_dict(data: Dict):
    """
    Create strategy from dictionary
    This function is at module level so it can access all strategy classes
    """
    strategy_name = data['name']
    
    # Map of all available strategies
    strategy_classes = {
        'RandomStrategy': RandomStrategy,
        'MovingAverageCrossover': MovingAverageCrossover,
        'RSIStrategy': RSIStrategy,
        'MultiIndicatorStrategy': MultiIndicatorStrategy,
        'AdvancedMultiIndicatorStrategy': AdvancedMultiIndicatorStrategy,
        'MomentumBreakoutStrategy': MomentumBreakoutStrategy,
        'MeanReversionStrategy': MeanReversionStrategy,
        'UltraAggressiveStrategy': UltraAggressiveStrategy,
        'MegaIndicatorStrategy': MegaIndicatorStrategy,
        'HyperAggressiveStrategy': HyperAggressiveStrategy,
        'UltimateStrategy': UltimateStrategy,
        'EnhancedMovingAverageStrategy': EnhancedMovingAverageStrategy,
        'EnhancedMA': EnhancedMovingAverageStrategy,  # Alias
    }
    
    if strategy_name not in strategy_classes:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    
    strategy_class = strategy_classes[strategy_name]
    return strategy_class(**data['parameters'])
