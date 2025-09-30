from typing import Optional

from datetime import datetime, timezone


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
