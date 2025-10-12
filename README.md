# dbus-mppsolar

Venus OS D-Bus service for MPP Solar inverters, specifically designed for PI30 models.

This service adapts the [dbus-serialbattery](https://github.com/mr-manuel/venus-os_dbus-serialbattery) codebase to work with MPP Solar inverters using the [mpp-solar](https://github.com/jblance/mpp-solar) Python package.

## Disclaimer

**Initial code conversion via Grok xAI**  
**Modifications and Testing by: HHaufe (spacecabbie)**

## Features

- D-Bus integration with Venus OS
- Support for PI30 inverters via serial and USB/HIDRAW connections
- Real-time monitoring and control
- Automatic inverter detection and configuration
- Comprehensive logging and error handling

## Requirements

- Venus OS (or compatible Linux system with D-Bus)
- Python 3.7+
- MPP Solar inverter (PI30 series)
- Serial or USB connection to inverter

## Installation

### Automatic Installation (Recommended)

1. Copy the `dbus-mppsolar` directory to your Venus OS device:
   ```bash
   scp -r dbus-mppsolar root@venus-device:/opt/victronenergy/
   ```

2. Run the installation script:
   ```bash
   ssh root@venus-device
   cd /opt/victronenergy/dbus-mppsolar
   ./install.sh
   ```

### Manual Installation

1. Install Python dependencies:
   ```bash
   pip3 install mpp-solar pyserial dbus-python gobject
   ```

2. Copy service file:
   ```bash
   cp service/com.victronenergy.mppsolar.service /etc/systemd/system/
   ```

3. Reload systemd and enable service:
   ```bash
   systemctl daemon-reload
   systemctl enable com.victronenergy.mppsolar.service
   systemctl start com.victronenergy.mppsolar.service
   ```

## Configuration

1. Copy the default configuration:
   ```bash
   cp config.default.ini config.ini
   ```

2. Edit `config.ini` with your inverter settings:
   - `PORT`: Serial port (e.g., `/dev/ttyUSB0`) or USB device path
   - `BAUD_RATE`: Communication baud rate (default: 2400)
   - `PROTOCOL`: MPP Solar protocol version (default: PI30)
   - `TIMEOUT`: Connection timeout in seconds

## Usage

### Starting the Service

```bash
# Using systemd
systemctl start com.victronenergy.mppsolar.service

# Or run manually
./start-mppsolar.sh
```

### Monitoring

Check service status:
```bash
systemctl status com.victronenergy.mppsolar.service
```

View logs:
```bash
journalctl -u com.victronenergy.mppsolar.service -f
```

### Testing

Run standalone tests:
```bash
python3 test/standalone_mppsolar_test.py
```

## D-Bus Paths

The service publishes the following D-Bus paths:

- `/Ac/Out/L1/V` - AC output voltage
- `/Ac/Out/L1/I` - AC output current
- `/Ac/Out/L1/P` - AC output power
- `/Ac/Out/L1/F` - AC frequency
- `/Dc/0/Voltage` - DC input voltage
- `/Dc/0/Current` - DC input current
- `/Dc/0/Power` - DC input power
- `/Connected` - Connection status (0/1)
- `/Status` - Service status (0=Offline, 1=Running)

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check USB/serial cable connection
   - Verify inverter is powered on
   - Check port permissions: `ls -la /dev/ttyUSB*`

2. **D-Bus Errors**
   - Ensure D-Bus is running: `systemctl status dbus`
   - Check service permissions

3. **Import Errors**
   - Install missing dependencies: `pip3 install mpp-solar pyserial dbus-python gobject`

### Logs

Check service logs:
```bash
journalctl -u com.victronenergy.mppsolar.service -n 50
```

## Venus OS Integration

This service integrates with Venus OS components:

- **GX devices**: Cerbo GX, CCGX, etc.
- **VRM portal**: Remote monitoring and control
- **Venus OS apps**: Display inverter data in the GUI

## Project Structure

```
dbus-mppsolar/
├── README.md                           # 📖 Project documentation and installation guide
├── pyproject.toml                      # ⚙️ Python project configuration with dependencies
├── dbus-mppsolar.py                    # 🚀 Main D-Bus service entry point and main loop
├── standalone_mppsolar_test.py         # 🧪 Standalone testing script for device connection
├── dbus-mppsolar/                      # 📁 Core service modules directory
│   ├── battery.py                      # 🔋 MPP Solar inverter device implementation
│   ├── dbushelper.py                   # 🔌 D-Bus communication helper for Venus OS
│   ├── utils.py                        # 🛠️ Configuration management and utility functions
│   ├── config.default.ini              # ⚙️ Default configuration template
│   └── dbus-mppsolar.py                # 🔄 Alternative service entry point (duplicate)
├── service/                            # 🔧 Systemd service configuration
│   └── com.victronenergy.mppsolar.service # 📋 Systemd service definition file
├── test/                               # 🧪 Testing directory
│   └── README.md                       # 📋 Test documentation and usage instructions
├── .github/                            # 🔧 GitHub repository configuration
│   └── copilot-instructions.md         # 🤖 AI assistant instructions for development
├── *.sh                                # 📜 Shell scripts for service management
│   ├── install.sh                      # 📦 Automated installation script
│   ├── uninstall.sh                    # 🗑️ Service removal script
│   ├── enable.sh                       # ✅ Enable systemd service
│   ├── disable.sh                      # ❌ Disable systemd service
│   ├── restart.sh                      # 🔄 Restart service script
│   └── start-mppsolar.sh               # ▶️ Manual service start script
├── bms/                                # 🔋 Empty directory (reserved for future BMS drivers)
├── ext/                                # 📦 Empty directory (reserved for external dependencies)
├── qml/                                # 🎨 Empty directory (reserved for QML UI components)
└── rc/                                 # 🔧 Empty directory (reserved for runtime configuration)
```

### 📁 Directory and File Details

#### **Root Level Files**
- **`README.md`** - Comprehensive project documentation including installation, configuration, usage, and troubleshooting
- **`pyproject.toml`** - Python project configuration defining dependencies (mpp-solar, pyserial, dbus-python, gobject)
- **`dbus-mppsolar.py`** - Main service entry point that initializes D-Bus, sets up the MPP service, and runs the main event loop
- **`standalone_mppsolar_test.py`** - Independent testing script to verify MPP Solar device connection and data retrieval

#### **Core Service Directory (`dbus-mppsolar/`)**
- **`battery.py`** - Implements the Battery class that handles MPP Solar inverter communication using the mpp-solar package
- **`dbushelper.py`** - D-Bus helper class that publishes inverter data to Venus OS D-Bus paths for system integration
- **`utils.py`** - Utility functions for configuration loading, logging setup, and Venus OS constants
- **`config.default.ini`** - Template configuration file with default settings for port, baud rate, protocol, and timeouts
- **`dbus-mppsolar.py`** - Alternative/duplicate service entry point (may be redundant)

#### **Service Configuration (`service/`)**
- **`com.victronenergy.mppsolar.service`** - Systemd service definition for automatic startup and management

#### **Testing (`test/`)**
- **`README.md`** - Documentation for testing procedures and expected results

#### **GitHub Configuration (`.github/`)**
- **`copilot-instructions.md`** - Instructions for AI assistants on project development guidelines and workflow

#### **Management Scripts (`*.sh`)**
- **`install.sh`** - Automated installation script that sets up dependencies, copies files, and configures systemd
- **`uninstall.sh`** - Removes the service, cleans up files, and disables systemd service
- **`enable.sh`** - Enables the systemd service for automatic startup
- **`disable.sh`** - Disables the systemd service
- **`restart.sh`** - Restarts the running service
- **`start-mppsolar.sh`** - Manual service startup script

#### **Reserved Directories**
- **`bms/`** - Empty directory reserved for future BMS (Battery Management System) driver implementations
- **`ext/`** - Empty directory for external dependencies and libraries
- **`qml/`** - Empty directory for QML user interface components (if GUI development is added)
- **`rc/`** - Empty directory for runtime configuration scripts and hooks

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Acknowledgments

- Based on [dbus-serialbattery](https://github.com/mr-manuel/venus-os_dbus-serialbattery) by mr-manuel
- Uses [mpp-solar](https://github.com/jblance/mpp-solar) package by jblance
- Compatible with [Venus OS](https://github.com/victronenergy/venus) by Victron Energy