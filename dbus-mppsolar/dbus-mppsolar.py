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
import gobject

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dbushelper import DbusHelper
from battery import Battery
from utils import logger

def main():
    """Main function to start the D-Bus service"""
    logger.info("Starting dbus-mppsolar service")

    # Initialize D-Bus main loop
    DBusGMainLoop(set_as_default=True)

    # Create battery instance
    battery = Battery()

    # Create D-Bus helper
    dbus_helper = DbusHelper(battery)

    # Setup D-Bus service
    if not dbus_helper.setup_vedbus():
        logger.error("Failed to setup D-Bus service")
        return 1

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