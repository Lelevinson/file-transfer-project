"""
Folder watching.

Watches the source folder with watchdog and reacts to newly created files.
Also provides start_watching() / stop_watching() so the entry point can
control the observer without touching its internals.
"""

import pathlib
import time
import logging
from shutil import rmtree, move
from collections.abc import Callable

from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver
from watchdog.events import FileSystemEventHandler

from file_transfer.core.transfer_service import process_folder

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
        1. Check if the file still exist or not

        Since folders creation make watchdog event assigment unpredictable,
        it might be removed already in previous events.

        2. Wait until the file has finished being written.

        Checks the file size every few seconds; when it stops changing the
        file is ready. Raises TimeoutError if it never settles.
        """
        if not source_file.exists():
            raise FileNotFoundError("Your file has been cleaned!")

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
    def __init__(
        self,
        source_root: str,
        target_root: str,
        fail_root: str,
        category: list[str],
        display_notification: Callable[[str, str, str], None],
        display_error: Callable[[str, str], None],
    ):
        # save all the available users folders
        self._category = category
        self._source = pathlib.Path(source_root)
        self._target = pathlib.Path(target_root)
        self._fail = pathlib.Path(fail_root)
        self._users = [user for user in self._source.iterdir() if user.is_dir()]
        self._display_notification = display_notification
        self._display_error = display_error

    def dispatch(self, event) -> None:
        """
        Catch-all wrapper around every event callback (on_created, ...).

        watchdog runs this on the observer's background thread, and any uncaught
        exception here would kill that thread SILENTLY -- the app keeps running
        but quietly stops transferring anything. Logging and swallowing keeps the
        watcher alive no matter what a single event hits.
        """
        try:
            super().dispatch(event)
        except Exception:
            logger.exception("Watcher event handler crashed but was kept alive")

    # def initial_transfer(self) -> None:
    #     """
    #     Transfer files that already exist, once, when the app first starts.
    #     """
    #     for user_id in self._users:
    #         for cat in self._category:
    #             process_folder(
    #                 self._source,
    #                 self._target,
    #                 user_id.name,
    #                 cat,
    #             )

    def on_created(self, event) -> None:
        """
        Handle a watchdog "file created" event: validate it, wait for the
        file to be ready, then transfer its folder to the target.
        """
        # events assigned by watchdog to a complex folders are inconsitent
        # if we create say user_id/category/file, we will have 6 total events (NOT 1)
        # but only 2 possible cases:
        # - if it is folders (user_id/ and user_id/category)
        # - and if it is a file (user_id/category/file)
        # we must handle these

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
        except FileNotFoundError as error:
            logger.error(f"Watcher Failed: {error}")
            return
        except TimeoutError as error:
            logger.error(f"Watcher Failed: {error}")
            return

        # get the 'category' and 'user id' parts of the path that triggered on_created
        try:
            category = source_file.parent.name
            user_id = source_file.parent.parent.name
            result = process_folder(
                self._source,
                self._target,
                user_id,
                category,
            )
        except FileNotFoundError as error:
            # non-registered user: remove the whole bogus user folder from source,
            # not just the category (otherwise the empty user folder lingers)
            wrong_user_folder = self._source / user_id
            rmtree(wrong_user_folder)
            self._display_error(
                "Transfer Failed",
                "You uploaded a file for a non-registered User ID.",
            )
            logger.error(
                f"User ID in target_folder not found! Cleaning up file in the source_folder"
            )
            return

        # a reader/transfer failure inside process_folder returns None (already logged).
        # Tell the user instead of failing silently.
        if result is None:
            self._display_error(
                "Transfer Failed",
                f"Could not transfer the file(s) for {user_id}/{category}. "
                f"Please check the log (Open Log in the tray menu) for details.",
            )
            return

        transferred_file_list, rejected_file_list = result

        # toast when files actually landed in the target
        if transferred_file_list:
            self._display_notification(
                f"{len(transferred_file_list)} file(s) transferred to {user_id}/{category}",
                "Transfer Complete",
            )

        # move policy-rejected files out to the fail folder
        # (fail folder is OUTSIDE source, so moving here does NOT re-trigger watchdog)
        if rejected_file_list:
            fail_location = self._fail / user_id / category
            fail_location.mkdir(parents=True, exist_ok=True)

            for file in rejected_file_list:
                # shutil.move errors if the destination already exists, so find a
                # free name first (report.jpg -> report_1.jpg -> report_2.jpg ...)
                destination = fail_location / file.name
                counter = 1
                while destination.exists():
                    destination = fail_location / f"{file.stem}_{counter}{file.suffix}"
                    counter += 1
                move(str(file), str(destination))

            logger.info(
                f"Moved {len(rejected_file_list)} rejected file(s) to fail folder: {user_id}/{category}"
            )
            self._display_error(
                "File(s) Rejected",
                f"{len(rejected_file_list)} file(s) failed validation and were not transferred. "
                f"Check the log (Open Log in the tray menu) for the reason, and {fail_location} to see the file(s)",
            )


def start_watching(
    source_root: str,
    target_root: str,
    fail_root: str,
    category: list[str],
    display_notification: Callable[[str, str, str], None],
    display_error: Callable[[str, str], None],
) -> BaseObserver:
    """
    Start watching the source folder for new files.

    Does the full startup sequence so the entry point does not have to:
    - build the event handler
    - watch source root and all its subfolders (recursive=True)
    - transfer files that already exist, once
    - start the observer thread

    Return: the running Observer, so the caller can stop it later.
    """
    handler = AppHandler(
        source_root, target_root, fail_root, category, display_notification, display_error
    )

    observer = Observer()
    observer.schedule(handler, path=source_root, recursive=True)

    # Transfer existing files once when app starts.
    # handler.initial_transfer()

    observer.start()
    return observer


def stop_watching(observer: BaseObserver) -> None:
    """
    Stop the observer if it is running, then wait for its thread to finish.
    """
    if observer.is_alive():
        observer.stop()
    observer.join()
