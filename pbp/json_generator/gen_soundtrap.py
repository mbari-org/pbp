# pbp, Apache License 2.0
# Filename: json_generator/gen_soundtrap.py
# Description:  Captures SoundTrap metadata either from a local directory of S3 bucket
import urllib
from typing import List

import boto3
import datetime
import pandas as pd
import re
import pytz

from datetime import timedelta
from pathlib import Path

from progressbar import progressbar

from pbp.json_generator.gen_abstract import MetadataGeneratorAbstract
from pbp.json_generator.metadata_extractor import SoundTrapWavFile
from pbp.json_generator.corrector import MetadataCorrector
from pbp.json_generator.utils import parse_s3_or_gcp_url, InstrumentType


class SoundTrapMetadataGenerator(MetadataGeneratorAbstract):
    """
    Captures SoundTrap wav file metadata either from a local directory or S3 bucket.
    """

    START = datetime.datetime.now(pytz.utc)
    END = datetime.datetime.now(pytz.utc)

    def __init__(
        self,
        log,  # : loguru.Logger,
        uri: str,
        json_base_dir: str,
        prefix: List[str],
        start: datetime.datetime = START,
        end: datetime.datetime = END,
    ):
        """
        :param uri:
            The local directory or S3 bucket that contains the wav files
        :param json_base_dir:
            The local directory to write the json files to
        :param prefix:
            The search pattern to match the wav files, e.g. 'MARS'
        :param start:
            The start date to search for wav files
        :param end:
            The end date to search for wav files check is done.
        :return:
        """
        super().__init__(log, uri, json_base_dir, prefix, start, end, 0.0)

    def run(self):
        try:
            xml_cache_path = Path(self.json_base_dir) / "xml_cache"
            xml_cache_path.mkdir(exist_ok=True, parents=True)
            wav_files = []

            self.log.info(
                f"Searching in {self.audio_loc}/*.wav for wav files that match the prefix {self.prefix}* ..."
            )

            bucket, prefix, scheme = parse_s3_or_gcp_url(self.audio_loc)
            # This does not work for GCS
            if scheme == "gs":
                self.log.error("GS not supported for SoundTrap")
                return

            def get_file_date(xml_file: str) -> datetime:
                """
                Check if the xml file is in the search pattern and is within the start and end dates
                :param xml_file:
                    The xml file with the metadata
                :return:
                    Record starting datetime if the file is within the start and end dates; otherwise, return None
                """
                xml_file_path = Path(xml_file)
                # see if the file is a regexp match to self.prefix
                for s in self.prefix:
                    rc = re.search(s, xml_file_path.stem)

                    if rc and rc.group(0):
                        try:
                            pattern_date1 = re.compile(
                                r"(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})"
                            )  # 20161025T184500Z
                            search = pattern_date1.search(xml_file_path.stem)
                            if search:
                                match = search.groups()
                                year, month, day, hour, minute, second = map(int, match)
                                f_path_dt = datetime.datetime(
                                    year, month, day, hour, minute, second
                                )
                            else:
                                f_path_dt = datetime.datetime.strptime(
                                    xml_file_path.stem.split(".")[1], "%y%m%d%H%M%S"
                                )
                            if self.start <= f_path_dt <= self.end:
                                return f_path_dt
                        except ValueError:
                            self.log.error(f"Could not parse {xml_file_path.name}")
                return None

            if scheme == "file":
                parsed_uri = urllib.parse.urlparse(self.audio_loc)
                wav_path = Path(parsed_uri.path)
                for filename in progressbar(
                    sorted(wav_path.rglob("*.xml")), prefix="Searching : "
                ):
                    wav_path = filename.parent / f"{filename.stem}.wav"
                    start_dt = get_file_date(filename)
                    if start_dt:
                        wav_files.append(
                            SoundTrapWavFile(wav_path.as_posix(), filename, start_dt)
                        )
            else:
                # if the audio_loc is a s3 url, then we need to list the files in buckets that cover the start and end
                # dates
                self.log.info(f"Searching between {self.start} and {self.end}")

                client = boto3.client("s3")
                paginator = client.get_paginator("list_objects")

                operation_parameters = {"Bucket": bucket}
                page_iterator = paginator.paginate(**operation_parameters)
                self.log.info(
                    f"Searching in bucket: {bucket} for .wav and .xml files between {self.start} and {self.end} "
                )
                # list the objects in the bucket
                # loop through the objects and check if they match the search pattern
                for page in page_iterator:
                    for obj in page["Contents"]:
                        key = obj["Key"]

                        if ".xml" in key and get_file_date(key):
                            xml_path = xml_cache_path / key
                            wav_uri = f"s3://{bucket}/{key}".replace(
                                "self.log.xml", "wav"
                            )

                            # Check if the xml file is in the cache directory
                            if not xml_path.exists():
                                # Download the xml file to a temporary directory
                                self.log.info(f"Downloading {key} ...")
                                client.download_file(bucket, key, xml_path)

                            start_dt = get_file_date(wav_uri)
                            if start_dt:
                                wav_files.append(
                                    SoundTrapWavFile(wav_uri, xml_path, start_dt)
                                )

            self.log.info(
                f"Found {len(wav_files)} files to process that cover the period {self.start} - {self.end}"
            )

            if len(wav_files) == 0:
                return

            # sort the files by start time
            wav_files.sort(key=lambda x: x.start)

            # create a dataframe from the wav files
            self.log.info(
                f"Creating dataframe from {len(wav_files)} files spanning {wav_files[0].start} to {wav_files[-1].start}..."
            )
            for wc in wav_files:
                df_wav = wc.to_df()

                # concatenate the metadata to the dataframe
                self.df = pd.concat([self.df, df_wav], axis=0)

            # drop any rows with duplicate uris, keeping the first
            self.df = self.df.drop_duplicates(subset=["uri"], keep="first")

        except Exception as ex:
            self.log.exception(str(ex))
        finally:
            days = (self.end - self.start).days + 1

            if len(self.df) == 0:
                self.log.info(f"No data found between {self.start} and {self.end}")
                return

            # Correct the metadata for each day
            for day in range(days):
                day_start = self.start + timedelta(days=day)
                self.log.debug(f"Running metadata corrector for {day_start}")
                corrector = MetadataCorrector(
                    self.log,
                    self.df,
                    self.json_base_dir,
                    day_start,
                    InstrumentType.NRS,
                    False,
                )
                corrector.run()


if __name__ == "__main__":
    from pbp.logging_helper import create_logger

    log_dir = Path("tests/log")
    json_dir = Path("tests/json/soundtrap")
    log_dir.mkdir(exist_ok=True, parents=True)
    json_dir.mkdir(exist_ok=True, parents=True)

    log = create_logger(
        log_filename_and_level=(
            f"{log_dir}/test_soundtrap_metadata_generator.log",
            "INFO",
        ),
        console_level="INFO",
    )

    start = datetime.datetime(2023, 7, 18)
    end = datetime.datetime(2023, 7, 19)
    gen = SoundTrapMetadataGenerator(
        log, "s3://pacific-sound-ch01", json_dir.as_posix(), ["7000"], start, end
    )
    gen.run()
