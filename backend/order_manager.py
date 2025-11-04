"""
Order Management System for Live Trading
Handles order placement, tracking, and execution monitoring
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from ib_insync import Stock, MarketOrder, LimitOrder, StopOrder, StopLimitOrder, Order as IBOrder, Trade as IBTrade

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
                created_at=datetime.utcnow()
            )
            
            logger.info("Step 2 OK: Order object created")
            logger.info("Step 3: Adding order to database...")
            
            self.db.add(order)
            
            logger.info("Step 3a: Committing to database...")
            self.db.commit()
            
            logger.info("Step 3b: Refreshing order from database...")
            self.db.refresh(order)
            
            logger.info(f"Step 3 OK: Order created in DB with ID={order.id}, Status={order.status.value}")
            
            # Place order with IBKR if collector is available
            # TEMPORARY: Skip IBKR to test if that's blocking
            logger.warning(f"Step 4 SKIPPED (TEMPORARY): Not placing order with IBKR for testing")
            order.status_message = "IBKR submission temporarily disabled for debugging"
            self.db.commit()
            
            # Commented out for debugging
            # if self.ibkr_collector and self.ibkr_collector.connected:
            #     logger.info(f"Step 4: IBKR is connected, placing order {order.id}...")
            #     success = self._place_order_with_ibkr(order, ticker)
            #     if not success:
            #         logger.error(f"Step 4 FAILED: Could not place order {order.id} with IBKR")
            #         order.status = OrderStatus.ERROR
            #         order.status_message = "Failed to submit to IBKR"
            #         self.db.commit()
            #     else:
            #         logger.info(f"Step 4 OK: Order {order.id} placed with IBKR")
            # else:
            #     logger.warning(f"Step 4 SKIPPED: IBKR not connected - order {order.id} saved locally only")
            #     order.status_message = "IBKR not connected"
            #     self.db.commit()
            
            # Capture order details BEFORE closing session to avoid DetachedInstanceError
            order_id = order.id
            order_status = order.status.value
            
            logger.info(f"Step 5: Closing database session...")
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
            except:
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
            logger.info(f"Step 4a: Getting contract for {ticker.symbol}...")
            # Get contract
            contract = self.ibkr_collector.get_contract(
                ticker.symbol,
                exchange='SMART',
                currency=ticker.currency
            )
            
            if not contract:
                logger.error(f"Step 4a FAILED: Could not get contract for {ticker.symbol}")
                return False
            
            logger.info(f"Step 4a OK: Contract obtained for {ticker.symbol}")
            logger.info(f"Step 4b: Creating IBKR order object...")
            
            # Create IBKR order object
            ib_order = self._create_ib_order(order)
            
            if not ib_order:
                logger.error("Step 4b FAILED: Could not create IBKR order object")
                return False
            
            logger.info(f"Step 4b OK: IBKR order object created (type={order.order_type})")
            logger.info(f"Step 4c: Placing order with IBKR...")
            
            # Place order - THIS CAN BLOCK!
            trade = self.ibkr_collector.ib.placeOrder(contract, ib_order)
            
            logger.info(f"Step 4c OK: placeOrder() returned, trade object received")
            logger.info(f"Step 4d: Updating order with IBKR IDs...")
            
            # Update order with IBKR IDs
            order.ibkr_order_id = ib_order.orderId
            order.perm_id = ib_order.permId if hasattr(ib_order, 'permId') else None
            order.status = OrderStatus.SUBMITTED
            order.submitted_at = datetime.utcnow()
            order.status_message = "Submitted to IBKR"
            
            logger.info(f"Step 4e: Committing order update to DB...")
            self.db.commit()
            
            logger.info(f"Step 4 COMPLETE: Order {order.id} submitted to IBKR with ID {ib_order.orderId}")
            
            return True
            
        except Exception as e:
            logger.error(f"!!! EXCEPTION in _place_order_with_ibkr: {e}")
            import traceback
            logger.error(traceback.format_exc())
            order.status = OrderStatus.ERROR
            order.status_message = str(e)
            try:
                self.db.commit()
            except:
                pass
            return False
            # Place order
            trade = self.ibkr_collector.ib.placeOrder(contract, ib_order)
            
            # Update order with IBKR IDs
            order.ibkr_order_id = ib_order.orderId
            order.perm_id = ib_order.permId if hasattr(ib_order, 'permId') else None
            order.status = OrderStatus.SUBMITTED
            order.submitted_at = datetime.utcnow()
            order.status_message = "Submitted to IBKR"
            
            self.db.commit()
            
            logger.info(f"Order {order.id} submitted to IBKR with ID {ib_order.orderId}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error placing order with IBKR: {e}")
            order.status = OrderStatus.ERROR
            order.status_message = str(e)
            self.db.commit()
            return False
    
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
            
            if status_str == "FILLED":
                order.status = OrderStatus.FILLED
                order.filled_quantity = ib_trade.orderStatus.filled
                order.remaining_quantity = ib_trade.orderStatus.remaining
                order.avg_fill_price = ib_trade.orderStatus.avgFillPrice
                order.filled_at = datetime.utcnow()
                
            elif status_str in ["PRESUBMITTED", "SUBMITTED"]:
                order.status = OrderStatus.SUBMITTED
                
            elif "CANCEL" in status_str:
                order.status = OrderStatus.CANCELLED
                order.cancelled_at = datetime.utcnow()
                
            elif status_str in ["INACTIVE", "PENDING_CANCEL", "PENDING_SUBMIT"]:
                order.status = OrderStatus.PENDING
                
            else:
                order.status_message = status_str
            
            # Update fill quantities
            order.filled_quantity = ib_trade.orderStatus.filled
            order.remaining_quantity = ib_trade.orderStatus.remaining
            
            if ib_trade.orderStatus.avgFillPrice > 0:
                order.avg_fill_price = ib_trade.orderStatus.avgFillPrice
            
            self.db.commit()
            
            logger.info(f"Order {order_id} status updated: {order.status.value}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
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
            order.cancelled_at = datetime.utcnow()
            order.status_message = "Cancelled by user"
            
            self.db.commit()
            
            logger.info(f"Order {order_id} cancelled")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            self.db.rollback()
            return False
    
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
        if not self.ibkr_collector or not self.ibkr_collector.connected:
            logger.warning("Cannot sync - IBKR not connected")
            return 0
        
        try:
            updated_count = 0
            
            # Get all open orders from IBKR
            ib_trades = self.ibkr_collector.ib.openTrades()
            
            # Get pending/submitted orders from database
            pending_orders = self.db.query(Order).filter(
                Order.status.in_([OrderStatus.PENDING, OrderStatus.SUBMITTED])
            ).all()
            
            for order in pending_orders:
                if not order.ibkr_order_id:
                    continue
                
                # Find matching IBKR trade
                for ib_trade in ib_trades:
                    if ib_trade.order.orderId == order.ibkr_order_id:
                        self.update_order_status(order.id, ib_trade)
                        updated_count += 1
                        break
            
            logger.info(f"Synced {updated_count} orders with IBKR")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Error syncing with IBKR: {e}")
            return 0
