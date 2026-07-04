"""
Folder watching.

Watches the source folder with watchdog and reacts to newly created files.
Also provides start_watching() / stop_watching() so the entry point can
control the observer without touching its internals.
"""

import pathlib
import time
import logging

from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver
from watchdog.events import FileSystemEventHandler

from file_transfer.core.transfer_service import transfer_folder

logger = logging.getLogger(__name__)


class Validator:
    """
    Validate watchdog events and file readiness.

    Use for:
    - checking a new event is a file, not a folder
    - checking a file has finished being written before transfer
    """

    @staticmethod
    def validate_path(source_path: FileSystemEventHandler) -> None:
        """
        Raise an error if the event is a folder instead of a file.
        """
        if source_path.is_directory:
            raise IsADirectoryError(f"You just created a folder, not a file!")

    @staticmethod
    def validate_file(source_file: pathlib.Path) -> None:
        """
        Wait until the file has finished being written.

        Checks the file size every few seconds; when it stops changing the
        file is ready. Raises TimeoutError if it never settles.
        """
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
        Transfer files that already exist, once, when the app first starts.
        """
        for folder in self._path_sub_folder:
            transfer_folder(folder.name, self._source, self._target)

    def on_created(self, event) -> None:
        """
        Handle a watchdog "file created" event: validate it, wait for the
        file to be ready, then transfer its folder to the target.
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


def start_watching(source_root: str, target_root: str) -> BaseObserver:
    """
    Start watching the source folder for new files.

    Does the full startup sequence so the entry point does not have to:
    - build the event handler
    - watch source root and all its subfolders (recursive=True)
    - transfer files that already exist, once
    - start the observer thread

    Return: the running Observer, so the caller can stop it later.
    """
    handler = AppHandler(source_root, target_root)

    observer = Observer()
    observer.schedule(handler, path=source_root, recursive=True)

    # Transfer existing files once when app starts.
    handler.initial_transfer()

    observer.start()
    return observer


def stop_watching(observer: BaseObserver) -> None:
    """
    Stop the observer if it is running, then wait for its thread to finish.
    """
    if observer.is_alive():
        observer.stop()
    observer.join()
