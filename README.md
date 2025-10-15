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

#### Direct MPP Solar Communication

For direct communication with your MPP Solar inverter (useful for testing and debugging), use the provided wrapper script:

```bash
# Get device protocol info
./run-mpp-solar.sh -p /dev/hidraw0 -c QPI

# Get full inverter status
./run-mpp-solar.sh -p /dev/hidraw0 -c QPIGS

# Get device mode
./run-mpp-solar.sh -p /dev/hidraw0 -c QMOD

# With debug output
./run-mpp-solar.sh -p /dev/hidraw0 -c QPIGS -D

# List available commands for PI30 protocol
./run-mpp-solar.sh -P PI30 -c
```

**Note:** The `run-mpp-solar.sh` script is specifically designed for Venus OS to avoid Python package installation conflicts. It provides direct access to all mpp-solar functionality without requiring package installation.

## D-Bus Paths

The service publishes the following D-Bus paths:

### Inverter Data Paths
- `/Ac/Out/L1/V` - AC output voltage
- `/Ac/Out/L1/I` - AC output current
- `/Ac/Out/L1/P` - AC output power
- `/Ac/Out/L1/F` - AC frequency
- `/Dc/0/Voltage` - DC input voltage
- `/Dc/0/Current` - DC input current
- `/Dc/0/Power` - DC input power

### Device Information Paths
- `/DeviceInstance` - Device instance ID (dynamically assigned)
- `/ProductId` - Product ID
- `/ProductName` - Product name
- `/FirmwareVersion` - Firmware version
- `/Connected` - Connection status (0/1)
- `/Status` - Service status (0=Offline, 1=Running)

### Management Paths
- `/Mgmt/ProcessName` - Process name (default: "dbus-mppsolar")
- `/Mgmt/ProcessVersion` - Process version (default: "1.0.0")
- `/Mgmt/Connection` - Connection type (auto-detected: "USB HID", "Serial USB", "Serial ACM", etc.)

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

### Configuration

Edit `/data/apps/dbus-mppsolarv2/dbus_mppsolar/config.ini`:

```ini
[MPPSOLAR]
PORT = /dev/ttyUSB0          # Serial port (check with ls /dev/ttyUSB*)
BAUD_RATE = 2400            # Communication baud rate
PROTOCOL = PI30             # MPP Solar protocol
TIMEOUT = 5                 # Connection timeout in seconds

[DBUS]
SERVICE_NAME = com.victronenergy.inverter  # D-Bus service name
DEVICE_INSTANCE = 0         # Unique device instance (auto-assigned if in use)
```

**Device Instance Configuration:**
- Set `DEVICE_INSTANCE = 0` for the first inverter
- For multiple inverters, use different instance numbers (0, 1, 2, etc.)
- If the configured instance is already in use, the service will auto-assign the next available instance
- The service name becomes `com.victronenergy.inverter.{instance}`

**Find the correct serial port:**
```bash
ls /dev/ttyUSB* /dev/ttyACM* /dev/ttyS*
dmesg | grep tty  # Check recent serial device connections
```

### Testing

#### 1. Standalone Connection Test

Test the MPP Solar device connection independently:

```bash
cd /data/apps/dbus-mppsolarv2
python3 standalone_mppsolar_test.py
```

Expected output:
```
MPP Solar Device Test
=====================
Port: /dev/ttyUSB0
Baud Rate: 2400
Protocol: PI30

Testing connection...
✓ Connection successful!
Device Info: {...}
Status Data: {...}
```

#### 2. Direct MPP Solar Communication Test

Test direct communication with the inverter using the wrapper script:

```bash
# Basic connectivity test
./run-mpp-solar.sh -p /dev/hidraw0 -c QPI

# Full status test
./run-mpp-solar.sh -p /dev/hidraw0 -c QPIGS -I
```

This bypasses the D-Bus service and tests raw inverter communication.

#### 3. Service Status Check

```bash
# Check if service is running
systemctl status com.victronenergy.mppsolar.service

# View service logs
journalctl -u com.victronenergy.mppsolar.service -f

# Restart service
systemctl restart com.victronenergy.mppsolar.service
```

#### 3. D-Bus Path Verification

Check if D-Bus paths are published correctly:

```bash
# List all D-Bus services
dbus -y com.victronenergy.inverter /DeviceInstance GetValue

# Check specific paths
dbus -y com.victronenergy.inverter /Ac/Out/L1/V GetValue
dbus -y com.victronenergy.inverter /Connected GetValue
dbus -y com.victronenergy.inverter /ProductName GetValue
```

