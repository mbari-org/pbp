# pypam-based-processing
# Filename: metadata/generator/gen_abstract.py
# Description:  Abstract class that captures sound wav metadata

import pathlib
from datetime import datetime
from pathlib import Path

import pandas as pd
import logger
import utils as utils
from src.logging_helper import PbpLogger


class MetadataGeneratorAbstract(object):
    def __init__(self,
                 pbp_logger: PbpLogger,
                 wav_loc: str,
                 metadata_loc: str,
                 search: [str],
                 start: datetime,
                 end: datetime,
                 seconds_per_file: float = 0.):
        """
        Abstract class for capturing sound wav metadata
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
        try:
            self.wav_loc = wav_loc
            self.metadata_path = metadata_loc
            self.df = pd.DataFrame()
            self.start = start
            self.end = end
            self.search = search
            self.seconds_per_file = None if seconds_per_file == 0 else seconds_per_file
            self._log = pbp_logger
            self.cache_path = Path(log_dir) / 's3cache' / f'{self.__class__.__name__}'
            self.cache_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._log.err(f'Could not initialize {self.__class__.__name__} for {start:%Y%m%d}')
            raise e



    def search(self):
        self.log.info(
            f'{self.log_prefix} Searching in {self.wav_loc}/*.wav for wav files that match the search pattern {self.search}* ...')

        is_s3 = re.match(r'^s3://', self.wav_loc)
        # the bucket name will optionally have a * at the end
        # keep only the bucket name before the *
        bucket_core = re.sub(r'\*$', '', self.wav_loc)
        bucket_core = re.sub(r'^s3://', '', bucket_core)
        return bucket_core, is_s3, wav_files



    @staticmethod
    def raw(path_or_url: str):
        w = utils.IcListenWavFile(path_or_url)

        if w.has_exception():
            return None  # skip this file

        return w

    @property
    def log(self):
        return self._log

    @property
    def seconds_per_file(self):
        return self.seconds_per_file

    @property
    def correct_df(self):
        return self.df

    # abstract run method
    def run(self):
        pass
