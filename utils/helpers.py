"""
Utility functions for Boursicotor
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


def format_currency(value: float, currency: str = "EUR") -> str:
    """Format value as currency"""
    if currency == "EUR":
        return f"{value:,.2f} €"
    elif currency == "USD":
        return f"${value:,.2f}"
    else:
        return f"{value:,.2f} {currency}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format value as percentage"""
    return f"{value:+.{decimals}f}%"


def calculate_position_size(
    capital: float,
    risk_percent: float,
    entry_price: float,
    stop_loss_price: float
) -> int:
    """
    Calculate position size based on risk management
    
    Args:
        capital: Total capital available
        risk_percent: Percentage of capital to risk (e.g., 0.02 for 2%)
        entry_price: Entry price per share
        stop_loss_price: Stop loss price per share
        
    Returns:
        Number of shares to buy
    """
    risk_amount = capital * risk_percent
    price_risk = abs(entry_price - stop_loss_price)
    
    if price_risk == 0:
        return 0
    
    quantity = int(risk_amount / price_risk)
    
    # Ensure we don't exceed capital
    max_quantity = int(capital / entry_price)
    
    return min(quantity, max_quantity)


def calculate_stop_loss(entry_price: float, stop_loss_percent: float, direction: str = "LONG") -> float:
    """
    Calculate stop loss price
    
    Args:
        entry_price: Entry price
        stop_loss_percent: Stop loss percentage (e.g., 0.05 for 5%)
        direction: 'LONG' or 'SHORT'
        
    Returns:
        Stop loss price
    """
    if direction == "LONG":
        return entry_price * (1 - stop_loss_percent)
    else:  # SHORT
        return entry_price * (1 + stop_loss_percent)


def calculate_take_profit(entry_price: float, target_percent: float, direction: str = "LONG") -> float:
    """
    Calculate take profit price
    
    Args:
        entry_price: Entry price
        target_percent: Target profit percentage (e.g., 0.10 for 10%)
        direction: 'LONG' or 'SHORT'
        
    Returns:
        Take profit price
    """
    if direction == "LONG":
        return entry_price * (1 + target_percent)
    else:  # SHORT
        return entry_price * (1 - target_percent)


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio
    
    Args:
        returns: Series of returns
        risk_free_rate: Annual risk-free rate (default 2%)
        
    Returns:
        Sharpe ratio
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    
    # Annualize returns (assuming daily data)
    excess_returns = returns.mean() - (risk_free_rate / 252)
    return (excess_returns / returns.std()) * np.sqrt(252)


def calculate_max_drawdown(equity_curve: List[float]) -> Tuple[float, int, int]:
    """
    Calculate maximum drawdown
    
    Args:
        equity_curve: List of equity values
        
    Returns:
        Tuple of (max_drawdown_percent, start_index, end_index)
    """
    equity_array = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity_array)
    drawdown = (equity_array - running_max) / running_max
    
    max_dd_idx = np.argmin(drawdown)
    max_dd = drawdown[max_dd_idx] * 100
    
    # Find start of drawdown
    start_idx = np.argmax(running_max[:max_dd_idx+1])
    
    return max_dd, start_idx, max_dd_idx


