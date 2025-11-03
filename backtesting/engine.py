"""
Backtesting engine for testing trading strategies
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from backend.config import logger


@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    initial_capital: float = 10000.0
    commission: float = 0.001  # 0.1%
    slippage: float = 0.0005  # 0.05%
    max_position_size: float = 10000.0
    risk_per_trade: float = 0.02  # 2%


@dataclass
class Trade:
    """Trade record"""
    entry_time: datetime
    exit_time: Optional[datetime]
    symbol: str
    direction: str  # 'LONG' or 'SHORT'
    entry_price: float
    exit_price: Optional[float]
    quantity: int
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    commission: float = 0.0
    status: str = 'OPEN'  # 'OPEN', 'CLOSED'


class BacktestEngine:
    """Backtesting engine for strategy evaluation"""
    
    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.reset()
    
    def reset(self):
        """Reset backtesting state"""
        self.capital = self.config.initial_capital
        self.positions: List[Trade] = []
        self.closed_trades: List[Trade] = []
        self.equity_curve: List[float] = [self.config.initial_capital]
        self.timestamps: List[datetime] = []
    
    def open_position(
        self,
        timestamp: datetime,
        symbol: str,
        direction: str,
        price: float,
        quantity: int = None,
        percent_capital: float = None
    ) -> Optional[Trade]:
        """
        Open a new position
        
        Args:
            timestamp: Entry timestamp
            symbol: Symbol to trade
            direction: 'LONG' or 'SHORT'
            price: Entry price
            quantity: Number of shares (optional if percent_capital is provided)
            percent_capital: Percentage of capital to use (optional if quantity is provided)
            
        Returns:
            Trade object if successful, None otherwise
        """
        # Calculate quantity if not provided
        if quantity is None and percent_capital is not None:
            position_value = self.capital * percent_capital
            quantity = int(position_value / price)
        
        if quantity is None or quantity <= 0:
            logger.warning("Invalid quantity for opening position")
            return None
        
        # Calculate position value
        position_value = quantity * price
        
        # Check if we have enough capital
        if position_value > self.capital:
            logger.warning(f"Insufficient capital: need {position_value}, have {self.capital}")
            return None
        
        # Check max position size
        if position_value > self.config.max_position_size:
            logger.warning(f"Position size {position_value} exceeds max {self.config.max_position_size}")
            return None
        
        # Calculate commission
        commission = position_value * self.config.commission
        
        # Apply slippage
        slippage_amount = price * self.config.slippage
        effective_price = price + slippage_amount if direction == 'LONG' else price - slippage_amount
        
        # Create trade
        trade = Trade(
            entry_time=timestamp,
            exit_time=None,
            symbol=symbol,
            direction=direction,
            entry_price=effective_price,
            exit_price=None,
            quantity=quantity,
            commission=commission,
            status='OPEN'
        )
        
        # Update capital
        self.capital -= (position_value + commission)
        self.positions.append(trade)
        
        logger.info(f"Opened {direction} position: {quantity} shares at {effective_price:.2f}")
        return trade
    
    def close_position(
        self,
        timestamp: datetime,
        trade: Trade,
        price: float
    ) -> Optional[Trade]:
        """
        Close an existing position
        
        Args:
            timestamp: Exit timestamp
            trade: Trade to close
            price: Exit price
            
        Returns:
            Closed trade object
        """
        if trade.status != 'OPEN':
            logger.warning("Trade already closed")
            return None
        
        # Apply slippage
        slippage_amount = price * self.config.slippage
        effective_price = price - slippage_amount if trade.direction == 'LONG' else price + slippage_amount
        
        # Calculate P&L
        if trade.direction == 'LONG':
            pnl = (effective_price - trade.entry_price) * trade.quantity
        else:  # SHORT
            pnl = (trade.entry_price - effective_price) * trade.quantity
        
        # Calculate commission
        exit_commission = effective_price * trade.quantity * self.config.commission
        pnl -= (trade.commission + exit_commission)
        
        # Update trade
        trade.exit_time = timestamp
        trade.exit_price = effective_price
        trade.pnl = pnl
        trade.pnl_percent = (pnl / (trade.entry_price * trade.quantity)) * 100
        trade.status = 'CLOSED'
        trade.commission += exit_commission
        
        # Update capital
        self.capital += (effective_price * trade.quantity + pnl)
        
        # Move to closed trades
        self.positions.remove(trade)
        self.closed_trades.append(trade)
        
        logger.info(f"Closed {trade.direction} position: P&L = {pnl:.2f} ({trade.pnl_percent:.2f}%)")
        return trade
    
    def update_equity(self, timestamp: datetime, current_prices: Dict[str, float]):
        """
        Update equity curve with current prices
        
        Args:
            timestamp: Current timestamp
            current_prices: Dictionary of symbol -> current price
        """
        total_value = self.capital
        
        # Add value of open positions
        for trade in self.positions:
            if trade.symbol in current_prices:
                current_price = current_prices[trade.symbol]
                if trade.direction == 'LONG':
                    position_value = current_price * trade.quantity
                else:  # SHORT
                    position_value = (2 * trade.entry_price - current_price) * trade.quantity
                total_value += position_value
        
        self.equity_curve.append(total_value)
        self.timestamps.append(timestamp)
    
    def run_backtest(
        self,
        df: pd.DataFrame,
        strategy_func,
        symbol: str
    ) -> Dict:
        """
        Run backtest with a strategy function
        
        Args:
            df: DataFrame with OHLCV data and indicators
            strategy_func: Function that returns signals ('BUY', 'SELL', 'HOLD')
            symbol: Symbol being traded
            
        Returns:
            Backtest results dictionary
        """
        self.reset()
        
        logger.info(f"Starting backtest for {symbol} with {len(df)} bars")
        
        for idx in range(len(df)):
            current_bar = df.iloc[idx]
            timestamp = df.index[idx]
            
            # Get strategy signal
            signal = strategy_func(df.iloc[:idx+1])
            
            # Execute trades based on signal
            if signal == 'BUY' and len(self.positions) == 0:
                self.open_position(
                    timestamp=timestamp,
                    symbol=symbol,
                    direction='LONG',
                    price=current_bar['close'],
                    percent_capital=self.config.risk_per_trade
                )
            
            elif signal == 'SELL' and len(self.positions) > 0:
                for trade in self.positions[:]:  # Copy list to avoid modification during iteration
                    if trade.direction == 'LONG':
                        self.close_position(
                            timestamp=timestamp,
                            trade=trade,
                            price=current_bar['close']
                        )
            
            # Update equity curve
            self.update_equity(timestamp, {symbol: current_bar['close']})
        
        # Close any remaining positions at the end
        if self.positions:
            last_bar = df.iloc[-1]
            for trade in self.positions[:]:
                self.close_position(
                    timestamp=df.index[-1],
                    trade=trade,
                    price=last_bar['close']
                )
        
        # Calculate results
        results = self.calculate_results()
        logger.info(f"Backtest completed: Total return = {results['total_return']:.2f}%")
        
        return results
    
    def calculate_results(self) -> Dict:
        """Calculate backtest performance metrics"""
        if not self.closed_trades:
            return {
                'total_return': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'final_capital': self.capital,
            }
        
        # Total return
        total_return = ((self.capital - self.config.initial_capital) / self.config.initial_capital) * 100
        
        # Trade statistics
        wins = [t for t in self.closed_trades if t.pnl > 0]
        losses = [t for t in self.closed_trades if t.pnl <= 0]
        
        winning_trades = len(wins)
        losing_trades = len(losses)
        total_trades = len(self.closed_trades)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Average win/loss
        avg_win = np.mean([t.pnl for t in wins]) if wins else 0
        avg_loss = np.mean([t.pnl for t in losses]) if losses else 0
        
        # Profit factor
        total_wins = sum([t.pnl for t in wins]) if wins else 0
        total_losses = abs(sum([t.pnl for t in losses])) if losses else 0
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0
        
        # Max drawdown
        equity_array = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max * 100
        max_drawdown = np.min(drawdown)
        
        # Sharpe ratio (simplified)
        returns = np.diff(equity_array) / equity_array[:-1]
        sharpe_ratio = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if len(returns) > 0 and np.std(returns) > 0 else 0
        
        return {
            'initial_capital': self.config.initial_capital,
            'final_capital': self.capital,
            'total_return': total_return,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'equity_curve': self.equity_curve,
            'timestamps': self.timestamps,
            'trades': self.closed_trades,
        }


if __name__ == "__main__":
    # Test with sample data
    dates = pd.date_range('2024-01-01', periods=100, freq='1H')
    df = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    # Simple strategy: Buy when price crosses above 100, sell when below
    def simple_strategy(data):
        if len(data) < 2:
            return 'HOLD'
        current_price = data['close'].iloc[-1]
        if current_price > 100:
            return 'BUY'
        elif current_price < 100:
            return 'SELL'
        return 'HOLD'
    
    # Run backtest
    engine = BacktestEngine()
    results = engine.run_backtest(df, simple_strategy, 'TEST')
    
    print(f"Total Return: {results['total_return']:.2f}%")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']:.2f}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
