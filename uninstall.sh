#!/bin/bash
# MPP Solar D-Bus service uninstallation script

SERVICE_DIR="/opt/victronenergy/dbus-mppsolar"
SERVICE_FILE="/etc/systemd/system/com.victronenergy.mppsolar.service"

echo "Uninstalling MPP Solar D-Bus service..."

# Stop and disable service
echo "Stopping and disabling service..."
systemctl stop com.victronenergy.mppsolar.service || true
systemctl disable com.victronenergy.mppsolar.service || true

# Remove service file
if [ -f "$SERVICE_FILE" ]; then
    rm "$SERVICE_FILE"
fi

# Reload systemd
systemctl daemon-reload

# Remove service directory
if [ -d "$SERVICE_DIR" ]; then
    echo "Removing service files..."
    rm -rf "$SERVICE_DIR"
fi

echo "MPP Solar D-Bus service uninstalled successfully!"