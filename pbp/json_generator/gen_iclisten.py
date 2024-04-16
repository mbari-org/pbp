# pypam-based-processing, Apache License 2.0
# Filename: metadata/generator/gen_iclisten.py
# Description:  Captures ICListen wav metadata in a pandas dataframe from either a local directory or S3 bucket.

import re
from datetime import timedelta
from datetime import datetime
from typing import List

import boto3

import pandas as pd
from pathlib import Path
from progressbar import progressbar
import pbp.json_generator.utils as utils
from pbp.json_generator.corrector import MetadataCorrector
from pbp.json_generator.metadata_extractor import IcListenWavFile
from pbp.json_generator.gen_abstract import MetadataGeneratorAbstract


class IcListenMetadataGenerator(MetadataGeneratorAbstract):
    log_prefix = None

    def __init__(
        self,
        uri: str,
        json_base_dir: str,
        start: datetime,
        end: datetime,
        prefix: List[str],
        seconds_per_file: float = 300.0,
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
        :param prefix:
            The search pattern to match the wav files, e.g. 'MARS' for MARS_YYYYMMDD_HHMMSS.wav
        :param seconds_per_file:
            The number of seconds per file expected in a wav file to check for missing data. If 0, then no check is done.
        :return:
        """
        super().__init__(uri, json_base_dir, prefix, start, end, seconds_per_file)
        self.log_prefix = f"{self.__class__.__name__} {start:%Y%m%d}"

    def run(self):
        log.info(f"Generating metadata for {self.start} to {self.end}...")

        bucket_name, prefix, scheme = utils.parse_s3_or_gcp_url(self.audio_loc)

        # gs is not supported for icListen
        if scheme == "gs":
            log.error(f"{self.log_prefix} GS is not supported for icListen audio files")
            return

        # Run for each day in the range
        for day in pd.date_range(self.start, self.end, freq="D"):
            try:
                self.df = None
                log.info(
                    f"{self.log_prefix} Searching in {self.audio_loc}/*.wav for wav files that match the search pattern {self.prefix}* ..."
                )

                wav_files = []

                def check_file(f: str, f_start_dt: datetime, f_end_dt: datetime):
                    """
                    Check if the file matches the search pattern and is within the start and end dates
                    :param f:
                        The path to the file
                    :param f_start_dt:
                        The start date to check
                    :param f_end_dt:
                        The end date to check
                    :return:
                    """

                    f_path = Path(f)
                    f_wav_dt = None

                    for s in self.prefix:
                        # see if the file is a regexp match to search
                        rc = re.search(s, f_path.stem)

                        if rc and rc.group(0):
                            try:
                                # MARS file date is in the filename MARS_YYYYMMDD_HHMMSS.wav
                                f_path_dt = datetime.strptime(
                                    f_path.stem, f"{s}_%Y%m%d_%H%M%S"
                                )

                                if f_start_dt <= f_path_dt <= f_end_dt:
                                    log.info(
                                        f"{self.log_prefix} Found {f_path.name} to process"
                                    )
                                    wav_files.append(IcListenWavFile(f, f_path_dt))
                                    f_wav_dt = f_path_dt
                            except ValueError:
                                log.error(
                                    f"{self.log_prefix} Could not parse {f_path.name}"
                                )
                                return None

                    return f_wav_dt

                # Set the start and end dates to 30 minutes before and after the start and end dates
                start_dt = day - timedelta(hours=1)
                end_dt = day + timedelta(days=1)

                # set the window to 3x the expected duration of the wav file to account for any missing data
                minutes_window = int(self.seconds_per_file * 3 / 60)
                start_dt_hour = start_dt - timedelta(minutes=minutes_window)
                end_dt_hour = end_dt + timedelta(minutes=minutes_window)

                if scheme == "file":
                    wav_path = Path(self.audio_loc)
                    for filename in progressbar(
                        sorted(wav_path.rglob("*.wav")), prefix="Searching : "
                    ):
                        check_file(filename.as_posix(), start_dt, end_dt)
                if scheme == "s3":
                    client = boto3.client("s3")
                    for day_hour in pd.date_range(start=start_dt, end=end_dt, freq="h"):
                        bucket = f"{bucket_name}-{day_hour.year:04d}"
                        prefix = f"{day_hour.month:02d}/MARS_{day_hour.year:04d}{day_hour.month:02d}{day_hour.day:02d}_{day_hour.hour:02d}"
                        paginator = client.get_paginator("list_objects")

                        operation_parameters = {"Bucket": bucket, "Prefix": prefix}
                        page_iterator = paginator.paginate(**operation_parameters)
                        log.info(
                            f"{self.log_prefix}  Searching in bucket: {bucket} prefix: {prefix}"
                        )
                        # list the objects in the bucket
                        # loop through the objects and check if they match the search pattern
                        for page in page_iterator:
                            if "Contents" not in page:
                                log.info(f"{self.log_prefix}  No data found in {bucket}")
                                break

                            for obj in page["Contents"]:
                                key = obj["Key"]
                                wav_dt = check_file(
                                    f"s3://{bucket}/{key}", start_dt, end_dt
                                )
                                if wav_dt is None:
                                    continue
                                if wav_dt > end_dt_hour:
                                    break
                                if wav_dt < start_dt_hour:
                                    break

                log.info(
                    f"{self.log_prefix}  Found {len(wav_files)} files to process that cover the period {start_dt} - {end_dt}"
                )

                # sort the files by start time
                wav_files.sort(key=lambda x: x.start)

                # create a dataframe from the wav files
                log.info(
                    f"{self.log_prefix}  Creating dataframe from {len(wav_files)} files spanning {wav_files[0].start} to {wav_files[-1].start}..."
                )
                for wc in wav_files:
                    df_wav = wc.to_df()

                    # concatenate the metadata to the dataframe
                    self.df = pd.concat([self.df, df_wav], axis=0)

                log.debug(f"{self.log_prefix}  Running metadata corrector for {day}")
                corrector = MetadataCorrector(
                    self.df, self.json_base_dir, day, False, 600.0
                )
                corrector.run()

            except Exception as ex:
                log.exception(str(ex))


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
        uri="s3://pacific-sound-256khz",
        json_base_dir=json_dir.as_posix(),
        prefix=["MARS"],
        start=start,
        end=end,
        seconds_per_file=300,
    )
    generator.run()
