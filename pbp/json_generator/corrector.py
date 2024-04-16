# pypam-based-processing, Apache License 2.0
# Filename: metadata/utils/corrector.py
# Description: Correct metadata for wav files and saves the results to a json file.

import datetime
from datetime import timedelta
from loguru import logger as log
import numpy as np
import pandas as pd
from pathlib import Path
import shutil
import tempfile
import json


class MetadataCorrector:
    def __init__(
        self,
        correct_df: pd.DataFrame,
        json_path_out: str,
        day: datetime,
        variable_duration: bool = False,
        seconds_per_file: float = -1,
    ):
        """
        Correct the metadata for a day and save to a json file
        :param correct_df:
            The dataframe containing the metadata to correct
        :param json_path_out:
            The path to save the corrected metadata json file
        :param day:
            The day to correct
        :param variable_duration:
            True if the files vary in duration
        :param seconds_per_file:
            The number of seconds in each file; not used for sound trap files
        """
        self.correct_df = correct_df
        self.json_base_dir = json_path_out
        self.day = day
        self.variable_duration = variable_duration
        self.seconds_per_file = seconds_per_file

    def run(self):
        """Run the corrector"""

        try:
            if self.variable_duration:
                files_per_day = None
                # Filter the metadata to the day, starting 6 hours before the day starts to capture overlap
                df = self.correct_df[
                    (self.correct_df["start"] >= self.day - timedelta(hours=6))
                    & (self.correct_df["start"] < self.day + timedelta(days=1))
                ]
            else:  # ICListen/NRS files fixed, but may be missing or incomplete if the system was down
                files_per_day = int(86400 / self.seconds_per_file)
                # Filter the metadata to the day, starting 1 file before the day starts to capture overlap
                df = self.correct_df[
                    (
                        (self.correct_df["start"] >= self.day)
                        & (self.correct_df["start"] < self.day + timedelta(days=1))
                    )
                    | (
                        (self.correct_df["end"] >= self.day)
                        & (self.correct_df["start"] < self.day)
                    )
                ]

            log.debug(f"Creating metadata for day {self.day}")

            if len(df) == 0:
                log.warning(f"No metadata found for day {self.day}")
                return

            # convert the start and end times to datetime
            df = df.copy()

            df["start"] = pd.to_datetime(df["start"])
            df["end"] = pd.to_datetime(df["end"])

            # get the file list that covers the requested day
            log.info(
                f'Found {len(df)} files from day {self.day}, starting {df.iloc[0]["start"]} ending {df.iloc[-1]["end"]}'
            )

            # if there are no files, then return
            if len(df) == 0:
                log.warning(f"No files found for {self.day}")
                return

            day_process = df

            if self.variable_duration:
                log.info(f"Files for {self.day} are variable. Skipping duration check")
                for index, row in day_process.iterrows():
                    log.debug(f'File {row["uri"]} duration {row["duration_secs"]} ')
            else:
                for index, row in day_process.iterrows():
                    # if the duration_secs is not seconds per file, then the file is not complete
                    if row["duration_secs"] != self.seconds_per_file:
                        log.warning(
                            f'File {row["duration_secs"]}  != {self.seconds_per_file}. File is not complete'
                        )
                        continue

            # check whether there is a discrepancy between the number of seconds in the file and the number
            # of seconds in the metadata. If there is a discrepancy, then correct the metadata
            # This is only reliable for full days of data contained in complete files for IcListen data
            day_process["jitter_secs"] = 0

            if self.variable_duration or (
                len(day_process) == files_per_day + 1
                and len(day_process["duration_secs"].unique()) == 1
                and day_process.iloc[0]["duration_secs"] == self.seconds_per_file
            ):
                # check whether the differences are all the same
                if (
                    len(day_process["start"].diff().unique()) == 1
                    or self.variable_duration
                ):
                    log.warning(f"No drift for {self.day}")
                else:
                    log.info(f"Correcting drift for {self.day}")

                    # correct the metadata
                    jitter = 0
                    start = day_process.iloc[0]["start"]
                    end = start + timedelta(seconds=self.seconds_per_file)

                    for index, row in day_process.iterrows():
                        # jitter is the difference between the expected start time and the actual start time
                        # jitter is 0 for the first file
                        if row.start == start:
                            # round the jitter to the nearest second
                            jitter = start.to_datetime64() - row.start.to_datetime64()
                            jitter = int(jitter / np.timedelta64(1, "s"))

                        # correct the start and end times
                        day_process.loc[index, "start"] = start
                        day_process.loc[index, "end"] = end
                        day_process.loc[index, "jitter_secs"] = jitter

                        if self.variable_duration:
                            end = row.end
                        else:
                            end = start + timedelta(seconds=self.seconds_per_file)
                        # round the end time to the nearest second as the timestamp is only accurate to the second
                        end = end.replace(microsecond=0)
                        # set the times for the next files
                        start = end
            else:
                day_process = self.no_jitter(self.day, day_process)

            # drop any rows with duplicate uri times, keeping the first
            # duplicates can be caused by the jitter correction
            if "uri" in day_process.columns:
                day_process = day_process.drop_duplicates(subset=["uri"], keep="first")
            if "url" in day_process.columns:
                day_process = day_process.drop_duplicates(subset=["url"], keep="first")

            # save explicitly as UTC by setting the timezone in the start and end times
            day_process["start"] = day_process["start"].dt.tz_localize("UTC")
            # Note: as day_process["end"] coming from upstream seems to become incorrect
            # (except for the first entry in the JSON), that is, with `end` becoming equal to `start`,
            # directly assigning it here based on day_process["start"]:
            day_process["end"] = day_process["start"] + timedelta(
                seconds=self.seconds_per_file
            )
            # TODO(Danelle): review/confirm the above.

            self.save_day(self.day, day_process)

        except Exception as e:
            log.exception(f"Error correcting metadata for  {self.day}. {e}")
        finally:
            log.debug(
                f"Done correcting metadata for {self.day}. Saved to {self.json_base_dir}"
            )

    def no_jitter(self, day: datetime, day_process: pd.DataFrame) -> pd.DataFrame:
        """
        Set the jitter to 0 and calculate the end time from the start time and the duration
        :param day:
            The day being processed
        :param day_process:
            The dataframe to correct
        :return:
            The corrected dataframe
        """
        log.warning(
            f"Cannot correct {self.day}. Using file start times as is, setting jitter to 0 and using "
            f"calculated end times."
        )
        # calculate the difference between each row start time and save as diff in a copy of the dataframe
        day_process = day_process.copy()
        day_process["diff"] = day_process["start"].diff()
        day_process["jitter_secs"] = 0
        # calculate the end time which is the start time plus the number of seconds in the file
        day_process["end"] = day_process["start"] + pd.to_timedelta(
            day_process["duration_secs"], unit="s"
        )
        return day_process

    def save_day(self, day: datetime, day_process: pd.DataFrame, prefix: str = None):
        """
        Save the day's metadata to a single json file either locally or to s3
        :param day:
            The day to save
        :param day_process:
            The dataframe containing the metadata for the day
        :param prefix:
            An optional prefix for the filename
        :return:
        """
        # if the exception column is empty, then drop it
        if day_process["exception"].isnull().all():
            day_process.drop(columns=["exception"], inplace=True)
        else:
            # replace the NaN with an empty string
            day_process["exception"].fillna("", inplace=True)

        # drop the pcm, fs, subtype, etc. columns
        day_process.drop(columns=["fs", "subtype", "jitter_secs"], inplace=True)

        # if there is a diff column, then drop it
        if "diff" in day_process.columns:
            day_process.drop(columns=["diff"], inplace=True)

        # Save with second accuracy to a temporary file formatted with ISO date format
        df_final = day_process.sort_values(by=["start"])

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            if prefix:
                temp_metadata = tmp_path / f"{prefix}_{day:%Y%m%d}.json"
            else:
                temp_metadata = tmp_path / f"{day:%Y%m%d}.json"

            df_final.to_json(
                temp_metadata.as_posix(),
                orient="records",
                date_format="iso",
                date_unit="s",
            )
            log.debug(f"Wrote {temp_metadata.as_posix()}")

            # read the file back in using records format with json
            with open(temp_metadata.as_posix(), "r") as f:
                dict_records = json.load(f)

            # write the file back out with indenting
            with open(temp_metadata.as_posix(), "w", encoding="utf-8") as f:
                json.dump(dict_records, f, ensure_ascii=True, indent=4)

            # copy the file to a local metadata directory with year subdirectory
            output_path = Path(self.json_base_dir, str(day.year))
            output_path.mkdir(parents=True, exist_ok=True)
            shutil.copy2(temp_metadata.as_posix(), output_path)
            log.info(f"Wrote {output_path}/{temp_metadata.name}")
