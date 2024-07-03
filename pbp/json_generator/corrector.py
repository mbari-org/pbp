# pypam-based-processing, Apache License 2.0
# Filename: metadata/utils/corrector.py
# Description: Correct metadata for wav files and saves the results to a json file.

import datetime
from datetime import timedelta
import numpy as np
import pandas as pd
from pathlib import Path
import shutil
import tempfile
import json

from pbp.json_generator.utils import InstrumentType


class MetadataCorrector:
    def __init__(
        self,
        log,  # : loguru.Logger,
        correct_df: pd.DataFrame,
        json_path_out: str,
        day: datetime,
        instrument_type: InstrumentType,
        time_correct: bool = False,
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
        :param instrument_type:
            The type of instrument the metadata is coming from: NRS, ICLISTEN, SOUNDTRAP
        :param time_correct:
            True if need to adjust the time stamp based only supported for ICLISTEN
        :param seconds_per_file:
            (optional) number of seconds in each file
        """
        self.instrument_type = instrument_type
        self.correct_df = correct_df
        self.json_base_dir = json_path_out
        self.day = day
        self.log = log
        self.time_correct = time_correct
        self.seconds_per_file = seconds_per_file
        self.files_per_day = None
        # Must have seconds per file for ICLISTEN to correct for drift conditional check
        if self.instrument_type == InstrumentType.ICLISTEN:
            if self.seconds_per_file == -1:
                self.log.exception("No seconds per file provided for ICLISTEN")
                return
            self.files_per_day = int(86400 / self.seconds_per_file)
            self.log.debug(
                f"Metadata corrector for {self.instrument_type} with {self.seconds_per_file} seconds per file"
            )

    def run(self):
        """Run the corrector"""

        try:
            # Filter the metadata to the day capturing the files both immediately
            # before and after the day
            df = self.correct_df[
                (
                    (self.correct_df["start"] >= self.day)
                    & (self.correct_df["end"] < self.day + timedelta(days=1))
                )
                | (
                    (self.correct_df["end"] > self.day)
                    & (self.correct_df["start"] <= self.day)
                )
            ]

            self.log.debug(f"Creating metadata for day {self.day} from {len(df)} files...")

            if len(df) == 0:
                self.log.warning(f"No metadata found for day {self.day}")
                return

            # convert the start and end times to datetime
            self.log.info(f'{df.iloc[0]["start"]}')
            df = df.copy()
            self.log.info(f'{df.iloc[0]["start"]}')

            df["start"] = pd.to_datetime(df["start"])
            df["end"] = pd.to_datetime(df["end"])

            self.log.info(f'====> {len(df)}')
            # get the file list that covers the requested day
            # self.log.info(
            #     f'Found {len(df)} files from day {self.day}, starting {df.iloc[0]["start"]} ending {df.iloc[-1]["end"]}'
            # )

            # if there are no files, then return
            if len(df) == 0:
                self.log.warning(f"No files found for {self.day}")
                return

            day_process = df

            for index, row in day_process.iterrows():
                self.log.debug(f'File {row["uri"]} duration {row["duration_secs"]} ')
                if (
                    self.seconds_per_file > 0
                    and row["duration_secs"] != self.seconds_per_file
                ):
                    self.log.warning(
                        f'File {row["duration_secs"]}  != {self.seconds_per_file}. File is not complete'
                    )

            # check whether there is a discrepancy between the number of seconds in the file and the number
            # of seconds in the metadata. If there is a discrepancy, then correct the metadata
            # This is only reliable for full days of data contained in complete files for IcListen data
            day_process["jitter_secs"] = 0

            if self.instrument_type == InstrumentType.ICLISTEN and (
                len(day_process) == self.files_per_day + 1
                and len(day_process["duration_secs"].unique()) == 1
                and day_process.iloc[0]["duration_secs"] == self.seconds_per_file
            ):
                # check whether the differences are all the same
                if len(day_process["start"].diff().unique()) == 1 or self.time_correct:
                    self.log.warning(f"No drift for {self.day}")
                else:
                    self.log.info(f"Correcting drift for {self.day}")

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

                        if self.time_correct:
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
            day_process["end"] = day_process["start"] + timedelta(
                seconds=self.seconds_per_file
            )

            self.save_day(self.day, day_process)

        except Exception as e:
            self.log.exception(f"Error correcting metadata for  {self.day}. {e}")
        finally:
            self.log.debug(
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
        self.log.warning(
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
            self.log.debug(f"Wrote {temp_metadata.as_posix()}")

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
            self.log.info(f"Wrote {output_path}/{temp_metadata.name}")
