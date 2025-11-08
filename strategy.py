"""
strategy.py

Description:
Trading strategy - indicator calculations and signal detection

Features:
- EMA, RSI, MACD indicators
- Buy and sell signal generation
- Triple Confirmation Strategy (EMA + RSI + MACD + Volume)
"""

import pandas as pd
import ta


class StrategyConfig:
    """
    All strategy configuration parameters
    """
    def __init__(self):
        # EMA settings
        self.ema_short = 20
        self.ema_long = 50
        
        # RSI settings
        self.rsi_period = 14
        
        # MACD settings
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
        # Volume settings
        self.vol_multiplier = 1.3
        
        # Take Profit and Stop Loss
        self.tp_percent = 0.5   # percent
        self.sl_percent = 0.25  # percent
        
        # Trend clarity threshold
        self.trend_threshold_pct = 0.15


# Global config object
strategy_cfg = StrategyConfig()


def compute_indicators(df: pd.DataFrame):
    """
    Add all indicators to dataframe
    
    Args:
        df: OHLCV dataframe
        
    Returns:
        DataFrame: Dataframe with indicators
    """
    df = df.copy()
    
    # EMA - Exponential Moving Average
    df['ema_short'] = ta.trend.EMAIndicator(
        df['close'], 
        window=strategy_cfg.ema_short
    ).ema_indicator()
    
    df['ema_long'] = ta.trend.EMAIndicator(
        df['close'], 
        window=strategy_cfg.ema_long
    ).ema_indicator()
    
    # RSI - Relative Strength Index
    df['rsi'] = ta.momentum.RSIIndicator(
        df['close'], 
        window=strategy_cfg.rsi_period
    ).rsi()
    
    # MACD - Moving Average Convergence Divergence
    macd = ta.trend.MACD(
        df['close'],
        window_slow=strategy_cfg.macd_slow,
        window_fast=strategy_cfg.macd_fast,
        window_sign=strategy_cfg.macd_signal
    )
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_hist'] = macd.macd_diff()
    
    # Volume average (10 candles)
    df['vol_avg_10'] = df['volume'].rolling(10).mean()
    
    return df


def check_signal(df: pd.DataFrame, timeframe: str, symbol: str):
    """
    Check for buy or sell signals
    
    Args:
        df: Dataframe with indicators
        timeframe: Timeframe (e.g., '1m', '5m')
        symbol: Trading pair (e.g., 'BTC/USDT')
        
    Returns:
        tuple: (signal: str or None, details: dict or None)
    """
    # Check if data is sufficient
    if df is None or len(df) < 15:
        return None, None
    
    # Latest and previous candles
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    ema_s = latest['ema_short']
    ema_l = latest['ema_long']
    
    # Check if EMA data is available
    if pd.isna(ema_s) or pd.isna(ema_l):
        return None, None
    
    # Volume check
    vol_ok = False
    if not pd.isna(latest['vol_avg_10']):
        vol_ok = latest['volume'] > (latest['vol_avg_10'] * strategy_cfg.vol_multiplier)
    
    # EMA difference (trend clarity)
    ema_diff_pct = abs((ema_s - ema_l) / ema_l) * 100 if ema_l != 0 else 0
    trend_clear = ema_diff_pct > strategy_cfg.trend_threshold_pct
    
    # MACD signals
    macd_bull = (latest['macd'] > latest['macd_signal']) and (latest['macd_hist'] > 0)
    macd_bear = (latest['macd'] < latest['macd_signal']) and (latest['macd_hist'] < 0)
    
    # RSI
    rsi = latest['rsi']
    
    # Buy conditions (LONG)
    buy_cond = (
        ema_s > ema_l and          # Short EMA above long EMA
        macd_bull and              # MACD bullish signal
        vol_ok and                 # Volume surge
        (rsi >= 45 and rsi <= 70) and  # RSI in proper range
        trend_clear                # Trend is clear
    )
    
    # Sell conditions (SHORT)
    sell_cond = (
        ema_s < ema_l and          # Short EMA below long EMA
        macd_bear and              # MACD bearish signal
        vol_ok and                 # Volume surge
        (rsi >= 30 and rsi <= 55) and  # RSI in proper range
        trend_clear                # Trend is clear
    )
    
    # If buy signal
    if buy_cond:
        details = {
            'type': 'LONG',
            'symbol': symbol,
            'timeframe': timeframe,
            'price': float(latest['close']),
            'ema_short': float(ema_s),
            'ema_long': float(ema_l),
            'rsi': float(rsi),
            'macd': float(latest['macd']),
            'macd_signal': float(latest['macd_signal']),
            'vol': float(latest['volume']),
            'vol_avg_10': float(latest['vol_avg_10']) if not pd.isna(latest['vol_avg_10']) else None
        }
        return 'BUY LONG', details
    
    # If sell signal
    elif sell_cond:
        details = {
            'type': 'SHORT',
            'symbol': symbol,
            'timeframe': timeframe,
            'price': float(latest['close']),
            'ema_short': float(ema_s),
            'ema_long': float(ema_l),
            'rsi': float(rsi),
            'macd': float(latest['macd']),
            'macd_signal': float(latest['macd_signal']),
            'vol': float(latest['volume']),
            'vol_avg_10': float(latest['vol_avg_10']) if not pd.isna(latest['vol_avg_10']) else None
        }
        return 'SELL SHORT', details
    
    # No signal
    return None, None


def calculate_tp_sl(price: float, signal_type: str):
    """
    Calculate Take Profit and Stop Loss
    
    Args:
        price: Current price
        signal_type: 'LONG' or 'SHORT'
        
    Returns:
        tuple: (tp: float, sl: float)
    """
    if signal_type == 'LONG':
        tp = price * (1 + strategy_cfg.tp_percent / 100)
        sl = price * (1 - strategy_cfg.sl_percent / 100)
    else:  # SHORT
        tp = price * (1 - strategy_cfg.tp_percent / 100)
        sl = price * (1 + strategy_cfg.sl_percent / 100)
    
    return tp, sl
