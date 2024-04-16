# pypam-based-processing
# Filename: metadata/generator/gen_abstract.py
# Description:  Abstract class that captures sound wav metadata
from datetime import datetime
from typing import List

import pandas as pd


class MetadataGeneratorAbstract(object):
    def __init__(
        self,
        audio_loc: str,
        json_base_dir: str,
        prefix: List[str],
        start: datetime,
        end: datetime,
        seconds_per_file: float = 0.0,
        **kwargs,
    ):
        """
        Abstract class for capturing sound wav metadata
        :param audio_loc:
            The local directory or cloud bucket that contains the wav files
        :param json_base_dir:
            The local directory to write the json files to
        :param prefix:
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
            self.audio_loc = audio_loc
            self.json_base_dir = json_base_dir
            self.df = pd.DataFrame()
            self.start = start
            self.end = end
            self.prefix = prefix
            self._seconds_per_file = None if seconds_per_file == 0 else seconds_per_file
        except Exception as e:
            raise e

    @property
    def seconds_per_file(self):
        return self._seconds_per_file

    @property
    def correct_df(self):
        return self.df

    # abstract run method
    def run(self):
        pass
