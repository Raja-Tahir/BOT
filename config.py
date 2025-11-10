import json
import os

CONFIG_FILE = "config.json"

default_config = {
    "api_key": "",
    "api_secret": "",
    "telegram_token": "",
    "telegram_chat_id": "",
    "check_interval": 5,
    "use_indicators": {
        "rsi": True,
        "macd": True,
        "ema": True,
        "bb": True
    },
    "stop_loss": 0.02,
    "take_profit": 0.05,
    "reverse_check_mode": False  # ✅ New flag for reverse data testing
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(default_config)
        return default_config

    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        save_config(default_config)
        return default_config


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


def update_config(key, value):
    config = load_config()
    config[key] = value
    save_config(config)


def reset_to_default():
    save_config(default_config)


def toggle_reverse_check(enable: bool):
    """Enable or disable reverse check mode from GUI."""
    config = load_config()
    config["reverse_check_mode"] = enable
    save_config(config)
