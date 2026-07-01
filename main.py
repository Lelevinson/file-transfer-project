# py modules
import time
import logging

# own modules
from config import SOURCE_ROOT, TARGET_ROOT, FOLDER_NAMES, SELECTED_FOLDER
from watcher import AppHandler, observer

# ========= initialize logger object for logging ========= #
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    encoding="UTF-8",
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)


# ========= all folders transfer logic ========= #
if __name__ == "__main__":
    handler = AppHandler(SOURCE_ROOT, TARGET_ROOT)
    observer.schedule(event_handler=handler, path=SOURCE_ROOT, recursive=True)
    handler.initial_transfer()
    observer.start()

    try:
        while observer.is_alive():
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
