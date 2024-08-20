# pbp, Apache License 2.0
# Filename: meta_gen/utils.py
# Description:  Utility functions for parsing S3, GS or local file urls and defining sound instrument types for metadata generation
import re
from typing import Tuple, List
from urllib.parse import urlparse
from datetime import datetime
from pathlib import Path


class InstrumentType:
    NRS = "NRS"
    ICLISTEN = "ICLISTEN"
    SOUNDTRAP = "SOUNDTRAP"


def parse_s3_or_gcp_url(url) -> Tuple[str, str, str]:
    """
    Parse the S3, GS of local file url
    :param url: The url to parse, e.g. s3://bucket/prefix, gs://bucket/prefix, file://path/to/file
    :return: a tuple with the bucket, prefix and scheme
    """
    parsed_url = urlparse(url)
    bucket = parsed_url.netloc
    prefix = parsed_url.path.lstrip("/")
    if parsed_url.scheme == "file":
        bucket = ""
        prefix = parsed_url.path
    return bucket, prefix, parsed_url.scheme


# Function to extract the timecode
def extract_timecode(filename: str, prefixes: List[str]):
    """
    Extract the timecode from a filename
    :param filename: The filename to extract the timecode from
    :param prefixes: The prefixes to match the filename, e.g. MARS, NRS11, 6000
    :return: The timecode or None if the timecode cannot be extracted
    """
    # Define the regex patterns for the different formats, e.g. MARS_YYYYMMDD_HHMMSS.wav, NRS11_20191023_222213.flac,
    # 6000.221111155338.wav
    patterns = {
        "underscore_format1": r"{}[._]?(\d{{8}})_(\d{{6}})\.\w+$",
        "underscore_format2": r"{}[._]?(\d{{6}})_(\d{{6}})\.\w+$",
        "dot_format": r"{}[._]?(\d{{12}})\.\w+$",
        "iso_format": r"{}[._]?(\d{{8}}T\d{{6}}Z)\.\w+$",
    }
    for prefix in prefixes:
        for pattern_name, pattern in patterns.items():
            regex = pattern.format(prefix)
            match = re.match(regex, Path(filename).name)
            if match:
                timecode_parts = match.groups()
                # Correct the seconds if they are 60 - this happens in some NRS files
                hhmmss = timecode_parts[-1]
                if hhmmss[-2:] == "60":
                    hhmmss = hhmmss[:-2] + "59"
                    corrected_timecode = timecode_parts[:-1] + (hhmmss,)
                    return "".join(corrected_timecode)

                return "".join(timecode_parts)
    return None


def get_datetime(time_str: str, prefixes: List[str]):
    """
    Parse all possible time formats in the time_str into a datetime object
    :param time_str: The time string to parse
    :param prefixes: The prefixes to match the filename, e.g. MARS, NRS11, 6000
    :return: datetime object or None if the time_str cannot be parsed
    """
    time_str = extract_timecode(time_str, prefixes)
    if time_str is None:
        return None
    possible_dt_formats = [
        "%Y%m%d_%H%M%S",
        "%y%m%d_%H%M%S",
        "%y%m%d%H%M%S",
        "%Y%m%d%H%M%S",
        "%Y%m%dT%H%M%SZ",
        "%Y%m%dT%H%M%S",
    ]
    for fmt in possible_dt_formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue

    return None
