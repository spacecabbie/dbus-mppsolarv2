# -*- coding: utf-8 -*-
"""
Utilities for dbus-mppsolar
Based on dbus-serialbattery utils.py

This code was generated with the help of Grok XAI
"""

import logging
import configparser
import os
from typing import Any, Union

# Setup logging configuration
# Configure basic logging with timestamp, logger name, level, and message
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)  # Get logger instance for this module

# Configuration management
# Initialize ConfigParser for handling INI-style configuration files
config = configparser.ConfigParser()

# Define configuration file paths
config_file = os.path.join(os.path.dirname(__file__), 'config.ini')  # User configuration file
default_config_file = os.path.join(os.path.dirname(__file__), 'config.default.ini')  # Default configuration file

# Load default configuration first (provides fallback values)
if os.path.exists(default_config_file):
    config.read(default_config_file)

# Load user configuration if it exists (overrides defaults)
if os.path.exists(config_file):
    config.read(config_file)

def get_config_value(key: str, section: str = 'MPPSOLAR', default: Any = None) -> Any:
    """
    Get configuration value from config file.

    Retrieves a value from the specified section and key.
    Falls back to default value if key/section not found.

    Args:
        key: Configuration key to retrieve
        section: Configuration section (default: 'MPPSOLAR')
        default: Default value if key not found

    Returns:
        Configuration value or default
    """
    try:
        return config.get(section, key)
    except (configparser.NoOptionError, configparser.NoSectionError):
        return default

def get_bool_from_config(key: str, section: str = 'MPPSOLAR', default: bool = False) -> bool:
    """
    Get boolean configuration value.

    Converts string values like 'true', '1', 'yes', 'on' to boolean True.
    Handles both string and boolean inputs.

    Args:
        key: Configuration key to retrieve
        section: Configuration section (default: 'MPPSOLAR')
        default: Default boolean value if key not found

    Returns:
        Boolean value of configuration
    """
    value = get_config_value(key, section, default)
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)

def safe_number_format(value: Union[float, None], format_string: str = '{:.2f}') -> str:
    """
    Safely format numbers, handling None values.

    Formats numeric values with the given format string.
    Returns '---' for None values and string representation for invalid types.

    Args:
        value: Numeric value to format (can be None)
        format_string: Format string for numbers (default: 2 decimal places)

    Returns:
        Formatted string or '---' for None
    """
    if value is None:
        return '---'
    try:
        return format_string.format(value)
    except (ValueError, TypeError):
        return str(value)

# MPP Solar specific constants
# Default values for MPP Solar device communication
DEFAULT_PORT = '/dev/ttyUSB0'  # Default serial port for USB connection
DEFAULT_BAUD_RATE = 2400      # Default baud rate for PI30 protocol
DEFAULT_PROTOCOL = 'PI30'     # MPP Solar protocol version
DEFAULT_TIMEOUT = 5           # Default connection timeout in seconds
DEFAULT_POLL_INTERVAL = 1000  # Default polling interval in milliseconds

# D-Bus constants
# D-Bus service identification for Venus OS integration
DBUS_SERVICE_NAME = 'com.victronenergy.inverter'  # D-Bus service name
DBUS_PATH_BASE = '/Inverter/0'                    # Base path for D-Bus objects

# Venus OS constants
# Product identification for Venus OS device recognition
PRODUCT_NAME = 'MPP Solar Inverter'  # Human-readable product name
PRODUCT_ID = 0xBFFF                  # Unique product identifier (hex)
DEVICE_TYPE = 0xFFFF                 # Device type identifier