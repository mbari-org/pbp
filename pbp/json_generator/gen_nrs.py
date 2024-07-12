# pbp, Apache License 2.0
# Filename: metadata/generator/gen_nrs.py
# Description:  Captures NRS recorded metadata in a pandas dataframe from either a local directory or gs bucket.

import re
from datetime import timedelta, datetime
import time
from typing import List

from google.cloud import storage

import pandas as pd
from pathlib import Path
from progressbar import progressbar
from pbp.json_generator.corrector import MetadataCorrector
from pbp.json_generator.metadata_extractor import FlacFile, GenericWavFile as WavFile
from pbp.json_generator.gen_abstract import MetadataGeneratorAbstract
from pbp.json_generator.utils import parse_s3_or_gcp_url, InstrumentType


class NRSMetadataGenerator(MetadataGeneratorAbstract):
    def __init__(
        self,
        log,  # : loguru.Logger,
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
            The number of seconds per file expected in a flac/wav file to check for missing data. If 0, then no check is done.
        :return:
        """
        super().__init__(log, uri, json_base_dir, prefix, start, end, seconds_per_file)

    def run(self):
        self.log.info(f"Generating metadata for {self.start} to {self.end}...")

        bucket, prefix, scheme = parse_s3_or_gcp_url(self.audio_loc)

        # S3 is not supported for NRS
        if scheme == "s3":
            self.log.error("S3 is not supported for NRS audio files")
            return

        def parse_filename(f: str) -> datetime or None:
            """
            Check if the file matches the search pattern and is within the start and end dates
            :param f:
                The path to the file
            :return: The beginning recording time of the file
            """
            f_path = Path(f)
            f_path_dt = None

            for s in self.prefix:
                # see if the file is a regexp match to search
                rc = re.search(s, f_path.stem)

                if rc and rc.group(0):
                    try:
                        pattern_date = re.compile(
                            r"(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})"
                        )  # 20191231_230836
                        search = pattern_date.search(f_path.stem)
                        if search:
                            match = search.groups()
                            year, month, day, hour, minute, second = map(int, match)
                            if second == 60:  # this is a bug in the flac files names
                                second = 59
                            f_path_dt = datetime(year, month, day, hour, minute, second)
                            return f_path_dt
                        else:
                            self.log.error(f"Could not parse {f_path.name}")
                            return None
                    except ValueError:
                        self.log.error(f"Could not parse {f_path.name}")
                        return None

            return f_path_dt

        sound_files = []
        self.df = None
        self.log.info(
            f"Searching in {self.audio_loc}/ for files that match the search pattern {self.prefix}* ..."
        )

        # set the window to 1 flac file to account for any missing data
        minutes_window = int(self.seconds_per_file / 60)

        # pad the start and end dates to account for any missing data
        start_dt = self.start - timedelta(minutes=minutes_window)
        end_dt = self.end + timedelta(days=1)

        if scheme == "file" or scheme == "":
            sound_path = Path(f"/{bucket}/{prefix}")
            # First search for flac files
            for filename in progressbar(
                sorted(sound_path.rglob("*.flac")), prefix="Searching : "
            ):
                flac_dt = parse_filename(filename)
                if start_dt <= flac_dt <= end_dt:
                    self.log.info(f"Found file {filename} with timestamp {flac_dt}")
                    sound_files.append(FlacFile(self.log, str(filename), flac_dt))
            # Next search for wav files
            for filename in progressbar(
                sorted(sound_path.rglob("*.wav")), prefix="Searching : "
            ):
                wav_dt = parse_filename(filename)
                if start_dt <= wav_dt <= end_dt:
                    self.log.info(f"Found file {filename} with timestamp {wav_dt}")
                    sound_files.append(WavFile(self.log, str(filename), wav_dt))

        if scheme == "gs":
            client = storage.Client.create_anonymous_client()
            bucket_obj = client.get_bucket(bucket)

            # get list of files - this is a generator
            # data is organized in a flat filesystem, so there are no optimizations here for querying
            blobs = bucket_obj.list_blobs(prefix=prefix)
            for i, blob in enumerate(blobs):
                self.log.info(f"Processing {blob.name}")
                f_path = f"gs://{bucket}/{blob.name}"
                f_dt = parse_filename(f_path)
                if start_dt <= f_dt <= end_dt:
                    self.log.info(f"Found file {blob.name} with timestamp {f_dt}")
                    sound_files.append(FlacFile(self.log, f_path, f_dt))
                # delay to avoid 400 error
                if i % 100 == 0:
                    self.log.info(f"{i} files processed")
                    time.sleep(1)
                if f_dt > end_dt:
                    break

        self.log.info(
            f"Found {len(sound_files)} files to process that cover the period {start_dt} - {end_dt}"
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
                self.log.info(
                    f"Creating dataframe from {len(sound_files)} "
                    f"files spanning {sound_files[0].start} to {sound_files[-1].start} in self.json_base_dir..."
                )

                self.log.debug(f" Running metadata corrector for {day}")
                corrector = MetadataCorrector(
                    self.log,
                    self.df,
                    self.json_base_dir,
                    day,
                    InstrumentType.NRS,
                    False,
                    self.seconds_per_file,
                )
                corrector.run()

            except Exception as ex:
                self.log.exception(str(ex))


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
        prefix=["NRS11"],
        start=start,
        end=end,
    )
    generator.run()
