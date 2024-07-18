# pbp, Apache License 2.0
# Filename: metadata/generator/gen_base.py
# Description:  Base class that captures sound wav metadata
from datetime import datetime
from pathlib import Path
from typing import List

import matplotlib.dates as mdates
import pandas as pd


class MetadataGeneratorBase(object):
    def __init__(
        self,
        log,  # : loguru.Logger,
        audio_loc: str,
        json_base_dir: str,
        prefix: List[str],
        start: datetime,
        end: datetime,
        seconds_per_file: float = 0.0,
        **kwargs,
    ):
        """
        Base class for capturing sound wav metadata
        :param audio_loc:
            The local directory or cloud bucket that contains the wav files
        :param json_base_dir:
            The local directory to write the json files to
        :param prefix:
            The search pattern to match the wav files, e.g. 'MARS'
        :param start:
            The start date to search for wav files
        :param end:
            The end date to search for wav files
        :param seconds_per_file:
            The number of seconds per file expected in a wav file to check for missing data. If missing, then no check is done.
        :return:
        """
        try:
            self.audio_loc = audio_loc
            self.json_base_dir = json_base_dir
            self.df = pd.DataFrame()
            self.start = start
            self.end = end
            self.prefix = prefix
            self._log = log
            self._seconds_per_file = None if seconds_per_file == 0 else seconds_per_file
        except Exception as e:
            raise e

    @property
    def seconds_per_file(self):
        return self._seconds_per_file

    @property
    def log(self):
        return self._log

    # abstract run method
    def run(self):
        pass

    def plot_coverage(self, json_base_dir, prefix: str = ""):
        # Create a plot of the dataframe with the x axis as the month, and the y axis as the daily recording
        # coverage, which is percent of the day covered by recordings
        self.df["duration"] = (self.df["end"] - self.df["start"]).dt.total_seconds()
        if self.df["duration"].nunique() == 1:
            self.log.info(
                f"All recorded durations are the same length: {self.df['duration'].iloc[0]} seconds"
            )
        # Create a timeseries with 1 second resolution, starting with the first start time and ending with the last
        # end time
        seconds_dt = pd.date_range(
            start=self.df.iloc[0]["start"], end=self.df.iloc[-1]["end"], freq="1s"
        )
        seconds_df = pd.DataFrame(seconds_dt)
        seconds_df["duration"] = 1
        # Create a new dataframe that populates a 10second resolution for the duration of the recording
        recording_df = pd.DataFrame()
        for i, row in self.df.iterrows():
            df = pd.DataFrame(
                index=pd.date_range(start=i, periods=int(row["duration"]), freq="1s")
            )
            df["duration"] = 1
            recording_df = pd.concat([recording_df, df])
        # Sum how`many seconds are in each day in new_df
        daily_sum_df = recording_df.resample("1D").sum()
        # Truncate to the start and end dates
        daily_sum_df = daily_sum_df[
            (daily_sum_df.index <= self.start) & (daily_sum_df.index <= self.end)
        ]
        if daily_sum_df.empty:
            self.log.info(
                f"No recordings found in the date range {self.start} to {self.end}"
            )
            return
        # Calculate the coverage as a percentage and round to the nearest integer
        daily_sum_df["coverage"] = (
            100 * daily_sum_df["duration"] / 86400
        )  # 86400 seconds in a day
        plot = daily_sum_df["coverage"].plot()
        plot.set_ylabel("Recording coverage (% of day)")
        plot.set_ylim(0, 100)
        # Setting the tick positions to weekly if the period is less than 30 days, otherwise monthly
        if (self.end - self.start).days < 30:
            plot.xaxis.set_major_locator(mdates.WeekdayLocator())
            plot.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M:%S"))
            plot.tick_params(axis="x", rotation=45)
        else:
            plot.xaxis.set_major_locator(mdates.MonthLocator())
            plot.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M:%S"))
            plot.tick_params(axis="x", rotation=45)
        # Enhance the line color and width to make it more visible - note that anything with a few percent will not
        # be noticeably different in the plot
        plot.get_lines()[0].set_color("blue")
        plot.get_lines()[0].set_linewidth(5)
        plot.set_title(
            f"{prefix} Temporal coverage of recording for {self.start :%Y-%m-%d} to {self.end :%Y-%m-%d}"
        )
        plot_file = (
            Path(json_base_dir)
            / f"{prefix}_coverage_{self.start :%Y%m%d}_{self.end :%Y%m%d}.png"
        )
        fig = plot.get_figure()
        fig.set_size_inches(10, 5)
        fig.set_dpi(300)
        if plot_file.exists():
            plot_file.unlink()
        fig.savefig(plot_file.as_posix(), bbox_inches="tight")
        self.log.info(f"Saved plot to {plot_file}")
        daily_sum_df = daily_sum_df.rename_axis("day")
        daily_sum_df = daily_sum_df.rename(columns={"duration": "seconds"})
        daily_sum_df["coverage"] = daily_sum_df["coverage"].round(2)
        if len(prefix) > 0:
            daily_sum_df.to_csv(
                Path(json_base_dir)
                / f"{prefix}_coverage_{self.start :%Y%m%d}_{self.end :%Y%m%d}.csv"
            )
        else:
            daily_sum_df.to_csv(
                Path(json_base_dir)
                / f"coverage_{self.start :%Y%m%d}_{self.end :%Y%m%d}.csv"
            )
