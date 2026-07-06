"""
File validation policy.

Decides which files may be transferred. A file must pass every check:
sane filename, allowed extension, non-empty and under the size limit,
and content (magic bytes) that matches the claimed extension.
Each rejected file is logged together with the reason it failed.
"""

import logging
from pathlib import Path

import filetype

from file_transfer.config import ALLOWED_EXT, MAX_FILE_MB

logger = logging.getLogger(__name__)

# Names Windows reserves for devices: a file called CON or CON.txt cannot be
# handled normally, and filenames become folder paths in this app.
_RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"}
_RESERVED_NAMES |= {f"COM{i}" for i in range(1, 10)}
_RESERVED_NAMES |= {f"LPT{i}" for i in range(1, 10)}

# Characters Windows forbids in filenames (control characters are checked
# separately by code point).
_ILLEGAL_CHARS = set('<>:"/\\|?*')

_MAX_NAME_LENGTH = 150

# What filetype may legitimately report for each allowed extension.
# .docx/.xlsx are ZIP containers, and legacy Office formats share one OLE2
# container signature, so several answers are acceptable. An empty set means
# the format has no signature at all (plain text): any positive detection is
# therefore a mismatch. Extensions missing from this map skip the check.
_MAGIC_COMPATIBLE = {
    ".pdf": {"pdf"},
    ".docx": {"docx", "zip"},
    ".xlsx": {"xlsx", "zip"},
    ".xls": {"xls", "doc", "ppt", "msi"},
    ".txt": set(),
}


def filter_by_policy(file_list: list[Path]) -> tuple[list[Path], list[Path]]:
    allowed_file_list = []
    rejected_file_list = []

    for path in file_list:
        reason = _rejection_reason(path)
        if reason is None:
            allowed_file_list.append(path)
        else:
            logger.warning(f"Rejected '{path.name}': {reason}")
            rejected_file_list.append(path)

    return allowed_file_list, rejected_file_list


def _rejection_reason(path: Path) -> str | None:
    """
    Return why this file must be rejected, or None if it passes every check.

    Checks are ordered cheapest first, and the name check must come before
    anything that touches the disk: a reserved name like CON.txt can make
    even stat() misbehave on Windows.
    """
    reason = _check_name(path.name)
    if reason:
        return reason

    if path.suffix.lower() not in ALLOWED_EXT:
        return f"extension '{path.suffix}' is not allowed"

    try:
        reason = _check_size(path)
        if reason:
            return reason
        return _check_content(path)
    except OSError as error:
        return f"file could not be read ({error})"


def _check_name(name: str) -> str | None:
    if len(name) > _MAX_NAME_LENGTH:
        return f"filename is too long ({len(name)} characters, max {_MAX_NAME_LENGTH})"
    if ".." in name:
        return "filename contains '..'"
    if any(char in _ILLEGAL_CHARS or ord(char) < 32 for char in name):
        return "filename contains characters not allowed on Windows"
    if name != name.rstrip(". "):
        return "filename ends with a dot or space"
    # Windows reserves CON and also CON.txt, so only the part before the
    # first dot decides.
    if name.split(".")[0].upper() in _RESERVED_NAMES:
        return "filename is a reserved Windows device name"
    return None


def _check_size(path: Path) -> str | None:
    size = path.stat().st_size
    if size == 0:
        return "file is empty"
    if size > MAX_FILE_MB * 1024 * 1024:
        return f"file is larger than {MAX_FILE_MB} MB"
    return None


def _check_content(path: Path) -> str | None:
    compatible = _MAGIC_COMPATIBLE.get(path.suffix.lower())
    if compatible is None:
        return None

    kind = filetype.guess(str(path))
    if kind is None:
        # No recognizable signature. Plain text and other unsigned formats
        # land here, so trust the already-checked extension instead of
        # wrongly rejecting legitimate files.
        return None

    if kind.extension not in compatible:
        return f"content looks like '{kind.extension}', which does not match '{path.suffix}'"
    return None
