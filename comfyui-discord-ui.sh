#!/bin/bash

# https://stackoverflow.com/a/1482133
SCRIPT_DIR="$(dirname -- "$(readlink -f -- "$0";)";)"
cd "$SCRIPT_DIR"

source ./venv/bin/activate
python3 -u bot.py
