from pathlib import Path

from file_transfer.config import ALLOWED_EXT


def filter_by_policy(file_list: list[Path]) -> tuple[list[Path], list[Path]]:
    allowed_file_list = [
        path for path in file_list if path.suffix.lower() in ALLOWED_EXT
    ]

    rejected_file_list = [
        path for path in file_list if path.suffix.lower() not in ALLOWED_EXT
    ]

    return allowed_file_list, rejected_file_list
