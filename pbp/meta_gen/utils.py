# pbp, Apache License 2.0
# Filename: meta_gen/utils.py
# Description:  Utility functions for parsing S3, GS or local file urls and defining sound instrument types for metadata generation
import re
from typing import Tuple, List
from urllib.parse import urlparse
from datetime import datetime
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


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
        "underscore_format1": r"{}[._]?(\d{{8}})_(\d{{6}})\.",
        "underscore_format2": r"{}[._]?(\d{{6}})_(\d{{6}})\.",
        "dot_format": r"{}[._]?(\d{{12}})\.",
        "iso_format": r"{}[._]?(\d{{8}}T\d{{6}}Z)\.",
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


def plot_daily_coverage(
    instrument_type: InstrumentType,
    df: pd.DataFrame,
    base_dir: str,
    start: datetime,
    end: datetime,
) -> str:
    """
    Plot the daily coverage of the recordings
    :param instrument_type: The type of instrument, e.g. NRS, ICLISTEN, SOUNDTRAP
    :param df: The dataframe with the recordings
    :param base_dir: The base directory to store the plot
    :param start: The start date of the recordings
    :param end: The end date of the recordings
    :return: The path to the plot file
    """
    # Create a plot of the dataframe with the x-axis as the month, and the y-axis as the daily recording coverage,
    # which is percent of the day covered by recordings
    plt.rcParams["text.usetex"] = False
    df["duration"] = (df["end"] - df["start"]).dt.total_seconds()
    ts_df = df[["start", "duration"]].copy()
    ts_df.set_index("start", inplace=True)
    daily_sum_df = ts_df.resample("D").sum()
    daily_sum_df["coverage"] = 100 * daily_sum_df["duration"] / 86400
    daily_sum_df["coverage"] = daily_sum_df[
        "coverage"
    ].round()  # round to nearest integer
    plot = daily_sum_df["coverage"].plot()
    plot.set_ylabel("Daily % Recording")
    plot.set_xlabel("Date")
    plot.set_xticks(daily_sum_df.index.values)
    plot.set_ylim(0, 102)
    # Angle the x-axis labels for better readability and force them to be in the format YYYY-MM-DD
    plot.set_xticklabels([x.strftime("%Y-%m-%d") for x in daily_sum_df.index])
    plot.set_xticklabels(plot.get_xticklabels(), rotation=45, horizontalalignment="right")
    # Adjust the title based on the instrument type
    if instrument_type == InstrumentType.NRS:
        plot.set_title("Daily Coverage of NRS Recordings")
    elif instrument_type == InstrumentType.ICLISTEN:
        plot.set_title("Daily Coverage of icListen Recordings")
    elif instrument_type == InstrumentType.SOUNDTRAP:
        plot.set_title("Daily Coverage of SoundTrap Recordings")
    plot_file = Path(base_dir) / f"soundtrap_coverage_{start:%Y%m%d}_{end:%Y%m%d}.jpg"
    dpi = 300
    fig = plot.get_figure()
    fig.set_size_inches(10, 5)
    fig.set_dpi(dpi)
    fig.savefig(plot_file.as_posix(), bbox_inches="tight")
    plt.close(fig)
    return plot_file.as_posix()
