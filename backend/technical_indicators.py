"""
Technical indicators calculation using pandas and numpy
"""
import pandas as pd
import numpy as np
from typing import Optional
from backend.config import logger


class TechnicalIndicators:
    """Calculate technical indicators for trading strategies"""
    
    @staticmethod
    def add_sma(df: pd.DataFrame, periods: list = [20, 50, 100, 200]) -> pd.DataFrame:
        """Add Simple Moving Averages"""
        for period in periods:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
        return df
    
    @staticmethod
    def add_ema(df: pd.DataFrame, periods: list = [12, 26, 50, 200]) -> pd.DataFrame:
        """Add Exponential Moving Averages"""
        for period in periods:
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        return df
    
    @staticmethod
    def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add Relative Strength Index"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
        return df
    
    @staticmethod
    def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """Add MACD (Moving Average Convergence Divergence)"""
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        return df
    
    @staticmethod
    def add_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
        """Add Bollinger Bands"""
        df['bb_middle'] = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        df['bb_upper'] = df['bb_middle'] + (std_dev * std)
        df['bb_lower'] = df['bb_middle'] - (std_dev * std)
        df['bb_width'] = df['bb_upper'] - df['bb_lower']
        df['bb_percent'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        return df
    
    @staticmethod
    def add_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """Add Stochastic Oscillator"""
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        
        df['stoch_k'] = 100 * (df['close'] - low_min) / (high_max - low_min)
        df['stoch_d'] = df['stoch_k'].rolling(window=d_period).mean()
        return df
    
    @staticmethod
    def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df[f'atr_{period}'] = true_range.rolling(window=period).mean()
        return df
    
    @staticmethod
    def add_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add Average Directional Index"""
        # Calculate True Range (keep as Series with index)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = pd.Series(np.max(ranges, axis=1), index=df.index)
        
        # Calculate price movements
        high_diff = df['high'] - df['high'].shift()
        low_diff = df['low'].shift() - df['low']
        
        # Calculate Directional Movement (keep as Series to preserve index)
        dm_plus = pd.Series(0.0, index=df.index)
        dm_plus[high_diff > low_diff] = np.maximum(high_diff[high_diff > low_diff], 0)
        
        dm_minus = pd.Series(0.0, index=df.index)
        dm_minus[low_diff > high_diff] = np.maximum(low_diff[low_diff > high_diff], 0)
        
        # Calculate Directional Indicators
        di_plus = 100 * (dm_plus.rolling(window=period).mean() / true_range.rolling(window=period).mean())
        di_minus = 100 * (dm_minus.rolling(window=period).mean() / true_range.rolling(window=period).mean())
        
        # Calculate ADX
        dx = 100 * np.abs(di_plus - di_minus) / (di_plus + di_minus)
        df['adx'] = dx.rolling(window=period).mean()
        df['di_plus'] = di_plus
        df['di_minus'] = di_minus
        return df
    
    @staticmethod
    def add_obv(df: pd.DataFrame) -> pd.DataFrame:
        """Add On-Balance Volume"""
        df['obv'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        return df
    
    @staticmethod
    def add_vwap(df: pd.DataFrame) -> pd.DataFrame:
        """Add Volume Weighted Average Price"""
        df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
        return df
    
    @staticmethod
    def add_cci(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """Add Commodity Channel Index"""
        tp = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
        df[f'cci_{period}'] = (tp - sma_tp) / (0.015 * mad)
        return df
    
    @staticmethod
    def add_williams_r(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add Williams %R"""
        high_max = df['high'].rolling(window=period).max()
        low_min = df['low'].rolling(window=period).min()
        df[f'williams_r_{period}'] = -100 * (high_max - df['close']) / (high_max - low_min)
        return df
    
    @staticmethod
    def add_roc(df: pd.DataFrame, period: int = 12) -> pd.DataFrame:
        """Add Rate of Change"""
        df[f'roc_{period}'] = ((df['close'] - df['close'].shift(period)) / df['close'].shift(period)) * 100
        return df
    
    @staticmethod
    def add_mfi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add Money Flow Index"""
        # Calculate Typical Price
        tp = (df['high'] + df['low'] + df['close']) / 3
        
        # Calculate Money Flow
        mf = tp * df['volume']
        
        # Calculate Positive and Negative Money Flow
        pmf = np.where(tp > tp.shift(1), mf, 0)
        nmf = np.where(tp < tp.shift(1), mf, 0)
        
        # Calculate Money Flow Ratio
        pmf_sum = pd.Series(pmf).rolling(window=period).sum()
        nmf_sum = pd.Series(nmf).rolling(window=period).sum()
        mfr = pmf_sum / nmf_sum
        
        # Calculate MFI
        df[f'mfi_{period}'] = 100 - (100 / (1 + mfr))
        return df
    
    @staticmethod
    def add_ichimoku(df: pd.DataFrame) -> pd.DataFrame:
        """Add Ichimoku Cloud"""
        # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
        nine_period_high = df['high'].rolling(window=9).max()
        nine_period_low = df['low'].rolling(window=9).min()
        df['ichimoku_conversion'] = (nine_period_high + nine_period_low) / 2
        
        # Kijun-sen (Base Line): (26-period high + 26-period low)/2
        period26_high = df['high'].rolling(window=26).max()
        period26_low = df['low'].rolling(window=26).min()
        df['ichimoku_base'] = (period26_high + period26_low) / 2
        
        # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2
        df['ichimoku_span_a'] = ((df['ichimoku_conversion'] + df['ichimoku_base']) / 2).shift(26)
        
        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
        period52_high = df['high'].rolling(window=52).max()
        period52_low = df['low'].rolling(window=52).min()
        df['ichimoku_span_b'] = ((period52_high + period52_low) / 2).shift(26)
        
        # Chikou Span (Lagging Span): Current closing price shifted 26 periods back
        df['ichimoku_lagging'] = df['close'].shift(-26)
        
        return df
    
    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add all available technical indicators"""
        logger.info("Calculating all technical indicators...")
        
        # Moving Averages
        df = TechnicalIndicators.add_sma(df, [20, 50, 100, 200])
        df = TechnicalIndicators.add_ema(df, [12, 26, 50, 200])
        
        # Momentum Indicators
        df = TechnicalIndicators.add_rsi(df, 14)
        df = TechnicalIndicators.add_macd(df)
        df = TechnicalIndicators.add_stochastic(df)
        df = TechnicalIndicators.add_cci(df, 20)
        df = TechnicalIndicators.add_williams_r(df, 14)
        df = TechnicalIndicators.add_roc(df, 12)
        
        # Volatility Indicators
        df = TechnicalIndicators.add_bollinger_bands(df)
        df = TechnicalIndicators.add_atr(df, 14)
        
        # Volume Indicators
        df = TechnicalIndicators.add_obv(df)
        df = TechnicalIndicators.add_vwap(df)
        df = TechnicalIndicators.add_mfi(df, 14)
        
        # Trend Indicators
        df = TechnicalIndicators.add_adx(df, 14)
        df = TechnicalIndicators.add_ichimoku(df)
        
        logger.info(f"Added {len(df.columns) - 6} technical indicators")  # -6 for OHLCV + timestamp
        return df


def calculate_and_update_indicators(df: pd.DataFrame, save_to_db: bool = False) -> pd.DataFrame:
    """
    Calculate all indicators and optionally save to database
    
    Args:
        df: DataFrame with OHLCV data
        save_to_db: Whether to update database records
        
    Returns:
        DataFrame with all indicators
    """
    if df.empty:
        logger.warning("Empty DataFrame provided")
        return df
    
    # Calculate all indicators
    df = TechnicalIndicators.add_all_indicators(df)
    
    # TODO: Implement database update if save_to_db is True
    if save_to_db:
        logger.info("Database update not yet implemented")
    
    return df


if __name__ == "__main__":
    # Test with sample data
    dates = pd.date_range('2024-01-01', periods=100, freq='1min')
    df = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100)
    })
    df.set_index('timestamp', inplace=True)
    
    # Calculate indicators
    df = calculate_and_update_indicators(df)
    print(df.columns.tolist())
    print(df.tail())
