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

from dbus_mppsolar.utils import logger, get_config_value, safe_number_format, PORT, BAUD_RATE, POLL_INTERVAL
from dbus_mppsolar.inverter import Inverter
from dbus_mppsolar.dbushelper import DbusHelper

try:
    import dbus
    import gi.repository.GObject as gobject
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

        Sets up instance variables for inverter, D-Bus helper, main loop,
        and running state.
        """
        self.inverter: Optional[Inverter] = None  # MPP Solar inverter instance
        self.dbus_helper: Optional[DbusHelper] = None  # D-Bus communication helper
        self.mainloop: Optional[gobject.MainLoop] = None  # GLib main event loop
        self.running = False  # Flag to track if service is running

    def setup(self) -> bool:
        """
        Setup the MPP Solar service.

        Initializes the inverter connection and D-Bus service.
        Returns True if setup successful, False otherwise.

        Returns:
            bool: True if setup completed successfully, False on failure
        """
        try:
            logger.info("Setting up MPP Solar D-Bus service...")

            # Create and test inverter connection
            self.inverter = Inverter(port=PORT, baud=BAUD_RATE)
            if not self.inverter.test_connection():
                logger.error("Failed to connect to MPP Solar device")
                return False

            # Initialize D-Bus helper for Venus OS integration
            self.dbus_helper = DbusHelper(self.inverter)
            if not self.dbus_helper.setup_vedbus():
                logger.error("Failed to setup D-Bus service")
                return False

            # Update management information
            # Set process name to the actual service name
            self.dbus_helper.update_process_name("dbus-mppsolar")

            # Set process version
            self.dbus_helper.update_process_version("0.0.1-alpha")

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
            self.dbus_helper.update_connection_type(connection_type)

            logger.info("MPP Solar D-Bus service setup complete")
            return True

        except Exception as e:
            logger.error(f"Error during service setup: {e}")
            return False

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

            # Publish initial inverter data to D-Bus
            self.dbus_helper.publish_inverter()

            # Start the GLib main event loop
            logger.info("Starting MPP Solar D-Bus service main loop...")
            self.mainloop = gobject.MainLoop()

            # Add timer for periodic data updates (every POLL_INTERVAL ms)
            gobject.timeout_add(POLL_INTERVAL, self._update_data)

            # Run the main loop (blocks until quit)
            self.mainloop.run()

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.running = False
            logger.info("MPP Solar D-Bus service stopped")

    def _update_data(self) -> bool:
        """
        Update inverter data periodically.

        Called by the GLib timer to refresh inverter data and publish
        to D-Bus. Returns True to continue the timer.

        Returns:
            bool: Always True to keep the timer running
        """
        try:
            if self.inverter and self.dbus_helper:
                # Refresh data from the MPP Solar device
                self.inverter.refresh_data()

                # Publish updated data to D-Bus
                self.dbus_helper.publish_inverter()

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