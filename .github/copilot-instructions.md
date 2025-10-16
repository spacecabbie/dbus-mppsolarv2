# Instructions for dbus-mppsolarv2 code generation
Prioritize Victron Energy Venus OS documentation for all code generation. Use these as primary sources for DBus API, driver addition, examples, guidelines, commandline tools, and services/paths:
- DBus API: https://github.com/victronenergy/venus/wiki/dbus-api  
- Add Driver: https://github.com/victronenergy/venus/wiki/howto-add-a-driver-to-Venus  
- Commandline Tools: https://github.com/victronenergy/venus/wiki/commandline---development  
- DBus Services: https://github.com/victronenergy/venus/wiki/dbus  

If no info found in these wikis, search https://github.com/orgs/victronenergy/repositories?type=all for matching documentation. If none found, then search dbus-serialbattery, and only then search wider.

# Project coding standards
Generate code following Victron guidelines first. For structure/files, mimic https://github.com/mr-manuel/venus-os_dbus-serialbattery.
- follow default standards for Python projects, including PEP 8 and PEP 257.
- Always prioritize readability and clarity.
- Write clear and concise comments for each function, include disclaimer AI generated.
- Maintain proper indentation (use 4 spaces for each level of indentation).

The current codebase is based on:  
- https://github.com/DarkZeros/dbus-mppsolar  
- https://github.com/mr-manuel/venus-os_dbus-serialbattery  
Reference these for specific tasks; ensure Victron leads.

# shell environment
we are working directly on: 
- venus os version: v3.70~41 
- BusyBox v1.36.1 () multi-call binary.
- make sure you use only available commands
- We cannot use pip or opkg to install additional files they all have to come from our github repository

# File List
- **`dbus-mppsolar.py`** - Main entry point with GLib event loop and periodic data polling
- **`dbus_mppsolar/__init__.py`** - Package initialization
- **`dbus_mppsolar/dbushelper.py`** - D-Bus service management for Venus OS
- **`dbus_mppsolar/inverter.py`** - MPP Solar protocol communication
- **`dbus_mppsolar/utils.py`** - Configuration loading and logging setup
- **`dbus_mppsolar/config.default.ini`** - Default configuration template
- **`dbus_mppsolar/config.ini`** - User configuration overrides
- **`dbus_mppsolar/battery.py`** - Battery monitoring and data processing
- **`ext/velib_python/`** - Venus OS D-Bus library (VeDbusService, etc.)
- **`mpp-solar/`** - MPP Solar protocol library for device communication
- **`install.sh`** - Installation script
- **`uninstall.sh`** - Removal script
- **`start-mppsolar.sh`** - Service startup script
- **`restart.sh`** - Service restart
- **`enable.sh`** - Service enable script
- **`disable.sh`** - Service disable script
- **`standalone_mppsolar_test.py`** - Standalone testing without D-Bus
- **`debug_import.py`** - Import debugging utility
- **`README.md`** - Project documentation
- **`pyproject.toml`** - Project configuration
- **`test/`** - Test directory structure
- **`utils/`** - Development utilities (BLE tools, etc.)
- **`qml/`** - QML interface files
- **`rc/`** - Resource files
- **`service/`** - Service configuration files
- **`bms/`** - Battery management system files
