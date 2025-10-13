# -*- coding: utf-8 -*-
"""
MPP Solar D-Bus service for Venus OS
Main service entry point for MPP Solar inverter integration

This code was generated with the help of Grok XAI
"""

import sys
import os
import signal
import time
from typing import Optional

# Add current directory to path for module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dbus_mppsolar.utils import logger, get_config_value, safe_number_format
from dbus_mppsolar.battery import Battery
from dbus_mppsolar.dbushelper import DbusHelper

try:
    import dbus
    import gobject
    from dbus.mainloop.glib import DBusGMainLoop
except ImportError as e:
    logger.error(f"D-Bus dependencies not available: {e}")
    logger.error("Please install dbus-python and gobject")
    sys.exit(1)

class MPPService:
    """
    MPP Solar D-Bus service class.

    This class manages the lifecycle of the MPP Solar D-Bus service,
    including initialization, data collection, and D-Bus communication.
    """

    def __init__(self):
        """
        Initialize the MPP Solar service.

        Sets up instance variables for battery, D-Bus helper, main loop,
        and running state.
        """
        self.battery: Optional[Battery] = None  # MPP Solar battery/inverter instance
        self.dbus_helper: Optional[DbusHelper] = None  # D-Bus communication helper
        self.mainloop: Optional[gobject.MainLoop] = None  # GLib main event loop
        self.running = False  # Flag to track if service is running

    def setup(self) -> bool:
        """
        Setup the MPP Solar service.

        Initializes the battery connection and D-Bus service.
        Returns True if setup successful, False otherwise.

        Returns:
            bool: True if setup completed successfully, False on failure
        """
        try:
            logger.info("Setting up MPP Solar D-Bus service...")

            # Create and test battery connection
            self.battery = Battery()
            if not self.battery.test_connection():
                logger.error("Failed to connect to MPP Solar device")
                return False

            # Get unique identifier for device instance assignment
            unique_id = self.battery.unique_identifier()
            logger.info(f"Device unique identifier: {unique_id}")

            # Get device instance from LocalSettings
            device_instance = self._get_device_instance(unique_id)
            logger.info(f"Assigned device instance: {device_instance}")

            # Initialize D-Bus helper for Venus OS integration
            self.dbus_helper = DbusHelper(self.battery, device_instance)
            if not self.dbus_helper.setup_vedbus():
                logger.error("Failed to setup D-Bus service")
                return False

            logger.info("MPP Solar D-Bus service setup complete")
            return True

        except Exception as e:
            logger.error(f"Error during service setup: {e}")
            return False

    def _get_device_instance(self, unique_id: str) -> int:
        """
        Get device instance from LocalSettings.

        Uses Venus OS LocalSettings to assign a unique device instance
        for this device. For PV inverters, uses class 'pvinverter'.

        Args:
            unique_id: Unique identifier for the device

        Returns:
            int: Assigned device instance number
        """
        try:
            # Connect to system bus
            bus = dbus.SystemBus()

            # Get settings service
            settings = bus.get_object('com.victronenergy.settings', '/')

            # Calculate preferred instance based on port
            # For serial ports: ttyUSBx -> 288 + x
            port = self.battery.port
            preferred_instance = 288  # default for ttyUSB0
            if 'ttyUSB' in port:
                try:
                    x = int(port.split('ttyUSB')[1])
                    preferred_instance = 288 + x
                except (ValueError, IndexError):
                    pass

            # Add setting for this device
            settings_path = f'/Settings/Devices/{unique_id}/ClassAndVrmInstance'
            settings.AddSetting(settings_path, ('pvinverter', preferred_instance))

            # Get the assigned instance
            instance = settings.GetValue(settings_path)
            return int(instance)

        except Exception as e:
            logger.warning(f"Failed to get device instance from LocalSettings: {e}")
            # Fallback to default instance
            return 0

    def run(self) -> None:
        """
        Run the main service loop.

        Sets up signal handlers, publishes initial data, and starts the
        GLib main loop with periodic data updates.
        """
        try:
            self.running = True

            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)

            # Publish initial battery data to D-Bus
            self.dbus_helper.publish_battery()

            # Start the GLib main event loop
            logger.info("Starting MPP Solar D-Bus service main loop...")
            self.mainloop = gobject.MainLoop()

            # Add timer for periodic data updates (every 1000ms = 1 second)
            gobject.timeout_add(1000, self._update_data)

            # Run the main loop (blocks until quit)
            self.mainloop.run()

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.running = False
            logger.info("MPP Solar D-Bus service stopped")

    def _update_data(self) -> bool:
        """
        Update battery data periodically.

        Called by the GLib timer to refresh inverter data and publish
        to D-Bus. Returns True to continue the timer.

        Returns:
            bool: Always True to keep the timer running
        """
        try:
            if self.battery and self.dbus_helper:
                # Refresh data from the MPP Solar device
                self.battery.refresh_data()

                # Publish updated data to D-Bus
                self.dbus_helper.publish_battery()

            return True  # Continue timer

        except Exception as e:
            logger.error(f"Error updating data: {e}")
            return True  # Continue timer even on error

    def _signal_handler(self, signum, frame) -> None:
        """
        Handle shutdown signals.

        Called when SIGTERM or SIGINT is received. Quits the main loop
        to gracefully shutdown the service.

        Args:
            signum: Signal number (e.g., signal.SIGTERM)
            frame: Current stack frame (unused)
        """
        logger.info(f"Received signal {signum}, shutting down...")
        if self.mainloop:
            self.mainloop.quit()
        self.running = False

def main():
    """
    Main entry point for the MPP Solar D-Bus service.

    Sets up D-Bus main loop, initializes service, and starts running.
    Handles exceptions and keyboard interrupts gracefully.
    """
    try:
        # Set up D-Bus main loop for GLib integration
        DBusGMainLoop(set_as_default=True)

        # Create and setup the MPP Solar service
        service = MPPService()
        if not service.setup():
            logger.error("Failed to setup service")
            sys.exit(1)

        # Run the service (blocks)
        service.run()

    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()