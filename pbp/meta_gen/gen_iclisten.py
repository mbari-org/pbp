# pbp, Apache License 2.0
# Filename: metadata/generator/gen_iclisten.py
# Description:  Captures ICListen wav metadata in a pandas dataframe from either a local directory or S3 bucket.
from datetime import timedelta
from datetime import datetime
from typing import List

import boto3
from botocore import UNSIGNED
from botocore.client import Config
import loguru

import pandas as pd
from pathlib import Path
from progressbar import progressbar
from pbp.meta_gen.utils import (
    InstrumentType,
    parse_s3_or_gcp_url,
    get_datetime,
    plot_daily_coverage,
)
from pbp.meta_gen.json_generator import JsonGenerator
from pbp.meta_gen.meta_reader import GenericWavFile, FlacFile
from pbp.meta_gen.gen_abstract import MetadataGeneratorAbstract


class IcListenMetadataGenerator(MetadataGeneratorAbstract):
    log_prefix = None

    def __init__(
        self,
        log: "loguru.Logger",
        uri: str,
        json_base_dir: str,
        start: datetime,
        end: datetime,
        prefixes: List[str],
        seconds_per_file: float = 600.0,
    ):
        """
        Captures ICListen wav metadata in a pandas dataframe from either a local directory or S3 bucket.
        :param uri:
            The local directory or S3 bucket that contains the wav files
        :param json_base_dir:
            The local directory to store the metadata
        :param start:
            The start date to search for wav files
        :param end:
            The end date to search for wav files
        :param prefixes:
            The search pattern to match the wav files, e.g. 'MARS_' for MARS_YYYYMMDD_HHMMSS.wav
        :param seconds_per_file:
            The number of seconds per file expected in a wav file to check for missing data. If 0, then no check is done.
        :return:
        """
        super().__init__(log, uri, json_base_dir, prefixes, start, end, seconds_per_file)
        self.log_prefix = f"{self.__class__.__name__} {start:%Y%m%d}"

    def run(self):
        self.log.info(
            f"{self.log_prefix} Generating metadata for {self.start} to {self.end}..."
        )

        bucket_name, prefix, scheme = parse_s3_or_gcp_url(self.audio_loc)

        # gs is not supported for icListen
        if scheme == "gs":
            self.log.error(
                f"{self.log_prefix} GS is not supported for icListen audio files"
            )
            return

        # Run for each day in the range
        self.df = None
        for day in pd.date_range(self.start, self.end, freq="D"):
            try:
                for s in self.prefixes:
                    self.log.info(
                        f"{self.log_prefix} Searching in {self.audio_loc}/ "
                        f"for wav or flac files that match the search patterns {s}* ..."
                    )

                sound_files = []

                # Set the start and end dates to 1 hour before and after the start and end dates
                start_dt = day - timedelta(hours=1)
                end_dt = day + timedelta(days=1)

                if scheme == "file":
                    sound_path = Path(self.audio_loc.split("file://")[-1])
                    file_extensions = ["*.flac", "*.wav"]
                    for ext in file_extensions:
                        for filename in progressbar(
                            sorted(sound_path.rglob(ext)), prefix="Searching : "
                        ):
                            f_dt = get_datetime(filename, self.prefixes)
                            if f_dt and start_dt <= f_dt <= end_dt:
                                self.log.info(
                                    f"Found file {filename} with timestamp {f_dt}"
                                )
                                if ext == "*.flac":
                                    sound_files.append(
                                        FlacFile(self.log, str(filename), f_dt)
                                    )
                                if ext == "*.wav":
                                    sound_files.append(
                                        GenericWavFile(self.log, str(filename), f_dt)
                                    )

                if scheme == "s3":
                    client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
                    for day_hour in pd.date_range(start=start_dt, end=end_dt, freq="h"):
                        bucket = f"{bucket_name}-{day_hour.year:04d}"

                        for p in self.prefixes:
                            prefix = f"{day_hour.month:02d}/{p}{day_hour.year:04d}{day_hour.month:02d}{day_hour.day:02d}_{day_hour.hour:02d}"
                            paginator = client.get_paginator("list_objects")

                            operation_parameters = {"Bucket": bucket, "Prefix": prefix}
                            page_iterator = paginator.paginate(**operation_parameters)
                            self.log.info(
                                f"{self.log_prefix} Searching in bucket: {bucket} prefixes: {self.prefixes}"
                            )

                            # list the objects in the bucket
                            # loop through the objects and check if they match the search pattern
                            for page in page_iterator:
                                if "Contents" not in page:
                                    self.log.info(
                                        f"{self.log_prefix}  No data found in {bucket}"
                                    )
                                    break

                                for obj in page["Contents"]:
                                    key = obj["Key"]
                                    f_dt = get_datetime(
                                        f"s3://{bucket}/{key}", self.prefixes
                                    )
                                    if f_dt is None:
                                        continue
                                    if start_dt <= f_dt <= end_dt:
                                        self.log.info(
                                            f"Found {f's3://{bucket}/{key}'} with timestamp {f_dt}"
                                        )
                                        if key.endswith(".flac"):
                                            sound_files.append(
                                                FlacFile(
                                                    self.log, f"s3://{bucket}/{key}", f_dt
                                                )
                                            )
                                        if key.endswith(".wav"):
                                            sound_files.append(
                                                GenericWavFile(
                                                    self.log, f"s3://{bucket}/{key}", f_dt
                                                )
                                            )

                self.log.debug(
                    f"{self.log_prefix} Found {len(sound_files)} files to process that "
                    f"cover the expanded period {start_dt} - {end_dt}"
                )

                if len(sound_files) == 0:
                    self.log.info(
                        f"{self.log_prefix}  No files found to process that "
                        f"cover the period {start_dt} - {end_dt}"
                    )
                    return

                # sort the files by start time
                sound_files.sort(key=lambda x: x.start)

                # create a dataframe from the wav files
                self.log.debug(
                    f"{self.log_prefix} creating dataframe from {len(sound_files)} files "
                    f"spanning {sound_files[0].start} to {sound_files[-1].start}..."
                )

                for wc in sound_files:
                    df_wav = wc.to_df()

                    # concatenate the metadata to the dataframe
                    self.df = pd.concat([self.df, df_wav], axis=0)

                self.log.debug(f"{self.log_prefix}  Running metadata json_gen for {day}")
                json_gen = JsonGenerator(
                    self.log,
                    self.df,
                    self.json_base_dir,
                    day,
                    InstrumentType.ICLISTEN,
                    True,
                    self.seconds_per_file,
                )
                json_gen.run()

            except Exception as ex:
                self.log.exception(str(ex))

        # plot the daily coverage only on files that are greater than the start date
        # this is to avoid plotting any coverage on files only included for overlap
        plot_file = plot_daily_coverage(
            InstrumentType.ICLISTEN,
            self.df[self.df["start"] >= self.start],
            self.json_base_dir,
            self.start,
            self.end,
        )
        self.log.info(f"Coverage plot saved to {plot_file}")


if __name__ == "__main__":
    from pbp.logging_helper import create_logger

    log_dir = Path("tests/log")
    json_dir = Path("tests/json/mars")
    log_dir.mkdir(exist_ok=True, parents=True)
    json_dir.mkdir(exist_ok=True, parents=True)

    log = create_logger(
        log_filename_and_level=(
            f"{log_dir}/test_iclisten_metadata_generator.log",
            "INFO",
        ),
        console_level="INFO",
    )

    start = datetime(2023, 7, 18, 0, 0, 0)
    end = datetime(2023, 7, 18, 0, 0, 0)

    # If only running one day, use a single generator
    generator = IcListenMetadataGenerator(
        log,
        uri="s3://pacific-sound-256khz",
        json_base_dir=json_dir.as_posix(),
        prefixes=["MARS_"],
        start=start,
        end=end,
        seconds_per_file=600,
    )
    generator.run()
