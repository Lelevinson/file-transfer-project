"""
Transfer service.

Combines the reader, the policy checks and the server delivery into one
action: send all valid files in a category folder to the backend server.
This is what the watcher calls for each folder.
"""

import os
import pathlib
import logging

import requests

from file_transfer.core.source_reader import Reader
from file_transfer.core.file_sender import Sender
from file_transfer.core.policy_filter import filter_by_policy

# ========= app own logger object ========= #
logger = logging.getLogger(__name__)


def _is_file_ready(file: pathlib.Path) -> bool:
    """
    Check if a file is finished being written.

    The trick: rename the file to its own name. That changes nothing,
    but Windows refuses to rename a file another program still has open.
    So rename works -> file is done. Rename fails -> still being copied.
    """
    try:
        os.rename(file, file)
        return True
    except OSError:
        return False


# ========= folder transfer logic ========= #
def process_folder(
    source_root: pathlib.Path, user_id: str, category: str
) -> tuple[list[pathlib.Path], list[pathlib.Path]] | None:
    """
    Send one user/category folder from source to the backend server.

    Steps:
    1. list the files in source/<user_id>/<category>
    2. skip files that are still being copied (their own event handles them)
    3. validate the rest (filename, extension, size, content)
    4. upload the allowed files to the server, which verifies each hash

    Return (allowed, rejected) file lists, or None if a step failed.
    """
    source_location = pathlib.Path(source_root) / user_id / category

    user_folder = f"{user_id}/{category}"

    logger.info(f"Start transfer folder: {user_folder}")

    ### to GET the list of files in each user's subfolder categories
    try:
        path = Reader(str(source_location))
        file_list = path.get_file()

        # only touch files that are finished; a mid-copy neighbour stays in
        # source and is transferred later by its own watchdog event
        ready_file_list = [file for file in file_list if _is_file_ready(file)]
        if len(ready_file_list) < len(file_list):
            logger.info(
                f"Skipped {len(file_list) - len(ready_file_list)} file(s) in {user_folder} that are still being written"
            )

        allowed_file_list, rejected_file_list = filter_by_policy(ready_file_list)
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

    ### to SEND the files in the list to the backend server
    try:
        Sender.send_file_list(allowed_file_list, user_id, category)
        logger.info(
            f"Transfer Succeed! Sent {len(allowed_file_list)} allowed file(s) to the server for {user_folder}\nFiles: {[*allowed_file_list]}"
        )  # the server verifies each file's hash before answering success
    except FileNotFoundError:
        raise  # SPECIAL CASE the server does not know this User ID
    except requests.ConnectionError as error:
        logger.error(
            f"Transfer Failed [{user_folder}]: backend server not reachable! \nMessage: {error}"
        )
        return
    except OSError as error:
        # covers server refusals and requests' other errors (timeouts, ...)
        logger.error(f"Transfer Failed [{user_folder}]: {error}")
        return

    return allowed_file_list, rejected_file_list
