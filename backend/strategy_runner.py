"""
Strategy Runner - Executes strategies and generates trading signals
Used by AutoTrader to calculate signals from live price data
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict
from loguru import logger
import json

from backend.models import Strategy as StrategyModel, SessionLocal
from backend.backtesting_engine import (
    SimpleMovingAverageStrategy, 
    RSIStrategy, 
    EnhancedMovingAverageStrategy
)
from backend.constants import CONST_CLOSE


class StrategyRunner:
    """Executes trading strategies and generates signals"""
    
    def __init__(self):
        """Initialize strategy runner"""
        self.strategy_cache = {}
    
    def generate_signals(self, df: pd.DataFrame, strategy_model: StrategyModel) -> Optional[pd.DataFrame]:
        """
        Generate trading signals using a strategy
        
        Args:
            df: DataFrame with OHLCV data (index should be datetime)
            strategy_model: Strategy model from database
            
        Returns:
            DataFrame with signals or None if error
        """
        try:
            if df is None or df.empty:
                logger.warning("Empty DataFrame provided to generate_signals")
                return None
            
            # Create strategy instance from database model
            strategy = self._create_strategy(strategy_model)
            
            if strategy is None:
                logger.error(f"Could not create strategy from model: {strategy_model.name}")
                return None
            
            # Generate signals
            logger.debug(f"Generating signals using {strategy_model.name}...")
            
            # Make a copy of the DataFrame to avoid modifying original
            df_copy = df.copy()
            
            # Generate base signals (-1=SELL, 0=HOLD, 1=BUY)
            signals = strategy.generate_signals(df_copy)
            
            # Add signals to DataFrame
            df_copy['signal'] = signals
            
            # Add position (cumulative signal)
            df_copy['position'] = df_copy['signal'].fillna(0)
            
            logger.debug(f"Generated {len(signals)} signals, latest signal: {signals.iloc[-1]}")
            
            return df_copy
            
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _create_strategy(self, strategy_model: StrategyModel):
        """
        Create strategy instance from database model
        
        Args:
            strategy_model: Strategy ORM model
            
        Returns:
            Strategy instance or None
        """
        try:
            strategy_type = strategy_model.strategy_type if hasattr(strategy_model, 'strategy_type') else "SMA"
            
            # Parse parameters from JSON
            params = {}
            if hasattr(strategy_model, 'parameters') and strategy_model.parameters:
                try:
                    if isinstance(strategy_model.parameters, str):
                        params = json.loads(strategy_model.parameters)
                    else:
                        params = strategy_model.parameters
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse strategy parameters: {strategy_model.parameters}")
                    params = {}
            
            logger.debug(f"Creating strategy: type={strategy_type}, params={params}")
            
            # Create appropriate strategy instance
            if strategy_type == "SMA" or strategy_type == "SimpleMovingAverage":
                return SimpleMovingAverageStrategy(
                    fast=params.get('fast_period', 10),
                    slow=params.get('slow_period', 30)
                )
            
            elif strategy_type == "RSI":
                return RSIStrategy(
                    period=params.get('period', 14),
                    oversold=params.get('oversold', 30),
                    overbought=params.get('overbought', 70)
                )
            
            elif strategy_type == "Enhanced" or strategy_type == "EnhancedMovingAverage":
                return EnhancedMovingAverageStrategy(
                    fast=params.get('fast_period', 5),
                    slow=params.get('slow_period', 20),
                    rsi_period=params.get('rsi_period', 14),
                    rsi_oversold=params.get('rsi_oversold', 30),
                    rsi_overbought=params.get('rsi_overbought', 70)
                )
            
            else:
                logger.error(f"Unknown strategy type: {strategy_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating strategy: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def get_signal_value(self, signal_series: pd.Series) -> int:
        """
        Get the latest signal value from a signal series
        
        Args:
            signal_series: Series of signal values
            
        Returns:
            Latest signal value (1=BUY, -1=SELL, 0=HOLD)
        """
        if signal_series is None or signal_series.empty:
            return 0
        
        latest = signal_series.iloc[-1]
        
        # Ensure it's an integer
        if pd.isna(latest):
            return 0
        
        return int(latest)
