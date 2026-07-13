"""
Main entry point of the app.

Wiring only. It starts the pieces and shuts them down cleanly:
1. set up logging
2. start the watchdog watcher
3. start the system tray app
4. stop the watcher when the app exits

The *how* of the watcher and tray lives in its own module (watch, ui).
"""

# python/pip packages
import logging
import os
import signal
import sys

import requests

# own modules
from file_transfer.config import (
    SOURCE_ROOT,
    FAIL_ROOT,
    CATEGORY,
    LOG_FILE,
    USER_IDS,
    SERVER_URL,
)
from file_transfer.watch.watcher import start_watching, stop_watching
from file_transfer.ui.tray import TrayApp

# In a windowed (--noconsole) build there is no console, so sys.stdout/stderr
# are None -- redirect them to nowhere so stray print() calls don't crash.
# encoding="utf-8" is ESSENTIAL: the default here is the OS ANSI codepage
# (cp1252 on many machines), which cannot encode Chinese. A stray print() of a
# Chinese folder name would then raise UnicodeEncodeError mid-transfer and kill
# the watcher thread. utf-8 encodes anything; errors="replace" is a last resort.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8", errors="replace")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8", errors="replace")

logger = logging.getLogger(__name__)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    encoding="UTF-8",
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)


def enable_dpi_awareness() -> None:
    """
    Tell Windows this app draws its own pixels at the real screen resolution.

    Without this, Windows *bitmap-stretches* the whole process on a scaled
    display (e.g. 125%/150%), which makes the file dialog, tray menu and
    popups look blurry. Declaring DPI-awareness makes them render crisp.

    Must be called BEFORE any window (Tk root, dialogs) is created.
    Wrapped in try/except because it is Windows-only and best-effort.
    """
    if sys.platform != "win32":
        return
    import ctypes

    # Try the modern "Per-Monitor v2" mode first: crisp AND it lets Windows
    # scale native UI (the tray menu, standard dialogs) to the screen's DPI.
    # Fall back to older modes on older Windows.
    try:
        # -4 = DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor
        return
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()  # oldest, system-wide
    except Exception:
        logger.warning("Could not enable DPI awareness", exc_info=True)


# ========= start watcher and tray app ========= #+
if __name__ == "__main__":
    # Ask the backend which users are registered. The slice assignment fills
    # the SAME list object everyone imported, so the User ID dialog sees the
    # fresh names. If the server is unreachable, keep the config list so the
    # app still opens -- the server re-checks every upload anyway.
    try:
        _response = requests.get(f"{SERVER_URL}/users", timeout=3)
        USER_IDS[:] = [_user["id"] for _user in _response.json()]
        logger.info(f"Fetched {len(USER_IDS)} registered user(s) from the backend")
    except OSError as error:
        logger.warning(f"Could not fetch users from backend, using config list: {error}")

    # Crisp (not blurry) windows on scaled displays -- must run before Tk starts.
    enable_dpi_awareness()

    # Start tray app. On exit, stop the watcher.
    tray_app = TrayApp(SOURCE_ROOT, CATEGORY, on_exit=lambda: stop_watching(observer))

    # Start watching source (schedules, transfers existing files, starts thread).
    observer = start_watching(
        SOURCE_ROOT,
        FAIL_ROOT,
        CATEGORY,
        tray_app.display_notification,
        tray_app.display_error,
    )

    def handle_ctrl_c(signum, frame) -> None:
        """
        Handle Ctrl+C from terminal.

        signum and frame are passed by Python's signal module.
        We do not need to use them here.
        """
        logger.info("Ctrl+C received, exiting app")
        tray_app.request_exit()

    # Connect terminal Ctrl+C to our clean shutdown.
    signal.signal(signal.SIGINT, handle_ctrl_c)

    try:
        tray_app.run()

    except KeyboardInterrupt:
        tray_app.request_exit()

    finally:
        stop_watching(observer)
