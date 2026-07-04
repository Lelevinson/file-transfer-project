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
import signal

# own modules
from file_transfer.config import SOURCE_ROOT, TARGET_ROOT, CATEGORY
from file_transfer.watch.watcher import start_watching, stop_watching
from file_transfer.ui.tray import TrayApp

logger = logging.getLogger(__name__)

logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    encoding="UTF-8",
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)


# ========= start watcher and tray app ========= #
if __name__ == "__main__":
    # Start watching source (schedules, transfers existing files, starts thread).
    observer = start_watching(SOURCE_ROOT, TARGET_ROOT)

    # Start tray app. On exit, stop the watcher.
    tray_app = TrayApp(SOURCE_ROOT, CATEGORY, on_exit=lambda: stop_watching(observer))

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
