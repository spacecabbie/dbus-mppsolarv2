# MPP Solar Test Directory

This directory contains test scripts for the MPP Solar D-Bus service.

## Files

- `standalone_mppsolar_test.py` - Standalone test script for MPP Solar device connection and data retrieval

## Running Tests

### Standalone Test

To run the standalone test without D-Bus integration:

```bash
cd /data/apps/dbus-mppsolarv2
python3 test/standalone_mppsolar_test.py
```

This will test:
- MPP Solar device connection
- Data retrieval from the inverter
- Basic data parsing

## Test Results

The test script will output:
- Connection status
- Retrieved inverter data (voltage, current, power, frequency)
- Any errors encountered

## Troubleshooting

If tests fail:
1. Check device connection (USB/serial port)
2. Verify MPP Solar device is powered on
3. Check configuration in `config.default.ini`
4. Ensure mpp-solar package is installed