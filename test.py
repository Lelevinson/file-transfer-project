import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="test.log",
    encoding="utf-8",
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s",
)

try:
    raise OSError
except OSError as error:
    logger.exception(f"this is test")
