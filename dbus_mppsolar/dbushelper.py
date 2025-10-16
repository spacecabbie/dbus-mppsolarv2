# -*- coding: utf-8 -*-
"""
D-Bus helper for MPP Solar inverters
Updated for Multi/Solar Charger service architecture

This code was generated with the help of Grok XAI
"""

import logging
import sys
import os
from typing import Dict, Any, Optional

# Add current directory to path for module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Add path to velib_python
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "..", "ext", "velib_python"))

from .utils import logger, DBUS_SERVICE_NAME, SOLAR_SERVICE_NAME, BATTERY_SERVICE_NAME, PRODUCT_NAME, PRODUCT_ID, DEVICE_TYPE, DEVICE_INSTANCE

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
    D-Bus helper class for MPP Solar inverters with Multi/Solar Charger architecture.

    This class manages the D-Bus interface for MPP Solar inverters in Venus OS.
    It creates separate services for Multi (inverter/charger) and Solar Charger (PV)
    functionality based on device capabilities.
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

        # Construct service names
        self.multi_service_name = DBUS_SERVICE_NAME
        self.solar_service_name = SOLAR_SERVICE_NAME
        self.battery_service_name = f"{BATTERY_SERVICE_NAME}.mppsolar"

        # Service instances
        self.multi_service = None   # VeDbusService for Multi (inverter/charger)
        self.solar_service = None   # VeDbusService for Solar Charger (PV)
        self.battery_service = None # VeDbusService for Battery (battery monitoring)

        # Path definitions with capability requirements
        self._multi_paths: Dict[str, Dict[str, Any]] = {}  # Multi service paths
        self._solar_paths: Dict[str, Dict[str, Any]] = {}  # Solar service paths

        # Initialize path definitions
        self._define_multi_paths()
        self._define_solar_paths()
        self._define_battery_paths()

    def _define_multi_paths(self):
        """
        Define D-Bus paths for the Multi service (inverter/charger functionality).
        """
        # Core paths (always required)
        self._multi_paths = {
            # Management paths
            '/Mgmt/ProcessName': {'value': 'dbus-mppsolar', 'required': True, 'description': 'Process Name'},
            '/Mgmt/ProcessVersion': {'value': '1.0.0', 'required': True, 'description': 'Process Version'},
            '/Mgmt/Connection': {'value': 'Serial USB', 'required': True, 'description': 'Connection Type'},

            # Identification paths
            '/DeviceInstance': {'value': self.device_instance, 'required': True, 'description': 'Device Instance'},
            '/DeviceType': {'value': DEVICE_TYPE, 'required': True, 'description': 'Device Type'},
            '/ProductId': {'value': PRODUCT_ID, 'required': True, 'description': 'Product ID'},
            '/ProductName': {'value': PRODUCT_NAME, 'required': True, 'description': 'Product Name'},
            '/FirmwareVersion': {'value': '1.0.0', 'required': True, 'description': 'Firmware Version'},
            '/HardwareVersion': {'value': 0, 'required': True, 'description': 'Hardware Version'},
            '/Connected': {'value': 0, 'required': True, 'description': 'Connected'},
            '/Status': {'value': 0, 'required': True, 'description': 'Status'},

            # AC Output paths (core functionality)
            '/Ac/Out/L1/V': {'value': None, 'required': True, 'description': 'AC Output Voltage'},
            '/Ac/Out/L1/F': {'value': None, 'required': True, 'description': 'AC Output Frequency'},
            '/Ac/Out/L1/P': {'value': None, 'required': True, 'description': 'AC Output Active Power'},
            '/Ac/Out/L1/S': {'value': None, 'required': False, 'description': 'AC Output Apparent Power'},
            '/Ac/Out/L1/I': {'value': None, 'required': False, 'description': 'AC Output Current'},

            # Operating state
            '/Mode': {'value': 3, 'required': True, 'description': 'Operating Mode'},  # 3=On
            '/State': {'value': 9, 'required': True, 'description': 'Operating State'},  # 9=Inverting
        }

        # Conditional paths (added based on capabilities)
        self._multi_paths.update({
            # AC Input paths (if AC input available)
            '/Ac/In/1/L1/V': {'value': None, 'required': False, 'description': 'AC Input Voltage'},
            '/Ac/In/1/L1/F': {'value': None, 'required': False, 'description': 'AC Input Frequency'},
            '/Ac/ActiveIn/L1/V': {'value': None, 'required': False, 'description': 'Active AC Input Voltage'},
            '/Ac/ActiveIn/L1/I': {'value': None, 'required': False, 'description': 'Active AC Input Current'},
            '/Ac/ActiveIn/L1/P': {'value': None, 'required': False, 'description': 'Active AC Input Power'},
            '/Ac/ActiveIn/Connected': {'value': 0, 'required': False, 'description': 'AC Input Connected'},
            '/Ac/ActiveIn/ActiveInput': {'value': 240, 'required': False, 'description': 'Active Input'},

            # Battery paths (if battery data available)
            '/Dc/0/Voltage': {'value': None, 'required': False, 'description': 'Battery Voltage'},
            '/Dc/0/Current': {'value': None, 'required': False, 'description': 'Battery Current'},
            '/Dc/0/Power': {'value': None, 'required': False, 'description': 'Battery Power'},
            '/Dc/0/Temperature': {'value': None, 'required': False, 'description': 'Battery Temperature'},
            '/Soc': {'value': None, 'required': False, 'description': 'State of Charge'},

            # PV paths (for solar data under Multi service)
            '/Pv/0/V': {'value': None, 'required': False, 'description': 'PV Input Voltage'},
            '/Pv/0/I': {'value': None, 'required': False, 'description': 'PV Input Current'},
            '/Pv/0/P': {'value': None, 'required': False, 'description': 'PV Input Power'},
            '/Yield/Power': {'value': None, 'required': False, 'description': 'PV Power Yield'},
        })

    def _define_solar_paths(self):
        """
        Define D-Bus paths for the Solar Charger service (PV functionality).
        """
        self._solar_paths = {
            # Management paths
            '/Mgmt/ProcessName': {'value': 'dbus-mppsolar-solar', 'required': True, 'description': 'Process Name'},
            '/Mgmt/ProcessVersion': {'value': '1.0.0', 'required': True, 'description': 'Process Version'},
            '/Mgmt/Connection': {'value': 'Serial USB', 'required': True, 'description': 'Connection Type'},

            # Identification paths
            '/DeviceInstance': {'value': self.device_instance, 'required': True, 'description': 'Device Instance'},
            '/DeviceType': {'value': 0, 'required': True, 'description': 'Device Type'},
            '/ProductId': {'value': 0xA042, 'required': True, 'description': 'Product ID'},
            '/ProductName': {'value': 'MPP Solar PV Charger', 'required': True, 'description': 'Product Name'},
            '/FirmwareVersion': {'value': '1.0.0', 'required': True, 'description': 'Firmware Version'},
            '/HardwareVersion': {'value': 0, 'required': True, 'description': 'Hardware Version'},
            '/Connected': {'value': 0, 'required': True, 'description': 'Connected'},

            # PV paths (core for solar charger)
            '/Pv/0/V': {'value': None, 'required': True, 'description': 'PV Input Voltage'},
            '/Pv/0/I': {'value': None, 'required': True, 'description': 'PV Input Current'},
            '/Pv/0/P': {'value': None, 'required': True, 'description': 'PV Input Power'},
            '/Yield/Power': {'value': None, 'required': True, 'description': 'PV Power Yield'},

            # Operating state
            '/State': {'value': 0, 'required': True, 'description': 'Charger State'},
            '/MppOperationMode': {'value': 0, 'required': True, 'description': 'MPPT Operation Mode'},
            '/Mode': {'value': 1, 'required': True, 'description': 'Charger Mode'},  # 1=On
        }

    def _define_battery_paths(self):
        """
        Define D-Bus paths for the Battery service (battery monitoring).
        """
        self._battery_paths = {
            # Management paths
            '/Mgmt/ProcessName': {'value': 'dbus-mppsolar-battery', 'required': True, 'description': 'Process Name'},
            '/Mgmt/ProcessVersion': {'value': '1.0.0', 'required': True, 'description': 'Process Version'},
            '/Mgmt/Connection': {'value': 'Serial USB', 'required': True, 'description': 'Connection Type'},

            # Identification paths
            '/DeviceInstance': {'value': self.device_instance, 'required': True, 'description': 'Device Instance'},
            '/ProductId': {'value': PRODUCT_ID, 'required': True, 'description': 'Product ID'},
            '/ProductName': {'value': 'MPP Solar Battery', 'required': True, 'description': 'Product Name'},
            '/Connected': {'value': 0, 'required': True, 'description': 'Connected'},

            # Battery core paths
            '/Dc/0/Voltage': {'value': None, 'required': True, 'description': 'Battery Voltage'},
            '/Dc/0/Current': {'value': None, 'required': True, 'description': 'Battery Current'},
            '/Dc/0/Power': {'value': None, 'required': True, 'description': 'Battery Power'},
            '/Dc/0/Temperature': {'value': None, 'required': False, 'description': 'Battery Temperature'},
            '/Soc': {'value': None, 'required': True, 'description': 'State of Charge'},
            '/Info/MaxChargeCurrent': {'value': None, 'required': False, 'description': 'Maximum Charge Current'},
            '/Info/MaxDischargeCurrent': {'value': None, 'required': False, 'description': 'Maximum Discharge Current'},
        }

    def assess_capabilities_and_create_services(self) -> bool:
        """
        Assess device capabilities and create appropriate D-Bus services.

        This method evaluates what the MPP Solar device supports and creates
        the necessary D-Bus services (Multi and/or Solar Charger) based on
        device capabilities.

        Returns:
            bool: True if services created successfully, False otherwise
        """
        try:
            logger.info("Assessing device capabilities and creating D-Bus services...")

            # Get capabilities from the inverter
            capabilities = self.inverter.assess_device_capabilities()

            # Check minimum requirements
            if not capabilities.get('minimum_requirements_met', False):
                logger.error("Device does not meet minimum requirements for Venus OS integration")
                logger.error("Required: AC output capability")
                logger.error(f"Current capabilities: {capabilities}")
                return False

            logger.info(f"Device capabilities: {capabilities}")

            # Always create Multi service for inverter/charger functionality
            if not self._create_multi_service(capabilities):
                logger.error("Failed to create Multi service")
                return False

            # Create Solar Charger service if device has PV data
            # Disabled to avoid conflicts - PV data published by Multi service
            # if capabilities.get('has_pv_data', False):
            #     if not self._create_solar_service(capabilities):
            #         logger.warning("Failed to create Solar Charger service, continuing with Multi only")
            #     else:
            #         logger.info("Solar Charger service created successfully")

            # Create Battery service if device has battery data
            logger.info(f"Skipping battery service creation - battery data will be published by Multi service")
            # Note: In Venus OS, Multi inverters publish battery data directly, separate battery service not needed

            logger.info("D-Bus services created successfully")
            return True

        except Exception as e:
            logger.error(f"Error assessing capabilities and creating services: {e}")
            return False

    def _create_multi_service(self, capabilities: Dict[str, bool]) -> bool:
        """
        Create the Multi service with appropriate paths based on capabilities.

        Args:
            capabilities: Device capability assessment results

        Returns:
            bool: True if service created successfully
        """
        try:
            # Create the Multi D-Bus service (defer registration until main loop starts)
            import dbus
            # Use system bus for Multi service
            bus = dbus.SystemBus()
            self.multi_service = VeDbusService(self.multi_service_name, bus=bus, register=False)

            # Add paths based on capabilities
            for path, config in self._multi_paths.items():
                # Always add required paths
                if config['required']:
                    self.multi_service.add_path(path, config['value'], description=config['description'])
                    logger.debug(f"Added required Multi path: {path}")
                # Add conditional paths only if capability exists
                elif self._should_add_path(path, capabilities):
                    self.multi_service.add_path(path, config['value'], description=config['description'])
                    logger.debug(f"Added conditional Multi path: {path}")
                else:
                    logger.debug(f"Skipped Multi path (no capability): {path}")

            logger.info(f"Multi service created (not yet registered): {self.multi_service_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create Multi service: {e}")
            return False

    def _create_solar_service(self, capabilities: Dict[str, bool]) -> bool:
        """
        Create the Solar Charger service.

        Args:
            capabilities: Device capability assessment results

        Returns:
            bool: True if service created successfully
        """
        try:
            # Create the Solar Charger D-Bus service with separate bus to avoid conflicts
            import dbus
            # Use a separate system bus connection for Solar service
            bus = dbus.SystemBus()
            self.solar_service = VeDbusService(self.solar_service_name, bus=bus, register=False)

            # Add all solar paths (PV data is required for this service to exist)
            for path, config in self._solar_paths.items():
                self.solar_service.add_path(path, config['value'], description=config['description'])
                logger.debug(f"Added Solar path: {path}")

            logger.info(f"Solar Charger service created (not yet registered): {self.solar_service_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create Solar Charger service: {e}")
            return False

    def _create_battery_service(self, capabilities: Dict[str, bool]) -> bool:
        """
        Create the Battery service.

        Args:
            capabilities: Device capability assessment results

        Returns:
            bool: True if service created successfully
        """
        try:
            logger.info(f"Creating Battery service with name: {self.battery_service_name}")
            # Create the Battery D-Bus service
            self.battery_service = VeDbusService(self.battery_service_name, register=True)

            # Add all battery paths (battery data is required for this service to exist)
            for path, config in self._battery_paths.items():
                self.battery_service.add_path(path, config['value'], description=config['description'])
                logger.debug(f"Added Battery path: {path}")

            # Register the service
            logger.info("Registering Battery service...")
            self.battery_service.register()
            logger.info(f"Battery service registered: {self.battery_service_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create Battery service: {e}")
            import traceback
            logger.error(f"Battery service creation traceback: {traceback.format_exc()}")
            return False

    def register_services(self) -> bool:
        """
        Register all created D-Bus services on the bus.
        
        This should be called after the main loop has started to ensure
        proper D-Bus registration.
        
        Returns:
            bool: True if all services registered successfully
        """
        logger.info("Attempting to register D-Bus services...")
        try:
            success = True
            
            if self.multi_service:
                logger.info(f"Registering Multi service: {self.multi_service_name}")
                self.multi_service.register()
                logger.info(f"Multi service registered: {self.multi_service_name}")
            
            if self.solar_service:
                logger.info(f"Registering Solar service: {self.solar_service_name}")
                self.solar_service.register()
                logger.info(f"Solar Charger service registered: {self.solar_service_name}")
            
            if self.battery_service:
                logger.info(f"Registering Battery service: {self.battery_service_name}")
                self.battery_service.register()
                logger.info(f"Battery service registered: {self.battery_service_name}")
            
            logger.info("D-Bus service registration completed")
            return success
            
        except Exception as e:
            logger.error(f"Error registering services: {e}")
            return False

    def _should_add_path(self, path: str, capabilities: Dict[str, bool]) -> bool:
        """
        Determine if a conditional path should be added based on device capabilities.

        Args:
            path: D-Bus path to check
            capabilities: Device capability assessment

        Returns:
            bool: True if path should be added
        """
        # AC Output paths (apparent power, current)
        if path.startswith('/Ac/Out/L1/'):
            return capabilities.get('has_ac_output', False)

        # AC Input paths
        if path.startswith('/Ac/In/') or path.startswith('/Ac/ActiveIn/'):
            return capabilities.get('has_ac_input', False)

        # Battery paths
        if path.startswith('/Dc/0/') or path == '/Soc':
            return capabilities.get('has_battery_data', False)

        # Temperature paths
        if 'Temperature' in path:
            return capabilities.get('has_temperature', False)

        # PV paths
        if path.startswith('/Pv/') or path == '/Yield/Power':
            return capabilities.get('has_pv_data', False)

        # Custom paths - add if data might be available
        if path in ['/BusVoltage', '/Ac/Out/LoadPercentage']:
            return True  # These are custom paths, add them if they might have data

        return False

    def map_mpp_values_to_dbus(self, mpp_data: Dict[str, Any], capabilities: Dict[str, bool]) -> Dict[str, Any]:
        """
        Map MPP Solar values to D-Bus paths with proper fallbacks.

        Args:
            mpp_data: Raw MPP Solar data
            capabilities: Device capabilities

        Returns:
            dict: Mapping of D-Bus paths to values
        """
        mapping = {}

        # Multi service mappings
        if self.multi_service:
            # Core AC output
            if capabilities['has_ac_output']:
                mapping.update({
                    '/Ac/Out/L1/V': mpp_data.get('ac_voltage'),
                    '/Ac/Out/L1/F': mpp_data.get('frequency'),
                    '/Ac/Out/L1/P': mpp_data.get('ac_power'),
                    '/Ac/Out/L1/S': mpp_data.get('ac_apparent_power'),
                    '/Ac/Out/L1/I': mpp_data.get('ac_current'),
                    '/Ac/Out/LoadPercentage': mpp_data.get('ac_load_percentage'),
                })

            # AC input (conditional)
            if capabilities['has_ac_input']:
                ac_input_voltage = mpp_data.get('ac_input_voltage')
                ac_input_frequency = mpp_data.get('ac_input_frequency')
                # For ActiveIn paths, use the same values as In/1/L1 for now
                # In a real implementation, these might be different based on active input
                mapping.update({
                    '/Ac/In/1/L1/V': ac_input_voltage,
                    '/Ac/In/1/L1/F': ac_input_frequency,
                    '/Ac/ActiveIn/L1/V': ac_input_voltage,
                    '/Ac/ActiveIn/L1/I': mpp_data.get('ac_input_current'),  # May need to calculate
                    '/Ac/ActiveIn/L1/P': mpp_data.get('ac_input_power'),    # May need to calculate
                    '/Ac/ActiveIn/Connected': 1 if ac_input_voltage and ac_input_voltage > 1.0 else 0,
                    '/Ac/ActiveIn/ActiveInput': 0 if ac_input_voltage and ac_input_voltage > 1.0 else 240,
                })

            # Battery data (conditional) - published by Multi service
            if capabilities['has_battery_data']:
                # Calculate net battery current
                charge_current = mpp_data.get('battery_charging_current', 0)
                discharge_current = mpp_data.get('battery_discharge_current', 0)
                net_current = charge_current - discharge_current

                # Calculate battery power
                battery_voltage = mpp_data.get('battery_voltage')
                battery_power = battery_voltage * net_current if battery_voltage else None

                mapping.update({
                    '/Dc/0/Voltage': battery_voltage,
                    '/Dc/0/Current': net_current,
                    '/Dc/0/Power': battery_power,
                    '/Soc': mpp_data.get('battery_capacity'),
                })

            # Temperature (conditional)
            if capabilities['has_temperature']:
                temp = mpp_data.get('heat_sink_temp')
                if temp and 0 <= temp <= 100:
                    mapping['/Dc/0/Temperature'] = temp

            # System data
            mapping['/BusVoltage'] = mpp_data.get('bus_voltage')

            # Operating state for Multi service
            multi_state = self._derive_operating_state(mpp_data)
            mapping.update(multi_state)

        # PV data under Multi service
        if capabilities['has_pv_data']:
            mapping.update({
                '/Pv/0/V': mpp_data.get('pv_voltage'),
                '/Pv/0/I': mpp_data.get('pv_current'),
                '/Pv/0/P': mpp_data.get('pv_power'),
                '/Yield/Power': mpp_data.get('pv_power'),
            })

        # Battery service mappings
        # Note: Battery data is published by the Multi service in Venus OS Multi inverters

        return mapping

    def _derive_operating_state(self, mpp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Derive operating state for Multi service from MPP Solar status.

        Args:
            mpp_data: MPP Solar data

        Returns:
            dict: State mappings
        """
        state_mapping = {}

        # Check if device is actually producing AC power (primary indicator)
        ac_voltage = mpp_data.get('ac_voltage', 0)
        ac_power = mpp_data.get('ac_power', 0)

        logger.debug(f"Operating state check: AC voltage={ac_voltage}, AC power={ac_power}")

        if ac_voltage > 180 and ac_power > 10:  # Device is actively inverting
            state_mapping['/Mode'] = 3  # On
            state_mapping['/State'] = 9  # Inverting
            logger.debug("Setting operating state: Mode=3 (On), State=9 (Inverting)")
        else:
            # Fallback to the reported switch state
            if mpp_data.get('is_switched_on') is False:
                state_mapping['/Mode'] = 4  # Off
                state_mapping['/State'] = 0  # Off
                logger.debug("Setting operating state: Mode=4 (Off), State=0 (Off) - device reports not switched on")
            else:
                state_mapping['/Mode'] = 3  # On
                state_mapping['/State'] = 9  # Inverting
                logger.debug("Setting operating state: Mode=3 (On), State=9 (Inverting) - fallback")

        # Check charging status for more detailed state (if applicable)
        is_charging = mpp_data.get('is_charging_on', False)
        is_scc_charging = mpp_data.get('is_scc_charging_on', False)

        if is_charging or is_scc_charging:
            if mpp_data.get('is_charging_to_float', False):
                state_mapping['/State'] = 5  # Float charging
                logger.debug("Adjusting state to 5 (Float charging)")
            else:
                state_mapping['/State'] = 3  # Bulk charging
                logger.debug("Adjusting state to 3 (Bulk charging)")

        return state_mapping

    def _derive_solar_state(self, mpp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Derive operating state for Solar Charger service.

        Args:
            mpp_data: MPP Solar data

        Returns:
            dict: State mappings
        """
        state_mapping = {}

        # Default state
        state_mapping['/Mode'] = 4  # Off
        state_mapping['/State'] = 0  # Off
        state_mapping['/MppOperationMode'] = 0  # Off

        # Check if PV charging is active
        pv_voltage = mpp_data.get('pv_voltage', 0)
        pv_power = mpp_data.get('pv_power', 0)

        if pv_voltage > 10 and pv_power > 0:  # PV active
            state_mapping['/Mode'] = 1  # On
            state_mapping['/State'] = 3  # Bulk
            state_mapping['/MppOperationMode'] = 2  # MPPT Active

        return state_mapping

    def publish_data(self, dbus_mapping: Dict[str, Any], mpp_data: Dict[str, Any] = None) -> bool:
        """
        Publish data to appropriate D-Bus services.

        Args:
            dbus_mapping: Mapping of D-Bus paths to values
            mpp_data: Raw MPP Solar data (needed for service-specific state derivation)

        Returns:
            bool: True if publishing successful
        """
        print(f"DEBUG: publish_data called with mpp_data: {mpp_data is not None}, mapping keys: {list(dbus_mapping.keys())}")
        with open('/tmp/debug.log', 'a') as f:
            f.write(f"publish_data called with mpp_data: {mpp_data is not None}, mapping has Mode: {'/Mode' in dbus_mapping}, State: {'/State' in dbus_mapping}\n")
            if '/Mode' in dbus_mapping:
                f.write(f"Mode value: {dbus_mapping['/Mode']}\n")
            if '/State' in dbus_mapping:
                f.write(f"State value: {dbus_mapping['/State']}\n")
        try:
            success = True

            # Update Multi service
            if self.multi_service:
                # Get the correct operating state for Multi service
                multi_state = {}
                if mpp_data is not None:
                    multi_state = self._derive_operating_state(mpp_data)
                    logger.debug(f"Multi state derived: {multi_state}")
                else:
                    logger.debug("mpp_data is None")

                for path, value in dbus_mapping.items():
                    if path in self._multi_paths:
                        # Use service-specific state for Mode/State paths
                        if path in ['/Mode', '/State']:
                            print(f"DEBUG: Processing {path}, value from mapping: {value}, multi_state: {multi_state}")
                            if path in multi_state:
                                actual_value = multi_state[path]
                                print(f"DEBUG: Using multi-specific {path} = {actual_value}")
                            else:
                                actual_value = value
                                print(f"DEBUG: Using mapping value for {path} = {actual_value}")
                        else:
                            actual_value = value

                        if actual_value is not None:
                            # Only publish if the path was actually added to the service
                            if path in self.multi_service._dbusobjects:
                                try:
                                    self.multi_service[path] = actual_value
                                    logger.debug(f"Updated Multi {path} = {actual_value}")
                                except Exception as e:
                                    logger.error(f"Error publishing data to D-Bus: '{path}' = {actual_value}, error: {e}")
                                    success = False
                            else:
                                logger.debug(f"Skipped Multi {path} (not in service)")
                        else:
                            logger.debug(f"Skipped Multi {path} (value is None)")
                    elif path in self._multi_paths and value is None:
                        logger.debug(f"Skipped Multi {path} (value is None)")

            # Update Solar service
            if self.solar_service:
                # Get the correct operating state for Solar service
                solar_state = {}
                if mpp_data is not None:
                    solar_state = self._derive_solar_state(mpp_data)

                for path, value in dbus_mapping.items():
                    if path in self._solar_paths:
                        # Use service-specific state for Mode/State/MppOperationMode paths
                        if path in ['/Mode', '/State', '/MppOperationMode'] and path in solar_state:
                            actual_value = solar_state[path]
                        else:
                            actual_value = value

                        if actual_value is not None:
                            # Only publish if the path was actually added to the service
                            if path in self.solar_service._dbusobjects:
                                try:
                                    self.solar_service[path] = actual_value
                                    logger.debug(f"Updated Solar {path} = {actual_value}")
                                except Exception as e:
                                    logger.error(f"Error publishing data to D-Bus: '{path}' = {actual_value}, error: {e}")
                                    success = False
                            else:
                                logger.debug(f"Skipped Solar {path} (not in service)")
                        else:
                            logger.debug(f"Skipped Solar {path} (value is None)")
                    elif path in self._solar_paths and value is None:
                        logger.debug(f"Skipped Solar {path} (value is None)")

            # Update Battery service
            # Note: Battery data is published by Multi service, no separate battery service

            return success

        except Exception as e:
            logger.error(f"Error publishing data to D-Bus: {e}")
            return False

    def update_connection_status(self, online: bool):
        """
        Update connection status on all services.

        Args:
            online: Whether device is online
        """
        try:
            connected_value = 1 if online else 0
            status_value = 1 if online else 0

            if self.multi_service:
                self.multi_service['/Connected'] = connected_value
                self.multi_service['/Status'] = status_value

            if self.solar_service:
                self.solar_service['/Connected'] = connected_value

            # Battery service connection status handled by Multi service

        except Exception as e:
            logger.error(f"Error updating connection status: {e}")

    def log_data_mapping(self, mpp_data: Dict[str, Any], dbus_mapping: Dict[str, Any], capabilities: Dict[str, bool]):
        """
        Comprehensive logging of data mapping process.

        Args:
            mpp_data: Raw MPP Solar data
            dbus_mapping: D-Bus path mappings
            capabilities: Device capabilities
        """
        if not logger.isEnabledFor(logging.DEBUG):
            return

        logger.debug("=== MPP Solar Data Mapping ===")
        logger.debug(f"Capabilities: {capabilities}")
        logger.debug(f"Raw MPP data keys: {list(mpp_data.keys())}")

        # Log published paths
        published = {k: v for k, v in dbus_mapping.items() if v is not None}
        logger.debug(f"Publishing {len(published)} paths: {list(published.keys())}")

        # Log services being updated
        services = []
        if self.multi_service:
            services.append("Multi")
        if self.solar_service:
            services.append("Solar")
        # Battery service not used - data published by Multi service
        logger.debug(f"Updating services: {services}")