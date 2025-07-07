# pbp, Apache License 2.0
# Filename: meta_gen/utils.py
# Description:  Utility functions for parsing S3, GS or local file urls and defining sound instrument types for metadata generation
import re
from typing import Tuple, List
from urllib.parse import urlparse
import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import NullLocator

from pbp.plot_const import DEFAULT_DPI


class InstrumentType:
    NRS = "NRS"
    ICLISTEN = "ICLISTEN"
    SOUNDTRAP = "SOUNDTRAP"
    RESEA = "RESEA"


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
        "underscore_format3": r"{}[._]?(\d{{4}})-(\d{{2}})-(\d{{2}})_(\d{{2}})-(\d{{2}})-(\d{{2}})\.",
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
        "%Y-%m-%d_%H-%M-%S",
    ]
    for fmt in possible_dt_formats:
        try:
            return datetime.datetime.strptime(time_str, fmt)
        except ValueError:
            continue

    return None


def plot_daily_coverage(
    instrument_type: InstrumentType,
    df: pd.DataFrame,
    base_dir: str,
    start: datetime.datetime,
    end: datetime.datetime,
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
    # Create a plot of the dataframe with the x-axis as the month, and the y-axis as the daily recording coverage.
    # This is percent of the day covered by recordings
    plt.rcParams["text.usetex"] = False
    plt.rcParams["axes.edgecolor"] = "black"
    duration = (df["end"] - df["start"]).dt.total_seconds()
    ts_df = df[["start"]].copy()
    ts_df["duration"] = duration
    ts_df.set_index("start", inplace=True)
    daily_sum_df = ts_df.resample("D").sum()
    daily_sum_df["coverage"] = 100 * daily_sum_df["duration"] / 86400
    daily_sum_df["coverage"] = daily_sum_df[
        "coverage"
    ].round()  # round to nearest integer
    # Cap the coverage at 100%
    daily_sum_df["coverage"] = daily_sum_df["coverage"].clip(upper=100)
    if len(daily_sum_df) == 1:
        # Add a row with a NaN coverage before and after the single day to avoid matplotlib
        # warnings about automatically expanding the x-axis
        daily_sum_df.loc[daily_sum_df.index[0] - pd.DateOffset(days=1)] = np.nan
        daily_sum_df.loc[daily_sum_df.index[0] + pd.DateOffset(days=1)] = np.nan
    plot = daily_sum_df["coverage"].plot(
        linestyle="-",
        markerfacecolor="none",
        marker="o",
        color="b",
        markersize=5,
        linewidth=1,
        figsize=(8, 4),
    )
    plot.set_ylabel("Daily % Recording", fontsize=8)
    plot.set_xlabel("Date", fontsize=8)
    plot.set_xticks(daily_sum_df.index.values)
    plot.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    # Maximum 15 ticks on the x-axis
    # plot.xaxis.set_major_locator(
    #     MaxNLocator(nbins=min(15, len(daily_sum_df.index.values) - 1))
    # )
    plot.axes.set_facecolor("#E4E4F1")
    # Rotate the x-axis labels for better readability
    plt.xticks(rotation=45)
    # Set both x and y axis tick label font size to 6
    plot.tick_params(axis="both", which="major", labelsize=6)
    # Disable the minor ticks on the x-axis using NullLocator, as they are not needed
    plot.xaxis.set_minor_locator(NullLocator())
    # Set the y-axis limits to 0-110 to avoid the plot being too close to the top
    plot.set_ylim(0, 110)
    # Adjust the title based on the instrument type
    if instrument_type == InstrumentType.NRS:
        plot.set_title("Daily Coverage of NRS Recordings", fontsize=11)
    elif instrument_type == InstrumentType.ICLISTEN:
        plot.set_title("Daily Coverage of icListen Recordings", fontsize=11)
    elif instrument_type == InstrumentType.SOUNDTRAP:
        plot.set_title("Daily Coverage of SoundTrap Recordings", fontsize=11)
    plot_file = (
        Path(base_dir)
        / f"{str(instrument_type).lower()}_coverage_{start:%Y%m%d}_{end:%Y%m%d}.jpg"
    )
    fig = plot.get_figure()
    fig.autofmt_xdate()
    fig.savefig(plot_file.as_posix(), dpi=DEFAULT_DPI, bbox_inches="tight")
    plt.close(fig)
    return plot_file.as_posix()


def check_start_end_args(start, end):
    """
    Check if start and end dates are at 00:00:00. If it's a datetime.date object, convert to datetime.datetime object.
    :param start The start date of the recordings
    :param end The end date of the recordings
    :return The corrected start and end date of the recordings as datetime.datetime objects
    """
    if type(start) is datetime.date:
        start = datetime.datetime(start.year, start.month, start.day)
    if type(end) is datetime.date:
        end = datetime.datetime(end.year, end.month, end.day)

    if type(start) is datetime.datetime:
        if start.hour == 0 and start.minute == 0 and start.second == 0:
            pass
        else:
            raise ValueError(
                "Start must be of type datetime.date or a datetime.datetime object at 00:00:00. "
                "Otherwise that would be the start of the HMD computation."
            )

    if type(end) is datetime.datetime:
        if end.hour == 0 and end.minute == 0 and end.second == 0:
            pass
        else:
            raise ValueError(
                "End must be of type datetime.date or a datetime.datetime object at 00:00:00. "
                "Otherwise that would be the start of the HMD computation."
            )

    return start, end
