# pypam-based-processing, Apache License 2.0
# Filename: metadata/generator/gen_nrs.py
# Description:  Captures NRS flac metadata in a pandas dataframe from either a local directory or gs bucket.

import re
from datetime import timedelta, datetime
import time
from typing import List

from loguru import logger as log
from google.cloud import storage

import pandas as pd
from pathlib import Path
from progressbar import progressbar
from pbp.json_generator.corrector import MetadataCorrector
from pbp.json_generator.metadata_extractor import FlacFile
from pbp.json_generator.gen_abstract import MetadataGeneratorAbstract
from pbp.json_generator.utils import parse_s3_or_gcp_url


class NRSMetadataGenerator(MetadataGeneratorAbstract):
    def __init__(
        self,
        uri: str,
        json_base_dir: str,
        start: datetime,
        end: datetime,
        prefix: List[str],
        seconds_per_file: float = 14400.0,
    ):
        """
        Captures NRS audio metadata in a pandas dataframe from either a local directory or GS bucket.
        :param uri:
            The local directory or GCP bucket that contains the audio files
        :param json_base_dir:
            The local directory to store the metadata
        :param start:
            The start date to search for flac files
        :param end:
            The end date to search for flac files
        :param prefix:
            The search pattern to match the flac files, e.g. 'MARS' for MARS_YYYYMMDD_HHMMSS.flac
        :param seconds_per_file:
            The number of seconds per file expected in a flac file to check for missing data. If 0, then no check is done.
        :return:
        """
        super().__init__(uri, json_base_dir, prefix, start, end, seconds_per_file)

    def run(self):
        log.info(f"Generating metadata for {self.start} to {self.end}...")

        bucket, prefix, scheme = parse_s3_or_gcp_url(self.audio_loc)

        # S3 is not supported for NRS
        if scheme == "s3":
            log.error("S3 is not supported for NRS audio files")
            return

        def parse_filename(f: str) -> datetime:
            """
            Check if the file matches the search pattern and is within the start and end dates
            :param f:
                The path to the file
            :return: The beginning recording time of the file
            """
            f_path = Path(f)
            f_flac_dt = None

            for s in self.prefix:
                # see if the file is a regexp match to search
                rc = re.search(s, f_path.stem)

                if rc and rc.group(0):
                    try:
                        # files are in the format NRS11_20191231_230836.flac'
                        # extract the timestamp from the file name into the format YYYYMMDDHHMMSS
                        f_parts = f_path.stem.split("_")
                        # If the last two digits of the timestamp are 60, subtract 1 second
                        if f_parts[2][-2:] == "60":
                            f_parts = f_parts[1] + f_parts[2]
                            # Make the last two digits 59
                            f_parts = f_parts[:-2] + "59"
                        else:
                            f_parts = f_parts[1] + f_parts[2]

                        f_path_dt = datetime.strptime(f_parts, "%Y%m%d%H%M%S")
                        return f_path_dt
                    except ValueError:
                        log.error(f"Could not parse {f_path.name}")
                        return None

            return f_flac_dt

        flac_files = []
        self.df = None
        log.info(
            f"Searching in {self.audio_loc}/ for files that match the search pattern {self.prefix}* ..."
        )

        # set the window to 1 flac file to account for any missing data
        minutes_window = int(self.seconds_per_file / 60)

        # set the start and end dates to 1 hour before and after the start and end dates
        start_dt = (
            self.start
            - timedelta(minutes=minutes_window)
            - timedelta(minutes=minutes_window)
        )
        end_dt = self.end + timedelta(days=1)

        if scheme == "file" or scheme == "":
            flac_path = Path(f"/{bucket}/{prefix}")
            for filename in progressbar(
                sorted(flac_path.rglob("*.flac")), prefix="Searching : "
            ):
                flac_dt = parse_filename(filename)
                if start_dt <= flac_dt <= end_dt:
                    log.info(f"Found file {filename} with timestamp {flac_dt}")
                    flac_files.append(FlacFile(filename, flac_dt))
        if scheme == "gs":
            client = storage.Client.create_anonymous_client()
            bucket_obj = client.get_bucket(bucket)

            # get list of files - this is a generator
            # data is organized in a flat filesystem, so there are no optimizations here for querying
            blobs = bucket_obj.list_blobs(prefix=prefix)
            for i, blob in enumerate(blobs):
                log.info(f"Processing {blob.name}")
                f_path = f"gs://{bucket}/{blob.name}"
                flac_dt = parse_filename(f_path)
                if start_dt <= flac_dt <= end_dt:
                    log.info(f"Found file {blob.name} with timestamp {flac_dt}")
                    flac_files.append(FlacFile(f_path, flac_dt))
                # delay to avoid 400 error
                if i % 100 == 0:
                    log.info(f"{i} files processed")
                    time.sleep(1)
                if flac_dt > end_dt:
                    break

        log.info(
            f"Found {len(flac_files)} files to process that cover the period {start_dt} - {end_dt}"
        )

        if len(flac_files) == 0:
            return

        # sort the files by start time
        flac_files.sort(key=lambda x: x.start)
        for wc in flac_files:
            df_flac = wc.to_df()

            # concatenate the metadata to the dataframe
            self.df = pd.concat([self.df, df_flac], axis=0)

        # correct each day in the range
        for day in pd.date_range(self.start, self.end, freq="D"):
            try:
                # create a dataframe from the flac files
                log.info(
                    f"Creating dataframe from {len(flac_files)} "
                    f"files spanning {flac_files[0].start} to {flac_files[-1].start} in self.json_base_dir..."
                )

                log.debug(f" Running metadata corrector for {day}")
                corrector = MetadataCorrector(
                    self.df,
                    self.json_base_dir,
                    day,
                    False,
                    self.seconds_per_file,
                )
                corrector.run()

            except Exception as ex:
                log.exception(str(ex))


if __name__ == "__main__":
    from pbp.logging_helper import create_logger

    log_dir = Path("tests/log")
    json_dir = Path("tests/json/nrs")
    log_dir.mkdir(exist_ok=True, parents=True)
    json_dir.mkdir(exist_ok=True, parents=True)

    log = create_logger(
        log_filename_and_level=(
            f"{log_dir}/test_nrs_metadata_generator.log",
            "INFO",
        ),
        console_level="INFO",
    )

    start = datetime(2019, 10, 24, 0, 0, 0)
    end = datetime(2019, 11, 1, 0, 0, 0)

    generator = NRSMetadataGenerator(
        uri="gs://noaa-passive-bioacoustic/nrs/audio/11/nrs_11_2019-2021/audio",
        json_base_dir=json_dir.as_posix(),
        prefix=["NRS11"],
        start=start,
        end=end,
    )
    generator.run()
