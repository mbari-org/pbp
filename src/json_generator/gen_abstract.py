# pypam-based-processing
# Filename: metadata/generator/gen_abstract.py
# Description:  Abstract class that captures sound wav metadata
import logging

import re

from datetime import datetime

import pandas as pd

from src.json_generator import utils
from src.logging_helper import PbpLogger, create_logger


class MetadataGeneratorAbstract(object):
    def __init__(self,
                 logger: PbpLogger,
                 wav_loc: str,
                 json_base_dir: str,
                 search: [str],
                 start: datetime,
                 end: datetime,
                 seconds_per_file: float = 0.,
                 **kwargs):
        """
        Abstract class for capturing sound wav metadata
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
        try:
            self.wav_loc = wav_loc
            self.json_base_dir = json_base_dir
            self.df = pd.DataFrame()
            self.start = start
            self.end = end
            self.search = search
            self._seconds_per_file = None if seconds_per_file == 0 else seconds_per_file
            self.logger = logger
        except Exception as e:
            raise e

    def setup(self):
        """
        Setup by first getting the bucket name and checking if it is an S3 bucket
        :return:
        """
        self.log.info(
            f'{self.log_prefix} Searching in {self.wav_loc}/*.wav for wav files that match the search pattern {self.search}* ...')

        is_s3 = re.match(r'^s3://', self.wav_loc)
        # the bucket name will optionally have a * at the end
        # keep only the bucket name before the *
        bucket_core = re.sub(r'\*$', '', self.wav_loc)
        bucket_core = re.sub(r'^s3://', '', bucket_core)
        return bucket_core, is_s3

    @staticmethod
    def raw(path_or_url: str):
        w = utils.IcListenWavFile(path_or_url)

        if w.has_exception():
            return None  # skip this file

        return w

    @property
    def log(self):
        return self.logger

    @property
    def seconds_per_file(self):
        return self._seconds_per_file

    @property
    def correct_df(self):
        return self.df

    # abstract run method
    def run(self):
        pass

