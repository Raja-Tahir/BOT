# === FILE: gui.py ===
"""
GUI module for AI Signal Bot Pro v2.1
Provides interface for live checking, reverse testing, and indicator selection.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading

import config_manager
import worker
import strategy
import utils

AVAILABLE_INDICATORS = ["rsi", "ema", "macd", "bb"]

class MainGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Signal Bot Pro v2.1")
        self.geometry("820x600")

        self.selected_indicators = {name: tk.BooleanVar(value=True) for name in AVAILABLE_INDICATORS}
        self.worker_instance = None

        self.create_widgets()

    def create_widgets(self):
        frm = ttk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Symbol entry
        ttk.Label(frm, text="Symbol:").grid(row=0, column=0, sticky=tk.W)
        self.symbol_entry = ttk.Entry(frm)
        self.symbol_entry.insert(0, "TURBO/USDT")
        self.symbol_entry.grid(row=0, column=1, sticky=tk.W)

        # Indicators
        ttk.Label(frm, text="Indicators:").grid(row=1, column=0, sticky=tk.N)
        ind_frm = ttk.Frame(frm)
        ind_frm.grid(row=1, column=1, sticky=tk.W)
        for r, name in enumerate(AVAILABLE_INDICATORS):
            cb = ttk.Checkbutton(ind_frm, text=name.upper(), variable=self.selected_indicators[name])
            cb.grid(row=r, column=0, sticky=tk.W)

        # Buttons
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(10,0))

        ttk.Button(btn_frame, text="Run Live Check", command=self.run_live_once).grid(row=0, column=0, padx=6)
        ttk.Button(btn_frame, text="Reverse Test (Indicators)", command=self.run_reverse_test).grid(row=0, column=1, padx=6)
        ttk.Button(btn_frame, text="Open Log File", command=self.open_log_file).grid(row=0, column=2, padx=6)

        # Output box
        ttk.Label(frm, text="Output:").grid(row=3, column=0, sticky=tk.NW, pady=(10,0))
        self.output_box = scrolledtext.ScrolledText(frm, width=90, height=25)
        self.output_box.grid(row=3, column=1, sticky=tk.W, pady=(10,0))

    def append_output(self, text: str):
        self.output_box.insert(tk.END, text + "\n")
        self.output_box.see(tk.END)
        utils.save_output(text, "signals_log.txt")

    def run_live_once(self):
        symbol = self.symbol_entry.get().strip()
        selected_inds = [k for k, v in self.selected_indicators.items() if v.get()]
        self.append_output(f"Running live check for {symbol} with {selected_inds}")
        strat = strategy.Strategy(symbol)
        df = strat.run(steps=200)
        last_signal = df['Signal'].iloc[-1]
        if last_signal:
            self.append_output(f"Live Signal: {last_signal}")

    def run_reverse_test(self):
        symbol = self.symbol_entry.get().strip()
        selected_inds = [k for k, v in self.selected_indicators.items() if v.get()]
        # Enable reverse mode in config
        config_manager.toggle_reverse_check(True)

        def thread_func():
            self.append_output(f"Starting Reverse Test for {symbol} with {selected_inds}...")
            strat = strategy.Strategy(symbol)
            df = strat.run(steps=300)
            rev_signals = df[df['Signal'] != '']
            for _, row in rev_signals.iterrows():
                self.append_output(f"@{row['Signal']}")
            self.append_output("Reverse Test Completed.")
            # Disable reverse mode after test
            config_manager.toggle_reverse_check(False)

        t = threading.Thread(target=thread_func, daemon=True)
        t.start()

    def open_log_file(self):
        import os
        fn = "signals_log.txt"
        if os.path.exists(fn):
            os.startfile(fn)
        else:
            messagebox.showinfo("Info", f"Log file not found: {fn}")


if __name__ == "__main__":
    app = MainGUI()
    app.mainloop()