```
dbus-mppsolarv2/
├── README.md                           # 📖 Project documentation and installation guide
├── pyproject.toml                      # ⚙️ Python project configuration with dependencies
├── dbus-mppsolar.py                    # 🚀 Main D-Bus service entry point and main loop
├── standalone_mppsolar_test.py         # 🧪 Standalone testing script for device connection
├── mpp-solar/                          # 📦 MPP Solar communication library (git submodule)
├── dbus-mppsolar/                      # 📁 Core service modules directory
│   ├── inverter.py                     # 🔋 MPP Solar inverter device implementation
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
│   ├── start-mppsolar.sh               # ▶️ Manual service start script
│   └── run-mpp-solar.sh                # 🔧 Direct MPP Solar communication wrapper
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

#### **MPP Solar Library (`mpp-solar/`)**
- **`mpp-solar/`** - Git submodule containing the MPP Solar communication library for inverter protocol handling

#### **Core Service Directory (`dbus-mppsolar/`)**
- **`inverter.py`** - Implements the Inverter class that handles MPP Solar inverter communication using the mpp-solar package
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
- **`bms/`** - Empty directory reserved for future BMS (Inverter Management System) driver implementations
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

## Code Architecture & Flow Diagrams

### 🏗️ Class Diagram

```mermaid
classDiagram
    class MPPService {
        +inverter: Inverter
        +dbus_helper: DbusHelper
        +mainloop: MainLoop
        +running: bool
        +__init__()
        +setup() bool
        +run() void
        -_update_data() bool
        -_signal_handler(signum, frame) void
    }

    class Inverter {
        +port: str
        +baud_rate: int
        +protocol: str
        +mpp_device: MPP
        +online: bool
        +voltage: float
        +current: float
        +power: float
        +ac_voltage: float
        +ac_current: float
        +frequency: float
        +__init__(port, baud, address)
        +test_connection() bool
        +refresh_data() bool
        -_init_device() void
        -_parse_status_data(data) void
        +get_settings() bool
        +unique_identifier() str
        +connection_name() str
        +custom_name() str
        +product_name() str
        +use_callback(callback) bool
        +get_allow_to_charge() bool
        +get_allow_to_discharge() bool
        +validate_data() bool
    }

    class DbusHelper {
        +inverter: Inverter
        +dbus_service: VeDbusService
        +_paths: Dict
        +_dbus_paths: Dict
        +__init__(battery)
        +setup_vedbus() bool
        +publish_inverter() bool
        +publish_dbus() bool
    }

    class Utils {
        +logger: Logger
        +config: ConfigParser
        +get_config_value(key, section, default) Any
        +get_bool_from_config(key, section, default) bool
        +safe_number_format(value, format) str
    }

    MPPService --> Inverter : creates
    MPPService --> DbusHelper : creates
    Inverter --> Utils : uses
    DbusHelper --> Utils : uses
    DbusHelper --> Inverter : monitors

    note for MPPService "Main service orchestrator\nManages service lifecycle"
    note for Inverter "MPP Solar device handler\nCommunicates with inverter"
    note for DbusHelper "D-Bus interface manager\nPublishes data to Venus OS"
    note for Utils "Configuration & utilities\nLogging, config loading"
```

### 🔄 Execution Flow Diagram

```mermaid
flowchart TD
    A["dbus-mppsolar.py"] --> B["main()"]
    B --> C["DBusGMainLoop set_as_default=True"]
    C --> D["Create MPPService instance"]
    D --> E["service.setup()"]
    E --> F{"Setup successful?"}
    F -->|"No"| G["Log error & exit"]
    F -->|"Yes"| H["service.run()"]

    H --> I["Setup signal handlers"]
    I --> J["Publish initial data"]
    J --> K["Create GLib MainLoop"]
    K --> L["Add periodic timer every 1000ms"]
    L --> M["Start main loop blocking call"]

    M --> N["_update_data timer fires"]
    N --> O["inverter.refresh_data()"]
    O --> P{"Data refresh successful?"}
    P -->|"Yes"| Q["dbus_helper.publish_inverter()"]
    P -->|"No"| R["Log error"]
    Q --> S["Return True continue timer"]
    R --> S

    M --> T["Signal received SIGTERM/SIGINT"]
    T --> U["_signal_handler called"]
    U --> V["mainloop.quit()"]
    V --> W["Set running = False"]
    W --> X["Exit main loop"]
    X --> Y["Service shutdown complete"]

    classDef entry fill:#e1f5fe
    classDef setup fill:#f3e5f5
    classDef runtime fill:#e8f5e8
    classDef update fill:#fff3e0
    classDef shutdown fill:#ffebee

    class A entry
    class B,C,D,E setup
    class H,I,J,K,L,M runtime
    class N,O,P,Q,R,S update
    class T,U,V,W,X,Y shutdown
