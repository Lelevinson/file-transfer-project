import shutil
import pathlib
import hashlib
from file_transfer.utils import *


class Validator:
    """
    Receive: [String of target directory],
             [List of pathlib.Path objects]
    Use For: [Validate if path exist and is indeed a directory path],
             [Hash the file's path]
    Return: [None],
            [List of hashed string of the file's path]
    """

    @staticmethod
    def validate_path(path: pathlib.Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"path '{path}' does not exist")
        if not path.is_dir():
            raise NotADirectoryError(f"path '{path}' is not a directory")

    @staticmethod
    def validate_hash(source_hash: dict[str, str], target_hash: dict[str, str]) -> None:
        if source_hash != target_hash:
            raise OSError("Hash checking failed after transfer")

    @staticmethod
    def hash_file(file_path: pathlib.Path) -> str:
        with file_path.open("rb") as file:
            return hashlib.file_digest(file, "sha256").hexdigest()

    @staticmethod
    def hash_file_list(path_list: list[pathlib.Path]) -> dict[str, str]:
        return {file.name: Validator.hash_file(file) for file in path_list}


class Transfer:
    """
    Main Transfer Object
    Receive: List of Pathlib.Path object and String of target directory
    Utilities (currently): transfer list of file names to a target directory path
    Return: None
    """

    @staticmethod
    def transfer_file(path_list: list[pathlib.Path], target_location: str) -> None:
        target_path = pathlib.Path(target_location)
        Validator.validate_path(target_path)  # will raise errors to main if any

        # hashing source directory files
        source_hash = Validator.hash_file_list(path_list)

        # move files from source to target
        for file in path_list:
            shutil.move(file, target_path)

        # hashing target directory files
        new_path_list = [target_path / file.name for file in path_list]
        target_hash = Validator.hash_file_list(new_path_list)

        # raise error if num of hashed source file list != num of hashed target file list
        Validator.validate_hash(source_hash, target_hash)
