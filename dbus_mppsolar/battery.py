# -*- coding: utf-8 -*-
"""
MPP Solar Battery Implementation for Venus OS
Based on dbus-serialbattery battery.py
Adapted to use mpp-solar package for PI30 inverters

This code was generated with the help of Grok XAI
"""

from typing import Union, Tuple, List, Dict, Callable
import logging
import time
import configparser
from abc import ABC, abstractmethod

# Import mpp-solar package for inverter communication
try:
    import sys
    import os
    # Add mpp-solar submodule to path (the package is inside mpp-solar/mppsolar/)
    mpp_solar_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mpp-solar', 'mppsolar')
    if mpp_solar_path not in sys.path:
        sys.path.insert(0, mpp_solar_path)
    from mppsolar.helpers import get_device_class
    # Get the mppsolar device class
    MPP = get_device_class("mppsolar")
    if MPP is None:
        raise ImportError("Could not load mppsolar device class")
except ImportError:
    print("mpp-solar submodule not found. Please run: git submodule update --init --recursive")
    MPP = None

from .utils import logger

class Battery(ABC):
    """
    MPP Solar Battery implementation for Venus OS D-Bus service.

    This class handles communication with MPP Solar inverters using the
    mpp-solar Python package. It adapts the interface to work with Venus OS
    D-Bus service, treating the inverter as a "battery" for compatibility.
    """

    def __init__(self, port: str = None, baud: int = 2400, address: str = None):
        """
        Initialize MPP Solar battery instance.

        Sets up connection parameters and initializes the MPP Solar device.

        Args:
            port: Serial port path (default: /dev/ttyUSB0)
            baud: Baud rate for serial communication (default: 2400)
            address: Device address (optional)
        """
        self.port = port or "/dev/ttyUSB0"  # Serial port for inverter connection
        self.baud_rate = baud  # Communication baud rate
        self.address = address  # Device address (if applicable)
        self.protocol = "PI30"  # MPP Solar protocol version

        # MPP Solar device instance (initialized in _init_device)
        self.mpp_device = None

        # Connection status
        self.online = False  # Whether device is connected and responding
        self.connection_info = "Initializing..."  # Status message

        # Device identification
        self.serial_number = None  # Device serial number for uniqueness

        # Basic battery parameters (adapted for inverter)
        self.voltage = None  # DC voltage (not directly applicable to inverters)
        self.current = None  # DC current
        self.power = None  # DC power
        self.soc = None  # State of charge (not applicable to inverters)
        self.capacity = None  # Battery capacity (placeholder)

        # Inverter-specific parameters
        self.ac_voltage = None  # AC output voltage
        self.ac_current = None  # AC output current
        self.ac_power = None  # AC output power
        self.frequency = None  # AC frequency

        # Status flags (adapted for inverter operation)
        self.charge_fet = None  # Charge FET status (always enabled for inverters)
        self.discharge_fet = None  # Discharge FET status

        # Initialize the MPP Solar device connection
        self._init_device()

    def _init_device(self):
        """
        Initialize MPP Solar device connection.

        Creates an MPP instance with the configured parameters.
        Logs success or failure of initialization.
        """
        if MPP is None:
            logger.error("MPP Solar package not available")
            return

        try:
            # Create MPP Solar device instance
            self.mpp_device = MPP(device=self.port,
                                baud=self.baud_rate,
                                protocol=self.protocol)
            logger.info(f"MPP Solar device initialized on {self.port}")
        except Exception as e:
            logger.error(f"Failed to initialize MPP Solar device: {e}")
            self.mpp_device = None

    def test_connection(self) -> bool:
        """
        Test connection to MPP Solar device.

        Attempts to get device info to verify connection.
        Updates online status and connection info accordingly.

        Returns:
            bool: True if connection successful, False otherwise
        """
        if self.mpp_device is None:
            return False

        try:
            # Query device for basic information using QPI command
            result = self.mpp_device.run_command("QPI")
            if result and not isinstance(result, dict) or "ERROR" not in result:
                self.online = True
                self.connection_info = f"Connected to {self.port}"
                # Store serial number if available
                if isinstance(result, dict) and 'Protocol ID' in result:
                    self.serial_number = result.get('Protocol ID', [None])[0]
                logger.info("MPP Solar device connection successful")
                return True
            else:
                self.online = False
                self.connection_info = "Connection failed"
                return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            self.online = False
            self.connection_info = f"Error: {str(e)}"
            return False

    def refresh_data(self) -> bool:
        """
        Refresh data from MPP Solar device.

        Queries the device for current status and parses the response.
        Updates all data attributes with fresh values.

        Returns:
            bool: True if data refresh successful, False otherwise
        """
        if not self.online or self.mpp_device is None:
            return False

        try:
            # Get general status from the inverter using QPIGS command
            status = self.mpp_device.run_command("QPIGS")

            if status and not isinstance(status, dict) or "ERROR" not in status:
                # Parse and update data from status response
                self._parse_status_data(status)
                return True
            else:
                logger.warning("Failed to get status from MPP Solar device")
                return False

        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
            self.online = False
            return False

    def _parse_status_data(self, status_data):
        """
        Parse status data from MPP Solar device.

        Extracts relevant parameters from the device response and updates
        instance variables. Handles data conversion and validation.

        Args:
            status_data: Raw status data from MPP Solar device
        """
        try:
            # Extract AC parameters from status data
            # Note: QPIGS returns a dictionary with descriptive keys
            if 'AC Output Voltage' in status_data:
                self.ac_voltage = float(status_data['AC Output Voltage'][0])

            if 'AC Output Frequency' in status_data:
                self.frequency = float(status_data['AC Output Frequency'][0])

            if 'AC Output Active Power' in status_data:
                self.ac_power = float(status_data['AC Output Active Power'][0])

            # Calculate AC current from power and voltage if available
            if self.ac_power and self.ac_voltage:
                self.ac_current = self.ac_power / self.ac_voltage

            # For inverters, DC values are mapped from AC for compatibility
            # Inverters don't have traditional batteries, so we use AC values
            if self.ac_voltage:
                self.voltage = self.ac_voltage  # DC voltage equivalent

            if self.ac_current:
                self.current = self.ac_current  # DC current equivalent

            if self.ac_power:
                self.power = self.ac_power  # DC power equivalent

            # Set basic battery values (placeholders for D-Bus compatibility)
            self.soc = 100  # Inverters always show 100% "charge"
            self.capacity = 10000  # Placeholder capacity in Wh

            # Set FET status (inverters are always "enabled")
            self.charge_fet = True
            self.discharge_fet = True

        except Exception as e:
            logger.error(f"Error parsing status data: {e}")

    def get_settings(self) -> bool:
        """
        Get device settings.

        Not applicable for inverters, but required for interface compatibility.

        Returns:
            bool: Always True
        """
        return True

    def unique_identifier(self) -> str:
        """
        Return unique identifier for this device.

        Used for device identification in Venus OS.
        Prefers serial number for uniqueness, falls back to port/protocol.

        Returns:
            str: Unique identifier string
        """
        if self.serial_number:
            return f"mppsolar_{self.serial_number}"
        return f"mppsolar_{self.port}_{self.protocol}"

    def connection_name(self) -> str:
        """
        Return connection name for display.

        Human-readable connection description.

        Returns:
            str: Connection name string
        """
        return f"MPP Solar {self.protocol} on {self.port}"

    def custom_name(self) -> str:
        """
        Return custom display name.

        Used in Venus OS interface.

        Returns:
            str: Custom display name
        """
        return f"MPP Solar {self.protocol} Inverter"

    def product_name(self) -> str:
        """
        Return product name.

        Official product name for identification.

        Returns:
            str: Product name string
        """
        return f"MPP Solar {self.protocol} Inverter"

    def use_callback(self, callback: Callable) -> bool:
        """
        MPP Solar devices don't support callbacks.

        Required for interface compatibility.

        Args:
            callback: Callback function (ignored)

        Returns:
            bool: Always False
        """
        return False

    def get_allow_to_charge(self) -> bool:
        """
        Check if device allows charging.

        Inverters can always "charge" (generate power).

        Returns:
            bool: Always True for inverters
        """
        return True

    def get_allow_to_discharge(self) -> bool:
        """
        Check if device allows discharging.

        Inverters can always discharge (provide power).

        Returns:
            bool: Always True for inverters
        """
        return True

    def validate_data(self) -> bool:
        """
        Validate that we have reasonable data.

        Checks if AC voltage is within expected range.

        Returns:
            bool: True if data is valid, False otherwise
        """
        if self.ac_voltage is None:
            return False
        if self.ac_voltage < 180 or self.ac_voltage > 280:
            logger.warning(f"AC voltage out of range: {self.ac_voltage}V")
            return False
        return True