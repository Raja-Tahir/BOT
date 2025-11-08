"""
data_fetcher.py

Description:
Fetch market data from Bitget exchange

Features:
- Fetch data using CCXT library
- Convert OHLCV to pandas dataframe
- Calculate candle close timing
"""

import time
import pandas as pd
import ccxt


class DataFetcher:
    """
    Class for fetching data from Bitget
    """
    
    def __init__(self, exchange_id='bitget'):
        """
        Initialize DataFetcher
        
        Args:
            exchange_id: Exchange name (default: 'bitget')
        """
        self.exchange_id = exchange_id
        self.exchange = None
        self._initialize_exchange()
    
    def _initialize_exchange(self):
        """
        Initialize CCXT exchange
        """
        try:
            self.exchange = getattr(ccxt, self.exchange_id)({
                'enableRateLimit': True
            })
        except Exception as e:
            print(f"Error: Could not initialize exchange - {e}")
            self.exchange = None
    
    def fetch_ohlcv_df(self, symbol: str, timeframe: str = '1m', limit: int = 200):
        """
        Fetch OHLCV data and create dataframe
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe ('1m', '5m', '15m', etc.)
            limit: Number of candles to fetch
            
        Returns:
            DataFrame: OHLCV data or None if error occurs
        """
        if not self.exchange:
            print("Error: Exchange not available")
            return None
        
        try:
            # Fetch data from Bitget
            ohlcv = self.exchange.fetch_ohlcv(
                symbol, 
                timeframe=timeframe, 
                limit=limit
            )
            
            # Create dataframe
            df = pd.DataFrame(
                ohlcv, 
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Add datetime column
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('datetime', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"Error: Could not fetch data - {e}")
            return None
    
    def get_latest_price(self, symbol: str):
        """
        Get current price
        
        Args:
            symbol: Trading pair
            
        Returns:
            float: Current price or None
        """
        if not self.exchange:
            return None
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            print(f"Error: Could not get price - {e}")
            return None
    
    @staticmethod
    def align_to_next_candle(timeframe: str):
        """
        Calculate seconds until next candle close
        
        Args:
            timeframe: Timeframe (e.g., '1m', '5m')
            
        Returns:
            int: Time in seconds
        """
        # Extract minutes from timeframe (e.g., '1m' -> 1)
        tf_minutes = int(timeframe.replace('m', ''))
        
        # Current time
        now = time.time()
        
        # Seconds remaining until next candle
        seconds_till_next = (tf_minutes * 60) - (int(now) % (tf_minutes * 60))
        
        return seconds_till_next
    
    def is_exchange_available(self):
        """
        Check if exchange is available
        
        Returns:
            bool: True if available
        """
        return self.exchange is not None
    
    def get_exchange_info(self):
        """
        Get exchange information
        
        Returns:
            dict: Exchange details
        """
        if not self.exchange:
            return None
        
        return {
            'id': self.exchange.id,
            'name': self.exchange.name,
            'has': {
                'fetchOHLCV': self.exchange.has.get('fetchOHLCV', False),
                'fetchTicker': self.exchange.has.get('fetchTicker', False)
            }
        }
    
    def validate_symbol(self, symbol: str):
        """
        Check if symbol is valid
        
        Args:
            symbol: Trading pair
            
        Returns:
            bool: True if valid
        """
        if not self.exchange:
            return False
        
        try:
            # Load exchange markets
            self.exchange.load_markets()
            return symbol in self.exchange.markets
        except Exception as e:
            print(f"Error: Could not validate symbol - {e}")
            return False
