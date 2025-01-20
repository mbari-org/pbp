# pbp, Apache License 2.0
# Filename: metadata/generator/gen_abstract.py
# Description:  Abstract class that captures sound wav metadata
from datetime import datetime
from typing import List

import pandas as pd


class MetadataGeneratorAbstract(object):
    def __init__(
        self,
        log,  # : loguru.Logger,
        audio_loc: str,
        json_base_dir: str,
        prefixes: List[str],
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
        :param prefixes:
            The search patterns to match the wav files, e.g. 'MARS'
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
            self.prefixes = prefixes
            self._log = log
            self._seconds_per_file = None if seconds_per_file == 0 else seconds_per_file
        except Exception as e:
            raise e

        if type(start) is datetime.datetime:
            if start.hour == 0 and start.minute == 0 and start.second == 0:
                pass
            else:
                raise ValueError("Start must be of type datetime.date or a datetime.datetime object at 00:00:00. "
                                 "Otherwise that would be the start of the HMD computation.")

        if type(end) is datetime.datetime:
            if end.hour == 0 and end.minute == 0 and end.second == 0:
                pass
            else:
                raise ValueError("End must be of type datetime.date or a datetime.datetime object at 00:00:00. "
                                 "Otherwise that would be the start of the HMD computation.")

    @property
    def seconds_per_file(self):
        return self._seconds_per_file

    @property
    def log(self):
        return self._log

    # abstract run method
    def run(self):
        pass


class SoundTrapMetadataGeneratorAbstract(object):
    def __init__(
        self,
        log,  # : loguru.Logger,
        audio_loc: str,
        json_base_dir: str,
        prefixes: List[str],
        xml_dir: str,
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
        :param prefixes:
            The search patterns to match the wav files, e.g. 'MARS'
        :param xml_dir
            The local directory that contains the log.xml files, defaults to audio_loc if none is specified.
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
            self.prefixes = prefixes
            self.xml_dir = xml_dir
            self._log = log
            self._seconds_per_file = None if seconds_per_file == 0 else seconds_per_file
        except Exception as e:
            raise e

    @property
    def seconds_per_file(self):
        return self._seconds_per_file

    @property
    def log(self):
        return self._log

    # abstract run method
    def run(self):
        pass
