"""
Server-side delivery.

Sends validated files to the backend over HTTP instead of copying them into
a local target folder. The server checks the user is registered, verifies
the SHA-256 hash of what actually arrived and records the file -- so a
success answer means "arrived intact", and only then is the local copy
removed to complete the move.
"""

import logging
import pathlib

import requests

from file_transfer.config import SERVER_URL
from file_transfer.core.file_mover import Validator

logger = logging.getLogger(__name__)


class Sender:
    """
    Main sender object.

    Upload a list of files to the backend, one request per file, deleting
    each local copy once the server confirms it arrived intact.
    """

    @staticmethod
    def send_file(file: pathlib.Path, user_id: str, category: str) -> None:
        """
        Upload one file together with its metadata and hash.

        Raise:
        - FileNotFoundError if the server does not know this user
          (same meaning as the old missing target folder, so the watcher's
          special case keeps working unchanged)
        - OSError for any other refusal, carrying the server's reason
        """
        file_hash = Validator.hash_file(file)

        with file.open("rb") as handle:
            response = requests.post(
                f"{SERVER_URL}/upload",
                files={"file": (file.name, handle)},
                data={"user_id": user_id, "category": category, "hash": file_hash},
                timeout=30,
            )

        if response.status_code == 404:
            raise FileNotFoundError(
                f"user '{user_id}' is not registered on the server"
            )

        if response.status_code != 201:
            raise OSError(
                f"server refused '{file.name}': {response.status_code} {response.text}"
            )

    @staticmethod
    def send_file_list(
        file_list: list[pathlib.Path], user_id: str, category: str
    ) -> None:
        """
        Upload files one by one, deleting each local copy after the server
        confirms it. A failure part-way leaves the remaining files in the
        source folder, where the next watchdog event retries them.
        """
        for file in file_list:
            Sender.send_file(file, user_id, category)
            file.unlink()
