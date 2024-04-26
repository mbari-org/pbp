import copy
import sys
import loguru
import os
import pathlib

from typing import Optional, Tuple


def create_logger(
    log_filename_and_level: Optional[Tuple[str, str]] = None,
    console_level: Optional[str] = None,
):  # -> loguru.Logger:  # poetry complains about not recognizing this type :(
    """
    Create logger instance, typically to be used for a day of processing.

    NOTE: The created object should be passed around to all relevant functions.
    Do not use `from loguru import logger` (or similar) to obtain the logger.

    :param log_filename_and_level:
        (filename, level) tuple or None to disable file logging.
    :param console_level:
        The log level for the console, or None to disable console logging.
    """

    fmt = "{time} {level} {message}"
    loguru.logger.remove()
    log = copy.deepcopy(loguru.logger)
    if log_filename_and_level is not None:
        log_filename, log_level = log_filename_and_level
        # create log_filename's parent directory if needed:
        parent_dir = pathlib.Path(log_filename).parent
        pathlib.Path(parent_dir).mkdir(parents=True, exist_ok=True)
        file_fmt = fmt
        if os.getenv("EXCLUDE_LOG_TIME", "no") == "yes":
            # test convenience to facilitate local diffing of log files
            file_fmt = "{level} {message}"
        log.add(
            sink=open(log_filename, "w"), level=log_level, format=file_fmt, enqueue=True
        )

    if console_level is not None:
        log.add(
            sink=sys.stderr, level=console_level, format=fmt, colorize=True, enqueue=True
        )

    return log
