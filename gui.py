"""
gui.py

Description:
Complete Graphical User Interface (Tkinter)

Features:
- Clean and easy interface
- Symbol, timeframe, TP/SL settings
- Live logs display
- Start/Stop buttons
- Manual testing buttons
"""

import os
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from config_manager import load_config, send_telegram_message, get_log_directory, get_log_file_path
from strategy import strategy_cfg
from worker import Worker


class ScalperGUI:
    """
    Complete GUI for AI Scalping Bot
    """
    
    def __init__(self, root):
        """
        Initialize GUI
        
        Args:
            root: Tkinter main window
        """
        self.root = root
        root.title('AI Scalping Bot Pro — GUI')
        root.geometry('900x680')
        root.minsize(820, 560)
        
        # Theme and style
        self._setup_style()
        
        # Top section: Controls
        self._create_top_controls()
        
        # Middle section: Logs and details
        self._create_middle_section()
        
        # Bottom section: Status bar
        self._create_bottom_status()
        
        # Internal variables
        self.worker = None
        self.cmd_queue = queue.Queue()
        self.cfg = None
        self._lock = threading.Lock()
        
        # Load config if exists
        default_config = os.path.join(os.path.dirname(__file__), 'config.json')
        if os.path.exists(default_config):
            self.load_config(default_config)
    
    def _setup_style(self):
        """
        GUI styling
        """
        style = ttk.Style(self.root)
        try:
            style.theme_use('clam')
        except:
            pass
        
        style.configure('TFrame', background='#f6f8fa')
        style.configure('TLabel', background='#f6f8fa', font=('Segoe UI', 10))
        style.configure('Header.TLabel', font=('Segoe UI Semibold', 14))
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('TEntry', font=('Segoe UI', 10))
    
    def _create_top_controls(self):
        """
        Create controls in top section
        """
        top = ttk.Frame(self.root, padding=12, style='TFrame')
        top.pack(side='top', fill='x')
        
        # Symbol
        ttk.Label(top, text='Symbol:', style='TLabel').grid(row=0, column=0, sticky='w')
        self.symbol_var = tk.StringVar(value='BTC/USDT')
        self.symbol_entry = ttk.Entry(top, textvariable=self.symbol_var, width=18)
        self.symbol_entry.grid(row=0, column=1, padx=6)
        
        # Timeframe
        ttk.Label(top, text='Timeframe:', style='TLabel').grid(row=0, column=2, sticky='w', padx=(12,0))
        self.tf_var = tk.StringVar(value='1m')
        self.tf_combo = ttk.Combobox(top, textvariable=self.tf_var, values=['1m','5m'], width=6, state='readonly')
        self.tf_combo.grid(row=0, column=3, padx=6)
        
        # TP percent
        ttk.Label(top, text='TP %:', style='TLabel').grid(row=0, column=4, sticky='w', padx=(12,0))
        self.tp_var = tk.StringVar(value=str(strategy_cfg.tp_percent))
        ttk.Entry(top, textvariable=self.tp_var, width=6).grid(row=0, column=5, padx=6)
        
        # SL percent
        ttk.Label(top, text='SL %:', style='TLabel').grid(row=0, column=6, sticky='w', padx=(12,0))
        self.sl_var = tk.StringVar(value=str(strategy_cfg.sl_percent))
        ttk.Entry(top, textvariable=self.sl_var, width=6).grid(row=0, column=7, padx=6)
        
        # Start button
        self.start_btn = ttk.Button(top, text='▶ Start', command=self.start)
        self.start_btn.grid(row=0, column=8, padx=(12,4))
        
        # Stop button
        self.stop_btn = ttk.Button(top, text='⏹ Stop', command=self.stop, state='disabled')
        self.stop_btn.grid(row=0, column=9, padx=(4,0))
    
    def _create_middle_section(self):
        """
        Middle section: Logs and details
        """
        middle = ttk.Frame(self.root, padding=8, style='TFrame')
        middle.pack(fill='both', expand=True)
        
        # Left side - Logs
        left = ttk.Frame(middle, width=520, style='TFrame')
        left.pack(side='left', fill='both', expand=True)
        ttk.Label(left, text='Live Logs', style='Header.TLabel').pack(anchor='w')
        
        self.log_text = tk.Text(left, wrap='none', height=30, font=('Consolas',10))
        self.log_text.pack(fill='both', expand=True, padx=6, pady=6)
        self.log_text.configure(state='disabled')
        
        # Right side - Details and controls
        right = ttk.Frame(middle, width=360, style='TFrame')
        right.pack(side='right', fill='y')
        ttk.Label(right, text='Details & Controls', style='Header.TLabel').pack(anchor='w')
        
        # Status
        self.status_var = tk.StringVar(value='Idle')
        ttk.Label(right, text='Status:', style='TLabel').pack(anchor='w', pady=(6,0))
        ttk.Label(right, textvariable=self.status_var, style='TLabel').pack(anchor='w')
        
        ttk.Separator(right).pack(fill='x', pady=8)
        
        # File buttons
        ttk.Button(right, text='Open logs folder', command=self.open_logs).pack(fill='x', padx=8, pady=4)
        ttk.Button(right, text='Load config.json', command=lambda: self.load_config()).pack(fill='x', padx=8, pady=4)
        ttk.Button(right, text='Export signals CSV', command=self.export_csv).pack(fill='x', padx=8, pady=4)
        
        ttk.Separator(right).pack(fill='x', pady=8)
        
        # Testing buttons
        ttk.Label(right, text='Manual / Test', style='TLabel').pack(anchor='w', pady=(6,0))
        ttk.Button(right, text='Test Telegram', command=self.test_telegram).pack(fill='x', padx=8, pady=4)
        ttk.Button(right, text='Manual BUY signal', command=lambda: self.manual_signal('BUY LONG')).pack(fill='x', padx=8, pady=4)
        ttk.Button(right, text='Manual SELL signal', command=lambda: self.manual_signal('SELL SHORT')).pack(fill='x', padx=8, pady=4)
        
        ttk.Separator(right).pack(fill='x', pady=8)
        
        # Strategy parameters
        ttk.Label(right, text='Strategy Params', style='TLabel').pack(anchor='w', pady=(6,0))
        
        ttk.Label(right, text='EMA Short:').pack(anchor='w')
        self.ema_short_var = tk.IntVar(value=strategy_cfg.ema_short)
        ttk.Entry(right, textvariable=self.ema_short_var).pack(fill='x', padx=8, pady=2)
        
        ttk.Label(right, text='EMA Long:').pack(anchor='w')
        self.ema_long_var = tk.IntVar(value=strategy_cfg.ema_long)
        ttk.Entry(right, textvariable=self.ema_long_var).pack(fill='x', padx=8, pady=2)
    
    def _create_bottom_status(self):
        """
        Bottom section status bar
        """
        bottom = ttk.Frame(self.root, padding=6, style='TFrame')
        bottom.pack(side='bottom', fill='x')
        self.bottom_label = ttk.Label(bottom, text='Ready — load config.json to continue', style='TLabel')
        self.bottom_label.pack(side='left')
    
    # --------------- Helper functions ---------------
    
    def safe_log(self, text):
        """
        Thread-safe logging
        
        Args:
            text: Text to write in log
        """
        ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        msg = f"[{ts}] {text}\n"
        
        def _append():
            self.log_text.configure(state='normal')
            self.log_text.insert('end', msg)
            self.log_text.see('end')
            self.log_text.configure(state='disabled')
        
        self.root.after(0, _append)
    
    def open_logs(self):
        """
        Open logs folder
        """
        path = get_log_directory()
        try:
            if os.name == 'nt':
                os.startfile(path)
            elif os.name == 'posix':
                os.system(f'xdg-open "{path}"')
        except Exception as e:
            messagebox.showinfo('Open logs', f'Cannot open folder: {e}')
    
    def load_config(self, path=None):
        """
        Load config.json
        
        Args:
            path: Path to config file (optional)
        """
        if not path:
            path = filedialog.askopenfilename(
                title='Select config.json', 
                filetypes=[('json','*.json')]
            )
        
        if not path:
            return
        
        cfg = load_config(path)
        if not cfg:
            messagebox.showerror('Config', 'Could not load config.json')
            return
        
        self.cfg = cfg
        self.bottom_label.config(text=f'Loaded: {os.path.basename(path)}')
        
        # Show Telegram ID
        tg = cfg.get('telegram', {})
        if tg.get('chat_id'):
            self.safe_log(f"Telegram Chat ID: {tg.get('chat_id')}")
        
        self.safe_log('Config loaded successfully')
    
    def export_csv(self):
        """
        Export signals to CSV
        """
        log_file = get_log_file_path()
        
        if not os.path.exists(log_file):
            messagebox.showinfo('Export', 'No signals logged yet')
            return
        
        dest = filedialog.asksaveasfilename(
            defaultextension='.csv', 
            filetypes=[('CSV','*.csv')]
        )
        
        if dest:
            try:
                with open(log_file,'rb') as fr, open(dest,'wb') as fw:
                    fw.write(fr.read())
                messagebox.showinfo('Export', 'Exported successfully')
            except Exception as e:
                messagebox.showerror('Export', f'Error: {e}')
    
    def test_telegram(self):
        """
        Send Telegram test message
        """
        if not self.cfg:
            messagebox.showwarning('Telegram', 'Load config.json first')
            return
        
        bot = self.cfg.get('telegram', {}).get('bot_token')
        chat = self.cfg.get('telegram', {}).get('chat_id')
        
        ok, resp = send_telegram_message(bot, chat, 'Test message from AI Scalping Bot GUI ✅')
        
        if ok:
            messagebox.showinfo('Telegram', 'Test message sent')
            self.safe_log('Telegram test successful')
        else:
            messagebox.showerror('Telegram', f'Failed: {resp}')
    
    def manual_signal(self, typ):
        """
        Send manual signal (for testing)
        
        Args:
            typ: 'BUY LONG' or 'SELL SHORT'
        """
        sym = self.get_symbol() or 'BTC/USDT'
        price = 'MANUAL'
        msg = f"*{typ}*\n\nPair: `{sym}`\nPrice: `{price}`\n\n(This is a manual/test signal)"
        
        self.safe_log(f"Manual signal: {typ} {sym}")
        
        if self.cfg:
            bot = self.cfg.get('telegram', {}).get('bot_token')
            chat = self.cfg.get('telegram', {}).get('chat_id')
            threading.Thread(
                target=send_telegram_message, 
                args=(bot, chat, msg), 
                daemon=True
            ).start()
    
    def get_symbol(self):
        """
        Get selected symbol
        
        Returns:
            str: Symbol
        """
        return self.symbol_var.get().strip()
    
    def get_timeframe(self):
        """
        Get selected timeframe
        
        Returns:
            str: Timeframe
        """
        return self.tf_var.get().strip()
    
    # --------------- Start / Stop ---------------
    
    def start(self):
        """
        Start worker
        """
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        
        if not os.path.exists(config_path):
            messagebox.showwarning(
                'Config', 
                'Please place config.json next to this script or load via button'
            )
            return
        
        self.cfg = load_config(config_path)
        if not self.cfg:
            messagebox.showerror('Config', 'Failed to read config.json')
            return
        
        # Get parameters from GUI
        try:
            strategy_cfg.tp_percent = float(self.tp_var.get())
            strategy_cfg.sl_percent = float(self.sl_var.get())
            strategy_cfg.ema_short = int(self.ema_short_var.get())
            strategy_cfg.ema_long = int(self.ema_long_var.get())
        except Exception as e:
            messagebox.showerror('Params', f'Invalid parameter: {e}')
            return
        
        # Update UI
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_var.set('Running')
        self.safe_log('Starting worker...')
        
        # Start worker
        self.cmd_queue = queue.Queue()
        self.worker = Worker(self, self.cfg, self.cmd_queue)
        self.worker.start()
    
    def stop(self):
        """
        Stop worker
        """
        if self.worker:
            self.cmd_queue.put('stop')
            self.worker.stop()
            self.worker = None
        
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_var.set('Stopped')
        self.safe_log('Stopped by user')


def on_closing(app, root):
    """
    Handle window closing
    
    Args:
        app: GUI object
        root: Tkinter window
    """
    if app.worker:
        if messagebox.askyesno('Exit', 'Worker is running. Stop and exit?'):
            app.stop()
            root.destroy()
    else:
        root.destroy()
