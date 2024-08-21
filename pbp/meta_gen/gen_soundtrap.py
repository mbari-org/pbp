# pbp, Apache License 2.0
# Filename: meta_gen/gen_soundtrap.py
# Description:  Captures SoundTrap metadata either from a local directory of S3 bucket
import urllib
from typing import List

import boto3
from botocore import UNSIGNED
from botocore.client import Config
import datetime
import pandas as pd
import pytz

from datetime import timedelta
from pathlib import Path
from progressbar import progressbar

from pbp.meta_gen.gen_abstract import MetadataGeneratorAbstract
from pbp.meta_gen.meta_reader import SoundTrapWavFile
from pbp.meta_gen.json_generator import JsonGenerator
from pbp.meta_gen.utils import (
    parse_s3_or_gcp_url,
    InstrumentType,
    get_datetime,
    plot_daily_coverage,
)


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
        prefixes: List[str],
        start: datetime.datetime = START,
        end: datetime.datetime = END,
    ):
        """
        :param uri:
            The local directory or S3 bucket that contains the wav files
        :param json_base_dir:
            The local directory to write the json files to
        :param prefixes:
            The search pattern to match the wav files, e.g. 'MARS'
        :param start:
            The start date to search for wav files
        :param end:
            The end date to search for wav files check is done.
        :return:
        """
        super().__init__(log, uri, json_base_dir, prefixes, start, end, 0.0)

    def run(self):
        try:
            xml_cache_path = Path(self.json_base_dir) / "xml_cache"
            xml_cache_path.mkdir(exist_ok=True, parents=True)
            wav_files = []

            self.log.info(
                f"Searching in {self.audio_loc}/*.wav for wav files that match the prefixes {self.prefixes}* ..."
            )

            bucket, prefix, scheme = parse_s3_or_gcp_url(self.audio_loc)
            # This does not work for GCS
            if scheme == "gs":
                self.log.error("GS not supported for SoundTrap")
                return

            # Set the start and end dates to 1 day before and after the start and end dates
            start_dt = self.start - timedelta(days=1)
            end_dt = self.end + timedelta(days=1)

            if scheme == "file":
                parsed_uri = urllib.parse.urlparse(self.audio_loc)
                wav_path = Path(parsed_uri.path)
                for filename in progressbar(
                    sorted(wav_path.rglob("*.wav")), prefix="Searching : "
                ):
                    wav_path = filename.parent / f"{filename.stem}.wav"
                    xml_path = filename.parent / f"{filename.stem}.xml"
                    start_dt = get_datetime(wav_path, self.prefixes)
                    # Must have a start date to be valid and also must have a corresponding xml file
                    if start_dt and xml_path.exists() and start_dt <= start_dt <= end_dt:
                        wav_files.append(
                            SoundTrapWavFile(wav_path.as_posix(), xml_path, start_dt)
                        )
            else:
                # if the audio_loc is a s3 url, then we need to list the files in buckets that cover the start and end
                # dates
                self.log.info(f"Searching between {start_dt} and {end_dt}")

                client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
                paginator = client.get_paginator("list_objects")

                operation_parameters = {"Bucket": bucket}
                page_iterator = paginator.paginate(**operation_parameters)
                self.log.info(
                    f"Searching in bucket: {bucket} for .wav and .xml files between {start_dt} and {end_dt}"
                )

                # list the objects in the bucket
                # loop through the objects and check if they match the search pattern
                for page in page_iterator:
                    for obj in page["Contents"]:
                        key = obj["Key"]
                        uri = f"s3://{bucket}/{key}"
                        key_dt = get_datetime(uri, self.prefixes)
                        xml_path = xml_cache_path / key
                        xml_path = xml_path.with_suffix(".xml")
                        key_xml = key.replace(".wav", ".log.xml")

                        if key_dt is None:
                            continue
                        if start_dt <= key_dt <= end_dt and key.endswith(".wav"):
                            # download the associated xml file to the wav file and create a SoundTrapWavFile object
                            try:
                                self.log.info(f"Downloading {key_xml} ...")
                                client.download_file(bucket, key_xml, xml_path)
                                wav_files.append(SoundTrapWavFile(uri, xml_path, key_dt))
                            except Exception as ex:
                                self.log.error(
                                    f"Could not download {key_xml} - {str(ex)}"
                                )
                                continue

            self.log.info(
                f"Found {len(wav_files)} files to process that cover the expanded period {start_dt} - {end_dt}"
            )

            if len(wav_files) == 0:
                return

            # sort the files by start time
            wav_files.sort(key=lambda x: x.start)

            # create a dataframe from the wav files
            self.log.info(
                f"Creating dataframe from {len(wav_files)} files spanning "
                f"{wav_files[0].start} to {wav_files[-1].start}..."
            )
            for wc in wav_files:
                df_wav = wc.to_df()

                # concatenate the metadata to the dataframe
                self.df = pd.concat([self.df, df_wav], axis=0)

            # drop any rows with duplicate uris - sometimes the same file is found in multiple searches
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
                self.log.debug(f"Running metadata json_gen for {day}")
                json_gen = JsonGenerator(
                    self.log,
                    self.df,
                    self.json_base_dir,
                    self.start + timedelta(days=day),
                    InstrumentType.SOUNDTRAP,
                    False,
                )
                json_gen.run()

            # plot the daily coverage
            plot_file = plot_daily_coverage(
                InstrumentType.SOUNDTRAP,
                self.df,
                self.json_base_dir,
                self.start,
                self.end,
            )
            self.log.info(f"Coverage plot saved to {plot_file}")


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
