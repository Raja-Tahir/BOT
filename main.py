"""
main.py

Description:
Main file to start the program

Usage:
    python main.py

Requirements:
    pip install ccxt pandas ta requests
"""

import tkinter as tk
from gui import ScalperGUI, on_closing


def main():
    """
    Start AI Scalping Bot GUI
    """
    # Create Tkinter main window
    root = tk.Tk()
    
    # Create GUI object
    app = ScalperGUI(root)
    
    # Set window close handler
    root.protocol('WM_DELETE_WINDOW', lambda: on_closing(app, root))
    
    # Start GUI
    root.mainloop()


if __name__ == '__main__':
    print("=" * 50)
    print("AI Scalping Bot Pro")
    print("=" * 50)
    print("Starting GUI...")
    print("Make sure config.json is in the same folder")
    print("=" * 50)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
