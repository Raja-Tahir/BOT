# === FILE: utils.py ===
"""
Helper utilities for AI Signal Bot Pro v2.1
Includes technical indicators and output/logging functions.
"""
import pandas as pd
import numpy as np
from datetime import datetime

# === Technical Indicators ===

def sma(series: pd.Series, period: int = 20) -> pd.Series:
    return series.rolling(period).mean()

def ema(series: pd.Series, period: int = 20) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / (avg_loss + 1e-8)
    return 100 - (100 / (1 + rs))

# === Output / Logging ===

LOG_FILE = "signals_log.txt"

def save_output(text: str, file_name: str = None):
    fn = file_name or LOG_FILE
    with open(fn, 'a') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {text}\n")