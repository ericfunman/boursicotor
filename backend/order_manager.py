"""
Order Management System for Live Trading
Handles order placement, tracking, and execution monitoring
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from ib_insync import Stock, MarketOrder, LimitOrder, StopOrder, StopLimitOrder, Order as IBOrder, Trade as IBTrade
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import threading
import signal
import traceback as tb

from backend.models import Order, OrderStatus, Ticker, Strategy, SessionLocal
from backend.config import logger


class OrderManager:
    """Manages live trading orders"""
    
    def __init__(self, ibkr_collector=None):
        """
        Initialize OrderManager
        
        Args:
            ibkr_collector: IBKRCollector instance for order execution
        """
        self.ibkr_collector = ibkr_collector
        self._executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="IBKR_Order")
        self._pending_submissions = {}  # {order_id: Future}
    
    @property
    def db(self):
        """Get a new database session each time (Streamlit-safe)"""
        if not hasattr(self, '_db') or self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def _close_db(self):
        """Close current database session"""
        if hasattr(self, '_db') and self._db is not None:
            self._db.close()
            self._db = None
    
    def create_order(
        self,
        symbol: str,
        action: str,
        quantity: int,
        order_type: str = "MARKET",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        strategy_id: Optional[int] = None,
        notes: Optional[str] = None,
        is_paper_trade: bool = True
    ) -> Optional[Order]:
        """
        Create and place an order
        
        Args:
            symbol: Stock symbol
            action: 'BUY' or 'SELL'
            quantity: Number of shares
            order_type: 'MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT'
            limit_price: Limit price for LIMIT/STOP_LIMIT orders
            stop_price: Stop price for STOP/STOP_LIMIT orders
            strategy_id: Associated strategy ID (optional)
            notes: Additional notes
            is_paper_trade: Whether this is a paper trade
        
        Returns:
            Created Order object or None
        """
        try:
            logger.info(f"=== CREATE ORDER START: {action} {quantity} {symbol} @ {order_type} ===")
            
            # Get ticker from database
            logger.info("Step 1: Querying database for ticker...")
            ticker = self.db.query(Ticker).filter(Ticker.symbol == symbol).first()
            if not ticker:
                logger.error(f"Ticker {symbol} not found in database")
                self._close_db()
                return None
            
            logger.info(f"Step 1 OK: Ticker {symbol} found: ID={ticker.id}, Name={ticker.name}")
            
            # Validate order parameters
            if order_type in ["LIMIT", "STOP_LIMIT"] and limit_price is None:
                logger.error("Limit price required for LIMIT/STOP_LIMIT orders")
                self._close_db()
                return None
            
            if order_type in ["STOP", "STOP_LIMIT"] and stop_price is None:
                logger.error("Stop price required for STOP/STOP_LIMIT orders")
                self._close_db()
                return None
            
            logger.info("Step 2: Validation OK, creating Order object...")
            
            # Create order record in database
            order = Order(
                ticker_id=ticker.id,
                strategy_id=strategy_id,
                action=action,
                order_type=order_type,
                quantity=quantity,
                limit_price=limit_price,
                stop_price=stop_price,
                remaining_quantity=quantity,
                status=OrderStatus.PENDING,
                notes=notes,
                is_paper_trade=is_paper_trade,
                created_at=datetime.now()
            )
            
            logger.info("Step 2 OK: Order object created")
            logger.info("Step 3: Adding order to database...")
            
            self.db.add(order)
            
            logger.info("Step 3a: Committing to database...")
            self.db.commit()
            
            logger.info("Step 3b: Refreshing order from database...")
            self.db.refresh(order)
            
            logger.info(f"Step 3 OK: Order created in DB with ID={order.id}, Status={order.status.value}")
            
            # Place order with IBKR if collector is available - DIRECT CALL (no thread)
            if self.ibkr_collector and self.ibkr_collector.ib.isConnected():
                logger.info(f"Step 4: IBKR connected, submitting order {order.id} DIRECTLY...")
                try:
                    success = self._place_order_with_ibkr(order, ticker)
                    if success:
                        logger.info(f"Step 4 OK: Order {order.id} submitted to IBKR successfully")
                    else:
                        logger.error(f"Step 4 FAILED: Order {order.id} submission failed")
                except Exception as e:
                    logger.error(f"Step 4 EXCEPTION: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    order.status = OrderStatus.ERROR
                    order.status_message = f"Error: {str(e)[:200]}"
                    self.db.commit()
            else:
                logger.warning(f"Step 4 SKIPPED: IBKR not connected - order {order.id} saved locally only")
                order.status_message = "IBKR not connected - order saved locally"
                self.db.commit()
            
            # Capture order details BEFORE closing session to avoid DetachedInstanceError
            order_id = order.id
            order_status = order.status.value
            
            logger.info("Step 5: Closing database session...")
            self._close_db()
            
            logger.info(f"=== CREATE ORDER COMPLETE: Order {order_id}, Status={order_status} ===")
            
            return order
            
        except Exception as e:
            logger.error(f"!!! EXCEPTION in create_order: {e}")
            import traceback
            logger.error(traceback.format_exc())
            try:
                self.db.rollback()
                self._close_db()
            except Exception:
                pass
            return None
    
    def _place_order_with_ibkr(self, order: Order, ticker: Ticker) -> bool:
        """
        Submit order to IBKR
        
        Args:
            order: Order database object
            ticker: Ticker database object
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Step 4a: Creating contract for {ticker.symbol}...")
            
            # Use get_contract() from collector which has proper currency/exchange detection
            # instead of relying on potentially incorrect DB values
            contract = self.ibkr_collector.get_contract(
                symbol=ticker.symbol,
                exchange='SMART',  # Let IBKR auto-route
                currency=None  # Auto-detect: USD first, then EUR
            )
            
            if not contract:
                logger.error(f"Step 4a FAILED: Could not qualify contract for {ticker.symbol}")
                order.status = OrderStatus.ERROR
                order.status_message = f"Could not qualify contract for {ticker.symbol}"
                self.db.commit()
                return False
            
            logger.info(f"Step 4a OK: Contract created: {contract.symbol} on {contract.exchange} (currency: {contract.currency})")
            logger.info("Step 4b: Creating IBKR order object...")
            
            # Create IBKR order object
            ib_order = self._create_ib_order(order)
            
            if not ib_order:
                logger.error("Step 4b FAILED: Could not create IBKR order object")
                order.status = OrderStatus.ERROR
                order.status_message = "Could not create IBKR order"
                self.db.commit()
                return False
            
            logger.info(f"Step 4b OK: IBKR order object created (type={order.order_type})")
            logger.info("Step 4c: Placing order with IBKR...")
            
            # Place order (IBKR will qualify the contract automatically)
            trade = self.ibkr_collector.ib.placeOrder(contract, ib_order)
            
            logger.info(f"Step 4c OK: placeOrder() returned, trade: {trade}")
            logger.info("Step 4e: Updating order with IBKR IDs...")
            
            # Get the actual IBKR orderId from trade object
            # IMPORTANT: trade.order.orderId is assigned by IBKR during placeOrder()
            import time
            time.sleep(0.1)  # Brief wait to ensure orderId is stable
            actual_order_id = trade.order.orderId
            
            # Update order with IBKR IDs
            order.ibkr_order_id = actual_order_id
            order.perm_id = trade.order.permId if hasattr(trade.order, 'permId') else None
            order.status = OrderStatus.SUBMITTED
            order.submitted_at = datetime.now()
            order.status_message = f"Submitted to IBKR (ID: {actual_order_id})"
            
            logger.info(f"Step 4e: IBKR assigned orderId = {actual_order_id}")
            
            logger.info("Step 4e: Committing order update to DB...")
            self.db.commit()
            
            logger.info(f"Step 4 COMPLETE: Order {order.id} submitted to IBKR with ID {actual_order_id}")
            
            # Monitor order execution (non-blocking - in thread)
            logger.info(f"Step 4f: Starting order monitoring in background with orderId={actual_order_id}")
            self._monitor_order_async(order.id, actual_order_id)
            
            return True
            
        except Exception as e:
            logger.error(f"!!! EXCEPTION in _place_order_with_ibkr: {e}")
            import traceback
            logger.error(traceback.format_exc())
            order.status = OrderStatus.ERROR
            order.status_message = str(e)
            try:
                self.db.commit()
            except Exception:
                pass
            return False
    
    def _monitor_order_async(self, order_id: int, ibkr_order_id: int):
        """
        Monitor order execution asynchronously in background thread
        Waits for IBKR events and updates DB when order fills
        
        Args:
            order_id: Our DB Order ID to monitor
            ibkr_order_id: The IBKR order ID (for matching fills)
        """
        def monitor():
            """TODO: Add docstring."""
            try:
                logger.info(f"[Monitor] Starting async monitoring for order {order_id} (IBKR ID: {ibkr_order_id})")
                
                db = SessionLocal()
                
                # Get order from DB
                order = db.query(Order).filter(Order.id == order_id).first()
                if not order:
                    logger.warning(f"[Monitor] Order {order_id} not found in DB")
                    db.close()
                    return
                
                symbol = order.ticker.symbol if order.ticker else "UNKNOWN"
                
                # Wait for order to fill (market orders may take 2-5 seconds for fills to appear in API)
                import time
                time.sleep(5)  # Wait 5 seconds for order to be executed and fills to propagate
                
                # Check if filled in IBKR by verifying portfolio position
                try:
                    logger.info("[Monitor] Verifying fill by checking portfolio position...")
                    positions = self.ibkr_collector.ib.positions()
                    
                    # Find our position
                    our_position = None
                    for position in positions:
                        if position.contract.symbol == symbol:
                            our_position = position
                            break
                    
                    filled = 0
                    avg_price = 0
                    
                    if our_position and int(our_position.position) >= int(order.quantity):
                        # Position confirms the fill!
                        filled = int(order.quantity)
                        logger.info(f"[Monitor] ✅ Position confirmed: {our_position.position} shares of {symbol}")
                        
                        # Try to get average fill price from fills() API
                        try:
                            all_fills = self.ibkr_collector.ib.fills()
                            matching_fills = [
                                f for f in all_fills 
                                if f.contract.symbol == symbol and 
                                   f.execution.orderId == ibkr_order_id
                            ]
                            
                            if matching_fills:
                                total_cost = sum(f.execution.price * f.execution.shares for f in matching_fills)
                                avg_price = total_cost / filled
                                logger.info(f"[Monitor] ✅ Found fill: {filled} shares @ {avg_price:.2f}")
                        except Exception as e:
                            logger.warning(f"[Monitor] Could not get fill price details: {e}")
                            avg_price = 0
                    else:
                        # Fallback to fills() API
                        logger.info("[Monitor] Position too small, trying fills() API")
                        all_fills = self.ibkr_collector.ib.fills()
                    
                        matching_fills = [
                            f for f in all_fills 
                            if f.contract.symbol == symbol and 
                               f.execution.orderId == ibkr_order_id
                        ]
                    
                        if matching_fills:
                            filled = int(sum(f.execution.shares for f in matching_fills))
                            total_cost = sum(f.execution.price * f.execution.shares for f in matching_fills)
                            avg_price = total_cost / filled if filled > 0 else 0
                            
                            logger.info(f"[Monitor] ✅ Found {len(matching_fills)} fills: {filled} shares @ {avg_price:.2f}")
                    
                    # Update DB
                    if filled > 0:
                        order.filled_quantity = filled
                        order.remaining_quantity = max(0, int(order.quantity) - filled)
                        if avg_price > 0:
                            order.avg_fill_price = avg_price
                        
                        if filled >= int(order.quantity):
                            order.status = OrderStatus.FILLED
                            order.status_message = f"Filled at {avg_price:.2f} ({filled} shares)"
                            logger.info(f"[Monitor] ✅ Order {order_id} marked as FILLED in DB")
                        else:
                            order.status = OrderStatus.SUBMITTED
                            order.status_message = f"Partially filled ({filled}/{int(order.quantity)} shares)"
                        
                        db.commit()
                    else:
                        logger.warning(f"[Monitor] No fills found for {symbol}")
                
                except Exception as e:
                    logger.error(f"[Monitor] Error checking fills: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                db.close()
                logger.info(f"[Monitor] Finished monitoring order {order_id}")
                
            except Exception as e:
                logger.error(f"[Monitor] Exception in monitor thread: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        # Start monitoring in background thread
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def _place_order_with_ibkr_async(self, order_id: int, ticker_id: int) -> bool:
        """
        Async wrapper for IBKR order placement - runs in background thread
        Uses a new DB session to avoid conflicts with main thread
        
        Args:
            order_id: Order ID to submit
            ticker_id: Ticker ID for the order
        
        Returns:
            True if successful, False otherwise
        """
        db = SessionLocal()  # New session for this thread
        try:
            logger.info(f"[Thread] Starting IBKR submission for order {order_id}")
            logger.info(f"[Thread] IBKR connected: {self.ibkr_collector.ib.isConnected()}")
            
            # Get order and ticker from DB
            order = db.query(Order).filter(Order.id == order_id).first()
            ticker = db.query(Ticker).filter(Ticker.id == ticker_id).first()
            
            if not order or not ticker:
                logger.error(f"[Thread] Order {order_id} or Ticker {ticker_id} not found in DB")
                return False
            
            logger.info(f"[Thread] Order and Ticker loaded: {ticker.symbol} ({ticker.currency})")
            
            # Check if IBKR is still connected
            if not self.ibkr_collector.ib.isConnected():
                logger.error("[Thread] IBKR not connected!")
                order.status = OrderStatus.ERROR
                order.status_message = "IBKR connection lost"
                db.commit()
                return False
            
            logger.info(f"[Thread] Creating Stock contract for {ticker.symbol}...")
            
            # Use get_contract() which has proper timeout protection (15s)
            # instead of direct qualifyContracts() call that could block indefinitely
            contract = self.ibkr_collector.get_contract(
                symbol=ticker.symbol,
                exchange='SMART',
                currency=None  # Auto-detect: USD first, then EUR
            )
            
            if not contract:
                logger.error(f"[Thread] Could not qualify contract for {ticker.symbol}")
                order.status = OrderStatus.ERROR
                order.status_message = f"Invalid symbol or market closed: {ticker.symbol}"
                db.commit()
                return False
            
            logger.info(f"[Thread] Contract qualified: {contract}")
            
            logger.info("[Thread] Creating IBKR order object...")
            
            # Create IBKR order
            ib_order = self._create_ib_order(order)
            
            logger.info(f"[Thread] IBKR order object creation completed, result: {ib_order is not None}")
            
            if not ib_order:
                logger.error("[Thread] Could not create IBKR order object")
                order.status = OrderStatus.ERROR
                order.status_message = "Could not create IBKR order"
                db.commit()
                return False
            
            logger.info(f"[Thread] IBKR order details: {ib_order}")
            logger.info(f"[Thread] Calling IBKR placeOrder() for order {order_id}...")
            
            # Place order (blocking call, but we're in a background thread)
            trade = self.ibkr_collector.ib.placeOrder(contract, ib_order)
            
            logger.info(f"[Thread] placeOrder() completed for order {order_id}, trade: {trade}")
            
            # Update order with IBKR details
            order.ibkr_order_id = ib_order.orderId
            order.perm_id = ib_order.permId if hasattr(ib_order, 'permId') else None
            order.status = OrderStatus.SUBMITTED
            order.submitted_at = datetime.now()
            order.status_message = f"Submitted to IBKR (ID: {ib_order.orderId})"
            db.commit()
            
            logger.info(f"[Thread] Order {order_id} successfully submitted to IBKR with ID {ib_order.orderId}")
            logger.info("[Thread] Database updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"[Thread] EXCEPTION submitting order {order_id} to IBKR: {e}")
            logger.error(f"[Thread] Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"[Thread] Traceback:\n{traceback.format_exc()}")
            try:
                order = db.query(Order).filter(Order.id == order_id).first()
                if order:
                    order.status = OrderStatus.ERROR
                    order.status_message = f"IBKR error: {str(e)[:200]}"
                    db.commit()
                    logger.error(f"[Thread] Updated order {order_id} status to ERROR in DB")
            except Exception as db_error:
                logger.error(f"[Thread] Could not update DB with error: {db_error}")
            return False
        finally:
            try:
                db.close()
                logger.info(f"[Thread] DB session closed for order {order_id}")
            except Exception as close_error:
                logger.error(f"[Thread] Error closing DB: {close_error}")
    
    def _create_ib_order(self, order: Order) -> Optional[IBOrder]:
        """
        Create IBKR order object from database Order
        
        Args:
            order: Order database object
        
        Returns:
            IBKR Order object or None
        """
        try:
            if order.order_type == "MARKET":
                return MarketOrder(order.action, order.quantity)
            
            elif order.order_type == "LIMIT":
                return LimitOrder(order.action, order.quantity, order.limit_price)
            
            elif order.order_type == "STOP":
                return StopOrder(order.action, order.quantity, order.stop_price)
            
            elif order.order_type == "STOP_LIMIT":
                return StopLimitOrder(
                    order.action,
                    order.quantity,
                    order.limit_price,
                    order.stop_price
                )
            
            else:
                logger.error(f"Unknown order type: {order.order_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating IB order: {e}")
            return None
    
    def check_pending_submissions(self, timeout: float = 0.1) -> Dict[int, str]:
        """
        Check status of pending IBKR submissions
        
        Args:
            timeout: How long to wait for each submission (in seconds)
        
        Returns:
            Dict of {order_id: status} for completed submissions
        """
        completed = {}
        to_remove = []
        
        for order_id, future in self._pending_submissions.items():
            try:
                if future.done():
                    try:
                        result = future.result(timeout=timeout)
                        completed[order_id] = "success" if result else "failed"
                    except Exception as e:
                        logger.error(f"Background submission for order {order_id} failed: {e}")
                        completed[order_id] = "error"
                    to_remove.append(order_id)
            except Exception as e:
                logger.error(f"Error checking submission status for order {order_id}: {e}")
        
        # Clean up completed submissions
        for order_id in to_remove:
            del self._pending_submissions[order_id]
        
        return completed
    
    def update_order_status(self, order_id: int, ib_trade: IBTrade) -> bool:
        """
        Update order status from IBKR trade object
        
        Args:
            order_id: Database order ID
            ib_trade: IBKR trade object
        
        Returns:
            True if successful
        """
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                logger.error(f"Order {order_id} not found")
                return False
            
            # Update status
            status_str = ib_trade.orderStatus.status.upper()
            
            logger.info(f"Updating order {order_id}: IBKR status = {status_str}, filled = {ib_trade.orderStatus.filled}, remaining = {ib_trade.orderStatus.remaining}")
            
            if status_str == "FILLED":
                order.status = OrderStatus.FILLED
                order.filled_quantity = ib_trade.orderStatus.filled
                order.remaining_quantity = ib_trade.orderStatus.remaining
                order.avg_fill_price = ib_trade.orderStatus.avgFillPrice
                order.filled_at = datetime.now()
                logger.info(f"Order {order_id} marked as FILLED")
                
            elif status_str in ["PRESUBMITTED", "SUBMITTED", "PENDINGSUBMIT", "PENDING_SUBMIT"]:
                order.status = OrderStatus.SUBMITTED
                logger.info(f"Order {order_id} marked as SUBMITTED (IBKR status: {status_str})")
                
            elif "CANCEL" in status_str:
                order.status = OrderStatus.CANCELLED
                order.cancelled_at = datetime.now()
                logger.info(f"Order {order_id} marked as CANCELLED")
                
            elif status_str in ["INACTIVE", "PENDING_CANCEL"]:
                order.status = OrderStatus.PENDING
                logger.info(f"Order {order_id} marked as PENDING")
                
            else:
                order.status_message = status_str
                logger.warning(f"Order {order_id} has unknown status: {status_str}")
            
            # Update fill quantities
            order.filled_quantity = ib_trade.orderStatus.filled
            order.remaining_quantity = ib_trade.orderStatus.remaining
            
            if ib_trade.orderStatus.avgFillPrice > 0:
                order.avg_fill_price = ib_trade.orderStatus.avgFillPrice
            
            self.db.commit()
            
            logger.info(f"Order {order_id} status updated to: {order.status.value}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.db.rollback()
            return False
    
    def cancel_order(self, order_id: int) -> bool:
        """
        Cancel an order
        
        Args:
            order_id: Database order ID
        
        Returns:
            True if successful
        """
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                logger.error(f"Order {order_id} not found")
                return False
            
            if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
                logger.warning(f"Cannot cancel order {order_id} - status: {order.status.value}")
                return False
            
            # Cancel with IBKR if submitted
            if order.ibkr_order_id and self.ibkr_collector and self.ibkr_collector.connected:
                # Find the trade
                open_orders = self.ibkr_collector.ib.openOrders()
                for trade in open_orders:
                    if trade.order.orderId == order.ibkr_order_id:
                        self.ibkr_collector.ib.cancelOrder(trade.order)
                        logger.info(f"Cancelled IBKR order {order.ibkr_order_id}")
                        break
            
            # Update database
            order.status = OrderStatus.CANCELLED
            order.cancelled_at = datetime.now()
            order.status_message = "Cancelled by user"
            
            self.db.commit()
            
            logger.info(f"Order {order_id} cancelled")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            self.db.rollback()
            return False
    
    def cancel_multiple_orders(self, order_ids: List[int]) -> Dict[int, bool]:
        """
        Cancel multiple orders at once
        
        Args:
            order_ids: List of order IDs to cancel
        
        Returns:
            Dictionary {order_id: success} for each order
        """
        results = {}
        
        for order_id in order_ids:
            try:
                success = self.cancel_order(order_id)
                results[order_id] = success
            except Exception as e:
                logger.error(f"Error cancelling order {order_id}: {e}")
                results[order_id] = False
        
        return results
    
    def cancel_all_orders(self, status_filter: Optional[OrderStatus] = None) -> Dict[str, int]:
        """
        Cancel all orders (optionally filtered by status)
        
        Args:
            status_filter: Only cancel orders with this status (None = all cancellable orders)
        
        Returns:
            Dictionary with 'cancelled' and 'failed' counts
        """
        try:
            # Get all cancellable orders
            query = self.db.query(Order).filter(
                Order.status.in_([OrderStatus.PENDING, OrderStatus.SUBMITTED])
            )
            
            if status_filter:
                query = query.filter(Order.status == status_filter)
            
            orders = query.all()
            
            cancelled = 0
            failed = 0
            
            for order in orders:
                if self.cancel_order(order.id):
                    cancelled += 1
                else:
                    failed += 1
            
            logger.info(f"Cancelled {cancelled} orders, {failed} failed")
            
            return {'cancelled': cancelled, 'failed': failed}
            
        except Exception as e:
            logger.error(f"Error in cancel_all_orders: {e}")
            return {'cancelled': 0, 'failed': 0}
    
    def get_order(self, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        return self.db.query(Order).filter(Order.id == order_id).first()
    
    def get_orders(
        self,
        ticker_symbol: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        limit: int = 100
    ) -> List[Order]:
        """
        Get orders with optional filters
        
        Args:
            ticker_symbol: Filter by ticker symbol
            status: Filter by order status
            limit: Maximum number of orders to return
        
        Returns:
            List of Order objects
        """
        try:
            query = self.db.query(Order).join(Ticker)
            
            if ticker_symbol:
                query = query.filter(Ticker.symbol == ticker_symbol)
            
            if status:
                query = query.filter(Order.status == status)
            
            orders = query.order_by(Order.created_at.desc()).limit(limit).all()
            
            return orders
            
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []
    
    def get_order_statistics(self, ticker_symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get order statistics
        
        Args:
            ticker_symbol: Optional ticker to filter by
        
        Returns:
            Dictionary with statistics
        """
        try:
            query = self.db.query(Order)
            
            if ticker_symbol:
                query = query.join(Ticker).filter(Ticker.symbol == ticker_symbol)
            
            total_orders = query.count()
            filled_orders = query.filter(Order.status == OrderStatus.FILLED).count()
            cancelled_orders = query.filter(Order.status == OrderStatus.CANCELLED).count()
            pending_orders = query.filter(Order.status.in_([OrderStatus.PENDING, OrderStatus.SUBMITTED])).count()
            
            # Calculate total volume and commission
            filled = query.filter(Order.status == OrderStatus.FILLED).all()
            total_volume = sum(o.filled_quantity * o.avg_fill_price for o in filled if o.avg_fill_price)
            total_commission = sum(o.commission for o in filled if o.commission)
            
            return {
                'total_orders': total_orders,
                'filled': filled_orders,
                'cancelled': cancelled_orders,
                'pending': pending_orders,
                'total_volume': total_volume,
                'total_commission': total_commission,
                'fill_rate': (filled_orders / total_orders * 100) if total_orders > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting order statistics: {e}")
            return {}
    
    def sync_with_ibkr(self) -> int:
        """
        Sync order status with IBKR
        Updates all pending/submitted orders with current status from IBKR
        
        Returns:
            Number of orders updated
        """
        if not self.ibkr_collector or not self.ibkr_collector.ib.isConnected():
            logger.warning("Cannot sync - IBKR not connected")
            return 0
        
        try:
            updated_count = 0
            
            # Get ALL trades from IBKR (including filled/cancelled)
            ib_trades = self.ibkr_collector.ib.trades()
            
            logger.info(f"Found {len(ib_trades)} total trades in IBKR")
            
            # Log all IBKR order IDs for debugging
            if ib_trades:
                ibkr_order_ids = [t.order.orderId for t in ib_trades]
                logger.info(f"IBKR order IDs: {ibkr_order_ids}")
                # Log details of each IBKR trade
                for t in ib_trades:
                    # Calculate filled quantity from fills/executions
                    filled_qty = sum(f.execution.shares for f in t.fills) if t.fills else 0
                    qty = t.order.totalQuantity if t.order.totalQuantity > 0 else filled_qty
                    logger.info(f"  IBKR trade: ID={t.order.orderId}, {t.contract.symbol} {t.order.action} qty={qty} (total={t.order.totalQuantity}, filled={t.orderStatus.filled if hasattr(t.orderStatus, 'filled') else 'N/A'}, from_fills={filled_qty}), status={t.orderStatus.status}")
            
            # Get pending/submitted orders from database
            pending_orders = self.db.query(Order).filter(
                Order.status.in_([OrderStatus.PENDING, OrderStatus.SUBMITTED])
            ).all()
            
            logger.info(f"Found {len(pending_orders)} pending/submitted orders in DB")
            
            # Track which IBKR trades have been matched to avoid duplicates
            matched_ibkr_ids = set()
            
            for order in pending_orders:
                logger.info(f"Processing DB order {order.id}: {order.action} {order.quantity} {order.ticker.symbol if order.ticker else 'N/A'}, created: {order.created_at}")
                
                if not order.ibkr_order_id:
                    logger.info(f"Order {order.id} has no IBKR ID, skipping")
                    continue
                
                # Find matching IBKR trade
                # Try multiple matching strategies:
                # 1. Match by IBKR order ID (primary)
                # 2. Match by symbol + action + quantity + time proximity (fallback if ID changed)
                found = False
                
                for ib_trade in ib_trades:
                    ib_symbol = ib_trade.contract.symbol
                    ib_action = ib_trade.order.action
                    # For filled orders, totalQuantity may be 0, use filled quantity from fills/executions
                    ib_quantity = ib_trade.order.totalQuantity
                    if ib_quantity == 0:
                        # Try orderStatus.filled first
                        if hasattr(ib_trade.orderStatus, 'filled') and ib_trade.orderStatus.filled > 0:
                            ib_quantity = ib_trade.orderStatus.filled
                        # If still 0, calculate from fills/executions
                        elif ib_trade.fills:
                            ib_quantity = sum(f.execution.shares for f in ib_trade.fills)
                    ib_order_id = ib_trade.order.orderId
                    
                    # Skip if this IBKR trade was already matched
                    if ib_order_id in matched_ibkr_ids:
                        continue
                    
                    # Strategy 1: Match by IBKR order ID
                    if ib_order_id == order.ibkr_order_id:
                        logger.info(f"✓ Matched by ID! Order {order.id} (created {order.created_at}) <-> IBKR {ib_order_id}, status: {ib_trade.orderStatus.status}")
                        matched_ibkr_ids.add(ib_order_id)
                        self.update_order_status(order.id, ib_trade)
                        updated_count += 1
                        found = True
                        break
                    
                    # Strategy 2: Match by symbol + action + quantity (for reconnections where ID changed)
                    # Only match if not already matched to prevent duplicates
                    if (order.ticker and 
                        ib_symbol == order.ticker.symbol and 
                        ib_action == order.action and 
                        ib_quantity == order.quantity):
                        logger.info(f"✓ Matched by details! Order {order.id} (created {order.created_at}) <-> IBKR {ib_order_id} ({ib_symbol} {ib_action} {ib_quantity}), status: {ib_trade.orderStatus.status}")
                        # Update the IBKR order ID in our database
                        old_id = order.ibkr_order_id
                        order.ibkr_order_id = ib_order_id
                        self.db.commit()
                        logger.info(f"Updated IBKR order ID from {old_id} to {ib_order_id}")
                        matched_ibkr_ids.add(ib_order_id)
                        self.update_order_status(order.id, ib_trade)
                        updated_count += 1
                        found = True
                        break
                
                if not found:
                    logger.warning(f"✗ No matching IBKR trade found for order {order.id} (IBKR ID: {order.ibkr_order_id}, {order.action} {order.quantity} {order.ticker.symbol if order.ticker else 'N/A'})")
            
            logger.info(f"Synced {updated_count} orders with IBKR")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Error syncing with IBKR: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions from IBKR
        
        Returns:
            List of position dictionaries with symbol, quantity, avg_cost, market_value, etc.
        """
        if not self.ibkr_collector or not self.ibkr_collector.ib.isConnected():
            logger.warning("Cannot get positions - IBKR not connected")
            return []
        
        try:
            positions = []
            ib_positions = self.ibkr_collector.ib.positions()
            
            logger.info(f"Found {len(ib_positions)} positions in IBKR")
            
            for pos in ib_positions:
                positions.append({
                    'symbol': pos.contract.symbol,
                    'exchange': pos.contract.exchange,
                    'currency': pos.contract.currency,
                    'position': pos.position,
                    'avg_cost': pos.avgCost,
                    'market_price': pos.marketPrice if hasattr(pos, 'marketPrice') else None,
                    'market_value': pos.marketValue if hasattr(pos, 'marketValue') else None,
                    'unrealized_pnl': pos.unrealizedPNL if hasattr(pos, 'unrealizedPNL') else None,
                    'realized_pnl': pos.realizedPNL if hasattr(pos, 'realizedPNL') else None,
                })
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting positions from IBKR: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
