import logging
from typing import Generator, Tuple

# for simplicity, a common logger
LOGGER_NAME = "PYPBP"


def set_logger(output_dir: str, year: int, month: int, day: int) -> str:
    logger = get_logger()
    log_filename = f"{output_dir}/milli_psd_{year:04}{month:02}{day:02}.log"
    handler = logging.FileHandler(log_filename, mode="w")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    # also log to console
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    logger.addHandler(console)
    return log_filename


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)


def info(s: str):
    logging.getLogger(LOGGER_NAME).info(s)


def debug(s: str):
    get_logger().debug(s)


def warn(s: str):
    get_logger().warning(s)


def error(s: str):
    get_logger().error(s)


def gen_hour_minute_times(
    segment_size_in_mins: int = 1,
) -> Generator[Tuple[int, int], None, None]:
    """
    Generate a sequence of starting (hour, minute) tuples to cover a whole day.
    For example, for segment_size_in_mins=1, the sequence is:
    (0, 0), ..., (23, 58), (23, 59)
    """
    day_minutes = 24 * 60
    current_minute = 0

    while current_minute < day_minutes:
        at_hour, at_minute = divmod(current_minute, 60)
        yield at_hour, at_minute
        current_minute += segment_size_in_mins


def map_prefix(prefix_map: str, s: str) -> str:
    """
    Helper to replace a prefix to another prefix in given string
    according to prefix_map.
    :param prefix_map:  Like "old~new".
    :param s:  The string to replace the prefix in.
    :return:  Resulting string, possibly unchanged.
    """
    if "~" in prefix_map:
        old, new = prefix_map.split("~", 2)
        if s.startswith(old):
            return new + s[len(old) :]
    return s
