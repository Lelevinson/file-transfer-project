"""
Tkinter GUI helper.

Small unit used by the tray app. Handles everything Tkinter:
- one hidden root window
- the file picker dialog
- popup message boxes
- a safe queue so pystray can hand GUI work back to Tkinter
"""

import logging
import pathlib
import queue
import tkinter as tk
from tkinter import filedialog, messagebox

logger = logging.getLogger(__name__)


class GuiHelper:
    """
    Handle Tkinter GUI things.

    Use for:
    - hidden Tkinter root window
    - file picker dialog
    - popup message boxes
    - safe queue between pystray and Tkinter
    """

    def __init__(self):
        self._is_exiting = False
        self._task_queue = queue.Queue()

        # Tkinter needs one root window.
        # We hide it because this app mainly lives in the system tray.
        self._root = tk.Tk()
        self._root.withdraw()
        self._root.attributes("-topmost", True)

        # Ask Tkinter to check queued GUI tasks every 100ms.
        self._root.after(100, self._process_gui_tasks)

    def run(self) -> None:
        """
        Start Tkinter GUI loop.

        This keeps the app alive until root.quit() is called.
        """
        self._root.mainloop()

    def stop(self) -> None:
        """
        Stop Tkinter GUI loop.
        """
        self._is_exiting = True
        self._root.quit()

    def schedule_task(self, task) -> None:
        """
        Put a GUI task into queue.

        pystray menu callbacks may run outside Tkinter's own loop.
        So instead of opening dialogs directly there, we queue the work.
        """
        self._task_queue.put(task)

    def select_file(self) -> pathlib.Path | None:
        """
        Open a file picker dialog.

        Return:
        - pathlib.Path if user selected a file
        - None if user cancelled
        """
        selected_file = filedialog.askopenfilename(
            parent=self._root,
            title="Choose file to upload",
        )

        if selected_file == "":
            return None

        return pathlib.Path(selected_file)

    def show_message(self, title: str, message: str, is_error: bool = False) -> None:
        """
        Show small popup message.

        Use:
        - messagebox.showinfo for normal message
        - messagebox.showerror for error message
        """
        if is_error:
            messagebox.showerror(title, message, parent=self._root)
        else:
            messagebox.showinfo(title, message, parent=self._root)

    def _process_gui_tasks(self) -> None:
        """
        Run queued GUI tasks from Tkinter's event loop.

        This method calls itself again every 100ms while app is running.
        """
        while True:
            try:
                task = self._task_queue.get_nowait()
            except queue.Empty:
                break

            try:
                task()
            except Exception as error:
                logger.exception(f"Tray GUI task failed: {error}")

        if not self._is_exiting:
            self._root.after(100, self._process_gui_tasks)
