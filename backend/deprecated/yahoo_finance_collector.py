"""
Alternative data source for historical data - Yahoo Finance
Pour le backtesting et la création de stratégies avec des données réelles
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from backend.config import logger
from backend.models import SessionLocal, Ticker, HistoricalData


class YahooFinanceCollector:
    """
    Collecteur de données historiques via Yahoo Finance
    Alternative pour obtenir de gros volumes de données historiques
    """
    
    # Mapping des tickers français pour Yahoo Finance
    FRENCH_TICKER_MAPPING = {
        'GLE': 'GLE.PA',      # Société Générale
        'MC': 'MC.PA',        # LVMH
        'OR': 'OR.PA',        # L'Oréal
        'TTE': 'TTE.PA',      # TotalEnergies (ex FP.PA)
        'BNP': 'BNP.PA',      # BNP Paribas
        'AI': 'AI.PA',        # Air Liquide
        'SAN': 'SAN.PA',      # Sanofi
        'ACA': 'ACA.PA',      # Crédit Agricole
        'SU': 'SU.PA',        # Schneider Electric
        'CAP': 'CAP.PA',      # Capgemini
        'CS': 'CS.PA',        # AXA
        'DG': 'DG.PA',        # Vinci
        'BN': 'BN.PA',        # Danone
        'RI': 'RI.PA',        # Pernod Ricard
        'RMS': 'RMS.PA',      # Hermès
        'KER': 'KER.PA',      # Kering
    }
    
    def __init__(self):
        """Initialize Yahoo Finance collector"""
        logger.info("📊 Yahoo Finance collector initialized")
    
    def get_yahoo_ticker(self, symbol: str) -> str:
        """
        Convert French ticker to Yahoo Finance ticker
        
        Args:
            symbol: French ticker (e.g., 'GLE')
            
        Returns:
            Yahoo Finance ticker (e.g., 'GLE.PA')
        """
        return self.FRENCH_TICKER_MAPPING.get(symbol, f"{symbol}.PA")
    
    def fetch_historical_data(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical data from Yahoo Finance
        
        Args:
            symbol: French ticker symbol
            period: Data period ('1d','5d','1mo','3mo','6mo','1y','2y','5y','10y','ytd','max')
            interval: Data interval ('1m','2m','5m','15m','30m','60m','90m','1h','1d','5d','1wk','1mo','3mo')
            
        Returns:
            DataFrame with OHLCV data
            
        Note:
            - Pour interval < 1 jour, période max = 60 jours
            - Pour interval >= 1 jour, période max = illimitée
        """
        try:
            yahoo_ticker = self.get_yahoo_ticker(symbol)
            logger.info(f"📥 Fetching {symbol} ({yahoo_ticker}) from Yahoo Finance: period={period}, interval={interval}")
            
            ticker = yf.Ticker(yahoo_ticker)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"⚠️ No data received for {symbol}")
                return None
            
            # Rename columns to match our schema
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Keep only necessary columns
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            logger.info(f"✅ Received {len(df)} data points for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error fetching data from Yahoo Finance: {e}")
            return None
    
    def store_to_database(
        self,
        symbol: str,
        name: str,
        df: pd.DataFrame,
        progress_callback=None
    ) -> int:
        """
        Store data in database
        
        Args:
            symbol: Ticker symbol
            name: Company name
            df: DataFrame with historical data
            progress_callback: Optional callback(current, total) for progress updates
            
        Returns:
            Number of records inserted
        """
        if df is None or df.empty:
            return 0
        
        db = SessionLocal()
        try:
            # Get or create ticker
            ticker_obj = db.query(Ticker).filter(Ticker.symbol == symbol).first()
            if not ticker_obj:
                ticker_obj = Ticker(symbol=symbol, name=name)
                db.add(ticker_obj)
                db.commit()
                db.refresh(ticker_obj)
                logger.info(f"✅ Created ticker: {symbol}")
            
            inserted = 0
            total_rows = len(df)
            
            for idx, (timestamp, row) in enumerate(df.iterrows()):
                # Update progress
                if progress_callback:
                    progress_callback(idx + 1, total_rows)
                
                # Convert timestamp to datetime
                if isinstance(timestamp, pd.Timestamp):
                    timestamp = timestamp.to_pydatetime()
                
                # Check if record already exists
                existing = db.query(HistoricalData).filter(
                    HistoricalData.ticker_id == ticker_obj.id,
                    HistoricalData.timestamp == timestamp
                ).first()
                
                if not existing:
                    record = HistoricalData(
                        ticker_id=ticker_obj.id,
                        timestamp=timestamp,
                        open=float(row['open']),
                        high=float(row['high']),
                        low=float(row['low']),
                        close=float(row['close']),
                        volume=int(row['volume']),
                        interval='1day'  # Default, could be parameterized
                    )
                    db.add(record)
                    inserted += 1
            
            db.commit()
            logger.info(f"✅ Inserted {inserted} new records for {symbol}")
            return inserted
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error storing data: {e}")
            return 0
        finally:
            db.close()
    
    def collect_and_store_chunked(
        self,
        symbol: str,
        name: str,
        period: str = "1y",
        interval: str = "1d",
        progress_callback=None
    ) -> int:
        """
        Fetch and store historical data with automatic chunking for intraday intervals
        
        Args:
            symbol: French ticker symbol
            name: Company name
            period: Data period
            interval: Data interval
            progress_callback: Optional callback(current, total, message) for progress updates
            
        Returns:
            Number of records inserted
        """
        # Determine if we need chunking based on interval
        needs_chunking = False
        chunk_days = 1
        
        # Yahoo Finance limitations
        if interval == "1m":
            needs_chunking = True
            chunk_days = 7  # Max 7 days for 1 minute
        elif interval in ["2m", "5m", "15m", "30m"]:
            needs_chunking = True
            chunk_days = 59  # Max ~60 days for these intervals
        elif interval in ["1h", "90m"]:
            needs_chunking = True
            chunk_days = 729  # Max ~2 years for hourly
        
        # Parse period to days
        period_days = self._parse_period_to_days(period)
        
        # If no chunking needed or period is short enough, use regular method
        if not needs_chunking or period_days <= chunk_days:
            logger.info(f"📥 Single request for {symbol}: {period} @ {interval}")
            df = self.fetch_historical_data(symbol, period, interval)
            if df is not None:
                return self.store_to_database(symbol, name, df, progress_callback)
            return 0
        
        # Chunking required
        logger.info(f"🔄 Chunking required for {symbol}: {period} @ {interval}")
        logger.info(f"   Period: {period_days} days, Chunk size: {chunk_days} days")
        
        # Calculate number of chunks
        num_chunks = (period_days + chunk_days - 1) // chunk_days
        logger.info(f"   Total chunks: {num_chunks}")
        
        # Get end date (today)
        end_date = datetime.now()
        
        total_inserted = 0
        
        for chunk_idx in range(num_chunks):
            # Calculate date range for this chunk
            chunk_end = end_date - timedelta(days=chunk_idx * chunk_days)
            chunk_start = chunk_end - timedelta(days=chunk_days)
            
            # Make sure we don't go before the requested period
            actual_start = max(chunk_start, end_date - timedelta(days=period_days))
            
            # Progress callback
            if progress_callback:
                progress_callback(
                    chunk_idx + 1,
                    num_chunks,
                    f"Collecte chunk {chunk_idx + 1}/{num_chunks}: {actual_start.strftime('%Y-%m-%d')} → {chunk_end.strftime('%Y-%m-%d')}"
                )
            
            logger.info(f"   Chunk {chunk_idx + 1}/{num_chunks}: {actual_start.strftime('%Y-%m-%d')} → {chunk_end.strftime('%Y-%m-%d')}")
            
            # Fetch data for this chunk using start/end dates
            df = self._fetch_with_dates(symbol, actual_start, chunk_end, interval)
            
            if df is not None and not df.empty:
                inserted = self.store_to_database(symbol, name, df, progress_callback)
                total_inserted += inserted
                logger.info(f"   ✅ Chunk {chunk_idx + 1}: {inserted} records inserted")
            else:
                logger.warning(f"   ⚠️ Chunk {chunk_idx + 1}: No data received")
        
        logger.info(f"✅ Chunked collection complete: {total_inserted} total records inserted")
        return total_inserted
    
    def _parse_period_to_days(self, period: str) -> int:
        """Convert period string to number of days"""
        period_map = {
            "1d": 1,
            "5d": 5,
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365,
            "2y": 730,
            "5y": 1825,
            "10y": 3650,
            "max": 9999  # Large number for max
        }
        return period_map.get(period, 365)
    
    def _fetch_with_dates(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> Optional[pd.DataFrame]:
        """
        Fetch data using specific start and end dates
        
        Args:
            symbol: Ticker symbol
            start_date: Start datetime
            end_date: End datetime
            interval: Data interval
            
        Returns:
            DataFrame with OHLCV data or None
        """
        # Convert to Yahoo Finance ticker
        yahoo_symbol = self.FRENCH_TICKER_MAPPING.get(symbol, f"{symbol}.PA")
        
        try:
            ticker = yf.Ticker(yahoo_symbol)
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=False
            )
            
            if df.empty:
                return None
            
            # Rename columns
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Keep only necessary columns
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error fetching data: {e}")
            return None
    
    def collect_and_store(
        self,
        symbol: str,
        name: str,
        period: str = "1y",
        interval: str = "1d",
        progress_callback=None
    ) -> int:
        """
        Fetch and store historical data in one operation
        
        Args:
            symbol: French ticker symbol
            name: Company name
            period: Data period
            interval: Data interval
            progress_callback: Optional callback(current, total) for progress updates
            
        Returns:
            Number of records inserted
        """
        df = self.fetch_historical_data(symbol, period, interval)
        if df is not None:
            return self.store_to_database(symbol, name, df, progress_callback)
        return 0
    
    @staticmethod
    def delete_ticker_data(symbol: str) -> dict:
        """
        Delete all historical data for a specific ticker
        
        Args:
            symbol: Ticker symbol to delete
            
        Returns:
            Dictionary with deletion info: {'success': bool, 'deleted_records': int, 'message': str}
        """
        db = SessionLocal()
        try:
            # Find the ticker
            ticker_obj = db.query(Ticker).filter(Ticker.symbol == symbol).first()
            
            if not ticker_obj:
                logger.warning(f"⚠️ Ticker {symbol} not found in database")
                return {
                    'success': False,
                    'deleted_records': 0,
                    'message': f"Le ticker {symbol} n'existe pas en base"
                }
            
            # Count records before deletion
            record_count = db.query(HistoricalData).filter(
                HistoricalData.ticker_id == ticker_obj.id
            ).count()
            
            # Delete all historical data for this ticker
            db.query(HistoricalData).filter(
                HistoricalData.ticker_id == ticker_obj.id
            ).delete()
            
            # Delete the ticker itself
            db.delete(ticker_obj)
            
            db.commit()
            
            logger.info(f"✅ Deleted {record_count} records for ticker {symbol}")
            
            return {
                'success': True,
                'deleted_records': record_count,
                'message': f"Suppression réussie : {record_count} enregistrements supprimés pour {symbol}"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error deleting ticker data: {e}")
            return {
                'success': False,
                'deleted_records': 0,
                'message': f"Erreur lors de la suppression : {str(e)}"
            }
        finally:
            db.close()


def demo_yahoo_finance():
    """Demonstration of Yahoo Finance collector"""
    
    print("\n" + "="*70)
    print("COLLECTEUR YAHOO FINANCE - DÉMONSTRATION")
    print("="*70)
    print("\n💡 Yahoo Finance permet de récupérer:")
    print("   - Jusqu'à 10 ans d'historique quotidien")
    print("   - Jusqu'à 60 jours d'historique intraday (1min, 5min, etc.)")
    print("   - SANS limite de 1200 points !")
    print("\n" + "="*70)
    
    collector = YahooFinanceCollector()
    
    # Test 1: Récupérer 5 ans de données quotidiennes
    print("\n🔍 Test 1: 5 ans de données quotidiennes pour Société Générale")
    print("-" * 70)
    
    inserted = collector.collect_and_store(
        symbol="GLE",
        name="Société Générale",
        period="5y",
        interval="1d"
    )
    
    if inserted > 0:
        print(f"✅ {inserted} points collectés (environ 1250 jours de bourse)")
        print("   → Parfait pour le backtesting long terme !")
    
    # Test 2: Données intraday récentes
    print("\n🔍 Test 2: 60 jours de données 1 heure pour LVMH")
    print("-" * 70)
    
    inserted = collector.collect_and_store(
        symbol="MC",
        name="LVMH",
        period="60d",
        interval="1h"
    )
    
    if inserted > 0:
        print(f"✅ {inserted} points collectés")
        print("   → Idéal pour stratégies intraday !")
    
    # Test 3: Maximum de données
    print("\n🔍 Test 3: Maximum de données (10 ans) pour TotalEnergies")
    print("-" * 70)
    
    inserted = collector.collect_and_store(
        symbol="TTE",
        name="TotalEnergies",
        period="max",
        interval="1d"
    )
    
    if inserted > 0:
        print(f"✅ {inserted} points collectés")
        print("   → Données historiques complètes pour analyse approfondie !")
    
    # Afficher les statistiques
    print("\n" + "="*70)
    print("STATISTIQUES DE LA BASE DE DONNÉES")
    print("="*70)
    
    db = SessionLocal()
    try:
        for ticker in db.query(Ticker).all():
            count = db.query(HistoricalData).filter(
                HistoricalData.ticker_id == ticker.id
            ).count()
            print(f"   {ticker.symbol}: {count:,} points")
    finally:
        db.close()
    
    print("\n💡 Avantages de Yahoo Finance:")
    print("   ✅ Gratuit et sans limite stricte")
    print("   ✅ Données historiques sur plusieurs années")
    print("   ✅ Fiable et largement utilisé")
    print("   ✅ Pas besoin de compte production")
    print("\n⚠️  Limitations:")
    print("   - Données intraday limitées à 60 jours")
    print("   - Pas de données tick-by-tick")
    print("   - Peut avoir un léger délai (15-20 min)")


if __name__ == "__main__":
    # Vérifier si yfinance est installé
    try:
        import yfinance
        demo_yahoo_finance()
    except ImportError:
        print("\n❌ Erreur: Le module 'yfinance' n'est pas installé")
        print("\n📦 Pour l'installer:")
        print("   pip install yfinance")
        print("\n💡 Une fois installé, relancez ce script pour collecter des données !")
