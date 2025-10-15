# -*- coding: utf-8 -*-
"""
Utilities for dbus-mppsolar
Based on dbus-serialbattery utils.py

This code was generated with the help of Grok XAI
"""

import logging
import configparser
from pathlib import Path
from typing import Any, Union

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MPP-Solar")

PATH_CONFIG_DEFAULT = "config.default.ini"
PATH_CONFIG_USER = "config.ini"

config = configparser.ConfigParser()
path = Path(__file__).parents[0]
default_config_file_path = path.joinpath(PATH_CONFIG_DEFAULT).absolute().__str__()
custom_config_file_path = path.joinpath(PATH_CONFIG_USER).absolute().__str__()
config.read([default_config_file_path, custom_config_file_path])

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

# MPP Solar specific constants - read from config
# Default values for MPP Solar device communication
PORT = get_config_value('PORT', default='/dev/ttyUSB0')
BAUD_RATE = int(get_config_value('BAUD_RATE', default=2400))
PROTOCOL = get_config_value('PROTOCOL', default='PI30')
TIMEOUT = int(get_config_value('TIMEOUT', default=5))
POLL_INTERVAL = int(get_config_value('POLL_INTERVAL', default=1000))

# D-Bus constants
# D-Bus service identification for Venus OS integration
DBUS_SERVICE_NAME = get_config_value('SERVICE_NAME', 'DBUS', 'com.victronenergy.inverter')
DEVICE_INSTANCE = int(get_config_value('DEVICE_INSTANCE', 'DBUS', 0))

# Venus OS constants
# Product identification for Venus OS device recognition
PRODUCT_NAME = get_config_value('PRODUCT_NAME', 'VENUS', 'MPP Solar Inverter')
PRODUCT_ID = int(get_config_value('PRODUCT_ID', 'VENUS', '0xBFFF'), 16)
DEVICE_TYPE = int(get_config_value('DEVICE_TYPE', 'VENUS', '0xFFFF'), 16)

# Legacy constants for backward compatibility
DEFAULT_PORT = PORT
DEFAULT_BAUD_RATE = BAUD_RATE
DEFAULT_PROTOCOL = PROTOCOL
DEFAULT_TIMEOUT = TIMEOUT
DEFAULT_POLL_INTERVAL = POLL_INTERVAL

# D-Bus path base
DBUS_PATH_BASE = f'/Inverter/{DEVICE_INSTANCE}'


# Publish config variables to dbus
def publish_config_variables(dbusservice):
    """
    Publish configuration variables to D-Bus.

    Adds all configuration constants to D-Bus paths under /Info/Config/
    for monitoring and debugging purposes.

    Args:
        dbusservice: D-Bus service instance to publish to
    """
    config_vars = {
        'PORT': PORT,
        'BAUD_RATE': BAUD_RATE,
        'PROTOCOL': PROTOCOL,
        'TIMEOUT': TIMEOUT,
        'POLL_INTERVAL': POLL_INTERVAL,
        'DBUS_SERVICE_NAME': DBUS_SERVICE_NAME,
        'DEVICE_INSTANCE': DEVICE_INSTANCE,
        'PRODUCT_NAME': PRODUCT_NAME,
        'PRODUCT_ID': PRODUCT_ID,
        'DEVICE_TYPE': DEVICE_TYPE,
    }

    for variable, value in config_vars.items():
        if (
            isinstance(value, float)
            or isinstance(value, int)
            or isinstance(value, str)
        ):
            dbusservice.add_path(f"/Info/Config/{variable}", value)