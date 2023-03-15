import logging
from typing import Generator, Tuple


def set_logger(opts):
    log_filename = (
        f"{opts.output_dir}/milli_psd_{opts.year:04}{opts.month:02}{opts.day:02}.log"
    )
    logging.basicConfig(
        filename=log_filename,
        filemode="w",
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def info(s: str):
    logging.info(s)


def debug(s: str):
    logging.debug(s)


def warn(s: str):
    logging.warning(s)


def error(s: str):
    logging.error(s)


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
