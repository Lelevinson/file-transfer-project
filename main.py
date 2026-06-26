import pathlib
from config import SOURCE_LOCATION, TARGET_LOCATION
from reader import Reader
from transfer import Transfer

path = Reader(SOURCE_LOCATION)

print(Transfer.transfer(path.getFile(), TARGET_LOCATION))
