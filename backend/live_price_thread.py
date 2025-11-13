"""
Background thread for collecting live market prices
Runs independently from Streamlit and saves to database
"""
import threading
import time
from typing import Optional, Callable
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models import SessionLocal, Ticker, HistoricalData
from backend.ibkr_collector import IBKRCollector
from backend.config import logger


class LivePriceCollector:
    """Manages background thread for collecting live prices"""
    
    def __init__(self):
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.symbol: Optional[str] = None
        self.interval = 3  # seconds between price collections
    
    def start(self, symbol: str, interval: int = 3) -> bool:
        """
        Start collecting live prices for a symbol
        
        Args:
            symbol: Stock symbol (e.g., 'TTE')
            interval: Seconds between price collections (default: 3)
            
        Returns:
            True if started successfully
        """
        if self.running:
            logger.warning(f"Live price collector already running for {self.symbol}")
            return False
        
        self.symbol = symbol
        self.interval = interval
        self.running = True
        
        # Start background thread
        self.thread = threading.Thread(
            target=self._collect_prices,
            daemon=True,
            name=f"LivePriceCollector-{symbol}"
        )
        self.thread.start()
        logger.info(f"Live price collector started for {symbol} (interval: {interval}s)")
        return True
    
    def stop(self) -> bool:
        """Stop collecting live prices"""
        if not self.running:
            return False
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info(f"Live price collector stopped for {self.symbol}")
        return True
    
    def _collect_prices(self):
        """Background thread function - runs continuously"""
        collector = None
        db: Optional[Session] = None
        
        try:
            # Initialize database connection for this thread
            db = SessionLocal()
            
            # Create IBKR collector
            collector = IBKRCollector()
            
            logger.info(f"[LivePriceCollector] Starting price collection for {self.symbol}")
            
            while self.running:
                try:
                    # Get current market price
                    price = collector.get_current_market_price(self.symbol, "EUR")
                    
                    if price is not None:
                        # Save to database
                        self._save_price_to_db(db, self.symbol, price)
                        logger.info(f"[LivePriceCollector] {self.symbol}: {price}€ saved to DB")
                    else:
                        logger.warning(f"[LivePriceCollector] No price retrieved for {self.symbol}")
                    
                    # Wait before next collection
                    time.sleep(self.interval)
                    
                except Exception as e:
                    logger.error(f"[LivePriceCollector] Error collecting price: {e}", exc_info=True)
                    time.sleep(self.interval)
        
        except Exception as e:
            logger.error(f"[LivePriceCollector] Fatal error: {e}", exc_info=True)
        
        finally:
            # Cleanup
            if db:
                db.close()
            if collector:
                try:
                    collector.disconnect()
                except:
                    pass
            logger.info(f"[LivePriceCollector] Thread ended for {self.symbol}")
    
    def _save_price_to_db(self, db: Session, symbol: str, price: float) -> bool:
        """Save price to database"""
        try:
            # Get or create ticker
            ticker = db.query(Ticker).filter(Ticker.symbol == symbol).first()
            if not ticker:
                ticker = Ticker(
                    symbol=symbol,
                    name=symbol,
                    exchange="EURONEXT",
                    currency="EUR"
                )
                db.add(ticker)
                db.commit()
                db.refresh(ticker)
            
            # Create historical data record
            record = HistoricalData(
                ticker_id=ticker.id,
                timestamp=datetime.now(),
                open=price,
                high=price,
                low=price,
                close=price,
                volume=0,
                interval='1day'  # Live data stored as daily interval
            )
            db.add(record)
            db.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error saving price to DB: {e}")
            db.rollback()
            return False


# Global instance
_live_collector = LivePriceCollector()


def start_live_price_collection(symbol: str, interval: int = 3) -> bool:
    """Start live price collection for a symbol"""
    return _live_collector.start(symbol, interval)


def stop_live_price_collection() -> bool:
    """Stop live price collection"""
    return _live_collector.stop()


def is_collecting(symbol: Optional[str] = None) -> bool:
    """Check if collecting live prices"""
    if symbol:
        return _live_collector.running and _live_collector.symbol == symbol
    return _live_collector.running


def get_current_symbol() -> Optional[str]:
    """Get symbol currently being collected"""
    return _live_collector.symbol if _live_collector.running else None
