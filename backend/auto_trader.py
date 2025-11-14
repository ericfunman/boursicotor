"""
Automatic Trading System
Monitors live prices, calculates indicators, and executes trades based on strategy signals
"""
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
import numpy as np
from loguru import logger

from backend.models import (
    SessionLocal, AutoTraderSession, AutoTraderStatus, 
    Ticker, Strategy, Order, OrderStatus, HistoricalData
)
from backend.order_manager import OrderManager
from backend.data_collector import DataCollector
from backend.ibkr_collector import IBKRCollector


class AutoTrader:
    """
    Automatic trading system that:
    1. Polls live prices at regular intervals
    2. Calculates strategy indicators
    3. Detects BUY/SELL signals
    4. Executes trades automatically
    """
    
    def __init__(self, session_id: int, ibkr_collector: Optional[IBKRCollector] = None):
        """
        Initialize AutoTrader for a specific session
        
        Args:
            session_id: Database ID of the AutoTraderSession
            ibkr_collector: IBKR connection for live data and order execution
        """
        self.session_id = session_id
        self.ibkr_collector = ibkr_collector
        self.data_collector = DataCollector()
        self.order_manager = OrderManager(ibkr_collector)
        
        # Runtime state
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.price_buffer: List[Dict] = []  # Buffer of recent prices for indicator calculation
        self.buffer_size = 200  # Keep last 200 data points
        
        # Load session from database
        self.load_session()
    
    def load_session(self):
        """Load session configuration from database"""
        db = SessionLocal()
        try:
            session = db.query(AutoTraderSession).filter(
                AutoTraderSession.id == self.session_id
            ).first()
            
            if not session:
                raise ValueError(f"AutoTrader session {self.session_id} not found")
            
            self.session = session
            self.ticker = session.ticker
            self.strategy = session.strategy
            
            logger.info(f"AutoTrader loaded: Session #{self.session_id}, {self.ticker.symbol}, Strategy: {self.strategy.name}")
            
        finally:
            db.close()
    
    def start(self):
        """Start the automatic trading loop"""
        if self.running:
            logger.warning(f"AutoTrader #{self.session_id} already running")
            return
        
        self.running = True
        
        # Update session status
        db = SessionLocal()
        try:
            session = db.query(AutoTraderSession).filter(
                AutoTraderSession.id == self.session_id
            ).first()
            session.status = AutoTraderStatus.RUNNING
            session.started_at = datetime.now()
            session.stopped_at = None
            session.error_message = None
            db.commit()
        finally:
            db.close()
        
        # Start live price collection for this ticker
        # This ensures we have real-time price data for strategy signals
        from backend.live_price_thread import start_live_price_collection
        start_live_price_collection(self.ticker.symbol, interval=10)
        logger.info(f"📊 Live price collection started for {self.ticker.symbol}")
        
        # Start trading loop in separate thread
        self.thread = threading.Thread(target=self._trading_loop, daemon=True)
        self.thread.start()
        
        logger.info(f"✅ AutoTrader #{self.session_id} started")
    
    def stop(self):
        """Stop the automatic trading loop"""
        if not self.running:
            logger.warning(f"AutoTrader #{self.session_id} not running")
            return
        
        self.running = False
        
        # Stop live price collection
        from backend.live_price_thread import stop_live_price_collection
        stop_live_price_collection()
        logger.info(f"📊 Live price collection stopped")
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        # Update session status
        db = SessionLocal()
        try:
            session = db.query(AutoTraderSession).filter(
                AutoTraderSession.id == self.session_id
            ).first()
            session.status = AutoTraderStatus.STOPPED
            session.stopped_at = datetime.now()
            db.commit()
        finally:
            db.close()
        
        logger.info(f"🛑 AutoTrader #{self.session_id} stopped")
    
    def _trading_loop(self):
        """Main trading loop - runs in separate thread"""
        logger.info(f"Trading loop started for session #{self.session_id}")
        
        # Load initial historical data for buffer
        self._init_price_buffer()
        
        while self.running:
            try:
                # 1. Fetch current price
                current_price = self._fetch_live_price()
                
                if current_price:
                    # 2. Add to buffer
                    self._add_to_buffer(current_price)
                    
                    # 3. Calculate indicators
                    signals = self._calculate_signals()
                    
                    # 4. Check for trading signal
                    if signals:
                        self._process_signal(signals)
                    
                    # 5. Update session
                    self._update_session()
                
                # Wait for next polling interval
                db = SessionLocal()
                try:
                    session = db.query(AutoTraderSession).filter(
                        AutoTraderSession.id == self.session_id
                    ).first()
                    interval = session.polling_interval
                finally:
                    db.close()
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                self._handle_error(str(e))
                time.sleep(60)  # Wait 1 minute on error
        
        logger.info(f"Trading loop ended for session #{self.session_id}")
    
    def _init_price_buffer(self):
        """Initialize price buffer with recent historical data"""
        logger.info(f"Initializing price buffer for {self.ticker.symbol} (ticker_id={self.ticker.id})...")
        
        db = SessionLocal()
        try:
            # Debug: Check how many historical data points exist for this ticker
            total_count = db.query(HistoricalData).filter(
                HistoricalData.ticker_id == self.ticker.id
            ).count()
            logger.info(f"Total historical data points in DB for ticker_id {self.ticker.id}: {total_count}")
            
            # Get last 200 historical data points - use 'timestamp' instead of 'date'
            historical = db.query(HistoricalData).filter(
                HistoricalData.ticker_id == self.ticker.id
            ).order_by(HistoricalData.timestamp.desc()).limit(self.buffer_size).all()
            
            logger.info(f"Found {len(historical)} historical data points to load into buffer")
            
            # Reverse to chronological order
            historical = list(reversed(historical))
            
            # Add to buffer
            for h in historical:
                self.price_buffer.append({
                    'timestamp': h.timestamp,  # Use timestamp instead of date
                    'open': h.open,
                    'high': h.high,
                    'low': h.low,
                    'close': h.close,
                    'volume': h.volume
                })
            
            logger.info(f"✅ Initialized price buffer with {len(self.price_buffer)} historical data points")
            
        except Exception as e:
            logger.error(f"❌ Error initializing price buffer: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            db.close()
    
    def _get_contract_info(self) -> tuple:
        """Get ticker exchange and currency information"""
        exchange = self.ticker.exchange if hasattr(self.ticker, 'exchange') else 'SMART'
        currency = self.ticker.currency if hasattr(self.ticker, 'currency') else 'EUR'
        return exchange, currency
    
    def _fetch_live_price(self) -> Optional[Dict]:
        """
        Fetch current live price from live_price_thread collection
        The live_price_thread continuously collects 1-min bars and saves to DB
        This method retrieves those saved prices for the trading loop
        
        Returns:
            Dictionary with price data or None if failed
        """
        try:
            logger.debug(f"Fetching live price for {self.ticker.symbol}...")
            
            # Get prices collected by live_price_thread from DB (1-minute bars)
            # These are collected every 10 seconds with real-time data
            db = SessionLocal()
            try:
                # Query 1-minute bars (collected by live_price_thread)
                latest_price = db.query(HistoricalData).filter(
                    HistoricalData.ticker_id == self.ticker.id,
                    HistoricalData.interval == '1min'  # 1-minute bars from live_price_thread
                ).order_by(HistoricalData.timestamp.desc()).first()
                
                if latest_price:
                    logger.debug(f"Got live price from live_price_thread collection: {latest_price.close:.4f} @ {latest_price.timestamp}")
                    return {
                        'timestamp': latest_price.timestamp,
                        'open': latest_price.open,
                        'high': latest_price.high,
                        'low': latest_price.low,
                        'close': latest_price.close,
                        'volume': latest_price.volume if latest_price.volume else 0
                    }
                else:
                    logger.warning(f"No 1-minute bar data collected for {self.ticker.symbol}")
            finally:
                db.close()
            
            logger.warning(f"❌ Could not fetch live price for {self.ticker.symbol} (no DB data)")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error fetching live price: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _add_to_buffer(self, price_data: Dict):
        """Add new price data to buffer and maintain buffer size"""
        self.price_buffer.append(price_data)
        
        # Keep only last buffer_size entries
        if len(self.price_buffer) > self.buffer_size:
            self.price_buffer = self.price_buffer[-self.buffer_size:]
    
    def _calculate_signals(self) -> Optional[Dict]:
        """
        Calculate strategy indicators and detect signals
        
        Returns:
            Dictionary with signal info or None if no signal
        """
        if len(self.price_buffer) < 50:  # Need minimum data for indicators
            logger.debug("Not enough data in buffer for signal calculation")
            return None
        
        try:
            # Convert buffer to DataFrame
            df = pd.DataFrame(self.price_buffer)
            df['date'] = df['timestamp']
            df = df.set_index('date')
            
            # Calculate strategy indicators
            from backend.strategy_runner import StrategyRunner
            
            runner = StrategyRunner()
            signals_df = runner.generate_signals(df, self.strategy)
            
            if signals_df is None or signals_df.empty:
                return None
            
            # Get latest signal
            latest = signals_df.iloc[-1]
            
            signal_dict = {
                'timestamp': datetime.now(),
                'price': latest['close'],
                'signal': latest.get('signal', 0),
                'indicators': {}
            }
            
            # Extract indicator values for logging
            for col in signals_df.columns:
                if col not in ['open', 'high', 'low', 'close', 'volume', 'signal', 'position']:
                    signal_dict['indicators'][col] = latest.get(col, None)
            
            logger.debug(f"Signal calculated: {signal_dict['signal']} at {signal_dict['price']}")
            
            return signal_dict
            
        except Exception as e:
            logger.error(f"Error calculating signals: {e}")
            return None
    
    def _determine_action_and_quantity(self, signal_value: int, session) -> tuple:
        """
        Determine trading action and quantity based on signal
        
        Args:
            signal_value: Trading signal (1=BUY, -1=SELL, 0=HOLD)
            session: AutoTraderSession object
            
        Returns:
            Tuple (action, quantity) or (None, 0) if no action
        """
        if signal_value == 1:  # BUY signal
            if session.current_position < session.max_position_size:
                quantity = min(
                    session.max_position_size - session.current_position,
                    session.max_position_size // 10  # Buy in chunks of 10%
                )
                return "BUY", quantity
                
        elif signal_value == -1:  # SELL signal
            if session.current_position > 0:
                return "SELL", session.current_position  # Sell all
        
        return None, 0
    
    def _process_signal(self, signals: Dict):
        """
        Process trading signal and execute order if conditions are met
        
        Args:
            signals: Signal dictionary from _calculate_signals
        """
        signal_value = signals.get('signal', 0)
        current_price = signals.get('price')
        
        if signal_value == 0:  # HOLD
            return
        
        db = SessionLocal()
        try:
            session = db.query(AutoTraderSession).filter(
                AutoTraderSession.id == self.session_id
            ).first()
            
            # Check trading limits
            if session.total_orders >= session.max_daily_trades:
                logger.warning(f"Max daily trades reached ({session.max_daily_trades})")
                return
            
            # Determine action and quantity
            action, quantity = self._determine_action_and_quantity(signal_value, session)
            
            if action and quantity > 0:
                logger.info(f"🎯 Signal detected: {action} {quantity} {self.ticker.symbol} @ {current_price}")
                
                # Create and execute order
                order = self.order_manager.create_order(
                    symbol=self.ticker.symbol,
                    action=action,
                    order_type="MARKET",
                    quantity=quantity,
                    strategy_id=self.strategy.id
                )
                
                if order:
                    # Update session
                    session.total_orders += 1
                    session.last_signal = action
                    session.last_signal_at = datetime.now()
                    
                    # Update position (optimistic - will be corrected by sync)
                    if action == "BUY":
                        session.current_position += quantity
                    else:
                        session.current_position -= quantity
                    
                    db.commit()
                    
                    logger.info(f"✅ Order #{order.id} created: {action} {quantity} {self.ticker.symbol}")
                else:
                    session.failed_orders += 1
                    db.commit()
                    logger.error("❌ Failed to create order")
            
        finally:
            db.close()
        
        # Sync position with IBKR to correct any optimistic estimates
        self._sync_position_with_ibkr()
    
    def _update_session(self):
        """Update session with latest state"""
        db = SessionLocal()
        try:
            session = db.query(AutoTraderSession).filter(
                AutoTraderSession.id == self.session_id
            ).first()
            
            session.last_check_at = datetime.now()
            session.updated_at = datetime.now()
            
            db.commit()
            
        finally:
            db.close()
    
    def _sync_position_with_ibkr(self):
        """
        Synchronize current position with actual IBKR portfolio
        This ensures we have the true position, not an optimistic estimate
        """
        try:
            if not self.ibkr_collector or not self.ibkr_collector.ib.isConnected():
                logger.warning("Cannot sync position: IBKR not connected")
                return None
            
            # Get all positions from IBKR
            ib_positions = self.ibkr_collector.ib.positions()
            
            # Find our ticker's position
            actual_position = 0
            for pos in ib_positions:
                if pos.contract.symbol == self.ticker.symbol:
                    actual_position = int(pos.position)
                    logger.info(f"📊 Position sync: {self.ticker.symbol} = {actual_position} shares (from IBKR)")
                    break
            
            # Update session with actual position
            db = SessionLocal()
            try:
                session = db.query(AutoTraderSession).filter(
                    AutoTraderSession.id == self.session_id
                ).first()
                
                if session.current_position != actual_position:
                    logger.info(f"Position corrected: {session.current_position} -> {actual_position}")
                    session.current_position = actual_position
                    db.commit()
                
                return actual_position
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error syncing position with IBKR: {e}")
            return None
    
    def _handle_error(self, error_message: str):
        """Handle error in trading loop"""
        logger.error(f"AutoTrader #{self.session_id} error: {error_message}")
        
        db = SessionLocal()
        try:
            session = db.query(AutoTraderSession).filter(
                AutoTraderSession.id == self.session_id
            ).first()
            
            session.status = AutoTraderStatus.ERROR
            session.error_message = error_message
            session.updated_at = datetime.now()
            
            db.commit()
            
        finally:
            db.close()
        
        # Stop trading on error
        self.running = False
    
    def get_status(self) -> Dict:
        """Get current status of the auto trader"""
        db = SessionLocal()
        try:
            session = db.query(AutoTraderSession).filter(
                AutoTraderSession.id == self.session_id
            ).first()
            
            return {
                'session_id': session.id,
                'status': session.status.value,
                'ticker': session.ticker.symbol,
                'strategy': session.strategy.name,
                'running': self.running,
                'current_position': session.current_position,
                'total_orders': session.total_orders,
                'successful_orders': session.successful_orders,
                'failed_orders': session.failed_orders,
                'total_pnl': session.total_pnl,
                'last_signal': session.last_signal,
                'last_signal_at': session.last_signal_at,
                'last_check_at': session.last_check_at,
                'started_at': session.started_at,
                'buffer_size': len(self.price_buffer)
            }
            
        finally:
            db.close()


class AutoTraderManager:
    """Manages multiple AutoTrader instances"""
    
    def __init__(self, ibkr_collector: Optional[IBKRCollector] = None):
        """TODO: Add docstring."""
        self.ibkr_collector = ibkr_collector
        self.traders: Dict[int, AutoTrader] = {}  # session_id -> AutoTrader
    
    def create_session(self, ticker_id: int, strategy_id: int, config: Dict = None) -> int:
        """
        Create new auto trading session
        
        Args:
            ticker_id: Ticker database ID
            strategy_id: Strategy database ID
            config: Optional configuration overrides
        
        Returns:
            Session ID
        """
        db = SessionLocal()
        try:
            session = AutoTraderSession(
                ticker_id=ticker_id,
                strategy_id=strategy_id,
                status=AutoTraderStatus.STOPPED,
                polling_interval=config.get('polling_interval', 60) if config else 60,
                max_position_size=config.get('max_position_size', 100) if config else 100,
                max_daily_trades=config.get('max_daily_trades', 10) if config else 10,
                stop_loss_pct=config.get('stop_loss_pct', 2.0) if config else 2.0,
                take_profit_pct=config.get('take_profit_pct', 5.0) if config else 5.0
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            logger.info(f"Created AutoTrader session #{session.id}")
            
            return session.id
            
        finally:
            db.close()
    
    def start_session(self, session_id: int):
        """Start an auto trading session"""
        if session_id in self.traders:
            logger.warning(f"Session #{session_id} already has active trader")
            return
        
        # Log IBKR connection status
        ibkr_connected = self.ibkr_collector and self.ibkr_collector.ib.isConnected()
        logger.info(f"Starting session #{session_id} - IBKR connected: {ibkr_connected}")
        
        trader = AutoTrader(session_id, self.ibkr_collector)
        trader.start()
        self.traders[session_id] = trader
    
    def stop_session(self, session_id: int):
        """Stop an auto trading session"""
        trader = self.traders.get(session_id)
        if trader:
            trader.stop()
            del self.traders[session_id]
        else:
            logger.warning(f"No active trader for session #{session_id}")
    
    def stop_all(self):
        """Stop all active trading sessions"""
        for session_id in self.traders.keys():
            self.stop_session(session_id)
    
    def get_all_sessions(self) -> List[Dict]:
        """Get all trading sessions"""
        db = SessionLocal()
        try:
            sessions = db.query(AutoTraderSession).order_by(
                AutoTraderSession.created_at.desc()
            ).all()
            
            result = []
            for session in sessions:
                # Skip sessions with orphaned references
                if session.ticker is None or session.strategy is None:
                    logger.warning(f"Skipping session #{session.id}: orphaned ticker or strategy")
                    continue
                
                result.append({
                    'id': session.id,
                    'ticker': session.ticker.symbol,
                    'strategy': session.strategy.name,
                    'status': session.status.value,
                    'current_position': session.current_position,
                    'total_orders': session.total_orders,
                    'total_pnl': session.total_pnl,
                    'started_at': session.started_at,
                    'stopped_at': session.stopped_at,
                    'is_active': session.id in self.traders
                })
            
            return result
            
        finally:
            db.close()
