import sys

from loguru import logger as log
import os
import pathlib

from typing import Optional, Tuple


def create_logger(
    log_filename_and_level: Optional[Tuple[str, str]] = None,
    console_level: Optional[str] = None,
):
    """
    Create logger.

    :param log_filename_and_level:
        (filename, level) tuple or None to disable file logging.
    :param console_level:
        The log level for the console, or None to disable console logging.
    """

    log.remove()
    fmt = "{time} {level} {message}"
    if log_filename_and_level is not None:
        log_filename, log_level = log_filename_and_level
        # create log_filename's parent directory if needed:
        parent_dir = pathlib.Path(log_filename).parent
        pathlib.Path(parent_dir).mkdir(parents=True, exist_ok=True)
        file_fmt = fmt
        if os.getenv("EXCLUDE_LOG_TIME", "no") == "yes":
            # test convenience to facilitate local diffing of log files
            file_fmt = "{level} {message}"
        log.add(sink=open(log_filename, "w"), level=log_level, format=file_fmt)

    if console_level is not None:
        log.add(sink=sys.stderr, level=console_level, format=fmt, colorize=True)

    return log
