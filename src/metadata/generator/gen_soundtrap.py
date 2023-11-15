# pypam-based-processing
# Filename: metadata/generator/gen_soundtrap.py
# Description:  Captures SoundTrap metadata either from a local directory of S3 bucket

import datetime
import shutil
from datetime import timedelta, datetime
import pandas as pd
from pathlib import Path
import boto3
import tempfile
import re
from progressbar import progressbar
import utils
from .gen_abstract import MetadataGeneratorAbstract


class SoundTrapMetadataGenerator(MetadataGeneratorAbstract):
    """
    Captures SoundTrap wav file metadata either from a local directory or S3 bucket.
    """
    start = datetime.utcnow()
    end = datetime.utcnow()

    def __init__(
            self,
            log_dir: str,
            wav_loc: str,
            metadata_loc: str,
            search: [str],
            start: datetime,
            end: datetime):
        """
        Captures SoundTrap wav file metadata either from a local directory or S3 bucket.

        :param pbp_logger:
            The logger
        :param wav_loc:
            The local directory or S3 bucket that contains the wav files
        :param metadata_loc:
            The local directory or S3 bucket to store the metadata
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
        super().__init__(log_dir, wav_loc, metadata_loc, search, start, end, 0.)
        self.start = start
        self.end = end
        # Add a prefix to the log messages to differentiate between the different metadata generators running by date
        # This is useful when running multiple metadata generators in parallel
        self.log_prefix = f'{self.__class__.__name__} {self.start:%Y%m%d}' # SoundTrapMetadataGenerator 20210801

    def run(self):

        try:
            self.search()

            def add_file(xml_file: str, wav_file: str):
                """
                Check if the xml file is in the cache directory
                :param xml_file:
                    The xml file with the metadata
                :param wav_file:
                    The wav file
                :return: 
                    None
                """

                f_path = Path(xml_file)
                # see if the file is a regexp match to self.search
                for s in self.search:
                    rc = re.search(s, f_path.stem)

                    if rc and rc.group(0):
                        try:
                            # If a SoundTrap file, then the date is in the filename XXXX.YYYYMMDDHHMMSS.xml
                            f_path_dt = datetime.strptime(f_path.stem.split('.')[1], '%y%m%d%H%M%S')
                            if self.start <= f_path_dt <= self.end:
                                wav_files.append(utils.SoundTrapWavFile(wav_file, xml_file))
                        except ValueError:
                            self.log.error(f'{self.log_prefix} Could not parse {f_path.name}')

            if not is_s3:
                wav_path = Path(self.wav_loc)
                for filename in progressbar(sorted(wav_path.rglob('*.xml')), prefix='Searching : '):
                    wav_path = filename.parent / f'{filename.stem}.wav'
                    add_file(filename, wav_path)
            else:
                # if the wav_loc is a s3 url, then we need to list the files in buckets that cover the start and end
                # dates
                self.log.info(f'{self.log_prefix} Searching between {self.start} and {self.end}')

                client = boto3.client('s3')

                bucket = f'{bucket_core}'
                paginator = client.get_paginator('list_objects')

                operation_parameters = {'Bucket': bucket}
                page_iterator = paginator.paginate(**operation_parameters)
                self.log.info(f'Searching in bucket: {bucket} for .wav and .xml files between {self.start} and {self.end} ')
                # list the objects in the bucket
                # loop through the objects and check if they match the search pattern
                with tempfile.TemporaryDirectory() as tmpdir:
                    for page in page_iterator:
                        for obj in page['Contents']:
                            key = obj['Key']

                            if '.xml' in key:
                                output_xml = f'{tmpdir}/{key}'
                                output_wav = f's3://{bucket}/{key}'.replace('log.xml', 'wav')

                                # Check if the xml file is in the cache directory
                                xml_path = Path(self.cache_path, key)
                                if xml_path.exists():
                                    shutil.copy(xml_path, output_xml)
                                else:
                                    # Download the xml file to a temporary directory
                                    self.log.info(f'{self.log_prefix}  Downloading {key} ...')
                                    client.download_file(bucket, key, output_xml)
                                    # Save the xml file to the cache directory
                                    self.log.info(f'{self.log_prefix} Saving {key} to {self.cache_path} ...')
                                    shutil.copy(output_xml, self.cache_path)
                                add_file(xml_path, output_wav)

            self.log.info(f'{self.log_prefix} Found {len(wav_files)} files to process that cover the period {self.start} - {self.end}')

            if len(wav_files) == 0:
                return

            # sort the files by start time
            wav_files.sort(key=lambda x: x.start)

            # create a dataframe from the wav files
            self.log.info(f'{self.log_prefix} Creating dataframe from {len(wav_files)} files spanning {wav_files[0].start} to {wav_files[-1].start}...')
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
                corrector = utils.MetadataCorrector(self.log, self.df, self.metadata_path, day_start, soundtrap, 0)
                corrector.run()


