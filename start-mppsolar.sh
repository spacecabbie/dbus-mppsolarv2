#!/bin/bash
# MPP Solar D-Bus service run script

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SERVICE_DIR="/opt/victronenergy/dbus-mppsolar"

# Check if running on Venus OS
if [ ! -d "/opt/victronenergy" ]; then
    echo "Error: This script is designed for Venus OS"
    exit 1
fi

# Check if service is installed
if [ ! -f "$SERVICE_DIR/dbus-mppsolar.py" ]; then
    echo "Error: MPP Solar service not installed"
    echo "Run install.sh first"
    exit 1
fi

# Start the service
echo "Starting MPP Solar D-Bus service..."
cd "$SERVICE_DIR"
python3 dbus-mppsolar.py