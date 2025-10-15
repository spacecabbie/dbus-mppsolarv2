# -*- coding: utf-8 -*-
"""
D-Bus helper for MPP Solar inverters
Based on dbus-serialbattery dbushelper.py
Adapted for inverter D-Bus interface

This code was generated with the help of Grok XAI
"""

import logging
import sys
import os
from typing import Dict, Any

# Add current directory to path for module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Add path to velib_python
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "..", "ext", "velib_python"))

from .utils import logger, DBUS_SERVICE_NAME, DBUS_PATH_BASE, PRODUCT_NAME, PRODUCT_ID, DEVICE_TYPE, DEVICE_INSTANCE

try:
    import dbus
    import gi.repository.GObject as gobject
    from vedbus import VeDbusService
except ImportError as e:
    logger.error(f"D-Bus dependencies not available: {e}")
    logger.error("Please install dbus-python and gobject")
    sys.exit(1)

class DbusHelper:
    """
    D-Bus helper class for MPP Solar inverters.

    This class manages the D-Bus interface for MPP Solar inverters in Venus OS.
    It publishes inverter data to D-Bus paths that Venus OS can monitor and display.
    Based on the dbus-serialbattery DbusHelper but adapted for inverter data.
    """

    def __init__(self, inverter, device_instance: int = None):
        """
        Initialize D-Bus helper.

        Sets up D-Bus paths and prepares for service initialization.

        Args:
            inverter: Inverter instance (MPP Solar inverter) to monitor
            device_instance: Device instance number for uniqueness (if None, uses config value)
        """
        self.inverter = inverter  # Reference to the inverter instance

        # Use provided instance or get from config
        if device_instance is None:
            self.device_instance = DEVICE_INSTANCE
        else:
            self.device_instance = device_instance

        # Construct the full service name with instance
        self.service_name = f"{DBUS_SERVICE_NAME}_{self.device_instance}"

        self.dbus_service = None  # VeDbusService instance
        self._paths: Dict[str, Any] = {}  # Dictionary of D-Bus paths

        # Define D-Bus paths for inverter data
        # These paths follow Venus OS D-Bus API conventions
        self._dbus_paths = {
            '/Ac/Out/L1/V': {'value': None, 'text': 'AC Voltage'},  # AC output voltage
            '/Ac/Out/L1/I': {'value': None, 'text': 'AC Current'},  # AC output current
            '/Ac/Out/L1/P': {'value': None, 'text': 'AC Power'},    # AC output power
            '/Ac/Out/L1/F': {'value': None, 'text': 'AC Frequency'}, # AC frequency
            '/Dc/0/Voltage': {'value': None, 'text': 'DC Voltage'},  # DC input voltage
            '/Dc/0/Current': {'value': None, 'text': 'DC Current'},  # DC input current
            '/Dc/0/Power': {'value': None, 'text': 'DC Power'},      # DC input power
            '/DeviceInstance': {'value': self.device_instance, 'text': 'Device Instance'}, # Device instance ID
            '/ProductId': {'value': PRODUCT_ID, 'text': 'Product ID'},   # Product identifier
            '/ProductName': {'value': PRODUCT_NAME, 'text': 'Product Name'}, # Product name
            '/FirmwareVersion': {'value': '1.0.0', 'text': 'Firmware Version'}, # Firmware version
            '/Connected': {'value': 0, 'text': 'Connected'},  # Connection status (0/1)
            '/Status': {'value': 0, 'text': 'Status'},        # Service status (0=Offline, 1=Running)
            '/State': {'value': 0, 'text': 'Inverter State'}, # Inverter operational state (0=Off, 9=Inverting)
            '/Mgmt/ProcessName': {'value': 'dbus-mppsolar', 'text': 'Process Name'},  # Process name for management
            '/Mgmt/ProcessVersion': {'value': '1.0.0', 'text': 'Process Version'},    # Process version
            '/Mgmt/Connection': {'value': 'Serial USB', 'text': 'Connection Type'},   # Connection type
        }

    def setup_vedbus(self, publish_config: bool = True) -> bool:
        """
        Setup D-Bus service.

        Creates and initializes the VeDbusService with all required paths.
        This method must be called before publishing data.

        Args:
            publish_config: Whether to publish configuration variables to D-Bus

        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            # Create the D-Bus service with register=False (don't register yet)
            self.dbus_service = VeDbusService(self.service_name, register=False)

            # Add all defined D-Bus paths to the service
            for path, info in self._dbus_paths.items():
                self.dbus_service.add_path(path, info['value'], description=info['text'])

            # Publish config variables if requested
            if publish_config:
                self._publish_config_variables()

            # Now register the service after all paths are added
            self.dbus_service.register()

            logger.info(f"D-Bus service {self.service_name} initialized and registered")
            return True

        except Exception as e:
            logger.error(f"Failed to setup D-Bus service: {e}")
            return False

    def _publish_config_variables(self) -> None:
        """
        Publish configuration variables to D-Bus.

        Adds all configuration constants to D-Bus paths under /Info/Config/
        for monitoring and debugging purposes.
        """
        from .utils import PORT, BAUD_RATE, PROTOCOL, TIMEOUT, POLL_INTERVAL
        from .utils import DBUS_SERVICE_NAME, DEVICE_INSTANCE, PRODUCT_NAME, PRODUCT_ID, DEVICE_TYPE

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
                self.dbus_service.add_path(f"/Info/Config/{variable}", value)

    def publish_inverter(self) -> bool:
        """
        Publish inverter data to D-Bus.

        Updates all D-Bus paths with current data from the inverter.
        Only publishes non-None values to avoid overwriting with invalid data.

        Returns:
            bool: True if publishing successful, False otherwise
        """
        try:
            # Update AC output parameters
            if self.inverter.ac_voltage is not None:
                self.dbus_service['/Ac/Out/L1/V'] = self.inverter.ac_voltage

            if self.inverter.ac_current is not None:
                self.dbus_service['/Ac/Out/L1/I'] = self.inverter.ac_current

            if self.inverter.ac_power is not None:
                self.dbus_service['/Ac/Out/L1/P'] = self.inverter.ac_power

            if self.inverter.frequency is not None:
                self.dbus_service['/Ac/Out/L1/F'] = self.inverter.frequency

            # Update DC input parameters (mapped from AC for compatibility)
            if self.inverter.voltage is not None:
                self.dbus_service['/Dc/0/Voltage'] = self.inverter.voltage

            if self.inverter.current is not None:
                self.dbus_service['/Dc/0/Current'] = self.inverter.current

            if self.inverter.power is not None:
                self.dbus_service['/Dc/0/Power'] = self.inverter.power

            # Update connection and status flags
            self.dbus_service['/Connected'] = 1 if self.inverter.online else 0
            self.dbus_service['/Status'] = 1 if self.inverter.online else 0
            # Set inverter state: 9=Inverting (normal operation), 0=Off
            self.dbus_service['/State'] = 9 if self.inverter.online else 0

            return True

        except Exception as e:
            logger.error(f"Error publishing data to D-Bus: {e}")
            return False

    def publish_dbus(self) -> bool:
        """
        Alias for publish_inverter for compatibility.

        Some parts of the codebase may call this method name.
        Delegates to publish_inverter().

        Returns:
            bool: True if publishing successful, False otherwise
        """
        return self.publish_inverter()

    def update_process_name(self, name: str) -> bool:
        """
        Update the process name in D-Bus.

        Args:
            name: New process name to set

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            self.dbus_service['/Mgmt/ProcessName'] = name
            self._dbus_paths['/Mgmt/ProcessName']['value'] = name
            logger.debug(f"Updated process name to: {name}")
            return True
        except Exception as e:
            logger.error(f"Error updating process name: {e}")
            return False

    def update_process_version(self, version: str) -> bool:
        """
        Update the process version in D-Bus.

        Args:
            version: New process version to set

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            self.dbus_service['/Mgmt/ProcessVersion'] = version
            self._dbus_paths['/Mgmt/ProcessVersion']['value'] = version
            logger.debug(f"Updated process version to: {version}")
            return True
        except Exception as e:
            logger.error(f"Error updating process version: {e}")
            return False

    def update_connection_type(self, connection: str) -> bool:
        """
        Update the connection type in D-Bus.

        Args:
            connection: New connection type to set (e.g., 'Serial USB', 'USB HID', 'Bluetooth')

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            self.dbus_service['/Mgmt/Connection'] = connection
            self._dbus_paths['/Mgmt/Connection']['value'] = connection
            logger.debug(f"Updated connection type to: {connection}")
            return True
        except Exception as e:
            logger.error(f"Error updating connection type: {e}")
            return False