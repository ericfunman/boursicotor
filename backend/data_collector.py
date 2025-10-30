"""
Data collection service for fetching and storing market data
"""
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd
from sqlalchemy.orm import Session

from backend.models import Ticker, HistoricalData, SessionLocal
from backend.config import logger, DATA_CONFIG, ALPHA_VANTAGE_API_KEY, POLYGON_API_KEY

# IBKR client is optional - will use mock data if not available
IBKR_AVAILABLE = False
ibkr_client = None

# Saxo Bank client
SAXO_AVAILABLE = False
try:
    from brokers.saxo_client import SaxoClient
    SAXO_AVAILABLE = True
    logger.info("✅ Saxo Bank client available")
except Exception as e:
    logger.warning(f"⚠️ Saxo Bank not available: {e}")

# Yahoo Finance client
YAHOO_AVAILABLE = False
try:
    import yfinance as yf
    YAHOO_AVAILABLE = True
    logger.info("✅ Yahoo Finance client available")
except Exception as e:
    logger.warning(f"⚠️ Yahoo Finance not available: {e}")

# Alpha Vantage client
ALPHA_VANTAGE_AVAILABLE = False
try:
    from alpha_vantage.timeseries import TimeSeries
    ALPHA_VANTAGE_AVAILABLE = True
    logger.info("✅ Alpha Vantage client available")
except Exception as e:
    logger.warning(f"⚠️ Alpha Vantage not available: {e}")

# Polygon.io client
POLYGON_AVAILABLE = False
try:
    from polygon import RESTClient
    POLYGON_AVAILABLE = True
    logger.info("✅ Polygon.io client available")
except Exception as e:
    logger.warning(f"⚠️ Polygon.io not available: {e}")


