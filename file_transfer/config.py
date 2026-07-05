"""
App configuration.

Settings are loaded from config.json (sitting next to the app) instead of being
hardcoded here, so paths and options can be edited without touching the code.
This module reads that file once at startup and exposes the same names the rest
of the app imports -- so nothing else needs to change.

Where config.json is looked for:
- normal run (python -m file_transfer): next to this file
- packaged .exe (PyInstaller): next to the executable, so users can edit it
"""

import sys
import json
import pathlib

# Decide where to look for config.json.
if getattr(sys, "frozen", False):
    # running as a bundled .exe -> look next to the executable (user-editable)
    _base_dir = pathlib.Path(sys.executable).parent
else:
    # running from source -> look next to this config.py
    _base_dir = pathlib.Path(__file__).parent

_config_path = _base_dir / "config.json"

with _config_path.open(encoding="utf-8") as _file:
    _config = json.load(_file)

# Expose the same names the rest of the app already imports.
SOURCE_ROOT = _config["source_root"]
TARGET_ROOT = _config["target_root"]
FAIL_ROOT = _config["fail_root"]
ALLOWED_EXT = _config["allowed_ext"]
SELECTED_FOLDER = _config["selected_folder"]
CATEGORY = _config["category"]
