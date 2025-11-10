# === FILE: data_fetcher.py ===
"""
Data fetching module for AI Signal Bot Pro v2.1
Handles historical and live price fetching.
Supports reverse check mode for backtesting.
"""
import pandas as pd
import numpy as np
import time
from datetime import datetime

import config


def fetch_historical(symbol: str, limit: int = 500) -> pd.DataFrame:
    """
    Placeholder function to fetch historical OHLCV data.
    Currently generates synthetic data for testing.
    """
    rng = pd.date_range(end=datetime.utcnow(), periods=limit, freq='T')
    price = 100 + np.cumsum(np.random.randn(limit) * 0.2)
    df = pd.DataFrame({
        'timestamp': rng.astype(int) // 10**9,
        'open': price + np.random.randn(limit) * 0.02,
        'high': price + abs(np.random.randn(limit) * 0.2),
        'low': price - abs(np.random.randn(limit) * 0.2),
        'close': price,
        'volume': np.random.randint(1, 10, size=limit)
    })

    # Reverse mode support
    if config_manager.load_config().get('reverse_check_mode'):
        df = df.iloc[::-1].reset_index(drop=True)

    return df


def fetch_live(symbol: str) -> dict:
    """
    Placeholder for live price fetching.
    Returns the latest OHLCV snapshot.
    """
    df = fetch_historical(symbol, limit=1)
    last_row = df.iloc[-1]
    return {
        'timestamp': last_row['timestamp'],
        'open': last_row['open'],
        'high': last_row['high'],
        'low': last_row['low'],
        'close': last_row['close'],
        'volume': last_row['volume']
    }