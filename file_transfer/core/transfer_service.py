"""
Transfer service.

Combines the reader and the file operations into one action: transfer all
files in a category folder from the source to the matching target folder.
This is what the watcher calls for each folder.
"""

import pathlib
import logging

from file_transfer.core.source_reader import Reader
from file_transfer.core.file_mover import Transfer
from file_transfer.core.policy_filter import filter_by_policy

# ========= app own logger object ========= #
logger = logging.getLogger(__name__)


# ========= folder transfer logic ========= #
def process_folder(
    source_root: pathlib.Path, target_root: pathlib.Path, user_id: str, category: str
) -> tuple[list[pathlib.Path], list[pathlib.Path]] | None:
    source_location = pathlib.Path(source_root) / user_id / category
    target_location = pathlib.Path(target_root) / user_id / category

    user_folder = f"{user_id}/{category}"

    logger.info(f"Start transfer folder: {user_folder}")

    ### to GET the list of files in each user's subfolder categories
    try:
        path = Reader(str(source_location))
        file_list = path.get_file()
        allowed_file_list, rejected_file_list = filter_by_policy(file_list)
        logger.info(
            f"Reader Succeed! Read {len(file_list)} file(s) from {user_folder}\nAllowed Files: {[*allowed_file_list]}\nRejected Files: {[*rejected_file_list]}"
        )
    except FileNotFoundError as error:
        logger.error(f"Reader Failed [{user_folder}]: {error}")
        return
    except NotADirectoryError as error:
        logger.error(f"Reader Failed [{user_folder}]: {error}")
        return
    except PermissionError as error:
        logger.error(
            f"Reader Failed [{user_folder}]: Permission to access denied! \nMessage: {error}"
        )
        return
    except OSError as error:
        logger.error(f"Reader Failed [{user_folder}]: OS error! \nMessage: {error}")
        return

    ### to TRANSFER the files in the list to target subfolder
    try:
        Transfer.transfer_file(allowed_file_list, str(target_location))
        logger.info(
            f"Transfer Succeed! Transferred {len(allowed_file_list)} allowed file(s) to {user_folder}\nFiles: {[*allowed_file_list]}"
        )  # if source and target hash list are different then will already throw error
    except FileNotFoundError:
        raise  # SPECIAL CASE if path does not exist, meaning inputted User ID is wrong
    except NotADirectoryError as error:
        logger.error(f"Transfer Failed [{user_folder}]: {error}")
        return
    except PermissionError as error:
        logger.error(
            f"Transfer Failed [{user_folder}]: Permission to access denied! \nMessage: {error}"
        )
        return
    except OSError as error:
        logger.error(f"Transfer Failed [{user_folder}]: OS error! \nMessage: {error}")
        return

    return allowed_file_list, rejected_file_list
