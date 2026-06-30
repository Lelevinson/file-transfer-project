import logging
from config import SOURCE_LOCATION, TARGET_LOCATION
from reader import Reader
from transfer import Transfer
from utils import dd

# ========= initialize logger object for logging ========= #
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="error.log",
    level=logging.INFO,
    encoding="UTF-8",
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)

# ========= transfer logic ========= #
if __name__ == "__main__":
    path = Reader(SOURCE_LOCATION)
    ### to get the list of files in the source directory
    try:  # Errors will be handled if we cannot access the files
        file_list = path.get_file()
        logger.info(f"Reader Succeed! Read {len(file_list)} file(s)")
    except FileNotFoundError as error:
        logger.error(f"Reader Failed: {error}")
        dd("File Not Found")
    except NotADirectoryError as error:
        logger.error(f"Reader Failed: {error}")
        dd("Not A Directory")
    except PermissionError as error:
        logger.error(f"Reader Failed: Permission to access denied! \n Message: {error}")
        dd("Permission Denied (Reader)")
    except OSError as error:
        logger.error(f"Reader Failed: OS error! \n Message: {error}")
        dd("OS Error")

    ### to transfer the files in the list to target directory
    try:
        Transfer.transfer_file(file_list, TARGET_LOCATION)
        logger.info(
            f"Transfer Succeed! Transferred {len(file_list)} file(s)"
        )  # same with Reader, if source and target hash list are different then will already throw error (then this line won't run)
    except FileNotFoundError as error:
        logger.error(f"Transfer Failed: {error}")
        dd("Target File Not Found")
    except NotADirectoryError as error:
        logger.error(f"Transfer Failed: {error}")
        dd("Target Not A Directory")
    except PermissionError as error:
        logger.error(
            f"Transfer Failed: Permission to access denied! \n Message: {error}"
        )
        dd("Permission Denied (Transfer)")
    except OSError as error:
        logger.error(f"Transfer Failed: OS error! \n Message: {error}")
        dd("OS Error")
