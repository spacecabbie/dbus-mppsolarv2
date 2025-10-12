#!/bin/bash
# MPP Solar D-Bus service restart script

echo "Restarting MPP Solar D-Bus service..."
systemctl restart com.victronenergy.mppsolar.service

echo "Service status:"
systemctl status com.victronenergy.mppsolar.service