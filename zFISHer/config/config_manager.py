import os
import json
import shutil



CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "config.json")

##########
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".zFISHer")
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.json")
DEFAULT_CONFIG_SOURCE = "/hpcf/authorized_apps/rhel8_apps/zfisher/vendor/zFISHer/zFISHer/config/config.json"

# Ensure the config directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)

# Copy the default config if it doesn't exist
if not os.path.exists(CONFIG_FILE_PATH):
    shutil.copy(DEFAULT_CONFIG_SOURCE, CONFIG_FILE_PATH)
###########


def load_config():
    """Load the configuration from the JSON file."""
    if not os.path.exists(CONFIG_FILE_PATH):
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE_PATH}")
    
    with open(CONFIG_FILE_PATH, "r") as config_file:
        return json.load(config_file)

def save_config(config):
    """Save the updated configuration to the JSON file."""
    with open(CONFIG_FILE_PATH, "w") as config_file:
        json.dump(config, config_file, indent=4)

def get_config_value(key):
    """Retrieve a specific configuration value."""
    config = load_config()
    return config.get(key)

def set_config_value(key, value):
    """Update a specific configuration value and save it."""
    config = load_config()
    
    # Ensure the value is stored as a float if it's a float
    if isinstance(value, float):
        config[key] = float(value)
    else:
        config[key] = value

    save_config(config)
