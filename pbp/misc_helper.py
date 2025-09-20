from typing import Any, Generator, Optional, Tuple, Union
from argparse import ArgumentParser, Namespace

from datetime import datetime, timezone
import numpy as np


def parse_timestamp(string: str, pattern: str) -> Optional[datetime]:
    """
    Extracts a timestamp from a string given a strftime-based pattern.

    Args:
        string (str): The string to parse, e.g. "MARS_20250914_122000.wav"
        pattern (str): A pattern with strftime codes, e.g. "MARS_%Y%m%d_%H%M%S.wav".
                      Non-strftime parts are treated as literal text.
    Returns:
        Optional[datetime]: The extracted timestamp, or None if it could not be parsed.
    """

    try:
        parsed = datetime.strptime(string, pattern)
        return parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_date(date: str) -> Tuple[int, int, int]:
    """
    Parses given string into a (year, month, day) integer tuple.
    :param date:
        Digit string with YYYYMMDD format.
    :return:
        (year, month, day) tuple.
    """
    assert date.isdigit() and len(date) == 8
    year, month, day = int(date[:4]), int(date[4:6]), int(date[6:8])
    return year, month, day


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


# Using Union as `X | Y syntax for unions requires Python 3.10`
def brief_list(lst: Union[list, np.ndarray[Any, Any]], max_items: int = 6) -> str:
    """
    Helper to format a list as a string, with a maximum number of items.
    :param lst:  The list to format.
    :param max_items:  The maximum number of items to show.
    :return:  The formatted string.
    """
    if len(lst) > max_items:
        half = max_items // 2
        rest = max_items - half
        prefix = ", ".join(str(x) for x in lst[:half])
        postfix = ", ".join(str(x) for x in lst[-rest:])
        return f"[{prefix}, ..., {postfix}]"
    return str(lst)


def print_given_args(parser: ArgumentParser, args: Namespace):
    """
    Prints the arguments that differ from their default values.
    """
    args_to_print = []

    for action in parser._actions:
        if hasattr(action, "dest") and action.dest != "help":
            actual_value = getattr(args, action.dest, None)
            default_value = action.default
            if actual_value != default_value and actual_value is not None:
                arg_name = action.dest.replace("_", "-")
                args_to_print.append((f"--{arg_name}", actual_value))

    if args_to_print:
        args_to_print.sort(key=lambda x: x[0])
        max_width = max(len(arg_name) for arg_name, _ in args_to_print)
        print(" Arguments differing from defaults:")
        for arg_name, value in args_to_print:
            print(f"    {arg_name:<{max_width}}  {value}")
