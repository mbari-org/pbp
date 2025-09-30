from typing import Any, Generator, Tuple, Union
from argparse import ArgumentParser, Namespace

import numpy as np


# TODO some utilities here could be moved to pbp.util as they are generic, not hmb-gen specific.


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


def gen_hour_minute_second_times(
    segment_size_in_secs: int = 60,
) -> Generator[Tuple[int, int, int], None, None]:
    """
    Generate a sequence of starting (hour, minute, second) tuples to cover a whole day.
    For example, for segment_size_in_secs=10, the sequence is:
    (0, 0, 0), (0, 0, 10), (0, 0, 20), ..., (23, 59, 50)
    """
    day_seconds = 24 * 60 * 60
    current_second = 0

    while current_second < day_seconds:
        hours = current_second // 3600
        minutes = (current_second % 3600) // 60
        seconds = current_second % 60
        yield hours, minutes, seconds
        current_second += segment_size_in_secs


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
