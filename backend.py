# === FILE: worker.py ===
"""
Worker module for AI Signal Bot Pro v2.1
Handles continuous live checking, reverse testing, and logs results.
"""
import threading
import time
import config
import strategy
import utils


class Worker:
    def __init__(self, symbol: str, interval: int = None):
        self.symbol = symbol
        self.interval = interval or config_manager.load_config().get('check_interval', 5)
        self.is_running = False
        self.thread = None

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1)

    def _run_loop(self):
        while self.is_running:
            try:
                reverse_mode = config_manager.load_config().get('reverse_check_mode', False)
                strat = strategy.Strategy(self.symbol)
                df = strat.run(steps=200)

                if reverse_mode:
                    # Only log signals that occurred in reverse mode
                    reversed_signals = df[df['Signal'] != '']
                    for _, row in reversed_signals.iterrows():
                        utils.save_output(f"[Reverse Test] {self.symbol} -> {row['Signal']}")
                else:
                    # Normal live signals
                    last_signal = df['Signal'].iloc[-1]
                    if last_signal:
                        utils.save_output(f"[Live] {self.symbol} -> {last_signal}")

            except Exception as e:
                utils.save_output(f"Worker error for {self.symbol}: {e}")

            time.sleep(self.interval * 60)  # interval in minutes