"""
Interactive Brokers connection and API wrapper
"""
from ib_insync import IB, Stock, util
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from backend.config import IBKR_CONFIG, logger
import asyncio


class IBKRClient:
    """Interactive Brokers API Client"""
    
    def __init__(self):
        self.ib = IB()
        self.connected = False
        self.host = IBKR_CONFIG["host"]
        self.port = IBKR_CONFIG["port"]
        self.client_id = IBKR_CONFIG["client_id"]
        
    def connect(self) -> bool:
        """Connect to Interactive Brokers"""
        try:
            self.ib.connect(
                host=self.host,
                port=self.port,
                clientId=self.client_id,
                timeout=20
            )
            self.connected = True
            logger.info(f"Connected to IBKR at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from Interactive Brokers"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR")
    
    def get_contract(self, symbol: str, exchange: str = "SBF", currency: str = "EUR") -> Stock:
        """
        Get stock contract for a ticker
        
        Args:
            symbol: Stock symbol (e.g., 'TTE', 'WLN')
            exchange: Exchange code (SBF for Euronext Paris)
            currency: Currency code
            
        Returns:
            Stock contract
        """
        contract = Stock(symbol, exchange, currency)
        self.ib.qualifyContracts(contract)
        return contract
    
    def get_historical_data(
        self,
        symbol: str,
        duration: str = "1 D",
        bar_size: str = "1 min",
        what_to_show: str = "TRADES",
        exchange: str = "SBF",
        currency: str = "EUR"
    ) -> List[Dict]:
        """
        Fetch historical data from IBKR
        
        Args:
            symbol: Stock symbol
            duration: Duration string (e.g., '1 D', '1 W', '1 M', '1 Y')
            bar_size: Bar size (e.g., '1 secs', '5 secs', '1 min', '5 mins', '1 hour', '1 day')
            what_to_show: Data type ('TRADES', 'MIDPOINT', 'BID', 'ASK')
            exchange: Exchange code
            currency: Currency code
            
        Returns:
            List of historical bars as dictionaries
        """
        try:
            if not self.connected:
                self.connect()
            
            contract = self.get_contract(symbol, exchange, currency)
            
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow=what_to_show,
                useRTH=True,  # Regular Trading Hours only
                formatDate=1
            )
            
            # Convert to list of dictionaries
            data = []
            for bar in bars:
                data.append({
                    'timestamp': bar.date,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume,
                })
            
            logger.info(f"Fetched {len(data)} bars for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return []
    
    def stream_realtime_data(self, symbol: str, callback, exchange: str = "SBF", currency: str = "EUR"):
        """
        Stream real-time data for a symbol
        
        Args:
            symbol: Stock symbol
            callback: Function to call with each new bar
            exchange: Exchange code
            currency: Currency code
        """
        try:
            if not self.connected:
                self.connect()
            
            contract = self.get_contract(symbol, exchange, currency)
            
            # Request real-time bars (5 seconds minimum)
            self.ib.reqRealTimeBars(
                contract,
                5,  # 5 seconds
                'TRADES',
                False
            )
            
            def on_bar_update(bars, has_new_bar):
                if has_new_bar:
                    bar = bars[-1]
                    data = {
                        'timestamp': bar.time,
                        'open': bar.open,
                        'high': bar.high,
                        'low': bar.low,
                        'close': bar.close,
                        'volume': bar.volume,
                    }
                    callback(data)
            
            bars = self.ib.reqRealTimeBars(contract, 5, 'TRADES', False)
            bars.updateEvent += on_bar_update
            
            logger.info(f"Started streaming real-time data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error streaming real-time data for {symbol}: {e}")
    
    def place_order(
        self,
        symbol: str,
        action: str,
        quantity: int,
        order_type: str = "MKT",
        limit_price: Optional[float] = None,
        exchange: str = "SBF",
        currency: str = "EUR"
    ) -> Optional[Dict]:
        """
        Place an order
        
        Args:
            symbol: Stock symbol
            action: 'BUY' or 'SELL'
            quantity: Number of shares
            order_type: 'MKT' (market), 'LMT' (limit), 'STP' (stop)
            limit_price: Limit price (for limit orders)
            exchange: Exchange code
            currency: Currency code
            
        Returns:
            Order details if successful
        """
        try:
            if not self.connected:
                self.connect()
            
            contract = self.get_contract(symbol, exchange, currency)
            
            from ib_insync import MarketOrder, LimitOrder
            
            if order_type == "MKT":
                order = MarketOrder(action, quantity)
            elif order_type == "LMT" and limit_price:
                order = LimitOrder(action, quantity, limit_price)
            else:
                logger.error(f"Unsupported order type: {order_type}")
                return None
            
            trade = self.ib.placeOrder(contract, order)
            logger.info(f"Placed {action} order for {quantity} shares of {symbol}")
            
            return {
                'order_id': trade.order.orderId,
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'order_type': order_type,
                'status': trade.orderStatus.status,
            }
            
        except Exception as e:
            logger.error(f"Error placing order for {symbol}: {e}")
            return None
    
    def get_account_summary(self) -> Dict:
        """Get account summary"""
        try:
            if not self.connected:
                self.connect()
            
            account_values = self.ib.accountSummary()
            
            summary = {}
            for item in account_values:
                summary[item.tag] = {
                    'value': item.value,
                    'currency': item.currency
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            return {}
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        try:
            if not self.connected:
                self.connect()
            
            positions = self.ib.positions()
            
            position_list = []
            for pos in positions:
                position_list.append({
                    'symbol': pos.contract.symbol,
                    'quantity': pos.position,
                    'avg_cost': pos.avgCost,
                    'market_value': pos.position * pos.marketPrice if hasattr(pos, 'marketPrice') else None,
                })
            
            return position_list
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []


# Singleton instance
ibkr_client = IBKRClient()


if __name__ == "__main__":
    # Test connection
    client = IBKRClient()
    if client.connect():
        print("Connected successfully!")
        
        # Test fetching historical data
        data = client.get_historical_data("TTE", duration="1 D", bar_size="1 min")
        print(f"Fetched {len(data)} bars")
        if data:
            print(f"Latest bar: {data[-1]}")
        
        client.disconnect()
