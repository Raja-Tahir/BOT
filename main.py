# === FILE: config.py ===
"""
Configuration and constants for AI Signal Bot Pro v2.1
Do NOT store real API keys here. Use environment variables or an encrypted vault.
"""

# General settings
INTERVAL_SECONDS = 300  # default 5 minutes
HISTORICAL_CANDLES = 500
DEFAULT_SYMBOL = "TURBO/USDT"

# Risk settings (can be edited from GUI)
DEFAULT_SL_PERCENT = 0.5  # 0.5%
DEFAULT_TP_PERCENT = 1.0  # 1%

# API placeholders (don't hardcode keys here)
EXCHANGE_API = {
    "name": "bitget",
    "api_key": None,
    "api_secret": None,
    "passphrase": None,
}

# GUI related
OUTPUT_LOGFILE = "signals_log.txt"


# === FILE: utils.py ===
"""
Helper utilities: simple indicators, file save, safe wrappers.
"""
import math
import csv
from datetime import datetime

import pandas as pd


def save_output(text: str, filename: str = "output.txt"):
    """Append timestamped text to filename."""
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.utcnow().isoformat()}] \t{text}\n")


def sma(series, period: int):
    return series.rolling(period).mean()


def ema(series, period: int):
    return series.ewm(span=period, adjust=False).mean()


def rsi(series, period: int = 14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / (avg_loss.replace(0, math.nan))
    rsi = 100 - (100 / (1 + rs))
    return rsi


def guard_dataframe(df):
    """Ensure required columns exist and convert types."""
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Expected pandas DataFrame")
    required = ["timestamp", "open", "high", "low", "close", "volume"]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"Missing column: {c}")
    df = df.copy()
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["close"]).reset_index(drop=True)
    return df


# === FILE: backend.py ===
"""
Backend engine: data fetching (placeholder), indicator calculation, signal generation,
and reverse/backtest testing function used by the GUI reverse-test button.
"""
from typing import List, Dict
import time
import pandas as pd

import config
import utils


# ------------------ Data fetching (placeholder) ------------------
def fetch_historical(symbol: str = None, limit: int = None) -> pd.DataFrame:
    """
    Placeholder: in real use, implement exchange API calls using CCXT or exchange SDK.
    For now this function will generate synthetic data so you can test logic offline.
    """
    symbol = symbol or config.DEFAULT_SYMBOL
    limit = limit or config.HISTORICAL_CANDLES

    # Synthetic timeseries generator
    import numpy as np
    rng = pd.date_range(end=pd.Timestamp.utcnow(), periods=limit, freq="T")
    price = 100 + np.cumsum(np.random.randn(limit) * 0.2)
    df = pd.DataFrame({
        "timestamp": rng.astype(int) // 10**9,
        "open": price + np.random.randn(limit) * 0.02,
        "high": price + abs(np.random.randn(limit) * 0.2),
        "low": price - abs(np.random.randn(limit) * 0.2),
        "close": price,
        "volume": np.random.randint(1, 10, size=limit),
    })
    return df


# ------------------ Indicator computation ------------------

def compute_indicators(df: pd.DataFrame, indicators: List[str]) -> Dict[str, pd.Series]:
    df = utils.guard_dataframe(df)
    out = {}
    close = df["close"]
    if "SMA_20" in indicators:
        out["SMA_20"] = utils.sma(close, 20)
    if "EMA_20" in indicators:
        out["EMA_20"] = utils.ema(close, 20)
    if "RSI_14" in indicators:
        out["RSI_14"] = utils.rsi(close, 14)
    # add more indicators as needed
    return out


# ------------------ Signal generation ------------------

def generate_signals(df: pd.DataFrame, indicators_dict: Dict[str, pd.Series]) -> List[str]:
    """
    Very simple rule-based signals for demo:
    - If close > EMA_20 and RSI_14 < 70 => Buy Long
    - If close < EMA_20 and RSI_14 > 30 => Sell Short
    This is intentionally simple: replace with your AI logic later.
    """
    signals = []
    if len(df) == 0:
        return signals
    last_close = df["close"].iloc[-1]
    ema = indicators_dict.get("EMA_20")
    rsi = indicators_dict.get("RSI_14")
    if ema is None or rsi is None:
        return signals
    ema_last = ema.iloc[-1]
    rsi_last = rsi.iloc[-1]
    if pd.isna(ema_last) or pd.isna(rsi_last):
        return signals
    if last_close > ema_last and rsi_last < 70:
        signals.append("Buy Long")
    if last_close < ema_last and rsi_last > 30:
        signals.append("Buy Short")
    return signals


# ------------------ Reverse/backtest runner ------------------

def run_reverse_test(symbol: str, indicators: List[str], steps: int = 200) -> Dict:
    """
    Run the indicator+signal logic on reversed historical data for testing.
    Steps: Fetch data, reverse it, compute indicators progressively and collect signals.
    Returns a dict summary and a list of timestamped signals.
    """
    df = fetch_historical(symbol, limit=steps)
    df = utils.guard_dataframe(df)

    # Reverse the dataframe (simulate running history forward but on reversed sequence)
    df_reversed = df.iloc[::-1].reset_index(drop=True)

    collected = []
    # Progressive computation: at each step compute indicators on slice
    for i in range(30, len(df_reversed)):
        window = df_reversed.iloc[: i + 1]
        inds = compute_indicators(window, indicators)
        sigs = generate_signals(window, inds)
        if sigs:
            ts = window["timestamp"].iloc[-1]
            collected.append({"timestamp": int(ts), "signals": sigs, "index": i})
    summary = {"symbol": symbol, "total_checks": len(df_reversed), "found": len(collected)}
    return {"summary": summary, "details": collected}