def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sortino ratio (similar to Sharpe but uses downside deviation)
    
    Args:
        returns: Series of returns
        risk_free_rate: Annual risk-free rate
        
    Returns:
        Sortino ratio
    """
    if len(returns) == 0:
        return 0.0
    
    # Calculate downside deviation
    negative_returns = returns[returns < 0]
    if len(negative_returns) == 0:
        return 0.0
    
    downside_std = negative_returns.std()
    if downside_std == 0:
        return 0.0
    
    excess_returns = returns.mean() - (risk_free_rate / 252)
    return (excess_returns / downside_std) * np.sqrt(252)


def calculate_win_rate(trades: List[Dict]) -> float:
    """
    Calculate win rate from list of trades
    
    Args:
        trades: List of trade dictionaries with 'pnl' key
        
    Returns:
        Win rate as percentage
    """
    if not trades:
        return 0.0
    
    winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
    return (winning_trades / len(trades)) * 100


def calculate_profit_factor(trades: List[Dict]) -> float:
    """
    Calculate profit factor (gross profit / gross loss)
    
    Args:
        trades: List of trade dictionaries with 'pnl' key
        
    Returns:
        Profit factor
    """
    if not trades:
        return 0.0
    
    gross_profit = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0)
    gross_loss = abs(sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0))
    
    if gross_loss == 0:
        return float('inf') if gross_profit > 0 else 0.0
    
    return gross_profit / gross_loss


def resample_ohlcv(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """
    Resample OHLCV data to different timeframe
    
    Args:
        df: DataFrame with OHLCV data (index must be datetime)
        timeframe: Target timeframe ('5min', '15min', '1H', '1D', etc.)
        
    Returns:
        Resampled DataFrame
    """
    resampled = df.resample(timeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })
    
    return resampled.dropna()


def validate_data_quality(df: pd.DataFrame) -> Dict[str, any]:
    """
    Validate data quality and return statistics
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        Dictionary with validation results
    """
    results = {
        'total_rows': len(df),
        'missing_values': df.isnull().sum().to_dict(),
        'duplicate_rows': df.duplicated().sum(),
        'date_range': (df.index.min(), df.index.max()) if len(df) > 0 else (None, None),
        'anomalies': []
    }
    
    # Check for price anomalies
    if 'close' in df.columns:
        # Check for zero or negative prices
        invalid_prices = (df['close'] <= 0).sum()
        if invalid_prices > 0:
            results['anomalies'].append(f"{invalid_prices} rows with invalid prices")
        
        # Check for extreme price changes
        price_changes = df['close'].pct_change()
        extreme_changes = (abs(price_changes) > 0.2).sum()  # >20% change
        if extreme_changes > 0:
            results['anomalies'].append(f"{extreme_changes} rows with extreme price changes (>20%)")
    
    # Check OHLC consistency
    if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
        inconsistent = ((df['high'] < df['low']) | 
                       (df['high'] < df['open']) | 
                       (df['high'] < df['close']) |
                       (df['low'] > df['open']) |
                       (df['low'] > df['close'])).sum()
        if inconsistent > 0:
            results['anomalies'].append(f"{inconsistent} rows with inconsistent OHLC values")
    
    return results


def generate_trading_hours(date: datetime, market: str = "EURONEXT") -> Tuple[datetime, datetime]:
    """
    Get trading hours for a specific market
    
    Args:
        date: Date to get trading hours for
        market: Market name
        
    Returns:
        Tuple of (market_open, market_close) datetime objects
    """
    # Euronext Paris trading hours: 09:00 - 17:30 CET
    if market == "EURONEXT":
        market_open = date.replace(hour=9, minute=0, second=0, microsecond=0)
        market_close = date.replace(hour=17, minute=30, second=0, microsecond=0)
    # Add other markets as needed
    else:
        market_open = date.replace(hour=9, minute=0, second=0, microsecond=0)
        market_close = date.replace(hour=17, minute=0, second=0, microsecond=0)
    
    return market_open, market_close


def is_market_open(timestamp: datetime, market: str = "EURONEXT") -> bool:
    """
    Check if market is open at given timestamp
    
    Args:
        timestamp: Timestamp to check
        market: Market name
        
    Returns:
        True if market is open
    """
    # Skip weekends
    if timestamp.weekday() >= 5:
        return False
    
    market_open, market_close = generate_trading_hours(timestamp, market)
    
    return market_open <= timestamp <= market_close


if __name__ == "__main__":
    # Test utilities
    print("Testing utility functions...")
    
    # Test currency formatting
    print(f"Currency: {format_currency(1234.56)}")
    print(f"Percentage: {format_percentage(12.345)}")
    
    # Test position sizing
    size = calculate_position_size(10000, 0.02, 50, 47.5)
    print(f"Position size: {size} shares")
    
    # Test stop loss
    sl = calculate_stop_loss(50, 0.05, "LONG")
    print(f"Stop loss: {sl:.2f}")
    
    # Test market hours
    now = datetime.now()
    is_open = is_market_open(now)
    print(f"Market open: {is_open}")
