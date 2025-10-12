#!/bin/bash
# Enable MPP Solar D-Bus service

echo "Enabling MPP Solar D-Bus service..."
systemctl enable com.victronenergy.mppsolar.service
echo "Service enabled successfully!"