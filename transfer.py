import shutil
import pathlib
import hashlib
from utils import *


class Validator:
    """
    Receive: Directory path string
    Validate if path exist and is indeed a directory path
    Return: None, just error checking
    """

    @staticmethod
    def validate_path(path: pathlib.Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"path '{path}' does not exist")
        if not path.is_dir():
            raise NotADirectoryError(f"path '{path}' is not a directory")

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
    Utils (currently): transfer list of file names to a target directory path
    """

    @staticmethod
    def transfer_file(path_list: list[pathlib.Path], target_location: str) -> None:
        target_path = pathlib.Path(target_location)
        Validator.validate_path(target_path)  # will raise errors to main if any

        source_hash = Validator.hash_file_list(path_list)

        # hashing source directory files
        for file in path_list:
            shutil.move(file, target_path)

        new_path_list = [target_path / file.name for file in path_list]
        target_hash = Validator.hash_file_list(new_path_list)

        if source_hash != target_hash:
            raise OSError(
                "Hash checking failed after transfer"
            )  # raise error if num of hashed source file list != num of hashed target file list


# if __name__ == "__main__":
#     Transfer.transfer_file()
