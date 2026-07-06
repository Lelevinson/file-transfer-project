"""
System tray app -- the "surface" of the UI layer.

This file does NOT do the real transfer itself. It is mostly *wiring*:
- build the tray menu
- connect menu clicks to actions
- start pystray + Tkinter

It combines three small units:
- GuiHelper       -> Tkinter windows, dialogs, popups        (gui_helper.py)
- FileUploader    -> copy a chosen file into source/category (file_uploader.py)
- TrayIconBuilder -> draw the little tray icon                (tray_icon.py)

Flow when the user uploads a file:
    user clicks a category
        -> GuiHelper asks which file
        -> FileUploader copies it into source/<category>
        -> watchdog notices the new file and runs the transfer logic.
The tray never calls the transfer logic directly.
"""

# python/pip packages
import logging
import os
import pathlib

import pystray

# own modules (the small units this surface combines)
from file_transfer.config import LOG_FILE
from file_transfer.ui.gui_helper import GuiHelper
from file_transfer.ui.file_uploader import FileUploader
from file_transfer.ui.tray_icon import TrayIconBuilder

# ========= tray app logger ========= #
logger = logging.getLogger(__name__)


class TrayApp:
    """
    Connect pystray menu actions to our app actions.

    This class is mostly "wiring":
    - build tray menu
    - connect menu item clicks to methods
    - start pystray + Tkinter
    """

    def __init__(self, source_root: str, category: list[str], on_exit=None):
        """
        Receive:
        - source_root: root source folder path
        - category: list of available category/folder names
        - on_exit: optional function to run before closing app
        """
        self._category = category
        self._on_exit = on_exit

        self._gui = GuiHelper()
        self._uploader = FileUploader(source_root)
        self._icon = pystray.Icon(
            "File Transfer",
            TrayIconBuilder.create(),
            "File Transfer",
            menu=self._create_menu(),
        )

    # ========= start tray app ========= #
    def run(self) -> None:
        """
        Start the tray app.

        Important:
        - pystray has its own event loop.
        - Tkinter also has its own event loop.

        To avoid frozen popups, pystray is started with run_detached(),
        then Tkinter owns the main GUI loop.
        """
        self._icon.run_detached()
        self._gui.run()

    # ========= top-level tray menu ========= #
    def _create_menu(self) -> pystray.Menu:
        """
        Create top-level tray menu.

        pystray.MenuItem receives:
        - text: what user sees
        - action: function to call OR submenu object
        """
        return pystray.Menu(
            # Second argument is a submenu here.
            pystray.MenuItem("Upload File", self._create_upload_menu()),
            # Second argument is a function/callback here.
            pystray.MenuItem("Open Log", self.open_log),
            pystray.MenuItem("Exit", self.exit_app),
        )

    # ========= upload submenu ========= #
    def _create_upload_menu(self) -> pystray.Menu:
        """
        Create submenu for Upload File.

        Example:
        Upload File
            體組成
            檢驗紀錄
            ...
        """
        menu_items = []

        for category_name in self._category:
            menu_item = pystray.MenuItem(
                category_name,
                self._create_upload_action(category_name),
            )
            menu_items.append(menu_item)

        # *menu_items means:
        # pass the list items one by one into pystray.Menu(...)
        return pystray.Menu(*menu_items)

    def _create_upload_action(self, category_name: str):
        """
        Create callback function for one category menu item.

        pystray will call the returned function when the user clicks a category.
        """

        def upload_action(icon, item):
            """
            This function shape matches pystray callback style.

            pystray passes:
            - icon: tray icon object
            - item: clicked menu item

            We do not need them here, but we accept them because pystray sends them.
            """

            def run_upload():
                self._upload_to_category(category_name)

            self._gui.schedule_task(run_upload)

        return upload_action

    # ========= action: upload file ========= #
    def _upload_to_category(self, category_name: str) -> None:
        """
        Ask user for one or more files, then copy them into source/category_name.

        After asking for files, input the User ID (once, for the whole batch).

        Watchdog will see the copied files and transfer them to the target folder.
        """
        selected_files = self._gui.select_files()
        if not selected_files:
            return

        user_id = self._gui.input_user()
        if user_id is None:
            return

        user_category_folder = f"{user_id}/{category_name}"

        copied_files = []
        failed_files = []

        # copy one by one so a single bad file does not stop the rest
        for selected_file in selected_files:
            try:
                copied_file = self._uploader.copy_file_to_user_category(
                    selected_file,
                    user_id,
                    category_name,
                )
                logger.info(f"Tray app copied file to source folder: {copied_file}")
                copied_files.append(copied_file)

            except OSError as error:
                logger.error(f"Tray app copy failed for {selected_file.name}: {error}")
                failed_files.append(selected_file)

        if copied_files:
            self.display_notification(
                f"Preparing {len(copied_files)} file(s) for transfer",
                "Copy File",
            )

        if failed_files:
            failed_names = ", ".join(file.name for file in failed_files)
            self._gui.show_message(
                "Copy Failed",
                f"Failed to copy {len(failed_files)} file(s) to {user_category_folder}: "
                f"{failed_names}. Please check the logs.",
                is_error=True,
            )

    # ========= action: open log ========= #
    def open_log(self, icon, item) -> None:
        """
        Menu callback for: Open Log.

        Schedule the real open-log action from Tkinter's GUI loop.
        """
        self._gui.schedule_task(self._open_log)

    def _open_log(self) -> None:
        """
        Real Open Log action.

        This runs from Tkinter's GUI loop.
        """
        log_path = pathlib.Path(LOG_FILE)

        if not log_path.exists():
            self._gui.show_message(
                "Log File", "The log file does not exist yet.", is_error=False
            )
            return

        os.startfile(log_path)

    # ========= action: exit ========= #
    def exit_app(self, icon, item) -> None:
        """
        Menu callback for: Exit.

        Schedule the actual shutdown from Tkinter's GUI loop.
        """
        self.request_exit()

    def request_exit(self) -> None:
        """
        Public method to ask tray app to exit.

        Use for:
        - tray menu Exit
        - Ctrl+C from terminal
        """
        self._gui.schedule_task(self._exit_app)

    def _exit_app(self) -> None:
        """
        Stop watcher, stop tray icon, and stop Tkinter loop.
        """
        logger.info("Tray app exit requested")

        if self._on_exit is not None:
            self._on_exit()

        self._icon.stop()
        self._gui.stop()

    # ========= utils: notification ========= #
    def display_notification(
        self, notif_message: str, notif_title: str, error: str = ""
    ) -> None:
        """
        Display a toast notification (bottom-right on screen).

        We draw our own toast window (GuiHelper.show_toast) instead of pystray's
        tray balloon: Windows silently drops those balloons, so they never
        appeared. Scheduled onto Tkinter's loop via the queue, so it is safe to
        call from the watcher's background thread.
        """
        message = notif_message if error == "" else f"{notif_message} Error: {error}"
        logger.info(f"Notification: {notif_title} - {message}")
        self._gui.schedule_task(
            lambda: self._gui.show_toast(notif_title, message)
        )

    # ========= utils: error popup ========= #
    def display_error(self, title: str, message: str) -> None:
        """
        Display a modal error popup that must be clicked to dismiss.

        Safe to call from the watcher thread: it only schedules the work
        onto Tkinter's loop (the queue). GuiHelper.show_message does the
        actual display, so nothing here touches Tkinter directly.
        """
        logger.info(f"Error popup: {title} - {message}")
        self._gui.schedule_task(
            lambda: self._gui.show_message(title, message, is_error=True)
        )
