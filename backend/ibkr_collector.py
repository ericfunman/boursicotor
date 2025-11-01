"""
Interactive Brokers / Lynx Data Collector
Collect historical and real-time market data via IBKR API
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv

from backend.config import logger
from backend.models import SessionLocal, Ticker as TickerModel, HistoricalData
from sqlalchemy import and_

# Load environment variables
load_dotenv()

try:
    from ib_insync import IB, Stock, util
    import nest_asyncio
    nest_asyncio.apply()  # Fix asyncio event loop for Streamlit
    IBKR_AVAILABLE = True
except ImportError:
    IBKR_AVAILABLE = False
    logger.warning("ib_insync not installed. IBKR data collection disabled.")


class IBKRCollector:
    """Collect market data from Interactive Brokers / Lynx"""
    
    def __init__(self):
        """Initialize IBKR collector"""
        if not IBKR_AVAILABLE:
            raise ImportError("ib_insync library not installed. Install with: pip install ib_insync")
        
        self.ib = IB()
        self.connected = False
        
        # Configuration from environment
        self.host = os.getenv('IBKR_HOST', '127.0.0.1')
        self.port = int(os.getenv('IBKR_PORT', '4002'))
        self.client_id = int(os.getenv('IBKR_CLIENT_ID', '1'))
        self.account = os.getenv('IBKR_ACCOUNT', 'DU0118471')
        
        logger.info(f"IBKR Collector initialized - {self.host}:{self.port}")
    
    def connect(self) -> bool:
        """Connect to IB Gateway/TWS"""
        try:
            if self.ib.isConnected():
                logger.info("Already connected to IBKR")
                return True
            
            logger.info(f"Connecting to IBKR at {self.host}:{self.port}...")
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.connected = True
            logger.info("✅ Connected to IBKR successfully")
            
            # Wait for account sync
            self.ib.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.ib.isConnected():
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR")
    
    def get_contract(self, symbol: str, exchange: str = 'SMART', currency: str = 'EUR') -> Optional[Stock]:
        """
        Get and qualify a stock contract
        
        Args:
            symbol: Stock symbol (e.g., 'WLN')
            exchange: Exchange (default: 'SMART' for automatic routing)
            currency: Currency (default: 'EUR' for European stocks)
        
        Returns:
            Qualified contract or None
        """
        try:
            contract = Stock(symbol, exchange, currency)
            contracts = self.ib.qualifyContracts(contract)
            
            if contracts:
                qualified = contracts[0]
                logger.info(f"Contract qualified: {qualified.symbol} on {qualified.primaryExchange}")
                return qualified
            else:
                logger.warning(f"Could not qualify contract for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error qualifying contract {symbol}: {e}")
            return None
    
    def get_historical_data(
        self,
        symbol: str,
        duration: str = '1 D',
        bar_size: str = '1 min',
        what_to_show: str = 'TRADES',
        use_rth: bool = False,
        exchange: str = 'SMART',
        currency: str = 'EUR'
    ) -> Optional[pd.DataFrame]:
        """
        Get historical data for a symbol
        
        Args:
            symbol: Stock symbol
            duration: Duration string (e.g., '1 D', '1 W', '1 M', '1 Y')
            bar_size: Bar size (e.g., '1 min', '5 mins', '1 hour', '1 day')
            what_to_show: Data type ('TRADES', 'MIDPOINT', 'BID', 'ASK')
            use_rth: Use regular trading hours only
            exchange: Exchange
            currency: Currency
        
        Returns:
            DataFrame with OHLCV data or None
        """
        try:
            if not self.connected:
                if not self.connect():
                    return None
            
            # Get contract
            contract = self.get_contract(symbol, exchange, currency)
            if not contract:
                return None
            
            logger.info(f"Requesting historical data: {symbol} - {duration} - {bar_size}")
            
            # Request historical data
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow=what_to_show,
                useRTH=use_rth,
                formatDate=1
            )
            
            if not bars:
                logger.warning(f"No historical data received for {symbol}")
                return None
            
            # Convert to DataFrame
            df = util.df(bars)
            
            if df.empty:
                logger.warning(f"Empty DataFrame for {symbol}")
                return None
            
            # Rename columns to match our schema
            df = df.rename(columns={
                'date': 'timestamp',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            })
            
            # Ensure timestamp is datetime
            if not isinstance(df['timestamp'].iloc[0], datetime):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            logger.info(f"✅ Received {len(df)} bars for {symbol}")
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return None
    
    def save_to_database(
        self,
        symbol: str,
        df: pd.DataFrame,
        interval: str,
        name: str = None,
        progress_callback=None
    ) -> Dict[str, any]:
        """
        Save historical data to database
        
        Args:
            symbol: Stock symbol
            df: DataFrame with historical data
            interval: Interval string (e.g., '1min', '1h', '1day')
            name: Stock name (optional)
            progress_callback: Optional callback function(current, total) for progress updates
        
        Returns:
            Dict with success status and statistics
        """
        db = SessionLocal()
        try:
            # Get or create ticker
            ticker = db.query(TickerModel).filter(TickerModel.symbol == symbol).first()
            
            if not ticker:
                ticker = TickerModel(
                    symbol=symbol,
                    name=name or symbol,
                    exchange='Euronext Paris'
                )
                db.add(ticker)
                db.commit()
                db.refresh(ticker)
                logger.info(f"Created new ticker: {symbol}")
            
            # Save historical data
            new_records = 0
            updated_records = 0
            total_rows = len(df)
            
            for idx, (_, row) in enumerate(df.iterrows()):
                # Update progress
                if progress_callback:
                    progress_callback(idx + 1, total_rows)
                
                # Check if record exists
                existing = db.query(HistoricalData).filter(
                    and_(
                        HistoricalData.ticker_id == ticker.id,
                        HistoricalData.timestamp == row['timestamp'],
                        HistoricalData.interval == interval
                    )
                ).first()
                
                if existing:
                    # Update existing record
                    existing.open = float(row['open'])
                    existing.high = float(row['high'])
                    existing.low = float(row['low'])
                    existing.close = float(row['close'])
                    existing.volume = int(row['volume'])
                    updated_records += 1
                else:
                    # Create new record
                    new_record = HistoricalData(
                        ticker_id=ticker.id,
                        timestamp=row['timestamp'],
                        open=float(row['open']),
                        high=float(row['high']),
                        low=float(row['low']),
                        close=float(row['close']),
                        volume=int(row['volume']),
                        interval=interval
                    )
                    db.add(new_record)
                    new_records += 1
            
            db.commit()
            
            logger.info(f"✅ Saved to database: {new_records} new, {updated_records} updated")
            
            return {
                'success': True,
                'symbol': symbol,
                'new_records': new_records,
                'updated_records': updated_records,
                'total_records': len(df),
                'interval': interval,
                'date_range': f"{df['timestamp'].min()} to {df['timestamp'].max()}"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving to database: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        
        finally:
            db.close()
    
    def collect_and_save(
        self,
        symbol: str,
        duration: str = '1 M',
        bar_size: str = '1 min',
        interval: str = '1min',
        name: str = None,
        progress_callback=None
    ) -> Dict[str, any]:
        """
        Collect historical data and save to database
        
        Args:
            symbol: Stock symbol
            duration: Duration string
            bar_size: Bar size for IBKR API
            interval: Interval for database storage
            name: Stock name
            progress_callback: Optional callback function(current, total) for progress updates
        
        Returns:
            Dict with results
        """
        try:
            # Get historical data
            df = self.get_historical_data(symbol, duration, bar_size)
            
            if df is None or df.empty:
                return {
                    'success': False,
                    'error': 'No data received from IBKR'
                }
            
            # Save to database
            result = self.save_to_database(symbol, df, interval, name, progress_callback)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in collect_and_save: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_account_summary(self) -> Optional[Dict[str, any]]:
        """
        Get account summary information
        
        Returns:
            Dict with account information or None
        """
        try:
            if not self.connected:
                if not self.connect():
                    return None
            
            # Get account summary
            summary = self.ib.accountSummary()
            self.ib.sleep(1)
            
            result = {}
            for item in summary:
                if item.currency not in result:
                    result[item.currency] = {}
                result[item.currency][item.tag] = item.value
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            return None
    
    def get_positions(self) -> List[Dict[str, any]]:
        """
        Get current positions
        
        Returns:
            List of positions
        """
        try:
            if not self.connected:
                if not self.connect():
                    return []
            
            positions = self.ib.positions()
            
            result = []
            for pos in positions:
                result.append({
                    'symbol': pos.contract.symbol,
                    'position': pos.position,
                    'avg_cost': pos.avgCost,
                    'market_value': pos.position * pos.avgCost,
                    'currency': pos.contract.currency
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def __del__(self):
        """Cleanup on deletion"""
        self.disconnect()


# Interval mapping for IBKR
IBKR_INTERVAL_MAP = {
    '1min': ('1 min', '1min'),
    '5min': ('5 mins', '5min'),
    '15min': ('15 mins', '15min'),
    '30min': ('30 mins', '30min'),
    '1h': ('1 hour', '1h'),
    '1day': ('1 day', '1day'),
}

IBKR_DURATION_MAP = {
    '1D': '1 D',
    '1W': '1 W',
    '2W': '2 W',
    '1M': '1 M',
    '3M': '3 M',
    '6M': '6 M',
    '1Y': '1 Y',
    '2Y': '2 Y',
}
