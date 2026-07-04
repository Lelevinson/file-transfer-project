"""
Main entry point of the app.

This file starts the app directly:
1. Start watchdog watcher
2. Start system tray app
3. Cleanly stop both when app exits
"""

# python/pip packages
import logging
import signal

# own modules
from file_transfer.config import SOURCE_ROOT, TARGET_ROOT, CATEGORY
from file_transfer.ui.tray import TrayApp
from file_transfer.watch.watcher import AppHandler, observer

# ========= initialize logger object for logging ========= #
logger = logging.getLogger(__name__)

logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    encoding="UTF-8",
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)


# ========= watcher helper ========= #
def stop_watcher() -> None:
    """
    Stop watchdog observer if it is currently running.
    """
    if observer.is_alive():
        observer.stop()


# ========= start watcher and tray app ========= #
if __name__ == "__main__":
    # Create our custom watchdog event handler.
    handler = AppHandler(SOURCE_ROOT, TARGET_ROOT)

    # Watch source root, including all category subfolders.
    observer.schedule(
        event_handler=handler,
        path=SOURCE_ROOT,
        recursive=True,
    )

    # Transfer existing files once when app starts.
    handler.initial_transfer()

    # Start watching for new files.
    observer.start()

    # Start tray app.
    tray_app = TrayApp(SOURCE_ROOT, CATEGORY, on_exit=stop_watcher)

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
        stop_watcher()
        observer.join()
