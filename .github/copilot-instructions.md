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
- `inverter.py`: MPP Solar device implementation
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

## AI contributor instructions — dbus-mppsolar

Short goal: maintain the Venus OS D-Bus service that exposes MPP Solar (PI30) inverter data using the bundled `mpp-solar` submodule.

Keep this doc short and actionable. When making changes, reference these canonical files and examples in the repo:

- Entry points: `dbus-mppsolar.py` (root) and `dbus_mppsolar/dbus-mppsolar.py`
- Device implementation: `dbus_mppsolar/inverter.py`
- D-Bus publishing: `dbus_mppsolar/dbushelper.py`
- Config & helpers: `dbus_mppsolar/utils.py` and `dbus_mppsolar/config.default.ini`
- Tests & quick checks: `standalone_mppsolar_test.py`
- Installer and service: `install.sh`, `service/com.victronenergy.mppsolar.service`, `start-mppsolar.sh`

Essential context and patterns
- Architecture: a small orchestrator (main -> MPPService) creates an `Inverter` instance (wraps the `mpp-solar` device) and a `DbusHelper` that maps device fields to Venus OS D-Bus paths. The main loop uses GLib timers (~1s) to call `inverter.refresh_data()` and then `dbus_helper.publish_inverter()`.
- Error handling: device communication is unstable by design; prefer conservative retries and clear logging. Check `inverter.test_connection()` and `inverter.refresh_data()` semantics when modifying polling or timeouts.
- Configuration: runtime settings live in `dbus_mppsolar/config.ini` (from `config.default.ini`). Prefer reading config via `utils.get_config_value()` to keep behaviour consistent.
- Naming & mapping: D-Bus paths use Venus OS conventions (e.g. `/Ac/Out/L1/V`, `/Dc/0/Voltage`, `/Connected`). When adding new metrics, mirror existing naming in `dbushelper.py` to avoid GUI/VRM breakage.

Developer workflows (commands you will use)
- Run service manually (foreground): `python3 dbus-mppsolar.py` or `./start-mppsolar.sh` (shell script sets environment similar to systemd).
- Run standalone device test: `python3 standalone_mppsolar_test.py` (useful for debugging serial/USB issues).
- Install on Venus OS (what CI/devs use on device): `./install.sh` (this copies service file and enables systemd unit). Check `service/` for unit options.
- View logs: `journalctl -u com.victronenergy.mppsolar.service -f` (for systemd) or stdout from the foreground run.

Project-specific conventions
- mpp-solar is included as a submodule under `mpp-solar/`; prefer using its device API via `dbus_mppsolar/inverter.py` wrapper rather than importing it directly across modules.
- Keep D-Bus exposure stable: adding or renaming paths can break VRM/GUI. Add new paths only when necessary and document them in `README.md`.
- Tests: there are no unit tests for most modules; use `standalone_mppsolar_test.py` and manual runs. When adding tests, keep them light and device-independent (mock serial or use a simulated device).
- Development history: Adapted from dbus-serialbattery codebase; handle submodule imports by adding `sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mpp-solar"))` if needed. Map inverter status dict to D-Bus paths in `update_paths_from_status()`. Add detailed docstrings and inline comments for all code. Include "commit by: Grok" in AI-generated commit messages.

Integration points and external dependencies
- mpp-solar submodule (protocol implementations) — see `mpp-solar/`.
- System D-Bus (system bus) — code creates a VeDbusService and registers paths on the system bus.
- Systemd service file: `service/com.victronenergy.mppsolar.service`.
- Hardware: serial/USB/HIDRAW device nodes (e.g., `/dev/ttyUSB0`, `/dev/hidraw*`). Code assumes POSIX devices and typical serial permissions.

Small examples (where to change things)
- To add a new published value: update `dbushelper._paths` and the publish logic in `dbushelper.publish_inverter()`; add mapping/formatting helpers in `utils.safe_number_format()` if needed.
- To change polling interval: edit the GLib timer setup in `dbus_mppsolar/dbus-mppsolar.py` (search for add_timeout or MainLoop timers).
- To support another protocol variant: adapt `inverter._init_device()` to instantiate the correct `mpp-solar` device and map responses in `_parse_status_data()`.
- To handle import issues: add sys.path.insert for submodule paths before imports.

Quality gates
- Before PR: run `python3 standalone_mppsolar_test.py` and a quick static lint (flake8/pyproject dependencies if present). Ensure no new D-Bus path names or config keys are added without updating `README.md`. Add detailed comments and Grok disclaimer to new code.

Development patterns and troubleshooting
- Expect iterative fixes: import issues often require multiple approaches (direct module loading for Python version compatibility, path adjustments for submodules)
- Test incrementally: start with standalone scripts, then D-Bus path verification, finally full service deployment
- Handle Python compatibility: use importlib for direct module loading when __init__.py causes syntax errors
- Maintain path consistency: update all references (/data/apps/dbus-mppsolarv2) across scripts, services, and docs
- Debug imports: check sys.path includes mpp-solar/mppsolar, use importlib.util for problematic modules

If anything here is unclear or you want more examples (tests, mocking serial devices, or mapping tables), tell me which area and I will expand this doc.
