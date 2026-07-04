"""
File uploader for the tray "Upload File" action.

Small unit used by the tray app. It does NOT move files to the final target.
It only copies the chosen file into source/<category>. After that, watchdog
notices the new file and the normal transfer logic takes over.
"""

import pathlib
import shutil


class FileUploader:
    """
    Handle file-copy logic for tray upload.

    This class does NOT move files to the final target folder.
    It only copies selected file into source/category.
    Then watchdog + existing transfer logic continues from there.
    """

    def __init__(self, source_root: str):
        self._source = pathlib.Path(source_root)

    def copy_file_to_category(
        self, selected_file: pathlib.Path, category_name: str
    ) -> pathlib.Path:
        """
        Copy selected file into source/category folder.

        Return:
        - final copied file path
        """
        category_folder = self._source / category_name
        category_folder.mkdir(parents=True, exist_ok=True)

        target_file = category_folder / selected_file.name
        target_file = self._get_available_path(target_file)

        # Use copy2 instead of move.
        # User's original file should stay where they selected it from.
        shutil.copy2(selected_file, target_file)

        return target_file

    def _get_available_path(self, file_path: pathlib.Path) -> pathlib.Path:
        """
        If file path already exists, create a new name.

        Example:
        - report.pdf
        - report_1.pdf
        - report_2.pdf
        """
        if not file_path.exists():
            return file_path

        counter = 1

        while True:
            new_path = file_path.with_name(
                f"{file_path.stem}_{counter}{file_path.suffix}"
            )

            if not new_path.exists():
                return new_path

            counter += 1
