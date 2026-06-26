import pathlib
import typing


class Testing_Service: ...


class Validate_Service:
    """
    Receive: Directory path string
    Validate if path exist and is indeed a directory path
    Return: Boolean
    """

    @staticmethod
    def validate(path: pathlib.Path) -> bool:
        return path.exists() and path.is_dir()  # need exist: TRUE ---> valid path
        # and is_dir: TRUE ---> is a directory path (not to a file)


class List_File_Service:
    """
    Receive: Directory path string
    List the file(s) inside that directory
    Return: List of strings
    """

    @staticmethod
    def list(path: pathlib.Path) -> list:
        return list(
            path.iterdir()
        )  # originally, the function return an iterator, which in Python disappear after looping
        # since we need the list of strings, we convert it to list


class Reader:
    """
    Main Reader object
    Utils (currently): get list of file names
    """

    def __init__(self, path: str):
        self._path = pathlib.Path(path)

    def getFile(self) -> list:
        if Validate_Service.validate(self._path):
            return List_File_Service.list(self._path)
        else:
            return []
