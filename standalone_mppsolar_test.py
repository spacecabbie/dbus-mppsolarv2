#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone test script for MPP Solar D-Bus service

This code was generated with the help of Grok XAI
"""

import sys
import os
import time

# Add current directory to Python path for module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import logger
from battery import Battery

def test_connection():
    """
    Test MPP Solar device connection.

    Creates a Battery instance and attempts to establish connection
    with the MPP Solar inverter. Logs success or failure.

    Returns:
        bool: True if connection test passes, False otherwise
    """
    logger.info("Testing MPP Solar device connection...")

    # Create battery instance with default settings
    battery = Battery()
    if battery.test_connection():
        logger.info("✓ Connection successful")
        return True
    else:
        logger.error("✗ Connection failed")
        return False

def test_data_refresh():
    """
    Test data refresh functionality.

    Tests the ability to refresh data from the connected MPP Solar device.
    Requires successful connection first. Logs retrieved data values.

    Returns:
        bool: True if data refresh test passes, False otherwise
    """
    logger.info("Testing data refresh...")

    # Create battery instance and test connection first
    battery = Battery()
    if not battery.test_connection():
        logger.error("Cannot test data refresh - connection failed")
        return False

    # Refresh data from the device
    battery.refresh_data()
    logger.info("✓ Data refresh completed")

    # Log the retrieved data values for verification
    logger.info(f"AC Voltage: {battery.ac_voltage}")
    logger.info(f"AC Current: {battery.ac_current}")
    logger.info(f"AC Power: {battery.ac_power}")
    logger.info(f"Frequency: {battery.frequency}")
    logger.info(f"DC Voltage: {battery.voltage}")
    logger.info(f"DC Current: {battery.current}")
    logger.info(f"DC Power: {battery.power}")

    return True

def main():
    """
    Main test function.

    Runs all test functions in sequence. Exits with error code
    if any test fails. Catches and logs unexpected exceptions.
    """
    logger.info("Starting MPP Solar standalone test...")

    try:
        # Test device connection
        if not test_connection():
            sys.exit(1)

        # Test data retrieval
        if not test_data_refresh():
            sys.exit(1)

        logger.info("✓ All tests passed!")

    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()