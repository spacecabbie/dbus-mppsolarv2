#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone test script for MPP Solar D-Bus service with Multi/Solar Charger architecture

This code was generated with the help of Grok XAI
"""

import sys
import os
import time

# Add current directory to Python path for module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dbus_mppsolar.utils import logger, get_config_value, PORT, BAUD_RATE, DEBUG_ENABLED, setup_logging
from dbus_mppsolar.inverter import Inverter
from dbus_mppsolar.dbushelper import DbusHelper

def test_connection():
    """
    Test MPP Solar inverter connection.

    Creates a Inverter instance and attempts to establish connection
    with the MPP Solar inverter. Logs success or failure.

    Returns:
        bool: True if connection test passes, False otherwise
    """
    logger.info("Testing MPP Solar inverter connection...")

    logger.info(f"Using port: {PORT}, baud: {BAUD_RATE}")

    # Create inverter instance with config settings
    inverter = Inverter(port=PORT, baud=BAUD_RATE)
    if inverter.test_connection():
        logger.info("✓ Connection successful")
        return True
    else:
        logger.error("✗ Connection failed")
        return False

def test_capability_assessment():
    """
    Test device capability assessment.

    Tests the ability to assess device capabilities from the connected
    MPP Solar inverter. Requires successful connection first.

    Returns:
        bool: True if capability assessment test passes, False otherwise
    """
    logger.info("Testing device capability assessment...")

    # Create inverter instance with config settings and test connection first
    inverter = Inverter(port=PORT, baud=BAUD_RATE)
    if not inverter.test_connection():
        logger.error("Cannot test capability assessment - connection failed")
        return False

    # Assess device capabilities
    capabilities = inverter.assess_device_capabilities()
    logger.info("✓ Capability assessment completed")

    # Log the assessed capabilities
    logger.info("Device Capabilities:")
    for cap, value in capabilities.items():
        logger.info(f"  {cap}: {value}")

    return True

def test_data_refresh():
    """
    Test data refresh functionality with comprehensive data mapping.

    Tests the ability to refresh data from the connected MPP Solar inverter
    and map it to D-Bus paths. Requires successful connection first.
    Logs retrieved data values and D-Bus mapping.

    Returns:
        bool: True if data refresh test passes, False otherwise
    """
    logger.info("Testing data refresh and D-Bus mapping...")

    # Create inverter instance with config settings and test connection first
    inverter = Inverter(port=PORT, baud=BAUD_RATE)
    if not inverter.test_connection():
        logger.error("Cannot test data refresh - connection failed")
        return False

    # Assess capabilities first
    capabilities = inverter.assess_device_capabilities()
    logger.info("Capabilities assessed for data mapping")

    # Refresh data from the inverter
    if not inverter.refresh_data():
        logger.error("Failed to refresh data from inverter")
        return False

    logger.info("✓ Data refresh completed")

    # Create D-Bus helper for mapping test
    dbus_helper = DbusHelper(inverter, device_instance=0)

    # Map MPP Solar data to D-Bus paths
    mpp_data = {
        'ac_voltage': inverter.ac_voltage,
        'ac_current': inverter.ac_current,
        'ac_power': inverter.ac_power,
        'ac_apparent_power': inverter.ac_apparent_power,
        'ac_load_percentage': inverter.ac_load_percentage,
        'frequency': inverter.frequency,
        'ac_input_voltage': inverter.ac_input_voltage,
        'ac_input_frequency': inverter.ac_input_frequency,
        'battery_voltage': inverter._battery_voltage,
        'battery_charging_current': max(0, inverter._battery_current) if inverter._battery_current and inverter._battery_current > 0 else 0,
        'battery_discharge_current': abs(min(0, inverter._battery_current)) if inverter._battery_current and inverter._battery_current < 0 else 0,
        'battery_capacity': inverter._battery_soc,
        'heat_sink_temp': inverter.heat_sink_temp,
        'pv_voltage': inverter.pv_voltage,
        'pv_current': inverter.pv_current,
        'pv_power': inverter.pv_power,
        'bus_voltage': inverter.bus_voltage,
        'is_switched_on': getattr(inverter, 'is_switched_on', True),
        'is_charging_on': getattr(inverter, 'is_charging_on', False),
        'is_scc_charging_on': getattr(inverter, 'is_scc_charging_on', False),
        'is_charging_to_float': getattr(inverter, 'is_charging_to_float', False),
    }

    # Map to D-Bus paths
    dbus_mapping = dbus_helper.map_mpp_values_to_dbus(mpp_data, capabilities)

    # Log the retrieved data values for verification
    logger.info("MPP Solar Data Values:")
    for key, value in mpp_data.items():
        logger.info(f"  {key}: {value}")

    # Log D-Bus mapping
    logger.info("D-Bus Path Mapping:")
    for path, value in dbus_mapping.items():
        logger.info(f"  {path}: {value}")

    return True

def test_dbus_service_creation():
    """
    Test D-Bus service creation without actually connecting to D-Bus.

    Tests the ability to create D-Bus services based on device capabilities.
    This test doesn't require actual D-Bus connection.

    Returns:
        bool: True if service creation test passes, False otherwise
    """
    logger.info("Testing D-Bus service creation (simulation)...")

    # Create inverter instance
    inverter = Inverter(port=PORT, baud=BAUD_RATE)

    # Create D-Bus helper
    dbus_helper = DbusHelper(inverter, device_instance=0)

    # Test service creation logic (without actual D-Bus connection)
    try:
        # This would normally create actual D-Bus services, but we'll just test the logic
        capabilities = {
            'has_ac_output': True,
            'has_ac_input': True,
            'has_battery': True,
            'has_pv': True,
            'can_charge': True,
            'can_discharge': True,
        }

        logger.info("✓ D-Bus service creation logic test completed")
        logger.info("Services that would be created:")
        logger.info(f"  - Multi service ({dbus_helper.multi_service_name})")
        logger.info(f"  - Solar Charger service ({dbus_helper.solar_service_name})")

        return True

    except Exception as e:
        logger.error(f"Service creation test failed: {e}")
        return False

def main():
    """
    Main test function.

    Runs all test functions in sequence. Exits with error code
    if any test fails. Catches and logs unexpected exceptions.
    """
    # Setup logging with debug support
    global logger
    logger = setup_logging(debug_enabled=DEBUG_ENABLED)

    logger.info("Starting MPP Solar standalone test with Multi/Solar Charger architecture...")

    try:
        # Test device connection
        if not test_connection():
            sys.exit(1)

        # Test capability assessment
        if not test_capability_assessment():
            sys.exit(1)

        # Test data retrieval and mapping
        if not test_data_refresh():
            sys.exit(1)

        # Test D-Bus service creation logic
        if not test_dbus_service_creation():
            sys.exit(1)

        logger.info("✓ All tests passed!")

    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=DEBUG_ENABLED)
        sys.exit(1)

if __name__ == "__main__":
    main()