from typing import Any, Generator, Optional, Tuple, Union
from argparse import ArgumentParser, Namespace

from datetime import datetime, timezone
import numpy as np


def extract_datetime(string: str, pattern: str) -> Optional[datetime]:
    """
    Extracts a datetime instance from a string given a strftime-based pattern.

    Args:
        string (str): The string to parse, e.g. "/path/to/MARS_20250914_122000.wav"
        pattern (str): A strftime pattern, e.g. "%Y%m%d_%H%M%S".
                      The pattern will be searched for anywhere within the string.
    Returns:
        Optional[datetime]: The extracted datetime, or None if it could not be parsed.
          For the example above: `datetime(2025, 9, 14, 12, 20, 0, tzinfo=timezone.utc)`.
    """
    import re

    try:
        # Convert strftime pattern to regex pattern
        # Replace strftime codes with regex groups that capture the expected format
        strftime_to_regex = {
            "%Y": r"(\d{4})",  # 4-digit year
            "%y": r"(\d{2})",  # 2-digit year
            "%m": r"(\d{1,2})",  # 1 or 2-digit month
            "%d": r"(\d{1,2})",  # 1 or 2-digit day
            "%H": r"(\d{1,2})",  # 1 or 2-digit hour
            "%M": r"(\d{1,2})",  # 1 or 2-digit minute
            "%S": r"(\d{1,2})",  # 1 or 2-digit second
        }

        # Build regex pattern from strftime pattern
        regex_pattern = pattern
        strftime_codes = []
        for strftime_code, regex_group in strftime_to_regex.items():
            if strftime_code in regex_pattern:
                strftime_codes.append(strftime_code)
                regex_pattern = regex_pattern.replace(strftime_code, regex_group)

        # Find all matches and take the last one
        matches = list(re.finditer(regex_pattern, string))
        if not matches:
            return None

        # Extract the last matched timestamp part
        timestamp_string = matches[-1].group(0)

        # Parse using the original strftime pattern
        parsed = datetime.strptime(timestamp_string, pattern)
        return parsed.replace(tzinfo=timezone.utc)

    except (ValueError, re.error):
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
