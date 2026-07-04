import logging
import time
import pathlib

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from file_transfer.config import SOURCE_ROOT

test = pathlib.Path(SOURCE_ROOT)

for x in test.iterdir():
    print(x)
