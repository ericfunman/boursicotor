"""
Real-time technical indicators calculation
"""
import pandas as pd
import numpy as np
from typing import Optional, Tuple, List


def calculate_rsi(prices: List[float], period: int = 14) -> Optional[List[float]]:
    """
    Calculate Relative Strength Index (RSI)
    
    Args:
        prices: List of closing prices
        period: RSI period (default 14)
    
    Returns:
        List of RSI values aligned with prices
    """
    if len(prices) < period + 1:
        return None
    
    df = pd.DataFrame({'close': prices})
    
    # Calculate price changes
    delta = df['close'].diff()
    
    # Separate gains and losses
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # Calculate RS and RSI
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.tolist()


def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[Tuple[List[float], List[float], List[float]]]:
    """
    Calculate MACD (Moving Average Convergence Divergence)
    
    Args:
        prices: List of closing prices
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line period (default 9)
    
    Returns:
        Tuple of (MACD line, Signal line, Histogram)
    """
    if len(prices) < slow + signal:
        return None
    
    df = pd.DataFrame({'close': prices})
    
    # Calculate EMAs
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    
    # Calculate MACD line
    macd = ema_fast - ema_slow
    
    # Calculate Signal line
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    
    # Calculate Histogram
    histogram = macd - signal_line
    
    return macd.tolist(), signal_line.tolist(), histogram.tolist()


def calculate_bollinger_bands(prices: List[float], period: int = 20, num_std: float = 2) -> Optional[Tuple[List[float], List[float], List[float]]]:
    """
    Calculate Bollinger Bands
    
    Args:
        prices: List of closing prices
        period: Moving average period (default 20)
        num_std: Number of standard deviations (default 2)
    
    Returns:
        Tuple of (Upper band, Middle band, Lower band)
    """
    if len(prices) < period:
        return None
    
    df = pd.DataFrame({'close': prices})
    
    # Calculate SMA
    sma = df['close'].rolling(window=period).mean()
    
    # Calculate standard deviation
    std = df['close'].rolling(window=period).std()
    
    # Calculate bands
    upper = sma + (std * num_std)
    lower = sma - (std * num_std)
    
    return upper.tolist(), sma.tolist(), lower.tolist()
