import pathlib
import time
import logging

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from file_transfer.core.transfer_service import transfer_folder

logger = logging.getLogger(__name__)


class Validator:
    """
    Receive: [FileSystemEventHandler event object],
             [pathlib.Path objects]
    Use For: [Validate if it is a newly created file and not folder],
             [Validate if the file is done transferring to the source folder]
    Return: [None],
            [None]
    """

    @staticmethod
    def validate_path(source_path: FileSystemEventHandler) -> None:
        if source_path.is_directory:
            raise IsADirectoryError(f"You just created a folder, not a file!")

    @staticmethod
    def validate_file(source_file: pathlib.Path) -> None:
        timer = 0

        while timer <= 60:
            file_size_before = source_file.stat().st_size
            time.sleep(3)
            file_size_after = source_file.stat().st_size
            logger.info(f"before: {file_size_before}, after: {file_size_after}")
            if file_size_before == file_size_after:
                return
            timer += 1

        if timer > 60:
            raise TimeoutError("Your file upload is too slow!")


class AppHandler(FileSystemEventHandler):
    def __init__(self, source_root: str, target_root: str):
        # save all the available sub-folders in the source folder
        self._source = pathlib.Path(source_root)
        self._target = pathlib.Path(target_root)
        self._path_sub_folder = [
            folder for folder in self._source.iterdir() if folder.is_dir()
        ]

    def initial_transfer(self) -> None:
        """
        use for initial transfer (when program start at the very first time)
        """
        for folder in self._path_sub_folder:
            transfer_folder(folder.name, self._source, self._target)

    def on_created(self, event) -> None:
        """
        on-created event handler that will be triggered everytime there is/are new file(s) in sub-folder(s)
        """
        # check if the newly created is a file and not a folder
        # there is also similar method in reader, but this one is to make sure that the validate_file method safe (since we'll use st_size)
        try:
            Validator.validate_path(event)
        except IsADirectoryError as error:
            logger.error(f"Watcher Failed: {error}")
            return

        # get full path of the created file that triggered this event
        source_file = pathlib.Path(event.src_path)

        # check for file readiness
        try:
            Validator.validate_file(source_file)
        except TimeoutError as error:
            logger.error(f"Watcher Failed: {error}")
            return

        # get the folder name of the current path that triggered on_created
        folder_name = source_file.parent.name
        transfer_folder(folder_name, self._source, self._target)


observer = Observer()
