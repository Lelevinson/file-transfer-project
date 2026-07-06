# Building the app + installer

> Build with a **standard python.org Python (3.13/3.14)** venv — **not** a
> Conda-based one. Conda hides core DLLs (libffi, tcl/tk) in places PyInstaller
> can't find, which breaks the frozen exe. Our `.venv` is built on standard
> Python for this reason.

## 1. Build the `.exe` (PyInstaller)

From the project root:

```
.venv/Scripts/python.exe -m PyInstaller --name FileTransfer --noconfirm --windowed --icon=assets/app.ico \
  --collect-submodules file_transfer --collect-submodules pystray --collect-submodules watchdog \
  run_app.py
```

- `run_app.py` is the entry point (reproduces `python -m file_transfer`).
- `--windowed` = no console window. `--icon` sets the exe/notification icon.
- `--collect-submodules` bundles dynamically-imported backends (pystray/watchdog).

Output: `dist/FileTransfer/` (the app folder).

Then place the **shippable** `config.json` (relative paths, so it's self-contained)
next to the exe — `dist/FileTransfer/config.json`:

```json
{ "source_root": "source", "target_root": "target", "fail_root": "fail", ... }
```

## 2. Build the installer (Inno Setup)

```
"C:\Users\user\AppData\Local\Programs\Inno Setup 6\ISCC.exe" installer.iss
```

Output: `installer_output/FileTransfer-Setup.exe` — the shareable installer.
It installs to `Documents\FileTransfer` (writable, no admin), creates
`source/target/fail/logs`, and adds Start-menu + desktop shortcuts.

## Notes

- The installer is **unsigned**, so Windows SmartScreen / Smart App Control warns
  "unknown publisher" — click "install anyway" (fine for a demo). Removing that
  warning needs a paid code-signing certificate or IT whitelisting.
- The mock user list + startup target-folder "registration" are **temporary
  demo scaffolding** (see the code comments marked `DEMO ONLY`) — replace with
  the server API later.
