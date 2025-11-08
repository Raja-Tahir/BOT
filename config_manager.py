"""
config_manager.py

Description:
Configuration file loader, Telegram messaging, and log directory setup.

Features:
- Load settings from config.json
- Send messages via Telegram bot
- Create and manage log directories
"""

import os
import json
import requests

# Application directory and log folder
APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(APP_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "signals.csv")

DEFAULT_CONFIG_PATH = os.path.join(APP_DIR, "config.json")


def load_config(path=DEFAULT_CONFIG_PATH):
    """
    Load config.json file
    
    Args:
        path: Path to config file
        
    Returns:
        dict: Config data or None if file not found
    """
    if not os.path.exists(path):
        return None
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error: Could not load config file - {e}")
        return None


def send_telegram_message(bot_token, chat_id, message):
    """
    Send message via Telegram
    
    Args:
        bot_token: Telegram bot token
        chat_id: Chat ID
        message: Message to send
        
    Returns:
        tuple: (success: bool, response: str)
    """
    if not bot_token or not chat_id:
        return False, "Telegram not configured"
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": str(chat_id),
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, data=data, timeout=30)
        if response.status_code != 200:
            return False, f"Error: {response.text}"
        return True, "Message sent successfully"
    except Exception as e:
        return False, f"Telegram error: {str(e)}"


def get_log_file_path():
    """
    Get full path to log file
    
    Returns:
        str: Path to log file
    """
    return LOG_FILE


def get_log_directory():
    """
    Get path to log directory
    
    Returns:
        str: Path to log folder
    """
    return LOG_DIR
