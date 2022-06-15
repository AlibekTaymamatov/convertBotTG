import time
import config

from path import path

seven_days_ago = time.time() - 7 * 86400
base = path(config)

for some_file in base.walkfiles():
    if some_file.mtime < seven_days_ago:
        some_file.remove()