class DataCollector:
    """Service for collecting and storing market data"""
    
    def __init__(self, use_saxo: bool = True):
        self.db: Session = SessionLocal()
        self.saxo_client = None
        self.alpha_vantage_client = None
        self.polygon_client = None
        
        # Initialize Saxo client if available and requested
        if use_saxo and SAXO_AVAILABLE:
            self.saxo_client = SaxoClient()
            if self.saxo_client.ensure_authenticated():
                logger.info("✅ Saxo Bank client initialized and authenticated")
            else:
                logger.warning("⚠️ Saxo Bank authentication failed")
                self.saxo_client = None
        
        # Initialize Alpha Vantage client if API key is available
        if ALPHA_VANTAGE_AVAILABLE and ALPHA_VANTAGE_API_KEY:
            try:
                self.alpha_vantage_client = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
                logger.info("✅ Alpha Vantage client initialized")
            except Exception as e:
                logger.warning(f"⚠️ Alpha Vantage initialization failed: {e}")
                self.alpha_vantage_client = None
        elif ALPHA_VANTAGE_AVAILABLE:
            logger.warning("⚠️ Alpha Vantage available but no API key provided")
        
        # Initialize Polygon.io client if API key is available
        if POLYGON_AVAILABLE and POLYGON_API_KEY:
            try:
                self.polygon_client = RESTClient(api_key=POLYGON_API_KEY)
                logger.info("✅ Polygon.io client initialized")
            except Exception as e:
                logger.warning(f"⚠️ Polygon.io initialization failed: {e}")
                self.polygon_client = None
        elif POLYGON_AVAILABLE:
            logger.warning("⚠️ Polygon.io available but no API key provided")
        
    def __del__(self):
        self.db.close()
    
    def ensure_ticker_exists(self, symbol: str, name: str = "", exchange: str = "EURONEXT") -> Ticker:
        """Ensure ticker exists in database"""
        ticker = self.db.query(Ticker).filter(Ticker.symbol == symbol).first()
        
        if not ticker:
            ticker = Ticker(
                symbol=symbol,
                name=name or symbol,
                exchange=exchange,
                currency="EUR"
            )
            self.db.add(ticker)
            self.db.commit()
            self.db.refresh(ticker)
            logger.info(f"Created ticker: {symbol}")
        
        return ticker
    
    def collect_historical_data(
        self,
        symbol: str,
        name: str = "",
        duration: str = "1D",
        bar_size: str = "1min",
        exchange: str = "EURONEXT"
    ) -> int:
        """
        Collect historical data and store in database
        
        Args:
            symbol: Stock symbol
            name: Stock name
            duration: Duration string (e.g., '1D', '5D', '1M')
            bar_size: Bar size (e.g., '1min', '5min', '1hour')
            exchange: Exchange code
            
        Returns:
            Number of records inserted
        """
        try:
            # Ensure ticker exists
            ticker = self.ensure_ticker_exists(symbol, name, exchange)
            
            # Try Saxo Bank first if available
            if self.saxo_client:
                logger.info(f"📊 Fetching data from Saxo Bank for {symbol}")
                df = self.saxo_client.get_historical_data(
                    symbol=symbol,
                    duration=duration,
                    bar_size=bar_size,
                    exchange=exchange
                )
                
                if df is not None and len(df) > 0:
                    return self._store_dataframe(df, ticker, bar_size)
                else:
                    logger.warning(f"⚠️ No data from Saxo Bank for {symbol}")
            
            # Fallback to IBKR if available
            if IBKR_AVAILABLE and ibkr_client is not None:
                if not ibkr_client.connected:
                    ibkr_client.connect()
                
                logger.info(f"Fetching historical data from IBKR for {symbol}: {duration}, {bar_size}")
                bars = ibkr_client.get_historical_data(
                    symbol=symbol,
                    duration=duration,
                    bar_size=bar_size,
                    exchange=exchange
                )
                
                if bars:
                    return self._store_bars(bars, ticker, bar_size)
            
            # Fallback to Yahoo Finance if available
            if YAHOO_AVAILABLE:
                logger.info(f"📊 Fetching data from Yahoo Finance for {symbol}")
                df = self._get_yahoo_data(symbol, duration, bar_size)
                if df is not None and len(df) > 0:
                    return self._store_dataframe(df, ticker, bar_size)
                else:
                    logger.warning(f"⚠️ No data from Yahoo Finance for {symbol}")
            
            # Fallback to Alpha Vantage if available
            if self.alpha_vantage_client:
                logger.info(f"📊 Fetching data from Alpha Vantage for {symbol}")
                df = self._get_alpha_vantage_data(symbol, duration, bar_size)
                if df is not None and len(df) > 0:
                    return self._store_dataframe(df, ticker, bar_size)
                else:
                    logger.warning(f"⚠️ No data from Alpha Vantage for {symbol}")
            
            # Fallback to Polygon.io if available
            if self.polygon_client:
                logger.info(f"📊 Fetching data from Polygon.io for {symbol}")
                df = self._get_polygon_data(symbol, duration, bar_size)
                if df is not None and len(df) > 0:
                    return self._store_dataframe(df, ticker, bar_size)
                else:
                    logger.warning(f"⚠️ No data from Polygon.io for {symbol}")
            
            # Last resort: generate mock data
            logger.warning(f"⚠️ No data source available, generating mock data for {symbol}")
            return self._generate_mock_data(symbol, duration, bar_size, ticker)
            
        except Exception as e:
            logger.error(f"❌ Error collecting historical data for {symbol}: {e}")
            self.db.rollback()
            return 0
    
    def _store_dataframe(self, df: pd.DataFrame, ticker: Ticker, bar_size: str) -> int:
        """
        Store DataFrame in database
        
        Args:
            df: DataFrame with OHLCV data (indexed by timestamp)
            ticker: Ticker object
            bar_size: Bar size interval
        
        Returns:
            Number of records inserted
        """
        try:
            inserted = 0
            
            for timestamp, row in df.iterrows():
                # Check if record already exists
                exists = self.db.query(HistoricalData).filter(
                    HistoricalData.ticker_id == ticker.id,
                    HistoricalData.timestamp == timestamp,
                    HistoricalData.interval == bar_size
                ).first()
                
                if not exists:
                    record = HistoricalData(
                        ticker_id=ticker.id,
                        timestamp=timestamp,
                        open=float(row['open']),
                        high=float(row['high']),
                        low=float(row['low']),
                        close=float(row['close']),
                        volume=int(row['volume']),
                        interval=bar_size
                    )
                    self.db.add(record)
                    inserted += 1
            
            self.db.commit()
            logger.info(f"✅ Inserted {inserted} new records for {ticker.symbol}")
            return inserted
            
        except Exception as e:
            logger.error(f"❌ Error storing dataframe: {e}")
            self.db.rollback()
            return 0
    
    def _store_bars(self, bars: List[dict], ticker: Ticker, bar_size: str) -> int:
        """Store IBKR bars in database"""
        try:
            inserted = 0
            
            for bar in bars:
                # Check if record already exists
                exists = self.db.query(HistoricalData).filter(
                    HistoricalData.ticker_id == ticker.id,
                    HistoricalData.timestamp == bar['timestamp'],
                    HistoricalData.interval == bar_size
                ).first()
                
                if not exists:
                    record = HistoricalData(
                        ticker_id=ticker.id,
                        timestamp=bar['timestamp'],
                        open=bar['open'],
                        high=bar['high'],
                        low=bar['low'],
                        close=bar['close'],
                        volume=bar['volume'],
                        interval=bar_size
                    )
                    self.db.add(record)
                    inserted += 1
            
            self.db.commit()
            logger.info(f"✅ Inserted {inserted} new records for {ticker.symbol}")
            return inserted
            
        except Exception as e:
            logger.error(f"❌ Error storing bars: {e}")
            self.db.rollback()
            return 0
    
    def collect_multiple_tickers(
        self,
        tickers: List[tuple],
        duration: str = "1D",
        bar_size: str = "5min"
    ):
        """
        Collect data for multiple tickers
        
        Args:
            tickers: List of (symbol, name) tuples
            duration: Duration string
            bar_size: Bar size
        """
        for symbol, name in tickers:
            logger.info(f"Collecting data for {symbol} - {name}")
            self.collect_historical_data(symbol, name, duration, bar_size)
            # Small delay to avoid rate limiting
            import time
            time.sleep(1)
    
    def get_latest_data(self, symbol: str, limit: int = 100) -> pd.DataFrame:
        """
        Get latest historical data for a ticker
        
        Args:
            symbol: Stock symbol
            limit: Number of records to fetch
            
        Returns:
            DataFrame with historical data
        """
        try:
            ticker = self.db.query(Ticker).filter(Ticker.symbol == symbol).first()
            if not ticker:
                logger.warning(f"Ticker {symbol} not found")
                return pd.DataFrame()
            
            records = self.db.query(HistoricalData).filter(
                HistoricalData.ticker_id == ticker.id
            ).order_by(
                HistoricalData.timestamp.desc()
            ).limit(limit).all()
            
            if not records:
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for record in reversed(records):
                data.append({
                    'timestamp': record.timestamp,
                    'open': record.open,
                    'high': record.high,
                    'low': record.low,
                    'close': record.close,
                    'volume': record.volume,
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            return df
            
        except Exception as e:
            logger.error(f"Error getting latest data for {symbol}: {e}")
            return pd.DataFrame()
    
    def cleanup_old_data(self, days: int = None):
        """
        Delete old historical data
        
        Args:
            days: Number of days to retain (default from config)
        """
        if days is None:
            days = DATA_CONFIG["retention_days"]
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted = self.db.query(HistoricalData).filter(
                HistoricalData.timestamp < cutoff_date
            ).delete()
            
            self.db.commit()
            logger.info(f"Deleted {deleted} old records older than {days} days")
            return deleted
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            self.db.rollback()
            return 0
    
    def _generate_mock_data(self, symbol: str, duration: str, bar_size: str, ticker: Ticker) -> int:
        """Generate mock historical data for testing when IBKR is not available"""
        import numpy as np
        
        logger.info(f"Generating mock data for {symbol}")
        
        # Parse duration (simplified)
        days = 1
        if 'D' in duration:
            days = int(duration.split()[0])
        elif 'W' in duration:
            days = int(duration.split()[0]) * 7
        elif 'M' in duration:
            days = int(duration.split()[0]) * 30
        
        # Parse bar size
        if 'min' in bar_size:
            minutes = int(bar_size.split()[0])
            periods = (days * 24 * 60) // minutes
        else:
            # Default to hourly data
            periods = days * 24
        
        # Generate timestamps
        end_time = datetime.now()
        timestamps = [end_time - timedelta(minutes=i*minutes) for i in range(periods)]
        timestamps.reverse()
        
        # Generate mock OHLCV data
        base_price = 100.0  # Base price for the mock data
        records_created = 0
        
        for i, timestamp in enumerate(timestamps):
            # Generate realistic price movements
            change = np.random.normal(0, 0.02)  # Random walk with volatility
            if i > 0:
                base_price *= (1 + change)
            
            # Generate OHLC with some spread
            spread = base_price * 0.01  # 1% spread
            open_price = base_price + np.random.uniform(-spread/2, spread/2)
            high_price = open_price + abs(np.random.normal(0, spread/2))
            low_price = open_price - abs(np.random.normal(0, spread/2))
            close_price = np.random.uniform(low_price, high_price)
            volume = np.random.randint(1000, 10000)
            
            # Create historical data record
            hist_data = HistoricalData(
                ticker_id=ticker.id,
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
                interval=bar_size.replace(' ', '')
            )
            
            self.db.add(hist_data)
            records_created += 1
            
            # Commit every 100 records to avoid memory issues
            if records_created % 100 == 0:
                self.db.commit()
        
        self.db.commit()
        logger.info(f"Generated {records_created} mock records for {symbol}")
        return records_created
    
    def _get_yahoo_data(self, symbol: str, duration: str, bar_size: str) -> Optional[pd.DataFrame]:
        """Get data from Yahoo Finance"""
        try:
            # Convert duration to Yahoo format
            duration_map = {
                "1D": "1d", "5D": "5d", "1W": "1wk", "1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y"
            }
            yahoo_duration = duration_map.get(duration, "1mo")
            
            # Convert bar_size to Yahoo interval
            interval_map = {
                "1min": "1m", "5min": "5m", "15min": "15m", "30min": "30m", "1hour": "1h", "1day": "1d"
            }
            yahoo_interval = interval_map.get(bar_size, "1d")
            
            # For European stocks, add .PA suffix for Paris exchange
            yahoo_symbol = f"{symbol}.PA"
            
            ticker = yf.Ticker(yahoo_symbol)
            df = ticker.history(period=yahoo_duration, interval=yahoo_interval)
            
            if df.empty:
                return None
            
            # Rename columns to match our format
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high', 
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Convert timezone to UTC if needed
            if df.index.tz is not None:
                df.index = df.index.tz_convert('UTC')
            else:
                df.index = df.index.tz_localize('UTC')
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data for {symbol}: {e}")
            return None
    
    def _get_alpha_vantage_data(self, symbol: str, duration: str, bar_size: str) -> Optional[pd.DataFrame]:
        """Get data from Alpha Vantage"""
        try:
            # Convert bar_size to Alpha Vantage function
            if bar_size in ["1min", "5min", "15min", "30min", "60min"]:
                function = "TIME_SERIES_INTRADAY"
                interval = bar_size.replace("60min", "60min")
            else:
                function = "TIME_SERIES_DAILY"
                interval = None
            
            # For European stocks, use different symbol format
            av_symbol = f"{symbol}.PAR"  # Paris exchange
            
            if function == "TIME_SERIES_INTRADAY":
                data, meta_data = self.alpha_vantage_client.get_intraday(
                    symbol=av_symbol, 
                    interval=interval, 
                    outputsize='full'
                )
            else:
                data, meta_data = self.alpha_vantage_client.get_daily(
                    symbol=av_symbol, 
                    outputsize='full'
                )
            
            if data.empty:
                return None
            
            # Rename columns
            data = data.rename(columns={
                '1. open': 'open',
                '2. high': 'high',
                '3. low': 'low', 
                '4. close': 'close',
                '5. volume': 'volume'
            })
            
            # Convert to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                data[col] = pd.to_numeric(data[col], errors='coerce')
            
            # Convert index to datetime and UTC
            data.index = pd.to_datetime(data.index)
            if data.index.tz is None:
                data.index = data.index.tz_localize('UTC')
            
            return data[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {symbol}: {e}")
            return None
    
    def _get_polygon_data(self, symbol: str, duration: str, bar_size: str) -> Optional[pd.DataFrame]:
        """Get data from Polygon.io"""
        try:
            # Convert bar_size to Polygon timespan
            timespan_map = {
                "1min": "minute", "5min": "minute", "15min": "minute", "30min": "minute", 
                "1hour": "hour", "1day": "day"
            }
            multiplier_map = {
                "1min": 1, "5min": 5, "15min": 15, "30min": 30, "1hour": 1, "1day": 1
            }
            
            timespan = timespan_map.get(bar_size, "day")
            multiplier = multiplier_map.get(bar_size, 1)
            
            # Convert duration to date range
            duration_map = {
                "1D": 1, "5D": 5, "1W": 7, "1M": 30, "3M": 90, "6M": 180, "1Y": 365
            }
            days = duration_map.get(duration, 30)
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # For European stocks, try different formats
            # Polygon.io may not have all European stocks, so try multiple formats
            polygon_symbols = [
                f"{symbol}.PA",  # Euronext Paris
                symbol,          # Direct symbol (if available)
                f"{symbol}.AS",  # Amsterdam
                f"{symbol}.BR"   # Brussels
            ]
            
            aggs = None
            for polygon_symbol in polygon_symbols:
                try:
                    aggs = self.polygon_client.get_aggs(
                        ticker=polygon_symbol,
                        multiplier=multiplier,
                        timespan=timespan,
                        from_=start_date.strftime('%Y-%m-%d'),
                        to=end_date.strftime('%Y-%m-%d'),
                        limit=50000
                    )
                    if aggs:
                        logger.info(f"✅ Found data for {symbol} using {polygon_symbol}")
                        break
                except Exception as e:
                    logger.debug(f"Symbol {polygon_symbol} not found: {e}")
                    continue
            
            if not aggs:
                return None
            
            # Convert to DataFrame
            data = []
            for agg in aggs:
                data.append({
                    'timestamp': pd.to_datetime(agg.timestamp, unit='ms', utc=True),
                    'open': agg.open,
                    'high': agg.high,
                    'low': agg.low,
                    'close': agg.close,
                    'volume': agg.volume
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Error fetching Polygon.io data for {symbol}: {e}")
            return None


if __name__ == "__main__":
    # Example usage
    collector = DataCollector()
    
    # Collect data for TotalEnergies
    collector.collect_historical_data(
        symbol="TTE",
        name="TotalEnergies",
        duration="5 D",
        bar_size="5 mins"
    )
    
    # Get latest data
    df = collector.get_latest_data("TTE", limit=50)
    print(df.head())
