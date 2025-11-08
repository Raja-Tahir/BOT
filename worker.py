"""
worker.py

Description:
Background worker - check signals and send alerts

Features:
- Runs in separate thread
- Checks data when candle closes
- Sends Telegram alerts on signal detection
- Saves logs to CSV file
"""

import os
import time
import threading
import queue
from datetime import datetime
import pandas as pd

from config_manager import load_config, send_telegram_message, get_log_file_path
from strategy import compute_indicators, check_signal, calculate_tp_sl, strategy_cfg
from data_fetcher import DataFetcher


class Worker(threading.Thread):
    """
    Background worker class - runs in separate thread
    """
    
    def __init__(self, gui, config, cmd_queue: queue.Queue):
        """
        Initialize worker
        
        Args:
            gui: GUI object (for displaying logs)
            config: Config data (from config.json)
            cmd_queue: Command queue
        """
        super().__init__(daemon=True)
        self.gui = gui
        self.config = config
        self.cmd_queue = cmd_queue
        self._stop_event = threading.Event()
        
        # Initialize data fetcher
        self.data_fetcher = DataFetcher('bitget')
        
        if not self.data_fetcher.is_exchange_available():
            gui.safe_log("Error: Could not initialize exchange")
    
    def stop(self):
        """
        Signal worker to stop
        """
        self._stop_event.set()
    
    def stopped(self):
        """
        Check if worker has stopped
        
        Returns:
            bool: True if stopped
        """
        return self._stop_event.is_set()
    
    def run(self):
        """
        Main worker loop - all work happens here
        """
        self.gui.safe_log("Worker started ✅")
        
        while not self.stopped():
            try:
                # Check for commands from GUI
                try:
                    cmd = self.cmd_queue.get_nowait()
                    if cmd == 'stop':
                        self.gui.safe_log('Stopping worker...')
                        break
                except queue.Empty:
                    pass
                
                # Get symbol and timeframe
                symbol = self.gui.get_symbol()
                timeframe = self.gui.get_timeframe()
                
                if not symbol or not timeframe:
                    self.gui.safe_log('Symbol or timeframe not set')
                    time.sleep(1)
                    continue
                
                # Wait until next candle close
                sleep_for = self.data_fetcher.align_to_next_candle(timeframe)
                
                if sleep_for > 1:
                    self.gui.safe_log(
                        f"⏳ Waiting: {int(sleep_for)}s until candle close ({timeframe})"
                    )
                    # Sleep in small chunks so stop signal is detected quickly
                    for _ in range(int(sleep_for)):
                        if self.stopped():
                            break
                        time.sleep(1)
                    
                    # Wait a bit after candle close
                    time.sleep(2)
                
                # Fetch data
                df = self.data_fetcher.fetch_ohlcv_df(symbol, timeframe, limit=300)
                
                if df is None:
                    self.gui.safe_log('❌ Could not fetch data')
                    time.sleep(5)
                    continue
                
                # Add indicators
                df_with_indicators = compute_indicators(df)
                
                # Check for signals
                signal, details = check_signal(df_with_indicators, timeframe, symbol)
                
                if signal:
                    # Signal detected! 🎯
                    self._handle_signal(signal, details)
                else:
                    # No signal
                    latest_price = df_with_indicators['close'].iloc[-1]
                    self.gui.safe_log(
                        f"📊 No signal ({symbol} {timeframe}) - Price: {latest_price:.6f}"
                    )
            
            except Exception as e:
                self.gui.safe_log(f"❌ Worker error: {e}")
                time.sleep(2)
        
        self.gui.safe_log("Worker stopped ⏹️")
    
    def _handle_signal(self, signal: str, details: dict):
        """
        Handle signal detection
        
        Args:
            signal: Signal type ('BUY LONG' or 'SELL SHORT')
            details: Signal details
        """
        price = details['price']
        signal_type = details['type']
        symbol = details['symbol']
        timeframe = details['timeframe']
        
        # Calculate TP and SL
        tp, sl = calculate_tp_sl(price, signal_type)
        
        # Create Telegram message
        message = self._create_telegram_message(signal, details, tp, sl)
        
        # Display in logs
        self.gui.safe_log(f"🎯 Signal detected! {signal} {symbol} @ {price}")
        
        # Save to CSV file
        self._save_to_csv(signal, details)
        
        # Send to Telegram (in separate thread)
        telegram_thread = threading.Thread(
            target=self._send_telegram_alert, 
            args=(message,),
            daemon=True
        )
        telegram_thread.start()
    
    def _create_telegram_message(self, signal: str, details: dict, tp: float, sl: float):
        """
        Create message for Telegram
        
        Args:
            signal: Signal
            details: Details
            tp: Take Profit
            sl: Stop Loss
            
        Returns:
            str: Formatted message
        """
        price = details['price']
        symbol = details['symbol']
        timeframe = details['timeframe']
        rsi = details['rsi']
        ema_short = details['ema_short']
        ema_long = details['ema_long']
        vol = details['vol']
        vol_avg = details['vol_avg_10']
        
        message = f"""*{signal}* 🎯

📊 *Pair:* `{symbol}`
💰 *Price:* `{price:.6f}`
🎯 *TP:* `{tp:.6f}`
🛑 *SL:* `{sl:.6f}`

📈 *Indicators:*
• RSI: `{rsi:.2f}`
• EMA{strategy_cfg.ema_short}: `{ema_short:.6f}`
• EMA{strategy_cfg.ema_long}: `{ema_long:.6f}`
• Volume: `{vol:.0f}` (avg: `{vol_avg:.0f}`)

⏰ *Timeframe:* {timeframe}
🕐 *Time:* {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        return message
    
    def _send_telegram_alert(self, message: str):
        """
        Send alert to Telegram
        
        Args:
            message: Message to send
        """
        if not self.config:
            self.gui.safe_log('⚠️ Config not found - cannot send Telegram')
            return
        
        telegram_config = self.config.get('telegram', {})
        bot_token = telegram_config.get('bot_token')
        chat_id = telegram_config.get('chat_id')
        
        if not bot_token or not chat_id:
            self.gui.safe_log('⚠️ Telegram settings not found')
            return
        
        success, response = send_telegram_message(bot_token, chat_id, message)
        
        if success:
            self.gui.safe_log('✅ Telegram alert sent')
        else:
            self.gui.safe_log(f'❌ Telegram error: {response}')
    
    def _save_to_csv(self, signal: str, details: dict):
        """
        Save signal to CSV file
        
        Args:
            signal: Signal
            details: Details
        """
        log_file = get_log_file_path()
        
        row = {
            'timestamp': datetime.utcnow().isoformat(),
            'pair': details.get('symbol'),
            'timeframe': details.get('timeframe'),
            'signal': signal,
            'price': details.get('price'),
            'ema_short': details.get('ema_short'),
            'ema_long': details.get('ema_long'),
            'rsi': details.get('rsi'),
            'macd': details.get('macd'),
            'macd_signal': details.get('macd_signal'),
            'vol': details.get('vol'),
            'vol_avg_10': details.get('vol_avg_10')
        }
        
        try:
            df_row = pd.DataFrame([row])
            write_header = not os.path.exists(log_file)
            df_row.to_csv(log_file, mode='a', header=write_header, index=False)
            self.gui.safe_log(f'💾 Log saved')
        except Exception as e:
            self.gui.safe_log(f'❌ Could not save log: {e}')
