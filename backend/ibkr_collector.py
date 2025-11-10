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
    
    # Known European stocks and their preferred exchange/currency
    EUROPEAN_STOCKS = {
        'TTE': {'exchange': 'SBF', 'currency': 'EUR', 'name': 'TotalEnergies'},
        'WLN': {'exchange': 'SBF', 'currency': 'EUR', 'name': 'Walnur'},  # XETRA but try SBF first
        'FP': {'exchange': 'SBF', 'currency': 'EUR', 'name': 'L\'Oreal'},
        'MC': {'exchange': 'SBF', 'currency': 'EUR', 'name': 'LVMH'},
        'OR': {'exchange': 'SBF', 'currency': 'EUR', 'name': 'L\'Oreal'},
        'AC': {'exchange': 'SBF', 'currency': 'EUR', 'name': 'AccorHotels'},
        'ALO': {'exchange': 'SBF', 'currency': 'EUR', 'name': 'Alstom'},
        'BNP': {'exchange': 'SBF', 'currency': 'EUR', 'name': 'BNP Paribas'},
        'LR': {'exchange': 'SBF', 'currency': 'EUR', 'name': 'Legrand'},
        'SAF': {'exchange': 'SBF', 'currency': 'EUR', 'name': 'Safran'},
    }
    
    # Interval hierarchy in seconds (for aggregation logic)
    INTERVAL_SECONDS = {
        '1 secs': 1,
        '5 secs': 5,
        '10 secs': 10,
        '15 secs': 15,
        '30 secs': 30,
        '1 min': 60,
        '2 mins': 120,
        '3 mins': 180,
        '5 mins': 300,
        '10 mins': 600,
        '15 mins': 900,
        '20 mins': 1200,
        '30 mins': 1800,
        '1 hour': 3600,
        '2 hours': 7200,
        '3 hours': 14400,
        '4 hours': 14400,
        '1 day': 86400,
        '1 week': 604800,
        '1 month': 2592000,
    }
    
    # IBKR Historical Data Limitations (max duration per bar size)
    # Source: https://interactivebrokers.github.io/tws-api/historical_limitations.html
    IBKR_LIMITS = {
        '1 secs': {'max_duration': '1 D', 'chunk_days': 1, 'recommended_max_days': 7},      # 1 day max, recommend max 1 week total
        '5 secs': {'max_duration': '2 D', 'chunk_days': 2, 'recommended_max_days': 14},     # 2 days max, recommend max 2 weeks total
        '10 secs': {'max_duration': '2 D', 'chunk_days': 2, 'recommended_max_days': 14},    # 2 days max
        '15 secs': {'max_duration': '2 D', 'chunk_days': 2, 'recommended_max_days': 14},    # 2 days max
        '30 secs': {'max_duration': '1 W', 'chunk_days': 7, 'recommended_max_days': 30},    # 1 week max
        '1 min': {'max_duration': '1 W', 'chunk_days': 7, 'recommended_max_days': 90},      # 1 week max, recommend max 3 months
        '2 mins': {'max_duration': '1 W', 'chunk_days': 7, 'recommended_max_days': 90},     # 1 week max
        '3 mins': {'max_duration': '1 W', 'chunk_days': 7, 'recommended_max_days': 90},     # 1 week max
        '5 mins': {'max_duration': '1 W', 'chunk_days': 7, 'recommended_max_days': 90},     # 1 week max
        '10 mins': {'max_duration': '1 W', 'chunk_days': 7, 'recommended_max_days': 90},    # 1 week max
        '15 mins': {'max_duration': '1 W', 'chunk_days': 7, 'recommended_max_days': 90},    # 1 week max
        '20 mins': {'max_duration': '1 W', 'chunk_days': 7, 'recommended_max_days': 90},    # 1 week max
        '30 mins': {'max_duration': '1 M', 'chunk_days': 30, 'recommended_max_days': 180},  # 1 month max
        '1 hour': {'max_duration': '1 M', 'chunk_days': 30, 'recommended_max_days': 365},   # 1 month max
        '2 hours': {'max_duration': '1 M', 'chunk_days': 30, 'recommended_max_days': 365},  # 1 month max
        '3 hours': {'max_duration': '1 M', 'chunk_days': 30, 'recommended_max_days': 365},  # 1 month max
        '4 hours': {'max_duration': '1 M', 'chunk_days': 30, 'recommended_max_days': 365},  # 1 month max
        '8 hours': {'max_duration': '1 M', 'chunk_days': 30, 'recommended_max_days': 365},  # 1 month max
        '1 day': {'max_duration': '1 Y', 'chunk_days': 365, 'recommended_max_days': 3650},  # 1 year max
        '1 week': {'max_duration': '1 Y', 'chunk_days': 365, 'recommended_max_days': 3650}, # 1 year max
        '1 month': {'max_duration': '1 Y', 'chunk_days': 365, 'recommended_max_days': 3650}, # 1 year max
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
        
        logger.info(f"IBKR Collector initialized - {self.host}:{self.port} with clientId={self.client_id}")
    
    def connect(self) -> bool:
        """Connect to IB Gateway/TWS"""
        try:
            if self.ib.isConnected():
                logger.info("Already connected to IBKR")
                return True
            
            logger.info(f"Connecting to IBKR at {self.host}:{self.port}...")
            # Increased timeout from 15s to 20s for Celery background tasks which are less prioritized
            self.ib.connect(self.host, self.port, clientId=self.client_id, timeout=20)
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
    
    def get_contract(self, symbol: str = None, exchange: str = 'SMART', currency: str = None, isin: str = None) -> Optional[Stock]:
        """
        Get and qualify a stock contract
        
        Tries to qualify with multiple exchanges and currencies to handle both US and European stocks.
        Supports both symbol and ISIN lookup - ISIN is faster for European stocks.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'TTE', 'WLN')
            exchange: Exchange (default: 'SMART' for automatic routing)
            currency: Currency (default: None to auto-detect - tries USD first, then EUR)
            isin: ISIN code (e.g., 'FR0000120271' for TTE) - faster for European stocks
        
        Returns:
            Qualified contract or None
        """
        try:
            import time
            from ib_insync import Contract
            
            # If ISIN provided, try that first (much faster for European stocks)
            # NOTE: Contract doesn't accept isin directly, so we skip this for now
            # and rely on symbol-based lookup with proper exchange ordering
            
            # Fallback to symbol-based lookup
            if not symbol:
                logger.error("Symbol must be provided")
                return None
            
            # Check if this is a known European stock
            european_stock = self.EUROPEAN_STOCKS.get(symbol.upper())
            if european_stock and exchange == 'SMART':
                # For known European stocks with SMART routing, prioritize EUR + European exchanges
                exchange = european_stock['exchange']
                currency = european_stock['currency']
                logger.info(f"Known European stock: {symbol} → preferring {exchange}/{currency}")
            
            # If currency not specified, try currencies based on exchange
            currencies_to_try = []
            if currency:
                currencies_to_try = [currency]
            else:
                # Determine currency order based on exchange
                if exchange in ['SBF', 'EURONEXT', 'XETRA', 'BME']:
                    # European exchanges - EUR first, then USD
                    currencies_to_try = ['EUR', 'USD']
                else:
                    # Default: USD first (US stocks on SMART/NASDAQ), then EUR
                    currencies_to_try = ['USD', 'EUR']
            
            # Determine exchanges to try
            exchanges_to_try = []
            if exchange == 'SMART':
                # For SMART routing, try exchanges in order:
                # - SBF first (Euronext - faster for EU stocks like TTE, WLN)
                # - SMART (auto-routing for US stocks)
                # - NASDAQ (explicit US if SMART fails)
                exchanges_to_try = ['SBF', 'SMART', 'NASDAQ']
            else:
                exchanges_to_try = [exchange]
            
            # Try combinations of exchange and currency
            for curr in currencies_to_try:
                for ex in exchanges_to_try:
                    try:
                        contract = Stock(symbol, ex, curr)
                        
                        # Call qualifyContracts directly (blocking - on main thread)
                        # This avoids threading issues with ib_insync's asyncio integration
                        # Retry up to 3 times with progressive backoff if it fails
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                contracts = self.ib.qualifyContracts(contract)
                                
                                if contracts:
                                    qualified = contracts[0]
                                    logger.info(f"Contract qualified: {qualified.symbol} on {qualified.primaryExchange} (exchange: {qualified.exchange}, currency: {qualified.currency})")
                                    return qualified
                                else:
                                    logger.debug(f"Exchange {ex}, currency {curr} - no contracts found for {symbol}")
                                break  # Exit retry loop if qualifyContracts succeeded (even if no contracts found)
                                
                            except Exception as e:
                                if attempt < max_retries - 1:
                                    wait_time = 0.5 * (2 ** attempt)  # 0.5s, 1s, 2s
                                    logger.debug(f"Exchange {ex}, currency {curr} - attempt {attempt + 1} failed for {symbol}, retrying in {wait_time}s: {e}")
                                    time.sleep(wait_time)
                                else:
                                    logger.debug(f"Exchange {ex}, currency {curr} - all {max_retries} attempts failed for {symbol}: {e}")
                                    break
                    except Exception as e:
                        logger.debug(f"Exception in get_contract for {ex}/{curr}/{symbol}: {e}")
                        continue
            
            logger.warning(f"Could not qualify contract for {symbol} on any exchange/currency combination")
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
        currency: str = None
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
            currency: Currency (None to auto-detect - tries USD first, then EUR)
        
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
        currency: str = None,
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
            recommended_max = limit_info.get('recommended_max_days', 365)
            
            # Info only (don't warn - streaming handles large requests well)
            if requested_days > recommended_max:
                logger.info(f"📊 Large request: {requested_days} days with {bar_size} bars → {(requested_days + max_chunk_days - 1) // max_chunk_days} chunks (streaming mode)")
            
            # If within limits, use standard method
            if requested_days <= max_chunk_days:
                logger.info(f"Request within IBKR limits ({requested_days} <= {max_chunk_days} days)")
                return self.get_historical_data(symbol, duration, bar_size, what_to_show, use_rth, exchange, currency)
            
            # Calculate chunks needed
            num_chunks = (requested_days + max_chunk_days - 1) // max_chunk_days
            
            # Estimate time (approx 2-3 seconds per chunk with IBKR pacing)
            estimated_minutes = (num_chunks * 2.5) / 60
            
            if estimated_minutes < 1:
                time_estimate = f"{int(num_chunks * 2.5)} secondes"
            elif estimated_minutes < 60:
                time_estimate = f"{int(estimated_minutes)} minutes"
            else:
                time_estimate = f"{estimated_minutes/60:.1f} heures"
            
            logger.info(f"📊 Splitting request into {num_chunks} chunks ({requested_days} days / {max_chunk_days} days per chunk)")
            logger.info(f"⏱️ Estimated collection time: ~{time_estimate}")
            
            # Warn for very large requests (but don't block)
            if num_chunks > 100:
                logger.warning(f"⚠️ Very large request: {num_chunks} chunks (~{time_estimate}). Data will be collected and saved progressively.")
            
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
                    # Format date for IBKR with timezone to avoid Warning 2174
                    # Use Europe/Paris timezone for European stocks
                    end_datetime = end_date.strftime('%Y%m%d %H:%M:%S') + ' Europe/Paris'
                    
                    bars = self.ib.reqHistoricalData(
                        contract,
                        endDateTime=end_datetime,
                        durationStr=chunk_duration,
                        barSizeSetting=bar_size,
                        whatToShow=what_to_show,
                        useRTH=use_rth,
                        formatDate=1,
                        timeout=120  # Increase timeout to 120 seconds for large requests
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
    
    def get_data_coverage(self, symbol: str, interval: str, start_date: datetime, end_date: datetime) -> Dict:
        """
        Get data coverage for a symbol/interval in the specified date range
        
        Args:
            symbol: Stock symbol
            interval: Interval string (e.g., '1min', '5secs')
            start_date: Start of requested range
            end_date: End of requested range
            
        Returns:
            Dict with coverage info: {
                'has_data': bool,
                'first_date': datetime or None,
                'last_date': datetime or None,
                'total_records': int,
                'missing_ranges': [{'start': datetime, 'end': datetime}, ...],
                'is_complete': bool
            }
        """
        db = SessionLocal()
        try:
            from sqlalchemy import func
            
            # Get ticker
            ticker = db.query(TickerModel).filter(TickerModel.symbol == symbol).first()
            if not ticker:
                return {
                    'has_data': False,
                    'first_date': None,
                    'last_date': None,
                    'total_records': 0,
                    'missing_ranges': [{'start': start_date, 'end': end_date}],
                    'is_complete': False
                }
            
            # Get date range and count
            result = db.query(
                func.min(HistoricalData.timestamp).label('first'),
                func.max(HistoricalData.timestamp).label('last'),
                func.count(HistoricalData.id).label('count')
            ).filter(
                and_(
                    HistoricalData.ticker_id == ticker.id,
                    HistoricalData.interval == interval,
                    HistoricalData.timestamp >= start_date,
                    HistoricalData.timestamp <= end_date
                )
            ).first()
            
            if not result.count or result.count == 0:
                return {
                    'has_data': False,
                    'first_date': None,
                    'last_date': None,
                    'total_records': 0,
                    'missing_ranges': [{'start': start_date, 'end': end_date}],
                    'is_complete': False
                }
            
            first_date = result.first
            last_date = result.last
            total_records = result.count
            
            # Calculate missing ranges
            missing_ranges = []
            
            # Missing at the beginning?
            if first_date > start_date:
                missing_ranges.append({
                    'start': start_date,
                    'end': first_date - timedelta(days=1)
                })
            
            # Missing at the end?
            if last_date < end_date:
                missing_ranges.append({
                    'start': last_date + timedelta(days=1),
                    'end': end_date
                })
            
            # Check for gaps in the middle (simplified - could be enhanced)
            # For now, we assume continuous data between first and last
            
            is_complete = len(missing_ranges) == 0
            
            return {
                'has_data': True,
                'first_date': first_date,
                'last_date': last_date,
                'total_records': total_records,
                'missing_ranges': missing_ranges,
                'is_complete': is_complete
            }
            
        except Exception as e:
            logger.error(f"Error getting data coverage: {e}", exc_info=True)
            return {
                'has_data': False,
                'first_date': None,
                'last_date': None,
                'total_records': 0,
                'missing_ranges': [{'start': start_date, 'end': end_date}],
                'is_complete': False
            }
        finally:
            db.close()
    
    def find_aggregable_interval(self, symbol: str, target_interval: str, start_date: datetime, end_date: datetime) -> Optional[str]:
        """
        Find a smaller interval that can be aggregated to the target interval
        
        Args:
            symbol: Stock symbol
            target_interval: Desired interval (e.g., '1 min')
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            Source interval string if found, None otherwise
        """
        if target_interval not in self.INTERVAL_SECONDS:
            return None
        
        target_seconds = self.INTERVAL_SECONDS[target_interval]
        
        # Find all smaller intervals that divide evenly into target
        aggregable_intervals = []
        for interval, seconds in self.INTERVAL_SECONDS.items():
            if seconds < target_seconds and target_seconds % seconds == 0:
                # Check if we have data for this interval
                coverage = self.get_data_coverage(symbol, interval, start_date, end_date)
                if coverage['has_data'] and coverage['total_records'] > 0:
                    aggregable_intervals.append((interval, seconds, coverage))
        
        if not aggregable_intervals:
            return None
        
        # Return the largest (closest to target) interval with best coverage
        # Sort by seconds descending (largest first)
        aggregable_intervals.sort(key=lambda x: x[1], reverse=True)
        
        # Prefer intervals with complete coverage
        for interval, seconds, coverage in aggregable_intervals:
            if coverage['is_complete']:
                logger.info(f"✅ Can aggregate {interval} → {target_interval} (complete coverage)")
                return interval
        
        # If no complete coverage, return the one with most data
        best = aggregable_intervals[0]
        logger.info(f"⚠️ Can partially aggregate {best[0]} → {target_interval} ({best[2]['total_records']} records)")
        return best[0]
    
    def aggregate_interval_data(self, symbol: str, source_interval: str, target_interval: str, 
                               start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """
        Aggregate OHLCV data from smaller to larger interval
        
        Args:
            symbol: Stock symbol
            source_interval: Source interval (e.g., '5 secs')
            target_interval: Target interval (e.g., '1 min')
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with aggregated data, or None if error
        """
        db = SessionLocal()
        try:
            from sqlalchemy import func
            
            # Get ticker
            ticker = db.query(TickerModel).filter(TickerModel.symbol == symbol).first()
            if not ticker:
                return None
            
            # Fetch source data
            source_data = db.query(HistoricalData).filter(
                and_(
                    HistoricalData.ticker_id == ticker.id,
                    HistoricalData.interval == source_interval,
                    HistoricalData.timestamp >= start_date,
                    HistoricalData.timestamp <= end_date
                )
            ).order_by(HistoricalData.timestamp).all()
            
            if not source_data:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'timestamp': row.timestamp,
                'open': row.open,
                'high': row.high,
                'low': row.low,
                'close': row.close,
                'volume': row.volume
            } for row in source_data])
            
            # Calculate aggregation factor
            source_seconds = self.INTERVAL_SECONDS[source_interval]
            target_seconds = self.INTERVAL_SECONDS[target_interval]
            factor = target_seconds // source_seconds
            
            logger.info(f"Aggregating {source_interval} → {target_interval} (factor: {factor}x, {len(df)} rows)")
            
            # Set timestamp as index for resampling
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Resample using pandas
            # Determine pandas frequency string
            freq_map = {
                60: '1min',      # 1 min
                300: '5min',     # 5 mins
                600: '10min',    # 10 mins
                900: '15min',    # 15 mins
                1800: '30min',   # 30 mins
                3600: '1H',      # 1 hour
                7200: '2H',      # 2 hours
                14400: '4H',     # 4 hours
                86400: '1D',     # 1 day
                604800: '1W',    # 1 week
            }
            
            freq = freq_map.get(target_seconds)
            if not freq:
                logger.error(f"Unsupported target interval for aggregation: {target_interval}")
                return None
            
            # Aggregate OHLCV
            aggregated = df.resample(freq).agg({
                'open': 'first',    # First open of the period
                'high': 'max',      # Highest high
                'low': 'min',       # Lowest low
                'close': 'last',    # Last close
                'volume': 'sum'     # Sum of volumes
            }).dropna()
            
            # Reset index to get timestamp column back
            aggregated.reset_index(inplace=True)
            
            logger.info(f"✅ Aggregation complete: {len(aggregated)} {target_interval} bars from {len(df)} {source_interval} bars")
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating interval data: {e}", exc_info=True)
            return None
        finally:
            db.close()
    
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
            logger.info(f"📊 Starting database save for {symbol}: {len(df)} rows, columns: {list(df.columns)}")

            # Validate DataFrame
            if df.empty:
                return {
                    'success': False,
                    'error': 'DataFrame is empty'
                }

            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return {
                    'success': False,
                    'error': f'Missing required columns: {missing_columns}'
                }

            # Check for NaN values
            nan_counts = df.isnull().sum()
            if nan_counts.sum() > 0:
                logger.warning(f"NaN values found: {nan_counts.to_dict()}")

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
            skipped_records = 0  # Track records that are identical (no update needed)
            total_rows = len(df)
            errors = []

            for idx, (_, row) in enumerate(df.iterrows()):
                try:
                    # Update progress
                    if progress_callback:
                        progress_callback(idx + 1, total_rows)

                    # Validate row data
                    try:
                        timestamp = pd.to_datetime(row['timestamp'])
                        open_price = float(row['open'])
                        high_price = float(row['high'])
                        low_price = float(row['low'])
                        close_price = float(row['close'])
                        volume_val = int(row['volume'])
                    except (ValueError, TypeError) as e:
                        errors.append(f"Row {idx}: Invalid data types - {e}")
                        continue

                    # Check if record exists
                    existing = db.query(HistoricalData).filter(
                        and_(
                            HistoricalData.ticker_id == ticker.id,
                            HistoricalData.timestamp == timestamp,
                            HistoricalData.interval == interval
                        )
                    ).first()

                    if existing:
                        # Check if data has changed before updating
                        if (existing.open == open_price and
                            existing.high == high_price and
                            existing.low == low_price and
                            existing.close == close_price and
                            existing.volume == volume_val):
                            # Data identical - skip update
                            skipped_records += 1
                        else:
                            # Data changed - update record
                            existing.open = open_price
                            existing.high = high_price
                            existing.low = low_price
                            existing.close = close_price
                            existing.volume = volume_val
                            updated_records += 1
                    else:
                        # Create new record
                        new_record = HistoricalData(
                            ticker_id=ticker.id,
                            timestamp=timestamp,
                            open=open_price,
                            high=high_price,
                            low=low_price,
                            close=close_price,
                            volume=volume_val,
                            interval=interval
                        )
                        db.add(new_record)
                        new_records += 1

                    # Commit every 1000 records to avoid memory issues
                    if (new_records + updated_records + skipped_records) % 1000 == 0:
                        db.commit()
                        logger.info(f"Committed {new_records + updated_records}/{total_rows} records ({skipped_records} skipped)")

                except Exception as e:
                    error_msg = f"Row {idx}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

            # Final commit
            db.commit()

            result = {
                'success': True,
                'symbol': symbol,
                'new_records': new_records,
                'updated_records': updated_records,
                'skipped_records': skipped_records,
                'total_records': len(df),
                'interval': interval,
                'date_range': f"{df['timestamp'].min()} to {df['timestamp'].max()}"
            }

            if errors:
                result['warnings'] = errors[:10]  # Log first 10 errors
                logger.warning(f"Completed with {len(errors)} errors: {errors[:3]}")

            logger.info(f"✅ Saved to database: {new_records} new, {updated_records} updated, {skipped_records} skipped (identical)")

            return result

        except Exception as e:
            db.rollback()
            logger.error(f"Error saving to database: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
        
        finally:
            db.close()
    
    def _collect_gap_from_ibkr(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        duration_str: str,
        bar_size: str,
        interval: str,
        name: str = None,
        progress_callback=None
    ) -> Dict:
        """
        Helper to collect data from IBKR for a specific date gap using chunking logic
        
        Args:
            symbol: Stock symbol
            start_date: Gap start date
            end_date: Gap end date
            duration_str: Duration string for the gap
            bar_size: IBKR bar size
            interval: DB interval
            name: Stock name
            progress_callback: Progress callback
            
        Returns:
            Dict with collection results
        """
        try:
            gap_days = (end_date - start_date).days + 1
            
            if bar_size not in self.IBKR_LIMITS:
                # Fallback for unknown bar size
                df = self.get_historical_data(symbol, duration_str, bar_size)
                if df is None or df.empty:
                    return {'success': False, 'error': 'No data received'}
                return self.save_to_database(symbol, df, interval, name, progress_callback)
            
            limit_info = self.IBKR_LIMITS[bar_size]
            max_chunk_days = limit_info['chunk_days']
            
            # If within limits, single request
            if gap_days <= max_chunk_days:
                logger.info(f"Gap within IBKR limits ({gap_days} <= {max_chunk_days} days), single request")
                df = self.get_historical_data(symbol, duration_str, bar_size)
                if df is None or df.empty:
                    return {'success': False, 'error': 'No data received'}
                return self.save_to_database(symbol, df, interval, name, progress_callback)
            
            # Need chunking
            num_chunks = (gap_days + max_chunk_days - 1) // max_chunk_days
            logger.info(f"Chunking gap into {num_chunks} requests")
            
            total_new = 0
            total_updated = 0
            total_records = 0
            errors = []
            
            chunk_end_date = end_date
            
            # Process each chunk
            for chunk_idx in range(num_chunks):
                # Update progress callback
                if progress_callback:
                    progress_callback(chunk_idx + 1, num_chunks)
                
                try:
                    remaining_days = gap_days - (chunk_idx * max_chunk_days)
                    chunk_days = min(max_chunk_days, remaining_days)
                    
                    if chunk_days < 7:
                        chunk_duration = f"{chunk_days} D"
                    elif chunk_days < 30:
                        chunk_duration = f"{chunk_days // 7} W"
                    else:
                        chunk_duration = f"{chunk_days // 30} M"
                    
                    logger.info(f"  📦 Chunk {chunk_idx + 1}/{num_chunks}: {chunk_duration} ending {chunk_end_date.strftime('%Y-%m-%d')}")
                    
                    # Ensure connection
                    if not self.connected:
                        if not self.connect():
                            errors.append(f"Chunk {chunk_idx + 1}: Failed to connect")
                            continue
                    
                    contract = self.get_contract(symbol)
                    if not contract:
                        errors.append(f"Chunk {chunk_idx + 1}: Failed to get contract")
                        continue
                    
                    # Request data with timezone to avoid Warning 2174
                    end_datetime = chunk_end_date.strftime('%Y%m%d %H:%M:%S') + ' Europe/Paris'
                    
                    bars = self.ib.reqHistoricalData(
                        contract,
                        endDateTime=end_datetime,
                        durationStr=chunk_duration,
                        barSizeSetting=bar_size,
                        whatToShow='TRADES',
                        useRTH=False,
                        formatDate=1,
                        timeout=120
                    )
                    
                    if not bars:
                        logger.warning(f"No data for chunk {chunk_idx + 1}")
                        self.ib.sleep(1)
                        continue
                    
                    # Convert to DataFrame
                    df_chunk = util.df(bars)
                    if df_chunk.empty:
                        logger.warning(f"Empty chunk {chunk_idx + 1}")
                        self.ib.sleep(1)
                        continue
                    
                    df_chunk = df_chunk.rename(columns={'date': 'timestamp'})
                    if not isinstance(df_chunk['timestamp'].iloc[0], datetime):
                        df_chunk['timestamp'] = pd.to_datetime(df_chunk['timestamp'])
                    
                    df_chunk = df_chunk[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                    
                    logger.info(f"  ✅ Chunk {chunk_idx + 1}: {len(df_chunk)} bars collected")
                    
                    # Save chunk
                    save_result = self.save_to_database(symbol, df_chunk, interval, name, None)
                    
                    if save_result['success']:
                        total_new += save_result['new_records']
                        total_updated += save_result['updated_records']
                        total_records += save_result['total_records']
                        logger.info(f"  💾 Chunk {chunk_idx + 1} saved: +{save_result['new_records']} new, +{save_result['updated_records']} updated")
                    else:
                        errors.append(f"Chunk {chunk_idx + 1}: {save_result.get('error')}")
                    
                    # Update for next chunk
                    if not df_chunk.empty:
                        chunk_end_date = pd.to_datetime(df_chunk['timestamp'].min())
                    
                    # Pace requests
                    if chunk_idx < num_chunks - 1:
                        self.ib.sleep(1)
                
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_idx + 1}: {e}")
                    errors.append(f"Chunk {chunk_idx + 1}: {e}")
                    continue
            
            result = {
                'success': total_records > 0,
                'symbol': symbol,
                'new_records': total_new,
                'updated_records': total_updated,
                'total_records': total_records,
                'interval': interval
            }
            
            if errors:
                result['warnings'] = errors[:10]
            
            return result
            
        except Exception as e:
            logger.error(f"Error collecting gap from IBKR: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def collect_and_save_streaming(
        self,
        symbol: str,
        duration: str = '1 M',
        bar_size: str = '1 min',
        interval: str = '1min',
        name: str = None,
        progress_callback=None
    ) -> Dict[str, any]:
        """
        Collect historical data and save to database chunk by chunk (streaming mode)
        More memory efficient for large requests - saves each chunk immediately
        
        OPTIMIZED: Checks for existing data, aggregates from smaller intervals when possible,
        and only queries IBKR for missing gaps.
        
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
            logger.info(f"🔍 Smart collection for {symbol}: {duration} @ {bar_size} (streaming mode)")
            
            # Calculate date range
            requested_days = self._parse_duration_to_days(duration)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=requested_days)
            
            logger.info(f"📅 Requested range: {start_date.date()} → {end_date.date()} ({requested_days} days)")
            
            # STEP 1: Check if data already exists for this exact interval
            coverage = self.get_data_coverage(symbol, interval, start_date, end_date)
            
            if coverage['is_complete']:
                logger.info(f"✅ Data already complete in database ({coverage['total_records']} records)")
                return {
                    'success': True,
                    'symbol': symbol,
                    'new_records': 0,
                    'updated_records': 0,
                    'total_records': coverage['total_records'],
                    'interval': interval,
                    'message': 'Data already exists, no collection needed',
                    'date_range': f"{coverage['first_date']} to {coverage['last_date']}"
                }
            
            # STEP 2: Try to aggregate from smaller interval if target doesn't exist or incomplete
            if not coverage['has_data'] or len(coverage['missing_ranges']) > 0:
                source_interval = self.find_aggregable_interval(symbol, interval, start_date, end_date)
                
                if source_interval:
                    logger.info(f"📊 Aggregating from {source_interval} → {interval}")
                    aggregated_df = self.aggregate_interval_data(symbol, source_interval, interval, start_date, end_date)
                    
                    if aggregated_df is not None and not aggregated_df.empty:
                        # Save aggregated data
                        result = self.save_to_database(symbol, aggregated_df, interval, name, progress_callback)
                        
                        # Re-check coverage after aggregation
                        new_coverage = self.get_data_coverage(symbol, interval, start_date, end_date)
                        
                        if new_coverage['is_complete']:
                            logger.info(f"✅ Complete coverage achieved through aggregation!")
                            return result
                        else:
                            logger.info(f"⚠️ Partial coverage from aggregation, will fill remaining gaps from IBKR")
                            coverage = new_coverage  # Update coverage for gap filling
            
            # STEP 3: Identify missing ranges that need IBKR queries
            if coverage['missing_ranges']:
                logger.info(f"📊 Filling {len(coverage['missing_ranges'])} gap(s) from IBKR")
                
                total_new = 0
                total_updated = 0
                total_records = 0
                
                for gap_idx, gap in enumerate(coverage['missing_ranges']):
                    gap_start = gap['start']
                    gap_end = gap['end']
                    gap_days = (gap_end - gap_start).days + 1
                    
                    logger.info(f"📦 Gap {gap_idx + 1}/{len(coverage['missing_ranges'])}: {gap_start.date()} → {gap_end.date()} ({gap_days} days)")
                    
                    # Convert gap to duration string for IBKR
                    if gap_days < 7:
                        gap_duration = f"{gap_days} D"
                    elif gap_days < 30:
                        gap_duration = f"{gap_days // 7} W"
                    else:
                        gap_duration = f"{gap_days // 30} M"
                    
                    # Query IBKR for this gap using standard chunking logic
                    # (Keep existing chunking logic but applied to the gap only)
                    gap_result = self._collect_gap_from_ibkr(
                        symbol, gap_start, gap_end, gap_duration, bar_size, interval, name, progress_callback
                    )
                    
                    if gap_result and gap_result.get('success'):
                        total_new += gap_result.get('new_records', 0)
                        total_updated += gap_result.get('updated_records', 0)
                        total_records += gap_result.get('total_records', 0)
                
                return {
                    'success': True,
                    'symbol': symbol,
                    'new_records': total_new,
                    'updated_records': total_updated,
                    'total_records': total_records,
                    'interval': interval,
                    'message': f'Filled {len(coverage["missing_ranges"])} gap(s) from IBKR',
                    'date_range': f"{start_date} to {end_date}"
                }
            
            # If we get here, something unexpected happened
            logger.warning("No gaps found but coverage not complete - falling through to standard collection")
            
            # FALLBACK: Use original logic for compatibility
            logger.info(f"Collecting data for {symbol}: {duration} @ {bar_size} (streaming mode)")
            
            # Check chunking requirements
            if bar_size not in self.IBKR_LIMITS:
                logger.warning(f"Unknown bar size: {bar_size}, using standard method")
                # Fall back to standard method
                df = self.get_historical_data(symbol, duration, bar_size)
                if df is None or df.empty:
                    return {'success': False, 'error': 'No data received'}
                return self.save_to_database(symbol, df, interval, name, progress_callback)
            
            limit_info = self.IBKR_LIMITS[bar_size]
            max_chunk_days = limit_info['chunk_days']
            recommended_max = limit_info.get('recommended_max_days', 365)
            
            # Warn if excessive
            if requested_days > recommended_max:
                logger.warning(f"⚠️ Requested {requested_days} days exceeds recommended {recommended_max} days for {bar_size}")
            
            # If within limits, use standard method
            if requested_days <= max_chunk_days:
                logger.info(f"Request within IBKR limits ({requested_days} <= {max_chunk_days} days)")
                df = self.get_historical_data(symbol, duration, bar_size)
                if df is None or df.empty:
                    return {'success': False, 'error': 'No data received'}
                return self.save_to_database(symbol, df, interval, name, progress_callback)
            
            # Calculate chunks
            num_chunks = (requested_days + max_chunk_days - 1) // max_chunk_days
            
            # Estimate time (approx 2-3 seconds per chunk with IBKR pacing)
            estimated_minutes = (num_chunks * 2.5) / 60
            
            if estimated_minutes < 1:
                time_estimate = f"{int(num_chunks * 2.5)} secondes"
            elif estimated_minutes < 60:
                time_estimate = f"{int(estimated_minutes)} minutes"
            else:
                time_estimate = f"{estimated_minutes/60:.1f} heures"
            
            logger.info(f"📊 Processing {num_chunks} chunks - saving each immediately to database")
            logger.info(f"⏱️ Estimated time: ~{time_estimate}")
            
            # Warn if very large request (but don't block it)
            if num_chunks > 100:
                logger.warning(f"⚠️ Large request: {num_chunks} chunks (~{time_estimate}) will be processed. This may take a while but will save progressively.")
            
            # Initialize counters
            total_new = 0
            total_updated = 0
            total_records = 0
            errors = []
            
            end_date = datetime.now()
            
            # Process each chunk and save immediately
            for chunk_idx in range(num_chunks):
                try:
                    # Calculate chunk duration
                    remaining_days = requested_days - (chunk_idx * max_chunk_days)
                    chunk_days = min(max_chunk_days, remaining_days)
                    
                    if chunk_days < 7:
                        chunk_duration = f"{chunk_days} D"
                    elif chunk_days < 30:
                        chunk_duration = f"{chunk_days // 7} W"
                    else:
                        chunk_duration = f"{chunk_days // 30} M"
                    
                    logger.info(f"📦 Chunk {chunk_idx + 1}/{num_chunks}: {chunk_duration} ending {end_date.strftime('%Y-%m-%d')}")
                    
                    # Get chunk data
                    if not self.connected:
                        if not self.connect():
                            errors.append(f"Chunk {chunk_idx + 1}: Failed to connect")
                            continue
                    
                    contract = self.get_contract(symbol)
                    if not contract:
                        errors.append(f"Chunk {chunk_idx + 1}: Failed to get contract")
                        continue
                    
                    # Request historical data for this chunk with timezone to avoid Warning 2174
                    end_datetime = end_date.strftime('%Y%m%d %H:%M:%S') + ' Europe/Paris'
                    
                    bars = self.ib.reqHistoricalData(
                        contract,
                        endDateTime=end_datetime,
                        durationStr=chunk_duration,
                        barSizeSetting=bar_size,
                        whatToShow='TRADES',
                        useRTH=False,
                        formatDate=1,
                        timeout=120
                    )
                    
                    if not bars:
                        logger.warning(f"No data for chunk {chunk_idx + 1}")
                        self.ib.sleep(1)
                        continue
                    
                    # Convert to DataFrame
                    df_chunk = util.df(bars)
                    if df_chunk.empty:
                        logger.warning(f"Empty chunk {chunk_idx + 1}")
                        self.ib.sleep(1)
                        continue
                    
                    # Rename columns
                    df_chunk = df_chunk.rename(columns={'date': 'timestamp'})
                    if not isinstance(df_chunk['timestamp'].iloc[0], datetime):
                        df_chunk['timestamp'] = pd.to_datetime(df_chunk['timestamp'])
                    
                    df_chunk = df_chunk[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                    
                    logger.info(f"✅ Chunk {chunk_idx + 1}: {len(df_chunk)} bars collected")
                    
                    # Save chunk immediately to database
                    save_result = self.save_to_database(symbol, df_chunk, interval, name, None)
                    
                    if save_result['success']:
                        total_new += save_result['new_records']
                        total_updated += save_result['updated_records']
                        total_records += save_result['total_records']
                        logger.info(f"💾 Chunk {chunk_idx + 1} saved: +{save_result['new_records']} new, +{save_result['updated_records']} updated")
                    else:
                        errors.append(f"Chunk {chunk_idx + 1}: {save_result.get('error')}")
                    
                    # Update progress
                    if progress_callback:
                        progress_callback(chunk_idx + 1, num_chunks)
                    
                    # Update end_date for next chunk
                    if not df_chunk.empty:
                        end_date = pd.to_datetime(df_chunk['timestamp'].min())
                    
                    # Pace requests
                    if chunk_idx < num_chunks - 1:
                        self.ib.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_idx + 1}: {e}")
                    errors.append(f"Chunk {chunk_idx + 1}: {e}")
                    continue
            
            # Final result
            result = {
                'success': total_records > 0,
                'symbol': symbol,
                'new_records': total_new,
                'updated_records': total_updated,
                'total_records': total_records,
                'interval': interval,
                'chunks_processed': num_chunks
            }
            
            if errors:
                result['warnings'] = errors[:10]
                logger.warning(f"Completed with {len(errors)} chunk errors")
            
            logger.info(f"✅ Streaming save completed: {total_new} new, {total_updated} updated, {total_records} total")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in streaming collect_and_save: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
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
