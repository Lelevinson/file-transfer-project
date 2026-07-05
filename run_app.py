"""
Packaging launcher.

PyInstaller needs a single entry script, but the app is a package normally run
with `python -m file_transfer`. This reproduces that exactly, so the frozen
.exe behaves the same as running the module from source.
"""

import runpy

runpy.run_module("file_transfer", run_name="__main__")
