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

from .utils import logger, DBUS_SERVICE_NAME, DBUS_PATH_BASE, PRODUCT_NAME, PRODUCT_ID, DEVICE_TYPE

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

    def __init__(self, inverter, device_instance: int = 0):
        """
        Initialize D-Bus helper.

        Sets up D-Bus paths and prepares for service initialization.

        Args:
            inverter: Inverter instance (MPP Solar inverter) to monitor
            device_instance: Device instance number for uniqueness
        """
        self.inverter = inverter  # Reference to the inverter instance
        self.device_instance = device_instance  # Device instance for uniqueness
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
            '/Mgmt/ProcessName': {'value': 'dbus-mppsolar', 'text': 'Process Name'},  # Process name for management
            '/Mgmt/ProcessVersion': {'value': '1.0.0', 'text': 'Process Version'},    # Process version
            '/Mgmt/Connection': {'value': 'Serial USB', 'text': 'Connection Type'},   # Connection type
        }

    def setup_vedbus(self) -> bool:
        """
        Setup D-Bus service.

        Creates and initializes the VeDbusService with all required paths.
        This method must be called before publishing data.

        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            # Create the D-Bus service with the configured service name
            self.dbus_service = VeDbusService(DBUS_SERVICE_NAME)

            # Add all defined D-Bus paths to the service
            for path, info in self._dbus_paths.items():
                self.dbus_service.add_path(path, info['value'], description=info['text'])

            logger.info(f"D-Bus service {DBUS_SERVICE_NAME} initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to setup D-Bus service: {e}")
            return False

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