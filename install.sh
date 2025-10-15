#!/bin/bash
# MPP Solar D-Bus service installation script for Venus OS

set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SERVICE_DIR="/data/etc/dbus-mppsolarv2"
SERVICE_FILE="/etc/systemd/system/com.victronenergy.mppsolar.service"

echo "Installing MPP Solar D-Bus service..."

# Check if running on Venus OS
if [ ! -d "/data/etc" ]; then
    echo "Error: This script is designed for Venus OS"
    exit 1
fi

# Initialize and update submodules
echo "Initializing git submodules..."
cd "$SCRIPT_DIR"
git submodule update --init --recursive

# Create service directory
echo "Creating service directory..."
mkdir -p "$SERVICE_DIR"

# Copy files
echo "Copying service files..."
cp -r "$SCRIPT_DIR"/* "$SERVICE_DIR/"

# Install Python dependencies (excluding mpp-solar which is now a submodule)
echo "Installing Python dependencies..."
cd "$SERVICE_DIR"
pip3 install pyserial dbus-python gobject

# Install service
echo "Installing systemd service..."
cp "$SERVICE_DIR/service/com.victronenergy.mppsolar.service" "$SERVICE_FILE"

# Make scripts executable
chmod +x "$SERVICE_DIR"/*.sh
chmod +x "$SERVICE_DIR"/*.py

# Reload systemd
systemctl daemon-reload

# Enable and start service
echo "Enabling and starting service..."
systemctl enable com.victronenergy.mppsolar.service
systemctl start com.victronenergy.mppsolar.service

echo "MPP Solar D-Bus service installed successfully!"
echo "Service status: systemctl status com.victronenergy.mppsolar.service"