# ------------------ Live check (single shot) ------------------

def run_live_check(symbol: str, indicators: List[str]) -> Dict:
    df = fetch_historical(symbol, limit=200)
    df = utils.guard_dataframe(df)
    inds = compute_indicators(df, indicators)
    sigs = generate_signals(df, inds)
    return {"symbol": symbol, "signals": sigs}


# === FILE: mainGUI.py ===
"""
Main GUI for AI Signal Bot Pro v2.1
Features:
- Indicator selection (checkboxes)
- Start/Stop Live checking (not fully automated scheduler here)
- Reverse Test button to run backtest-like check on reversed data
- Save results to file
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time

import config
import backend
import utils


AVAILABLE_INDICATORS = ["SMA_20", "EMA_20", "RSI_14"]


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Signal Bot Pro v2.1")
        self.geometry("820x600")
        self.selected_indicators = {name: tk.BooleanVar(value=(name in ["EMA_20", "RSI_14"])) for name in AVAILABLE_INDICATORS}
        self.is_running = False
        self.create_widgets()

    def create_widgets(self):
        frm = ttk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Symbol entry
        sym_lbl = ttk.Label(frm, text="Symbol:")
        sym_lbl.grid(row=0, column=0, sticky=tk.W)
        self.symbol_entry = ttk.Entry(frm)
        self.symbol_entry.insert(0, config.DEFAULT_SYMBOL)
        self.symbol_entry.grid(row=0, column=1, sticky=tk.W)

        # Indicators
        ind_lbl = ttk.Label(frm, text="Indicators:")
        ind_lbl.grid(row=1, column=0, sticky=tk.N)
        ind_frm = ttk.Frame(frm)
        ind_frm.grid(row=1, column=1, sticky=tk.W)
        r = 0
        for name in AVAILABLE_INDICATORS:
            cb = ttk.Checkbutton(ind_frm, text=name, variable=self.selected_indicators[name])
            cb.grid(row=r, column=0, sticky=tk.W)
            r += 1

        # Buttons
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))

        self.live_btn = ttk.Button(btn_frame, text="Run Live Check", command=self.run_live_once)
        self.live_btn.grid(row=0, column=0, padx=6)

        self.reverse_btn = ttk.Button(btn_frame, text="Reverse Test (Indicators)", command=self.run_reverse_test)
        self.reverse_btn.grid(row=0, column=1, padx=6)

        self.save_btn = ttk.Button(btn_frame, text="Open Log File", command=self.open_log_file)
        self.save_btn.grid(row=0, column=2, padx=6)

        # Output
        out_lbl = ttk.Label(frm, text="Output:")
        out_lbl.grid(row=3, column=0, sticky=tk.NW, pady=(10, 0))
        self.output_box = scrolledtext.ScrolledText(frm, width=90, height=25)
        self.output_box.grid(row=3, column=1, sticky=tk.W, pady=(10, 0))

    def append_output(self, text: str):
        self.output_box.insert(tk.END, text + "\n")
        self.output_box.see(tk.END)
        utils.save_output(text, config.OUTPUT_LOGFILE)

    def run_live_once(self):
        symbol = self.symbol_entry.get().strip() or config.DEFAULT_SYMBOL
        indicators = [k for k, v in self.selected_indicators.items() if v.get()]
        self.append_output(f"Running live check for {symbol} with {indicators}")
        res = backend.run_live_check(symbol, indicators)
        self.append_output(f"Result: {res}")

    def run_reverse_test(self):
        symbol = self.symbol_entry.get().strip() or config.DEFAULT_SYMBOL
        indicators = [k for k, v in self.selected_indicators.items() if v.get()]
        # run in a separate thread to keep UI responsive
        t = threading.Thread(target=self._reverse_test_thread, args=(symbol, indicators), daemon=True)
        t.start()

    def _reverse_test_thread(self, symbol, indicators):
        self.append_output(f"Starting reverse test for {symbol} with {indicators}...")
        try:
            res = backend.run_reverse_test(symbol, indicators, steps=300)
            summary = res.get("summary", {})
            details = res.get("details", [])
            self.append_output(f"Reverse test summary: {summary}")
            for d in details:
                self.append_output(f"@{d['timestamp']} idx:{d['index']} -> {d['signals']}")
            self.append_output("Reverse test completed.")
        except Exception as e:
            self.append_output(f"Error during reverse test: {e}")

    def open_log_file(self):
        import os
        fn = config.OUTPUT_LOGFILE
        if not os.path.exists(fn):
            messagebox.showinfo("Info", f"Log file not found: {fn}")
            return
        # open file with default app
        try:
            os.startfile(fn)
        except Exception:
            messagebox.showinfo("Info", f"Log file located at: {os.path.abspath(fn)}")


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
