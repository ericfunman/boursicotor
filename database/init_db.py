"""
Database initialization script
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.models import init_db, Ticker, SessionLocal
from backend.config import logger, FRENCH_TICKERS


def initialize_database():
    """Initialize database with tables and initial data"""
    try:
        logger.info("Initializing database...")
        
        # Create all tables
        init_db()
        logger.info("✅ Database tables created successfully")
        
        # Add French tickers
        db = SessionLocal()
        try:
            for symbol, name in FRENCH_TICKERS.items():
                # Check if ticker already exists
                existing = db.query(Ticker).filter(Ticker.symbol == symbol).first()
                if not existing:
                    ticker = Ticker(
                        symbol=symbol,
                        name=name,
                        exchange="EURONEXT",
                        currency="EUR",
                        is_active=True
                    )
                    db.add(ticker)
                    logger.info(f"Added ticker: {symbol} - {name}")
            
            db.commit()
            logger.info("✅ Initial tickers added successfully")
            
        except Exception as e:
            logger.error(f"Error adding tickers: {e}")
            db.rollback()
        finally:
            db.close()
        
        logger.info("✅ Database initialization completed")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


if __name__ == "__main__":
    print("🚀 Initializing Boursicotor Database...")
    print("=" * 50)
    
    initialize_database()
    
    print("=" * 50)
    print("✅ Database initialization completed!")
    print("\nNext steps:")
    print("1. Update .env file with your database credentials")
    print("2. Update .env file with your IBKR credentials")
    print("3. Run: streamlit run frontend/app.py")
