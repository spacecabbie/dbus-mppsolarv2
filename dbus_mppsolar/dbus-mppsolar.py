# dbus-mppsolar - Venus OS D-Bus service for MPP Solar inverters
# Based on dbus-serialbattery by mr-manuel
# Adapted to use mpp-solar package for PI30 inverters

# Main service file
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

from dbushelper import DbusHelper
from inverter import Inverter
from .utils import logger, PORT, BAUD_RATE, POLL_INTERVAL

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
        # Publish inverter data (this will call refresh_data internally)
        dbus_helper.publish_inverter()
        return True  # Keep the timer running
    except Exception as e:
        logger.error(f"Error polling inverter: {e}")
        return True  # Keep the timer running even on errors

def main():
    """Main function to start the D-Bus service"""
    logger.info("Starting dbus-mppsolar service")

    logger.info(f"Using port: {PORT}, baud: {BAUD_RATE}, poll_interval: {POLL_INTERVAL}ms")

    # Initialize D-Bus main loop
    DBusGMainLoop(set_as_default=True)

    # Create inverter instance with config settings
    logger.info(f"Creating Inverter instance with port={PORT}, baud={BAUD_RATE}")
    inverter = Inverter(port=PORT, baud=BAUD_RATE)
    logger.info(f"Inverter created with port: {inverter.port}")

    # Create D-Bus helper
    dbus_helper = DbusHelper(inverter)

    # Setup D-Bus service
    if not dbus_helper.setup_vedbus():
        logger.error("Failed to setup D-Bus service")
        return 1

    # Update management information
    # Set process name to the actual service name
    dbus_helper.update_process_name("dbus-mppsolar")

    # Set process version (could be read from a version file in the future)
    dbus_helper.update_process_version("1.0.0")

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
    dbus_helper.update_connection_type(connection_type)

    # Setup periodic polling timer
    logger.info(f"Setting up polling timer with interval {POLL_INTERVAL}ms")
    gobject.timeout_add(POLL_INTERVAL, lambda: poll_inverter(dbus_helper))

    # Main loop
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