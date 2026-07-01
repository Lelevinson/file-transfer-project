# python/pip packages
import pathlib
import logging

# own packages
from reader import Reader
from transfer import Transfer

# ========= app own logger object ========= #
logger = logging.getLogger(__name__)


# ========= folder transfer logic ========= #
def transfer_folder(
    folder_name: str, source_root: pathlib.Path, target_root: pathlib.Path
) -> None:
    source_location = pathlib.Path(source_root) / folder_name
    target_location = pathlib.Path(target_root) / folder_name

    logger.info(f"Start transfer folder: {folder_name}")

    ### to GET the list of files in the source subfolder
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
            f"Reader Failed [{folder_name}]: Permission to access denied! \nMessage: {error}"
        )
        print(f"Reader Failed [{folder_name}]: Permission Denied")
        return
    except OSError as error:
        logger.error(f"Reader Failed [{folder_name}]: OS error! \nMessage: {error}")
        print(f"Reader Failed [{folder_name}]: OS Error")
        return

    ### to TRANSFER the files in the list to target subfolder
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
            f"Transfer Failed [{folder_name}]: Permission to access denied! \nMessage: {error}"
        )
        print(f"Transfer Failed [{folder_name}]: Permission Denied")
        return
    except OSError as error:
        logger.error(f"Transfer Failed [{folder_name}]: OS error! \nMessage: {error}")
        print(f"Transfer Failed [{folder_name}]: OS Error")
        return

    print(f"Transfer Succeed: {folder_name} ({len(file_list)} file(s))")
