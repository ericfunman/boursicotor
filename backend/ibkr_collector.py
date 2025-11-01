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
    
    # IBKR Historical Data Limitations (max duration per bar size)
    # Source: https://interactivebrokers.github.io/tws-api/historical_limitations.html
    IBKR_LIMITS = {
        '1 secs': {'max_duration': '1 D', 'chunk_days': 1},      # 1 day max
        '5 secs': {'max_duration': '2 D', 'chunk_days': 2},      # 2 days max
        '10 secs': {'max_duration': '2 D', 'chunk_days': 2},     # 2 days max
        '15 secs': {'max_duration': '2 D', 'chunk_days': 2},     # 2 days max
        '30 secs': {'max_duration': '1 W', 'chunk_days': 7},     # 1 week max
        '1 min': {'max_duration': '1 W', 'chunk_days': 7},       # 1 week max
        '2 mins': {'max_duration': '1 W', 'chunk_days': 7},      # 1 week max
        '3 mins': {'max_duration': '1 W', 'chunk_days': 7},      # 1 week max
        '5 mins': {'max_duration': '1 W', 'chunk_days': 7},      # 1 week max
        '10 mins': {'max_duration': '1 W', 'chunk_days': 7},     # 1 week max
        '15 mins': {'max_duration': '1 W', 'chunk_days': 7},     # 1 week max
        '20 mins': {'max_duration': '1 W', 'chunk_days': 7},     # 1 week max
        '30 mins': {'max_duration': '1 M', 'chunk_days': 30},    # 1 month max
        '1 hour': {'max_duration': '1 M', 'chunk_days': 30},     # 1 month max
        '2 hours': {'max_duration': '1 M', 'chunk_days': 30},    # 1 month max
        '3 hours': {'max_duration': '1 M', 'chunk_days': 30},    # 1 month max
        '4 hours': {'max_duration': '1 M', 'chunk_days': 30},    # 1 month max
        '8 hours': {'max_duration': '1 M', 'chunk_days': 30},    # 1 month max
        '1 day': {'max_duration': '1 Y', 'chunk_days': 365},     # 1 year max
        '1 week': {'max_duration': '1 Y', 'chunk_days': 365},    # 1 year max
        '1 month': {'max_duration': '1 Y', 'chunk_days': 365},   # 1 year max
    }
    
    def __init__(self, client_id: int = None):
        """Initialize IBKR collector
        
        Args:
            client_id: Custom client ID. If None, uses env var or generates random ID
        """
        if not IBKR_AVAILABLE:
            raise ImportError("ib_insync library not installed. Install with: pip install ib_insync")
        
        self.ib = IB()
        self.connected = False
        
        # Configuration from environment
        self.host = os.getenv('IBKR_HOST', '127.0.0.1')
        self.port = int(os.getenv('IBKR_PORT', '4002'))
        
        # Client ID: use provided, env var, or generate random (2-999)
        if client_id is not None:
            self.client_id = client_id
        else:
            import random
            self.client_id = int(os.getenv('IBKR_CLIENT_ID', random.randint(2, 999)))
        
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
    
    def _parse_duration_to_days(self, duration: str) -> int:
        """
        Convert IBKR duration string to number of days
        
        Args:
            duration: Duration string (e.g., '1 D', '2 W', '3 M', '1 Y')
        
        Returns:
            Number of days
        """
        parts = duration.strip().split()
        if len(parts) != 2:
            return 0
        
        value = int(parts[0])
        unit = parts[1].upper()
        
        if unit == 'D':
            return value
        elif unit == 'W':
            return value * 7
        elif unit == 'M':
            return value * 30
        elif unit == 'Y':
            return value * 365
        else:
            return 0
    
    def get_historical_data_chunked(
        self,
        symbol: str,
        duration: str = '1 M',
        bar_size: str = '5 secs',
        what_to_show: str = 'TRADES',
        use_rth: bool = False,
        exchange: str = 'SMART',
        currency: str = 'EUR',
        progress_callback=None
    ) -> Optional[pd.DataFrame]:
        """
        Get historical data with automatic chunking based on IBKR limits
        
        Args:
            symbol: Stock symbol
            duration: Total duration requested (e.g., '1 M', '3 M')
            bar_size: Bar size (e.g., '5 secs', '1 min')
            what_to_show: Data type
            use_rth: Use regular trading hours only
            exchange: Exchange
            currency: Currency
            progress_callback: Optional callback(current_chunk, total_chunks)
        
        Returns:
            Combined DataFrame with all historical data
        """
        try:
            # Check if chunking is needed
            if bar_size not in self.IBKR_LIMITS:
                logger.warning(f"Unknown bar size: {bar_size}, using standard request")
                return self.get_historical_data(symbol, duration, bar_size, what_to_show, use_rth, exchange, currency)
            
            limit_info = self.IBKR_LIMITS[bar_size]
            requested_days = self._parse_duration_to_days(duration)
            max_chunk_days = limit_info['chunk_days']
            
            # If request is within limits, use standard method
            if requested_days <= max_chunk_days:
                logger.info(f"Request within IBKR limits ({requested_days} <= {max_chunk_days} days)")
                return self.get_historical_data(symbol, duration, bar_size, what_to_show, use_rth, exchange, currency)
            
            # Calculate chunks needed
            num_chunks = (requested_days + max_chunk_days - 1) // max_chunk_days
            logger.info(f"📊 Splitting request into {num_chunks} chunks ({requested_days} days / {max_chunk_days} days per chunk)")
            
            all_data = []
            end_date = datetime.now()
            
            for chunk_idx in range(num_chunks):
                # Update progress
                if progress_callback:
                    progress_callback(chunk_idx + 1, num_chunks)
                
                # Calculate chunk duration
                remaining_days = requested_days - (chunk_idx * max_chunk_days)
                chunk_days = min(max_chunk_days, remaining_days)
                
                # Format duration string
                if chunk_days < 7:
                    chunk_duration = f"{chunk_days} D"
                elif chunk_days < 30:
                    chunk_duration = f"{chunk_days // 7} W"
                else:
                    chunk_duration = f"{chunk_days // 30} M"
                
                logger.info(f"📦 Chunk {chunk_idx + 1}/{num_chunks}: {chunk_duration} ending at {end_date.strftime('%Y-%m-%d')}")
                
                # Request chunk
                if not self.connected:
                    if not self.connect():
                        logger.error("Failed to connect to IBKR")
                        break
                
                contract = self.get_contract(symbol, exchange, currency)
                if not contract:
                    logger.error(f"Failed to get contract for {symbol}")
                    break
                
                try:
                    bars = self.ib.reqHistoricalData(
                        contract,
                        endDateTime=end_date.strftime('%Y%m%d %H:%M:%S'),
                        durationStr=chunk_duration,
                        barSizeSetting=bar_size,
                        whatToShow=what_to_show,
                        useRTH=use_rth,
                        formatDate=1
                    )
                    
                    if bars:
                        df_chunk = util.df(bars)
                        if not df_chunk.empty:
                            logger.info(f"✅ Chunk {chunk_idx + 1}: {len(df_chunk)} bars")
                            all_data.append(df_chunk)
                            
                            # Update end_date for next chunk
                            if not df_chunk.empty:
                                end_date = pd.to_datetime(df_chunk['date'].min())
                        else:
                            logger.warning(f"Empty chunk {chunk_idx + 1}")
                    else:
                        logger.warning(f"No data for chunk {chunk_idx + 1}")
                    
                    # Respect IBKR pacing (avoid too many requests)
                    if chunk_idx < num_chunks - 1:
                        self.ib.sleep(1)  # 1 second between requests
                        
                except Exception as e:
                    logger.error(f"Error fetching chunk {chunk_idx + 1}: {e}")
                    continue
            
            # Combine all chunks
            if not all_data:
                logger.warning(f"No data collected for {symbol}")
                return None
            
            df_combined = pd.concat(all_data, ignore_index=True)
            
            # Remove duplicates
            df_combined = df_combined.drop_duplicates(subset=['date'], keep='first')
            df_combined = df_combined.sort_values('date')
            
            # Rename columns
            df_combined = df_combined.rename(columns={
                'date': 'timestamp',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            })
            
            # Ensure timestamp is datetime
            if not isinstance(df_combined['timestamp'].iloc[0], datetime):
                df_combined['timestamp'] = pd.to_datetime(df_combined['timestamp'])
            
            logger.info(f"✅ Total collected: {len(df_combined)} bars for {symbol}")
            
            return df_combined[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Error in chunked historical data collection: {e}")
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
        Uses automatic chunking for large requests based on IBKR limits
        
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
            # Get historical data with automatic chunking
            logger.info(f"Collecting data for {symbol}: {duration} @ {bar_size}")
            df = self.get_historical_data_chunked(
                symbol=symbol,
                duration=duration,
                bar_size=bar_size,
                progress_callback=progress_callback
            )
            
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
