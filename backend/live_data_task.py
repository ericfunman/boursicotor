"""
Celery task for live data collection and streaming
"""
from datetime import datetime, timedelta
from backend.celery_config import celery_app
from backend.models import SessionLocal, Ticker as TickerModel, HistoricalData
from backend.config import logger
from backend.ibkr_collector import IBKRCollector
import time
import json
import redis

# Redis connection for live data storage
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    logger.info("[Live Task] Redis connected for live data caching")
except Exception:
    redis_client = None
    logger.warning("[Live Task] Redis not available for live data caching")


@celery_app.task(bind=True)
def stream_live_data_continuous(self, symbol: str, duration: int = 300):
    """
    Stream live data from IBKR to Redis for a specific symbol
    Runs in background and updates Redis cache every second
    
    Uses portfolio prices as fallback if market data subscription fails
    
    Args:
        symbol: Stock symbol (e.g., 'WLN')
        duration: Collection duration in seconds (default: 5 minutes)
    
    Returns:
        Dictionary with collection summary
    """
    try:
        logger.info(f"[Stream] Starting live stream for {symbol} (duration: {duration}s)")
        
        # Initialize collector with dedicated client_id for Celery tasks
        collector = IBKRCollector(client_id=2)  # Use client_id=2 for Celery live data tasks
        if not collector.connect():
            logger.error(f"[Stream] Failed to connect to IBKR for {symbol}")
            return {'success': False, 'error': 'IBKR connection failed'}
        
        # Get contract - this now tries SBF first for EUR stocks
        contract = collector.get_contract(symbol)
        if not contract:
            logger.error(f"[Stream] Contract not found for {symbol}")
            collector.disconnect()
            return {'success': False, 'error': f'Contract not found for {symbol}'}
        
        logger.info(f"[Stream] Contract: {contract.symbol} on exchange={contract.exchange} (primaryExchange={contract.primaryExchange})")
        
        # Try to get market data, but fall back to portfolio if subscription fails
        logger.info(f"[Stream] Requesting market data for {symbol}")
        ticker_data = collector.ib.reqMktData(contract, '', False, False)
        
        # Stream data
        collected_count = 0
        start_time = time.time()
        redis_key = f"live_data:{symbol}"
        last_price = None
        use_portfolio_fallback = False
        
        # Initial wait to let IBKR send delayed data (longer for delayed data)
        logger.info(f"[Stream] Waiting for market data to arrive (delayed data may take 2-5 seconds)...")
        wait_count = 0
        for _ in range(15):  # Wait up to 7.5 seconds for delayed data
            if ticker_data.last > 0 or ticker_data.close > 0:
                logger.info(f"[Stream] ✅ Got market data for {symbol} after {wait_count*0.5:.1f}s")
                break
            wait_count += 1
            collector.ib.sleep(0.5)
        else:
            logger.warning(f"[Stream] ⚠️ Market data not available for {symbol}, will use portfolio prices as fallback")
            use_portfolio_fallback = True
        
        while time.time() - start_time < duration:
            try:
                # Get price - try market data first, then portfolio
                price = None
                
                if use_portfolio_fallback:
                    # Use portfolio prices as fallback
                    try:
                        portfolio = collector.ib.portfolio()
                        for item in portfolio:
                            if item.contract.symbol == symbol:
                                price = item.marketPrice
                                # Removed verbose debug - only log on price change
                                break
                    except Exception as e:
                        pass  # Silently continue on portfolio error
                else:
                    # Use market data
                    price = ticker_data.last if ticker_data.last > 0 else ticker_data.close
                
                # Always update Redis if we have a price (not just on change)
                if price and price > 0:
                    data_point = {
                        'symbol': symbol,
                        'timestamp': datetime.now().isoformat(),
                        'price': price,
                        'open': ticker_data.open if ticker_data.open > 0 else price,
                        'high': ticker_data.high if ticker_data.high > 0 else price,
                        'low': ticker_data.low if ticker_data.low > 0 else price,
                        'close': ticker_data.close if ticker_data.close > 0 else price,
                        'volume': ticker_data.volume if ticker_data.volume > 0 else 0,
                        'bid': ticker_data.bid if ticker_data.bid > 0 else price,
                        'ask': ticker_data.ask if ticker_data.ask > 0 else price,
                    }
                    
                    # Store in Redis with 60 second TTL - always update
                    if redis_client:
                        try:
                            redis_client.setex(
                                redis_key,
                                60,  # TTL
                                json.dumps(data_point)
                            )
                            if price != last_price:
                                logger.info(f"[Stream] {symbol}: {price}€ (updated)")
                                collected_count += 1
                            last_price = price
                        except Exception as e:
                            logger.warning(f"[Stream] Redis error: {e}")
                
                # Wait before next check
                collector.ib.sleep(0.2)  # Check more frequently (5 times per second)
            
            except Exception as e:
                logger.warning(f"[Stream] Error in loop: {e}")
                continue
        
        # Cancel market data subscription
        try:
            collector.ib.cancelMktData(contract)
        except Exception:
            pass
        
        collector.disconnect()
        
        logger.info(f"[Stream] Collected {collected_count} data points for {symbol}")
        
        return {
            'success': True,
            'symbol': symbol,
            'count': collected_count
        }
    
    except Exception as e:
        logger.error(f"[Stream] Error: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}
