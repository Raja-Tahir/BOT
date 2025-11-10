# === FILE: strategy.py ===
"""
Trading strategy module for AI Signal Bot Pro v2.1
Computes indicators, generates buy/sell signals.
Supports reverse/backtest mode.
"""
import pandas as pd
import utils
import data_fetcher
import config


class Strategy:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.indicators = config_manager.load_config().get('use_indicators', {})

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if self.indicators.get('rsi'):
            df['RSI_14'] = utils.rsi(df['close'])
        if self.indicators.get('ema'):
            df['EMA_20'] = utils.ema(df['close'], 20)
        if self.indicators.get('macd'):
            df['EMA_12'] = utils.ema(df['close'], 12)
            df['EMA_26'] = utils.ema(df['close'], 26)
            df['MACD'] = df['EMA_12'] - df['EMA_26']
        if self.indicators.get('bb'):
            df['SMA_20'] = utils.sma(df['close'], 20)
            df['BB_Upper'] = df['SMA_20'] + 2*df['close'].rolling(20).std()
            df['BB_Lower'] = df['SMA_20'] - 2*df['close'].rolling(20).std()
        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['Signal'] = ''
        for i in range(len(df)):
            if 'EMA_20' in df.columns and 'RSI_14' in df.columns:
                if df['close'].iloc[i] > df['EMA_20'].iloc[i] and df['RSI_14'].iloc[i] < 70:
                    df.at[i, 'Signal'] = 'Buy Long'
                elif df['close'].iloc[i] < df['EMA_20'].iloc[i] and df['RSI_14'].iloc[i] > 30:
                    df.at[i, 'Signal'] = 'Sell Short'
        return df

    def run(self, steps: int = 200) -> pd.DataFrame:
        df = data_fetcher.fetch_historical(self.symbol, limit=steps)
        df = self.compute_indicators(df)
        df = self.generate_signals(df)
        return df
