#!/bin/bash
# Wrapper script to run mpp-solar from the submodule on Venus OS
# This avoids Python package installation conflicts

MPP_SOLAR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/mpp-solar" && pwd)"
cd "$MPP_SOLAR_DIR"

# Set PYTHONPATH and run mpp-solar
PYTHONPATH="$MPP_SOLAR_DIR" python3 -c "import sys; sys.argv[0] = 'mpp-solar'; from mppsolar import main; main()" "$@"