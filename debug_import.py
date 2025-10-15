#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to test mpp-solar import
"""

import sys
import os

print("Current working directory:", os.getcwd())
print("Script location:", os.path.dirname(os.path.abspath(__file__)))

# Calculate the mpp_solar_path as done in inverter.py
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
mpp_solar_path = os.path.join(parent_dir, 'mpp-solar', 'mppsolar')

print("Calculated mpp_solar_path:", mpp_solar_path)
print("Path exists:", os.path.exists(mpp_solar_path))
print("Is directory:", os.path.isdir(mpp_solar_path))

if os.path.exists(mpp_solar_path):
    print("Contents of mppsolar directory:")
    for item in os.listdir(mpp_solar_path):
        print(f"  {item}")

# Try the import
try:
    if mpp_solar_path not in sys.path:
        sys.path.insert(0, mpp_solar_path)
        print("Added to sys.path:", mpp_solar_path)

    from mppsolar import MPP
    print("✓ Successfully imported MPP from mppsolar")
    print("MPP class:", MPP)

except ImportError as e:
    print("✗ Import failed:", e)
    print("sys.path:")
    for path in sys.path:
        print(f"  {path}")