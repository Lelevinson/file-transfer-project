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
from tkinter import filedialog, font as tkfont, messagebox, ttk

from file_transfer.config import USER_IDS

logger = logging.getLogger(__name__)

# ========= UI size knob ========= #
# The app is DPI-aware (crisp text), but that makes the UI physically small on
# high-DPI screens. This multiplies every font size. Raise it to make the whole
# UI bigger (dialog, dropdown, buttons, error box, toast); lower it for smaller.
UI_SCALE = 1.5


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

        # The app is DPI-aware (crisp) but that makes Tk's UI small on high-DPI
        # screens. Enlarge every built-in font so dialogs, the dropdown, buttons
        # and message boxes are comfortably sized. (Toast fonts scale too, below.)
        self._enlarge_default_fonts(UI_SCALE)

        # Ask Tkinter to check queued GUI tasks every 100ms.
        self._root.after(100, self._process_gui_tasks)

    def _enlarge_default_fonts(self, factor: float) -> None:
        """
        Scale Tk's built-in named fonts by `factor`.

        Every standard widget (labels, buttons, combobox, message boxes) uses
        one of these named fonts, so scaling them here resizes the whole UI in
        one place -- no need to set a font on each widget.
        """
        font_names = (
            "TkDefaultFont",
            "TkTextFont",
            "TkMenuFont",
            "TkHeadingFont",
            "TkCaptionFont",
            "TkSmallCaptionFont",
            "TkTooltipFont",
            "TkIconFont",
            "TkFixedFont",
        )
        for name in font_names:
            try:
                font = tkfont.nametofont(name)
                font.configure(size=int(font.cget("size") * factor))
            except tk.TclError:
                # some named fonts may not exist on every platform -- skip them
                continue

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

    def input_user(self) -> str | None:
        """
        Ask for a User ID with a small custom dialog containing an editable dropdown.

        The user can TYPE an ID or PICK one from the known list (USER_IDS).
        Returns the ID string, or None if cancelled or left blank.

        This is a *custom* dialog (our own Toplevel window) rather than the
        prebuilt simpledialog, because we need a dropdown inside it.
        """
        # 1) our own little window (instead of the prebuilt askstring dialog)
        dialog = tk.Toplevel(self._root)
        dialog.title("User ID")
        dialog.attributes("-topmost", True)
        dialog.resizable(False, False)
        dialog.grab_set()  # modal: block the rest of the app until answered

        tk.Label(dialog, text="Select or type the User's ID:").pack(
            padx=12, pady=(12, 4)
        )

        # 2) editable combobox: the list suggests known users, typing still allowed
        combo = ttk.Combobox(dialog, values=USER_IDS)
        combo.pack(padx=12, pady=4)
        combo.focus_set()

        # 3) a place to keep the result across the button callbacks; None = cancelled
        result = {"user_id": None}

        def on_ok():
            result["user_id"] = combo.get()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        buttons = tk.Frame(dialog)
        buttons.pack(pady=(4, 12))
        tk.Button(buttons, text="OK", width=8, command=on_ok).pack(side="left", padx=4)
        tk.Button(buttons, text="Cancel", width=8, command=on_cancel).pack(
            side="left", padx=4
        )

        # center the dialog on screen (the old askstring did this for us)
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        # 4) wait here until the dialog is closed -- this is what makes it modal
        self._root.wait_window(dialog)

        user_id = result["user_id"]
        if user_id is None or user_id.strip() == "":
            return None
        return user_id.strip()

    def show_message(self, title: str, message: str, is_error: bool = False) -> None:
        """
        Show a modal popup box (must be clicked to dismiss).

        Runs on Tkinter's loop, so call it via schedule_task from other threads.
        This is the "implementation" that TrayApp.display_error schedules.
        """
        if is_error:
            messagebox.showerror(title, message, parent=self._root)
        else:
            messagebox.showinfo(title, message, parent=self._root)

    def show_toast(self, title: str, message: str, duration_ms: int = 4000) -> None:
        """
        Show our own small notification window (bottom-right), auto-dismissing.

        We draw this ourselves instead of using pystray's tray balloon because
        that balloon is silently dropped by Windows (Focus Assist / notification
        settings / frozen-app quirks). This window is pure Tkinter -- we own the
        GUI loop, so it always shows.

        Runs on Tkinter's loop, so call it via schedule_task from other threads.
        """
        logger.info(f"Showing toast: {title} - {message}")

        # Scale the toast's own fonts with the same UI knob as the rest of the UI.
        title_size = int(10 * UI_SCALE)
        body_size = int(9 * UI_SCALE)

        toast = tk.Toplevel(self._root)
        toast.overrideredirect(True)  # no title bar / borders -- looks like a toast
        toast.attributes("-topmost", True)

        frame = tk.Frame(toast, bg="#2b2b2b", padx=16, pady=12)
        frame.pack(fill="both", expand=True)
        tk.Label(
            frame,
            text=title,
            bg="#2b2b2b",
            fg="#ffffff",
            font=("Segoe UI", title_size, "bold"),
            anchor="w",
            justify="left",
        ).pack(anchor="w")
        tk.Label(
            frame,
            text=message,
            bg="#2b2b2b",
            fg="#dddddd",
            font=("Segoe UI", body_size),
            anchor="w",
            justify="left",
            wraplength=int(300 * UI_SCALE),
        ).pack(anchor="w", pady=(4, 0))

        # Position at the fixed bottom-right corner, above the taskbar.
        toast.update_idletasks()
        sw = toast.winfo_screenwidth()
        sh = toast.winfo_screenheight()

        # The very FIRST toast can mis-report its size before it is fully
        # realized (worse with DPI awareness) -- a bogus (huge) size is what
        # shoved it into the top-left corner. If the measurement looks
        # implausible, fall back to sensible defaults so it always lands
        # bottom-right.
        width = toast.winfo_reqwidth()
        if width <= 1 or width > sw:
            width = int(360 * UI_SCALE)
        height = toast.winfo_reqheight()
        if height <= 1 or height > sh:
            height = int(90 * UI_SCALE)

        margin = 20
        taskbar = 48
        x = sw - width - margin
        y = sh - height - margin - taskbar
        toast.geometry(f"+{x}+{y}")
        toast.lift()  # force it above other windows (topmost alone can be flaky)

        # Auto-close after a few seconds.
        toast.after(duration_ms, toast.destroy)

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
