# dbus-mppsolar Project Instructions

## Project Status
- [x] Verify that the copilot-instructions.md file in the .github directory is created.
- [x] Clarify Project Requirements: Venus OS inverter driver adapting dbus-serialbattery to use mpp-solar package for PI30 inverters
- [x] Scaffold the Project: Created complete project structure with all necessary files and directories
- [x] Customize the Project: Adapted dbus-serialbattery codebase for MPP Solar inverter integration
- [x] Install Required Extensions: No extensions required for this Python project
- [x] Compile the Project: Dependencies installed, project ready for testing
- [x] Create and Run Task: No build tasks required for Python project
- [x] Launch the Project: Service can be launched via systemd or manual execution
- [x] Ensure Documentation is Complete: README.md and project documentation updated

## Project Overview
This is a Venus OS D-Bus service for MPP Solar inverters (PI30 series) that adapts the dbus-serialbattery codebase to use the mpp-solar Python package for communication.

## Key Components
- `dbus-mppsolar.py`: Main service entry point with D-Bus integration
- `battery.py`: MPP Solar device implementation
- `dbushelper.py`: D-Bus helper for Venus OS paths
- `utils.py`: Configuration and utility functions
- Service files for systemd integration
- Installation and management scripts

## Development Guidelines
- Follow Venus OS D-Bus API specifications
- Maintain compatibility with existing dbus-serialbattery patterns
- Use mpp-solar package for inverter communication
- Ensure proper error handling and logging
- Test on Venus OS environment before deployment

## Testing
- Use `standalone_mppsolar_test.py` for connection testing
- Verify D-Bus paths are published correctly
- Test on actual Venus OS hardware when possible

## Deployment
- Install via `install.sh` script on Venus OS
- Service runs as systemd service
- Monitor via journalctl and systemctl