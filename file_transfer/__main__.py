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
import pathlib
import signal

# own modules
from file_transfer.config import (
    SOURCE_ROOT,
    TARGET_ROOT,
    FAIL_ROOT,
    CATEGORY,
    LOG_FILE,
    USER_IDS,
)
from file_transfer.watch.watcher import start_watching, stop_watching
from file_transfer.ui.tray import TrayApp

logger = logging.getLogger(__name__)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    encoding="UTF-8",
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)


# ========= start watcher and tray app ========= #
if __name__ == "__main__":
    # DEMO ONLY: "register" the mock users by creating their target folders so
    # their transfers succeed. Remove this once the real server owns the user
    # list and the target side becomes an API instead of local folders.
    for _user in USER_IDS:
        for _cat in CATEGORY:
            pathlib.Path(TARGET_ROOT, _user, _cat).mkdir(parents=True, exist_ok=True)

    # Start tray app. On exit, stop the watcher.
    tray_app = TrayApp(SOURCE_ROOT, CATEGORY, on_exit=lambda: stop_watching(observer))

    # Start watching source (schedules, transfers existing files, starts thread).
    observer = start_watching(
        SOURCE_ROOT,
        TARGET_ROOT,
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
