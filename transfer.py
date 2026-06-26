import shutil
import pathlib


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


class Transfer:
    """
    Main Transfer Object
    Utils (currently): transfer list of file names to a target directory path
    """

    @staticmethod
    def transfer(pathList: list, targetLocation: str) -> bool:
        if Validate_Service.validate(pathlib.Path(targetLocation)):
            for path in pathList:
                shutil.move(path, targetLocation)
            return True
        else:
            return False
