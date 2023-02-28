import os
from math import ceil, floor
from typing import Generator, Optional

import numpy as np
import soundfile as sf

from src.json_support import parse_json_lines_file


class FileHelper:
    """
    Helps loading audio segments.
    """

    def __init__(
        self,
        json_base_dir: str,
        audio_base_dir: Optional[str] = None,
    ):
        """

        :param json_base_dir:
          Directory containing the YYYYMMDD.json json-lines files
        :param audio_base_dir:
          If given, this will be the base directory to use when the JSON `path` attribute is relative
          (not starting with a slash).
        """
        self.json_base_dir = json_base_dir
        self.audio_base_dir = audio_base_dir

        # the following set by select_day:
        self.year: Optional[int] = None
        self.month: Optional[int] = None
        self.day: Optional[int] = None
        self.json_filename: Optional[str] = None

    def select_day(self, year: int, month: int, day: int) -> bool:
        """
        Select the given day for subsequent processing of relevant audio segments.
        :return:  True only if selection was successful
        """

        json_filename = f"{self.json_base_dir}/{year:04}{month:02}{day:02}.json"
        if not os.path.isfile(json_filename):
            print(f"ERROR: {self.json_filename}: file not found\n")
            return False

        self.year = year
        self.month = month
        self.day = day
        self.json_filename = json_filename
        return True

    def gen_audio_segments(
        self, segment_size_in_secs: int = 60
    ) -> Generator[np.ndarray, None, None]:
        """
        Generate audio segments of the given size for the selected day.
        """
        assert self.json_filename is not None

        print(f"gen_audio_segments: segment_size_in_secs={segment_size_in_secs}")

        at_hour, at_minute, at_seconds = 0, 0, 0

        # ad_hoc_prefix = "/Volumes"
        ad_hoc_prefix = ""

        json_entries = parse_json_lines_file(self.json_filename)
        for tme in json_entries:
            wav_filename = (
                f"{ad_hoc_prefix}{tme.path}"
                if tme.path.startswith("/")
                else f"{self.audio_base_dir}/{tme.path}"
            )

            print(f"{wav_filename}:")

            _, sample_rate = sf.read(wav_filename, start=0, frames=1)
            print(f"  sample_rate = {sample_rate}")

            with sf.SoundFile(wav_filename) as f:
                start_time_secs = (at_hour * 60 + at_minute) * 60 + at_seconds
                start_sample = floor(start_time_secs * sample_rate)
                num_samples = ceil(segment_size_in_secs * sample_rate)

                print(f"  loading {num_samples:,} samples starting at {start_sample:,}")

                f.seek(start_sample)
                audio_segment = f.read(num_samples)
                yield audio_segment
                return
