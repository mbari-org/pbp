# pbp, Apache License 2.0
# Filename: metadata/generator/gen_nrs.py
# Description:  Captures NRS recorded metadata in a pandas dataframe from either a local directory or gs bucket.

import re
from datetime import timedelta, datetime
import time
from typing import List
import loguru

from google.cloud import storage

import pandas as pd
from pathlib import Path
from progressbar import progressbar

from pbp.meta_gen import utils
from pbp.meta_gen.json_generator import JsonGenerator
from pbp.meta_gen.meta_reader import FlacFile, GenericWavFile as WavFile
from pbp.meta_gen.gen_abstract import MetadataGeneratorAbstract
from pbp.meta_gen.utils import parse_s3_or_gcp_url, InstrumentType, plot_daily_coverage


class NRSMetadataGenerator(MetadataGeneratorAbstract):
    def __init__(
        self,
        log: "loguru.Logger",
        uri: str,
        json_base_dir: str,
        start: datetime,
        end: datetime,
        prefixes: List[str],
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
        :param prefixes:
            The search pattern to match the flac files, e.g. 'MARS_' for MARS_YYYYMMDD_HHMMSS.flac
        :param seconds_per_file:
            The number of seconds per file expected in a flac/wav file to check for missing data. If 0, then no check is done.
        :return:
        """
        super().__init__(log, uri, json_base_dir, prefixes, start, end, seconds_per_file)

    def run(self):
        self.log.info(f"Generating metadata for {self.start} to {self.end}...")

        bucket, prefix, scheme = parse_s3_or_gcp_url(self.audio_loc)

        # S3 is not supported for NRS
        if scheme == "s3":
            self.log.error("S3 is not supported for NRS audio files")
            return

        sound_files = []
        self.df = None
        self.log.info(
            f"Searching in {self.audio_loc}/ for files that match the search pattern {self.prefixes}* ..."
        )

        # set the window to 1 flac file to account for any missing data
        minutes_window = int(self.seconds_per_file / 60)

        # pad the start and end dates to account for any missing data
        start_dt = self.start - timedelta(minutes=minutes_window)
        end_dt = self.end + timedelta(days=1)

        if scheme == "file" or scheme == "":
            sound_path = Path(f"/{bucket}/{prefix}")
            file_extensions = ["*.flac", "*.wav"]
            for ext in file_extensions:
                for filename in progressbar(
                    sorted(sound_path.rglob(ext)), prefix="Searching : "
                ):
                    f_dt = utils.get_datetime(filename, self.prefixes)
                    if f_dt is None:
                        continue
                    if start_dt <= f_dt <= end_dt:
                        self.log.debug(f"Found file {filename} with timestamp {f_dt}")
                        if ext == "*.flac":
                            sound_files.append(FlacFile(self.log, str(filename), f_dt))
                        if ext == "*.wav":
                            sound_files.append(WavFile(self.log, str(filename), f_dt))

        if scheme == "gs":
            client = storage.Client.create_anonymous_client()
            bucket_obj = client.get_bucket(bucket)

            # get list of files - this is a generator
            # data is organized in a flat filesystem, so there are no optimizations here for querying
            blobs = bucket_obj.list_blobs(prefix=prefix)
            for i, blob in enumerate(blobs):
                f_path = f"gs://{bucket}/{blob.name}"
                f_dt = utils.get_datetime(f_path, self.prefixes)
                if f_dt is None:
                    continue
                if start_dt <= f_dt <= end_dt:
                    self.log.debug(f"Found file {blob.name} with timestamp {f_dt}")
                    if re.search(r"\.flac$", blob.name):
                        sound_files.append(FlacFile(self.log, f_path, f_dt))
                    if re.search(r"\.wav$", blob.name):
                        sound_files.append(WavFile(self.log, f_path, f_dt))
                # delay to avoid 400 error
                if i % 100 == 0 and i > 0:
                    self.log.info(
                        f"{i} files searched...found {len(sound_files)} files that match the search pattern"
                    )
                    time.sleep(1)
                if f_dt > end_dt:
                    break

        self.log.info(
            f"Found {len(sound_files)} files to process that cover the expanded period {start_dt} - {end_dt}"
        )

        if len(sound_files) == 0:
            return

        # sort the files by start time
        sound_files.sort(key=lambda x: x.start)
        for wc in sound_files:
            df_flac = wc.to_df()

            # concatenate the metadata to the dataframe
            self.df = pd.concat([self.df, df_flac], axis=0)

        # correct each day in the range
        for day in pd.date_range(self.start, self.end, freq="D"):
            try:
                # create a dataframe from the flac files
                self.log.debug(
                    f"Creating dataframe from {len(sound_files)} "
                    f"files spanning {sound_files[0].start} to {sound_files[-1].start} in self.json_base_dir..."
                )

                self.log.debug(f" Running metadata json_gen for {day}")
                json_gen = JsonGenerator(
                    self.log,
                    self.df,
                    self.json_base_dir,
                    day,
                    InstrumentType.NRS,
                    False,
                    self.seconds_per_file,
                )
                json_gen.run()

            except Exception as ex:
                self.log.exception(str(ex))

        # plot the daily coverage only on files that are greater than the start date
        # this is to avoid plotting any coverage on files only included for overlap
        plot_file = plot_daily_coverage(
            InstrumentType.NRS,
            self.df[self.df["start"] >= self.start],
            self.json_base_dir,
            self.start,
            self.end,
        )
        self.log.info(f"Coverage plot saved to {plot_file}")


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
        log,
        uri="gs://noaa-passive-bioacoustic/nrs/audio/11/nrs_11_2019-2021/audio",
        json_base_dir=json_dir.as_posix(),
        prefixes=["NRS11"],
        start=start,
        end=end,
    )
    generator.run()