```

### 📊 Sequence Diagram

```mermaid
sequenceDiagram
    participant M as main()
    participant S as MPPService
    participant B as Inverter
    participant D as DbusHelper
    participant DB as D-Bus

    M->>S: MPPService()
    S->>B: Inverter()
    B->>B: _init_device()
    B->>B: test_connection()
    S->>D: DbusHelper(battery)
    D->>D: setup_vedbus()
    D->>DB: Create VeDbusService
    D->>DB: Add D-Bus paths

    M->>S: setup()
    S->>B: test_connection()
    B-->>S: connection result
    S->>D: setup_vedbus()
    D-->>S: setup result
    S-->>M: setup result

    M->>S: run()
    S->>D: publish_battery()
    D->>DB: Publish initial data
    S->>S: Setup signal handlers
    S->>S: Create MainLoop
    S->>S: Add timer 1000ms

    loop Periodic updates
        S->>S: _update_data()
        S->>B: refresh_data()
        B->>B: get_general_status()
        B->>B: _parse_status_data()
        B-->>S: data
        S->>D: publish_battery()
        D->>DB: Update D-Bus paths
    end

    Note over M,DB: Service runs until signal received
    M->>S: Signal handler
    S->>S: mainloop.quit()
```

### 🔧 Data Flow & Dependencies

```mermaid
graph LR
    subgraph "Configuration Layer"
        CFG["config.default.ini"] --> U["utils.py"]
        CFG --> B["inverter.py"]
    end

    subgraph "Communication Layer"
        MPP["mpp-solar/ (submodule)"] --> B
        SERIAL["Serial Port /dev/ttyUSB0"] --> B
    end

    subgraph "Service Layer"
        B --> S["dbus-mppsolar.py MPPService"]
        U --> S
        D["dbushelper.py DbusHelper"] --> S
    end

    subgraph "Integration Layer"
        S --> DBUS["D-Bus System Bus"]
        D --> DBUS
        DBUS --> VRM["Venus OS VRM Portal"]
        DBUS --> GUI["Venus OS GUI Apps"]
    end

    subgraph "Management Layer"
        INST["install.sh"] --> SYS["systemd service"]
        EN["enable.sh"] --> SYS
        START["start-mppsolar.sh"] --> S
        TEST["standalone_mppsolar_test.py"] --> B
    end

    classDef config fill:#e3f2fd
    classDef comm fill:#f3e5f5
    classDef service fill:#e8f5e8
    classDef integration fill:#fff3e0
    classDef management fill:#fce4ec

    class CFG config
    class MPP,SERIAL comm
    class B,U,S,D service
    class DBUS,VRM,GUI integration
    class INST,EN,START,TEST,SYS management
```

### 📋 Component Relationships Explained

#### **Class Relationships:**
- **MPPService** → **Battery**: Creates and manages the battery instance
- **MPPService** → **DbusHelper**: Creates and manages the D-Bus interface
- **Battery** → **Utils**: Uses logging and configuration utilities
- **DbusHelper** → **Utils**: Uses logging and D-Bus constants
- **DbusHelper** → **Battery**: Monitors battery data for publishing

#### **Execution Flow:**
1. **Entry Point**: `dbus-mppsolar.py:main()` initializes D-Bus and creates service
2. **Setup Phase**: Service initializes battery connection and D-Bus interface
3. **Runtime Phase**: Main loop runs with periodic data updates every 1 second
4. **Data Flow**: Battery → MPPService → DbusHelper → D-Bus → Venus OS
5. **Shutdown**: Signal handlers gracefully stop the service

#### **Key Data Paths:**
- **AC Data**: `ac_voltage`, `ac_current`, `ac_power`, `frequency`
- **DC Data**: `voltage`, `current`, `power` (mapped from AC for compatibility)
- **Status**: `online`, `connection_info`, `soc`, `capacity`
- **D-Bus Paths**: `/Ac/Out/L1/*`, `/Dc/0/*`, `/Connected`, `/Status`


This architecture provides a clean separation between device communication, data processing, and system integration, making it maintainable and extensible for Venus OS compatibility.
