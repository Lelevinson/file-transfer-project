import pathlib
from file_transfer.utils import *


class Testing: ...


class Validator:
    """
    Receive: String of source directory
    Use For: Validate if path exist and is indeed a directory path
    Return: None, just error checking
    """

    @staticmethod
    def validate_path(path: pathlib.Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"path '{path}' does not exist")
        if not path.is_dir():
            raise NotADirectoryError(f"path '{path}' is not a directory")


class ListFile:
    """
    Receive: String of source directory
    Use For: List the file(s) inside that directory
    Return: List of pathlib.Path objects
    """

    @staticmethod
    def list_file(path: pathlib.Path) -> list[pathlib.Path]:
        return [file for file in path.iterdir() if file.is_file()]


class Reader:
    """
    Main Reader object
    Receive: String of source directory
    Utilities (currently): get list of file names
    Return: List of pathlib.Path objects
    """

    def __init__(self, path: str):
        self._path = pathlib.Path(path)

    # will raise errors to main if any
    # will return a list, if errors then will also raise to main
    def get_file(self) -> list[pathlib.Path]:
        Validator.validate_path(self._path)
        return ListFile.list_file(self._path)
