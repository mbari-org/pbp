# pypam-based-processing
# Filename: json_generator/gen_soundtrap.py
# Description:  Captures SoundTrap metadata either from a local directory of S3 bucket
import logging

import boto3
import datetime
import pandas as pd
import re
import pytz

from datetime import timedelta, datetime
from pathlib import Path
from progressbar import progressbar

from src import PbpLogger
from src.json_generator.gen_abstract import MetadataGeneratorAbstract
from src.json_generator.wavfile import SoundTrapWavFile
from src.json_generator.corrector import MetadataCorrector


class SoundTrapMetadataGenerator(MetadataGeneratorAbstract):
    """
    Captures SoundTrap wav file metadata either from a local directory or S3 bucket.
    """

    # Set the start and end dates to the current time in UTC
    start = datetime.now(pytz.utc)
    end = datetime.now(pytz.utc)

    log_prefix = None

    def __init__(
            self,
            logger: PbpLogger,
            wav_loc: str,
            json_base_dir: str,
            search: [str],
            start: datetime,
            end: datetime):
        """
        :param logger:
            The logger
        :param wav_loc:
            The local directory or S3 bucket that contains the wav files
        :param json_base_dir:
            The local directory to write the json files to
        :param search:
            The search pattern to match the wav files, e.g. 'MARS'
        :param start:
            The start date to search for wav files
        :param end:
            The end date to search for wav files
        :param seconds_per_file:
            The number of seconds per file expected in a wav file to check for missing data. If missing, then no check is done.
        :return:
        """
        super().__init__(logger, wav_loc, json_base_dir, search, start, end, 0.)

        # Add a prefix to the log messages to differentiate between the different metadata generators running by date
        # This is useful when running multiple metadata generators in parallel
        self.log_prefix = f'{self.__class__.__name__} {self.start:%Y%m%d}'

    def run(self):
        try:
            xml_cache_path = Path(self.json_base_dir) / 'xml_cache'
            xml_cache_path.mkdir(exist_ok=True, parents=True)
            wav_files = []
            bucket_core, is_s3 = self.setup()

            def check_file(xml_file: str) -> bool:
                """
                Check if the xml file is in the cache directory
                :param xml_file:
                    The xml file with the metadata
                :return: 
                    True if the file is within the start and end dates
                """
                wav_files = []
                f_path = Path(xml_file)
                # see if the file is a regexp match to self.search
                for s in self.search:
                    rc = re.search(s, f_path.stem)

                    if rc and rc.group(0):
                        try:
                            # If a SoundTrap file, then the date is in the filename XXXX.YYYYMMDDHHMMSS.xml
                            f_path_dt = datetime.strptime(f_path.stem.split('.')[1], '%y%m%d%H%M%S')
                            if self.start <= f_path_dt <= self.end:
                                return True
                        except ValueError:
                            self.log.error(f'{self.log_prefix} Could not parse {f_path.name}')

            if not is_s3:
                wav_path = Path(self.wav_loc)
                for filename in progressbar(sorted(wav_path.rglob('*.xml')), prefix='Searching : '):
                    wav_path = filename.parent / f'{filename.stem}.wav'
                    if check_file(filename):
                        wav_files.append(SoundTrapWavFile(wav_path, filename))
            else:
                # if the wav_loc is a s3 url, then we need to list the files in buckets that cover the start and end
                # dates
                self.log.info(f'{self.log_prefix} Searching between {self.start} and {self.end}')

                client = boto3.client('s3')

                bucket = f'{bucket_core}'
                paginator = client.get_paginator('list_objects')

                operation_parameters = {'Bucket': bucket}
                page_iterator = paginator.paginate(**operation_parameters)
                self.log.info(
                    f'Searching in bucket: {bucket} for .wav and .xml files between {self.start} and {self.end} ')
                # list the objects in the bucket
                # loop through the objects and check if they match the search pattern
                for page in page_iterator:
                    for obj in page['Contents']:
                        key = obj['Key']

                        if '.xml' in key and check_file(key):
                            xml_path = xml_cache_path / key
                            wav_uri = f's3://{bucket}/{key}'.replace('log.xml', 'wav')

                            # Check if the xml file is in the cache directory
                            if not xml_path.exists():
                                # Download the xml file to a temporary directory
                                self.log.info(f'{self.log_prefix}  Downloading {key} ...')
                                client.download_file(bucket, key, xml_path)
                            wav_files.append(SoundTrapWavFile(wav_uri, xml_path))

            self.log.info(
                f'{self.log_prefix} Found {len(wav_files)} files to process that cover the period {self.start} - {self.end}')

            if len(wav_files) == 0:
                return

            # sort the files by start time
            wav_files.sort(key=lambda x: x.start)

            # create a dataframe from the wav files
            self.log.info(
                f'{self.log_prefix} Creating dataframe from {len(wav_files)} files spanning {wav_files[0].start} to {wav_files[-1].start}...')
            for wc in wav_files:
                df_wav = wc.to_df()

                # concatenate the metadata to the dataframe
                self.df = pd.concat([self.df, df_wav], axis=0)

            # drop any rows with duplicate uris, keeping the first
            self.df = self.df.drop_duplicates(subset=['uri'], keep='first')

        except Exception as ex:
            self.log.exception(str(ex))
        finally:
            days = (self.end - self.start).days + 1

            if len(self.df) == 0:
                self.log.info(f'{self.log_prefix} No data found between {self.start} and {self.end}')
                return

            # Correct the metadata for each day
            for day in range(days):
                day_start = self.start + timedelta(days=day)
                self.log.debug(f'{self.log_prefix}  Running metadata corrector for {day_start}')
                soundtrap = True
                corrector = MetadataCorrector(self.log, self.df, self.json_base_dir, day_start, soundtrap, 0)
                corrector.run()


if __name__ == '__main__':
    from src.logging_helper import PbpLogger, create_logger
    from generator import SoundTrapMetadataGenerator
    log_dir = Path('tests/log')
    json_dir = Path('tests/json/soundtrap')
    log_dir.mkdir(exist_ok=True, parents=True)
    json_dir.mkdir(exist_ok=True, parents=True)

    logger = create_logger(
        log_filename_and_level=(
            f"{log_dir}/test_soundtrap_metadata_generator.log",
            logging.INFO,
        ),
        console_level=logging.INFO,
    )

    start = datetime(2023, 7, 18)
    end = datetime(2023, 7, 19)
    gen = SoundTrapMetadataGenerator(logger,
                                     's3://pacific-sound-ch01',
                                     json_dir.as_posix(),
                                     ["7000"],
                                     start, end)
    gen.run()
