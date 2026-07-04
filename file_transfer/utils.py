"""
Small shared helpers used across the app.
"""

import sys
import pathlib


def dd(input: any):
    print(input)
    sys.exit()


# def validate_path(path: pathlib.Path) -> bool:
#     return path.exists() and path.is_dir()  # need exist: TRUE ---> valid path
#     # and is_dir: TRUE ---> is a directory path (not to a file)
