import logging
import pathlib
from config import SOURCE_ROOT, TARGET_ROOT, FOLDER_NAMES, SELECTED_FOLDER
from reader import Reader
from transfer import Transfer

# ========= initialize logger object for logging ========= #
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    encoding="UTF-8",
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)


# ========= folder transfer logic ========= #
def transfer_folder(folder_name: str) -> None:
    source_location = pathlib.Path(SOURCE_ROOT) / folder_name
    target_location = pathlib.Path(TARGET_ROOT) / folder_name

    logger.info(f"Start transfer folder: {folder_name}")

    ### to get the list of files in the source subfolder
    try:
        path = Reader(str(source_location))
        file_list = path.get_file()
        logger.info(f"Reader Succeed! Read {len(file_list)} file(s) from {folder_name}")
    except FileNotFoundError as error:
        logger.error(f"Reader Failed [{folder_name}]: {error}")
        print(f"Reader Failed [{folder_name}]: File Not Found")
        return
    except NotADirectoryError as error:
        logger.error(f"Reader Failed [{folder_name}]: {error}")
        print(f"Reader Failed [{folder_name}]: Not A Directory")
        return
    except PermissionError as error:
        logger.error(
            f"Reader Failed [{folder_name}]: Permission to access denied! \n Message: {error}"
        )
        print(f"Reader Failed [{folder_name}]: Permission Denied")
        return
    except OSError as error:
        logger.error(f"Reader Failed [{folder_name}]: OS error! \n Message: {error}")
        print(f"Reader Failed [{folder_name}]: OS Error")
        return

    ### to transfer the files in the list to target subfolder
    try:
        Transfer.transfer_file(file_list, str(target_location))
        logger.info(
            f"Transfer Succeed! Transferred {len(file_list)} file(s) to {folder_name}"
        )  # if source and target hash list are different then will already throw error
    except FileNotFoundError as error:
        logger.error(f"Transfer Failed [{folder_name}]: {error}")
        print(f"Transfer Failed [{folder_name}]: Target File Not Found")
        return
    except NotADirectoryError as error:
        logger.error(f"Transfer Failed [{folder_name}]: {error}")
        print(f"Transfer Failed [{folder_name}]: Target Not A Directory")
        return
    except PermissionError as error:
        logger.error(
            f"Transfer Failed [{folder_name}]: Permission to access denied! \n Message: {error}"
        )
        print(f"Transfer Failed [{folder_name}]: Permission Denied")
        return
    except OSError as error:
        logger.error(f"Transfer Failed [{folder_name}]: OS error! \n Message: {error}")
        print(f"Transfer Failed [{folder_name}]: OS Error")
        return

    print(f"Transfer Succeed: {folder_name} ({len(file_list)} file(s))")


# ========= all folders transfer logic ========= #
if __name__ == "__main__":
    if SELECTED_FOLDER == "":
        folder_list = FOLDER_NAMES
    else:
        folder_list = [SELECTED_FOLDER]

    for folder_name in folder_list:
        transfer_folder(folder_name)
