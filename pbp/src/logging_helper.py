import logging
import os
import random
import string
import pathlib

from typing import Optional, Tuple


class PbpLogger:
    def __init__(
        self,
        name: str,
        log_filename_and_level: Optional[Tuple[str, int]] = None,
        console_level: Optional[int] = None,
    ):
        """
        Create a logger.

        :param name:
            The name of the logger, typically the date being processed.
        :param log_filename_and_level:
            (filename, level) tuple or None to disable file logging.
        :param console_level:
            The log level for the console, or None to disable console logging.
        """

        self.log_filename_and_level = log_filename_and_level
        self.console_level = console_level

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        if os.getenv("EXCLUDE_LOG_TIME", "no") == "yes":
            # test convenience to facilitate local diffing of log files
            fmt = "%(levelname)s %(message)s"
        else:
            fmt = "%(asctime)s %(levelname)s %(message)s"

        formatter = logging.Formatter(fmt)

        if log_filename_and_level is not None:
            log_filename, log_level = log_filename_and_level
            # create log_filename's parent directory if needed:
            parent_dir = pathlib.Path(log_filename).parent
            pathlib.Path(parent_dir).mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_filename, mode="w")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)
            self.logger.addHandler(file_handler)

        if console_level is not None:
            console = logging.StreamHandler()
            console.setLevel(console_level)
            console.setFormatter(formatter)
            self.logger.addHandler(console)

    def is_enabled_for(self, level):
        return self.logger.isEnabledFor(level)

    def info(self, s: str):
        self.logger.info(s)

    def debug(self, s: str):
        self.logger.debug(s)

    def warn(self, s: str):
        self.logger.warning(s)

    def error(self, s: str):
        self.logger.error(s)

    def exception(self, s: str):
        self.logger.exception(s)


def create_logger(
    log_filename_and_level: Optional[Tuple[str, int]] = None,
    console_level: Optional[int] = None,
) -> PbpLogger:
    """
    Creates a logger. A random name is associated.
    """
    name = "_" + "".join(random.choices(string.ascii_letters, k=7))
    return PbpLogger(name, log_filename_and_level, console_level)
