#!/bin/bash
# Wrapper: loads env and runs tracker.py with all arguments
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/env.sh"
exec python3 "$SCRIPT_DIR/tracker.py" "$@"
