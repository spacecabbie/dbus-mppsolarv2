# dbus-mppsolar - Venus OS D-Bus service for MPP Solar inverters
# Multi/Solar Charger service architecture with capability detection

import sys
import os
import logging
from time import sleep
from dbus.mainloop.glib import DBusGMainLoop
import dbus
import dbus.service
import gi.repository.GObject as gobject

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .dbushelper import DbusHelper
from .inverter import Inverter
from .utils import logger, PORT, BAUD_RATE, POLL_INTERVAL, DEVICE_INSTANCE, DEBUG_ENABLED, setup_logging

def poll_inverter(dbus_helper):
    """
    Poll the inverter for data and publish to D-Bus.

    This function is called periodically by the GLib timer to refresh
    data from the MPP Solar device and publish it to D-Bus.

    Args:
        dbus_helper: DbusHelper instance for publishing data

    Returns:
        bool: Always returns True to keep the timer running
    """
    try:
        # Refresh data from inverter
        if dbus_helper.inverter.refresh_data():
            # Get device capabilities (updated with each poll in case they change)
            capabilities = dbus_helper.inverter.capabilities

            # Map MPP Solar data to D-Bus paths
            mpp_data = {
                'ac_voltage': dbus_helper.inverter.ac_voltage,
                'ac_current': dbus_helper.inverter.ac_current,
                'ac_power': dbus_helper.inverter.ac_power,
                'ac_apparent_power': dbus_helper.inverter.ac_apparent_power,
                'ac_load_percentage': dbus_helper.inverter.ac_load_percentage,
                'frequency': dbus_helper.inverter.frequency,
                'ac_input_voltage': dbus_helper.inverter.ac_input_voltage,
                'ac_input_frequency': dbus_helper.inverter.ac_input_frequency,
                'battery_voltage': dbus_helper.inverter._battery_voltage,
                'battery_charging_current': max(0, dbus_helper.inverter._battery_current) if dbus_helper.inverter._battery_current and dbus_helper.inverter._battery_current > 0 else 0,
                'battery_discharge_current': abs(min(0, dbus_helper.inverter._battery_current)) if dbus_helper.inverter._battery_current and dbus_helper.inverter._battery_current < 0 else 0,
                'battery_capacity': dbus_helper.inverter._battery_soc,
                'heat_sink_temp': dbus_helper.inverter.heat_sink_temp,
                'pv_voltage': dbus_helper.inverter.pv_voltage,
                'pv_current': dbus_helper.inverter.pv_current,
                'pv_power': dbus_helper.inverter.pv_power,
                'bus_voltage': dbus_helper.inverter.bus_voltage,
                'is_switched_on': getattr(dbus_helper.inverter, 'is_switched_on', True),
                'is_charging_on': getattr(dbus_helper.inverter, 'is_charging_on', False),
                'is_scc_charging_on': getattr(dbus_helper.inverter, 'is_scc_charging_on', False),
                'is_charging_to_float': getattr(dbus_helper.inverter, 'is_charging_to_float', False),
            }

            # Map to D-Bus paths
            dbus_mapping = dbus_helper.map_mpp_values_to_dbus(mpp_data, capabilities)

            # Log comprehensive mapping details
            dbus_helper.log_data_mapping(mpp_data, dbus_mapping, capabilities)

            # Publish to D-Bus
            if dbus_helper.publish_data(dbus_mapping, mpp_data):
                # Update connection status
                dbus_helper.update_connection_status(dbus_helper.inverter.online)
                logger.debug("Data published successfully")
            else:
                logger.warning("Failed to publish data to D-Bus")

        else:
            logger.warning("Failed to refresh data from inverter")
            dbus_helper.update_connection_status(False)

        return True  # Keep the timer running

    except Exception as e:
        logger.error(f"Error in poll_inverter: {e}", exc_info=DEBUG_ENABLED)
        dbus_helper.update_connection_status(False)
        return True  # Keep the timer running even on errors

def main():
    """Main function to start the D-Bus service"""
    # Setup logging with debug support
    global logger
    logger = setup_logging(debug_enabled=DEBUG_ENABLED)

    logger.info("Starting dbus-mppsolar service with Multi/Solar Charger architecture")
    logger.info(f"Debug logging: {'enabled' if DEBUG_ENABLED else 'disabled'}")

    logger.info(f"Using port: {PORT}, baud: {BAUD_RATE}, poll_interval: {POLL_INTERVAL}ms")

    # Initialize D-Bus main loop
    DBusGMainLoop(set_as_default=True)

    # Create inverter instance with config settings
    logger.info(f"Creating Inverter instance with port={PORT}, baud={BAUD_RATE}")
    inverter = Inverter(port=PORT, baud=BAUD_RATE)
    logger.info(f"Inverter created with port: {inverter.port}")

    # Test connection to inverter
    if not inverter.test_connection():
        logger.error("Failed to connect to MPP Solar inverter")
        return 1

    # Create D-Bus helper
    dbus_helper = DbusHelper(inverter, DEVICE_INSTANCE)

    # Assess capabilities and create services
    if not dbus_helper.assess_capabilities_and_create_services():
        logger.error("Failed to create D-Bus services")
        return 1

    # Update management information
    dbus_helper.multi_service['/Mgmt/ProcessName'] = "dbus-mppsolar"
    dbus_helper.multi_service['/Mgmt/ProcessVersion'] = "1.0.0"

    # Determine connection type based on port
    if PORT.startswith('/dev/hidraw'):
        connection_type = "USB HID"
    elif PORT.startswith('/dev/tty'):
        connection_type = "Serial USB"
    elif PORT.startswith('/dev/ttyUSB'):
        connection_type = "Serial USB"
    elif PORT.startswith('/dev/ttyACM'):
        connection_type = "Serial ACM"
    else:
        connection_type = "Unknown"

    dbus_helper.multi_service['/Mgmt/Connection'] = connection_type
    if dbus_helper.solar_service:
        dbus_helper.solar_service['/Mgmt/Connection'] = connection_type

    logger.info(f"Connection type set to: {connection_type}")

    # Setup periodic polling timer
    logger.info(f"Setting up polling timer with interval {POLL_INTERVAL}ms")
    gobject.timeout_add(POLL_INTERVAL, lambda: poll_inverter(dbus_helper))

    # Main loop
    logger.info("Entering main event loop...")
    mainloop = gobject.MainLoop()
    try:
        mainloop.run()
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Service error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())