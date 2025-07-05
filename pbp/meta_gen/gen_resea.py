# pbp, Apache License 2.0
# Filename: metadata/generator/gen_resea.py
# Description:  Captures RESEA wav metadata in a pandas dataframe from either a local directory or S3 bucket.
from datetime import timedelta
from datetime import datetime
from typing import List
from urllib.parse import urlparse

import boto3
from botocore import UNSIGNED
from botocore.client import Config

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
from pbp.meta_gen.meta_reader import GenericWavFile
from pbp.meta_gen.gen_abstract import MetadataGeneratorAbstract


class ReseaMetadataGenerator(MetadataGeneratorAbstract):
    log_prefix = None

    def __init__(
        self,
        log,  # : loguru.Logger,
        uri: str,
        json_base_dir: str,
        start: datetime,
        end: datetime,
        prefixes: List[str],
        seconds_per_file: float = 600.0,
    ):
        """
        Captures RTSys wav metadata in a pandas dataframe from either a local directory or S3 bucket.
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

        # gs is not supported for RTSys
        if scheme == "gs":
            self.log.error(f"{self.log_prefix} GS is not supported for RTSys audio files")
            return

        # Run for each day in the range
        self.df = None
        for day in pd.date_range(self.start, self.end, freq="D"):
            try:
                for s in self.prefixes:
                    self.log.info(
                        f"{self.log_prefix} Searching in {self.audio_loc}/*.wav "
                        f"for wav files that match the search patterns {s}* ..."
                    )

                wav_files = []

                # Set the start and end dates to 1 hour before and after the start and end dates
                start_dt = day - timedelta(hours=1)
                end_dt = day + timedelta(days=1)

                if scheme == "file":
                    wav_path = Path(urlparse(self.audio_loc).path)
                    for filename in progressbar(
                        sorted(wav_path.rglob("*.wav")), prefix="Searching : "
                    ):
                        wav_dt = get_datetime(filename, self.prefixes)

                        if wav_dt and start_dt <= wav_dt <= end_dt:
                            self.log.info(
                                f"Found file {filename} with timestamp {wav_dt}"
                            )
                            wav_files.append(
                                GenericWavFile(self.log, str(filename), wav_dt)
                            )

                elif scheme == "s3":
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
                                    wav_dt = get_datetime(
                                        f"s3://{bucket}/{key}", self.prefixes
                                    )
                                    if wav_dt is None:
                                        continue
                                    if start_dt <= wav_dt <= end_dt:
                                        self.log.info(
                                            f'Found {f"s3://{bucket}/{key}"} with timestamp {wav_dt}'
                                        )
                                        wav_files.append(
                                            GenericWavFile(
                                                self.log, f"s3://{bucket}/{key}", wav_dt
                                            )
                                        )

                self.log.debug(
                    f"{self.log_prefix} Found {len(wav_files)} files to process that "
                    f"cover the expanded period {start_dt} - {end_dt}"
                )

                if len(wav_files) == 0:
                    self.log.info(
                        f"{self.log_prefix}  No files found to process that "
                        f"cover the period {start_dt} - {end_dt}"
                    )
                    return

                # sort the files by start times
                wav_files.sort(key=lambda x: x.start, reverse=False)

                # create a dataframe from the wav files
                self.log.debug(
                    f"{self.log_prefix} creating dataframe from {len(wav_files)} files "
                    f"spanning {wav_files[0].start} to {wav_files[-1].start}..."
                )

                for wc in wav_files:
                    df_wav = wc.to_df()

                    # concatenate the metadata to the dataframe
                    self.df = pd.concat([self.df, df_wav], axis=0)

                self.df = self.df.sort_values(by=["start"])

                self.log.debug(f"{self.log_prefix}  Running metadata json_gen for {day}")
                json_gen = JsonGenerator(
                    self.log,
                    self.df,
                    self.json_base_dir,
                    day,
                    InstrumentType.RESEA,
                    True,
                    self.seconds_per_file,
                )
                json_gen.run()

            except Exception as ex:
                self.log.exception(str(ex))

        # plot the daily coverage only on files that are greater than the start date
        # this is to avoid plotting any coverage on files only included for overlap
        plot_file = plot_daily_coverage(
            InstrumentType.RESEA,
            self.df[self.df["start"] >= self.start],
            self.json_base_dir,
            self.start,
            self.end,
        )
        self.log.info(f"Coverage plot saved to {plot_file}")
