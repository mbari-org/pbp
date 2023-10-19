from typing import Any, Generator, Tuple


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


# This:
# def brief_list(l: Union[List, np.ndarray[Any, Any]], max_items: int = 6) -> str:
# is causing trouble on gizo:
#   File "/PAM_Analysis/pypam-space/processing_our_data/pypam-based-processing/src/misc_helper.py", line 88, in <module>
#     def brief_list(l: Union[List, np.ndarray[Any, Any]], max_items: int = 6) -> str:
# TypeError: Type subscription requires python >= 3.9
# Disappointing that a type spec is not being just skipped at runtime! :(
# So, let's simplify like this for now:'
def brief_list(l: Any, max_items: int = 6) -> str:
    """
    Helper to format a list as a string, with a maximum number of items.
    :param l:  The list to format.
    :param max_items:  The maximum number of items to show.
    :return:  The formatted string.
    """
    if len(l) > max_items:
        half = max_items // 2
        rest = max_items - half
        prefix = ", ".join(str(x) for x in l[:half])
        postfix = ", ".join(str(x) for x in l[-rest:])
        return f"[{prefix}, ..., {postfix}]"
    return str(l)
