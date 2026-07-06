"""
Source-side reading.

Validates a source folder and lists the files inside it, so the transfer
service knows what needs to be moved.
"""

import pathlib
from file_transfer.utils import *


class Validator:
    """
    Validate a source path.

    Use for:
    - checking the path exists
    - checking the path is a directory, not a file
    """

    @staticmethod
    def validate_path(path: pathlib.Path) -> None:
        """
        Raise an error if the path does not exist or is not a directory.
        """
        if not path.exists():
            raise FileNotFoundError(f"path '{path}' does not exist")
        if not path.is_dir():
            raise NotADirectoryError(f"path '{path}' is not a directory")


class ListFile:
    """
    List files in a source directory.

    Returns only files, not subfolders.
    """

    @staticmethod
    def list_file(path: pathlib.Path) -> list[pathlib.Path]:
        """
        Return the files directly inside the directory (subfolders excluded).
        """
        return [file for file in path.iterdir() if file.is_file()]


class Reader:
    """
    Main reader object for a source directory.

    Use for:
    - validating the source path
    - getting the list of files inside it
    """

    def __init__(self, path: str):
        self._path = pathlib.Path(path)

    def get_file(self) -> list[pathlib.Path]:
        """
        Validate the source path, then return the files inside it.

        Any validation error is raised up to the caller.
        """
        Validator.validate_path(self._path)
        return ListFile.list_file(self._path)
