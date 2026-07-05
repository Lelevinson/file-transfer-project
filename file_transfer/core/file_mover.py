"""
Low-level file operations.

The mechanical work of moving files into a target folder and verifying the
move with SHA-256 hashes. Knows nothing about categories or customers --
it just moves the files it is handed.
"""

import shutil
import pathlib
import hashlib
from file_transfer.utils import *


class Validator:
    """
    Validate the target path and hash files.

    Use for:
    - checking the target path exists and is a directory
    - hashing files with SHA-256
    - comparing source vs target hashes after a move
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

    @staticmethod
    def validate_hash(source_hash: dict[str, str], target_hash: dict[str, str]) -> None:
        """
        Raise an error if the source and target hashes do not match.
        """
        if source_hash != target_hash:
            raise OSError("Hash checking failed after transfer")

    @staticmethod
    def hash_file(file_path: pathlib.Path) -> str:
        """
        Return the SHA-256 hash of one file's contents.
        """
        with file_path.open("rb") as file:
            return hashlib.file_digest(file, "sha256").hexdigest()

    @staticmethod
    def hash_file_list(path_list: list[pathlib.Path]) -> dict[str, str]:
        """
        Return a {file name: SHA-256 hash} mapping for a list of files.
        """
        return {file.name: Validator.hash_file(file) for file in path_list}


class Transfer:
    """
    Main transfer object.

    Move a list of files into a target directory, then verify the move by
    comparing SHA-256 hashes before and after.
    """

    @staticmethod
    def transfer_file(path_list: list[pathlib.Path], target_location: str) -> None:
        """
        Move files into the target directory and verify the move.

        Hashes the files before moving, moves them, then hashes them again
        at the target and compares -- raising an error if anything differs.
        """
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
