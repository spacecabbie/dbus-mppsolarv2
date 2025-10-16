# -*- coding: utf-8 -*-
"""
MPP Solar D-Bus service for Venus OS
Main service entry point for MPP Solar inverter integration with Multi/Solar Charger architecture

This code was generated with the help of Grok XAI
"""

import sys
import os
import signal
import time
from typing import Optional

# Add current directory to path for module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dbus_mppsolar.utils import logger, get_config_value, safe_number_format, PORT, BAUD_RATE, POLL_INTERVAL, DEVICE_INSTANCE, DEBUG_ENABLED, setup_logging
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
    MPP Solar D-Bus service class with Multi/Solar Charger architecture.

    This class manages the lifecycle of the MPP Solar D-Bus service,
    including initialization, capability assessment, data collection, and D-Bus communication.
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
        Setup the MPP Solar service with capability assessment.

        Initializes the inverter connection, assesses device capabilities,
        and creates appropriate D-Bus services.
        Returns True if setup successful, False otherwise.

        Returns:
            bool: True if setup completed successfully, False on failure
        """
        try:
            logger.info("Setting up MPP Solar D-Bus service with Multi/Solar Charger architecture...")
            logger.info(f"Debug logging: {'enabled' if DEBUG_ENABLED else 'disabled'}")

            # Create and test inverter connection
            self.inverter = Inverter(port=PORT, baud=BAUD_RATE)
            if not self.inverter.test_connection():
                logger.error("Failed to connect to MPP Solar device")
                return False

            # Initialize D-Bus helper for Venus OS integration
            self.dbus_helper = DbusHelper(self.inverter, DEVICE_INSTANCE)

            # Assess capabilities and create services
            if not self.dbus_helper.assess_capabilities_and_create_services():
                logger.error("Failed to create D-Bus services")
                return False

            # Update management information
            self.dbus_helper.multi_service['/Mgmt/ProcessName'] = "dbus-mppsolar"
            self.dbus_helper.multi_service['/Mgmt/ProcessVersion'] = "1.0.0"

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

            self.dbus_helper.multi_service['/Mgmt/Connection'] = connection_type
            if self.dbus_helper.solar_service:
                self.dbus_helper.solar_service['/Mgmt/Connection'] = connection_type

            logger.info(f"Connection type set to: {connection_type}")
            logger.info("MPP Solar D-Bus service setup complete")
            return True

        except Exception as e:
            logger.error(f"Error during service setup: {e}", exc_info=DEBUG_ENABLED)
            return False

    def run_mainloop(self, mainloop: gobject.MainLoop) -> None:
        """
        Run the main service loop with the provided main loop.

        Sets up signal handlers, publishes initial data, and runs the
        provided GLib main loop with periodic data updates.
        """
        try:
            self.running = True
            logger.info("Service run_mainloop() method started")

            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            logger.info("Signal handlers set up")

            # Publish initial inverter data to D-Bus
            logger.info("Calling initial _update_data()...")
            result = self._update_data()
            logger.info(f"Initial _update_data() returned: {result}")

            # Add timer for periodic data updates (every POLL_INTERVAL ms)
            gobject.timeout_add(POLL_INTERVAL, self._update_data)

            # Store the main loop reference for signal handler
            self.mainloop = mainloop

            # Run the main loop (blocks until quit)
            logger.info("Running main loop...")
            mainloop.run()

        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=DEBUG_ENABLED)
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
                if self.inverter.refresh_data():
                    # Get device capabilities (updated with each poll in case they change)
                    capabilities = self.inverter.capabilities

                    # Map MPP Solar data to D-Bus paths
                    mpp_data = {
                        'ac_voltage': self.inverter.ac_voltage,
                        'ac_current': self.inverter.ac_current,
                        'ac_power': self.inverter.ac_power,
                        'ac_apparent_power': self.inverter.ac_apparent_power,
                        'ac_load_percentage': self.inverter.ac_load_percentage,
                        'frequency': self.inverter.frequency,
                        'ac_input_voltage': self.inverter.ac_input_voltage,
                        'ac_input_frequency': self.inverter.ac_input_frequency,
                        'battery_voltage': self.inverter._battery_voltage,
                        'battery_charging_current': max(0, self.inverter._battery_current) if self.inverter._battery_current and self.inverter._battery_current > 0 else 0,
                        'battery_discharge_current': abs(min(0, self.inverter._battery_current)) if self.inverter._battery_current and self.inverter._battery_current < 0 else 0,
                        'battery_capacity': self.inverter._battery_soc,
                        'heat_sink_temp': self.inverter.heat_sink_temp,
                        'pv_voltage': self.inverter.pv_voltage,
                        'pv_current': self.inverter.pv_current,
                        'pv_power': self.inverter.pv_power,
                        'bus_voltage': self.inverter.bus_voltage,
                        'is_switched_on': getattr(self.inverter, 'is_switched_on', True),
                        'is_charging_on': getattr(self.inverter, 'is_charging_on', False),
                        'is_scc_charging_on': getattr(self.inverter, 'is_scc_charging_on', False),
                        'is_charging_to_float': getattr(self.inverter, 'is_charging_to_float', False),
                    }

                    # Map to D-Bus paths
                    dbus_mapping = self.dbus_helper.map_mpp_values_to_dbus(mpp_data, capabilities)

                    # Log comprehensive mapping details
                    self.dbus_helper.log_data_mapping(mpp_data, dbus_mapping, capabilities)

                    # Publish to D-Bus
                    if self.dbus_helper.publish_data(dbus_mapping, mpp_data):
                        # Update connection status
                        self.dbus_helper.update_connection_status(self.inverter.online)
                        logger.debug("Data published successfully")
                    else:
                        logger.warning("Failed to publish data to D-Bus")
                        self.dbus_helper.update_connection_status(False)
                else:
                    logger.warning("Failed to refresh data from inverter")
                    self.dbus_helper.update_connection_status(False)

            return True  # Continue timer

        except Exception as e:
            logger.error(f"Error updating data: {e}", exc_info=DEBUG_ENABLED)
            if self.dbus_helper:
                self.dbus_helper.update_connection_status(False)
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
        # Setup logging with debug support
        global logger
        logger = setup_logging(debug_enabled=DEBUG_ENABLED)

        # Set up D-Bus main loop for GLib integration
        DBusGMainLoop(set_as_default=True)

        # Create the MPP Solar service
        service = MPPService()
        if not service.setup():
            logger.error("Failed to setup service")
            sys.exit(1)

        # Create the main loop
        mainloop = gobject.MainLoop()

        # Now register the services since main loop is available
        if not service.dbus_helper.register_services():
            logger.error("Failed to register D-Bus services")
            sys.exit(1)

        # Run the service (blocks)
        service.run_mainloop(mainloop)

    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=DEBUG_ENABLED)
        sys.exit(1)

if __name__ == "__main__":
    main()