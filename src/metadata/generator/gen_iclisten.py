# pypam-based-processing, Apache License 2.0
# Filename: metadata/generator/gen_iclisten.py
# Description:  Captures ICListen wav metadata in a pandas dataframe from either a local directory or S3 bucket.

import re
from datetime import timedelta
from datetime import datetime
import boto3
import numpy as np

import pandas as pd
from pathlib import Path
from progressbar import progressbar
import metadata.utils as utils
from .gen_abstract import MetadataGeneratorAbstract


class IcListenMetadataGenerator(MetadataGeneratorAbstract):

    def __int__(
            self,
            pbp_logger: PbpLogger,
            wav_loc: str,
            metadata_loc: str,
            search: [str],
            start: datetime,
            end: datetime,
            seconds_per_file: float = 0.):
        """
        Captures ICListen wav metadata in a pandas dataframe from either a local directory or S3 bucket.
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
            The number of seconds per file expected in a wav file to check for missing data. If 0, then no check is done.
        :return:
        """
        super().__init__(pbp_logger, wav_loc, metadata_loc, search, start, end, seconds_per_file)
        self.log_prefix = f'{self.__class__.__name__} {self.start:%Y%m%d}'

    def run(self):
        print(f'Generating metadata for {self.start} to {self.end}...')

        # Run for each day in the range
        for day in pd.date_range(self.start, self.end, freq='D'):
            try:
                self.df = None
                self.log.info(f'{self.log_prefix} Searching in {self.wav_loc}/*.wav for wav files that match the search pattern {self.search}* ...')

                wav_files = []
                is_s3 = re.match(r'^s3://', self.wav_loc)
                # the bucket name will optionally have a * at the end
                # keep only the bucket name before the *
                bucket_core = re.sub(r'\*$', '', self.wav_loc)
                bucket_core = re.sub(r'^s3://', '', bucket_core)

                def check_file(f: str, f_start_dt: datetime, f_end_dt: datetime):

                    f_path = Path(f)
                    wav_dt = None

                    for s in self.search:
                        # see if the file is a regexp match to search
                        rc = re.search(s, f_path.stem)

                        if rc and rc.group(0):
                            try:
                                # MARS file date is in the filename MARS_YYYYMMDD_HHMMSS.wav
                                f_path_dt = datetime.strptime(f_path.stem, f'{s}_%Y%m%d_%H%M%S')

                                if f_start_dt <= f_path_dt <= f_end_dt:
                                    wc = utils.IcListenWavFile(f, f_path_dt)
                                    wav_files.append(wc)
                                    wav_dt = f_path_dt
                            except ValueError:
                                self.log.error(f'{self.log_prefix} Could not parse {f_path.name}')
                                return None

                    return wav_dt

                if not is_s3:
                    wav_path = Path(self.wav_loc)
                    for filename in progressbar(sorted(wav_path.rglob('*.wav')), prefix='Searching : '):
                        check_file(filename, start_dt, end_dt)
                else:
                    # if the wav_loc is a s3 url, then we need to list the files in buckets that cover the start and end
                    # dates
                    client = boto3.client('s3')

                    # Set the start and end dates to an hour before and after the start and end dates
                    start_dt = day - timedelta(hours=1)
                    end_dt = day + timedelta(days=1)
                    start_dt_hour = start_dt - timedelta(minutes=30)
                    end_dt_hour = end_dt + timedelta(minutes=30)

                    for day_hour in pd.date_range(start=start_dt, end=end_dt, freq='H'):

                        bucket = f'{bucket_core}-{day_hour.year:04d}'
                        prefix = f'{day_hour.month:02d}/MARS_{day_hour.year:04d}{day_hour.month:02d}{day_hour.day:02d}_{day_hour.hour:02d}'
                        paginator = client.get_paginator('list_objects')

                        operation_parameters = {'Bucket': bucket, 'Prefix': prefix}
                        page_iterator = paginator.paginate(**operation_parameters)
                        self.log.info(f'{self.log_prefix}  Searching in bucket: {bucket} prefix: {prefix}')
                        # list the objects in the bucket
                        # loop through the objects and check if they match the search pattern
                        for page in page_iterator:
                            if 'Contents' not in page:
                                self.log.info(f'{self.log_prefix}  No data found in {bucket}')
                                break

                            for obj in page['Contents']:
                                key = obj['Key']
                                wav_dt = check_file(f's3://{bucket}/{key}', start_dt, end_dt)
                                if wav_dt is None:
                                    continue
                                if wav_dt > end_dt_hour:
                                    break
                                if wav_dt < start_dt_hour:
                                    break
                                self.log.debug(f'{self.log_prefix}  Found {wav_dt}')
                                # num_found += 1
                                # if num_found > 100:
                                #     break

                self.log.info(f'{self.log_prefix}  Found {len(wav_files)} files to process that cover the period {start_dt} - {end_dt}')

                # sort the files by start time
                wav_files.sort(key=lambda x: x.start)

                # create a dataframe from the wav files
                self.log.info(
                    f'{self.log_prefix}  Creating dataframe from {len(wav_files)} files spanning {wav_files[0].start} to {wav_files[-1].start}...')
                for wc in wav_files:
                    df_wav = wc.to_df()

                    # concatenate the metadata to the dataframe
                    self.df = pd.concat([self.df, df_wav], axis=0)

                self.log.debug(f'{self.log_prefix}  Running metadata corrector for {day}')
                corrector = utils.MetadataCorrector(self.log, self.df, self.metadata_path, day, False, 600.)
                corrector.run()

            except Exception as ex:
                self.log.exception(str(ex))
