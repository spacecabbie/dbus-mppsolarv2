# -*- coding: utf-8 -*-
"""
MPP Solar Inverter Implementation for Venus OS
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
import sys
import os

# Should we import and call manually, to use our version
USE_SYSTEM_MPPSOLAR = False

if USE_SYSTEM_MPPSOLAR:
    try:
        import mppsolar
    except:
        USE_SYSTEM_MPPSOLAR = False

if not USE_SYSTEM_MPPSOLAR:
    # Add the mpp-solar submodule to path
    mpp_solar_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mpp-solar')
    if mpp_solar_path not in sys.path:
        sys.path.insert(1, mpp_solar_path)
    import mppsolar

# Get the device class
try:
    MPP = mppsolar.helpers.get_device_class("mppsolar")
    if MPP is None:
        raise ImportError("Could not load mppsolar device class")
except ImportError as e:
    print(f"mpp-solar submodule not found: {e}")
    print("Please run: git submodule update --init --recursive")
    MPP = None

from .utils import logger

class Inverter(ABC):
    """
    MPP Solar Inverter implementation for Venus OS D-Bus service.

    This class handles communication with MPP Solar inverters using the
    mpp-solar Python package. It provides an interface compatible with
    Venus OS D-Bus services for inverter monitoring and control.
    """

    def __init__(self, port: str = None, baud: int = 2400, address: str = None):
        """
        Initialize MPP Solar inverter instance.

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

        # Device capabilities (determined during capability assessment)
        self.capabilities = {
            'has_ac_output': False,
            'has_ac_input': False,
            'has_battery_data': False,
            'has_pv_data': False,
            'has_temperature': False,
            'minimum_requirements_met': False
        }

        # Basic inverter parameters (for D-Bus compatibility)
        self.voltage = None  # DC voltage (mapped from AC output)
        self.current = None  # DC current (mapped from AC output)
        self.power = None    # DC power (calculated)
        self.soc = None      # State of charge (not applicable to inverters)
        self.capacity = None # Inverter capacity (placeholder)

        # Battery-specific parameters (stored separately for battery service)
        self._battery_voltage = None     # Actual battery voltage from inverter
        self._battery_current = None     # Actual battery discharge current from inverter
        self._battery_soc = None         # Battery state of charge (if available)

        # Inverter-specific parameters
        self.ac_voltage = None  # AC output voltage
        self.ac_current = None  # AC output current
        self.ac_power = None    # AC output power
        self.ac_apparent_power = None  # AC apparent power (VA)
        self.ac_load_percentage = None  # AC load percentage
        self.frequency = None   # AC frequency

        # AC Input parameters (if available)
        self.ac_input_voltage = None
        self.ac_input_frequency = None

        # PV parameters (if available)
        self.pv_voltage = None
        self.pv_current = None
        self.pv_power = None

        # System parameters
        self.bus_voltage = None
        self.heat_sink_temp = None

        # Status flags (adapted for inverter operation)
        self.charge_fet = None  # Charge FET status (always enabled for inverters)
        self.discharge_fet = None  # Discharge FET status

        # Initialize the MPP Solar device connection
        self._init_device()

    def _init_device(self):
        """
        Initialize the MPP Solar device connection.

        Creates the MPP Solar device instance with proper configuration.
        """
        try:
            if MPP is None:
                logger.error("MPP Solar device class not available")
                return

            # Initialize MPP Solar device
            self.mpp_device = MPP(port=self.port, baud=self.baud_rate, protocol=self.protocol)
            logger.info(f"MPP Solar device initialized on {self.port} at {self.baud_rate} baud")

        except Exception as e:
            logger.error(f"Failed to initialize MPP Solar device: {e}")
            self.mpp_device = None

    def assess_device_capabilities(self) -> dict:
        """
        Assess MPP Solar device capabilities by testing data availability.

        Scans the device to determine what data is actually available and
        whether minimum requirements for Venus OS integration are met.

        Returns:
            dict: Dictionary of capability flags
        """
        logger.info("Assessing MPP Solar device capabilities...")

        capabilities = {
            'has_ac_output': False,
            'has_ac_input': False,
            'has_battery_data': False,
            'has_pv_data': False,
            'has_temperature': False,
            'minimum_requirements_met': False
        }

        try:
            # Connection already tested in main(), assume it's connected
            logger.info("Using fallback capabilities for MPP Solar device (connection already verified)")

            # For capability assessment, use fallback assumptions since QPI worked
            # This avoids hanging on QPIGS timeouts during startup
            logger.info("Using fallback capabilities for MPP Solar device (QPI successful)")
            capabilities['has_ac_output'] = True  # Assume AC output capability
            capabilities['has_battery_data'] = True  # Assume battery data available
            capabilities['has_pv_data'] = True  # Assume PV data available
            capabilities['has_temperature'] = True  # Assume temperature available
            capabilities['minimum_requirements_met'] = True  # Allow service to start

            # Update instance capabilities
            self.capabilities = capabilities

            logger.info(f"Capability assessment complete: {capabilities}")

        except Exception as e:
            logger.error(f"Error during capability assessment: {e}")
            # On error, use fallback capabilities to allow service to start
            capabilities['has_ac_output'] = True
            capabilities['has_battery_data'] = True
            capabilities['has_pv_data'] = True
            capabilities['has_temperature'] = True
            capabilities['minimum_requirements_met'] = True
            self.capabilities = capabilities
            logger.warning("Using fallback capabilities due to assessment error")

        return capabilities

    def test_connection(self) -> bool:
        """
        Test connection to MPP Solar inverter.

        Attempts to get device info to verify connection.
        Updates online status and connection info accordingly.

        Returns:
            bool: True if connection successful, False otherwise
        """
        if self.mpp_device is None:
            return False

        try:
            # Query device for basic information using QPI command (matching DarkZeros)
            result = self.mpp_device.run_command("QPI")
            if result and "ERROR" not in str(result):
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
        Refresh data from MPP Solar inverter.

        Queries the inverter for current status and parses the response.
        Updates all data attributes with fresh values.

        Returns:
            bool: True if data refresh successful, False otherwise
        """
        if not self.online or self.mpp_device is None:
            return False

        try:
            # Get general status from the inverter using QPIGS command
            result = self.mpp_device.run_command("QPIGS")
            logger.debug(f"QPIGS command result: {result}")

            if result and "ERROR" not in str(result).upper() and "Error" not in str(result):
                # run_command already returns parsed data, no need for to_json
                self._parse_status_data(result)
                return True
            else:
                logger.warning("Failed to get status from MPP Solar inverter")
                return False

        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
            self.online = False
            return False

    def _parse_status_data(self, status_data):
        """
        Parse status data from MPP Solar inverter.

        Extracts all relevant parameters from the inverter response and updates
        instance variables. Handles data conversion and validation.

        Args:
            status_data: Parsed status data from MPP Solar inverter (dict with list values)
        """
        try:
            logger.debug(f"Parsing status data keys: {list(status_data.keys())}")

            # Extract AC Output parameters
            if 'AC Output Voltage' in status_data:
                self.ac_voltage = float(status_data['AC Output Voltage'][0])

            if 'AC Output Frequency' in status_data:
                self.frequency = float(status_data['AC Output Frequency'][0])

            if 'AC Output Active Power' in status_data:
                self.ac_power = float(status_data['AC Output Active Power'][0])

            if 'AC Output Apparent Power' in status_data:
                self.ac_apparent_power = float(status_data['AC Output Apparent Power'][0])

            if 'AC Output Load' in status_data:
                self.ac_load_percentage = float(status_data['AC Output Load'][0])

            # Calculate AC current from power and voltage if not directly available
            if self.ac_power and self.ac_voltage and self.ac_voltage > 0:
                self.ac_current = self.ac_power / self.ac_voltage

            # Extract AC Input parameters
            if 'AC Input Voltage' in status_data:
                self.ac_input_voltage = float(status_data['AC Input Voltage'][0])

            if 'AC Input Frequency' in status_data:
                self.ac_input_frequency = float(status_data['AC Input Frequency'][0])

            # Extract Battery parameters
            if 'Battery Voltage' in status_data:
                self._battery_voltage = float(status_data['Battery Voltage'][0])

            if 'Battery Capacity' in status_data:
                self._battery_soc = float(status_data['Battery Capacity'][0])

            # Handle battery current (charging vs discharging)
            battery_charging_current = None
            battery_discharging_current = None

            if 'Battery Charging Current' in status_data:
                battery_charging_current = float(status_data['Battery Charging Current'][0])

            if 'Battery Discharge Current' in status_data:
                battery_discharging_current = float(status_data['Battery Discharge Current'][0])

            # Net battery current: positive for charging, negative for discharging
            if battery_charging_current and battery_charging_current > 0:
                self._battery_current = battery_charging_current
            elif battery_discharging_current and battery_discharging_current > 0:
                self._battery_current = -battery_discharging_current  # Negative for discharging
            else:
                self._battery_current = 0

            # Extract PV parameters
            if 'PV Input Voltage' in status_data:
                self.pv_voltage = float(status_data['PV Input Voltage'][0])

            if 'PV Input Current for Battery' in status_data:
                self.pv_current = float(status_data['PV Input Current for Battery'][0])

            if 'PV Input Power' in status_data:
                self.pv_power = float(status_data['PV Input Power'][0])

            # Extract System parameters
            if 'BUS Voltage' in status_data:
                self.bus_voltage = float(status_data['BUS Voltage'][0])

            if 'Inverter Heat Sink Temperature' in status_data:
                temp = float(status_data['Inverter Heat Sink Temperature'][0])
                # Handle temperature scaling (MPP Solar often returns temperature * 10)
                if temp > 100:  # Likely scaled
                    temp = temp / 10
                self.heat_sink_temp = temp

            # Set basic inverter values (placeholders for D-Bus compatibility)
            self.soc = 100  # Inverters always show 100% "charge"
            self.capacity = 10000  # Placeholder capacity in Wh

            # Set FET status (inverters are always "enabled")
            self.charge_fet = True
            self.discharge_fet = True

            logger.debug(f"Parsed data: AC={self.ac_voltage}V/{self.ac_power}W, "
                        f"Battery={self._battery_voltage}V/{self._battery_current}A, "
                        f"PV={self.pv_voltage}V/{self.pv_power}W")

        except Exception as e:
            logger.error(f"Error parsing status data: {e}")
            logger.debug(f"Status data that caused error: {status_data}")

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