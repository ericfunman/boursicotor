"""
Saxo Bank API client for market data and trading
"""
import requests
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import pandas as pd
from backend.config import logger


class SaxoClient:
    """Saxo Bank API client"""

    def __init__(self):
        # Load from environment variables
        self.base_url = os.getenv("SAXO_BASE_URL", "https://gateway.saxobank.com/sim/openapi")
        self.auth_url = os.getenv("SAXO_AUTH_URL", "https://sim.logonvalidation.net/authorize")
        self.token_url = os.getenv("SAXO_TOKEN_URL", "https://sim.logonvalidation.net/token")
        self.app_key = os.getenv("SAXO_APP_KEY", "")
        self.app_secret = os.getenv("SAXO_APP_SECRET", "")
        self.redirect_uri = os.getenv("SAXO_REDIRECT_URI", "http://localhost:8501/callback")
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.connected = False
        
        logger.info(f"Saxo Client initialized with URL: {self.base_url}")
        logger.info(f"App Key: {self.app_key[:8]}..." if self.app_key else "App Key: NOT SET")

    def refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token
        
        Returns:
            bool: True if refresh successful
        """
        try:
            if not self.refresh_token:
                logger.error("❌ No refresh token available")
                return False
            
            logger.info("🔄 Refreshing access token...")
            
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.app_key,
                'client_secret': self.app_secret
            }
            
            response = requests.post(self.token_url, data=data, timeout=30)
            
            if response.status_code in [200, 201]:
                tokens = response.json()
                self.access_token = tokens.get('access_token')
                
                # Update refresh token if provided
                new_refresh_token = tokens.get('refresh_token')
                if new_refresh_token:
                    self.refresh_token = new_refresh_token
                
                # Calculate expiration time
                expires_in = tokens.get('expires_in', 1200)  # Default 20 minutes
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                self.connected = True
                logger.info(f"✅ Access token refreshed (expires in {expires_in}s)")
                
                # Save updated tokens
                self._save_tokens(expires_in)
                
                return True
            else:
                logger.error(f"❌ Token refresh failed: {response.status_code} - {response.text}")
                self.connected = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Error refreshing token: {e}")
            self.connected = False
            return False
    
    def _save_tokens(self, expires_in: int = 1200):
        """Save tokens to file"""
        try:
            with open('.saxo_tokens', 'w') as f:
                f.write(f"ACCESS_TOKEN={self.access_token}\n")
                f.write(f"REFRESH_TOKEN={self.refresh_token}\n")
                f.write(f"EXPIRES_IN={expires_in}\n")
                f.write(f"EXPIRES_AT={self.token_expires_at.isoformat() if self.token_expires_at else ''}\n")
            logger.debug("💾 Tokens saved to file")
        except Exception as e:
            logger.warning(f"⚠️ Could not save tokens: {e}")
    
    def _load_tokens(self) -> bool:
        """Load tokens from file"""
        try:
            with open('.saxo_tokens', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        if key == 'ACCESS_TOKEN':
                            self.access_token = value
                        elif key == 'REFRESH_TOKEN':
                            self.refresh_token = value
                        elif key == 'EXPIRES_AT' and value:
                            try:
                                self.token_expires_at = datetime.fromisoformat(value)
                            except:
                                pass
            
            if self.access_token and self.refresh_token:
                self.connected = True
                logger.info("✅ Tokens loaded from file")
                
                # Check if token needs refresh
                if self.token_expires_at and datetime.now() >= self.token_expires_at - timedelta(minutes=5):
                    logger.info("⏰ Token expiring soon, refreshing...")
                    return self.refresh_access_token()
                
                return True
            return False
            
        except FileNotFoundError:
            logger.debug("No token file found")
            return False
        except Exception as e:
            logger.warning(f"⚠️ Error loading tokens: {e}")
            return False
    
    def ensure_authenticated(self) -> bool:
        """
        Ensure we have a valid access token, refresh if needed
        
        Returns:
            bool: True if authenticated
        """
        # If not connected, try to load tokens
        if not self.connected:
            if not self._load_tokens():
                logger.warning("⚠️ Not authenticated. Run: python authenticate_saxo.py")
                return False
        
        # Check if token is expiring soon (less than 5 minutes)
        if self.token_expires_at:
            time_until_expiry = self.token_expires_at - datetime.now()
            if time_until_expiry.total_seconds() < 300:  # 5 minutes
                logger.info("⏰ Token expiring soon, refreshing...")
                return self.refresh_access_token()
        
        return True

    def authenticate(self, authorization_code: Optional[str] = None) -> bool:
        """
        Authenticate with Saxo Bank API using OAuth2 Authorization Code flow
        
        Args:
            authorization_code: Authorization code from OAuth2 callback (optional for first time)
        
        Returns:
            bool: True if authentication successful
        """
        try:
            if not self.app_key or not self.app_secret:
                logger.error("❌ Saxo Bank App Key or App Secret not configured")
                return False

            # If we have an authorization code, exchange it for tokens
            if authorization_code:
                logger.info("Exchanging authorization code for access token...")
                
                data = {
                    'grant_type': 'authorization_code',
                    'code': authorization_code,
                    'redirect_uri': self.redirect_uri,
                    'client_id': self.app_key,
                    'client_secret': self.app_secret
                }
                
                response = requests.post(self.token_url, data=data, timeout=30)
                
                if response.status_code == 200:
                    tokens = response.json()
                    self.access_token = tokens.get('access_token')
                    self.refresh_token = tokens.get('refresh_token')
                    self.connected = True
                    logger.info("✅ Saxo Bank authentication successful")
                    return True
                else:
                    logger.error(f"❌ Token exchange failed: {response.status_code} - {response.text}")
                    return False
            
            # If no authorization code, return authorization URL
            else:
                auth_params = {
                    'response_type': 'code',
                    'client_id': self.app_key,
                    'redirect_uri': self.redirect_uri,
                    'state': 'random_state_string'  # Should be random in production
                }
                
                auth_url = f"{self.auth_url}?{'&'.join([f'{k}={v}' for k, v in auth_params.items()])}"
                logger.info(f"🔗 Authorization URL: {auth_url}")
                logger.warning("⚠️ Please visit the URL above to authorize the application")
                return False

        except Exception as e:
            logger.error(f"❌ Saxo Bank authentication failed: {e}")
            self.connected = False
            return False

    def connect(self) -> bool:
        """Connect to Saxo Bank"""
        return self.authenticate()

    def get_instrument_uic(self, symbol: str) -> Optional[int]:
        """
        Get the UIC (Unique Instrument Code) for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'TTE')
        
        Returns:
            int: UIC or None if not found
        """
        if not self.ensure_authenticated():
            logger.error("❌ Not authenticated to Saxo Bank")
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'Keywords': symbol,
                'AssetTypes': 'Stock',
                'limit': 10
            }
            
            response = requests.get(
                f"{self.base_url}/ref/v1/instruments",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                instruments = response.json()
                data = instruments.get('Data', [])
                
                if len(data) > 0:
                    # Préférer l'exchange Euronext Paris pour les actions françaises
                    for inst in data:
                        if inst.get('ExchangeId') == 'PAR':
                            uic = inst.get('Identifier')
                            logger.info(f"✅ UIC trouvé pour {symbol}: {uic} ({inst.get('Description')})")
                            return uic
                    
                    # Sinon prendre le premier
                    uic = data[0].get('Identifier')
                    logger.info(f"✅ UIC trouvé pour {symbol}: {uic} ({data[0].get('Description')})")
                    return uic
                else:
                    logger.warning(f"⚠️ Aucun instrument trouvé pour {symbol}")
                    return None
            else:
                logger.error(f"❌ Erreur recherche instrument: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur get_instrument_uic: {e}")
            return None

    def get_historical_data(self, symbol: str, duration: str = "1D", bar_size: str = "1min",
                           exchange: str = "EURONEXT") -> Optional[pd.DataFrame]:
        """
        Fetch historical data from Saxo Bank

        Args:
            symbol: Trading symbol (e.g., 'TTE')
            duration: Duration string (e.g., '1D', '5D', '1M')
            bar_size: Bar size (e.g., '1min', '5min', '1hour', '1day')
            exchange: Exchange code

        Returns:
            DataFrame with OHLCV data or None if failed
        """
        # Ensure we have a valid token
        if not self.ensure_authenticated():
            logger.error("❌ Not authenticated to Saxo Bank")
            return None

        try:
            # Get UIC for the symbol
            uic = self.get_instrument_uic(symbol)
            if not uic:
                logger.error(f"❌ Impossible de trouver l'UIC pour {symbol}")
                return None

            # Parse bar size to Horizon (in seconds)
            horizon = self._parse_bar_size(bar_size)
            
            # Parse duration to Count
            count = self._parse_duration_to_count(duration, bar_size)

            # Build API URL - Try different endpoints
            # First try: GET method with query params
            url = f"{self.base_url}/chart/v1/charts"

            params = {
                'AssetType': 'Stock',
                'Uic': uic,
                'Horizon': horizon,
                'Count': count,
                'Mode': 'From',
                'Time': datetime.now().isoformat()
            }

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            logger.info(f"📊 Fetching {symbol} (UIC: {uic}): {duration}, {bar_size} (Horizon: {horizon}, Count: {count})")

            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            # If GET fails, try POST
            if response.status_code == 404:
                logger.debug("GET failed, trying POST...")
                body = {
                    'Arguments': {
                        'AssetType': 'Stock',
                        'Uic': uic,
                        'Horizon': horizon,
                        'Count': count
                    }
                }
                response = requests.post(url, json=body, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Données reçues pour {symbol}")
                return self._parse_historical_data(data, symbol)
            else:
                logger.warning(f"⚠️ Chart API not available (Status: {response.status_code})")
                logger.info(f"📊 Using simulated historical data for {symbol}")
                
                # Fallback: Get current price and generate historical data
                return self._generate_simulated_historical_data(symbol, uic, count, bar_size)

        except Exception as e:
            logger.error(f"❌ Error fetching Saxo data for {symbol}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None

    def _convert_symbol_format(self, symbol: str, exchange: str) -> str:
        """Convert symbol to Saxo Bank format"""
        # Saxo Bank uses UIC (Unique Instrument Code) format
        # For simulation, we'll use a mapping
        symbol_map = {
            'TTE': '15766',  # TotalEnergies UIC
            'WLN': '15945',  # Worldline UIC
            'MC': '15875',   # LVMH UIC
            'OR': '15878',   # L'Oréal UIC
            'AIR': '15792',  # Airbus UIC
            'SAN': '15880',  # Sanofi UIC
            'BNP': '15770',  # BNP Paribas UIC
            'SU': '15885',   # Schneider Electric UIC
        }

        return symbol_map.get(symbol, symbol)

    def _parse_duration(self, duration: str) -> tuple:
        """Parse duration string to Saxo format"""
        # Default to 1 day
        count = 1
        unit = 'Day'

        if 'D' in duration:
            count = int(duration.replace('D', '').strip() or '1')
            unit = 'Day'
        elif 'W' in duration:
            count = int(duration.replace('W', '').strip() or '1')
            unit = 'Week'
        elif 'M' in duration:
            count = int(duration.replace('M', '').strip() or '1')
            unit = 'Month'

        return count, unit

    def _parse_duration_to_count(self, duration: str, bar_size: str) -> int:
        """
        Convert duration string to number of bars
        
        Args:
            duration: Duration string (e.g., '1D', '5D', '1M')
            bar_size: Bar size (e.g., '1min', '1hour', '1day')
        
        Returns:
            int: Number of bars to request
        """
        # Extract duration value and unit
        duration_value = 1
        duration_unit = 'D'
        
        if 'D' in duration:
            duration_value = int(duration.replace('D', '').strip() or '1')
            duration_unit = 'D'
        elif 'W' in duration:
            duration_value = int(duration.replace('W', '').strip() or '1')
            duration_unit = 'W'
        elif 'M' in duration:
            duration_value = int(duration.replace('M', '').strip() or '1')
            duration_unit = 'M'
        elif 'Y' in duration:
            duration_value = int(duration.replace('Y', '').strip() or '1')
            duration_unit = 'Y'
        
        # Calculate total minutes in duration
        duration_minutes = {
            'D': duration_value * 24 * 60,
            'W': duration_value * 7 * 24 * 60,
            'M': duration_value * 30 * 24 * 60,
            'Y': duration_value * 365 * 24 * 60
        }.get(duration_unit, 24 * 60)
        
        # Calculate bar size in minutes
        bar_minutes = {
            '1min': 1,
            '5min': 5,
            '15min': 15,
            '30min': 30,
            '1hour': 60,
            '4hour': 240,
            '1day': 1440
        }.get(bar_size, 60)
        
        # Calculate count (limit to max 1200 for most Saxo endpoints)
        # Note: This is a Saxo Bank API limitation, not configurable
        # Attempting to request more than 1200 bars will result in API errors
        count = min(int(duration_minutes / bar_minutes), 1200)
        
        return max(count, 10)  # Minimum 10 bars

    def _parse_bar_size(self, bar_size: str) -> int:
        """Convert bar size to Saxo horizon"""
        # Saxo uses horizon codes
        horizon_map = {
            '1min': 60,      # 1 minute
            '5min': 300,     # 5 minutes
            '15min': 900,    # 15 minutes
            '30min': 1800,   # 30 minutes
            '1hour': 3600,   # 1 hour
            '1day': 86400,   # 1 day
        }

        return horizon_map.get(bar_size, 3600)  # Default to 1 hour

    def _parse_historical_data(self, data: Dict[str, Any], symbol: str = "") -> pd.DataFrame:
        """Parse Saxo Bank API response to DataFrame"""
        try:
            if 'Data' not in data:
                logger.error("❌ No 'Data' key in Saxo response")
                logger.debug(f"Response keys: {data.keys()}")
                return pd.DataFrame()

            chart_data = data['Data']
            
            if len(chart_data) == 0:
                logger.warning(f"⚠️ No chart data returned for {symbol}")
                return pd.DataFrame()
            
            logger.info(f"📊 Parsing {len(chart_data)} bars for {symbol}")
            
            records = []

            for point in chart_data:
                # Saxo Bank timestamps are in UTC milliseconds or seconds
                timestamp = point.get('Time', 0)
                
                # Convert to datetime (handle both seconds and milliseconds)
                if timestamp > 10000000000:  # Milliseconds
                    dt = datetime.fromtimestamp(timestamp / 1000)
                else:  # Seconds
                    dt = datetime.fromtimestamp(timestamp)
                
                record = {
                    'timestamp': dt,
                    'open': float(point.get('Open', 0)),
                    'high': float(point.get('High', 0)),
                    'low': float(point.get('Low', 0)),
                    'close': float(point.get('Close', 0)),
                    'volume': int(point.get('Volume', 0))
                }
                records.append(record)

            df = pd.DataFrame(records)
            
            if len(df) > 0:
                df.set_index('timestamp', inplace=True)
                df = df.sort_index()  # Sort by timestamp
                logger.info(f"✅ DataFrame created: {len(df)} rows from {df.index[0]} to {df.index[-1]}")
            
            return df

        except Exception as e:
            logger.error(f"❌ Error parsing Saxo data: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return pd.DataFrame()
    
    def _generate_simulated_historical_data(self, symbol: str, uic: int, count: int, bar_size: str) -> pd.DataFrame:
        """
        Generate simulated historical data when Charts API is not available
        Uses current price from InfoPrices and generates realistic historical data
        """
        try:
            import numpy as np
            
            logger.info(f"📊 Generating simulated data for {symbol} (UIC: {uic})")
            
            # Get current price
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'Uic': uic,
                'AssetType': 'Stock'
            }
            
            response = requests.get(
                f"{self.base_url}/trade/v1/infoprices",
                headers=headers,
                params=params,
                timeout=30
            )
            
            # Default price if API fails
            current_price = 60.0
            
            if response.status_code == 200:
                price_data = response.json()
                if 'Quote' in price_data:
                    quote = price_data['Quote']
                    current_price = quote.get('Mid', quote.get('Last', 60.0))
                    logger.info(f"✅ Current price: {current_price}")
            else:
                logger.warning(f"⚠️ Using default price: {current_price}")
            
            # Generate timestamps
            bar_minutes = {
                '1min': 1,
                '5min': 5,
                '15min': 15,
                '30min': 30,
                '1hour': 60,
                '1day': 1440
            }.get(bar_size, 5)
            
            end_time = datetime.now()
            timestamps = [end_time - timedelta(minutes=bar_minutes * i) for i in range(count)]
            timestamps.reverse()
            
            # Generate realistic price movements
            np.random.seed(42)  # For reproducibility
            returns = np.random.normal(0, 0.002, count)  # 0.2% volatility
            prices = current_price * np.cumprod(1 + returns)
            
            # Generate OHLCV data
            records = []
            for i, (ts, close_price) in enumerate(zip(timestamps, prices)):
                # Generate realistic OHLCV
                volatility = close_price * 0.005  # 0.5% intrabar volatility
                high = close_price + abs(np.random.normal(0, volatility))
                low = close_price - abs(np.random.normal(0, volatility))
                open_price = prices[i-1] if i > 0 else close_price
                
                volume = int(np.random.uniform(10000, 100000))
                
                record = {
                    'timestamp': ts,
                    'open': round(open_price, 2),
                    'high': round(high, 2),
                    'low': round(low, 2),
                    'close': round(close_price, 2),
                    'volume': volume
                }
                records.append(record)
            
            df = pd.DataFrame(records)
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"✅ Simulated data generated: {len(df)} bars from {df.index[0]} to {df.index[-1]}")
            logger.info(f"   Price range: {df['low'].min():.2f} - {df['high'].max():.2f}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error generating simulated data: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return pd.DataFrame()

    def place_order(self, symbol: str, action: str, quantity: int,
                   order_type: str = "MKT", price: float = None) -> bool:
        """
        Place an order with Saxo Bank

        Args:
            symbol: Trading symbol
            action: 'BUY' or 'SELL'
            quantity: Number of shares
            order_type: Order type ('MKT', 'LMT', etc.)
            price: Limit price (for LMT orders)

        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            logger.error("Not connected to Saxo Bank")
            return False

        try:
            # Convert symbol
            saxo_symbol = self._convert_symbol_format(symbol, "EURONEXT")

            # Build order payload
            order_payload = {
                "AccountKey": "your_account_key",
                "AssetType": "Stock",
                "Uic": saxo_symbol,
                "Amount": quantity,
                "BuySell": action,
                "OrderType": order_type,
                "ManualOrder": True
            }

            if order_type == "LMT" and price:
                order_payload["OrderPrice"] = price

            url = f"{self.base_url}/trade/v2/orders"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(url, json=order_payload, headers=headers, timeout=30)

            if response.status_code in [200, 201]:
                logger.info(f"Order placed successfully: {action} {quantity} {symbol}")
                return True
            else:
                logger.error(f"Order failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return False

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information"""
        if not self.connected:
            return None

        try:
            url = f"{self.base_url}/port/v1/accounts/me"
            headers = {'Authorization': f'Bearer {self.access_token}'}

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get account info: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None


# Global Saxo client instance
saxo_client = SaxoClient()