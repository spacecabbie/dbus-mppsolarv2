#!/bin/bash
# Disable MPP Solar D-Bus service

echo "Disabling MPP Solar D-Bus service..."
systemctl disable com.victronenergy.mppsolar.service
echo "Service disabled successfully!"